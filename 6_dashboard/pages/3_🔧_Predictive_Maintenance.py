"""
Predictive Maintenance Dashboard Page
Displays maintenance predictions and recommendations
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="Predictive Maintenance - AIRP", page_icon="🔧", layout="wide")

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
</style>
""", unsafe_allow_html=True)

# INLINE AIRLINE MAPPING
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

# Header with navigation
col1, col2 = st.columns([6, 1])
with col1:
    st.title("🔧 Predictive Maintenance")
    st.markdown("AI-powered maintenance predictions based on flight patterns and wear indicators")
with col2:
    st.markdown("")
    st.markdown("")
    if st.button("🏠 Home", type="primary"):
        st.switch_page("app.py")

# Load maintenance predictions
@st.cache_data
def load_maintenance_data():
    data_path = Path('data/maintenance_predictions.csv')
    
    if not data_path.exists():
        st.error("""
        ⚠️ **Maintenance predictions not found!**
        
        Please run the analysis first:
        ```bash
        python 7_advanced_analytics/predictive_maintenance.py
        ```
        """)
        return None
    
    df = pd.read_csv(data_path)
    
    # Clean data
    if 'primary_callsign' in df.columns:
        df['primary_callsign'] = df['primary_callsign'].fillna('UNKNOWN')
    
    # Add airline names if not present
    if 'airline_code' in df.columns:
        if 'airline_name' not in df.columns:
            df['airline_name'] = df['airline_code'].apply(get_airline_name)
        # Also update existing airline names
        df['airline_name'] = df['airline_code'].apply(get_airline_name)
    elif 'primary_callsign' in df.columns:
        # Extract from callsign
        df['airline_code'] = df['primary_callsign'].str[:3].str.upper()
        df['airline_name'] = df['airline_code'].apply(get_airline_name)
    
    return df

df = load_maintenance_data()

if df is not None and len(df) > 0:
    st.markdown("---")
    
    # Key Metrics
    st.markdown("### 📊 System Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total = len(df)
        st.metric("Total Aircraft", f"{total}")
    
    with col2:
        critical = (df['maintenance_priority'] == 'CRITICAL').sum()
        st.metric("🔴 Critical", f"{critical}", 
                 delta=f"{critical/total*100:.1f}%" if total > 0 else "0%",
                 delta_color="inverse")
    
    with col3:
        high = (df['maintenance_priority'] == 'HIGH').sum()
        st.metric("🟠 High Priority", f"{high}",
                 delta=f"{high/total*100:.1f}%" if total > 0 else "0%",
                 delta_color="inverse")
    
    with col4:
        total_cost = df['estimated_cost_usd'].sum()
        st.metric("💰 Estimated Costs", f"${total_cost/1000:.0f}K")
    
    st.markdown("---")
    
    # Priority Distribution
    st.markdown("### 🎯 Maintenance Priority Distribution")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Pie chart
        priority_counts = df['maintenance_priority'].value_counts()
        
        colors = {
            'CRITICAL': '#dc2626',
            'HIGH': '#f97316', 
            'MEDIUM': '#fbbf24',
            'LOW': '#22c55e'
        }
        
        fig_pie = go.Figure(data=[go.Pie(
            labels=priority_counts.index,
            values=priority_counts.values,
            marker=dict(colors=[colors.get(p, '#gray') for p in priority_counts.index]),
            hole=0.4
        )])
        
        fig_pie.update_layout(
            height=300,
            showlegend=True,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Bar chart
        fig_bar = go.Figure(data=[go.Bar(
            x=priority_counts.index,
            y=priority_counts.values,
            marker=dict(color=[colors.get(p, '#gray') for p in priority_counts.index])
        )])
        
        fig_bar.update_layout(
            xaxis_title="Priority Level",
            yaxis_title="Number of Aircraft",
            height=300,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)
    
    st.markdown("---")
    
    # Filters
    st.markdown("### 🔍 Filter Aircraft")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        priority_filter = st.multiselect(
            "Priority Level",
            options=['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'],
            default=['CRITICAL', 'HIGH']
        )
    
    with col2:
        if 'airline_name' in df.columns and 'airline_code' in df.columns:
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
        min_score = st.slider(
            "Minimum Maintenance Score",
            min_value=0,
            max_value=100,
            value=60
        )
    
    # Apply filters
    filtered_df = df.copy()
    
    if priority_filter:
        filtered_df = filtered_df[filtered_df['maintenance_priority'].isin(priority_filter)]
    
    if airline_filter and 'airline_code' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['airline_code'].isin(airline_filter)]
    
    filtered_df = filtered_df[filtered_df['maintenance_score'] >= min_score]
    
    st.markdown(f"**Found {len(filtered_df)} aircraft matching criteria**")
    
    if len(filtered_df) > 0:
        st.markdown("---")
        
        # Aircraft List
        st.markdown("### ✈️ Aircraft Maintenance List")
        
        # Build display dataframe
        display_cols = []
        col_mapping = {}
        
        if 'primary_callsign' in filtered_df.columns:
            display_cols.append('primary_callsign')
            col_mapping['primary_callsign'] = 'Callsign'
        
        if 'airline_name' in filtered_df.columns:
            display_cols.append('airline_name')
            col_mapping['airline_name'] = 'Airline'
        
        display_cols.extend([
            'icao24', 'total_flights', 'total_hours', 
            'maintenance_score', 'maintenance_priority',
            'maintenance_window', 'estimated_cost_usd'
        ])
        
        col_mapping.update({
            'icao24': 'Aircraft ID',
            'total_flights': 'Flights',
            'total_hours': 'Hours',
            'maintenance_score': 'Score',
            'maintenance_priority': 'Priority',
            'maintenance_window': 'Window',
            'estimated_cost_usd': 'Est. Cost (USD)'
        })
        
        available_cols = [c for c in display_cols if c in filtered_df.columns]
        display_df = filtered_df[available_cols].copy()
        display_df.rename(columns={k: v for k, v in col_mapping.items() if k in display_df.columns}, inplace=True)
        
        # Format columns
        if 'Hours' in display_df.columns:
            display_df['Hours'] = display_df['Hours'].round(0)
        if 'Score' in display_df.columns:
            display_df['Score'] = display_df['Score'].round(1)
        if 'Est. Cost (USD)' in display_df.columns:
            display_df['Est. Cost (USD)'] = display_df['Est. Cost (USD)'].apply(lambda x: f"${x:,.0f}")
        
        # Add priority indicators
        if 'Priority' in display_df.columns:
            indicators = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🟢'}
            display_df.insert(0, '⚠️', display_df['Priority'].map(indicators))
        
        st.dataframe(display_df, use_container_width=True, height=400, hide_index=True)
        
        st.markdown("---")
        
        # Detailed View
        st.markdown("### 📋 Detailed Aircraft Analysis")
        
        # Create selection options
        aircraft_options = []
        for idx in range(len(filtered_df)):
            row = filtered_df.iloc[idx]
            callsign = row.get('primary_callsign', 'UNKNOWN')
            icao24 = row.get('icao24', 'N/A')
            priority = row.get('maintenance_priority', 'N/A')
            
            label = f"{callsign} ({icao24}) - {priority}"
            aircraft_options.append((idx, label))
        
        selected_idx = st.selectbox(
            "Select aircraft for detailed analysis:",
            options=[opt[0] for opt in aircraft_options],
            format_func=lambda i: next(opt[1] for opt in aircraft_options if opt[0] == i)
        )
        
        selected_aircraft = filtered_df.iloc[selected_idx]
        
        # Aircraft Header
        callsign = selected_aircraft.get('primary_callsign', 'UNKNOWN')
        airline = selected_aircraft.get('airline_name', 'Unknown')
        icao24 = selected_aircraft.get('icao24', 'N/A')
        
        st.markdown(f"## 🔧 {callsign}")
        if airline != 'Unknown':
            st.caption(f"{airline} | Aircraft ID: {icao24}")
        else:
            st.caption(f"Aircraft ID: {icao24}")
        
        # Priority Badge
        priority = selected_aircraft.get('maintenance_priority', 'UNKNOWN')
        priority_colors = {
            'CRITICAL': 'red',
            'HIGH': 'orange',
            'MEDIUM': 'yellow',
            'LOW': 'green'
        }
        
        st.markdown(f"**Priority:** :{priority_colors.get(priority, 'gray')}[{priority}]")
        
        st.markdown("---")
        
        # Key Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            score = selected_aircraft.get('maintenance_score', 0)
            st.metric("Maintenance Score", f"{score:.1f}/100")
            
            window = selected_aircraft.get('maintenance_window', 'N/A')
            st.metric("Maintenance Window", window)
        
        with col2:
            flights = selected_aircraft.get('total_flights', 0)
            st.metric("Total Flights", f"{flights:,.0f}")
            
            hours = selected_aircraft.get('total_hours', 0)
            st.metric("Flight Hours", f"{hours:,.0f}")
        
        with col3:
            distance = selected_aircraft.get('total_distance', 0)
            st.metric("Total Distance", f"{distance:,.0f} km")
            
            avg_risk = selected_aircraft.get('avg_risk_score', 0)
            st.metric("Avg Risk Score", f"{avg_risk:.1f}")
        
        with col4:
            cost = selected_aircraft.get('estimated_cost_usd', 0)
            st.metric("Estimated Cost", f"${cost:,.0f}")
            
            avg_eff = selected_aircraft.get('avg_efficiency', 0)
            st.metric("Avg Efficiency", f"{avg_eff:.1f}%")
        
        st.markdown("---")
        
        # Wear Indicators
        st.markdown("### 📊 Wear & Tear Indicators")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Factor breakdown
            factors = {
                'Flight Hours': selected_aircraft.get('hours_factor', 0) * 100,
                'Distance': selected_aircraft.get('distance_factor', 0) * 100,
                'Risk History': selected_aircraft.get('risk_factor', 0) * 100,
                'Efficiency Decline': selected_aircraft.get('efficiency_factor', 0) * 100,
                'Risk Ratio': selected_aircraft.get('risk_ratio_factor', 0) * 100,
                'Variability': selected_aircraft.get('variance_factor', 0) * 100,
            }
            
            fig = go.Figure(data=[go.Bar(
                x=list(factors.values()),
                y=list(factors.keys()),
                orientation='h',
                marker=dict(
                    color=list(factors.values()),
                    colorscale='RdYlGn_r',
                    cmin=0,
                    cmax=100
                )
            )])
            
            fig.update_layout(
                xaxis_title="Wear Factor (0-100)",
                height=350,
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white')
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Performance trends
            st.markdown("#### Performance Metrics")
            
            metrics = {
                'High-Risk Flights': selected_aircraft.get('high_risk_flights', 0),
                'Inefficient Flights': selected_aircraft.get('inefficient_flights', 0),
                'Days in Operation': selected_aircraft.get('days_in_operation', 0),
            }
            
            for metric, value in metrics.items():
                st.metric(metric, f"{value:,.0f}")
            
            st.markdown("---")
            
            # Risk ratio
            risk_ratio = selected_aircraft.get('risk_ratio', 0) * 100
            st.metric("High-Risk Flight %", f"{risk_ratio:.1f}%",
                     delta=f"{risk_ratio - 20:.1f}%" if risk_ratio > 20 else None,
                     delta_color="inverse")
        
        st.markdown("---")
        
        # Primary Causes
        st.markdown("### 🔍 Maintenance Causes")
        
        causes = selected_aircraft.get('primary_causes', 'Not available')
        
        if causes and causes != 'Not available':
            cause_list = [c.strip() for c in causes.split(',')]
            
            cols = st.columns(min(len(cause_list), 3))
            for idx, cause in enumerate(cause_list):
                with cols[idx % 3]:
                    st.warning(f"⚠️ {cause}")
        else:
            st.info("No specific causes identified - general wear and tear")
        
        st.markdown("---")
        
        # Recommendations
        st.markdown("### 💡 Maintenance Recommendations")
        
        recommendations = selected_aircraft.get('recommendations', 'Not available')
        
        if recommendations and recommendations != 'Not available':
            rec_list = [r.strip() for r in recommendations.split('|')]
            
            for rec in rec_list:
                if '⚠️' in rec or '🔴' in rec:
                    st.error(rec)
                elif '🔧' in rec:
                    st.warning(rec)
                elif '✅' in rec:
                    st.success(rec)
                else:
                    st.info(rec)
        else:
            st.info("Continue routine maintenance schedule")
        
        st.markdown("---")
        
        # Cost Breakdown
        st.markdown("### 💰 Cost Estimate Breakdown")
        
        col1, col2 = st.columns(2)
        
        with col1:
            priority = selected_aircraft.get('maintenance_priority', 'LOW')
            
            # Base costs reference
            base_costs_ref = {
                'CRITICAL': 150000,
                'HIGH': 75000,
                'MEDIUM': 35000,
                'LOW': 15000
            }
            
            base = base_costs_ref.get(priority, 15000)
            actual = selected_aircraft.get('estimated_cost_usd', 0)
            
            st.metric("Base Cost", f"${base:,.0f}")
            st.metric("Total Multipliers & Additions", f"${actual - base:,.0f}")
            st.metric("**Final Estimate**", f"**${actual:,.0f}**")
            
            # Show individual components
            st.markdown("---")
            st.markdown("**Cost Components:**")
            
            hours = selected_aircraft.get('total_hours', 0)
            if hours > 1000:
                st.info(f"🕐 Flight Hours: {hours:.0f} → High usage (2.5x multiplier)")
            elif hours > 500:
                st.info(f"🕐 Flight Hours: {hours:.0f} → Moderate-heavy (2.0x multiplier)")
            elif hours > 200:
                st.info(f"🕐 Flight Hours: {hours:.0f} → Moderate (1.5x multiplier)")
            else:
                st.info(f"🕐 Flight Hours: {hours:.0f} → Light usage (1.2x multiplier)")
            
            flights = selected_aircraft.get('total_flights', 0)
            cycle_cost = flights * 500
            st.info(f"✈️ Flight Cycles: {flights:.0f} → ${cycle_cost:,.0f}")
            
            distance = selected_aircraft.get('total_distance', 0)
            dist_cost = (distance / 10000) * 100
            st.info(f"📏 Distance: {distance:,.0f} km → ${dist_cost:,.0f}")
        
        with col2:
            st.info("""
            **Cost Factors Explained:**
            
            **Base Cost:**
            - Depends on priority level
            - Starting point for calculations
            
            **Flight Hours:**
            - More hours = higher multiplier
            - Reflects component wear
            
            **Flight Cycles:**
            - Each takeoff/landing = $500
            - High stress on airframe
            
            **Distance:**
            - $100 per 10,000 km
            - Component degradation
            
            **Risk & Efficiency:**
            - Additional penalties applied
            - Based on performance history
            
            💡 **Note:** These are estimates per maintenance event, not annual costs. Actual costs vary by:
            - Parts availability
            - Labor rates  
            - Location
            - Specific repairs needed
            """)
    
    else:
        st.info("No aircraft match your filter criteria. Adjust filters to see results.")

else:
    st.warning("No maintenance data available. Please run the analysis first.")

st.markdown("---")

# Footer
st.info("""
💡 **About Predictive Maintenance:**

This system analyzes flight patterns, performance metrics, and operational history to predict maintenance needs before failures occur. 
Maintenance scores are calculated using:
- Flight hours and distance
- Risk history and patterns
- Efficiency degradation
- Component stress indicators

**Benefits:**
- Prevent unexpected failures
- Optimize maintenance schedules
- Reduce downtime
- Lower total costs
""")