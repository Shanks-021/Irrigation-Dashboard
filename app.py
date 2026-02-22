import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os

# ─── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Farmer Irrigation Dashboard",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Dataset Registry ─────────────────────────────────────────────────────────
# Add new Excel files here: display_name → (filename, region_label)
DATASETS = {
    "Hyderabad Region": ("Format for data Amazon Project Hyd (1).xlsx", "Hyderabad"),
    "Bangalore Region": ("Format for data Amazon Project Blr.xlsx", "Bangalore"),
}

# ─── Improved CSS — light-on-dark with high contrast ──────────────────────────
st.markdown("""
<style>
    /* ── Global ── */
    .stApp {
        background: #0e1117;
    }
    section[data-testid="stSidebar"] {
        background: #161b22;
        border-right: 1px solid #30363d;
    }
    header[data-testid="stHeader"] {
        background: transparent;
    }

    /* ── KPI Cards ── */
    .kpi-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px 16px;
        text-align: center;
        transition: border-color 0.2s, transform 0.15s;
    }
    .kpi-card:hover {
        border-color: #58a6ff;
        transform: translateY(-2px);
    }
    .kpi-icon { font-size: 1.6rem; margin-bottom: 4px; }
    .kpi-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #58a6ff;
        margin: 6px 0 2px 0;
        line-height: 1.2;
    }
    .kpi-label {
        font-size: 0.75rem;
        font-weight: 600;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .kpi-sub {
        font-size: 0.78rem;
        color: #3fb950;
        margin-top: 4px;
    }

    /* ── Section Titles ── */
    .section-title {
        font-size: 1.15rem;
        font-weight: 600;
        color: #e6edf3;
        border-left: 3px solid #58a6ff;
        padding-left: 12px;
        margin: 36px 0 14px 0;
    }

    /* ── Sidebar dataset badge ── */
    .dataset-badge {
        background: #21262d;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 10px 12px;
        text-align: center;
        margin-bottom: 12px;
    }
    .dataset-badge .region {
        font-size: 1.05rem;
        font-weight: 600;
        color: #58a6ff;
    }
    .dataset-badge .file {
        font-size: 0.7rem;
        color: #8b949e;
        word-break: break-all;
    }
</style>
""", unsafe_allow_html=True)

# ─── Color Palette for Charts ─────────────────────────────────────────────────
CHART_COLORS = {
    "primary": "#58a6ff",
    "secondary": "#3fb950",
    "accent": "#d29922",
    "highlight": "#f78166",
    "purple": "#bc8cff",
    "cyan": "#39d2c0",
    "text": "#e6edf3",
    "muted": "#8b949e",
    "bg_card": "#161b22",
    "bg_plot": "#0d1117",
    "grid": "#21262d",
}
PALETTE = [
    "#58a6ff", "#3fb950", "#d29922", "#f78166", "#bc8cff",
    "#39d2c0", "#f0883e", "#a5d6ff", "#7ee787", "#ffd33d",
]
CHART_TEMPLATE = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor=CHART_COLORS["bg_plot"],
    font=dict(color=CHART_COLORS["text"], size=12),
    margin=dict(l=20, r=20, t=50, b=20),
)


# ─── Data Loading ─────────────────────────────────────────────────────────────
@st.cache_data
def load_data(file_path: str) -> pd.DataFrame:
    df = pd.read_excel(file_path, sheet_name="Sheet1", header=None, skiprows=1)

    cols = [
        "Sr_No", "Sap_No", "Farmer_Name", "Village_Name", "Mandal", "Mobile_No", "State",
        "Total_Area", "Crop_Name", "Sowing_Date", "Expected_Harvest_Date", "Crop_Stage",
        "Area_Acre", "Irrigation_Method", "No_Irrigation_Earlier", "Water_Flood_m3",
        "Water_Source", "Avg_Water_Flood_m3", "Pump_Rate", "Irrigation_Duration_Flood",
        "Meter_Reading_Date", "Drip_Supply_Date", "Drip_Install_Date", "No_Irrigations_Drip",
        "Total_Water_Drip_m3", "Irrigation_Duration_Drip", "Avg_Water_Drip_m3",
        "Meter_30Jan", "Water_Liters_30Jan", "Water_PerAcre_30Jan",
        "Meter_10Feb", "Water_Liters_10Feb", "Water_PerAcre_10Feb",
        "Meter_18Feb", "Water_Liters_18Feb", "Water_PerAcre_18Feb",
        "Meter_End", "Total_Water_Consumption",
        "Water_Saved_m3", "Yield_Before_Flood", "Yield_After_Drip",
        "Fertilizer_Saving_Pct", "Electricity_Saving_Pct", "Labour_Saving", "Input_Cost_Reduction",
    ]
    df.columns = cols
    df = df[~df["Sr_No"].isin(["Sr No", "Total"])].reset_index(drop=True)

    numeric_cols = [
        "Total_Area", "Area_Acre", "No_Irrigations_Drip", "Total_Water_Drip_m3",
        "Irrigation_Duration_Drip", "Avg_Water_Drip_m3",
        "Meter_30Jan", "Water_Liters_30Jan", "Water_PerAcre_30Jan",
        "Meter_10Feb", "Water_Liters_10Feb", "Water_PerAcre_10Feb",
        "Meter_18Feb", "Water_Liters_18Feb", "Water_PerAcre_18Feb",
        "Total_Water_Consumption", "Water_Saved_m3",
    ]
    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    farmer_fields = [
        "Sr_No", "Sap_No", "Farmer_Name", "Village_Name", "Mandal",
        "Mobile_No", "State", "Total_Area", "Irrigation_Method", "Water_Source",
    ]
    df[farmer_fields] = df[farmer_fields].ffill()
    return df


# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💧 Irrigation Dashboard")
    st.markdown("---")

    # ── Dataset Selector ──
    st.markdown("##### 📂 Select Dataset")
    dataset_name = st.selectbox(
        "Dataset",
        list(DATASETS.keys()),
        label_visibility="collapsed",
    )
    file_name, region_label = DATASETS[dataset_name]
    st.markdown(f"""
    <div class="dataset-badge">
        <div class="region">📍 {region_label}</div>
        <div class="file">{file_name}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Load selected dataset
    df = load_data(file_name)

    # ── Filters ──
    st.markdown("##### 🎛️ Filters")

    villages = ["All"] + sorted(df["Village_Name"].dropna().unique().tolist())
    sel_village = st.selectbox("Village", villages)

    crops = ["All"] + sorted(df["Crop_Name"].dropna().unique().tolist())
    sel_crop = st.selectbox("Crop", crops)

    water_sources = ["All"] + sorted(df["Water_Source"].dropna().unique().tolist())
    sel_source = st.selectbox("Water Source", water_sources)

# ─── Apply Filters ─────────────────────────────────────────────────────────────
filtered = df.copy()
if sel_village != "All":
    filtered = filtered[filtered["Village_Name"] == sel_village]
if sel_crop != "All":
    filtered = filtered[filtered["Crop_Name"] == sel_crop]
if sel_source != "All":
    filtered = filtered[filtered["Water_Source"] == sel_source]

# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center; padding:8px 0 0 0;">
    <h1 style="color:{CHART_COLORS['text']}; font-size:2rem; margin-bottom:0;">
        💧 Farmer Irrigation Dashboard
    </h1>
    <p style="color:{CHART_COLORS['muted']}; font-size:0.95rem; margin-top:2px;">
        {dataset_name} — Drip vs Flood Irrigation Impact Analysis
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("")

# ─── KPI Metrics ───────────────────────────────────────────────────────────────
total_water_consumption = filtered["Total_Water_Consumption"].dropna().sum()
total_water_drip = filtered["Total_Water_Drip_m3"].dropna().sum()
total_acres = filtered["Area_Acre"].dropna().sum()
num_farmers = filtered["Farmer_Name"].nunique()
num_crops = filtered["Crop_Name"].nunique()
avg_irrigations = filtered["No_Irrigations_Drip"].dropna().mean()
if pd.isna(avg_irrigations):
    avg_irrigations = 0

estimated_flood_water = total_water_drip * 2.5
water_saved_m3 = estimated_flood_water - total_water_drip
water_saved_liters = water_saved_m3 * 1000

kpi_items = [
    ("💧", "Total Water Saved", f"{water_saved_m3:,.0f} m³", f"≈ {water_saved_liters / 1e6:,.2f} M liters"),
    ("🌾", "Acres Covered", f"{total_acres:,.1f}", f"{filtered['Village_Name'].nunique()} villages"),
    ("👨‍🌾", "Farmers Benefited", f"{num_farmers}", f"{num_crops} crop types"),
    ("🔄", "Avg Irrigations", f"{avg_irrigations:,.1f}", "cycles per farmer"),
    ("📊", "Drip Water Used", f"{total_water_drip:,.0f} m³", f"{total_water_consumption / 1000:,.0f}K L consumed"),
]

cols_kpi = st.columns(len(kpi_items))
for col, (icon, label, value, sub) in zip(cols_kpi, kpi_items):
    with col:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon">{icon}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-label">{label}</div>
            <div class="kpi-sub">{sub}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("")

# ─── Helper: build meter time-series ──────────────────────────────────────────
def build_meter_df(data):
    rows = []
    for _, row in data.iterrows():
        for date_label, col in [("30 Jan 2026", "Meter_30Jan"),
                                 ("10 Feb 2026", "Meter_10Feb"),
                                 ("18 Feb 2026", "Meter_18Feb")]:
            val = row[col]
            if pd.notna(val):
                rows.append({
                    "Date": date_label,
                    "Farmer": row["Farmer_Name"],
                    "Crop": row["Crop_Name"],
                    "Meter_m3": val,
                    "Area": row["Area_Acre"],
                })
    return pd.DataFrame(rows)

meter_df = build_meter_df(filtered)
DATE_ORDER = ["30 Jan 2026", "10 Feb 2026", "18 Feb 2026"]

# ─── 1 · Water Meter Trend ────────────────────────────────────────────────────
st.markdown('<div class="section-title">📈 Water Meter Readings Over Time</div>', unsafe_allow_html=True)

if not meter_df.empty:
    agg = (meter_df.groupby("Date").agg(Total=("Meter_m3", "sum"), Farmers=("Farmer", "nunique"))
           .reindex(DATE_ORDER).reset_index())
    agg["Incremental"] = agg["Total"].diff().fillna(agg["Total"])

    c1, c2 = st.columns(2)

    with c1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=agg["Date"], y=agg["Total"],
            mode="lines+markers+text",
            text=[f"{v:,.0f}" for v in agg["Total"]],
            textposition="top center",
            textfont=dict(color=CHART_COLORS["text"], size=11),
            line=dict(color=CHART_COLORS["primary"], width=3),
            marker=dict(size=10, color=CHART_COLORS["primary"],
                        line=dict(width=2, color=CHART_COLORS["text"])),
            fill="tozeroy",
            fillcolor="rgba(88,166,255,0.08)",
        ))
        fig.update_layout(
            title=dict(text="Cumulative Meter Readings (m³)", font=dict(size=14)),
            xaxis_title="Date", yaxis_title="Total (m³)",
            xaxis=dict(gridcolor=CHART_COLORS["grid"]),
            yaxis=dict(gridcolor=CHART_COLORS["grid"]),
            height=400, **CHART_TEMPLATE,
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=agg["Date"], y=agg["Incremental"],
            text=[f"{v:,.0f} m³" for v in agg["Incremental"]],
            textposition="outside",
            textfont=dict(color=CHART_COLORS["text"], size=11),
            marker_color=[CHART_COLORS["primary"], CHART_COLORS["secondary"], CHART_COLORS["accent"]],
            marker_line=dict(width=0),
        ))
        fig.update_layout(
            title=dict(text="Incremental Water Per Period (m³)", font=dict(size=14)),
            xaxis_title="Date", yaxis_title="Added (m³)",
            xaxis=dict(gridcolor=CHART_COLORS["grid"]),
            yaxis=dict(gridcolor=CHART_COLORS["grid"]),
            height=400, **CHART_TEMPLATE,
        )
        st.plotly_chart(fig, use_container_width=True)

# ─── 2 · Water Consumption by Farmer ──────────────────────────────────────────
st.markdown('<div class="section-title">👨‍🌾 Water Consumption by Farmer</div>', unsafe_allow_html=True)

fw = (filtered.groupby("Farmer_Name")["Total_Water_Drip_m3"]
      .sum().dropna().sort_values(ascending=True).reset_index())
fw = fw[fw["Total_Water_Drip_m3"] > 0]

if not fw.empty:
    fig = px.bar(
        fw, x="Total_Water_Drip_m3", y="Farmer_Name", orientation="h",
        color="Total_Water_Drip_m3",
        color_continuous_scale=[[0, "#21262d"], [0.5, "#1f6feb"], [1, "#58a6ff"]],
        labels={"Total_Water_Drip_m3": "Water (m³)", "Farmer_Name": ""},
    )
    fig.update_layout(
        height=max(380, len(fw) * 28), showlegend=False, coloraxis_showscale=False,
        xaxis=dict(gridcolor=CHART_COLORS["grid"]),
        yaxis=dict(gridcolor=CHART_COLORS["grid"]),
        **CHART_TEMPLATE,
    )
    st.plotly_chart(fig, use_container_width=True)

# ─── 3 · Crop-wise ────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">🌱 Crop-wise Water Usage &amp; Area</div>', unsafe_allow_html=True)

c1, c2 = st.columns(2)

with c1:
    cw = (filtered.groupby("Crop_Name")
          .agg(Water=("Total_Water_Drip_m3", "sum"), Area=("Area_Acre", "sum"))
          .dropna().reset_index())
    cw = cw[cw["Water"] > 0].sort_values("Water", ascending=False)
    if not cw.empty:
        fig = px.bar(
            cw, x="Crop_Name", y="Water", color="Crop_Name",
            color_discrete_sequence=PALETTE,
            labels={"Water": "Water (m³)", "Crop_Name": ""},
        )
        fig.update_layout(
            title=dict(text="Drip Water by Crop (m³)", font=dict(size=14)),
            showlegend=False, height=400,
            xaxis=dict(gridcolor=CHART_COLORS["grid"]),
            yaxis=dict(gridcolor=CHART_COLORS["grid"]),
            **CHART_TEMPLATE,
        )
        st.plotly_chart(fig, use_container_width=True)

with c2:
    ca = (filtered.groupby("Crop_Name")["Area_Acre"].sum().dropna().reset_index())
    ca = ca[ca["Area_Acre"] > 0]
    if not ca.empty:
        fig = px.pie(
            ca, values="Area_Acre", names="Crop_Name",
            color_discrete_sequence=PALETTE, hole=0.45,
        )
        fig.update_traces(textinfo="percent+label",
                          textfont=dict(color="white", size=11))
        fig.update_layout(
            title=dict(text="Area by Crop (Acres)", font=dict(size=14)),
            height=400, **CHART_TEMPLATE,
        )
        st.plotly_chart(fig, use_container_width=True)

# ─── 4 · Village-wise ─────────────────────────────────────────────────────────
st.markdown('<div class="section-title">🏘️ Village-wise Comparison</div>', unsafe_allow_html=True)

c1, c2 = st.columns(2)

with c1:
    vs = (filtered.groupby("Village_Name")
          .agg(Farmers=("Farmer_Name", "nunique"), Acres=("Area_Acre", "sum"),
               Water=("Total_Water_Drip_m3", "sum"))
          .dropna().reset_index())
    if not vs.empty:
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Farmers", x=vs["Village_Name"], y=vs["Farmers"],
                             marker_color=CHART_COLORS["primary"]))
        fig.add_trace(go.Bar(name="Acres", x=vs["Village_Name"], y=vs["Acres"],
                             marker_color=CHART_COLORS["secondary"]))
        fig.update_layout(
            title=dict(text="Farmers & Acres by Village", font=dict(size=14)),
            barmode="group", height=400,
            xaxis=dict(gridcolor=CHART_COLORS["grid"]),
            yaxis=dict(gridcolor=CHART_COLORS["grid"]),
            legend=dict(font=dict(color=CHART_COLORS["text"])),
            **CHART_TEMPLATE,
        )
        st.plotly_chart(fig, use_container_width=True)

with c2:
    vw = (filtered.groupby("Village_Name")["Total_Water_Drip_m3"]
          .sum().dropna().reset_index())
    vw = vw[vw["Total_Water_Drip_m3"] > 0]
    if not vw.empty:
        fig = px.pie(
            vw, values="Total_Water_Drip_m3", names="Village_Name",
            color_discrete_sequence=PALETTE, hole=0.45,
        )
        fig.update_traces(textinfo="percent+label",
                          textfont=dict(color="white", size=11))
        fig.update_layout(
            title=dict(text="Water Share by Village", font=dict(size=14)),
            height=400, **CHART_TEMPLATE,
        )
        st.plotly_chart(fig, use_container_width=True)

# ─── 5 · Water Efficiency Bubble ──────────────────────────────────────────────
st.markdown('<div class="section-title">⚡ Water Efficiency — Per Acre</div>', unsafe_allow_html=True)

eff = filtered[["Farmer_Name", "Crop_Name", "Area_Acre", "Total_Water_Drip_m3"]].dropna()
eff = eff[eff["Area_Acre"] > 0].copy()
eff["Water_Per_Acre"] = eff["Total_Water_Drip_m3"] / eff["Area_Acre"]

if not eff.empty:
    fig = px.scatter(
        eff, x="Area_Acre", y="Total_Water_Drip_m3",
        size="Water_Per_Acre", color="Crop_Name",
        hover_data=["Farmer_Name"],
        color_discrete_sequence=PALETTE,
        labels={"Area_Acre": "Area (Acres)", "Total_Water_Drip_m3": "Drip Water (m³)",
                "Water_Per_Acre": "m³/Acre", "Crop_Name": "Crop"},
    )
    fig.update_layout(
        title=dict(text="Water vs Area — bubble = m³ per Acre", font=dict(size=14)),
        height=430,
        xaxis=dict(gridcolor=CHART_COLORS["grid"]),
        yaxis=dict(gridcolor=CHART_COLORS["grid"]),
        legend=dict(font=dict(color=CHART_COLORS["text"])),
        **CHART_TEMPLATE,
    )
    st.plotly_chart(fig, use_container_width=True)

# ─── 6 · Irrigation Frequency & Water Source ──────────────────────────────────
st.markdown('<div class="section-title">🔄 Irrigation Frequency &amp; Water Source</div>',
            unsafe_allow_html=True)

c1, c2 = st.columns(2)

with c1:
    freq = filtered["No_Irrigations_Drip"].dropna()
    if not freq.empty:
        fig = px.histogram(
            freq, nbins=10,
            color_discrete_sequence=[CHART_COLORS["primary"]],
            labels={"value": "Irrigation Cycles", "count": "Fields"},
        )
        fig.update_layout(
            title=dict(text="Distribution of Irrigation Cycles", font=dict(size=14)),
            xaxis_title="Cycles", yaxis_title="Fields",
            showlegend=False, height=380,
            xaxis=dict(gridcolor=CHART_COLORS["grid"]),
            yaxis=dict(gridcolor=CHART_COLORS["grid"]),
            **CHART_TEMPLATE,
        )
        st.plotly_chart(fig, use_container_width=True)

with c2:
    sc = filtered["Water_Source"].dropna().value_counts().reset_index()
    sc.columns = ["Source", "Count"]
    if not sc.empty:
        fig = px.pie(
            sc, values="Count", names="Source",
            color_discrete_sequence=[CHART_COLORS["primary"], CHART_COLORS["secondary"],
                                     CHART_COLORS["accent"]],
            hole=0.5,
        )
        fig.update_traces(textinfo="percent+label",
                          textfont=dict(color="white", size=11))
        fig.update_layout(
            title=dict(text="Water Source Split", font=dict(size=14)),
            height=380, **CHART_TEMPLATE,
        )
        st.plotly_chart(fig, use_container_width=True)

# ─── 7 · Heatmap ──────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">🗓️ Farmer × Date Meter Heatmap</div>', unsafe_allow_html=True)

if not meter_df.empty:
    pv = meter_df.pivot_table(index="Farmer", columns="Date", values="Meter_m3", aggfunc="sum")
    for c in DATE_ORDER:
        if c not in pv.columns:
            pv[c] = np.nan
    pv = pv[DATE_ORDER]

    fig = px.imshow(
        pv,
        color_continuous_scale=[[0, "#0d1117"], [0.35, "#1f6feb"], [0.7, "#58a6ff"], [1, "#a5d6ff"]],
        labels={"color": "Meter (m³)"},
        aspect="auto",
    )
    fig.update_layout(
        title=dict(text="Meter Readings by Farmer & Date", font=dict(size=14)),
        height=max(380, len(pv) * 26),
        **CHART_TEMPLATE,
    )
    st.plotly_chart(fig, use_container_width=True)

# ─── 8 · Data Table ───────────────────────────────────────────────────────────
st.markdown('<div class="section-title">📋 Detailed Data</div>', unsafe_allow_html=True)

show_cols = [
    "Farmer_Name", "Village_Name", "Crop_Name", "Area_Acre", "Water_Source",
    "No_Irrigations_Drip", "Total_Water_Drip_m3", "Avg_Water_Drip_m3",
    "Meter_30Jan", "Meter_10Feb", "Meter_18Feb", "Total_Water_Consumption",
]
disp = filtered[show_cols].dropna(how="all")
disp.columns = [
    "Farmer", "Village", "Crop", "Acres", "Source",
    "# Irrigations", "Drip Water (m³)", "Avg/Irrigation (m³)",
    "Meter 30 Jan", "Meter 10 Feb", "Meter 18 Feb", "Total Consumption",
]
st.dataframe(disp, use_container_width=True, height=400)

# ─── Footer ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center; padding:28px 0 10px 0; color:{CHART_COLORS['muted']}; font-size:0.75rem;">
    Amazon Farmer Irrigation Project — {dataset_name} | Data as of Feb 2026
</div>
""", unsafe_allow_html=True)
