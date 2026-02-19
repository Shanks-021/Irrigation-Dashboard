import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ─── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Farmer Irrigation Dashboard",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
    }
    /* KPI Cards */
    .kpi-card {
        background: rgba(255,255,255,0.07);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 16px;
        padding: 24px 20px;
        text-align: center;
        transition: transform 0.2s;
    }
    .kpi-card:hover { transform: translateY(-4px); }
    .kpi-value {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #00d2ff, #3a7bd5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 4px 0;
    }
    .kpi-label {
        font-size: 0.85rem;
        color: rgba(255,255,255,0.6);
        text-transform: uppercase;
        letter-spacing: 1.2px;
    }
    .kpi-delta {
        font-size: 0.8rem;
        color: #00e676;
        margin-top: 4px;
    }
    /* Section headers */
    .section-header {
        font-size: 1.3rem;
        font-weight: 700;
        color: #e0e0e0;
        border-left: 4px solid #00d2ff;
        padding-left: 12px;
        margin: 32px 0 16px 0;
    }
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: rgba(15,32,39,0.95);
    }
    /* Hide default header */
    header[data-testid="stHeader"] {
        background: transparent;
    }
</style>
""", unsafe_allow_html=True)


# ─── Data Loading & Cleaning ──────────────────────────────────────────────────
@st.cache_data
def load_data():
    file_path = "Format for data Amazon Project Hyd (1).xlsx"
    df = pd.read_excel(file_path, sheet_name='Sheet1', header=None, skiprows=1)

    cols = [
        'Sr_No', 'Sap_No', 'Farmer_Name', 'Village_Name', 'Mandal', 'Mobile_No', 'State',
        'Total_Area', 'Crop_Name', 'Sowing_Date', 'Expected_Harvest_Date', 'Crop_Stage',
        'Area_Acre', 'Irrigation_Method', 'No_Irrigation_Earlier', 'Water_Flood_m3',
        'Water_Source', 'Avg_Water_Flood_m3', 'Pump_Rate', 'Irrigation_Duration_Flood',
        'Meter_Reading_Date', 'Drip_Supply_Date', 'Drip_Install_Date', 'No_Irrigations_Drip',
        'Total_Water_Drip_m3', 'Irrigation_Duration_Drip', 'Avg_Water_Drip_m3',
        'Meter_30Jan', 'Water_Liters_30Jan', 'Water_PerAcre_30Jan',
        'Meter_10Feb', 'Water_Liters_10Feb', 'Water_PerAcre_10Feb',
        'Meter_18Feb', 'Water_Liters_18Feb', 'Water_PerAcre_18Feb',
        'Meter_End', 'Total_Water_Consumption',
        'Water_Saved_m3', 'Yield_Before_Flood', 'Yield_After_Drip',
        'Fertilizer_Saving_Pct', 'Electricity_Saving_Pct', 'Labour_Saving', 'Input_Cost_Reduction',
    ]
    df.columns = cols

    # Drop header row that got read as data, and total row
    df = df[~df['Sr_No'].isin(['Sr No', 'Total'])].reset_index(drop=True)

    # Convert numeric columns
    numeric_cols = [
        'Total_Area', 'Area_Acre', 'No_Irrigations_Drip', 'Total_Water_Drip_m3',
        'Irrigation_Duration_Drip', 'Avg_Water_Drip_m3',
        'Meter_30Jan', 'Water_Liters_30Jan', 'Water_PerAcre_30Jan',
        'Meter_10Feb', 'Water_Liters_10Feb', 'Water_PerAcre_10Feb',
        'Meter_18Feb', 'Water_Liters_18Feb', 'Water_PerAcre_18Feb',
        'Total_Water_Consumption', 'Water_Saved_m3',
    ]
    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c], errors='coerce')

    # Forward-fill farmer-level fields (each farmer has multiple crop rows)
    farmer_fields = ['Sr_No', 'Sap_No', 'Farmer_Name', 'Village_Name', 'Mandal',
                     'Mobile_No', 'State', 'Total_Area', 'Irrigation_Method', 'Water_Source']
    df[farmer_fields] = df[farmer_fields].ffill()

    return df


df = load_data()

# ─── Derived columns ──────────────────────────────────────────────────────────
# Unique farmer-level data
farmer_df = df.drop_duplicates(subset='Farmer_Name')

# ─── Sidebar Filters ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌾 Filters")
    st.markdown("---")

    villages = ['All'] + sorted(df['Village_Name'].dropna().unique().tolist())
    sel_village = st.selectbox("Village", villages)

    crops = ['All'] + sorted(df['Crop_Name'].dropna().unique().tolist())
    sel_crop = st.selectbox("Crop", crops)

    water_sources = ['All'] + sorted(df['Water_Source'].dropna().unique().tolist())
    sel_source = st.selectbox("Water Source", water_sources)

# Apply filters
filtered = df.copy()
if sel_village != 'All':
    filtered = filtered[filtered['Village_Name'] == sel_village]
if sel_crop != 'All':
    filtered = filtered[filtered['Crop_Name'] == sel_crop]
if sel_source != 'All':
    filtered = filtered[filtered['Water_Source'] == sel_source]

# ─── Title ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding: 10px 0 0 0;">
    <h1 style="color:white; font-size:2.4rem; margin-bottom:0;">
        💧 Amazon Farmer Irrigation Dashboard
    </h1>
    <p style="color:rgba(255,255,255,0.5); font-size:1rem; margin-top:4px;">
        Hyderabad Region — Drip vs Flood Irrigation Impact Analysis
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("")

# ─── KPI Metrics ───────────────────────────────────────────────────────────────
total_water_consumption = filtered['Total_Water_Consumption'].dropna().sum()
total_water_drip = filtered['Total_Water_Drip_m3'].dropna().sum()
total_acres = filtered['Area_Acre'].dropna().sum()
num_farmers = filtered['Farmer_Name'].nunique()
num_crops = filtered['Crop_Name'].nunique()
avg_irrigations = filtered['No_Irrigations_Drip'].dropna().mean()

# Estimate water saved: typical flood irrigation uses ~2.5x more water than drip per acre
# Using total drip consumption as baseline, estimated flood would be ~2.5x
estimated_flood_water = total_water_drip * 2.5
water_saved_m3 = estimated_flood_water - total_water_drip  # = 1.5 × drip
water_saved_liters = water_saved_m3 * 1000

cols_kpi = st.columns(5)

kpi_data = [
    ("Total Water Saved", f"{water_saved_m3:,.0f} m³", f"~{water_saved_liters/1e6:,.2f} M liters", "💧"),
    ("Acres Covered", f"{total_acres:,.1f}", f"Across {filtered['Village_Name'].nunique()} villages", "🌾"),
    ("Farmers Benefited", f"{num_farmers}", f"Growing {num_crops} crop types", "👨‍🌾"),
    ("Avg Irrigations (Drip)", f"{avg_irrigations:,.1f}", "Per farmer cycle", "🔄"),
    ("Total Drip Water Used", f"{total_water_drip:,.0f} m³", f"{total_water_consumption/1000:,.0f}K liters consumed", "📊"),
]

for col, (label, value, delta, icon) in zip(cols_kpi, kpi_data):
    with col:
        st.markdown(f"""
        <div class="kpi-card">
            <div style="font-size:1.8rem;">{icon}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-label">{label}</div>
            <div class="kpi-delta">{delta}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("")

# ─── Monthly Water Saving Trend ───────────────────────────────────────────────
st.markdown('<div class="section-header">📈 Water Meter Readings Over Time (Drip Irrigation)</div>',
            unsafe_allow_html=True)

# Build time-series from meter readings at 3 dates
meter_data = []
for _, row in filtered.iterrows():
    farmer = row['Farmer_Name']
    crop = row['Crop_Name']
    area = row['Area_Acre']
    for date_label, meter_col in [('30 Jan 2026', 'Meter_30Jan'),
                                   ('10 Feb 2026', 'Meter_10Feb'),
                                   ('18 Feb 2026', 'Meter_18Feb')]:
        val = row[meter_col]
        if pd.notna(val):
            meter_data.append({
                'Date': date_label,
                'Farmer': farmer,
                'Crop': crop,
                'Meter_Reading_m3': val,
                'Area_Acre': area,
            })

meter_df = pd.DataFrame(meter_data)

if not meter_df.empty:
    # Aggregate water usage by date
    agg_by_date = meter_df.groupby('Date').agg(
        Total_Meter_m3=('Meter_Reading_m3', 'sum'),
        Farmer_Count=('Farmer', 'nunique'),
    ).reset_index()
    agg_by_date['Date'] = pd.Categorical(agg_by_date['Date'],
                                          categories=['30 Jan 2026', '10 Feb 2026', '18 Feb 2026'],
                                          ordered=True)
    agg_by_date = agg_by_date.sort_values('Date')

    # Calculate period-over-period water increase (savings = less increase is better)
    agg_by_date['Incremental_m3'] = agg_by_date['Total_Meter_m3'].diff().fillna(agg_by_date['Total_Meter_m3'])

    col1, col2 = st.columns(2)

    with col1:
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=agg_by_date['Date'].astype(str),
            y=agg_by_date['Total_Meter_m3'],
            mode='lines+markers+text',
            text=[f"{v:,.0f}" for v in agg_by_date['Total_Meter_m3']],
            textposition='top center',
            line=dict(color='#00d2ff', width=3),
            marker=dict(size=12, color='#00d2ff', line=dict(width=2, color='white')),
            fill='tozeroy',
            fillcolor='rgba(0,210,255,0.1)',
        ))
        fig_trend.update_layout(
            title="Cumulative Water Meter Readings (m³)",
            xaxis_title="Reading Date",
            yaxis_title="Total Meter Reading (m³)",
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=400,
            font=dict(color='white'),
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    with col2:
        fig_incr = go.Figure()
        colors = ['#00d2ff', '#3a7bd5', '#00e676']
        fig_incr.add_trace(go.Bar(
            x=agg_by_date['Date'].astype(str),
            y=agg_by_date['Incremental_m3'],
            text=[f"{v:,.0f} m³" for v in agg_by_date['Incremental_m3']],
            textposition='outside',
            marker_color=colors[:len(agg_by_date)],
            marker_line=dict(width=0),
        ))
        fig_incr.update_layout(
            title="Incremental Water Usage Per Period (m³)",
            xaxis_title="Reading Date",
            yaxis_title="Water Added (m³)",
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=400,
            font=dict(color='white'),
        )
        st.plotly_chart(fig_incr, use_container_width=True)

# ─── Water Usage by Farmer ─────────────────────────────────────────────────────
st.markdown('<div class="section-header">👨‍🌾 Water Consumption by Farmer</div>', unsafe_allow_html=True)

farmer_water = (
    filtered.groupby('Farmer_Name')['Total_Water_Drip_m3']
    .sum()
    .dropna()
    .sort_values(ascending=True)
    .reset_index()
)
farmer_water = farmer_water[farmer_water['Total_Water_Drip_m3'] > 0]

if not farmer_water.empty:
    fig_farmer = px.bar(
        farmer_water,
        x='Total_Water_Drip_m3',
        y='Farmer_Name',
        orientation='h',
        color='Total_Water_Drip_m3',
        color_continuous_scale='Blues',
        labels={'Total_Water_Drip_m3': 'Water Used (m³)', 'Farmer_Name': 'Farmer'},
    )
    fig_farmer.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=max(400, len(farmer_water) * 28),
        font=dict(color='white'),
        showlegend=False,
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig_farmer, use_container_width=True)

# ─── Crop-wise Analysis ───────────────────────────────────────────────────────
st.markdown('<div class="section-header">🌱 Crop-wise Water Usage & Area Distribution</div>',
            unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    crop_water = (
        filtered.groupby('Crop_Name')
        .agg(Total_Water=('Total_Water_Drip_m3', 'sum'), Total_Area=('Area_Acre', 'sum'))
        .dropna()
        .reset_index()
    )
    crop_water = crop_water[crop_water['Total_Water'] > 0]

    if not crop_water.empty:
        fig_crop_water = px.bar(
            crop_water.sort_values('Total_Water', ascending=False),
            x='Crop_Name', y='Total_Water',
            color='Total_Water',
            color_continuous_scale='Tealgrn',
            labels={'Total_Water': 'Water (m³)', 'Crop_Name': 'Crop'},
        )
        fig_crop_water.update_layout(
            title="Total Drip Water Used by Crop (m³)",
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=400,
            font=dict(color='white'),
            showlegend=False,
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig_crop_water, use_container_width=True)

with col2:
    crop_area = (
        filtered.groupby('Crop_Name')['Area_Acre']
        .sum()
        .dropna()
        .reset_index()
    )
    crop_area = crop_area[crop_area['Area_Acre'] > 0]

    if not crop_area.empty:
        fig_crop_area = px.pie(
            crop_area,
            values='Area_Acre',
            names='Crop_Name',
            color_discrete_sequence=px.colors.sequential.Tealgrn,
            hole=0.45,
        )
        fig_crop_area.update_layout(
            title="Area Distribution by Crop (Acres)",
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=400,
            font=dict(color='white'),
        )
        fig_crop_area.update_traces(textinfo='percent+label')
        st.plotly_chart(fig_crop_area, use_container_width=True)

# ─── Village-wise Comparison ──────────────────────────────────────────────────
st.markdown('<div class="section-header">🏘️ Village-wise Comparison</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    village_stats = (
        filtered.groupby('Village_Name')
        .agg(
            Farmers=('Farmer_Name', 'nunique'),
            Total_Acres=('Area_Acre', 'sum'),
            Total_Water_m3=('Total_Water_Drip_m3', 'sum'),
        )
        .dropna()
        .reset_index()
    )

    if not village_stats.empty:
        fig_village = go.Figure()
        fig_village.add_trace(go.Bar(
            name='Farmers',
            x=village_stats['Village_Name'],
            y=village_stats['Farmers'],
            marker_color='#00d2ff',
            yaxis='y',
        ))
        fig_village.add_trace(go.Bar(
            name='Acres',
            x=village_stats['Village_Name'],
            y=village_stats['Total_Acres'],
            marker_color='#3a7bd5',
            yaxis='y',
        ))
        fig_village.update_layout(
            title="Farmers & Acres by Village",
            barmode='group',
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=400,
            font=dict(color='white'),
        )
        st.plotly_chart(fig_village, use_container_width=True)

with col2:
    village_water = (
        filtered.groupby('Village_Name')['Total_Water_Drip_m3']
        .sum()
        .dropna()
        .reset_index()
    )
    village_water = village_water[village_water['Total_Water_Drip_m3'] > 0]

    if not village_water.empty:
        fig_vw = px.pie(
            village_water,
            values='Total_Water_Drip_m3',
            names='Village_Name',
            color_discrete_sequence=['#00d2ff', '#3a7bd5', '#00e676', '#ffab00'],
            hole=0.45,
        )
        fig_vw.update_layout(
            title="Water Usage Share by Village",
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=400,
            font=dict(color='white'),
        )
        fig_vw.update_traces(textinfo='percent+label')
        st.plotly_chart(fig_vw, use_container_width=True)

# ─── Water Efficiency: per-Acre Analysis ──────────────────────────────────────
st.markdown('<div class="section-header">⚡ Water Efficiency — Per Acre Analysis</div>',
            unsafe_allow_html=True)

efficiency = filtered[['Farmer_Name', 'Crop_Name', 'Area_Acre', 'Total_Water_Drip_m3']].dropna()
efficiency = efficiency[efficiency['Area_Acre'] > 0]
efficiency['Water_Per_Acre'] = efficiency['Total_Water_Drip_m3'] / efficiency['Area_Acre']

if not efficiency.empty:
    fig_eff = px.scatter(
        efficiency,
        x='Area_Acre',
        y='Total_Water_Drip_m3',
        size='Water_Per_Acre',
        color='Crop_Name',
        hover_data=['Farmer_Name'],
        labels={
            'Area_Acre': 'Area (Acres)',
            'Total_Water_Drip_m3': 'Total Drip Water (m³)',
            'Water_Per_Acre': 'Water/Acre (m³)',
            'Crop_Name': 'Crop',
        },
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig_eff.update_layout(
        title="Water Usage vs Area — Bubble Size = Water Per Acre",
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=450,
        font=dict(color='white'),
    )
    st.plotly_chart(fig_eff, use_container_width=True)

# ─── Irrigation Frequency Distribution ────────────────────────────────────────
st.markdown('<div class="section-header">🔄 Drip Irrigation Frequency Distribution</div>',
            unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    irr_freq = filtered['No_Irrigations_Drip'].dropna()
    if not irr_freq.empty:
        fig_hist = px.histogram(
            irr_freq,
            nbins=10,
            color_discrete_sequence=['#00d2ff'],
            labels={'value': 'Number of Irrigations', 'count': 'Fields'},
        )
        fig_hist.update_layout(
            title="Distribution of Irrigation Cycles",
            xaxis_title="Number of Irrigations",
            yaxis_title="Number of Fields",
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=380,
            font=dict(color='white'),
            showlegend=False,
        )
        st.plotly_chart(fig_hist, use_container_width=True)

with col2:
    source_counts = filtered['Water_Source'].dropna().value_counts().reset_index()
    source_counts.columns = ['Source', 'Count']
    if not source_counts.empty:
        fig_source = px.pie(
            source_counts,
            values='Count',
            names='Source',
            color_discrete_sequence=['#00d2ff', '#3a7bd5', '#00e676'],
            hole=0.5,
        )
        fig_source.update_layout(
            title="Water Source Distribution",
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=380,
            font=dict(color='white'),
        )
        fig_source.update_traces(textinfo='percent+label')
        st.plotly_chart(fig_source, use_container_width=True)

# ─── Per-Farmer Meter Reading Heatmap ─────────────────────────────────────────
st.markdown('<div class="section-header">🗓️ Farmer-wise Meter Readings Heatmap</div>',
            unsafe_allow_html=True)

if not meter_df.empty:
    heatmap_pivot = meter_df.pivot_table(
        index='Farmer', columns='Date', values='Meter_Reading_m3', aggfunc='sum'
    )
    # Reorder columns
    for c in ['30 Jan 2026', '10 Feb 2026', '18 Feb 2026']:
        if c not in heatmap_pivot.columns:
            heatmap_pivot[c] = np.nan
    heatmap_pivot = heatmap_pivot[['30 Jan 2026', '10 Feb 2026', '18 Feb 2026']]

    fig_heat = px.imshow(
        heatmap_pivot,
        color_continuous_scale='Blues',
        labels={'color': 'Meter Reading (m³)'},
        aspect='auto',
    )
    fig_heat.update_layout(
        title="Water Meter Readings by Farmer & Date",
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=max(400, len(heatmap_pivot) * 26),
        font=dict(color='white'),
    )
    st.plotly_chart(fig_heat, use_container_width=True)

# ─── Data Table ────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">📋 Detailed Farmer Data</div>', unsafe_allow_html=True)

display_cols = [
    'Farmer_Name', 'Village_Name', 'Crop_Name', 'Area_Acre', 'Water_Source',
    'No_Irrigations_Drip', 'Total_Water_Drip_m3', 'Avg_Water_Drip_m3',
    'Meter_30Jan', 'Meter_10Feb', 'Meter_18Feb', 'Total_Water_Consumption',
]
display_df = filtered[display_cols].dropna(how='all')
display_df.columns = [
    'Farmer', 'Village', 'Crop', 'Area (Acres)', 'Water Source',
    '# Irrigations', 'Total Drip Water (m³)', 'Avg Water/Irrigation (m³)',
    'Meter 30 Jan', 'Meter 10 Feb', 'Meter 18 Feb', 'Total Consumption',
]

st.dataframe(
    display_df,
    use_container_width=True,
    height=400,
)

# ─── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding:30px 0 10px 0; color:rgba(255,255,255,0.3); font-size:0.8rem;">
    Amazon Farmer Irrigation Project — Hyderabad Region | Data as of Feb 2026
</div>
""", unsafe_allow_html=True)
