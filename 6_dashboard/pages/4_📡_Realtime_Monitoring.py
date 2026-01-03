"""
Real-Time Flight Monitoring Dashboard
Live tracking of active flights with auto-refresh
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
from datetime import datetime
import json
import time

st.set_page_config(page_title="Live Monitoring - AIRP", page_icon="📡", layout="wide")

# Dark theme CSS
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        background-color: #1e1e1e !important;
    }
    .main {
        background-color: #0e1117;
    }
    h1, h2, h3 {
        color: #58a6ff !important;
    }
    [data-testid="stDataFrame"] {
        border: 1px solid #30363d;
        border-radius: 8px;
    }
    .stButton>button {
        width: 100%;
    }
    .live-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        background-color: #22c55e;
        border-radius: 50%;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }
</style>
""", unsafe_allow_html=True)

# Header with navigation
col1, col2 = st.columns([6, 1])
with col1:
    st.title("📡 Real-Time Flight Monitoring")
    st.markdown('<span class="live-indicator"></span> **LIVE** - Updates every 30 seconds', unsafe_allow_html=True)
with col2:
    st.markdown("")
    st.markdown("")
    if st.button("🏠 Home", type="primary"):
        st.switch_page("app.py")

# Auto-refresh mechanism
auto_refresh = st.sidebar.checkbox("🔄 Auto-Refresh", value=True)
refresh_interval = st.sidebar.slider("Refresh Interval (seconds)", 10, 120, 30)

# Load real-time data
@st.cache_data(ttl=refresh_interval)
def load_realtime_data():
    """Load latest flight snapshot"""
    data_path = Path('data/realtime/latest_snapshot.csv')
    stats_path = Path('data/realtime/summary_stats.json')
    
    if not data_path.exists():
        return None, None
    
    df = pd.read_csv(data_path)
    
    # Load stats
    stats = None
    if stats_path.exists():
        with open(stats_path, 'r') as f:
            stats = json.load(f)
    
    return df, stats

df, stats = load_realtime_data()

# Check if streaming is active
if df is None or len(df) == 0:
    st.warning("""
    ⚠️ **No live data available**
    
    Start the real-time streamer first:
    ```bash
    python 8_realtime_monitoring/realtime_streamer.py
    ```
    
    Or to run continuous streaming:
    ```python
    from realtime_streamer import RealTimeFlightStreamer
    streamer = RealTimeFlightStreamer()
    streamer.run_continuous_stream(interval=30)
    ```
    """)
    st.stop()

# Display last update time
if stats and 'timestamp' in stats:
    update_time = datetime.fromisoformat(stats['timestamp'].replace('Z', '+00:00'))
    time_ago = (datetime.now(update_time.tzinfo) - update_time).total_seconds()
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.metric("Last Update", update_time.strftime("%H:%M:%S UTC"))
    with col2:
        st.metric("Time Ago", f"{int(time_ago)} seconds")
    with col3:
        if time_ago < 60:
            st.success("🟢 LIVE")
        elif time_ago < 180:
            st.warning("🟡 RECENT")
        else:
            st.error("🔴 STALE")

st.markdown("---")

# Key Metrics
st.markdown("### 📊 Live System Status")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    total = len(df)
    st.metric("🛫 Active Flights", f"{total:,}")

with col2:
    if 'risk_level' in df.columns:
        critical = (df['risk_level'] == 'CRITICAL').sum()
        high = (df['risk_level'] == 'HIGH').sum()
        st.metric("⚠️ High Risk", f"{critical + high}",
                 delta=f"{(critical + high)/total*100:.1f}%" if total > 0 else "0%",
                 delta_color="inverse")

with col3:
    if 'baro_altitude' in df.columns:
        avg_alt = df['baro_altitude'].mean()
        st.metric("✈️ Avg Altitude", f"{avg_alt:,.0f} m")

with col4:
    if 'velocity' in df.columns:
        avg_speed = df['velocity'].mean() * 3.6  # Convert m/s to km/h
        st.metric("🚀 Avg Speed", f"{avg_speed:.0f} km/h")

with col5:
    if 'origin_country' in df.columns:
        countries = df['origin_country'].nunique()
        st.metric("🌍 Countries", f"{countries}")

st.markdown("---")

# Risk Distribution
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🎯 Risk Distribution")
    
    if 'risk_level' in df.columns:
        risk_counts = df['risk_level'].value_counts()
        
        colors = {
            'CRITICAL': '#dc2626',
            'HIGH': '#f97316',
            'MEDIUM': '#fbbf24',
            'LOW': '#22c55e'
        }
        
        # Ensure all levels are present
        for level in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            if level not in risk_counts:
                risk_counts[level] = 0
        
        fig = go.Figure(data=[go.Pie(
            labels=risk_counts.index,
            values=risk_counts.values,
            marker=dict(colors=[colors.get(r, '#gray') for r in risk_counts.index]),
            hole=0.4,
            textinfo='label+percent+value'
        )])
        
        fig.update_layout(
            height=350,
            showlegend=True,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
        
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("### 🌍 Flights by Country")
    
    if 'origin_country' in df.columns:
        country_counts = df['origin_country'].value_counts().head(10)
        
        fig = go.Figure(data=[go.Bar(
            x=country_counts.values,
            y=country_counts.index,
            orientation='h',
            marker=dict(color='#3b82f6')
        )])
        
        fig.update_layout(
            xaxis_title="Number of Flights",
            yaxis_title="Country",
            height=350,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
        
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Interactive Map
st.markdown("### 🗺️ Live Flight Map")

if 'latitude' in df.columns and 'longitude' in df.columns:
    # Prepare map data
    map_df = df[df['latitude'].notna() & df['longitude'].notna()].copy()
    
    # Color by risk level
    risk_colors = {
        'CRITICAL': '#dc2626',
        'HIGH': '#f97316',
        'MEDIUM': '#fbbf24',
        'LOW': '#22c55e'
    }
    
    map_df['color'] = map_df['risk_level'].map(risk_colors)
    map_df['size'] = map_df['risk_score'] / 10 + 5  # Size based on risk
    
    # Create hover text
    map_df['hover_text'] = map_df.apply(
        lambda x: f"<b>{x['callsign']}</b><br>" +
                  f"Country: {x['origin_country']}<br>" +
                  f"Altitude: {x['baro_altitude']:.0f} m<br>" +
                  f"Speed: {x['velocity']*3.6:.0f} km/h<br>" +
                  f"Risk: {x['risk_level']} ({x['risk_score']:.0f})",
        axis=1
    )
    
    fig = go.Figure()
    
    # Add flights by risk level
    for risk_level in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
        level_df = map_df[map_df['risk_level'] == risk_level]
        
        if len(level_df) > 0:
            fig.add_trace(go.Scattergeo(
                lon=level_df['longitude'],
                lat=level_df['latitude'],
                mode='markers',
                marker=dict(
                    size=level_df['size'],
                    color=level_df['color'],
                    line=dict(width=0.5, color='white')
                ),
                text=level_df['hover_text'],
                hoverinfo='text',
                name=f"{risk_level} ({len(level_df)})"
            ))
    
    fig.update_layout(
        geo=dict(
            projection_type='natural earth',
            showland=True,
            landcolor='#1e293b',
            coastlinecolor='#475569',
            showocean=True,
            oceancolor='#0f172a',
            showcountries=True,
            countrycolor='#475569',
            center=dict(lat=20, lon=78),  # Center on India
            projection_scale=2
        ),
        height=600,
        showlegend=True,
        legend=dict(
            bgcolor='rgba(30, 41, 59, 0.8)',
            font=dict(color='white')
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )
    
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Active Flights Table
st.markdown("### ✈️ Active Flights")

# Filters
col1, col2, col3 = st.columns(3)

with col1:
    risk_filter = st.multiselect(
        "Filter by Risk",
        options=['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'],
        default=[]
    )

with col2:
    if 'origin_country' in df.columns:
        countries = sorted(df['origin_country'].unique())
        country_filter = st.multiselect(
            "Filter by Country",
            options=countries,
            default=[]
        )
    else:
        country_filter = []

with col3:
    search_callsign = st.text_input("Search Callsign", placeholder="e.g., AIC180")

# Apply filters
filtered_df = df.copy()

if risk_filter:
    filtered_df = filtered_df[filtered_df['risk_level'].isin(risk_filter)]

if country_filter:
    filtered_df = filtered_df[filtered_df['origin_country'].isin(country_filter)]

if search_callsign:
    filtered_df = filtered_df[
        filtered_df['callsign'].str.contains(search_callsign, case=False, na=False)
    ]

st.markdown(f"**Showing {len(filtered_df):,} of {len(df):,} flights**")

# Display table
if len(filtered_df) > 0:
    display_cols = ['callsign', 'origin_country', 'baro_altitude', 'velocity', 
                   'vertical_rate', 'risk_score', 'risk_level', 'risk_factors']
    available_cols = [c for c in display_cols if c in filtered_df.columns]
    
    display_df = filtered_df[available_cols].copy()
    
    # Rename columns
    col_mapping = {
        'callsign': 'Flight',
        'origin_country': 'Country',
        'baro_altitude': 'Altitude (m)',
        'velocity': 'Speed (m/s)',
        'vertical_rate': 'V/S (m/s)',
        'risk_score': 'Risk Score',
        'risk_level': 'Risk Level',
        'risk_factors': 'Risk Factors'
    }
    
    display_df.rename(columns={k: v for k, v in col_mapping.items() if k in display_df.columns}, inplace=True)
    
    # Format numbers
    if 'Altitude (m)' in display_df.columns:
        display_df['Altitude (m)'] = display_df['Altitude (m)'].round(0)
    if 'Speed (m/s)' in display_df.columns:
        display_df['Speed (m/s)'] = display_df['Speed (m/s)'].round(1)
    if 'V/S (m/s)' in display_df.columns:
        display_df['V/S (m/s)'] = display_df['V/S (m/s)'].round(1)
    if 'Risk Score' in display_df.columns:
        display_df['Risk Score'] = display_df['Risk Score'].round(1)
    
    # Add risk indicators
    if 'Risk Level' in display_df.columns:
        indicators = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🟢'}
        display_df.insert(0, '⚠️', display_df['Risk Level'].map(indicators))
    
    st.dataframe(display_df, use_container_width=True, height=400, hide_index=True)
else:
    st.info("No flights match your filter criteria")

st.markdown("---")

# System Info
st.markdown("### ℹ️ System Information")

col1, col2 = st.columns(2)

with col1:
    st.info(f"""
    **Data Source:** OpenSky Network API  
    **Update Frequency:** {refresh_interval} seconds  
    **Auto-Refresh:** {'Enabled' if auto_refresh else 'Disabled'}  
    **Region:** India & surrounding areas
    """)

with col2:
    if stats:
        st.success(f"""
        **Last Fetch:** {stats.get('timestamp', 'Unknown')}  
        **Total Flights:** {stats.get('total_flights', 0):,}  
        **Unique Countries:** {stats.get('unique_countries', 0)}  
        **Avg Altitude:** {stats.get('avg_altitude', 0):,.0f} m
        """)

# Auto-refresh logic
if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()