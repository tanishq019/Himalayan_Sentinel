# Training data

Place `flood_risk_dataset_india.csv` here from Kaggle: **Flood Risk Prediction Dataset in India**.

Prototype training dataset: Kaggle Flood Risk Prediction Dataset in India (synthetic).
The repository deliberately does not download or fabricate this source data. For a local UI smoke test only, run `python scripts/train_model.py --dev-synthetic`; it creates a separately labelled development dataset and must not be presented as the Kaggle dataset.
