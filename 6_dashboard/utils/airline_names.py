"""
Airline Name Mapping Utility
Maps ICAO/IATA codes to full airline names
"""

# Comprehensive airline mapping (ICAO 3-letter codes to full names)
AIRLINE_NAMES = {
    # Major Indian Carriers
    'AIC': 'Air India',
    'IGO': 'IndiGo',
    'VTI': 'Vistara',
    'SEJ': 'SpiceJet',
    'GOW': 'Go First',
    'AXB': 'AirAsia India',
    'JAI': 'Alliance Air',
    'AIE': 'Air India Express',
    'AKJ': 'Akasa Air',
    
    # Middle East Carriers
    'UAE': 'Emirates',
    'ETD': 'Etihad Airways',
    'QTR': 'Qatar Airways',
    'FDB': 'FlyDubai',
    'GFA': 'Gulf Air',
    'RJA': 'Royal Jordanian',
    'MSR': 'EgyptAir',
    'MEA': 'Middle East Airlines',
    'SVA': 'Saudia',
    'OMA': 'Oman Air',
    'KAC': 'Kuwait Airways',
    'ABY': 'Air Arabia',
    'NIA': 'Nas Air',
    'JAZ': 'Jazeera Airways',
    
    # African Carriers
    'ETH': 'Ethiopian Airlines',
    'SAA': 'South African Airways',
    'RAM': 'Royal Air Maroc',
    'KQA': 'Kenya Airways',
    'RWD': 'RwandAir',
    'DAH': 'Air Algerie',
    'TUI': 'Tunisair',
    'LLM': 'Libyan Airlines',
    
    # Asian Carriers
    'SIA': 'Singapore Airlines',
    'THA': 'Thai Airways',
    'MAS': 'Malaysia Airlines',
    'CPA': 'Cathay Pacific',
    'KAL': 'Korean Air',
    'JAL': 'Japan Airlines',
    'ANA': 'All Nippon Airways',
    'CES': 'China Eastern',
    'CSN': 'China Southern',
    'CCA': 'Air China',
    'VNA': 'Vietnam Airlines',
    'GIA': 'Garuda Indonesia',
    'PAL': 'Philippine Airlines',
    'SBI': 'S7 Airlines',
    'TGW': 'Scoot',
    'VJT': 'VietJet Air',
    'AXM': 'AirAsia X',
    'HVN': 'Vietnam Airlines',
    'CRK': 'Hong Kong Airlines',
    'AHK': 'Air Hong Kong',
    
    # European Carriers
    'BAW': 'British Airways',
    'AFR': 'Air France',
    'DLH': 'Lufthansa',
    'KLM': 'KLM',
    'SWR': 'Swiss',
    'AUA': 'Austrian Airlines',
    'SAS': 'SAS',
    'FIN': 'Finnair',
    'IBE': 'Iberia',
    'AEE': 'Aegean Airlines',
    'TAP': 'TAP Air Portugal',
    'LOT': 'LOT Polish Airlines',
    'CSA': 'Czech Airlines',
    'THY': 'Turkish Airlines',
    'AFL': 'Aeroflot',
    'RYR': 'Ryanair',
    'EZY': 'easyJet',
    'WZZ': 'Wizz Air',
    'VIR': 'Virgin Atlantic',
    'ITY': 'ITA Airways',
    'VOI': 'Volotea',
    'ENT': 'Enter Air',
    
    # American Carriers
    'AAL': 'American Airlines',
    'UAL': 'United Airlines',
    'DAL': 'Delta Air Lines',
    'SWA': 'Southwest Airlines',
    'JBU': 'JetBlue',
    'ASA': 'Alaska Airlines',
    'FFT': 'Frontier Airlines',
    'NKS': 'Spirit Airlines',
    'ACA': 'Air Canada',
    'WJA': 'WestJet',
    'AMX': 'Aeromexico',
    'AVA': 'Avianca',
    'AZU': 'Azul',
    'GLO': 'Gol',
    'TAM': 'LATAM',
    'CMP': 'Copa Airlines',
    
    # Oceania Carriers
    'QFA': 'Qantas',
    'ANZ': 'Air New Zealand',
    'FJI': 'Fiji Airways',
    
    # Cargo
    'FDX': 'FedEx',
    'UPS': 'UPS',
    'CLX': 'Cargolux',
    'ABW': 'AirBridgeCargo',
    
    # Other International
    'AHY': 'Azerbaijan Airlines',
    'BEE': 'Flybe',
    'REU': 'Air Austral',
    'FPO': 'Fly540',
    'CPZ': 'Compass Airlines',
}

def get_airline_name(code: str) -> str:
    """
    Get full airline name from code
    
    Args:
        code: 3-letter airline code (e.g., 'AIC', 'IGO')
    
    Returns:
        Full airline name or code if not found
    """
    if not code or str(code).upper() == 'NAN' or str(code) == '':
        return 'Unknown Airline'
    
    code = str(code).upper().strip()
    
    # Handle codes longer than 3 letters
    if len(code) > 3:
        code = code[:3]
    
    return AIRLINE_NAMES.get(code, code)

def get_airline_with_code(code: str) -> str:
    """
    Get formatted string with code and name
    
    Args:
        code: 3-letter airline code
    
    Returns:
        Formatted string like "AIC - Air India"
    """
    name = get_airline_name(code)
    if name == code or name == 'Unknown Airline':
        return code
    return f"{code} - {name}"

def add_airline_names(df, callsign_col='callsign'):
    """
    Add airline code and full name columns to dataframe
    
    Args:
        df: DataFrame with callsign column
        callsign_col: Name of callsign column
    
    Returns:
        DataFrame with airline_code and airline_name columns
    """
    import pandas as pd
    
    # Extract airline code (first 3 letters of callsign)
    df['airline_code'] = df[callsign_col].astype(str).str[:3].str.upper()
    
    # Replace 'NAN' codes with empty
    df.loc[df['airline_code'] == 'NAN', 'airline_code'] = ''
    
    # Map to full names
    df['airline_name'] = df['airline_code'].apply(get_airline_name)
    
    return df
