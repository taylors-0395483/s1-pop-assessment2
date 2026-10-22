# EV Campus Analytics

Taylor's Principles of Programming — Assessment 2 group project. This project prepares EV charging data, compares two classification models, and presents the results in a bilingual Streamlit app.

[中文说明](README.zh-CN.md)

## Project files

| File | Purpose |
| --- | --- |
| `0_ev_campus_dataset.csv` | Working dataset: 1,200 sessions, already cleaned, with charging power and peak-hour features. |
| `task1_data_pipeline.py` | Fill numeric missing values with medians, remove duplicate session IDs, calculate features, and print grouped statistics. |
| `task2_train_model.py` | Train and evaluate Decision Tree and Random Forest classifiers using an 80/20 split. |
| `task2_ev_model.pkl` | Selected Random Forest model and the input/encoding information needed for predictions. |
| `task2_model_comparison.csv` | Accuracy and macro precision, recall, and F1 scores for both models. |
| `task2_confusion_matrices.png` | Confusion matrices for both models on the test set. |
| `task3_app.py` | Dashboard, visual analytics, and live predictions, with English and Chinese interfaces. |
| `requirements.txt` | Python package versions for local installation and cloud deployment. |
| `packages.txt` | Chinese font package for charts on Streamlit Community Cloud. |

## Run locally

Use Python 3.12. In a terminal, open this project folder and install the versions used for the saved model and local app:

```bash
python -m pip install -r requirements.txt
```

The prepared dataset and trained model are included, so you can start the app directly:

```bash
python -m streamlit run task3_app.py
```

Open the local URL printed in the terminal. To stop the app, press `Ctrl+C`.

In PyCharm, select the same Python environment and run `task3_app.py` as a normal Python script. It starts Streamlit automatically; use **Run**, rather than a unit-test configuration.

## Re-run Tasks 1 and 2

These steps are optional when using the included data and model. To regenerate the results, run them in order:

```bash
python task1_data_pipeline.py
python task2_train_model.py
```

Task 1 **overwrites `0_ev_campus_dataset.csv`**. The included CSV is already processed, so its original missing values will not reappear when the script is run again. Task 2 overwrites its three output files. Restart the app after replacing the data or model so its cache is refreshed.

## Use the app

- **Executive KPI Dashboard:** filter charging records, view energy, duration and estimated revenue, and download the filtered CSV.
- **Visual Analytics Studio:** view energy versus battery temperature, charger counts, and average energy during peak and off-peak periods.
- **Live ML Prediction:** enter charging details and select **Predict status** to predict `Normal`, `Grid_Surge`, or `Overheated`.
- Use the language selector at the top right to switch between English and Chinese. CSV downloads retain the original field names and category codes.

Operation records beginning with `[TASK3]` appear in the terminal or PyCharm console, including filter changes, chart rendering, download requests and submitted predictions. They are not saved to a separate log file.

## Deploy to Streamlit Community Cloud

After pushing the project files, `requirements.txt` and `packages.txt` to GitHub:

1. Sign in at [Streamlit Community Cloud](https://share.streamlit.io/) and select **Create app** → **Yup, I have an app**.
2. Set the repository to `taylors-0395483/s1-pop-assessment2`, branch to `main`, and main file path to `task3_app.py`.
3. In **Advanced settings**, select **Python 3.12**. This app does not require API keys or secrets.
4. Select **Deploy** and wait for the installation to finish. Community Cloud reads both dependency files and starts the app; do not run the cleaning or training scripts during deployment.
5. Open the generated URL and check both languages, filters, CSV download, all three charts, and a submitted prediction.

`packages.txt` installs the WenQuanYi Zen Hei Chinese font on the cloud's Linux system. The app already selects this font when available. It also uses Matplotlib's `Agg` backend, which does not require a desktop GUI.

See the official [deployment instructions](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy) and [dependency instructions](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies).

## Rules and current results

- Average charging power: `Power_kW = Energy_kWh / (Duration_Mins / 60)`.
- Peak hours: **12:00–17:00**, using session overlap. AC/DC are the existing charger groups; no additional efficiency category is generated.
- Revenue is an estimate based on Assessment 1 tariffs and the fields available in the dataset. Carbon savings require a user-entered factor; the optional temperature alert also requires a user-entered threshold.

| Model | Test accuracy | Macro F1 |
| --- | --- | --- |
| Random Forest | 85.00% | 0.7674 |
| Decision Tree | 83.75% | 0.7444 |

Only the selected Random Forest is saved in the model file. Predictions can be incorrect, particularly for `Grid_Surge`. The app currently runs locally; cloud deployment and the demonstration video remain to be completed.
