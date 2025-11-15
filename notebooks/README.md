# Jupyter Notebooks for FDA-3-Stream Analysis

## Notebooks

1. **01_data_extraction_preprocessing.ipynb** - Module 1: Data extraction and feature generation
2. **02_model_training_evaluation.ipynb** - Module 2 & 3: Model training and evaluation

## Running the Notebooks

```bash
# Activate virtual environment
source ../venv/bin/activate

# Install Jupyter if not already installed
pip install jupyter

# Start Jupyter
jupyter notebook

# Or use JupyterLab
jupyter lab
```

## Notebook Contents

### 01_data_extraction_preprocessing.ipynb
- Loads revenue recognition data
- Computes numeric ratios (Revenue-to-CashFlow, Deferred Revenue Ratio)
- Extracts key phrases from policy text
- Preprocesses data for streaming

### 02_model_training_evaluation.ipynb
- Trains text classification models (MultinomialNB, LogisticRegression, HoeffdingTree)
- Trains regression models (LinearRegression, AdaptiveRandomForest)
- Evaluates models with metrics (Accuracy, F1, MAE, RMSE, R²)
- Analyzes feature importance

