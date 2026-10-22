# Task 3: Interactive Streamlit Dashboard, Charts and Model Predictions

from datetime import datetime
import json
from math import ceil
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

import joblib
import matplotlib

# Streamlit draws on worker threads, so use a backend without a desktop GUI.
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st


def log_event(event, **details):
    # Print one readable operation record to the PyCharm console, not a new file.
    if "_log_session" not in st.session_state:
        st.session_state["_log_session"] = uuid4().hex[:8]
    sequence = st.session_state.get("_log_sequence", 0) + 1
    st.session_state["_log_sequence"] = sequence
    timestamp = datetime.now(ZoneInfo("Asia/Kuala_Lumpur")).strftime("%Y-%m-%d %H:%M:%S")
    details_json = json.dumps(details, ensure_ascii=False, sort_keys=True, default=str)
    print(f"{timestamp} [TASK3] session={st.session_state['_log_session']} step={sequence} {event} {details_json}", flush=True)


def log_change(event, **details):
    # Skip duplicate state records caused by unrelated Streamlit reruns.
    snapshots = st.session_state.setdefault("_log_snapshots", {})
    current = json.dumps(details, ensure_ascii=False, sort_keys=True, default=str)
    if snapshots.get(event) != current:
        log_event(event, **details)
        snapshots[event] = current


# Keep the prepared Chinese text beside the original English text.
CHINESE = {
    "EV Campus Analytics": "校园电动汽车充电分析",
    "Taylor's Smart Campus | Charging data, visual analysis and status predictions": "泰莱智慧校园｜充电数据、图表分析与状态预测",
    "Navigation": "页面导航",
    "Executive KPI Dashboard": "数据概览",
    "Visual Analytics Studio": "图表分析",
    "Live ML Prediction": "状态预测",
    "Live Machine Learning Prediction": "充电状态预测",
    "Total energy (kWh)": "总充电量（kWh）",
    "Average duration (minutes)": "平均充电时长（分钟）",
    "Estimated peak revenue (RM)": "估算高峰收入（RM）",
    "Estimated carbon savings (kg CO2)": "估算碳减排量（kg CO2）",
    "Not configured": "未设置",
    "Delta values compare the filtered selection with the full dataset, not a previous date.": "变化值表示筛选结果与全部数据的差额，不是与上一日期比较。",
    "How the estimates are calculated": "估算方法说明",
    "Peak revenue is the sum of estimated session fees for sessions overlapping 12:00-17:00. Fees use Assessment 1 hourly tiers, rounded-up hours, fee caps, Staff and Student discounts, RM 5 peak surcharge and RM 15 idle surcharge when overstay is greater than zero.": "高峰收入是充电过程与 12:00–17:00 重叠的各次充电估算费用之和。采用 Assessment 1 的阶梯时薪、时长向上取整、费用上限及教职工和学生折扣，另计 RM 5 高峰附加费；超时停车大于零时加收 RM 15。",
    "First-time waivers, Eco-Pass discounts and RFID replacement fees are excluded because their fields are unavailable. These estimates are not actual receipts.": "数据没有首次充电、Eco-Pass 和补卡记录，因此不计首次免费、Eco-Pass 折扣及补卡费。结果为估算费用，不是实际收款。",
    "Carbon savings = selected energy (kWh) multiplied by the net savings factor entered in the sidebar. No factor is assumed by default.": "碳减排量＝所选记录的充电量（kWh）× 侧栏输入的净减排系数。默认不设置系数。",
    "Filtered charging records": "筛选后的充电记录",
    "Showing {selected:,} of {total:,} sessions. Peak flag: 1 = peak, 0 = off-peak.": "当前显示 {selected:,} / {total:,} 条记录。高峰标记：1＝高峰，0＝非高峰。",
    "Download filtered CSV": "下载筛选结果 CSV",
    "CSV downloads keep the original field names and category codes.": "下载的 CSV 保留原始字段名和类别代码。",
    "All charts use the same {count:,} filtered sessions.": "所有图表均使用当前筛选的 {count:,} 条记录。",
    "Energy and battery temperature": "充电量与电池温度",
    "Energy delivered (kWh)": "充电量（kWh）",
    "Battery temperature (°C)": "电池温度（°C）",
    "Charger type distribution": "充电桩类型分布",
    "Charger type": "充电桩类型",
    "Number of sessions": "充电次数",
    "Average energy: peak and off-peak": "高峰与非高峰的平均充电量",
    "Charging period (peak: 12:00-17:00)": "充电时段（高峰：12:00–17:00）",
    "Average energy per session (kWh)": "每次平均充电量（kWh）",
    "Model file missing. Run task2_train_model.py first.": "未找到模型文件，请先运行 task2_train_model.py。",
    "Saved model: {model}. Predictions can be incorrect, especially for Grid_Surge.": "已保存模型：{model}。预测可能有误，尤其是电网负荷突增类别。",
    "Charging inputs": "充电参数",
    "User type": "用户类型",
    "Start hour": "开始时间（小时）",
    "Duration (minutes)": "充电时长（分钟）",
    "Energy (kWh)": "充电量（kWh）",
    "Overstay (minutes)": "超时停车（分钟）",
    "Predict status": "预测状态",
    "Enter charging details in the sidebar, then select Predict status.": "请在侧栏填写充电参数，然后点击“预测状态”。",
    "Predicted status: {status}": "预测状态：{status}",
    "Calculated power (kW)": "计算功率（kW）",
    "Charging period": "充电时段",
    "Overstay recorded at or above your selected temperature alert threshold.": "存在超时停车，且温度达到或超过你设置的提醒阈值。",
    "Optional analysis settings": "可选分析设置",
    "Net carbon savings factor (kg CO2/kWh)": "净碳减排系数（kg CO2/kWh）",
    "Net emissions avoided per kWh relative to your chosen baseline.": "相对于所选基准，每 kWh 减少的净碳排放量。",
    "Temperature alert threshold (°C)": "温度提醒阈值（°C）",
    "Optional threshold for flagging overstays at high temperatures.": "用于提醒高温超时停车的可选阈值。",
    "Historical data filters": "历史数据筛选",
    "Minimum energy (kWh)": "最低充电量（kWh）",
    "No sessions match these filters. Adjust the sidebar selection.": "没有符合筛选条件的记录，请调整侧栏选项。",
    "{count} filtered sessions have an overstay at or above your temperature threshold.": "当前有 {count} 条记录存在超时停车，且温度达到或超过你设置的阈值。",
    "Run task1_data_pipeline.py to prepare the dataset first.": "请先运行 task1_data_pipeline.py 准备数据。",
    "Missing values remain. Run task1_data_pipeline.py first.": "数据仍有缺失值，请先运行 task1_data_pipeline.py。",
    "The dataset contains invalid numeric values.": "数据中存在无效数值。",
    "Data file missing: 0_ev_campus_dataset.csv": "未找到数据文件：0_ev_campus_dataset.csv",
    "AC": "AC（交流）", "DC": "DC（直流）",
    "Staff": "教职工", "Student": "学生", "Visitor": "访客",
    "All": "全部", "Peak": "高峰", "Off-peak": "非高峰",
    "Normal": "正常", "Overheated": "过热", "Grid_Surge": "电网负荷突增",
    "Random Forest": "随机森林", "Decision Tree": "决策树",
    "Session_ID": "充电记录编号", "Charger_Type": "充电桩类型",
    "User_Type": "用户类型", "Start_Hour": "开始时间（小时）",
    "Duration_Mins": "充电时长（分钟）", "Energy_kWh": "充电量（kWh）",
    "Overstay_Mins": "超时停车（分钟）", "Battery_Temp_C": "电池温度（°C）",
    "Grid_Status_Label": "充电状态", "Power_kW": "平均功率（kW）",
    "Peak_Hour_Flag": "高峰标记", "Estimated_Fee_RM": "估算费用（RM）",
}


def t(english, **values):
    # Translate presentation text without changing data or model category codes.
    text = CHINESE.get(english, english) if st.session_state.get("language") == "中文" else english
    return text.format(**values) if values else text


def option_labels(options):
    # Capture labels now so widget values stay stable when the language changes.
    return {value: t(value) for value in options}.get


def display_data(df):
    # Translate a display copy; downloads and prediction inputs keep original codes.
    displayed = df.copy()
    for column in ["Charger_Type", "User_Type", "Grid_Status_Label"]:
        if column in displayed.columns:
            displayed[column] = displayed[column].map(t)
    return displayed.rename(columns={column: t(column) for column in displayed.columns})


def estimate_fee(row):
    # Apply Assessment 1 rates to the fields available in the dataset.
    hours = ceil(row["Duration_Mins"] / 60)
    if row["Charger_Type"] == "AC":
        rate_1, rate_2, rate_3, overtime_rate, fee_cap = 4, 6, 8, 12, 80
    else:
        rate_1, rate_2, rate_3, overtime_rate, fee_cap = 10, 15, 20, 30, 150

    gross_fee = (
        min(hours, 2) * rate_1
        + min(max(hours - 2, 0), 2) * rate_2
        + min(max(hours - 4, 0), 2) * rate_3
        + max(hours - 6, 0) * overtime_rate
    )
    gross_fee = min(gross_fee, fee_cap)
    if row["User_Type"] == "Staff":
        gross_fee *= 0.50
    elif row["User_Type"] == "Student" and row["Charger_Type"] == "AC":
        gross_fee *= 0.75

    # Use Assessment 2's peak flag; unknown waivers and fees are excluded.
    peak_fee = 5 if row["Peak_Hour_Flag"] == 1 else 0
    idle_fee = 15 if row["Overstay_Mins"] > 0 else 0
    return round(gross_fee + peak_fee + idle_fee, 2)


@st.cache_data
def load_data():
    # Cache the prepared data without writing changes back to the CSV.
    folder = Path(__file__).resolve().parent
    df = pd.read_csv(folder / "0_ev_campus_dataset.csv")
    required = [
        "Charger_Type", "User_Type", "Start_Hour", "Duration_Mins",
        "Energy_kWh", "Overstay_Mins", "Battery_Temp_C", "Power_kW",
        "Peak_Hour_Flag", "Grid_Status_Label",
    ]
    if df.empty or not set(required).issubset(df.columns):
        raise ValueError("Run task1_data_pipeline.py to prepare the dataset first.")
    if df[required].isna().any().any():
        raise ValueError("Missing values remain. Run task1_data_pipeline.py first.")
    numeric = df[required].select_dtypes(include="number")
    if not np.isfinite(numeric.to_numpy()).all() or (df["Duration_Mins"] <= 0).any():
        raise ValueError("The dataset contains invalid numeric values.")
    df["Estimated_Fee_RM"] = df.apply(estimate_fee, axis=1)
    return df


@st.cache_resource
def load_model():
    # Reuse the saved Task 2 model instead of retraining on page reruns.
    folder = Path(__file__).resolve().parent
    return joblib.load(folder / "task2_ev_model.pkl")


def build_prediction_input(charger, user, start, duration, energy, overstay, temperature):
    # Derive the same power and peak features used in Task 1.
    if duration <= 0 or energy < 0 or overstay < 0 or not 0 <= start <= 23:
        raise ValueError("Check the charging duration, energy, overstay and start hour.")
    end_hour = start + duration / 60
    peak_flag = int((start < 17 and end_hour > 12) or end_hour > 36)
    return pd.DataFrame([{
        "Charger_Type": charger,
        "User_Type": user,
        "Start_Hour": start,
        "Duration_Mins": duration,
        "Energy_kWh": energy,
        "Overstay_Mins": overstay,
        "Battery_Temp_C": temperature,
        "Power_kW": energy / (duration / 60),
        "Peak_Hour_Flag": peak_flag,
    }])


def show_dashboard(df, filtered, carbon_factor):
    st.header(t("Executive KPI Dashboard"))
    peak_revenue = filtered.loc[filtered["Peak_Hour_Flag"] == 1, "Estimated_Fee_RM"].sum()
    full_peak_revenue = df.loc[df["Peak_Hour_Flag"] == 1, "Estimated_Fee_RM"].sum()
    energy, duration, revenue, carbon = st.columns(4)
    energy.metric(t("Total energy (kWh)"), f"{filtered['Energy_kWh'].sum():,.2f}")
    duration.metric(t("Average duration (minutes)"), f"{filtered['Duration_Mins'].mean():.1f}")
    revenue.metric(
        t("Estimated peak revenue (RM)"), f"{peak_revenue:,.2f}",
        delta=f"RM {peak_revenue - full_peak_revenue:,.2f}", delta_color="off",
    )
    if carbon_factor is None:
        carbon.metric(t("Estimated carbon savings (kg CO2)"), t("Not configured"))
    else:
        savings = filtered["Energy_kWh"].sum() * carbon_factor
        full_savings = df["Energy_kWh"].sum() * carbon_factor
        carbon.metric(
            t("Estimated carbon savings (kg CO2)"), f"{savings:,.2f}",
            delta=f"{savings - full_savings:,.2f} kg CO2", delta_color="off",
        )
    st.caption(t("Delta values compare the filtered selection with the full dataset, not a previous date."))

    with st.expander(t("How the estimates are calculated")):
        st.write(t(
            "Peak revenue is the sum of estimated session fees for sessions overlapping "
            "12:00-17:00. Fees use Assessment 1 hourly tiers, rounded-up hours, fee caps, "
            "Staff and Student discounts, RM 5 peak surcharge and RM 15 idle surcharge "
            "when overstay is greater than zero."
        ))
        st.write(t(
            "First-time waivers, Eco-Pass discounts and RFID replacement fees are excluded "
            "because their fields are unavailable. These estimates are not actual receipts."
        ))
        st.write(t(
            "Carbon savings = selected energy (kWh) multiplied by the net savings factor "
            "entered in the sidebar. No factor is assumed by default."
        ))

    st.subheader(t("Filtered charging records"))
    st.caption(t("Showing {selected:,} of {total:,} sessions. Peak flag: 1 = peak, 0 = off-peak.", selected=len(filtered), total=len(df)))
    st.dataframe(display_data(filtered), hide_index=True)
    st.caption(t("CSV downloads keep the original field names and category codes."))
    st.download_button(
        t("Download filtered CSV"), data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="task3_filtered_data.csv", mime="text/csv", key="download_filtered",
        on_click=log_event, args=("CSV_DOWNLOAD_REQUESTED",),
        kwargs={"file": "task3_filtered_data.csv", "rows": len(filtered),
                "columns": filtered.columns.tolist(), "language": st.session_state["language"]},
    )
    log_change(
        "DASHBOARD_RENDERED", rows=len(filtered),
        total_energy_kWh=round(float(filtered["Energy_kWh"].sum()), 2),
        average_duration_mins=round(float(filtered["Duration_Mins"].mean()), 1),
        estimated_peak_revenue_RM=round(float(peak_revenue), 2),
        carbon_factor=carbon_factor,
        carbon_savings_kg=None if carbon_factor is None else round(float(savings), 2),
        language=st.session_state["language"],
    )


def show_charts(filtered):
    log_event("CHARTS_STARTED", rows=len(filtered), language=st.session_state["language"])
    st.header(t("Visual Analytics Studio"))
    st.caption(t("All charts use the same {count:,} filtered sessions.", count=len(filtered)))
    left, right = st.columns(2)
    with left:
        st.subheader(t("Energy and battery temperature"))
        figure, axis = plt.subplots(figsize=(7, 5))
        sns.scatterplot(
            data=filtered, x="Energy_kWh", y="Battery_Temp_C",
            hue="Charger_Type", alpha=0.65, ax=axis,
        )
        axis.set_xlabel(t("Energy delivered (kWh)"))
        axis.set_ylabel(t("Battery temperature (°C)"))
        legend = axis.get_legend()
        legend.set_title(t("Charger type"))
        for label in legend.get_texts():
            label.set_text(t(label.get_text()))
        figure.tight_layout()
        st.pyplot(figure)
        plt.close(figure)
    with right:
        st.subheader(t("Charger type distribution"))
        counts = filtered["Charger_Type"].value_counts().rename_axis("Charger_Type").reset_index(name="Sessions")
        figure, axis = plt.subplots(figsize=(7, 5))
        sns.barplot(data=counts, x="Charger_Type", y="Sessions", color="steelblue", ax=axis)
        axis.set_xlabel(t("Charger type"))
        axis.set_ylabel(t("Number of sessions"))
        axis.set_xticks(range(len(counts)), [t(value) for value in counts["Charger_Type"]])
        figure.tight_layout()
        st.pyplot(figure)
        plt.close(figure)

    st.subheader(t("Average energy: peak and off-peak"))
    means = filtered.groupby("Peak_Hour_Flag")["Energy_kWh"].mean().reset_index()
    means["Period"] = means["Peak_Hour_Flag"].map({0: t("Off-peak"), 1: t("Peak")})
    figure, axis = plt.subplots(figsize=(9, 4))
    sns.barplot(data=means, x="Period", y="Energy_kWh", color="seagreen", ax=axis)
    axis.set_xlabel(t("Charging period (peak: 12:00-17:00)"))
    axis.set_ylabel(t("Average energy per session (kWh)"))
    figure.tight_layout()
    st.pyplot(figure)
    plt.close(figure)
    log_event(
        "CHARTS_RENDERED", chart_count=3, rows=len(filtered),
        charger_counts=filtered["Charger_Type"].value_counts().to_dict(),
        mean_energy_by_peak=filtered.groupby("Peak_Hour_Flag")["Energy_kWh"].mean().round(2).to_dict(),
        backend=matplotlib.get_backend(), language=st.session_state["language"],
    )


def show_prediction(df, temperature_limit):
    st.header(t("Live Machine Learning Prediction"))
    try:
        saved = load_model()
    except FileNotFoundError:
        log_event("MODEL_LOAD_FAILED", file="task2_ev_model.pkl", reason="File not found")
        st.error(t("Model file missing. Run task2_train_model.py first."))
        return
    st.caption(t("Saved model: {model}. Predictions can be incorrect, especially for Grid_Surge.", model=t(saved["model_name"])))

    # Submit all prediction inputs together, as shown in the lecture's form example.
    first = df.iloc[0]
    with st.sidebar.form("prediction_form"):
        st.subheader(t("Charging inputs"))
        charger = st.selectbox(t("Charger type"), ["AC", "DC"], index=None if "prediction_charger" in st.session_state else 0, format_func=option_labels(["AC", "DC"]), key="prediction_charger")
        user = st.selectbox(t("User type"), ["Staff", "Student", "Visitor"], index=None if "prediction_user" in st.session_state else 0, format_func=option_labels(["Staff", "Student", "Visitor"]), key="prediction_user")
        start = st.slider(t("Start hour"), 0, 23, int(first["Start_Hour"]), key="prediction_start")
        duration = st.number_input(t("Duration (minutes)"), min_value=1.0, value=float(first["Duration_Mins"]), step=1.0, key="prediction_duration")
        energy = st.number_input(t("Energy (kWh)"), min_value=0.0, value=float(first["Energy_kWh"]), step=0.1, key="prediction_energy")
        overstay = st.number_input(t("Overstay (minutes)"), min_value=0, value=0, step=1, key="prediction_overstay")
        temperature = st.number_input(t("Battery temperature (°C)"), value=float(first["Battery_Temp_C"]), step=0.1, key="prediction_temperature")
        submitted = st.form_submit_button(t("Predict status"), key="predict_submit")

    if submitted:
        inputs = build_prediction_input(charger, user, start, duration, energy, overstay, temperature)
        log_event("PREDICTION_REQUESTED", model=saved["model_name"], inputs=inputs.iloc[0].to_dict())
        # Match the exact dummy columns and column order saved during training.
        encoded = pd.get_dummies(inputs[saved["input_columns"]], columns=saved["categorical_columns"], dtype=int)
        encoded = encoded.reindex(columns=saved["feature_columns"], fill_value=0)
        st.session_state["prediction_result"] = {
            "inputs": inputs,
            "status": saved["model"].predict(encoded)[0],
        }
        log_event(
            "PREDICTION_RESULT", model=saved["model_name"],
            status=st.session_state["prediction_result"]["status"],
            power_kW=round(float(inputs.loc[0, "Power_kW"]), 4),
            peak_flag=int(inputs.loc[0, "Peak_Hour_Flag"]),
        )
    if "prediction_result" not in st.session_state:
        st.info(t("Enter charging details in the sidebar, then select Predict status."))
        return

    # Keep the last submitted result visible when switching the display language.
    inputs = st.session_state["prediction_result"]["inputs"]
    status = st.session_state["prediction_result"]["status"]
    message = t("Predicted status: {status}", status=t(status))
    if status == "Normal":
        st.success(message)
    elif status == "Overheated":
        st.error(message)
    else:
        st.warning(message)

    power, peak = st.columns(2)
    power.metric(t("Calculated power (kW)"), f"{inputs.loc[0, 'Power_kW']:.2f}")
    peak.metric(t("Charging period"), t("Peak") if inputs.loc[0, "Peak_Hour_Flag"] else t("Off-peak"))
    st.dataframe(display_data(inputs), hide_index=True)
    if temperature_limit is not None and inputs.loc[0, "Overstay_Mins"] > 0 and inputs.loc[0, "Battery_Temp_C"] >= temperature_limit:
        log_change("PREDICTION_TEMPERATURE_ALERT", threshold_C=temperature_limit,
                   temperature_C=float(inputs.loc[0, "Battery_Temp_C"]),
                   overstay_mins=int(inputs.loc[0, "Overstay_Mins"]))
        st.warning(t("Overstay recorded at or above your selected temperature alert threshold."))


def main():
    st.set_page_config(page_title=t("EV Campus Analytics"), page_icon="⚡", layout="wide")
    if "_log_session" not in st.session_state:
        log_event("SESSION_STARTED", streamlit_version=st.__version__, backend=matplotlib.get_backend())
    # Keep the selector at the top right, including in a narrow browser panel.
    with st.container(horizontal=True, horizontal_alignment="right"):
        st.selectbox("Language / 语言", ["English", "中文"], key="language", width=150)
    log_change("LANGUAGE_SELECTED", language=st.session_state["language"])
    # Re-send stored choices so the browser refreshes their translated labels.
    if st.session_state.get("display_language") != st.session_state["language"]:
        for key in ["navigation", "charger_filter", "user_filter", "period_filter", "prediction_charger", "prediction_user"]:
            if key in st.session_state:
                st.session_state[key] = st.session_state[key]
        st.session_state["display_language"] = st.session_state["language"]
    st.title(t("EV Campus Analytics"))
    st.caption(t("Taylor's Smart Campus | Charging data, visual analysis and status predictions"))
    # Prefer installed Chinese fonts so translated charts display readable glyphs.
    available_fonts = {font.name for font in font_manager.fontManager.ttflist}
    for font in ["PingFang SC", "Heiti SC", "Noto Sans CJK SC", "WenQuanYi Zen Hei"]:
        if font in available_fonts:
            plt.rcParams["font.family"] = font
            break
    pages = ["Executive KPI Dashboard", "Visual Analytics Studio", "Live ML Prediction"]
    page = st.sidebar.radio(t("Navigation"), pages, index=None if "navigation" in st.session_state else 0, format_func=option_labels(pages), key="navigation")
    log_change("PAGE_OPENED", page=page)
    try:
        df = load_data()
    except FileNotFoundError:
        log_event("DATA_LOAD_FAILED", file="0_ev_campus_dataset.csv", reason="File not found")
        st.error(t("Data file missing: 0_ev_campus_dataset.csv"))
        st.stop()
    except ValueError as error:
        log_event("DATA_LOAD_FAILED", reason=str(error))
        st.error(t(str(error)))
        st.stop()

    carbon_factor = None
    with st.sidebar.expander(t("Optional analysis settings")):
        if page == "Executive KPI Dashboard":
            carbon_factor = st.number_input(
                t("Net carbon savings factor (kg CO2/kWh)"), min_value=0.0,
                value=None, step=0.01, key="carbon_factor",
                help=t("Net emissions avoided per kWh relative to your chosen baseline."),
            )
        temperature_limit = st.number_input(
            t("Temperature alert threshold (°C)"), value=None, step=1.0, key="temperature_limit",
            help=t("Optional threshold for flagging overstays at high temperatures."),
        )
    if page == "Executive KPI Dashboard":
        log_change("CARBON_FACTOR_CHANGED", kg_CO2_per_kWh=carbon_factor)
    log_change("TEMPERATURE_THRESHOLD_CHANGED", threshold_C=temperature_limit)

    if page == "Live ML Prediction":
        show_prediction(df, temperature_limit)
        return

    st.sidebar.subheader(t("Historical data filters"))
    chargers = st.sidebar.multiselect(t("Charger type"), ["AC", "DC"], default=None if "charger_filter" in st.session_state else ["AC", "DC"], format_func=option_labels(["AC", "DC"]), key="charger_filter")
    user_types = sorted(df["User_Type"].unique())
    users = st.sidebar.multiselect(t("User type"), user_types, default=None if "user_filter" in st.session_state else user_types, format_func=option_labels(user_types), key="user_filter")
    periods = ["All", "Peak", "Off-peak"]
    period = st.sidebar.selectbox(t("Charging period"), periods, index=None if "period_filter" in st.session_state else 0, format_func=option_labels(periods), key="period_filter")
    minimum_energy = st.sidebar.slider(t("Minimum energy (kWh)"), 0.0, float(ceil(df["Energy_kWh"].max())), 0.0, 0.5, key="minimum_energy")
    filtered = df[
        df["Charger_Type"].isin(chargers)
        & df["User_Type"].isin(users)
        & (df["Energy_kWh"] >= minimum_energy)
    ]
    if period != "All":
        filtered = filtered[filtered["Peak_Hour_Flag"] == (1 if period == "Peak" else 0)]
    log_change(
        "FILTERS_APPLIED", chargers=list(chargers), users=list(users), period=period,
        minimum_energy_kWh=minimum_energy, matched_rows=len(filtered), total_rows=len(df),
    )
    if filtered.empty:
        log_event("FILTER_RESULT_EMPTY", page=page)
        st.info(t("No sessions match these filters. Adjust the sidebar selection."))
        return

    if temperature_limit is not None:
        risky = filtered[(filtered["Overstay_Mins"] > 0) & (filtered["Battery_Temp_C"] >= temperature_limit)]
        log_change("HISTORICAL_TEMPERATURE_CHECK", threshold_C=temperature_limit, matched_overstays=len(risky))
        if not risky.empty:
            st.warning(t("{count} filtered sessions have an overstay at or above your temperature threshold.", count=len(risky)))

    if page == "Executive KPI Dashboard":
        show_dashboard(df, filtered, carbon_factor)
    elif page == "Visual Analytics Studio":
        show_charts(filtered)


# Support both PyCharm's Run button and the normal Streamlit command.
if __name__ == "__main__":
    from streamlit.runtime.scriptrunner import get_script_run_ctx

    if get_script_run_ctx(suppress_warning=True) is None:
        from streamlit.web import cli

        cli.main([
            "run", str(Path(__file__).resolve()),
            "--server.address=127.0.0.1", "--browser.gatherUsageStats=false",
        ])
    else:
        try:
            main()
        except Exception as error:
            # Keep the traceback while adding the page and action context.
            log_event("ERROR", page=st.session_state.get("navigation"),
                      language=st.session_state.get("language"),
                      error_type=type(error).__name__, message=str(error))
            raise
