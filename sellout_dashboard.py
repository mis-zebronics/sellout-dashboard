import streamlit as st
import pandas as pd
import numpy as np

# 1. Page Settings configuration
st.set_page_config(
    page_title="Sellout Tracker Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Reusable UI Function for Custom Metric Cards (Matches the dark UI theme)
def custom_metric_card(label, main_value, subtext=None, border_color="#1f77b4"):
    # Generates a muted small gray subtitle block if an exact number is supplied
    subtext_html = f"<div style='font-size: 12px; color: #8a94a6; margin-top: 4px; font-weight: 400;'>({subtext})</div>" if subtext else ""
    
    return f"""
    <div style="
        background-color: #1a1f2c; 
        padding: 16px; 
        border-radius: 6px; 
        border-left: 4px solid {border_color};
        color: white;
        min-height: 100px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    ">
        <div style="font-size: 13px; color: #a3a8b4; font-weight: 500; letter-spacing: 0.4px;">{label}</div>
        <div style="font-size: 24px; font-weight: 700; margin-top: 6px; line-height: 1.1;">{main_value}</div>
        {subtext_html}
    </div>
    """

# ---------------------------------------------------------
# SIDEBAR NAVIGATION & FILTERS
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("## Dashboard Selector")
    st.write("---")
    
    st.markdown("**Choose Dashboard:**")
    # Custom stylized layout matching the selected state circle icons
    dashboard_mode = st.radio(
        label="Choose Dashboard Layout",
        options=["🔴 Sellout Tracker", "⚪ Sellin Tracker"],
        label_visibility="collapsed"
    )
    
    st.write("")
    # Sidebar alert info block
    st.info("💡 Select a dashboard to view analytics")
    
    # Expandable column mapping panel
    with st.expander("🔹 Column Mapping", expanded=False):
        st.caption("Map custom sheet parameters here.")
        
    st.write("---")
    st.markdown("### 🔵 Filters")
    
    # Selection Filter Dropdowns
    vert_filter = st.selectbox("Vert", ["All", "Vertical A", "Vertical B"])
    plat_filter = st.selectbox("Plat", ["All", "Platform A", "Platform B"])


# ---------------------------------------------------------
# MAIN DASHBOARD PANEL
# ---------------------------------------------------------
st.title("📊 Sellout Tracker Dashboard")

# Row ingestion alert indicator
st.success("Loaded 3,605 rows from Sellout Tracker")
st.write("")

# --- Section 1: Overall Performance Metrics ---
st.subheader("📊 Overall Performance")

# Grid initialization (6 columns)
col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.markdown(
        custom_metric_card(
            label="FY 25-26 Units", 
            main_value="68.83L", 
            subtext="68,83,000", 
            border_color="#2b7fff"  # Blue accent
        ), 
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        custom_metric_card(
            label="FY 26-27 Units", 
            main_value="15.07L", 
            subtext="15,07,000", 
            border_color="#2ea44f"  # Green accent
        ), 
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        custom_metric_card(
            label="Unit Growth", 
            main_value="-78.11%", 
            border_color="#d73a49"  # Red accent
        ), 
        unsafe_allow_html=True
    )

with col4:
    st.markdown(
        custom_metric_card(
            label="FY 25-26 G", 
            main_value="₹ 655.74Cr", 
            border_color="#2b7fff"  # Blue accent
        ), 
        unsafe_allow_html=True
    )

with col5:
    st.markdown(
        custom_metric_card(
            label="FY 26-27 G", 
            main_value="₹ 118.95Cr", 
            border_color="#2ea44f"  # Green accent
        ), 
        unsafe_allow_html=True
    )

with col6:
    st.markdown(
        custom_metric_card(
            label="GMS Growth", 
            main_value="-81.86%", 
            border_color="#d73a49"  # Red accent
        ), 
        unsafe_allow_html=True
    )

st.write("")
st.write("---")

# --- Section 2: Trend Analysis Area ---
st.subheader("📅 Monthly Trend")
st.markdown("**Units: LY vs Plan vs CY**")

# Generating structured mock data for the trend chart visualization line
chart_weeks = [f"Wk {i}" for i in range(1, 13)]
mock_data = pd.DataFrame({
    'LY': np.random.uniform(0.5, 0.9, 12),
    'Plan': np.random.uniform(0.6, 1.1, 12),
    'CY': np.random.uniform(0.4, 0.8, 12)
}, index=chart_weeks)

# Displays standard native chart framework matching layout bounds
st.line_chart(mock_data, height=280)
