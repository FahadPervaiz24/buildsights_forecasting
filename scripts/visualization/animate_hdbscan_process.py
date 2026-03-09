#!/usr/bin/env python3
"""Animate raw-permit HDBSCAN stages (raw, visual-cap, final assignment)."""

import argparse
import shutil
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.animation import FFMpegWriter, FuncAnimation, PillowWriter


BG = "#000000"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Animate latest raw-permit clustering process.")
    parser.add_argument(
        "--assignments",
        default="data/processed/permit_cluster_assignments.parquet",
        help="Parquet with cluster_id_raw/cluster_id_visual/cluster_id_final and lat/lon.",
    )
    parser.add_argument(
        "--output",
        default="scripts/visualization/output/hdbscan_process_improved.mp4",
        help="Output animation path (.mp4 preferred).",
    )
    parser.add_argument(
        "--max-points",
        type=int,
        default=350000,
        help="Max permits to animate (for render speed).",
    )
    parser.add_argument(
        "--point-size",
        type=float,
        default=0.55,
        help="Scatter point size.",
    )
    parser.add_argument("--fps", type=int, default=12, help="FPS for MP4 output.")
    parser.add_argument("--dpi", type=int, default=180, help="DPI for MP4 output.")
    parser.add_argument("--gif-fps", type=int, default=8, help="FPS for GIF fallback.")
    parser.add_argument("--gif-dpi", type=int, default=100, help="DPI for GIF fallback.")
    return parser.parse_args()


def colors_for_ids(ids: np.ndarray, *, seed: int, noise_color: tuple[float, float, float, float]) -> np.ndarray:
    rng = np.random.default_rng(seed)
    unique_ids = sorted(set(int(x) for x in ids.tolist()))
    cmap = {}
    for cid in unique_ids:
        if cid == -1:
            cmap[cid] = np.array(noise_color)
        else:
            cmap[cid] = np.array([rng.random(), rng.random(), rng.random(), 0.9])
    return np.vstack([cmap[int(x)] for x in ids])


def blend(a: np.ndarray, b: np.ndarray, t: float) -> np.ndarray:
    return (1.0 - t) * a + t * b


def build_density_colors(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    # Fast density proxy: 2D histogram bin count mapped back to points.
    bins = 420
    h, xedges, yedges = np.histogram2d(x, y, bins=bins)
    xi = np.clip(np.digitize(x, xedges) - 1, 0, h.shape[0] - 1)
    yi = np.clip(np.digitize(y, yedges) - 1, 0, h.shape[1] - 1)
    counts = h[xi, yi]
    log_counts = np.log1p(counts)
    vmax = np.nanpercentile(log_counts, 99)
    vmax = vmax if np.isfinite(vmax) and vmax > 0 else max(float(log_counts.max()), 1.0)
    norm = plt.Normalize(vmin=0.0, vmax=vmax)
    rgba = plt.get_cmap("plasma")(norm(log_counts))
    rgba[:, 3] = 0.9
    return rgba


def load_data(assignments_path: str, max_points: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    cols = ["latitude", "longitude", "cluster_id_raw", "cluster_id_visual", "cluster_id_final"]
    df = pd.read_parquet(assignments_path, columns=cols).dropna(subset=["latitude", "longitude"]).copy()
    if df.empty:
        raise RuntimeError("No valid points found in assignments file.")

    if len(df) > max_points:
        df = df.sample(n=max_points, random_state=42)

    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
        crs="EPSG:4326",
    ).to_crs("EPSG:2263")

    x = gdf.geometry.x.to_numpy()
    y = gdf.geometry.y.to_numpy()
    raw_ids = gdf["cluster_id_raw"].astype(int).to_numpy()
    visual_ids = gdf["cluster_id_visual"].astype(int).to_numpy()
    final_ids = gdf["cluster_id_final"].astype(int).to_numpy()
    return x, y, raw_ids, visual_ids, final_ids


def make_animation(
    x: np.ndarray,
    y: np.ndarray,
    density_colors: np.ndarray,
    raw_colors: np.ndarray,
    visual_colors: np.ndarray,
    final_colors: np.ndarray,
    point_size: float,
    output_path: Path,
    fps: int,
    dpi: int,
    gif_fps: int,
    gif_dpi: int,
) -> Path:
    hold_density = 20
    fade_to_raw = 24
    hold_raw = 16
    fade_to_visual = 24
    hold_visual = 16
    fade_to_final = 24
    hold_final = 24

    def frame_colors(frame: int) -> np.ndarray:
        if frame < hold_density:
            return density_colors

        frame -= hold_density
        if frame < fade_to_raw:
            return blend(density_colors, raw_colors, frame / max(fade_to_raw - 1, 1))

        frame -= fade_to_raw
        if frame < hold_raw:
            return raw_colors

        frame -= hold_raw
        if frame < fade_to_visual:
            return blend(raw_colors, visual_colors, frame / max(fade_to_visual - 1, 1))

        frame -= fade_to_visual
        if frame < hold_visual:
            return visual_colors

        frame -= hold_visual
        if frame < fade_to_final:
            return blend(visual_colors, final_colors, frame / max(fade_to_final - 1, 1))

        return final_colors

    total_frames = hold_density + fade_to_raw + hold_raw + fade_to_visual + hold_visual + fade_to_final + hold_final

    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(10, 10), facecolor=BG)
    ax.set_facecolor(BG)
    ax.axis("off")
    ax.set_aspect("equal", adjustable="box")

    pad = max(x.max() - x.min(), y.max() - y.min()) * 0.02
    ax.set_xlim(x.min() - pad, x.max() + pad)
    ax.set_ylim(y.min() - pad, y.max() + pad)

    scat = ax.scatter(x, y, s=point_size, c=density_colors, linewidths=0, marker="o")
    state = {"last_logged": -1}

    def update(frame: int):
        scat.set_color(frame_colors(frame))
        if frame % 10 == 0 and frame != state["last_logged"]:
            print(f"render frame {frame}")
            state["last_logged"] = frame
        return [scat]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.suffix.lower() == ".gif":
        print(f"rendering GIF: frames={total_frames}, fps={gif_fps}, dpi={gif_dpi}")
        anim = FuncAnimation(fig, update, frames=total_frames, interval=1000 / gif_fps, blit=True)
        writer = PillowWriter(fps=gif_fps)
        anim.save(output_path, writer=writer, dpi=gif_dpi)
        saved_path = output_path
    else:
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path:
            print(f"rendering MP4 with ffmpeg: frames={total_frames}, fps={fps}, dpi={dpi}")
            anim = FuncAnimation(fig, update, frames=total_frames, interval=1000 / fps, blit=True)
            writer = FFMpegWriter(fps=fps, codec="libx264", bitrate=3000)
            anim.save(output_path, writer=writer, dpi=dpi)
            saved_path = output_path
        else:
            fallback = output_path.with_suffix(".gif")
            print(
                f"ffmpeg not found on PATH. Saving GIF instead: {fallback}\n"
                f"rendering GIF fallback: frames={total_frames}, fps={gif_fps}, dpi={gif_dpi}"
            )
            anim = FuncAnimation(fig, update, frames=total_frames, interval=1000 / gif_fps, blit=True)
            writer = PillowWriter(fps=gif_fps)
            anim.save(fallback, writer=writer, dpi=gif_dpi)
            saved_path = fallback

    plt.close(fig)
    return saved_path


def main() -> None:
    args = parse_args()
    x, y, raw_ids, visual_ids, final_ids = load_data(args.assignments, args.max_points)
    print(f"points animated: {len(x):,}")

    density_colors = build_density_colors(x, y)
    raw_colors = colors_for_ids(raw_ids, seed=42, noise_color=(0.62, 0.62, 0.62, 0.88))
    visual_colors = colors_for_ids(visual_ids, seed=42, noise_color=(0.62, 0.62, 0.62, 0.88))
    final_colors = colors_for_ids(final_ids, seed=42, noise_color=(0.62, 0.62, 0.62, 0.88))

    saved = make_animation(
        x=x,
        y=y,
        density_colors=density_colors,
        raw_colors=raw_colors,
        visual_colors=visual_colors,
        final_colors=final_colors,
        point_size=args.point_size,
        output_path=Path(args.output),
        fps=args.fps,
        dpi=args.dpi,
        gif_fps=args.gif_fps,
        gif_dpi=args.gif_dpi,
    )
    print(f"saved animation: {saved}")


if __name__ == "__main__":
    main()
