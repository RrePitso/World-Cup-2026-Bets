# World Cup 2026 Predictive Betting Pipeline

## Overview
This repository contains a comprehensive, automated machine learning architecture designed to predict match outcomes and expected goals (xG) for the 2026 FIFA World Cup. The pipeline calculates the true probability of match events and identifies positive Expected Value (+EV) betting opportunities by comparing model outputs against live bookmaker odds.

The system utilizes a hybrid modeling approach, combining Random Forest Regressors for expected goals with calibrated classification models, distributed through Poisson probability mass functions to evaluate exact scorelines and Over/Under thresholds.

## Key Features
* **Hybrid Machine Learning Architecture**: Utilizes continuous regressors for Expected Goals (xG) and discrete classifiers for match outcomes (1X2).
* **Probability Calibration**: Implements Platt Scaling (Sigmoid) and Isotonic Regression via `CalibratedClassifierCV` to correct probability biases inherent in tree-based models, ensuring predictions represent true betting probabilities.
* **Dynamic Feature Engineering**: Integrates rolling historical metrics (Elo ratings, form, goal difference) with real-world heuristics (Transfermarkt squad values, Open-Meteo weather APIs, travel rest days, and group-stage stakes).
* **Automated MLOps**: Features a fully automated CI/CD pipeline using GitHub Actions to fetch new data, retrain the models, and generate predictions daily.
* **Interactive Dashboard**: Includes a Streamlit web application for visualizing upcoming fixtures, model confidence intervals, and betting edges.

---

## Repository Structure
```text
world-cup-2026-bets/
│
├── .github/workflows/
│   └── retrain_pipeline.yml     # Automated scheduled retraining and inference
│
├── app/                         # Streamlit Web Application
│   ├── main.py                  # Dashboard entry point
│   └── pages/                   # Application views
│       ├── 1_📅_Calendar.py
│       ├── 2_🔮_Predictions.py
│       └── 3_⚙️_Model_Status.py
│
├── src/                         # Core Pipeline Logic
│   ├── config.py                # Global configuration and environment variables
│   ├── data/
│   │   ├── fetcher.py           # API integration for fixtures and results
│   │   └── preprocessor.py      # Data cleaning and chronological splitting
│   ├── features/
│   │   └── engineering.py       # Elo ratings, form calculations, environmental factors
│   ├── models/
│   │   ├── train.py             # Model training, hyperparameter tuning, and calibration
│   │   └── dixon_coles.py       # Algorithmic goal distribution models
│   ├── inference/
│   │   └── predict.py           # Generation of predictions on upcoming fixtures
│   └── utils/
│       ├── betting.py           # EV calculations, Kelly Criterion, and edge detection
│       └── gdrive_sync.py       # State management and cloud synchronization
│
├── Betting.ipynb                # Jupyter Notebook for Model Iteration & Analysis
└── requirements.txt             # Python environment dependencies
## Methodology
1. Feature Engineering
The pipeline avoids lookahead bias by strictly utilizing a chronological train/test split. Features are engineered dynamically, computing pre-match states for every historical fixture. Variables include team strength disparities, fatigue indexing, and environmental penalties (e.g., high heat or humidity impacts).

2. Modeling
The core prediction engine handles outcomes on two fronts:

Goal Regressor: Predicts the combined total goals of a match.

Match Outcome Classifier: Predicts the 1X2 market (Home/Draw/Away) using custom class weighting to handle the natural imbalance of football results.
Both models are wrapped in cross-validated calibration methods to ensure the output probabilities (predict_proba) can be mathematically trusted when calculating betting value.

3. Value Calculation
Predictions are compared against implied bookmaker probabilities. The system calculates the Expected Value (EV) per unit staked and recommends bet sizing using a fractional Kelly Criterion to optimize bankroll growth while managing variance.

Installation
Prerequisites
Python 3.9+

## Git

### Setup Instructions
1. Clone the repository:
   ```bash
git clone https://github.com/yourusername/world-cup-2026-bets.git
cd world-cup-2026-bets
```
2. Create and activate a virtual environment:
   ```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```
3. Install the required dependencies:
      ```bash
pip install -r requirements.txt
   ```
4. Configure Environment Variables:
Create a .env file in the root directory and add any necessary API keys or Google Drive credentials required by config.py and gdrive_sync.py.

## Usage
## Running the Pipeline Locally
To execute the data fetching, feature engineering, and model training pipeline from scratch:
python src/models/train.py

To generate predictions for the next set of fixtures:
python src/inference/predict.py

## Launching the Dashboard
To start the interactive Streamlit application:
streamlit run app/main.py

## Automation
This repository utilizes GitHub Actions (retrain_pipeline.yml) to ensure the model remains up-to-date throughout the tournament. The workflow is triggered on a chronological schedule, automatically executing the data fetcher, retraining the models on the latest results, and uploading the updated artifacts to Google Drive.

## Model Iteration & Analysis (Betting.ipynb)
For a deep dive into the data exploration, feature engineering decisions, and model evolution, refer to the Betting.ipynb notebook included in the root directory.

Google Colab Compatibility: This file can be uploaded directly to Google Colab for cloud-based execution and review.

Important Note on Versioning: The notebook chronicles the development of several model iterations. The most current, accurate, and sophisticated architecture is Version 4. If you are reviewing the code, the most critical execution cells and the final production pipeline begin immediately following the "Version 4" markdown header.

## Disclaimer
For Educational and Informational Purposes Only.
The predictions, probabilities, and betting strategies generated by this repository do not constitute financial advice. Sports betting carries a high level of risk and may not be suitable for all users. Past performance of the machine learning models does not guarantee future results. Please gamble responsibly and only risk capital you can afford to lose.
