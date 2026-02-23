import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import gspread
from google.oauth2.service_account import Credentials

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

# Google Sheets URLs — mapped to the same region names
# These are read from .streamlit/secrets.toml
GSHEET_URLS = {}

try:
    gs_cfg = st.secrets["google_sheets"]
    if gs_cfg.get("hyderabad_url", "").startswith("https://"):
        GSHEET_URLS["Hyderabad Region"] = gs_cfg["hyderabad_url"]
    if gs_cfg.get("bangalore_url", "").startswith("https://"):
        GSHEET_URLS["Bangalore Region"] = gs_cfg["bangalore_url"]
except Exception:
    pass  # secrets not configured yet — Google Sheets option won't appear

GSHEETS_AVAILABLE = len(GSHEET_URLS) > 0

# ─── CSS — Clean Light Theme ──────────────────────────────────────────────────
st.markdown("""
<style>
    /* ── Global ── */
    .stApp {
        background: #f8f9fb;
    }
    section[data-testid="stSidebar"] {
        background: #1e293b;
        border-right: 1px solid #334155;
    }
    section[data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h5 {
        color: #f8fafc !important;
    }
    section[data-testid="stSidebar"] .stRadio label,
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stFileUploader label {
        color: #e2e8f0 !important;
    }
    section[data-testid="stSidebar"] hr {
        border-color: #475569 !important;
    }
    section[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] {
        background: #334155;
        border-color: #475569;
    }
    section[data-testid="stSidebar"] .stRadio [role="radiogroup"] label {
        background: transparent;
    }
    section[data-testid="stSidebar"] .stRadio [role="radiogroup"] label[data-checked="true"] {
        background: #334155;
    }
    header[data-testid="stHeader"] {
        background: transparent;
    }

    /* ── KPI Cards ── */
    .kpi-card {
        background: #ffffff;
        border: 1px solid #e1e4e8;
        border-radius: 12px;
        padding: 20px 16px;
        text-align: center;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
        transition: border-color 0.2s, transform 0.15s, box-shadow 0.2s;
    }
    .kpi-card:hover {
        border-color: #0969da;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(9,105,218,0.10);
    }
    .kpi-icon { font-size: 1.6rem; margin-bottom: 4px; }
    .kpi-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #0969da;
        margin: 6px 0 2px 0;
        line-height: 1.2;
    }
    .kpi-label {
        font-size: 0.75rem;
        font-weight: 600;
        color: #656d76;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .kpi-sub {
        font-size: 0.78rem;
        color: #1a7f37;
        margin-top: 4px;
    }

    /* ── Section Titles ── */
    .section-title {
        font-size: 1.15rem;
        font-weight: 600;
        color: #1f2328;
        border-left: 3px solid #0969da;
        padding-left: 12px;
        margin: 36px 0 14px 0;
    }

    /* ── Sidebar dataset badge ── */
    .dataset-badge {
        background: #334155;
        border: 1px solid #475569;
        border-radius: 8px;
        padding: 10px 12px;
        text-align: center;
        margin-bottom: 12px;
    }
    .dataset-badge .region {
        font-size: 1.05rem;
        font-weight: 600;
        color: #60a5fa !important;
    }
    .dataset-badge .file {
        font-size: 0.7rem;
        color: #94a3b8 !important;
        word-break: break-all;
    }
</style>
""", unsafe_allow_html=True)

# ─── Color Palette for Charts ─────────────────────────────────────────────────
CHART_COLORS = {
    "primary": "#0969da",
    "secondary": "#1a7f37",
    "accent": "#bf8700",
    "highlight": "#cf222e",
    "purple": "#8250df",
    "cyan": "#0598bc",
    "text": "#1f2328",
    "muted": "#656d76",
    "bg_card": "#ffffff",
    "bg_plot": "#ffffff",
    "grid": "#e1e4e8",
}
PALETTE = [
    "#0969da", "#1a7f37", "#bf8700", "#cf222e", "#8250df",
    "#0598bc", "#d4a72c", "#54aeff", "#4ac26b", "#e16f24",
]
CHART_TEMPLATE = dict(
    template="plotly_white",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor=CHART_COLORS["bg_plot"],
    font=dict(color=CHART_COLORS["text"], size=12),
    xaxis=dict(
        title_font=dict(color=CHART_COLORS["text"], size=13),
        tickfont=dict(color=CHART_COLORS["text"], size=11),
        gridcolor=CHART_COLORS["grid"],
    ),
    yaxis=dict(
        title_font=dict(color=CHART_COLORS["text"], size=13),
        tickfont=dict(color=CHART_COLORS["text"], size=11),
        gridcolor=CHART_COLORS["grid"],
    ),
    margin=dict(l=20, r=20, t=50, b=20),
)


# ─── Expected Columns (for upload validation) ─────────────────────────────────
EXPECTED_COLUMNS = [
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

NUMERIC_COLS = [
    "Total_Area", "Area_Acre", "No_Irrigations_Drip", "Total_Water_Drip_m3",
    "Irrigation_Duration_Drip", "Avg_Water_Drip_m3",
    "Meter_30Jan", "Water_Liters_30Jan", "Water_PerAcre_30Jan",
    "Meter_10Feb", "Water_Liters_10Feb", "Water_PerAcre_10Feb",
    "Meter_18Feb", "Water_Liters_18Feb", "Water_PerAcre_18Feb",
    "Total_Water_Consumption", "Water_Saved_m3",
]

FARMER_FIELDS = [
    "Sr_No", "Sap_No", "Farmer_Name", "Village_Name", "Mandal",
    "Mobile_No", "State", "Total_Area", "Irrigation_Method", "Water_Source",
]


def _clean_df(df: pd.DataFrame) -> pd.DataFrame:
    """Assign columns, clean rows, convert types, forward-fill."""
    if len(df.columns) != len(EXPECTED_COLUMNS):
        raise ValueError(
            f"Expected {len(EXPECTED_COLUMNS)} columns but got {len(df.columns)}.\n"
            "Please make sure you are using the standard irrigation Excel template."
        )
    df.columns = EXPECTED_COLUMNS
    df = df[~df["Sr_No"].isin(["Sr No", "Total"])].reset_index(drop=True)
    for c in NUMERIC_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df[FARMER_FIELDS] = df[FARMER_FIELDS].ffill()
    return df


# ─── Data Loading ─────────────────────────────────────────────────────────────
@st.cache_data
def load_data(file_path: str) -> pd.DataFrame:
    df = pd.read_excel(file_path, sheet_name="Sheet1", header=None, skiprows=1)
    return _clean_df(df)


def load_data_from_upload(file_bytes) -> pd.DataFrame:
    """Load and validate an uploaded Excel file."""
    df = pd.read_excel(file_bytes, sheet_name="Sheet1" if "Sheet1" in pd.ExcelFile(file_bytes).sheet_names else 0, header=None, skiprows=1)
    return _clean_df(df)


@st.cache_data(ttl=10, show_spinner=False)  # cache for 10 seconds, then re-fetch live data
def load_data_from_gsheet(sheet_url: str) -> pd.DataFrame:
    """Pull live data from a Google Sheet and return a cleaned DataFrame."""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scopes
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_url(sheet_url).sheet1
    rows = sheet.get_all_values()
    # rows[0] = group headers, rows[1] = field headers, data from rows[2:]
    df = pd.DataFrame(rows[1:])  # skip group header row
    return _clean_df(df)


# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💧 Irrigation Dashboard")
    st.markdown("---")

    # ── Data Source ──
    source_options = ["📁 Local Excel"]
    if GSHEETS_AVAILABLE:
        source_options.insert(0, "☁️ Google Sheets (Live)")
    st.markdown("##### 🔌 Data Source")
    data_source = st.radio(
        "Source", source_options, index=0, label_visibility="collapsed",
    )

    st.markdown("---")

    # ── Dataset Selector ──
    st.markdown("##### 📂 Select Dataset")
    dataset_name = st.selectbox(
        "Dataset",
        list(DATASETS.keys()),
        label_visibility="collapsed",
    )
    file_name, region_label = DATASETS[dataset_name]

    # Show live badge when using Google Sheets
    if data_source.startswith("☁️") and dataset_name in GSHEET_URLS:
        st.markdown(f"""
        <div class="dataset-badge">
            <div class="region" style="color:{CHART_COLORS['secondary']};">🟢 Live — Google Sheets</div>
            <div class="file">Auto-refreshes every 5 min</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🔄 Refresh Now", width="stretch"):
            st.cache_data.clear()
            st.rerun()
        # Auto-refresh the page every 5 minutes for live updates
        st.markdown(
            '<meta http-equiv="refresh" content="300">',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ── File Uploader (only for local mode) ──
    uploaded_file = None
    if data_source == "📁 Local Excel":
        st.markdown("##### 📤 Upload New Excel")
        uploaded_file = st.file_uploader(
            "Drop an Excel file here",
            type=["xlsx", "xls"],
            label_visibility="collapsed",
            help="Upload a new irrigation Excel file (must follow the standard template with 45 columns).",
        )
        if uploaded_file:
            st.markdown(f"""
            <div class="dataset-badge">
                <div class="region">📄 Uploaded File</div>
                <div class="file">{uploaded_file.name}</div>
            </div>
            """, unsafe_allow_html=True)

# ─── Load Data ─────────────────────────────────────────────────────────────────
upload_error = None
gsheet_error = None

if data_source.startswith("☁️") and dataset_name in GSHEET_URLS:
    # ── Google Sheets (live) ──
    try:
        df = load_data_from_gsheet(GSHEET_URLS[dataset_name])
        dataset_name = f"{dataset_name} (Live)"
    except Exception as e:
        gsheet_error = str(e)
        df = load_data(file_name)  # fallback to local Excel
elif uploaded_file is not None:
    try:
        df = load_data_from_upload(uploaded_file)
        dataset_name = f"Uploaded — {uploaded_file.name}"
    except ValueError as e:
        upload_error = str(e)
        df = load_data(file_name)
    except Exception as e:
        upload_error = f"Could not read file: {e}"
        df = load_data(file_name)
else:
    df = load_data(file_name)

filtered = df.copy()

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

# Show upload error if any
if upload_error:
    st.error(f"⚠️ **Upload failed:** {upload_error}")
    st.info("Falling back to the selected dataset. Please upload a file that uses the standard irrigation template (45 columns).")

# Show Google Sheets error if any
if gsheet_error:
    st.error(f"⚠️ **Google Sheets failed:** {gsheet_error}")
    st.info("Falling back to local Excel file. Check that the sheet is shared with the service account and secrets are configured.")

st.markdown("")
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

# ─── Monthly Water Saved (Bar Graph) ──────────────────────────────────────────
st.markdown('<div class="section-title">💧 Monthly Water Saved (Estimated)</div>', unsafe_allow_html=True)

# Derive monthly totals from meter readings (drip usage per month)
jan_drip = filtered["Water_Liters_30Jan"].dropna().sum() / 1000  # convert liters → m³
feb_drip = (filtered["Water_Liters_10Feb"].dropna().sum() + filtered["Water_Liters_18Feb"].dropna().sum()) / 1000

# Estimate flood water as 2.5× drip, so saved = flood − drip = 1.5× drip
jan_saved = jan_drip * 1.5
feb_saved = feb_drip * 1.5

monthly_df = pd.DataFrame({
    "Month": ["January 2026", "February 2026"],
    "Water_Saved_m3": [jan_saved, feb_saved],
})

if monthly_df["Water_Saved_m3"].sum() > 0:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=monthly_df["Month"],
        y=monthly_df["Water_Saved_m3"],
        text=[f"{v:,.0f} m³" for v in monthly_df["Water_Saved_m3"]],
        textposition="outside",
        textfont=dict(color=CHART_COLORS["text"], size=12),
        marker_color=[CHART_COLORS["primary"], CHART_COLORS["secondary"]],
        marker_line=dict(width=0),
        width=0.45,
    ))
    fig.update_layout(
        title=dict(text="Estimated Water Saved Per Month (m³)", font=dict(size=14)),
        xaxis_title="Month",
        yaxis_title="Water Saved (m³)",
        yaxis_rangemode="tozero",
        height=400,
        **CHART_TEMPLATE,
    )
    st.plotly_chart(fig, width="stretch")
else:
    st.info("No meter reading data available to calculate monthly water savings.")

# ─── Water Saving Goal Tracker ─────────────────────────────────────────────────
st.markdown('<div class="section-title">🎯 Water Saving Goal Tracker</div>', unsafe_allow_html=True)

# Target: save enough water to offset all flood usage → target = estimated_flood_water
# Actual saved so far = water_saved_m3 (computed in KPI section above)
saving_target_m3 = estimated_flood_water  # total flood estimate = 2.5 × drip
actual_saved_m3 = water_saved_m3          # flood − drip = 1.5 × drip
goal_pct = min((actual_saved_m3 / saving_target_m3) * 100, 100) if saving_target_m3 > 0 else 0

c1, c2 = st.columns([1, 1])

with c1:
    # Gauge chart
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=goal_pct,
        number=dict(suffix="%", font=dict(size=42, color=CHART_COLORS["text"])),
        delta=dict(reference=100, valueformat=".1f", suffix="%",
                   increasing=dict(color=CHART_COLORS["secondary"]),
                   decreasing=dict(color=CHART_COLORS["highlight"])),
        title=dict(text="Goal Achieved", font=dict(size=16, color=CHART_COLORS["text"])),
        gauge=dict(
            axis=dict(range=[0, 100], ticksuffix="%",
                      tickcolor=CHART_COLORS["muted"],
                      tickfont=dict(color=CHART_COLORS["muted"])),
            bar=dict(color=CHART_COLORS["secondary"], thickness=0.75),
            bgcolor=CHART_COLORS["grid"],
            borderwidth=0,
            steps=[
                dict(range=[0, 40], color="rgba(207,34,46,0.12)"),
                dict(range=[40, 70], color="rgba(191,135,0,0.12)"),
                dict(range=[70, 100], color="rgba(26,127,55,0.12)"),
            ],
            threshold=dict(
                line=dict(color=CHART_COLORS["highlight"], width=3),
                thickness=0.8,
                value=100,
            ),
        ),
    ))
    fig.update_layout(height=350, **CHART_TEMPLATE)
    st.plotly_chart(fig, width="stretch")

with c2:
    # Summary breakdown
    remaining_m3 = max(saving_target_m3 - actual_saved_m3, 0)
    st.markdown(f"""
    <div class="kpi-card" style="padding:24px 20px; text-align:left; margin-top:10px;">
        <div style="font-size:0.85rem; color:{CHART_COLORS['muted']}; text-transform:uppercase; letter-spacing:1px; margin-bottom:14px;">
            Savings Breakdown
        </div>
        <div style="display:flex; justify-content:space-between; margin-bottom:12px;">
            <span style="color:{CHART_COLORS['text']};">🎯 Target (Flood Offset)</span>
            <span style="color:{CHART_COLORS['accent']}; font-weight:700;">{saving_target_m3:,.0f} m³</span>
        </div>
        <div style="display:flex; justify-content:space-between; margin-bottom:12px;">
            <span style="color:{CHART_COLORS['text']};">✅ Saved So Far</span>
            <span style="color:{CHART_COLORS['secondary']}; font-weight:700;">{actual_saved_m3:,.0f} m³</span>
        </div>
        <div style="display:flex; justify-content:space-between; margin-bottom:16px;">
            <span style="color:{CHART_COLORS['text']};">🔻 Remaining</span>
            <span style="color:{CHART_COLORS['highlight']}; font-weight:700;">{remaining_m3:,.0f} m³</span>
        </div>
        <div style="background:{CHART_COLORS['grid']}; border-radius:8px; height:14px; overflow:hidden;">
            <div style="background:linear-gradient(90deg, {CHART_COLORS['secondary']}, {CHART_COLORS['primary']});
                        width:{goal_pct:.1f}%; height:100%; border-radius:8px;"></div>
        </div>
        <div style="text-align:center; margin-top:8px; color:{CHART_COLORS['muted']}; font-size:0.78rem;">
            {goal_pct:.1f}% of target achieved
        </div>
    </div>
    """, unsafe_allow_html=True)

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
            fillcolor="rgba(9,105,218,0.08)",
        ))
        fig.update_layout(
            title=dict(text="Cumulative Meter Readings (m³)", font=dict(size=14)),
            xaxis_title="Date", yaxis_title="Total (m³)",
            height=400, **CHART_TEMPLATE,
        )
        st.plotly_chart(fig, width="stretch")

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
            height=400, **CHART_TEMPLATE,
        )
        st.plotly_chart(fig, width="stretch")

# ─── 2 · Crop-wise ────────────────────────────────────────────────────────────
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
            **CHART_TEMPLATE,
        )
        st.plotly_chart(fig, width="stretch")

with c2:
    ca = (filtered.groupby("Crop_Name")["Area_Acre"].sum().dropna().reset_index())
    ca = ca[ca["Area_Acre"] > 0]
    if not ca.empty:
        fig = px.pie(
            ca, values="Area_Acre", names="Crop_Name",
            color_discrete_sequence=PALETTE, hole=0.45,
        )
        fig.update_traces(textinfo="percent+label",
                          textfont=dict(color="#1f2328", size=11))
        fig.update_layout(
            title=dict(text="Area by Crop (Acres)", font=dict(size=14)),
            height=400, **CHART_TEMPLATE,
        )
        st.plotly_chart(fig, width="stretch")

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
            legend=dict(font=dict(color=CHART_COLORS["text"])),
            **CHART_TEMPLATE,
        )
        st.plotly_chart(fig, width="stretch")

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
                          textfont=dict(color="#1f2328", size=11))
        fig.update_layout(
            title=dict(text="Water Share by Village", font=dict(size=14)),
            height=400, **CHART_TEMPLATE,
        )
        st.plotly_chart(fig, width="stretch")

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
        legend=dict(font=dict(color=CHART_COLORS["text"])),
        **CHART_TEMPLATE,
    )
    st.plotly_chart(fig, width="stretch")

# ─── Footer ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center; padding:28px 0 10px 0; color:{CHART_COLORS['muted']}; font-size:0.75rem;">
    Amazon Farmer Irrigation Project — {dataset_name} | Data as of Feb 2026
</div>
""", unsafe_allow_html=True)
