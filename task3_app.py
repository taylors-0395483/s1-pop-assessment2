# Interactive Streamlit Dashboard, Charts and Model Predictions

import base64
from datetime import datetime
from html import escape
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
    "Smart Campus | Charging data, visual analysis and status predictions": "智慧校园｜充电数据、图表分析与状态预测",
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
    "Peak revenue is the sum of estimated session fees for sessions overlapping 12:00-17:00. Fees use tiered hourly rates, rounded-up hours, fee caps, Staff and Student discounts, RM 5 peak surcharge and RM 15 idle surcharge when overstay is greater than zero.": "高峰收入是充电过程与 12:00–17:00 重叠的各次充电估算费用之和。采用阶梯时薪、时长向上取整、费用上限及教职工和学生折扣，另计 RM 5 高峰附加费；超时停车大于零时加收 RM 15。",
    "First-time waivers, Eco-Pass discounts and RFID replacement fees are excluded because their fields are unavailable. These estimates are not actual receipts.": "数据没有首次充电、Eco-Pass 和补卡记录，因此不计首次免费、Eco-Pass 折扣及补卡费。结果为估算费用，不是实际收款。",
    "Carbon savings = selected energy (kWh) multiplied by the net savings factor entered under Settings. No factor is assumed by default.": "碳减排量＝所选记录的充电量（kWh）× 分析设置中的净减排系数。默认不设置系数。",
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


# Keep presentation labels separate from the original dataset category codes.
CHINESE.update({
    "Overview": "数据概览", "Visual analytics": "图表分析", "Status prediction": "状态预测",
    "Settings": "分析设置", "Language": "语言", "English": "English",
    "Taylor's Lakeside Campus": "泰莱大学湖畔校区",
    "Understand campus charging, one session at a time.": "汇总充电数据，了解校园充电使用情况。",
    "Explore charging patterns across the same filtered records.": "使用相同筛选记录，深入比较充电规律。",
    "Enter a charging session and review the saved model's prediction.": "输入一次充电的参数，查看已训练模型的预测。",
    "{count:,} historical charging sessions": "{count:,} 条历史充电记录",
    "Total energy": "总充电量", "Average duration": "平均充电时长",
    "Estimated peak revenue": "估算高峰收入", "Carbon savings": "碳减排量",
    "Duration and energy": "充电时长与电量", "Historical status distribution": "历史状态分布",
    "Sessions by start hour": "按会话开始小时统计", "Mean energy by charger": "各充电类型的平均充电量",
    "Start hour of charging session": "会话开始小时", "Peak period (12:00–17:00)": "高峰时段（12:00–17:00）",
    "Historical sessions grouped by their start hour; this is not live grid load.": "按历史会话的开始小时分组统计，不代表实时电网负荷。",
    "sessions": "条记录", "Mean charging power by charger": "不同充电类型的功率分布",
    "Charging power (kW)": "充电功率（kW）", "Charging power distribution": "充电功率分布",
    "Filters": "筛选条件", "Records and download": "记录与下载",
    "Revenue is an estimate. Carbon savings require a configured factor.": "收入为估算值；碳减排量需要设置系数。",
    "Add a factor under Settings to calculate carbon savings.": "在“分析设置”中添加系数后可计算碳减排量。",
    "No sessions match these filters. Adjust the filter selection above.": "没有符合条件的记录，请调整上方筛选条件。",
    "Prediction result": "预测结果", "Use the form on the left, then select Predict status.": "在左侧填写参数，然后点击“预测状态”。",
    "The result stays visible until another prediction is submitted.": "提交下一次预测前，将保留当前结果。",
    "Submitted session": "已提交的充电参数", "Temperature and overstay": "温度与超时停车",
    "Temperature alert threshold is not configured. Set it under Settings.": "温度提醒阈值尚未设置，可在“分析设置”中填写。",
    "No temperature-related overstay alert for this submitted session.": "本次提交的充电记录未触发高温超时停车提醒。",
    "Session ID": "充电记录编号", "Start hour": "开始时间（小时）",
    "Duration (min)": "充电时长（分钟）", "Energy (kWh)": "充电量（kWh）",
    "Overstay (min)": "超时停车（分钟）", "Battery temperature (°C)": "电池温度（°C）",
    "Grid status": "充电状态", "Power (kW)": "功率（kW）", "Peak flag": "高峰标记",
    "Estimated fee (RM)": "估算费用（RM）",
})


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
    labels = {
        "Session_ID": "Session ID", "Charger_Type": "Charger type", "User_Type": "User type",
        "Start_Hour": "Start hour", "Duration_Mins": "Duration (min)", "Energy_kWh": "Energy (kWh)",
        "Overstay_Mins": "Overstay (min)", "Battery_Temp_C": "Battery temperature (°C)",
        "Grid_Status_Label": "Grid status", "Power_kW": "Power (kW)",
        "Peak_Hour_Flag": "Peak flag", "Estimated_Fee_RM": "Estimated fee (RM)",
    }
    return displayed.rename(columns={column: t(labels.get(column, column)) for column in displayed.columns})


def estimate_fee(row):
    # Apply tiered charging rates to the fields available in the dataset.
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

    # Use the calculated peak flag; unknown waivers and fees are excluded.
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
    # Reuse the saved model instead of retraining on page reruns.
    folder = Path(__file__).resolve().parent
    return joblib.load(folder / "task2_ev_model.pkl")


def build_prediction_input(charger, user, start, duration, energy, overstay, temperature):
    # Derive the same power and peak features used in the data pipeline.
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


CHARGER_COLORS = {"AC": "#159879", "DC": "#548ACD"}
STATUS_COLORS = {"Normal": "#159879", "Grid_Surge": "#E6AF3B", "Overheated": "#D77679"}


@st.cache_data
def image_uri(filename):
    # Read committed assets relative to this script, including on Community Cloud.
    image = Path(__file__).resolve().parent / "assets" / filename
    mime = "image/png" if image.suffix == ".png" else "image/webp"
    return f"data:{mime};base64,{base64.b64encode(image.read_bytes()).decode()}"


def apply_style():
    # Style native Streamlit controls while keeping their keyboard interactions.
    st.markdown("""<style>
    .stApp { background:#eef5ff; color:#18253c; }
    [data-testid="stMainBlockContainer"] { max-width:1480px; padding:2.8rem 2.5rem 3rem; }
    [data-testid="stHeader"] { background:transparent; }
    [data-testid="stSidebar"] { display:none; }
    .st-key-top_navigation { background:white; padding:12px 18px; border-radius:12px; }
    .brand { display:flex; align-items:center; gap:10px; min-height:48px; }
    .brand img { width:52px; height:52px; object-fit:contain; }
    .brand strong { display:block; font-size:19px; letter-spacing:-.6px; color:#122344; }
    .brand small { font-size:12px; color:#74829a; }
    .st-key-navigation [role="radiogroup"] { gap:8px; flex-wrap:wrap; }
    .st-key-navigation [data-testid="stRadioOption"] { margin:0; padding:12px 10px; border-bottom:2px solid transparent; }
    .st-key-navigation [data-testid="stRadioOption"] > div > div:first-child { display:none; }
    .st-key-navigation [data-testid="stRadioOption"][data-selected="true"] { border-bottom-color:#155eef; color:#155eef; }
    .st-key-navigation label:focus-within { outline:2px solid #155eef; outline-offset:2px; }
    .st-key-navigation p { font-size:14px; font-weight:600; }
    .campus-banner { display:flex; align-items:center; justify-content:space-between; height:150px; overflow:hidden; margin:8px 0 4px; }
    .campus-banner .banner-copy { width:49%; padding:8px 4px; }
    .campus-banner h1,.page-heading h1 { font-size:32px; line-height:1.15; margin:0 0 10px; padding:0; letter-spacing:-1px; }
    .campus-banner p,.page-heading p { color:#687b96; margin:0 0 7px; font-size:14px; }
    .campus-banner img { width:49%; height:150px; object-fit:cover; object-position:center 65%; border-radius:12px; }
    .page-heading { padding:22px 4px 12px; }
    [data-testid="stVerticalBlockBorderWrapper"] > div { border-color:#e1e9f5; border-radius:12px; }
    .st-key-kpi_strip,.st-key-filter_bar,.st-key-records,.st-key-prediction_inputs,.st-key-prediction_result,
    div[class*="st-key-chart_"] { background:white; border-radius:12px; }
    .st-key-records { overflow:hidden; }
    .st-key-kpi_strip [data-testid="stMetric"] { padding:3px 8px; }
    .st-key-kpi_strip [data-testid="stMetricLabel"] p { color:#687b96; font-size:13px; }
    .st-key-kpi_strip [data-testid="stMetricValue"] { font-size:clamp(23px,2.3vw,34px); font-weight:650; }
    .st-key-kpi_strip [data-testid="stColumn"]:last-child [data-testid="stMetricValue"] { color:#8796ad; font-size:clamp(21px,2.1vw,30px); }
    .st-key-kpi_strip [data-testid="stColumn"] + [data-testid="stColumn"] { border-left:1px solid #e5edf7; }
    [data-testid="stMetricDelta"] { font-size:12px; }
    h3 { font-size:17px !important; letter-spacing:-.25px; }
    [data-testid="stCaptionContainer"] { color:#74829a; }
    [data-testid="stForm"] { border:0; padding:0; }
    .st-key-filter_bar [data-testid="stMultiSelect"] span { font-size:12px; }
    @media(max-width:760px) {
      [data-testid="stMainBlockContainer"] { padding:2.5rem 1rem; }
      .campus-banner { height:auto; gap:12px; align-items:stretch; }
      .campus-banner .banner-copy { width:57%; }
      .campus-banner h1,.page-heading h1 { font-size:25px; }
      .campus-banner img { width:40%; min-height:150px; }
      .brand strong { font-size:17px; }
      .st-key-kpi_strip [data-testid="stColumn"] + [data-testid="stColumn"] { border-left:0; }
    }
    </style>""", unsafe_allow_html=True)


def show_heading(page, count):
    labels = {
        "Executive KPI Dashboard": ("Overview", "Understand campus charging, one session at a time."),
        "Visual Analytics Studio": ("Visual analytics", "Explore charging patterns across the same filtered records."),
        "Live ML Prediction": ("Status prediction", "Enter a charging session and review the saved model's prediction."),
    }
    title, subtitle = labels[page]
    text = f"<h1>{escape(t(title))}</h1><p>{escape(t(subtitle))}</p>"
    if page == "Executive KPI Dashboard":
        text += f"<p>{escape(t('{count:,} historical charging sessions', count=count))}</p>"
        st.markdown(
            f'<div class="campus-banner"><div class="banner-copy">{text}</div>'
            f'<img src="{image_uri("taylors-campus.webp")}" alt="Taylor’s Lakeside Campus buildings and lake"></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(f'<div class="page-heading">{text}</div>', unsafe_allow_html=True)


def show_metrics(df, filtered, carbon_factor):
    peak_revenue = filtered.loc[filtered["Peak_Hour_Flag"] == 1, "Estimated_Fee_RM"].sum()
    full_peak_revenue = df.loc[df["Peak_Hour_Flag"] == 1, "Estimated_Fee_RM"].sum()
    with st.container(border=True, key="kpi_strip"):
        energy, duration, revenue, carbon = st.columns(4)
        energy.metric(t("Total energy (kWh)"), f"{filtered['Energy_kWh'].sum():,.2f}")
        duration.metric(t("Average duration (minutes)"), f"{filtered['Duration_Mins'].mean():.1f}" if len(filtered) else "—")
        revenue.metric(t("Estimated peak revenue"), f"RM {peak_revenue:,.2f}", delta=f"RM {peak_revenue - full_peak_revenue:,.2f}", delta_color="off")
        savings = None if carbon_factor is None else filtered["Energy_kWh"].sum() * carbon_factor
        carbon.metric(t("Estimated carbon savings (kg CO2)"), t("Not configured") if savings is None else f"{savings:,.2f}", delta=None if savings is None else f"{savings - df['Energy_kWh'].sum() * carbon_factor:,.2f} kg CO2", delta_color="off")
    st.caption(t("Revenue is an estimate. Carbon savings require a configured factor.") + " " + t("Delta values compare the filtered selection with the full dataset, not a previous date."))
    log_change(
        "DASHBOARD_RENDERED", rows=len(filtered), total_energy_kWh=round(float(filtered["Energy_kWh"].sum()), 2),
        average_duration_mins=None if filtered.empty else round(float(filtered["Duration_Mins"].mean()), 1),
        estimated_peak_revenue_RM=round(float(peak_revenue), 2), carbon_factor=carbon_factor,
        carbon_savings_kg=None if savings is None else round(float(savings), 2), language=st.session_state["language"],
    )


def show_filters(df):
    with st.container(border=True, key="filter_bar"):
        columns = st.columns([1.2, 1.6, 1.15, 1])
        with columns[0]:
            chargers = st.multiselect(t("Charger type"), ["AC", "DC"], default=None if "charger_filter" in st.session_state else ["AC", "DC"], format_func=option_labels(["AC", "DC"]), key="charger_filter")
        with columns[1]:
            user_types = sorted(df["User_Type"].unique())
            users = st.multiselect(t("User type"), user_types, default=None if "user_filter" in st.session_state else user_types, format_func=option_labels(user_types), key="user_filter")
        with columns[2]:
            periods = ["All", "Peak", "Off-peak"]
            period = st.selectbox(t("Charging period"), periods, format_func=option_labels(periods), key="period_filter")
        with columns[3]:
            minimum = st.number_input(t("Minimum energy (kWh)"), min_value=0.0, max_value=float(ceil(df["Energy_kWh"].max())), step=0.5, key="minimum_energy")
    filtered = df[df["Charger_Type"].isin(chargers) & df["User_Type"].isin(users) & (df["Energy_kWh"] >= minimum)]
    if period != "All":
        filtered = filtered[filtered["Peak_Hour_Flag"] == (1 if period == "Peak" else 0)]
    log_change("FILTERS_APPLIED", chargers=list(chargers), users=list(users), period=period, minimum_energy_kWh=minimum, matched_rows=len(filtered), total_rows=len(df))
    return filtered


def draw_chart(filtered, kind, wide=True):
    # Draw directly from filtered records, using consistent charger colours.
    figure, axis = plt.subplots(figsize=(7.4 if wide else 5.2, 2.9))
    if kind in ["duration", "temperature"]:
        x = "Duration_Mins" if kind == "duration" else "Energy_kWh"
        y = "Energy_kWh" if kind == "duration" else "Battery_Temp_C"
        for charger in ["AC", "DC"]:
            group = filtered[filtered["Charger_Type"] == charger]
            if not group.empty:
                axis.scatter(group[x], group[y], s=16, alpha=0.6, edgecolors="none", color=CHARGER_COLORS[charger], label=t(charger))
        axis.set_xlabel(t("Duration (min)") if kind == "duration" else t("Energy delivered (kWh)"))
        axis.set_ylabel(t("Energy delivered (kWh)") if kind == "duration" else t("Battery temperature (°C)"))
        axis.legend(frameon=False, loc="upper left", fontsize=9)
    elif kind == "status":
        labels = ["Normal", "Grid_Surge", "Overheated"]
        counts = filtered["Grid_Status_Label"].value_counts().reindex(labels, fill_value=0)
        axis.pie(counts, colors=[STATUS_COLORS[label] for label in labels], startangle=90, wedgeprops={"width": 0.25, "edgecolor": "white"})
        axis.text(0, 0, f"{len(filtered):,}\n{t('sessions')}", ha="center", va="center", fontsize=17, color="#18253c")
        axis.legend([f"{t(label)}: {count:,} ({count / len(filtered):.1%})" for label, count in counts.items()], loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False, fontsize=9)
    elif kind == "hours":
        counts = filtered.groupby("Start_Hour").size().reindex(range(24), fill_value=0)
        axis.bar(counts.index, counts, color=["#155eef" if 12 <= hour < 17 else "#97b9f2" for hour in counts.index], width=0.72)
        axis.axvspan(11.5, 16.5, color="#155eef", alpha=0.07, label=t("Peak period (12:00–17:00)"))
        axis.set(xlim=(-0.7, 23.7), xticks=[0, 4, 8, 12, 16, 20, 23])
        axis.set_xlabel(t("Start hour of charging session"))
        axis.set_ylabel(t("Number of sessions"))
        axis.legend(frameon=False, fontsize=9, loc="upper right")
    elif kind == "mean_energy":
        means = filtered.groupby("Charger_Type")["Energy_kWh"].mean().reindex(["AC", "DC"]).dropna()
        axis.barh([t(value) for value in means.index], means, color=[CHARGER_COLORS[value] for value in means.index], height=0.45)
        for position, value in enumerate(means):
            axis.text(value + means.max() * 0.025, position, f"{value:.2f}", va="center", fontsize=10)
        axis.set_xlim(0, max(float(means.max()) * 1.25, 1))
        axis.set_xlabel(t("Average energy per session (kWh)"))
    elif kind == "peak":
        means = filtered.groupby("Peak_Hour_Flag")["Energy_kWh"].mean()
        axis.bar([t("Peak") if value else t("Off-peak") for value in means.index], means, color=["#155eef" if value else "#97b9f2" for value in means.index], width=0.5)
        for position, value in enumerate(means):
            axis.text(position, value, f"{value:.2f}", ha="center", va="bottom", fontsize=10)
        axis.set_ylim(0, max(float(means.max()) * 1.22, 1))
        axis.set_xlabel(t("Charging period (peak: 12:00-17:00)"))
        axis.set_ylabel(t("Average energy per session (kWh)"))
    elif kind == "counts":
        counts = filtered["Charger_Type"].value_counts().reindex(["AC", "DC"], fill_value=0)
        axis.bar([t(value) for value in counts.index], counts, color=[CHARGER_COLORS[value] for value in counts.index], width=0.5)
        for position, value in enumerate(counts):
            axis.text(position, value, str(value), ha="center", va="bottom", fontsize=10)
        axis.set_ylim(0, max(int(counts.max()) * 1.2, 1))
        axis.set_ylabel(t("Number of sessions"))
    elif kind == "power":
        sns.boxplot(data=filtered, x="Charger_Type", y="Power_kW", hue="Charger_Type", order=["AC", "DC"], palette=CHARGER_COLORS, legend=False, width=0.45, linewidth=1.1, fliersize=3, ax=axis)
        axis.set_xlabel(t("Charger type"))
        axis.set_ylabel(t("Charging power (kW)"))
    if kind != "status":
        axis.spines[["top", "right"]].set_visible(False)
        axis.spines[["left", "bottom"]].set_color("#d4deeb")
        axis.tick_params(colors="#61738e", labelsize=9, length=0)
        axis.set_axisbelow(True)
        axis.grid(axis="x" if kind == "mean_energy" else "y", color="#edf1f7", linewidth=0.7)
        axis.xaxis.label.set_color("#61738e")
        axis.yaxis.label.set_color("#61738e")
    figure.tight_layout(pad=1.0)
    st.pyplot(figure, width="stretch")
    plt.close(figure)


def show_chart_grid(filtered, charts, section):
    log_event("CHARTS_STARTED", language=st.session_state["language"], rows=len(filtered), section=section)
    for offset in range(0, len(charts), 2):
        left, right = st.columns([1.45, 1])
        for position, (column, (kind, title)) in enumerate(zip([left, right], charts[offset:offset + 2])):
            with column, st.container(border=True, key=f"chart_{section}_{kind}"):
                st.subheader(t(title))
                draw_chart(filtered, kind, wide=position == 0)
                if kind == "hours":
                    st.caption(t("Historical sessions grouped by their start hour; this is not live grid load."))
    log_event("CHARTS_RENDERED", language=st.session_state["language"], rows=len(filtered), section=section, chart_count=len(charts), backend=matplotlib.get_backend())


def show_records(df, filtered):
    with st.container(border=True, key="records"):
        heading, action = st.columns([3, 1], vertical_alignment="center")
        heading.subheader(t("Records and download"))
        with action:
            st.download_button(t("Download filtered CSV"), data=filtered.to_csv(index=False).encode("utf-8"), file_name="task3_filtered_data.csv", mime="text/csv", key="download_filtered", type="primary", icon=":material/download:", on_click=log_event, args=("CSV_DOWNLOAD_REQUESTED",), kwargs={"file": "task3_filtered_data.csv", "rows": len(filtered), "columns": filtered.columns.tolist(), "language": st.session_state["language"]})
        st.caption(t("Showing {selected:,} of {total:,} sessions. Peak flag: 1 = peak, 0 = off-peak.", selected=len(filtered), total=len(df)))
        displayed = display_data(filtered)
        number_formats = {"Energy (kWh)": "%.2f", "Power (kW)": "%.2f", "Estimated fee (RM)": "%.2f"}
        st.dataframe(displayed, hide_index=True, height=330, width="stretch", key="filtered_records", column_config={t(label): st.column_config.NumberColumn(format=fmt) for label, fmt in number_formats.items()})
        st.caption(t("CSV downloads keep the original field names and category codes."))


def show_prediction(df, temperature_limit):
    saved = load_model()
    left, right = st.columns([1.05, 1], gap="large")
    with left, st.container(border=True, key="prediction_inputs"):
        st.subheader(t("Charging inputs"))
        first = df.iloc[0]
        with st.form("prediction_form"):
            a, b = st.columns(2)
            with a:
                charger = st.selectbox(t("Charger type"), ["AC", "DC"], format_func=option_labels(["AC", "DC"]), key="prediction_charger")
            with b:
                user = st.selectbox(t("User type"), ["Staff", "Student", "Visitor"], format_func=option_labels(["Staff", "Student", "Visitor"]), key="prediction_user")
            start = st.slider(t("Start hour"), 0, 23, int(first["Start_Hour"]), key="prediction_start")
            a, b = st.columns(2)
            with a:
                duration = st.number_input(t("Duration (minutes)"), min_value=1.0, value=float(first["Duration_Mins"]), step=1.0, key="prediction_duration")
                overstay = st.number_input(t("Overstay (minutes)"), min_value=0, value=0, step=1, key="prediction_overstay")
            with b:
                energy = st.number_input(t("Energy (kWh)"), min_value=0.0, value=float(first["Energy_kWh"]), step=0.1, key="prediction_energy")
                temperature = st.number_input(t("Battery temperature (°C)"), value=float(first["Battery_Temp_C"]), step=0.1, key="prediction_temperature")
            submitted = st.form_submit_button(t("Predict status"), key="predict_submit", type="primary", width="stretch", icon=":material/bolt:")
        st.caption(t("Saved model: {model}. Predictions can be incorrect, especially for Grid_Surge.", model=t(saved["model_name"])))
    if submitted:
        inputs = build_prediction_input(charger, user, start, duration, energy, overstay, temperature)
        log_event("PREDICTION_REQUESTED", model=saved["model_name"], inputs=inputs.iloc[0].to_dict())
        encoded = pd.get_dummies(inputs[saved["input_columns"]], columns=saved["categorical_columns"], dtype=int)
        encoded = encoded.reindex(columns=saved["feature_columns"], fill_value=0)
        st.session_state["prediction_result"] = {"inputs": inputs, "status": saved["model"].predict(encoded)[0]}
        log_event("PREDICTION_RESULT", model=saved["model_name"], status=st.session_state["prediction_result"]["status"], power_kW=round(float(inputs.loc[0, "Power_kW"]), 4), peak_flag=int(inputs.loc[0, "Peak_Hour_Flag"]))
    with right, st.container(border=True, key="prediction_result"):
        st.subheader(t("Prediction result"))
        if "prediction_result" not in st.session_state:
            st.info(t("Use the form on the left, then select Predict status."))
            return
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
        st.subheader(t("Temperature and overstay"))
        st.write(f"{inputs.loc[0, 'Battery_Temp_C']:.1f} °C · {inputs.loc[0, 'Overstay_Mins']:.0f} min")
        if temperature_limit is None:
            st.caption(t("Temperature alert threshold is not configured. Set it under Settings."))
        elif inputs.loc[0, "Overstay_Mins"] > 0 and inputs.loc[0, "Battery_Temp_C"] >= temperature_limit:
            log_change("PREDICTION_TEMPERATURE_ALERT", threshold_C=temperature_limit, temperature_C=float(inputs.loc[0, "Battery_Temp_C"]), overstay_mins=int(inputs.loc[0, "Overstay_Mins"]))
            st.warning(t("Overstay recorded at or above your selected temperature alert threshold."))
        else:
            st.info(t("No temperature-related overstay alert for this submitted session."))
        with st.expander(t("Submitted session")):
            st.dataframe(display_data(inputs), hide_index=True, width="stretch")
        st.caption(t("The result stays visible until another prediction is submitted."))


def main():
    st.session_state.setdefault("language", "English")
    st.set_page_config(page_title="EV Campus Analytics", page_icon=str(Path(__file__).resolve().parent / "assets" / "taylors-logo.png"), layout="wide", initial_sidebar_state="collapsed")
    apply_style()
    if "_log_session" not in st.session_state:
        log_event("SESSION_STARTED", streamlit_version=st.__version__, backend=matplotlib.get_backend())
    # Refresh stored choice labels when the display language changes.
    if st.session_state.get("display_language") != st.session_state["language"]:
        for key in ["navigation", "charger_filter", "user_filter", "period_filter", "prediction_charger", "prediction_user"]:
            if key in st.session_state:
                st.session_state[key] = st.session_state[key]
        st.session_state["display_language"] = st.session_state["language"]
    with st.container(key="top_navigation"):
        brand, navigation, settings, language = st.columns([2.8, 3.8, 1.3, 1.2], vertical_alignment="center")
        with brand:
            st.markdown(f'<div class="brand"><img src="{image_uri("taylors-logo.png")}" alt="Taylor’s University logo"><div><strong>EV Campus Analytics</strong><small>{escape(t("Taylor's Lakeside Campus"))}</small></div></div>', unsafe_allow_html=True)
        with navigation:
            pages = ["Executive KPI Dashboard", "Visual Analytics Studio", "Live ML Prediction"]
            labels = dict(zip(pages, [t("Overview"), t("Visual analytics"), t("Status prediction")]))
            page = st.radio(t("Navigation"), pages, index=None if "navigation" in st.session_state else 0, format_func=labels.get, horizontal=True, label_visibility="collapsed", key="navigation")
        with settings, st.popover(t("Settings"), icon=":material/tune:"):
            carbon_factor = st.number_input(t("Net carbon savings factor (kg CO2/kWh)"), min_value=0.0, value=None, step=0.01, key="carbon_factor", help=t("Net emissions avoided per kWh relative to your chosen baseline."))
            temperature_limit = st.number_input(t("Temperature alert threshold (°C)"), value=None, step=1.0, key="temperature_limit", help=t("Optional threshold for flagging overstays at high temperatures."))
            with st.expander(t("How the estimates are calculated")):
                st.write(t("Peak revenue is the sum of estimated session fees for sessions overlapping 12:00-17:00. Fees use tiered hourly rates, rounded-up hours, fee caps, Staff and Student discounts, RM 5 peak surcharge and RM 15 idle surcharge when overstay is greater than zero."))
                st.write(t("First-time waivers, Eco-Pass discounts and RFID replacement fees are excluded because their fields are unavailable. These estimates are not actual receipts."))
                st.write(t("Carbon savings = selected energy (kWh) multiplied by the net savings factor entered under Settings. No factor is assumed by default."))
        with language:
            st.selectbox("Language / 语言", ["English", "中文"], key="language", label_visibility="collapsed")
    log_change("LANGUAGE_SELECTED", language=st.session_state["language"])
    log_change("PAGE_OPENED", page=page)
    log_change("CARBON_FACTOR_CHANGED", kg_CO2_per_kWh=carbon_factor)
    log_change("TEMPERATURE_THRESHOLD_CHANGED", threshold_C=temperature_limit)
    # Prefer an installed Chinese font; packages.txt supplies one on Linux.
    available = {font.name for font in font_manager.fontManager.ttflist}
    for font in ["PingFang SC", "Heiti SC", "Noto Sans CJK SC", "WenQuanYi Zen Hei"]:
        if font in available:
            plt.rcParams["font.family"] = font
            break
    plt.rcParams.update({"font.size": 10, "axes.labelsize": 10, "figure.facecolor": "white", "axes.facecolor": "white"})
    try:
        df = load_data()
    except (FileNotFoundError, ValueError) as error:
        log_event("DATA_LOAD_FAILED", reason=str(error))
        st.error(t(str(error)))
        st.stop()
    show_heading(page, len(df))
    if page == "Live ML Prediction":
        try:
            show_prediction(df, temperature_limit)
        except FileNotFoundError:
            log_event("MODEL_LOAD_FAILED", file="task2_ev_model.pkl", reason="File not found")
            st.error(t("Model file missing. Run task2_train_model.py first."))
        return
    metrics = st.container() if page == "Executive KPI Dashboard" else None
    filtered = show_filters(df)
    if metrics is not None:
        with metrics:
            show_metrics(df, filtered, carbon_factor)
    if filtered.empty:
        log_event("FILTER_RESULT_EMPTY", page=page)
        st.info(t("No sessions match these filters. Adjust the filter selection above."))
        show_records(df, filtered)
        return
    if temperature_limit is not None:
        risky = filtered[(filtered["Overstay_Mins"] > 0) & (filtered["Battery_Temp_C"] >= temperature_limit)]
        log_change("HISTORICAL_TEMPERATURE_CHECK", threshold_C=temperature_limit, matched_overstays=len(risky))
        if not risky.empty:
            st.warning(t("{count} filtered sessions have an overstay at or above your temperature threshold.", count=len(risky)))
    if page == "Visual Analytics Studio":
        st.caption(t("All charts use the same {count:,} filtered sessions.", count=len(filtered)))
        # Keep each chart once, pairing detailed plots with compact summaries.
        charts = [
            ("temperature", "Energy and battery temperature"), ("status", "Historical status distribution"),
            ("duration", "Duration and energy"), ("mean_energy", "Mean energy by charger"),
            ("hours", "Sessions by start hour"), ("counts", "Charger type distribution"),
            ("peak", "Average energy: peak and off-peak"), ("power", "Charging power distribution"),
        ]
        show_chart_grid(filtered, charts, "analytics")
    show_records(df, filtered)


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
