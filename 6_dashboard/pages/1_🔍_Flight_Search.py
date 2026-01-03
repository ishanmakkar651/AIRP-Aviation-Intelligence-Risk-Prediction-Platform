"""
Flight Search - COMPLETE with Inline Airline Names
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(page_title="Flight Search - AIRP", page_icon="🔍", layout="wide")

# INLINE AIRLINE MAPPING - No external imports needed
AIRLINE_NAMES = {
    'AIC': 'Air India', 'IGO': 'IndiGo', 'VTI': 'Vistara', 'SEJ': 'SpiceJet',
    'GOW': 'Go First', 'AXB': 'AirAsia India', 'JAI': 'Alliance Air', 
    'AIE': 'Air India Express', 'AKJ': 'Akasa Air',
    'UAE': 'Emirates', 'ETD': 'Etihad Airways', 'QTR': 'Qatar Airways',
    'FDB': 'FlyDubai', 'GFA': 'Gulf Air', 'RJA': 'Royal Jordanian',
    'MSR': 'EgyptAir', 'MEA': 'Middle East Airlines', 'SVA': 'Saudia',
    'OMA': 'Oman Air', 'KAC': 'Kuwait Airways', 'ABY': 'Air Arabia',
    'ETH': 'Ethiopian Airlines', 'SAA': 'South African Airways',
    'RAM': 'Royal Air Maroc', 'KQA': 'Kenya Airways',
    'SIA': 'Singapore Airlines', 'THA': 'Thai Airways', 'MAS': 'Malaysia Airlines',
    'CPA': 'Cathay Pacific', 'KAL': 'Korean Air', 'JAL': 'Japan Airlines',
    'ANA': 'All Nippon Airways', 'VNA': 'Vietnam Airlines',
    'BAW': 'British Airways', 'AFR': 'Air France', 'DLH': 'Lufthansa',
    'KLM': 'KLM', 'SWR': 'Swiss', 'SAS': 'SAS', 'IBE': 'Iberia',
    'THY': 'Turkish Airlines', 'AFL': 'Aeroflot', 'VIR': 'Virgin Atlantic',
    'AAL': 'American Airlines', 'UAL': 'United Airlines', 'DAL': 'Delta Air Lines',
    'SWA': 'Southwest Airlines', 'JBU': 'JetBlue', 'ACA': 'Air Canada',
    'QFA': 'Qantas', 'ANZ': 'Air New Zealand',
    'FDX': 'FedEx', 'UPS': 'UPS', 'CLX': 'Cargolux',
}

def get_airline_name(code):
    """Get full airline name from 3-letter code"""
    if pd.isna(code) or str(code).strip() == '':
        return 'Unknown'
    code = str(code).upper().strip()[:3]
    return AIRLINE_NAMES.get(code, code)

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
</style>
""", unsafe_allow_html=True)

# Header with navigation
col1, col2 = st.columns([6, 1])
with col1:
    st.title("🔍 Flight Search & Analysis")
    st.markdown("Search for specific flights and view detailed analysis")
with col2:
    st.markdown("")
    st.markdown("")
    if st.button("🏠 Home", type="primary"):
        st.switch_page("app.py")

# Load data
@st.cache_data
def load_data():
    data_dir = Path('data')
    
    # Load all three CSVs
    operational = pd.read_csv(data_dir / 'operational_features.csv')
    risk = pd.read_csv(data_dir / 'risk_scores.csv')
    fuel = pd.read_csv(data_dir / 'fuel_anomalies.csv')
    
    # Start with operational (has callsigns)
    merged = operational.copy()
    
    # Merge risk scores
    if 'trajectory_id' in risk.columns:
        risk_cols = ['trajectory_id', 'final_risk_score', 'risk_level']
        if 'is_anomaly' in risk.columns:
            risk_cols.append('is_anomaly')
        merged = merged.merge(risk[risk_cols], on='trajectory_id', how='left', suffixes=('', '_risk'))
    
    # Merge fuel data
    if 'trajectory_id' in fuel.columns:
        fuel_cols = ['trajectory_id', 'fuel_anomaly', 'primary_inefficiency_cause']
        merged = merged.merge(fuel[fuel_cols], on='trajectory_id', how='left', suffixes=('', '_fuel'))
    
    # Clean callsigns
    if 'callsign' in merged.columns:
        merged['callsign'] = merged['callsign'].astype(str)
        merged['callsign'] = merged['callsign'].replace(['nan', 'None', ''], pd.NA)
        merged['callsign'] = merged['callsign'].str.strip()
        
        # Extract airline code and name
        merged['airline_code'] = merged['callsign'].str[:3].str.upper()
        merged['airline_name'] = merged['airline_code'].apply(get_airline_name)
    else:
        merged['callsign'] = 'UNKNOWN'
        merged['airline_code'] = 'UNK'
        merged['airline_name'] = 'Unknown'
    
    # Add defaults
    defaults = {
        'start_time': pd.NA,
        'duration_minutes': 0.0,
        'total_distance_km': 0.0,
        'fuel_efficiency_score': 0.0,
        'efficiency_category': 'Unknown',
        'final_risk_score': 0.0,
        'risk_level': 'LOW',
        'max_altitude_ft': 0.0,
        'avg_speed_kmh': 0.0,
        'fuel_anomaly': 1,
        'primary_inefficiency_cause': 'None'
    }
    
    for col, default in defaults.items():
        if col not in merged.columns:
            merged[col] = default
    
    return merged

df = load_data()

# Debug sidebar
with st.sidebar:
    st.markdown("### 📊 Data Status")
    total = len(df)
    if 'callsign' in df.columns:
        with_callsigns = df['callsign'].notna().sum()
        st.success(f"✅ Callsigns: {with_callsigns:,}/{total:,}")
        if 'airline_name' in df.columns:
            unique_airlines = df[df['airline_name'] != 'Unknown']['airline_name'].nunique()
            st.info(f"Airlines: {unique_airlines}")
    else:
        st.error("❌ No callsigns found")

st.markdown("---")

# Search Interface
st.markdown("### Search Flights")

col1, col2, col3, col4 = st.columns(4)

with col1:
    search_callsign = st.text_input("Search by Callsign", placeholder="e.g., AIC180")

with col2:
    # Airline filter - Simple version
    if 'airline_code' in df.columns and 'airline_name' in df.columns:
        # Get unique airlines
        airline_df = df[['airline_code', 'airline_name']].drop_duplicates()
        airline_df = airline_df[airline_df['airline_name'] != 'Unknown']
        airline_df = airline_df.sort_values('airline_name')
        
        # Create display options
        airline_display = []
        airline_code_map = {}
        for _, row in airline_df.iterrows():
            code = str(row['airline_code'])
            name = str(row['airline_name'])
            display = f"{code} - {name}"
            airline_display.append(display)
            airline_code_map[display] = code
        
        selected_airlines_display = st.multiselect(
            "Filter by Airline",
            options=airline_display,
            default=[]
        )
        
        # Convert back to codes
        airline_filter = [airline_code_map[disp] for disp in selected_airlines_display]
    else:
        airline_filter = []

with col3:
    risk_filter = st.multiselect(
        "Filter by Risk Level",
        options=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'],
        default=[]
    )

with col4:
    efficiency_filter = st.multiselect(
        "Filter by Efficiency",
        options=['Excellent', 'Good', 'Fair', 'Poor'],
        default=[]
    )

# Apply filters
filtered_df = df.copy()

if search_callsign and 'callsign' in filtered_df.columns:
    filtered_df = filtered_df[
        filtered_df['callsign'].str.contains(search_callsign, case=False, na=False)
    ]

if airline_filter and 'airline_code' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['airline_code'].isin(airline_filter)]

if risk_filter and 'risk_level' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['risk_level'].isin(risk_filter)]

if efficiency_filter and 'efficiency_category' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['efficiency_category'].isin(efficiency_filter)]

st.markdown(f"**Found {len(filtered_df):,} flights matching criteria**")

if len(filtered_df) > 0:
    # Display results
    st.markdown("### Search Results")
    
    display_cols = []
    col_mapping = {}
    
    if 'callsign' in filtered_df.columns:
        display_cols.append('callsign')
        col_mapping['callsign'] = 'Flight'
    
    if 'airline_name' in filtered_df.columns:
        display_cols.append('airline_name')
        col_mapping['airline_name'] = 'Airline'
    
    if 'start_time' in filtered_df.columns:
        display_cols.append('start_time')
        col_mapping['start_time'] = 'Start Time'
    
    for col, label in [
        ('duration_minutes', 'Duration (min)'),
        ('total_distance_km', 'Distance (km)'),
        ('fuel_efficiency_score', 'Efficiency'),
        ('efficiency_category', 'Category'),
        ('final_risk_score', 'Risk Score'),
        ('risk_level', 'Risk Level')
    ]:
        if col in filtered_df.columns:
            display_cols.append(col)
            col_mapping[col] = label
    
    display_df = filtered_df[display_cols].copy()
    display_df.rename(columns=col_mapping, inplace=True)
    
    # Format numbers
    if 'Duration (min)' in display_df.columns:
        display_df['Duration (min)'] = display_df['Duration (min)'].round(0)
    if 'Distance (km)' in display_df.columns:
        display_df['Distance (km)'] = display_df['Distance (km)'].round(0)
    if 'Efficiency' in display_df.columns:
        display_df['Efficiency'] = display_df['Efficiency'].round(1)
    if 'Risk Score' in display_df.columns:
        display_df['Risk Score'] = display_df['Risk Score'].round(1)
    
    # Add risk indicators
    if 'Risk Level' in display_df.columns:
        indicators = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🟢'}
        display_df.insert(0, '🚨', display_df['Risk Level'].map(indicators))
    
    st.dataframe(display_df, width="stretch", height=400, hide_index=True)
    
    st.markdown("---")
    
    # Detailed View
    st.markdown("### Detailed Flight Analysis")
    
    # Create flight options
    flight_options = []
    for idx in range(len(filtered_df)):
        row = filtered_df.iloc[idx]
        callsign = row.get('callsign', pd.NA)
        airline_name = row.get('airline_name', 'Unknown')
        trajectory_id = row.get('trajectory_id', idx)
        
        if pd.notna(callsign) and str(callsign) not in ['', 'nan', 'None', 'UNKNOWN']:
            if airline_name != 'Unknown':
                label = f"{callsign} - {airline_name} (ID: {trajectory_id})"
            else:
                label = f"{callsign} (ID: {trajectory_id})"
        else:
            label = f"Flight {idx+1} (ID: {trajectory_id})"
        
        flight_options.append((idx, label))
    
    selected_idx = st.selectbox(
        "Select a flight for detailed analysis:",
        options=[opt[0] for opt in flight_options],
        format_func=lambda i: next(opt[1] for opt in flight_options if opt[0] == i)
    )
    
    selected_flight = filtered_df.iloc[selected_idx]
    
    # Flight header
    callsign = selected_flight.get('callsign', pd.NA)
    airline_name = selected_flight.get('airline_name', 'Unknown')
    trajectory_id = selected_flight.get('trajectory_id', 'N/A')
    
    if pd.notna(callsign) and str(callsign) not in ['', 'nan', 'None', 'UNKNOWN']:
        if airline_name != 'Unknown':
            st.markdown(f"## ✈️ {callsign} - {airline_name}")
        else:
            st.markdown(f"## ✈️ {callsign}")
        st.caption(f"Trajectory ID: {trajectory_id}")
    else:
        st.markdown(f"## ✈️ Flight Analysis")
        st.caption(f"Trajectory ID: {trajectory_id}")
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        eff_score = selected_flight.get('fuel_efficiency_score', 0)
        st.metric("Efficiency Score", f"{eff_score:.1f}/100")
        eff_cat = selected_flight.get('efficiency_category', 'Unknown')
        st.metric("Category", eff_cat)
    
    with col2:
        risk_score = selected_flight.get('final_risk_score', 0)
        st.metric("Risk Score", f"{risk_score:.1f}/100")
        risk_level = selected_flight.get('risk_level', 'LOW')
        risk_indicators = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🟢'}
        st.metric("Risk Level", f"{risk_indicators.get(risk_level, '⚪')} {risk_level}")
    
    with col3:
        duration = selected_flight.get('duration_minutes', 0)
        st.metric("Duration", f"{duration:.0f} min")
        distance = selected_flight.get('total_distance_km', 0)
        st.metric("Distance", f"{distance:.0f} km")
    
    with col4:
        max_alt = selected_flight.get('max_altitude_ft', 0)
        st.metric("Max Altitude", f"{max_alt:.0f} ft")
        avg_speed = selected_flight.get('avg_speed_kmh', 0)
        st.metric("Avg Speed", f"{avg_speed:.0f} km/h")
    
    st.markdown("---")
    
    # Performance Breakdown
    st.markdown("### Performance Breakdown")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Efficiency Components")
        
        components = {
            'Altitude Stability': selected_flight.get('altitude_stability_score', 0),
            'Speed Stability': selected_flight.get('speed_stability_score', 0),
            'Route Directness': selected_flight.get('route_directness_score', 0),
        }
        
        fig = go.Figure(data=[
            go.Bar(
                x=list(components.values()),
                y=list(components.keys()),
                orientation='h',
                marker=dict(
                    color=list(components.values()),
                    colorscale='RdYlGn',
                    cmin=0,
                    cmax=100
                )
            )
        ])
        fig.update_layout(
            xaxis_title="Score (0-100)",
            height=300,
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
        st.plotly_chart(fig, width="stretch")
    
    with col2:
        st.markdown("#### Risk Factors")
        
        risk_factors = {
            'Speed Anomaly': selected_flight.get('is_speed_anomaly', 0) == 1,
            'Altitude Anomaly': selected_flight.get('is_altitude_anomaly', 0) == 1,
            'High Speed Variability': selected_flight.get('high_speed_variability', 0) == 1,
            'High Altitude Variability': selected_flight.get('high_altitude_variability', 0) == 1,
            'Complex Maneuvers': selected_flight.get('complex_maneuvers', 0) == 1,
        }
        
        active_risks = [k for k, v in risk_factors.items() if v]
        
        if active_risks:
            st.warning(f"**Active Risk Factors:** {len(active_risks)}")
            for risk in active_risks:
                st.markdown(f"- ⚠️ {risk}")
        else:
            st.success("✅ No major risk factors detected")
    
    st.markdown("---")
    
    # Inefficiency Analysis
    fuel_anom = selected_flight.get('fuel_anomaly', 1)
    if fuel_anom == -1:
        st.markdown("### 🔥 Fuel Inefficiency Detected")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            cause = selected_flight.get('primary_inefficiency_cause', 'Unknown')
            st.error(f"""
            **Primary Cause:**  
            {cause}
            
            **Efficiency Score:**  
            {eff_score:.1f}/100
            """)
        
        with col2:
            st.markdown("**Recommendations:**")
            
            if 'Altitude' in str(cause):
                st.markdown("""
                - ✅ Minimize unnecessary altitude changes
                - ✅ Maintain steady cruise altitude
                - ✅ Better coordination with ATC
                """)
            elif 'Speed' in str(cause):
                st.markdown("""
                - ✅ Maintain consistent cruise speed
                - ✅ Reduce speed fluctuations
                - ✅ Optimize throttle management
                """)
            else:
                st.markdown("""
                - ✅ Review flight procedures
                - ✅ Analyze operational constraints
                - ✅ Consult with operations team
                """)
    else:
        st.success("### ✅ Efficient Operation")

else:
    st.info("No flights found matching your search criteria.")

st.markdown("---")
st.markdown("💡 **Tip:** Use filters to narrow down flights, then select one for detailed analysis.")
