# BuildSights Forecasting v1

BuildSights is a spatiotemporal modeling project focused on understanding and forecasting construction activity in New York City using Department of Buildings (DOB) permit records.

The project builds a unified dataset from multiple DOB data sources, analyzes spatial patterns in permit activity, and develops forecasting baselines to predict monthly permit counts across the city.

The system combines **data engineering, spatial analysis, unsupervised clustering, and time-series forecasting** to better understand how construction activity evolves over time and across neighborhoods.

---

## Project Goals

- Build reliable monthly permit-count forecasting baselines with reproducible evaluation.
- Discover spatial structure in construction activity using unsupervised clustering.
- Support future modeling by creating interpretable spatial regimes for feature engineering and forecasting.

---

## What The Project Does

- Ingests historical and modern NYC DOB permit datasets from NYC Open Data APIs.
- Normalizes records from multiple permit systems into a single canonical dataset.
- Builds modeling-ready time-series datasets at both **community district** and **cluster-based spatial regimes**.
- Benchmarks baseline forecasting approaches (rolling mean and SARIMA-style comparisons).
- Uses **HDBSCAN clustering** on raw permit locations to identify organically emerging development zones.
- Post-processes clusters for stability and visualization.
- Generates visual diagnostics and animations to analyze permit density and clustering behavior.

---

## Data Sources

- **DOB Permit Issuance** (`ipu4-2q9a`)  
  Historical permit issuance records from NYC Open Data.

- **DOB NOW: Build – Approved Permits** (`rbx6-tga4`)  
  Modern DOB NOW system permit approvals.

- **NYC Community District Geometry**  
  Spatial boundary dataset used for district-level attribution and spatial analysis.

---

## Repository Structure

## Repository Structure
- `data/`: Raw and processed datasets used throughout the pipeline.
- `scripts/`: dData engineering, clustering, modeling, and visualization scripts.
- `report.md`: Experiment notes, modeling results, and interpretation findings.
- `PRD.md`: Project roadmap and milestone checklist tracking completed and remaining work.

## Documentation Map
- `data/README.md`: description of datasets and generated artifacts
- `scripts/README.md`: description of processing, modeling, and visualization scripts
