"""
Predictive Maintenance Analyzer
Predicts maintenance needs based on flight patterns and anomalies
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class PredictiveMaintenanceAnalyzer:
    """Analyzes flight data to predict maintenance needs"""
    
    def __init__(self):
        """Initialize analyzer"""
        self.data_dir = Path('data')
        self.maintenance_threshold = {
            'critical': 80,    # >80 score = CRITICAL
            'high': 60,        # 60-80 = HIGH
            'medium': 40,      # 40-60 = MEDIUM
            'low': 0           # <40 = LOW
        }
    
    def load_flight_data(self):
        """Load all necessary flight data"""
        print("Loading flight data...")
        
        # Load operational features
        operational = pd.read_csv(self.data_dir / 'operational_features.csv')
        
        # Load risk scores
        risk = pd.read_csv(self.data_dir / 'risk_scores.csv')
        
        # Load fuel anomalies
        fuel = pd.read_csv(self.data_dir / 'fuel_anomalies.csv')
        
        # Merge all data
        merged = operational.merge(risk, on='trajectory_id', how='left')
        merged = merged.merge(fuel[['trajectory_id', 'fuel_anomaly', 'primary_inefficiency_cause']], 
                             on='trajectory_id', how='left')
        
        print(f"✅ Loaded {len(merged):,} flight records")
        return merged
    
    def calculate_wear_indicators(self, df):
        """Calculate aircraft wear and tear indicators"""
        print("\nCalculating wear indicators...")
        
        # Check what columns we have
        print(f"Available columns: {list(df.columns)[:10]}...")  # Show first 10
        
        # Determine aircraft identifier column (handle _x, _y suffixes from merge)
        aircraft_col = None
        
        for base_col in ['icao24', 'aircraft_id', 'tail_number', 'callsign']:
            # Check exact match first
            if base_col in df.columns:
                aircraft_col = base_col
                break
            # Check with _x suffix
            elif f'{base_col}_x' in df.columns:
                aircraft_col = f'{base_col}_x'
                break
            # Check with _y suffix
            elif f'{base_col}_y' in df.columns:
                aircraft_col = f'{base_col}_y'
                break
        
        if aircraft_col is None:
            raise ValueError("No aircraft identifier column found! Available columns: " + str(list(df.columns)[:20]))
        
        print(f"Using '{aircraft_col}' as aircraft identifier")
        
        # Also handle other merged columns
        def get_col(base_name):
            """Get actual column name handling _x/_y suffixes"""
            if base_name in df.columns:
                return base_name
            elif f'{base_name}_x' in df.columns:
                return f'{base_name}_x'
            elif f'{base_name}_y' in df.columns:
                return f'{base_name}_y'
            return None
        
        # Get actual column names
        callsign_col = get_col('callsign')
        airline_code_col = get_col('airline_code')
        airline_name_col = get_col('airline_name')
        
        # Group by aircraft
        aircraft_stats = []
        
        for aircraft_id, group in df.groupby(aircraft_col):
            stats = {
                aircraft_col: aircraft_id,  # Use dynamic column name
                'total_flights': len(group),
                'total_hours': group['duration_minutes'].sum() / 60 if 'duration_minutes' in group.columns else 0,
                'total_distance': group['total_distance_km'].sum() if 'total_distance_km' in group.columns else 0,
                'avg_altitude': group.get('max_altitude_m', group.get('avg_altitude_m', pd.Series([0]))).mean(),
                'avg_speed': group.get('avg_velocity_ms', group.get('avg_speed_kmh', pd.Series([0]))).mean(),
            }
            
            # Extract callsign (use actual column name)
            if callsign_col and callsign_col in group.columns:
                callsigns = group[callsign_col].dropna()
                if len(callsigns) > 0:
                    stats['primary_callsign'] = callsigns.mode()[0] if len(callsigns.mode()) > 0 else callsigns.iloc[0]
                else:
                    stats['primary_callsign'] = 'UNKNOWN'
            else:
                stats['primary_callsign'] = str(aircraft_id)  # Use aircraft_id as fallback
            
            # Airline info (use actual column names)
            if airline_code_col and airline_code_col in group.columns:
                stats['airline_code'] = group[airline_code_col].mode()[0] if len(group[airline_code_col].mode()) > 0 else group[airline_code_col].iloc[0]
            
            if airline_name_col and airline_name_col in group.columns:
                stats['airline_name'] = group[airline_name_col].mode()[0] if len(group[airline_name_col].mode()) > 0 else group[airline_name_col].iloc[0]
            
            # Performance degradation indicators (handle missing columns)
            final_risk_col = 'final_risk_score' if 'final_risk_score' in group.columns else None
            fuel_eff_col = 'fuel_efficiency_score' if 'fuel_efficiency_score' in group.columns else None
            fuel_anom_col = 'fuel_anomaly' if 'fuel_anomaly' in group.columns else None
            
            if final_risk_col:
                stats['high_risk_flights'] = (group[final_risk_col] > 50).sum()
                stats['avg_risk_score'] = group[final_risk_col].mean()
            else:
                stats['high_risk_flights'] = 0
                stats['avg_risk_score'] = 0
            
            if fuel_anom_col:
                stats['inefficient_flights'] = (group[fuel_anom_col] == -1).sum()
            else:
                stats['inefficient_flights'] = 0
            
            if fuel_eff_col:
                stats['avg_efficiency'] = group[fuel_eff_col].mean()
            else:
                stats['avg_efficiency'] = 75.0  # Default middle value
            
            # Variability indicators (higher = more wear)
            altitude_var_col = 'altitude_variance' if 'altitude_variance' in group.columns else None
            speed_var_col = 'velocity_variance' if 'velocity_variance' in group.columns else None
            
            if altitude_var_col:
                stats['altitude_variance'] = group[altitude_var_col].mean()
            else:
                stats['altitude_variance'] = 0
            
            if speed_var_col:
                stats['speed_variance'] = group[speed_var_col].mean()
            else:
                stats['speed_variance'] = 0
            
            # Age proxy (days since first flight in dataset)
            start_time_col = 'start_time' if 'start_time' in group.columns else 'start_time_x' if 'start_time_x' in group.columns else None
            
            if start_time_col:
                group[start_time_col] = pd.to_datetime(group[start_time_col], errors='coerce')
                valid_times = group[start_time_col].dropna()
                if len(valid_times) > 0:
                    stats['days_in_operation'] = (valid_times.max() - valid_times.min()).days
                    stats['last_flight'] = valid_times.max()
                else:
                    stats['days_in_operation'] = 0
                    stats['last_flight'] = datetime.now()
            else:
                stats['days_in_operation'] = 0
                stats['last_flight'] = datetime.now()
            
            aircraft_stats.append(stats)
        
        aircraft_df = pd.DataFrame(aircraft_stats)
        
        # Add standard 'aircraft_id' column for consistency
        if aircraft_col != 'aircraft_id':
            aircraft_df['aircraft_id'] = aircraft_df[aircraft_col]
        
        print(f"✅ Analyzed {len(aircraft_df):,} aircraft")
        
        return aircraft_df
    
    def predict_maintenance_probability(self, aircraft_df):
        """Calculate maintenance probability score (0-100)"""
        print("\nCalculating maintenance probabilities...")
        
        # Normalize factors (0-1 scale)
        def normalize(series):
            min_val = series.min()
            max_val = series.max()
            if max_val == min_val:
                return pd.Series([0.5] * len(series))
            return (series - min_val) / (max_val - min_val)
        
        # Factor 1: Flight hours (more hours = higher maintenance need)
        aircraft_df['hours_factor'] = normalize(aircraft_df['total_hours'])
        
        # Factor 2: Distance (more distance = more wear)
        aircraft_df['distance_factor'] = normalize(aircraft_df['total_distance'])
        
        # Factor 3: Risk history (higher avg risk = more issues)
        aircraft_df['risk_factor'] = normalize(aircraft_df['avg_risk_score'])
        
        # Factor 4: Efficiency degradation (lower efficiency = wear)
        aircraft_df['efficiency_factor'] = 1 - normalize(aircraft_df['avg_efficiency'])
        
        # Factor 5: High-risk flight ratio
        aircraft_df['risk_ratio'] = aircraft_df['high_risk_flights'] / aircraft_df['total_flights']
        aircraft_df['risk_ratio_factor'] = normalize(aircraft_df['risk_ratio'])
        
        # Factor 6: Variability (higher variance = more stress)
        aircraft_df['variance_factor'] = normalize(
            aircraft_df['altitude_variance'] + aircraft_df['speed_variance']
        )
        
        # Weighted maintenance score (0-100)
        weights = {
            'hours_factor': 0.25,
            'distance_factor': 0.20,
            'risk_factor': 0.20,
            'efficiency_factor': 0.15,
            'risk_ratio_factor': 0.10,
            'variance_factor': 0.10
        }
        
        aircraft_df['maintenance_score'] = 0
        for factor, weight in weights.items():
            aircraft_df['maintenance_score'] += aircraft_df[factor] * weight * 100
        
        aircraft_df['maintenance_score'] = aircraft_df['maintenance_score'].round(1)
        
        # Classify priority
        def classify_priority(score):
            if score >= self.maintenance_threshold['critical']:
                return 'CRITICAL'
            elif score >= self.maintenance_threshold['high']:
                return 'HIGH'
            elif score >= self.maintenance_threshold['medium']:
                return 'MEDIUM'
            else:
                return 'LOW'
        
        aircraft_df['maintenance_priority'] = aircraft_df['maintenance_score'].apply(classify_priority)
        
        print(f"✅ Maintenance scores calculated")
        
        return aircraft_df
    
    def estimate_maintenance_window(self, aircraft_df):
        """Estimate when maintenance should be performed"""
        print("\nEstimating maintenance windows...")
        
        def calculate_window(row):
            score = row['maintenance_score']
            
            if score >= 80:
                return 'Immediate (0-7 days)'
            elif score >= 60:
                return 'Urgent (1-2 weeks)'
            elif score >= 40:
                return 'Soon (1 month)'
            else:
                return 'Routine (3+ months)'
        
        aircraft_df['maintenance_window'] = aircraft_df.apply(calculate_window, axis=1)
        
        return aircraft_df
    
    def identify_maintenance_causes(self, aircraft_df, full_df):
        """Identify primary causes for maintenance needs"""
        print("\nIdentifying maintenance causes...")
        
        # Determine which aircraft column to use (handle _x/_y suffixes)
        aircraft_col = None
        
        # Find the column that was used in aircraft_df
        for col in aircraft_df.columns:
            if any(base in col for base in ['icao24', 'aircraft_id', 'callsign']):
                # Check if this column also exists in full_df
                if col in full_df.columns:
                    aircraft_col = col
                    break
        
        if aircraft_col is None:
            # Try to find matching base names
            for base_col in ['icao24', 'aircraft_id', 'callsign']:
                # Check with _x suffix
                if f'{base_col}_x' in aircraft_df.columns and f'{base_col}_x' in full_df.columns:
                    aircraft_col = f'{base_col}_x'
                    break
                # Check exact match
                elif base_col in aircraft_df.columns and base_col in full_df.columns:
                    aircraft_col = base_col
                    break
        
        if aircraft_col is None:
            print(f"⚠️ Warning: Cannot identify maintenance causes")
            print(f"   Aircraft DF columns: {list(aircraft_df.columns)[:10]}")
            print(f"   Full DF columns: {list(full_df.columns)[:10]}")
            aircraft_df['primary_causes'] = 'Unable to determine - missing aircraft identifier'
            return aircraft_df
        
        print(f"   Using '{aircraft_col}' to match aircraft")
        
        causes = []
        
        for _, aircraft in aircraft_df.iterrows():
            aircraft_id = aircraft[aircraft_col]
            
            # Get flights for this aircraft
            aircraft_flights = full_df[full_df[aircraft_col] == aircraft_id]
            
            # Analyze patterns
            cause_factors = []
            
            # High altitude variance
            if 'altitude_variance' in aircraft.index and pd.notna(aircraft.get('altitude_variance')):
                if aircraft['altitude_variance'] > aircraft_df['altitude_variance'].quantile(0.75):
                    cause_factors.append('Frequent altitude changes')
            
            # High speed variance  
            if 'speed_variance' in aircraft.index and pd.notna(aircraft.get('speed_variance')):
                if aircraft['speed_variance'] > aircraft_df['speed_variance'].quantile(0.75):
                    cause_factors.append('Speed instability')
            
            # Many high-risk flights
            if 'risk_ratio' in aircraft.index and pd.notna(aircraft.get('risk_ratio')):
                if aircraft['risk_ratio'] > 0.2:
                    cause_factors.append('Repeated high-risk operations')
            
            # Low efficiency
            if 'avg_efficiency' in aircraft.index and pd.notna(aircraft.get('avg_efficiency')):
                if aircraft['avg_efficiency'] < 70:
                    cause_factors.append('Declining fuel efficiency')
            
            # Heavy usage
            if 'total_hours' in aircraft.index and pd.notna(aircraft.get('total_hours')):
                if aircraft['total_hours'] > aircraft_df['total_hours'].quantile(0.75):
                    cause_factors.append('High flight hours')
            
            # Long distance
            if 'total_distance' in aircraft.index and pd.notna(aircraft.get('total_distance')):
                if aircraft['total_distance'] > aircraft_df['total_distance'].quantile(0.75):
                    cause_factors.append('Extensive mileage')
            
            if len(cause_factors) == 0:
                cause_factors.append('Normal wear and tear')
            
            causes.append(', '.join(cause_factors))
        
        aircraft_df['primary_causes'] = causes
        
        return aircraft_df
    
    def generate_recommendations(self, aircraft_df):
        """Generate maintenance recommendations"""
        print("\nGenerating recommendations...")
        
        recommendations = []
        
        for _, aircraft in aircraft_df.iterrows():
            recs = []
            
            priority = aircraft['maintenance_priority']
            score = aircraft['maintenance_score']
            
            if priority == 'CRITICAL':
                recs.append('⚠️ Ground aircraft immediately for inspection')
                recs.append('🔧 Full systems check required')
                recs.append('📋 Review last 10 flight logs in detail')
            elif priority == 'HIGH':
                recs.append('⚠️ Schedule comprehensive maintenance within 2 weeks')
                recs.append('🔍 Inspect high-stress components')
                recs.append('📊 Monitor performance closely')
            elif priority == 'MEDIUM':
                recs.append('📅 Plan maintenance within next month')
                recs.append('🔧 Routine inspections recommended')
                recs.append('📈 Track efficiency trends')
            else:
                recs.append('✅ Continue routine maintenance schedule')
                recs.append('📊 Monitor for changes')
            
            # Specific recommendations based on causes
            causes = aircraft.get('primary_causes', '')
            
            if 'altitude changes' in causes.lower():
                recs.append('🔧 Check pressurization system')
            if 'speed instability' in causes.lower():
                recs.append('🔧 Inspect throttle control system')
            if 'fuel efficiency' in causes.lower():
                recs.append('⛽ Engine performance check needed')
            if 'high flight hours' in causes.lower():
                recs.append('🕐 Review airframe hours for scheduled maintenance')
            
            recommendations.append(' | '.join(recs))
        
        aircraft_df['recommendations'] = recommendations
        
        return aircraft_df
    
    def calculate_cost_estimates(self, aircraft_df):
        """Estimate maintenance costs - Realistic commercial aviation pricing"""
        print("\nCalculating cost estimates...")
        
        # Base maintenance costs (realistic commercial aviation - much higher!)
        base_costs = {
            'CRITICAL': 150000,  # $150k for critical/emergency maintenance (grounding, full inspection)
            'HIGH': 75000,       # $75k for high priority maintenance (comprehensive service)
            'MEDIUM': 35000,     # $35k for medium priority maintenance (scheduled service)
            'LOW': 15000         # $15k for routine maintenance (standard checks)
        }
        
        costs = []
        
        for _, aircraft in aircraft_df.iterrows():
            priority = aircraft['maintenance_priority']
            base_cost = base_costs[priority]
            
            # Get aircraft usage metrics
            hours = aircraft.get('total_hours', 0)
            distance = aircraft.get('total_distance', 0)
            flights = aircraft.get('total_flights', 0)
            
            # MUCH MORE AGGRESSIVE MULTIPLIERS
            
            # 1. Flight Hours Factor (exponential growth)
            # Commercial aircraft: $200-400 per flight hour in maintenance
            if hours > 1000:
                hours_multiplier = 2.5  # 2.5x for heavy use
            elif hours > 500:
                hours_multiplier = 2.0  # 2x for moderate-heavy use
            elif hours > 200:
                hours_multiplier = 1.5  # 1.5x for moderate use
            else:
                hours_multiplier = 1.2  # 1.2x for light use
            
            # 2. Distance Factor (wear from mileage)
            # Add $100 per 10,000km traveled
            distance_addition = (distance / 10000) * 100
            
            # 3. Flight Cycles Factor (takeoff/landing stress)
            # Each flight cycle costs ~$500 in wear
            cycle_cost = flights * 500
            
            # 4. Risk Factor (problems = expensive repairs)
            risk_score = aircraft.get('avg_risk_score', 0)
            if risk_score > 50:
                risk_multiplier = 2.0  # Double for high risk
            elif risk_score > 30:
                risk_multiplier = 1.5  # 1.5x for moderate risk
            else:
                risk_multiplier = 1.0  # Normal
            
            # 5. Efficiency Penalty (poor efficiency = component degradation)
            efficiency = aircraft.get('avg_efficiency', 75)
            if efficiency < 60:
                efficiency_addition = 25000  # $25k penalty for poor efficiency
            elif efficiency < 70:
                efficiency_addition = 15000  # $15k penalty
            elif efficiency < 80:
                efficiency_addition = 5000   # $5k penalty
            else:
                efficiency_addition = 0
            
            # 6. Variability Penalty (inconsistent operation = stress)
            alt_variance = aircraft.get('altitude_variance', 0)
            speed_variance = aircraft.get('speed_variance', 0)
            
            if alt_variance > 1000000 or speed_variance > 100:
                variability_addition = 10000  # $10k for high variability
            elif alt_variance > 500000 or speed_variance > 50:
                variability_addition = 5000   # $5k for moderate variability
            else:
                variability_addition = 0
            
            # CALCULATE TOTAL COST
            estimated_cost = (
                (base_cost * hours_multiplier * risk_multiplier) +  # Base with multipliers
                distance_addition +                                  # Distance wear
                cycle_cost +                                         # Flight cycles
                efficiency_addition +                                # Efficiency penalty
                variability_addition                                 # Variability penalty
            )
            
            # Ensure realistic minimum (even "routine" maintenance is expensive)
            min_cost = base_cost * 0.9  # At least 90% of base
            estimated_cost = max(estimated_cost, min_cost)
            
            costs.append(round(estimated_cost, 2))
        
        aircraft_df['estimated_cost_usd'] = costs
        
        # Show cost breakdown
        total_cost = aircraft_df['estimated_cost_usd'].sum()
        avg_cost = aircraft_df['estimated_cost_usd'].mean()
        min_cost = aircraft_df['estimated_cost_usd'].min()
        max_cost = aircraft_df['estimated_cost_usd'].max()
        
        print(f"   Cost range: ${min_cost:,.0f} - ${max_cost:,.0f}")
        print(f"   Average cost: ${avg_cost:,.0f}")
        print(f"   Total fleet cost: ${total_cost:,.0f}")
        
        return aircraft_df
    
    def run_full_analysis(self):
        """Run complete predictive maintenance analysis"""
        print("\n" + "="*70)
        print("PREDICTIVE MAINTENANCE ANALYSIS")
        print("="*70)
        
        # Load data
        full_df = self.load_flight_data()
        
        # Calculate wear indicators
        aircraft_df = self.calculate_wear_indicators(full_df)
        
        # Predict maintenance needs
        aircraft_df = self.predict_maintenance_probability(aircraft_df)
        
        # Estimate maintenance windows
        aircraft_df = self.estimate_maintenance_window(aircraft_df)
        
        # Identify causes
        aircraft_df = self.identify_maintenance_causes(aircraft_df, full_df)
        
        # Generate recommendations
        aircraft_df = self.generate_recommendations(aircraft_df)
        
        # Calculate costs
        aircraft_df = self.calculate_cost_estimates(aircraft_df)
        
        # Sort by priority
        priority_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        aircraft_df['priority_rank'] = aircraft_df['maintenance_priority'].map(priority_order)
        aircraft_df = aircraft_df.sort_values('priority_rank')
        
        # Save results
        output_path = self.data_dir / 'maintenance_predictions.csv'
        aircraft_df.to_csv(output_path, index=False)
        print(f"\n✅ Results saved to: {output_path}")
        
        # Display summary
        self.print_summary(aircraft_df)
        
        return aircraft_df
    
    def print_summary(self, aircraft_df):
        """Print analysis summary"""
        print("\n" + "="*70)
        print("MAINTENANCE ANALYSIS SUMMARY")
        print("="*70)
        
        total_aircraft = len(aircraft_df)
        
        print(f"\n📊 Aircraft Analyzed: {total_aircraft}")
        print(f"\n🔧 Maintenance Priority Breakdown:")
        
        for priority in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            count = (aircraft_df['maintenance_priority'] == priority).sum()
            percentage = (count / total_aircraft * 100)
            print(f"   {priority:8s}: {count:3d} aircraft ({percentage:5.1f}%)")
        
        print(f"\n💰 Cost Estimates:")
        total_cost = aircraft_df['estimated_cost_usd'].sum()
        avg_cost = aircraft_df['estimated_cost_usd'].mean()
        print(f"   Total: ${total_cost:,.2f}")
        print(f"   Average: ${avg_cost:,.2f} per aircraft")
        
        print(f"\n⚠️ Immediate Action Required:")
        critical = aircraft_df[aircraft_df['maintenance_priority'] == 'CRITICAL']
        if len(critical) > 0:
            print(f"   {len(critical)} aircraft need IMMEDIATE attention")
            for _, row in critical.head(5).iterrows():
                callsign = row.get('primary_callsign', 'UNKNOWN')
                score = row['maintenance_score']
                print(f"   - {callsign} (Score: {score:.1f})")
        else:
            print(f"   ✅ No critical maintenance needed")
        
        print(f"\n📅 Maintenance Schedule:")
        for window in aircraft_df['maintenance_window'].unique():
            count = (aircraft_df['maintenance_window'] == window).sum()
            print(f"   {window}: {count} aircraft")
        
        print("\n" + "="*70)


def main():
    """Main execution"""
    analyzer = PredictiveMaintenanceAnalyzer()
    results = analyzer.run_full_analysis()
    
    print("\n✅ Predictive maintenance analysis complete!")
    print(f"📊 Check data/maintenance_predictions.csv for full results")


if __name__ == "__main__":
    main()