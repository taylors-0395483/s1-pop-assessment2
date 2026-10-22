# Task 1: Data Cleaning, Feature Engineering and Statistical Aggregation

from pathlib import Path

import numpy as np
import pandas as pd


def main():
    # Locate the CSV in the same folder as this script.
    folder = Path(__file__).resolve().parent
    input_file = folder / "0_ev_campus_dataset.csv"

    # Load the data and record the row count before cleaning.
    df = pd.read_csv(input_file)
    original_rows = len(df)

    # Use the existing AC/DC categories for this assignment's grouping.
    # Remove any separate efficiency labels created by an earlier run.
    df = df.drop(columns=["Efficiency_Group"], errors="ignore")

    # Display the data size and missing values before cleaning.
    print("Before cleaning - rows and columns:")
    print(df.shape)

    print("\nMissing values before cleaning:")
    print(df.isna().sum())

    # Count repeated rows and repeated session IDs separately.
    print("\nDuplicate records before cleaning:")
    print(df.duplicated().sum())

    print("\nDuplicate Session_ID values before cleaning:")
    print(df["Session_ID"].duplicated().sum())

    # Keep one record per session before calculating column medians.
    if df["Session_ID"].isna().any():
        raise ValueError("Session_ID must not be missing.")
    df = df.drop_duplicates(subset="Session_ID", keep="first")

    # Select numeric columns for median-based filling.
    numeric_columns = df.select_dtypes(include="number").columns
    for column in numeric_columns:
        missing_count = df[column].isna().sum()
        if missing_count > 0:
            # Fill missing values using this column's median.
            median_value = df[column].median()
            df[column] = df[column].fillna(median_value)
            print(f"\n{column}: filled {missing_count} missing values with median {median_value}")

    # Stop before saving if numeric missing values or duplicate IDs remain.
    assert not df[numeric_columns].isna().any().any(), "Numeric missing values remain."
    assert not df["Session_ID"].duplicated().any(), "Duplicate session IDs remain."

    # Reject invalid measurements instead of saving infinite or negative power.
    if not np.isfinite(df[numeric_columns].to_numpy()).all():
        raise ValueError("Numeric columns must contain finite values.")
    if (df["Duration_Mins"] <= 0).any() or (df["Energy_kWh"] < 0).any():
        raise ValueError("Duration must be positive and energy must not be negative.")
    if not df["Start_Hour"].between(0, 23).all():
        raise ValueError("Start_Hour must be between 0 and 23.")
    if not df["Charger_Type"].isin(["AC", "DC"]).all():
        raise ValueError("Charger_Type must be AC or DC.")

    # Convert minutes to hours and calculate average charging power in kW.
    df["Power_kW"] = df["Energy_kWh"] / (df["Duration_Mins"] / 60)

    # Assessment 2 defines peak hours as 12:00-17:00, unlike Assessment 1.
    # Follow Assessment 1's overlap rule, using the supplied whole-hour start.
    peak_start = 12
    peak_end = 17
    end_hour = df["Start_Hour"] + df["Duration_Mins"] / 60
    overlaps_today = (df["Start_Hour"] < peak_end) & (end_hour > peak_start)
    overlaps_next_day = end_hour > (24 + peak_start)
    df["Peak_Hour_Flag"] = (overlaps_today | overlaps_next_day).astype(int)

    # Check the engineered features before overwriting the CSV.
    assert np.isfinite(df["Power_kW"]).all(), "Invalid charging power remains."
    assert df["Peak_Hour_Flag"].isin([0, 1]).all(), "Invalid peak-hour flags."

    # Display the cleaning results for verification.
    print("\nMissing values after cleaning:")
    print(df.isna().sum())

    print(f"\nRemoved duplicate sessions: {original_rows - len(df)}")
    print(f"Rows after cleaning: {len(df)}")

    print("\nSample engineered features:")
    print(df[["Session_ID", "Charger_Type", "Power_kW", "Peak_Hour_Flag"]].head().to_string(index=False))

    # Use Battery_Temp_C because the supplied CSV has no Ambient_Temp_C column.
    # Print summary tables without creating extra CSV files.
    for group_columns in [["Charger_Type"], ["Peak_Hour_Flag"], ["Charger_Type", "Peak_Hour_Flag"]]:
        summary = df.groupby(group_columns)[["Energy_kWh", "Battery_Temp_C"]].mean()
        summary.columns = ["Mean_Energy_kWh", "Mean_Battery_Temp_C"]
        print(f"\nMean energy and battery temperature by {', '.join(group_columns)}:")
        print(summary.round(2).to_string())

    # Overwrite the same CSV without adding a DataFrame index column.
    df.to_csv(input_file, index=False)
    print(f"\nSaved cleaned data back to: {input_file}")


# Run the pipeline only when this file is executed directly.
if __name__ == "__main__":
    main()
