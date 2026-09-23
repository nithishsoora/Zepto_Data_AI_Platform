# Module 2 — Analytics Pipeline

`run_analytics.py` is the single ordered pipeline for profiling, cleaning, EDA, classification, imbalance analysis, Random Forest tuning, regression, and artifact validation.

## Raw-load rule

Normal mode calls `sns.load_dataset('titanic')` exactly once and immediately writes `titanic.csv`. All subsequent operations use that DataFrame. `--offline` is provided for grading/reruns after the committed CSV exists.

## Missing-value strategy

The strategy is based on the original loaded DataFrame's missing percentages:

- `age`: 19.87% → median imputation (5–30%).
- `embarked`: 0.22% → drop affected rows (<5%).
- `deck`: 77.22% → drop the column (>30%).
- `embark_town`: 0.22% → drop affected rows (<5%); in practice these are the same rows already removed by the `embarked` rule.

## Modeling leakage control

The train/test split happens before classifier preprocessing. A `ColumnTransformer` inside a scikit-learn `Pipeline` fits imputers, one-hot encoding, and scaling only on the training data. Test data is only transformed through the already-fitted pipeline.

## Generated evidence

`outputs/` contains the missing-value table, bivariate rates, six-column correlation matrix, required charts, classifier metrics, imbalance comparison, RF tuning/OOB result, regression metrics, residual plot, model comparison, and reload check. `models/best_pipeline.joblib` is the complete fitted preprocessing + estimator object.
