# Buildsights Forecasting v1

This project is an ML-focused spatiotemporal permit modeling workspace for NYC: it builds a unified training dataset from multi-source DOB records, learns temporal baselines for count forecasting, and derives unsupervised spatial regimes using density-based clustering.

## Project Goal
- Build robust monthly permit-count forecasting baselines with reproducible evaluation.
- Learn spatial structure in permit activity via unsupervised clustering on raw point data.
- Support feature engineering and regime-aware modeling with interpretable cluster assignments.

## What The Project Does
- Ingests historical and modern DOB permit streams and normalizes them into a single canonical feature space.
- Produces modeling-ready panel/time-series datasets at district and cluster granularities.
- Benchmarks univariate forecasting baselines (rolling mean, SARIMA-style comparisons) using held-out error metrics.
- Runs adaptive borough-aware HDBSCAN to detect spatial permit regimes under heterogeneous urban densities.
- Post-processes clusters into visual-cap representations and full final assignments for downstream ML workflows.
- Generates analytical visuals/animations for density diagnostics, cluster validation, and model communication.

## Data Scope
- **DOB Permit Issuance** (`ipu4-2q9a`): historical permit issuance records.
- **DOB NOW: Build – Approved Permits** (`rbx6-tga4`): modern DOB NOW permit approvals.
- **NYC Community District geometry**: spatial context used for district attribution and borough-aware clustering calibration.

## Repository Structure
- `data/`: raw sources plus feature-engineered/derived artifacts used by forecasting and clustering models.
- `scripts/`: data engineering, model baselines, unsupervised clustering, and visualization/diagnostic code.
- `report.md`: experiment notes, metric snapshots, and interpretation findings.
- `PRD.md`: milestone checklist for data, modeling, evaluation, and handoff readiness.

## Documentation Map
- `data/README.md`: one-line description of files in the data directory.
- `scripts/README.md`: one-line description of scripts and visualization outputs.
