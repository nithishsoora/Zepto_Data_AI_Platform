# Analytics Results

## Missing-value profile and decisions

- `age`: **19.87%** missing — 19.87% missing: median-imputed (5–30%)..
- `embarked`: **0.22%** missing — 0.22% missing: dropped affected rows (<5%)..
- `deck`: **77.22%** missing — 77.22% missing: dropped column (>30%) because imputation would be unreliable..
- `embark_town`: **0.22%** missing — 0.22% missing: dropped affected rows (<5%)..

## Univariate findings

- IQR outliers: `age` = **65**, `fare` = **114**.
- Fare mean = **32.097**, median = **14.454**, mode = **8.050**; this is **right-skewed** based on the requested ordering rule.

## Bivariate findings

### Survival by sex

sex
female    74.04
male      18.89

### Survival by passenger class

pclass
1    62.62
2    47.28
3    24.24

### Survival by sex and class

sex     pclass
female  1         96.74
        2         92.11
        3         50.00
male    1         36.89
        2         15.74
        3         13.54

### Strongest correlations

- `pclass` ↔ `fare`: **-0.548**. This is one of the two largest absolute off-diagonal correlations in the required six-column matrix.
- `sibsp` ↔ `parch`: **0.415**. This is one of the two largest absolute off-diagonal correlations in the required six-column matrix.

## Multivariate data story

1. **Class + sex chart:** Survival rates differ strongly across sex and passenger class, showing that these two categorical variables jointly separate outcomes. The chart is descriptive and does not claim causality.

2. **Age + class box plot:** Age distributions overlap across survival groups, while class remains a visible grouping variable. This supports examining age jointly with class rather than treating age alone as the explanation.

3. **Age + fare scatter:** The plot shows the joint distribution of age and fare with survival and sex encoded, making clusters and overlap visible. It also shows why a multivariate model is useful: the classes are not perfectly separable by any single continuous feature.

4. **Survival heatmap:** The sex-by-class heatmap makes the combined survival-rate pattern easy to compare. The strongest contrasts occur when the two categorical dimensions are considered together.

## Standardization sanity check

The generated `standardization_check.csv` records the original and transformed means/stds for age and fare; the transformed columns should be approximately mean 0 and standard deviation 1.

## Modeling

A stratified split produced **711 training rows** and **178 test rows**. Stratification preserves the observed survived/not-survived class proportions across the two splits, reducing avoidable sampling variation in an imbalanced binary target.

All classifier preprocessing is inside the fitted scikit-learn pipeline, so imputers, one-hot encoders, and scalers are fitted on training data and only transformed on the test data.

### Classifier comparison

| model               |   accuracy |   precision |   recall |       f1 |      auc |
|:--------------------|-----------:|------------:|---------:|---------:|---------:|
| Logistic Regression |   0.808989 |    0.783333 | 0.691176 | 0.734375 | 0.860963 |
| Decision Tree       |   0.764045 |    0.76     | 0.558824 | 0.644068 | 0.837366 |
| Random Forest       |   0.808989 |    0.765625 | 0.720588 | 0.742424 | 0.819519 |

### Imbalance comparison

| variant               |   precision |   recall |       f1 |
|:----------------------|------------:|---------:|---------:|
| baseline              |    0.783333 | 0.691176 | 0.734375 |
| class_weight_balanced |    0.71831  | 0.75     | 0.733813 |
| SMOTE                 |    0.735294 | 0.735294 | 0.735294 |

The highest F1 in this three-way comparison is the `SMOTE` variant (**0.735**). Precision and recall should be considered together because the class-weight and SMOTE approaches change the balance between false positives and false negatives.

### Random Forest tuning

Best parameters: `{'model__max_depth': None, 'model__max_features': 'sqrt', 'model__n_estimators': 100}`. Best cross-validation F1 = **0.748**; OOB score = **0.802**.

### Regression side-task

|     MAE |    RMSE |       R2 |   Adjusted_R2 |
|--------:|--------:|---------:|--------------:|
| 21.1386 | 41.7465 | 0.346774 |       0.31178 |

The residual plot shows **heteroscedasticity** in this run: the correlation between absolute residual magnitude and predicted fare is **0.334**, and the highest-prediction quartile has much wider residual spread. The spread therefore changes with fitted value rather than remaining approximately constant.

## Final model-selection statement

On this fixed test split, the classifier with the highest F1 in the generated comparison is **Random Forest** (F1 = 0.742, AUC = 0.820). Its precision, recall, accuracy and AUC are shown in `model_comparison.csv`, so the deployment choice is tied to the observed metric values rather than a generic model preference. The saved artifact is the complete preprocessing-plus-estimator pipeline, not a bare estimator.
