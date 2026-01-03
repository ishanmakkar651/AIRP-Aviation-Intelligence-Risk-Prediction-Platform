"""
AI Assistant - COMPLETE with Inline Airline Names
"""

import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="AI Assistant - AIRP", page_icon="🤖", layout="wide")

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
    .stButton>button {
        background-color: #238636;
        color: white;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Header with navigation
col1, col2 = st.columns([6, 1])
with col1:
    st.title("🤖 AI Flight Operations Assistant")
    st.markdown("Ask questions about your flight data in natural language")
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
    
    # Clean callsigns and add airline info
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
        'final_risk_score': 0.0,
        'risk_level': 'LOW',
        'fuel_efficiency_score': 0.0,
        'duration_minutes': 0.0,
        'total_distance_km': 0.0,
        'primary_inefficiency_cause': 'None',
        'fuel_anomaly': 1,
        'hour_of_day': 0,
        'efficiency_category': 'Unknown'
    }
    
    for col, default in defaults.items():
        if col not in merged.columns:
            merged[col] = default
    
    return merged

df = load_data()

st.markdown("---")

# Example queries
st.markdown("### 💡 Example Questions")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **Risk Analysis:**
    - Which flights have the highest risk scores?
    - How many flights are classified as high risk?
    - Show me critical risk flights
    
    **Efficiency Questions:**
    - What's the average fuel efficiency?
    - Which flights are most inefficient?
    - Compare efficiency by time of day
    """)

with col2:
    st.markdown("""
    **Airline Performance:**
    - Which airline has the best efficiency?
    - Show me the top 5 airlines
    - Which airline is worst performing?
    - Compare EgyptAir vs Ethiopian Airlines
    - Compare Air India vs IndiGo
    - Rank all airlines by performance
    
    **Operational Insights:**
    - What causes fuel inefficiency?
    - When do most high-risk flights occur?
    - Show flights during peak hours
    """)

st.markdown("---")

# Query Interface
st.markdown("### Ask Your Question")

# Add helpful placeholder with rotating examples
user_query = st.text_input(
    "Enter your question:",
    placeholder="Try: Which airline has the best efficiency? or Compare Air India vs IndiGo",
    key="query_input"
)

if st.button("🔍 Analyze", type="primary"):
    if user_query:
        with st.spinner("Analyzing your question..."):
            query_lower = user_query.lower()
            response_found = False
            
            # Risk queries
            if "highest risk" in query_lower or "high risk" in query_lower:
                st.markdown("### 📊 Analysis Results: High Risk Flights")
                
                cols = ['callsign', 'airline_name', 'final_risk_score', 'risk_level', 'fuel_efficiency_score', 'duration_minutes']
                available_cols = [c for c in cols if c in df.columns]
                
                high_risk = df.nlargest(10, 'final_risk_score')[available_cols].copy()
                
                rename_map = {
                    'callsign': 'Flight',
                    'airline_name': 'Airline',
                    'final_risk_score': 'Risk Score',
                    'risk_level': 'Risk Level',
                    'fuel_efficiency_score': 'Efficiency',
                    'duration_minutes': 'Duration (min)'
                }
                high_risk.rename(columns={k: v for k, v in rename_map.items() if k in high_risk.columns}, inplace=True)
                
                # Format
                if 'Risk Score' in high_risk.columns:
                    high_risk['Risk Score'] = high_risk['Risk Score'].round(1)
                if 'Efficiency' in high_risk.columns:
                    high_risk['Efficiency'] = high_risk['Efficiency'].round(1)
                if 'Duration (min)' in high_risk.columns:
                    high_risk['Duration (min)'] = high_risk['Duration (min)'].round(0)
                
                # Add indicators
                if 'Risk Level' in high_risk.columns:
                    indicators = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🟢'}
                    high_risk.insert(0, '🚨', high_risk['Risk Level'].map(indicators))
                
                st.dataframe(high_risk, width="stretch", hide_index=True)
                
                if 'Risk Score' in high_risk.columns:
                    st.success(f"""
                    **Summary:** Found {len(high_risk)} flights with highest risk scores.  
                    Top risk score: {high_risk['Risk Score'].max():.1f}  
                    Average of top 10: {high_risk['Risk Score'].mean():.1f}
                    """)
                
                response_found = True
            
            # Efficiency queries
            elif "inefficient" in query_lower or "lowest efficiency" in query_lower:
                st.markdown("### 📊 Analysis Results: Most Inefficient Flights")
                
                cols = ['callsign', 'airline_name', 'fuel_efficiency_score', 'primary_inefficiency_cause', 'duration_minutes', 'total_distance_km']
                available_cols = [c for c in cols if c in df.columns]
                
                inefficient = df.nsmallest(10, 'fuel_efficiency_score')[available_cols].copy()
                
                rename_map = {
                    'callsign': 'Flight',
                    'airline_name': 'Airline',
                    'fuel_efficiency_score': 'Efficiency',
                    'primary_inefficiency_cause': 'Cause',
                    'duration_minutes': 'Duration (min)',
                    'total_distance_km': 'Distance (km)'
                }
                inefficient.rename(columns={k: v for k, v in rename_map.items() if k in inefficient.columns}, inplace=True)
                
                if 'Efficiency' in inefficient.columns:
                    inefficient['Efficiency'] = inefficient['Efficiency'].round(1)
                if 'Duration (min)' in inefficient.columns:
                    inefficient['Duration (min)'] = inefficient['Duration (min)'].round(0)
                if 'Distance (km)' in inefficient.columns:
                    inefficient['Distance (km)'] = inefficient['Distance (km)'].round(0)
                if 'Cause' in inefficient.columns:
                    inefficient['Cause'] = inefficient['Cause'].str[:25]
                
                st.dataframe(inefficient, width="stretch", hide_index=True)
                
                if 'Efficiency' in inefficient.columns:
                    st.success(f"""
                    **Summary:** Identified {len(inefficient)} most inefficient flights.  
                    Lowest efficiency: {inefficient['Efficiency'].min():.1f}/100  
                    Average: {inefficient['Efficiency'].mean():.1f}/100
                    """)
                
                response_found = True
            
            # Average queries
            elif "average" in query_lower and "efficiency" in query_lower:
                st.markdown("### 📊 Analysis Results: Efficiency Statistics")
                
                avg = df['fuel_efficiency_score'].mean()
                median = df['fuel_efficiency_score'].median()
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Average", f"{avg:.1f}/100")
                with col2:
                    st.metric("Median", f"{median:.1f}/100")
                with col3:
                    if 'efficiency_category' in df.columns:
                        excellent = (df['efficiency_category'] == 'Excellent').sum()
                        st.metric("Excellent", f"{excellent}")
                with col4:
                    if 'efficiency_category' in df.columns:
                        poor = (df['efficiency_category'] == 'Poor').sum()
                        st.metric("Poor", f"{poor}")
                
                import plotly.express as px
                fig = px.histogram(df, x='fuel_efficiency_score', nbins=30, color_discrete_sequence=['#3498db'])
                fig.update_layout(
                    xaxis_title="Efficiency Score",
                    yaxis_title="Flights",
                    height=400,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white')
                )
                st.plotly_chart(fig, width="stretch")
                
                response_found = True
            
            # Cause queries
            elif "cause" in query_lower and ("inefficien" in query_lower or "fuel" in query_lower):
                st.markdown("### 📊 Analysis Results: Fuel Inefficiency Causes")
                
                if 'fuel_anomaly' in df.columns and 'primary_inefficiency_cause' in df.columns:
                    causes = df[df['fuel_anomaly'] == -1]['primary_inefficiency_cause'].value_counts()
                    
                    cause_df = pd.DataFrame({
                        'Cause': causes.index,
                        'Count': causes.values,
                        'Percentage': (causes.values / causes.sum() * 100).round(1)
                    })
                    
                    st.dataframe(cause_df, width="stretch", hide_index=True)
                    
                    import plotly.express as px
                    fig = px.bar(cause_df, x='Count', y='Cause', orientation='h',
                                color='Count', color_continuous_scale='Reds')
                    fig.update_layout(
                        height=400,
                        showlegend=False,
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='white')
                    )
                    st.plotly_chart(fig, width="stretch")
                    
                    st.success(f"""
                    **Summary:** Analyzed {causes.sum()} inefficient flights.  
                    Top cause: {causes.index[0]} ({causes.values[0]} flights)
                    """)
                
                response_found = True
            
            # Airline queries - IMPROVED with better understanding
            elif any(keyword in query_lower for keyword in ["airline", "carrier", "compare", "best airline", "worst airline", "rank airline"]):
                st.markdown("### 📊 Analysis Results: Airline Performance")
                
                if 'airline_code' in df.columns and 'airline_name' in df.columns:
                    # Group by airline
                    airline_stats = df.groupby(['airline_code', 'airline_name']).agg({
                        'fuel_efficiency_score': 'mean',
                        'final_risk_score': 'mean',
                        'callsign': 'count'
                    }).reset_index()
                    
                    # Filter airlines with at least 5 flights
                    airline_stats = airline_stats[airline_stats['callsign'] >= 5]
                    airline_stats = airline_stats[airline_stats['airline_name'] != 'Unknown']
                    
                    airline_stats.columns = ['Code', 'Airline', 'Avg Efficiency', 'Avg Risk', 'Flights']
                    airline_stats['Avg Efficiency'] = airline_stats['Avg Efficiency'].round(1)
                    airline_stats['Avg Risk'] = airline_stats['Avg Risk'].round(1)
                    airline_stats = airline_stats.sort_values('Avg Efficiency', ascending=False)
                    
                    # Reorder columns
                    airline_stats = airline_stats[['Airline', 'Code', 'Flights', 'Avg Efficiency', 'Avg Risk']]
                    
                    # SMART RESPONSE based on query type
                    if "best" in query_lower or "top" in query_lower or "highest efficiency" in query_lower:
                        # Show only top 5
                        top_airlines = airline_stats.head(5)
                        st.markdown("#### 🏆 Top 5 Airlines by Efficiency")
                        st.dataframe(top_airlines, width="stretch", hide_index=True)
                        
                        best = top_airlines.iloc[0]
                        st.success(f"""
                        **Winner:** {best['Airline']} ({best['Code']}) leads with **{best['Avg Efficiency']:.1f}%** efficiency across {best['Flights']} flights.
                        """)
                        
                    elif "worst" in query_lower or "lowest" in query_lower or "poor" in query_lower:
                        # Show bottom 5
                        worst_airlines = airline_stats.tail(5).sort_values('Avg Efficiency')
                        st.markdown("#### 📉 Airlines Needing Improvement")
                        st.dataframe(worst_airlines, width="stretch", hide_index=True)
                        
                        worst = worst_airlines.iloc[0]
                        st.warning(f"""
                        **Needs Focus:** {worst['Airline']} ({worst['Code']}) has **{worst['Avg Efficiency']:.1f}%** efficiency and could improve operations.
                        """)
                        
                    elif "compare" in query_lower:
                        # Try to extract airline names from query
                        mentioned_airlines = []
                        for _, row in airline_stats.iterrows():
                            airline_name_lower = row['Airline'].lower()
                            code_lower = row['Code'].lower()
                            if airline_name_lower in query_lower or code_lower in query_lower:
                                mentioned_airlines.append(row['Code'])
                        
                        if len(mentioned_airlines) >= 2:
                            # Show comparison of mentioned airlines
                            comparison = airline_stats[airline_stats['Code'].isin(mentioned_airlines)]
                            st.markdown("#### 🔄 Head-to-Head Comparison")
                            st.dataframe(comparison, width="stretch", hide_index=True)
                            
                            # Determine winner
                            best_in_comparison = comparison.iloc[0]
                            worst_in_comparison = comparison.iloc[-1]
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.success(f"""
                                ### 🏆 Winner
                                **{best_in_comparison['Airline']}**
                                
                                ✈️ {best_in_comparison['Flights']} flights  
                                ⛽ {best_in_comparison['Avg Efficiency']:.1f}% efficiency  
                                ⚠️ {best_in_comparison['Avg Risk']:.1f} risk score
                                """)
                            with col2:
                                st.info(f"""
                                ### 📊 Runner-up
                                **{worst_in_comparison['Airline']}**
                                
                                ✈️ {worst_in_comparison['Flights']} flights  
                                ⛽ {worst_in_comparison['Avg Efficiency']:.1f}% efficiency  
                                ⚠️ {worst_in_comparison['Avg Risk']:.1f} risk score
                                """)
                            
                            # Show difference
                            eff_diff = best_in_comparison['Avg Efficiency'] - worst_in_comparison['Avg Efficiency']
                            st.metric(
                                "Efficiency Gap", 
                                f"{eff_diff:.1f} points",
                                delta=f"{eff_diff:.1f}",
                                delta_color="normal"
                            )
                        else:
                            # Show all airlines for general comparison
                            st.markdown("#### 📊 All Airlines Performance")
                            st.dataframe(airline_stats, width="stretch", hide_index=True)
                            
                            st.info(f"""
                            💡 **Tip:** Specify airlines to compare, e.g., *"Compare EgyptAir vs Ethiopian Airlines"*
                            """)
                    else:
                        # General airline ranking
                        st.markdown("#### 📊 Complete Airline Rankings")
                        st.dataframe(airline_stats, width="stretch", hide_index=True)
                    
                    # Always show best vs worst summary
                    st.markdown("---")
                    st.markdown("#### 📈 Performance Summary")
                    
                    best = airline_stats.iloc[0]
                    worst = airline_stats.iloc[-1]
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("🏆 Best", best['Airline'], f"{best['Avg Efficiency']:.1f}%")
                    with col2:
                        st.metric("📊 Average", airline_stats['Avg Efficiency'].mean().round(1), f"{airline_stats['Avg Efficiency'].mean():.1f}%")
                    with col3:
                        st.metric("📉 Needs Work", worst['Airline'], f"{worst['Avg Efficiency']:.1f}%")
                    
                    response_found = True
            
            # Count queries
            elif "how many" in query_lower:
                st.markdown("### 📊 Analysis Results: Count Statistics")
                
                if "high risk" in query_lower and 'risk_level' in df.columns:
                    count = (df['risk_level'].isin(['HIGH', 'CRITICAL'])).sum()
                    total = len(df)
                    st.metric("High/Critical Risk Flights", f"{count} ({100*count/total:.1f}%)")
                elif "inefficient" in query_lower and 'fuel_anomaly' in df.columns:
                    count = (df['fuel_anomaly'] == -1).sum()
                    total = len(df)
                    st.metric("Inefficient Flights", f"{count} ({100*count/total:.1f}%)")
                else:
                    st.metric("Total Flights", f"{len(df):,}")
                
                response_found = True
            
            # Default response
            if not response_found:
                st.warning("""
                I couldn't find a specific analysis for that question. Here are some suggestions:
                
                - **"Which flights have highest risk?"** - Shows top 10 risky flights
                - **"What's the average efficiency?"** - Shows efficiency statistics
                - **"Which airline is best?"** - Compares airline performance
                - **"What causes fuel inefficiency?"** - Shows root causes
                """)
                
                st.markdown("### 📊 General Statistics")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Flights", f"{len(df):,}")
                with col2:
                    st.metric("Avg Efficiency", f"{df['fuel_efficiency_score'].mean():.1f}/100")
                with col3:
                    if 'risk_level' in df.columns:
                        high = (df['risk_level'].isin(['HIGH', 'CRITICAL'])).sum()
                        st.metric("High Risk", f"{high}")
    else:
        st.info("💬 Please enter a question to analyze.")

st.markdown("---")

# Quick Stats
st.markdown("### 📈 Quick Statistics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Flights", f"{len(df):,}")

with col2:
    st.metric("Avg Efficiency", f"{df['fuel_efficiency_score'].mean():.1f}/100")

with col3:
    if 'risk_level' in df.columns:
        high_risk = (df['risk_level'].isin(['HIGH', 'CRITICAL'])).sum()
        st.metric("High Risk", f"{high_risk}")

with col4:
    if 'fuel_anomaly' in df.columns:
        inefficient = (df['fuel_anomaly'] == -1).sum()
        st.metric("Inefficient", f"{inefficient}")

st.markdown("---")

st.info("""
💡 **Tips for Better Results:**
- Be specific: *"Which airline has best efficiency?"* works better than *"airlines"*
- Use comparisons: *"Compare EgyptAir vs Ethiopian Airlines"*
- Ask about specifics: *"Show high risk flights"*, *"What causes inefficiency?"*
- One question at a time works best
""")
