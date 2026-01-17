-- Aviation Intelligence & Risk Prediction Platform (AIRP)
-- PostgreSQL Database Schema

-- Drop existing tables (for clean setup)
DROP TABLE IF EXISTS predictions CASCADE;
DROP TABLE IF EXISTS risk_scores CASCADE;
DROP TABLE IF EXISTS fuel_efficiency CASCADE;
DROP TABLE IF EXISTS flight_states CASCADE;
DROP TABLE IF EXISTS weather_data CASCADE;
DROP TABLE IF EXISTS airports CASCADE;
DROP TABLE IF EXISTS aircraft CASCADE;
DROP TABLE IF EXISTS airlines CASCADE;

-- ============================================
-- REFERENCE DATA TABLES
-- ============================================

-- Airlines Table
CREATE TABLE airlines (
    airline_id SERIAL PRIMARY KEY,
    icao_code VARCHAR(10) UNIQUE NOT NULL,
    iata_code VARCHAR(10),
    airline_name VARCHAR(200) NOT NULL,
    country VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_airlines_icao ON airlines(icao_code);

-- Aircraft Table
CREATE TABLE aircraft (
    aircraft_id SERIAL PRIMARY KEY,
    icao24 VARCHAR(10) UNIQUE NOT NULL,  -- Unique aircraft identifier
    registration VARCHAR(20),
    aircraft_type VARCHAR(50),  -- e.g., A320, B737
    manufacturer VARCHAR(100),  -- Boeing, Airbus, etc.
    model VARCHAR(100),
    operator VARCHAR(200),
    operator_icao VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_aircraft_icao24 ON aircraft(icao24);
CREATE INDEX idx_aircraft_type ON aircraft(aircraft_type);
CREATE INDEX idx_aircraft_updated ON aircraft(updated_at);

-- Airports Table
CREATE TABLE airports (
    airport_id SERIAL PRIMARY KEY,
    icao_code VARCHAR(10) UNIQUE,
    iata_code VARCHAR(10) UNIQUE,
    airport_name VARCHAR(200) NOT NULL,
    city VARCHAR(100),
    country VARCHAR(100),
    latitude DECIMAL(10, 6),
    longitude DECIMAL(10, 6),
    elevation_ft INTEGER,
    timezone VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_airports_icao ON airports(icao_code);
CREATE INDEX idx_airports_iata ON airports(iata_code);
CREATE INDEX idx_airports_country ON airports(country);

-- ============================================
-- OPERATIONAL DATA TABLES
-- ============================================

-- Flight States (Real-time and Historical)
CREATE TABLE flight_states (
    state_id BIGSERIAL PRIMARY KEY,
    icao24 VARCHAR(10) NOT NULL,
    callsign VARCHAR(20),
    
    -- Position
    latitude DECIMAL(10, 6),
    longitude DECIMAL(10, 6),
    baro_altitude DECIMAL(10, 2),  -- meters
    geo_altitude DECIMAL(10, 2),   -- meters
    
    -- Velocity
    velocity DECIMAL(10, 2),  -- m/s
    vertical_rate DECIMAL(10, 2),  -- m/s
    heading DECIMAL(10, 2),  -- degrees
    
    -- Status
    on_ground BOOLEAN,
    squawk VARCHAR(10),
    spi BOOLEAN,
    position_source INTEGER,
    
    -- Origin/Destination (if available)
    origin_airport VARCHAR(10),
    destination_airport VARCHAR(10),
    
    -- Timestamps
    last_contact TIMESTAMP,
    timestamp TIMESTAMP NOT NULL,
    collection_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (icao24) REFERENCES aircraft(icao24)
);

-- Partitioning by month for better performance
CREATE INDEX idx_flight_states_icao24 ON flight_states(icao24);
CREATE INDEX idx_flight_states_timestamp ON flight_states(timestamp);
CREATE INDEX idx_flight_states_callsign ON flight_states(callsign);
CREATE INDEX idx_flight_states_airports ON flight_states(origin_airport, destination_airport);

-- Composite indexes for common query patterns (performance optimization)
CREATE INDEX idx_flight_states_icao_time ON flight_states(icao24, timestamp DESC);
CREATE INDEX idx_flight_states_callsign_time ON flight_states(callsign, timestamp DESC);
CREATE INDEX idx_flight_states_time_icao ON flight_states(timestamp DESC, icao24);

-- Weather Data
CREATE TABLE weather_data (
    weather_id BIGSERIAL PRIMARY KEY,
    airport_code VARCHAR(10),
    latitude DECIMAL(10, 6),
    longitude DECIMAL(10, 6),
    
    -- Weather conditions
    temperature DECIMAL(5, 2),  -- Celsius
    pressure DECIMAL(8, 2),  -- hPa
    humidity INTEGER,  -- Percentage
    wind_speed DECIMAL(6, 2),  -- m/s
    wind_direction INTEGER,  -- degrees
    visibility INTEGER,  -- meters
    cloud_coverage INTEGER,  -- percentage
    weather_condition VARCHAR(100),
    
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (airport_code) REFERENCES airports(icao_code)
);

CREATE INDEX idx_weather_airport ON weather_data(airport_code);
CREATE INDEX idx_weather_timestamp ON weather_data(timestamp);

-- ============================================
-- ML/AI OUTPUT TABLES
-- ============================================

-- Fuel Efficiency Analysis
CREATE TABLE fuel_efficiency (
    efficiency_id BIGSERIAL PRIMARY KEY,
    icao24 VARCHAR(10) NOT NULL,
    callsign VARCHAR(20),
    flight_date DATE NOT NULL,
    
    -- Efficiency metrics
    altitude_variance DECIMAL(10, 2),
    speed_variance DECIMAL(10, 2),
    holding_pattern_detected BOOLEAN,
    holding_duration_minutes INTEGER,
    route_deviation_km DECIMAL(10, 2),
    
    -- Calculated scores
    efficiency_score DECIMAL(5, 2),  -- 0-100
    inefficiency_flag BOOLEAN,
    estimated_fuel_waste_kg DECIMAL(10, 2),
    
    -- Analysis period
    analysis_start TIMESTAMP,
    analysis_end TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (icao24) REFERENCES aircraft(icao24)
);

CREATE INDEX idx_fuel_icao24 ON fuel_efficiency(icao24);
CREATE INDEX idx_fuel_date ON fuel_efficiency(flight_date);
CREATE INDEX idx_fuel_score ON fuel_efficiency(efficiency_score);

-- Risk Scores
CREATE TABLE risk_scores (
    risk_id BIGSERIAL PRIMARY KEY,
    icao24 VARCHAR(10) NOT NULL,
    callsign VARCHAR(20),
    flight_date DATE NOT NULL,
    
    -- Risk factors
    speed_variance_score DECIMAL(5, 2),
    altitude_variance_score DECIMAL(5, 2),
    route_deviation_score DECIMAL(5, 2),
    congestion_score DECIMAL(5, 2),
    weather_risk_score DECIMAL(5, 2),
    
    -- Overall risk
    total_risk_score DECIMAL(5, 2),  -- 0-100
    risk_level VARCHAR(20),  -- LOW, MEDIUM, HIGH
    risk_factors TEXT[],  -- Array of identified risk factors
    
    -- Context
    origin_airport VARCHAR(10),
    destination_airport VARCHAR(10),
    
    -- Timestamps
    assessment_time TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (icao24) REFERENCES aircraft(icao24)
);

CREATE INDEX idx_risk_icao24 ON risk_scores(icao24);
CREATE INDEX idx_risk_date ON risk_scores(flight_date);
CREATE INDEX idx_risk_level ON risk_scores(risk_level);
CREATE INDEX idx_risk_score ON risk_scores(total_risk_score);

-- Predictions (Delay Prediction)
CREATE TABLE predictions (
    prediction_id BIGSERIAL PRIMARY KEY,
    
    -- Flight info
    callsign VARCHAR(20),
    icao24 VARCHAR(10),
    origin_airport VARCHAR(10),
    destination_airport VARCHAR(10),
    aircraft_type VARCHAR(50),
    airline_icao VARCHAR(10),
    
    -- Scheduled vs predicted
    scheduled_departure TIMESTAMP,
    scheduled_arrival TIMESTAMP,
    predicted_delay_minutes INTEGER,
    delay_probability DECIMAL(5, 4),  -- 0-1
    
    -- Actual (filled in later)
    actual_delay_minutes INTEGER,
    prediction_accuracy DECIMAL(5, 2),
    
    -- Model info
    model_version VARCHAR(50),
    confidence_score DECIMAL(5, 4),
    
    -- Timestamps
    prediction_time TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (icao24) REFERENCES aircraft(icao24)
);

CREATE INDEX idx_predictions_callsign ON predictions(callsign);
CREATE INDEX idx_predictions_airports ON predictions(origin_airport, destination_airport);
CREATE INDEX idx_predictions_time ON predictions(prediction_time);

-- ============================================
-- MATERIALIZED VIEWS FOR ANALYTICS
-- ============================================

-- Daily Flight Statistics
CREATE MATERIALIZED VIEW daily_flight_stats AS
SELECT 
    DATE(timestamp) as flight_date,
    COUNT(DISTINCT icao24) as unique_aircraft,
    COUNT(DISTINCT callsign) as total_flights,
    AVG(velocity) as avg_velocity,
    AVG(baro_altitude) as avg_altitude,
    COUNT(CASE WHEN on_ground = true THEN 1 END) as flights_on_ground,
    COUNT(CASE WHEN on_ground = false THEN 1 END) as flights_airborne
FROM flight_states
GROUP BY DATE(timestamp);

CREATE UNIQUE INDEX idx_daily_stats_date ON daily_flight_stats(flight_date);

-- Airport Congestion View
CREATE MATERIALIZED VIEW airport_congestion AS
SELECT 
    origin_airport as airport_code,
    DATE(timestamp) as congestion_date,
    EXTRACT(HOUR FROM timestamp) as hour,
    COUNT(*) as flight_count
FROM flight_states
WHERE origin_airport IS NOT NULL
GROUP BY origin_airport, DATE(timestamp), EXTRACT(HOUR FROM timestamp)

UNION ALL

SELECT 
    destination_airport as airport_code,
    DATE(timestamp) as congestion_date,
    EXTRACT(HOUR FROM timestamp) as hour,
    COUNT(*) as flight_count
FROM flight_states
WHERE destination_airport IS NOT NULL
GROUP BY destination_airport, DATE(timestamp), EXTRACT(HOUR FROM timestamp);

CREATE INDEX idx_airport_congestion ON airport_congestion(airport_code, congestion_date);

-- ============================================
-- FUNCTIONS AND TRIGGERS
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for aircraft table
CREATE TRIGGER update_aircraft_updated_at
    BEFORE UPDATE ON aircraft
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to refresh materialized views
CREATE OR REPLACE FUNCTION refresh_analytics_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY daily_flight_stats;
    REFRESH MATERIALIZED VIEW CONCURRENTLY airport_congestion;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================

COMMENT ON TABLE flight_states IS 'Real-time and historical flight position data from OpenSky Network';
COMMENT ON TABLE fuel_efficiency IS 'ML-generated fuel efficiency analysis and anomaly detection';
COMMENT ON TABLE risk_scores IS 'AI-generated operational risk assessments';
COMMENT ON TABLE predictions IS 'Delay predictions and their accuracy tracking';
COMMENT ON TABLE weather_data IS 'Weather conditions at airports for correlation analysis';

-- Grant permissions (adjust user as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO airp_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO airp_user;