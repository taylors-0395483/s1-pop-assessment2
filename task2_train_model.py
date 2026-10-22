# Task 2: Model Training, Evaluation and Export

from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier


def main():
    # Step 1: Load the Task 1 dataset to predict Grid_Status_Label.
    folder = Path(__file__).resolve().parent
    df = pd.read_csv(folder / "0_ev_campus_dataset.csv")

    # Step 2: Select inputs; the session ID and target must not be inputs.
    feature_columns = [
        "Charger_Type",
        "User_Type",
        "Start_Hour",
        "Duration_Mins",
        "Energy_kWh",
        "Overstay_Mins",
        "Battery_Temp_C",
        "Power_kW",
        "Peak_Hour_Flag",
    ]
    categorical_columns = ["Charger_Type", "User_Type"]
    required_columns = feature_columns + ["Grid_Status_Label"]
    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        raise ValueError(f"Run task1_data_pipeline.py first. Missing columns: {sorted(missing_columns)}")
    if df[required_columns].isna().any().any():
        raise ValueError("Missing values remain. Run task1_data_pipeline.py first.")

    X = df[feature_columns]
    y = df["Grid_Status_Label"]
    numeric_columns = [column for column in feature_columns if column not in categorical_columns]
    if not np.isfinite(X[numeric_columns].to_numpy(dtype=float)).all():
        raise ValueError("Numeric inputs must contain finite values.")

    print("Input features:")
    print(", ".join(feature_columns))
    print("\nTarget class counts:")
    print(y.value_counts().to_string())

    # Step 3: Split 80/20 while preserving class proportions.
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Learn dummy columns from training data and align test columns to them.
    X_train = pd.get_dummies(X_train, columns=categorical_columns, dtype=int)
    X_test = pd.get_dummies(X_test, columns=categorical_columns, dtype=int)
    X_test = X_test.reindex(columns=X_train.columns, fill_value=0)
    print(f"\nTraining records: {len(X_train)}")
    print(f"Test records: {len(X_test)}")
    assert X_train.index.intersection(X_test.index).empty, "Train and test rows overlap."

    # Step 4: Compare two basic classifiers without parameter tuning.
    models = {
        "Decision Tree": DecisionTreeClassifier(random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42),
    }
    labels = sorted(y.unique())
    results = []
    figure, axes = plt.subplots(1, 2, figsize=(13, 5))

    # Step 5: Train each model on training data only.
    for axis, (name, model) in zip(axes, models.items()):
        model.fit(X_train, y_train)
        predictions = model.predict(X_test)

        # Step 6: Evaluate on the same held-out test set for a fair comparison.
        # Macro averages give equal weight to each status, including rare ones.
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_test, predictions, average="macro", zero_division=0
        )
        results.append({
            "Model": name,
            "Accuracy": accuracy_score(y_test, predictions),
            "Precision_Macro": precision,
            "Recall_Macro": recall,
            "F1_Macro": f1,
        })
        print(f"\n{name} - per-class evaluation:")
        print(classification_report(y_test, predictions, labels=labels, zero_division=0))

        matrix = confusion_matrix(y_test, predictions, labels=labels)
        sns.heatmap(
            matrix, annot=True, fmt="d", cmap="Blues", cbar=False,
            xticklabels=labels, yticklabels=labels, ax=axis,
        )
        axis.set_title(name)
        axis.set_xlabel("Predicted status")
        axis.set_ylabel("Actual status")
        axis.tick_params(axis="x", rotation=20)
        axis.tick_params(axis="y", rotation=0)

    figure.tight_layout()
    chart_file = folder / "task2_confusion_matrices.png"
    figure.savefig(chart_file, dpi=150)
    plt.close(figure)

    # Rank by macro F1, then accuracy; retain model order if both scores tie.
    comparison = pd.DataFrame(results).sort_values(
        ["F1_Macro", "Accuracy"], ascending=False, kind="stable"
    ).reset_index(drop=True)
    comparison_file = folder / "task2_model_comparison.csv"
    comparison.to_csv(comparison_file, index=False)
    best_name = comparison.loc[0, "Model"]
    best_model = models[best_name]
    print("\nModel comparison (scores from 0 to 1):")
    print(comparison.round(4).to_string(index=False))
    print(f"\nSelected model: {best_name} (highest macro F1, then accuracy)")

    # Step 7: Save the fitted model and encoding columns for the Streamlit app.
    # Keep the evaluated 80%-trained model; do not retrain it on the test data.
    model_file = folder / "task2_ev_model.pkl"
    joblib.dump({
        "model": best_model,
        "model_name": best_name,
        "feature_columns": X_train.columns.tolist(),
        "input_columns": feature_columns,
        "categorical_columns": categorical_columns,
        "labels": labels,
    }, model_file)

    # Confirm that saving and loading preserves the model's predictions.
    saved = joblib.load(model_file)
    loaded_predictions = saved["model"].predict(X_test[saved["feature_columns"]])
    assert np.array_equal(loaded_predictions, best_model.predict(X_test))
    print("\nSample predictions from the saved model:")
    print(pd.DataFrame({
        "Actual": y_test.to_numpy()[:5],
        "Predicted": loaded_predictions[:5],
    }).to_string(index=False))

    print(f"\nSaved model and encoding information: {model_file}")
    print(f"Saved model comparison: {comparison_file}")
    print(f"Saved confusion matrices: {chart_file}")


# Run training only when this file is executed directly.
if __name__ == "__main__":
    main()
