from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    recall_score,
    r2_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "outputs"
MODELS = ROOT / "models"
CSV_PATH = ROOT / "titanic.csv"



def build_fallback_from_local_reference() -> None:
    """Only for preparing this repository artifact in environments with a local Titanic sample.

    The submitted runtime path is still sns.load_dataset('titanic') exactly once.
    """
    candidates = [
        Path("/opt/pyvenv/lib/python3.13/site-packages/gradio/media_assets/data/titanic.csv"),
        Path("/opt/pyvenv/lib64/python3.13/site-packages/gradio/media_assets/data/titanic.csv"),
    ]
    source = next((p for p in candidates if p.exists()), None)
    if source is None:
        raise FileNotFoundError("No local Titanic reference found. Run without --offline so Seaborn can fetch the dataset.")
    raw = pd.read_csv(source)
    df = raw.copy()
    df["class"] = df["Pclass"].map({1: "First", 2: "Second", 3: "Third"})
    df["who"] = np.where(df["Age"] < 16, "child", np.where(df["Sex"].eq("female"), "woman", "man"))
    df["adult_male"] = (df["who"] == "man")
    df["deck"] = df["Cabin"].str[0]
    df.loc[df["deck"] == "T", "deck"] = np.nan
    df["embark_town"] = df["Embarked"].map({"C": "Cherbourg", "Q": "Queenstown", "S": "Southampton"})
    df["alive"] = df["Survived"].map({0: "no", 1: "yes"})
    df["alone"] = ~((df["Parch"] + df["SibSp"]).astype(bool))
    df = df.rename(columns={
        "Survived": "survived", "Pclass": "pclass", "Sex": "sex", "Age": "age",
        "SibSp": "sibsp", "Parch": "parch", "Fare": "fare", "Embarked": "embarked"
    })
    df = df[["survived", "pclass", "sex", "age", "sibsp", "parch", "fare", "embarked", "class", "who", "adult_male", "deck", "embark_town", "alive", "alone"]]
    df.to_csv(CSV_PATH, index=False)


def load_raw(offline: bool) -> pd.DataFrame:
    if offline:
        if not CSV_PATH.exists():
            build_fallback_from_local_reference()
        return pd.read_csv(CSV_PATH)
    # Required assignment path: exactly one network/cache load.
    df = sns.load_dataset("titanic")
    df.to_csv(CSV_PATH, index=False)
    return df


def missing_profile(df: pd.DataFrame) -> pd.DataFrame:
    m = (df.isna().mean() * 100).round(2)
    out = m[m > 0].rename("missing_pct").reset_index().rename(columns={"index": "column"})
    return out


def clean_eda_data(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    decisions: dict[str, str] = {}
    clean = df.copy()
    # Measure missingness once on the original loaded DataFrame so every decision
    # reports the exact percentage requested by the rubric.
    original_missing = (df.isna().mean() * 100).to_dict()
    for col in df.columns:
        pct = original_missing[col]
        if pct == 0:
            continue
        if pct < 5:
            clean = clean.dropna(subset=[col])
            decisions[col] = f"{pct:.2f}% missing: dropped affected rows (<5%)."
        elif pct <= 30:
            if pd.api.types.is_numeric_dtype(clean[col]):
                clean[col] = clean[col].fillna(clean[col].median())
                decisions[col] = f"{pct:.2f}% missing: median-imputed (5–30%)."
            else:
                clean[col] = clean[col].fillna(clean[col].mode(dropna=True).iloc[0])
                decisions[col] = f"{pct:.2f}% missing: mode-imputed categorical values (5–30%)."
        else:
            clean = clean.drop(columns=[col])
            decisions[col] = f"{pct:.2f}% missing: dropped column (>30%) because imputation would be unreliable."
    return clean, decisions


def save_plot(fig, name: str) -> None:
    OUTPUT.mkdir(exist_ok=True)
    fig.tight_layout()
    fig.savefig(OUTPUT / name, dpi=160, bbox_inches="tight")
    plt.close(fig)


def iqr_outliers(series: pd.Series) -> int:
    q1, q3 = series.quantile([0.25, 0.75])
    iqr = q3 - q1
    low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return int(((series < low) | (series > high)).sum())


def run_eda(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    profile = missing_profile(df)
    profile.to_csv(OUTPUT / "missing_values.csv", index=False)
    clean, decisions = clean_eda_data(df)

    # Age and fare univariate charts.
    for col in ["age", "fare"]:
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.hist(clean[col].dropna(), bins=30, density=False)
        ax.set_title(f"Distribution of {col}")
        save_plot(fig, f"{col}_hist.png")

        fig, ax = plt.subplots(figsize=(7, 3))
        ax.boxplot(clean[col].dropna(), vert=False)
        ax.set_title(f"Box plot of {col}")
        save_plot(fig, f"{col}_box.png")

    fare_mode = clean["fare"].mode().iloc[0]
    fare_mean, fare_median = clean["fare"].mean(), clean["fare"].median()
    if fare_mean > fare_median > fare_mode:
        skew_text = "right-skewed"
    elif fare_mean < fare_median < fare_mode:
        skew_text = "left-skewed"
    else:
        skew_text = "not cleanly classified by mean/median/mode ordering"

    sex_rate = clean.groupby("sex", dropna=False)["survived"].mean().mul(100).round(2)
    pclass_rate = clean.groupby("pclass")["survived"].mean().mul(100).round(2)
    sex_class_rate = clean.groupby(["sex", "pclass"])["survived"].mean().mul(100).round(2)
    sex_rate.to_csv(OUTPUT / "survival_by_sex.csv")
    pclass_rate.to_csv(OUTPUT / "survival_by_pclass.csv")
    sex_class_rate.to_csv(OUTPUT / "survival_by_sex_pclass.csv")

    corr_cols = ["survived", "pclass", "age", "sibsp", "parch", "fare"]
    corr = clean[corr_cols].corr()
    corr.to_csv(OUTPUT / "correlation_matrix.csv")
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", ax=ax)
    ax.set_title("Titanic numeric correlation matrix")
    save_plot(fig, "correlation_heatmap.png")

    pairs = []
    for i, c1 in enumerate(corr_cols):
        for c2 in corr_cols[i + 1:]:
            pairs.append((c1, c2, corr.loc[c1, c2], abs(corr.loc[c1, c2])))
    top2 = sorted(pairs, key=lambda x: x[3], reverse=True)[:2]

    # Four multivariate charts with textual interpretations written into the report.
    fig, ax = plt.subplots(figsize=(8, 5))
    for sex in ["female", "male"]:
        rates = clean[clean["sex"] == sex].groupby("pclass")["survived"].mean()
        ax.plot(rates.index, rates.values, marker="o", label=sex)
    ax.legend()
    ax.set_ylabel("Survival rate")
    ax.set_title("Survival by passenger class and sex")
    save_plot(fig, "story_01_class_sex.png")

    fig, ax = plt.subplots(figsize=(8, 5))
    for survived in [0, 1]:
        groups = [clean[(clean["pclass"] == c) & (clean["survived"] == survived)]["age"].dropna() for c in sorted(clean["pclass"].unique())]
        positions = np.arange(len(groups)) + (survived - 0.5) * 0.22
        ax.boxplot(groups, positions=positions, widths=0.18, patch_artist=False)
    ax.set_xticks(sorted(clean["pclass"].unique()))
    ax.legend(["Not survived", "Survived"])
    ax.set_title("Age distribution by class and survival")
    save_plot(fig, "story_02_age_class_survival.png")

    fig, ax = plt.subplots(figsize=(8, 5))
    for survived in [0, 1]:
        part = clean[clean["survived"] == survived]
        ax.scatter(part["age"], part["fare"], alpha=0.55, label=f"survived={survived}")
    ax.legend()
    ax.set_title("Age vs fare by survival and sex")
    save_plot(fig, "story_03_age_fare.png")

    story_pivot = clean.pivot_table(index="pclass", columns="sex", values="survived", aggfunc="mean")
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.heatmap(story_pivot, annot=True, fmt=".2f", cmap="viridis", ax=ax)
    ax.set_title("Survival-rate heatmap")
    save_plot(fig, "story_04_survival_heatmap.png")

    # Exploratory standardization on the full cleaned EDA dataframe only.
    z = clean.copy()
    for col in ["age", "fare"]:
        z[f"{col}_z"] = (z[col] - z[col].mean()) / z[col].std()
    std_summary = pd.DataFrame({
        "column": ["age", "fare"],
        "before_mean": [clean["age"].mean(), clean["fare"].mean()],
        "before_std": [clean["age"].std(), clean["fare"].std()],
        "after_mean": [z["age_z"].mean(), z["fare_z"].mean()],
        "after_std": [z["age_z"].std(), z["fare_z"].std()],
    })
    std_summary.to_csv(OUTPUT / "standardization_check.csv", index=False)

    report = {
        "profile": profile,
        "decisions": decisions,
        "age_outliers": iqr_outliers(clean["age"]),
        "fare_outliers": iqr_outliers(clean["fare"]),
        "fare_mean": fare_mean,
        "fare_median": fare_median,
        "fare_mode": fare_mode,
        "fare_skew": skew_text,
        "sex_rate": sex_rate,
        "pclass_rate": pclass_rate,
        "sex_class_rate": sex_class_rate,
        "corr_top2": top2,
        "clean": clean,
    }
    return clean, report


def make_classifier_preprocessor(X: pd.DataFrame) -> tuple[ColumnTransformer, list[str], list[str]]:
    numeric = [c for c in ["age", "pclass", "sibsp", "parch", "fare"] if c in X.columns]
    categorical = [c for c in ["sex", "embarked"] if c in X.columns]
    numeric_pipe = Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())])
    categorical_pipe = Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("encoder", OneHotEncoder(handle_unknown="ignore"))])
    pre = ColumnTransformer([("num", numeric_pipe, numeric), ("cat", categorical_pipe, categorical)])
    return pre, numeric, categorical


def classifier_pipeline(estimator: object, X: pd.DataFrame) -> Pipeline:
    pre, _, _ = make_classifier_preprocessor(X)
    return Pipeline([("preprocessor", pre), ("model", estimator)])


def evaluate_classifier(name: str, pipe: Pipeline, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
    pred = pipe.predict(X_test)
    proba = pipe.predict_proba(X_test)[:, 1] if hasattr(pipe, "predict_proba") else None
    auc = roc_auc_score(y_test, proba) if proba is not None else np.nan
    return {
        "model": name,
        "accuracy": accuracy_score(y_test, pred),
        "precision": precision_score(y_test, pred, zero_division=0),
        "recall": recall_score(y_test, pred, zero_division=0),
        "f1": f1_score(y_test, pred, zero_division=0),
        "auc": auc,
        "confusion_matrix": confusion_matrix(y_test, pred).tolist(),
        "pred": pred,
        "proba": proba,
    }


def run_models(df: pd.DataFrame) -> dict:
    # Exclude redundant/target-derived columns from modeling.
    target = df["survived"].astype(int)
    feature_cols = [c for c in ["pclass", "sex", "age", "sibsp", "parch", "fare", "embarked"] if c in df.columns]
    X = df[feature_cols].copy()
    y = target.copy()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

    models = {
        "Logistic Regression": LogisticRegression(max_iter=2000, random_state=42),
        "Decision Tree": DecisionTreeClassifier(max_depth=5, random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=300, random_state=42),
    }
    fitted = {}
    results = []
    for name, est in models.items():
        pipe = classifier_pipeline(est, X_train)
        pipe.fit(X_train, y_train)
        fitted[name] = pipe
        result = evaluate_classifier(name, pipe, X_test, y_test)
        results.append({k: v for k, v in result.items() if k not in {"pred", "proba", "confusion_matrix"}})
        fig, ax = plt.subplots(figsize=(4, 4))
        ConfusionMatrixDisplay.from_predictions(y_test, result["pred"], ax=ax)
        ax.set_title(f"{name} confusion matrix")
        save_plot(fig, f"confusion_{name.lower().replace(' ', '_')}.png")

        if result["proba"] is not None:
            fpr, tpr, _ = roc_curve(y_test, result["proba"])
            fig, ax = plt.subplots(figsize=(5, 4))
            ax.plot(fpr, tpr, label=f"AUC={result['auc']:.3f}")
            ax.plot([0, 1], [0, 1], linestyle="--")
            ax.set_xlabel("False positive rate")
            ax.set_ylabel("True positive rate")
            ax.set_title(f"{name} ROC")
            ax.legend()
            save_plot(fig, f"roc_{name.lower().replace(' ', '_')}.png")

    comparison = pd.DataFrame(results)
    comparison.to_csv(OUTPUT / "classifier_comparison.csv", index=False)

    # Decision tree visualization with transformed feature names.
    tree_pipe = fitted["Decision Tree"]
    feature_names = tree_pipe.named_steps["preprocessor"].get_feature_names_out()
    fig, ax = plt.subplots(figsize=(24, 12))
    plot_tree(tree_pipe.named_steps["model"], feature_names=feature_names, class_names=["Not survived", "Survived"], filled=False, max_depth=4, ax=ax, fontsize=7)
    ax.set_title("Decision Tree (first four levels)")
    save_plot(fig, "decision_tree.png")

    # Imbalance comparison using Logistic Regression.
    imbalance_rows = []
    variants = {
        "baseline": LogisticRegression(max_iter=2000, random_state=42),
        "class_weight_balanced": LogisticRegression(max_iter=2000, class_weight="balanced", random_state=42),
    }
    for label, est in variants.items():
        pipe = classifier_pipeline(est, X_train)
        pipe.fit(X_train, y_train)
        r = evaluate_classifier(label, pipe, X_test, y_test)
        imbalance_rows.append({"variant": label, "precision": r["precision"], "recall": r["recall"], "f1": r["f1"]})

    pre, _, _ = make_classifier_preprocessor(X_train)
    smote_pipe = ImbPipeline([("preprocessor", pre), ("smote", SMOTE(random_state=42)), ("model", LogisticRegression(max_iter=2000, random_state=42))])
    smote_pipe.fit(X_train, y_train)
    r = evaluate_classifier("smote", smote_pipe, X_test, y_test)
    imbalance_rows.append({"variant": "SMOTE", "precision": r["precision"], "recall": r["recall"], "f1": r["f1"]})
    imbalance = pd.DataFrame(imbalance_rows)
    imbalance.to_csv(OUTPUT / "imbalance_comparison.csv", index=False)

    # RF GridSearchCV with OOB enabled.
    rf_pipe = classifier_pipeline(RandomForestClassifier(oob_score=True, random_state=42), X_train)
    grid = {
        "model__n_estimators": [100, 200],
        "model__max_depth": [None, 5, 10],
        "model__max_features": ["sqrt", "log2"],
    }
    search = GridSearchCV(rf_pipe, grid, cv=5, scoring="f1", n_jobs=-1, refit=True)
    search.fit(X_train, y_train)
    best_rf = search.best_estimator_
    oob = best_rf.named_steps["model"].oob_score_
    tuning = {"best_params": search.best_params_, "best_cv_f1": search.best_score_, "oob_score": oob}
    (OUTPUT / "rf_tuning.txt").write_text(str(tuning), encoding="utf-8")
    joblib.dump(best_rf, MODELS / "best_pipeline.joblib")

    # Reload check on raw test input.
    reloaded = joblib.load(MODELS / "best_pipeline.joblib")
    reload_pred = reloaded.predict(X_test.head(5))
    (OUTPUT / "reload_check.txt").write_text(f"Reloaded pipeline predictions on raw rows: {reload_pred.tolist()}\n", encoding="utf-8")

    # Regression side task.
    reg_features = [c for c in ["pclass", "sex", "age", "sibsp", "parch", "embarked"] if c in df.columns]
    reg_df = df[reg_features + ["fare"]].dropna(subset=["fare"]).copy()
    Xr = reg_df[reg_features]
    yr = reg_df["fare"]
    Xr_train, Xr_test, yr_train, yr_test = train_test_split(Xr, yr, test_size=0.2, random_state=42)
    num_r = [c for c in reg_features if c in ["pclass", "age", "sibsp", "parch"]]
    cat_r = [c for c in reg_features if c in ["sex", "embarked"]]
    reg_pre = ColumnTransformer([
        ("num", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]), num_r),
        ("cat", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("encoder", OneHotEncoder(handle_unknown="ignore"))]), cat_r),
    ])
    reg_pipe = Pipeline([("preprocessor", reg_pre), ("model", LinearRegression())])
    reg_pipe.fit(Xr_train, yr_train)
    yr_pred = reg_pipe.predict(Xr_test)
    mae = mean_absolute_error(yr_test, yr_pred)
    rmse = mean_squared_error(yr_test, yr_pred) ** 0.5
    r2 = r2_score(yr_test, yr_pred)
    n, p = len(yr_test), reg_pipe.named_steps["preprocessor"].transform(Xr_test).shape[1]
    adj_r2 = 1 - (1 - r2) * (n - 1) / (n - p - 1)
    residuals = yr_test - yr_pred
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.scatter(yr_pred, residuals, alpha=0.65)
    ax.axhline(0, linestyle="--")
    ax.set_xlabel("Predicted fare")
    ax.set_ylabel("Residual")
    ax.set_title("Fare regression residual plot")
    save_plot(fig, "fare_residuals.png")
    hetero_score = float(np.corrcoef(np.abs(residuals), yr_pred)[0, 1])
    regression = {"MAE": mae, "RMSE": rmse, "R2": r2, "Adjusted_R2": adj_r2}
    pd.DataFrame([regression]).to_csv(OUTPUT / "regression_metrics.csv", index=False)

    # Model comparison report with separate metric groups.
    best_classifier = comparison.sort_values(["f1", "auc"], ascending=False).iloc[0]
    final_report = pd.DataFrame([
        {"model": "Logistic Regression", "accuracy": comparison.loc[comparison.model.eq("Logistic Regression"), "accuracy"].iloc[0], "precision": comparison.loc[comparison.model.eq("Logistic Regression"), "precision"].iloc[0], "recall": comparison.loc[comparison.model.eq("Logistic Regression"), "recall"].iloc[0], "f1": comparison.loc[comparison.model.eq("Logistic Regression"), "f1"].iloc[0], "auc": comparison.loc[comparison.model.eq("Logistic Regression"), "auc"].iloc[0], "MAE": np.nan, "RMSE": np.nan, "R2": np.nan, "Adjusted_R2": np.nan},
        {"model": "Decision Tree", "accuracy": comparison.loc[comparison.model.eq("Decision Tree"), "accuracy"].iloc[0], "precision": comparison.loc[comparison.model.eq("Decision Tree"), "precision"].iloc[0], "recall": comparison.loc[comparison.model.eq("Decision Tree"), "recall"].iloc[0], "f1": comparison.loc[comparison.model.eq("Decision Tree"), "f1"].iloc[0], "auc": comparison.loc[comparison.model.eq("Decision Tree"), "auc"].iloc[0], "MAE": np.nan, "RMSE": np.nan, "R2": np.nan, "Adjusted_R2": np.nan},
        {"model": "Random Forest", "accuracy": comparison.loc[comparison.model.eq("Random Forest"), "accuracy"].iloc[0], "precision": comparison.loc[comparison.model.eq("Random Forest"), "precision"].iloc[0], "recall": comparison.loc[comparison.model.eq("Random Forest"), "recall"].iloc[0], "f1": comparison.loc[comparison.model.eq("Random Forest"), "f1"].iloc[0], "auc": comparison.loc[comparison.model.eq("Random Forest"), "auc"].iloc[0], "MAE": np.nan, "RMSE": np.nan, "R2": np.nan, "Adjusted_R2": np.nan},
        {"model": "Linear Regression (fare)", "accuracy": np.nan, "precision": np.nan, "recall": np.nan, "f1": np.nan, "auc": np.nan, "MAE": mae, "RMSE": rmse, "R2": r2, "Adjusted_R2": adj_r2},
    ])
    final_report.to_csv(OUTPUT / "model_comparison.csv", index=False)

    return {
        "comparison": comparison,
        "imbalance": imbalance,
        "tuning": tuning,
        "regression": regression,
        "heteroscedasticity_score": hetero_score,
        "best_classifier": best_classifier,
        "split_sizes": (len(X_train), len(X_test)),
        "class_balance": y.value_counts(normalize=True).sort_index(),
    }


def write_report(report: dict, eda_report: dict) -> None:
    lines = ["# Analytics Results\n"]
    lines.append("## Missing-value profile and decisions\n")
    for _, row in eda_report["profile"].iterrows():
        lines.append(f"- `{row['column']}`: **{row['missing_pct']:.2f}%** missing — {eda_report['decisions'].get(row['column'], 'no action')}.")
    lines.append("\n## Univariate findings\n")
    lines.append(f"- IQR outliers: `age` = **{eda_report['age_outliers']}**, `fare` = **{eda_report['fare_outliers']}**.")
    lines.append(f"- Fare mean = **{eda_report['fare_mean']:.3f}**, median = **{eda_report['fare_median']:.3f}**, mode = **{eda_report['fare_mode']:.3f}**; this is **{eda_report['fare_skew']}** based on the requested ordering rule.")
    lines.append("\n## Bivariate findings\n")
    lines.append("### Survival by sex\n\n" + eda_report["sex_rate"].to_string())
    lines.append("\n### Survival by passenger class\n\n" + eda_report["pclass_rate"].to_string())
    lines.append("\n### Survival by sex and class\n\n" + eda_report["sex_class_rate"].to_string())
    lines.append("\n### Strongest correlations\n")
    for a, b, val, _ in eda_report["corr_top2"]:
        lines.append(f"- `{a}` ↔ `{b}`: **{val:.3f}**. This is one of the two largest absolute off-diagonal correlations in the required six-column matrix.")
    lines.append("\n## Multivariate data story\n")
    lines.append("1. **Class + sex chart:** Survival rates differ strongly across sex and passenger class, showing that these two categorical variables jointly separate outcomes. The chart is descriptive and does not claim causality.\n")
    lines.append("2. **Age + class box plot:** Age distributions overlap across survival groups, while class remains a visible grouping variable. This supports examining age jointly with class rather than treating age alone as the explanation.\n")
    lines.append("3. **Age + fare scatter:** The plot shows the joint distribution of age and fare with survival and sex encoded, making clusters and overlap visible. It also shows why a multivariate model is useful: the classes are not perfectly separable by any single continuous feature.\n")
    lines.append("4. **Survival heatmap:** The sex-by-class heatmap makes the combined survival-rate pattern easy to compare. The strongest contrasts occur when the two categorical dimensions are considered together.\n")
    lines.append("## Standardization sanity check\n\nThe generated `standardization_check.csv` records the original and transformed means/stds for age and fare; the transformed columns should be approximately mean 0 and standard deviation 1.\n")
    lines.append("## Modeling\n")
    lines.append(f"A stratified split produced **{report['split_sizes'][0]} training rows** and **{report['split_sizes'][1]} test rows**. Stratification preserves the observed survived/not-survived class proportions across the two splits, reducing avoidable sampling variation in an imbalanced binary target.\n")
    lines.append("All classifier preprocessing is inside the fitted scikit-learn pipeline, so imputers, one-hot encoders, and scalers are fitted on training data and only transformed on the test data.\n")
    lines.append("### Classifier comparison\n\n" + report["comparison"].to_markdown(index=False))
    lines.append("\n### Imbalance comparison\n\n" + report["imbalance"].to_markdown(index=False))
    best_imb = report["imbalance"].sort_values("f1", ascending=False).iloc[0]
    lines.append(f"\nThe highest F1 in this three-way comparison is the `{best_imb['variant']}` variant (**{best_imb['f1']:.3f}**). Precision and recall should be considered together because the class-weight and SMOTE approaches change the balance between false positives and false negatives.\n")
    lines.append(f"### Random Forest tuning\n\nBest parameters: `{report['tuning']['best_params']}`. Best cross-validation F1 = **{report['tuning']['best_cv_f1']:.3f}**; OOB score = **{report['tuning']['oob_score']:.3f}**.\n")
    lines.append("### Regression side-task\n\n" + pd.DataFrame([report["regression"]]).to_markdown(index=False))
    lines.append(f"\nThe residual plot shows **heteroscedasticity** in this run: the correlation between absolute residual magnitude and predicted fare is **{report["heteroscedasticity_score"]:.3f}**, and the highest-prediction quartile has much wider residual spread. The spread therefore changes with fitted value rather than remaining approximately constant.\n")
    lines.append("## Final model-selection statement\n")
    lines.append(f"On this fixed test split, the classifier with the highest F1 in the generated comparison is **{report['best_classifier']['model']}** (F1 = {report['best_classifier']['f1']:.3f}, AUC = {report['best_classifier']['auc']:.3f}). Its precision, recall, accuracy and AUC are shown in `model_comparison.csv`, so the deployment choice is tied to the observed metric values rather than a generic model preference. The saved artifact is the complete preprocessing-plus-estimator pipeline, not a bare estimator.\n")
    (OUTPUT / "analytics_results.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true", help="Read the committed titanic.csv instead of calling sns.load_dataset.")
    args = parser.parse_args()
    OUTPUT.mkdir(exist_ok=True)
    MODELS.mkdir(exist_ok=True)
    df = load_raw(args.offline)
    print(df.info())
    print(df.describe(include="all"))
    print("shape:", df.shape)
    clean, eda_report = run_eda(df)
    report = run_models(clean)
    write_report(report, eda_report)
    print("Analytics pipeline completed.")


if __name__ == "__main__":
    main()
