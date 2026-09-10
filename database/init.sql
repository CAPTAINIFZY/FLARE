-- PostgreSQL Initialization Script for FLARE

CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role_id INTEGER REFERENCES roles(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    api_key VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE airports (
    iata_code VARCHAR(3) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL DEFAULT 'India',
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8)
);

CREATE TABLE airlines (
    code VARCHAR(10) PRIMARY KEY, -- IATA designator or custom code
    name VARCHAR(255) NOT NULL UNIQUE,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE routes (
    route_code VARCHAR(7) PRIMARY KEY, -- e.g., DEL-BOM
    origin_iata VARCHAR(3) REFERENCES airports(iata_code),
    destination_iata VARCHAR(3) REFERENCES airports(iata_code),
    distance_km INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    CONSTRAINT chk_route_code CHECK (route_code = origin_iata || '-' || destination_iata)
);

CREATE TABLE route_weights (
    id SERIAL PRIMARY KEY,
    route_code VARCHAR(7) REFERENCES routes(route_code),
    weight DECIMAL(5, 4) NOT NULL, -- e.g., 0.1500 for 15%
    effective_from DATE NOT NULL,
    effective_to DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE data_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    source_type VARCHAR(50) NOT NULL, -- realtime, historical, demo
    status VARCHAR(50) DEFAULT 'UNKNOWN', -- LIVE, RUNNING, WARNING, ERROR, BLOCKED, UNAVAILABLE, DEMO
    last_successful_collection TIMESTAMP WITH TIME ZONE,
    last_attempt TIMESTAMP WITH TIME ZONE,
    failure_count INTEGER DEFAULT 0,
    collection_mode VARCHAR(50)
);

CREATE TABLE collection_jobs (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES data_sources(id),
    status VARCHAR(50) NOT NULL, -- PENDING, RUNNING, COMPLETED, FAILED
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    records_collected INTEGER DEFAULT 0,
    error_message TEXT
);

CREATE TABLE collection_job_logs (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES collection_jobs(id),
    log_level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE fare_observations (
    id BIGSERIAL PRIMARY KEY,
    source VARCHAR(100) NOT NULL,
    source_type VARCHAR(50) NOT NULL, -- realtime, historical, demo, backtest
    origin VARCHAR(3) REFERENCES airports(iata_code),
    destination VARCHAR(3) REFERENCES airports(iata_code),
    route VARCHAR(7) REFERENCES routes(route_code),
    airline VARCHAR(100) NOT NULL,
    flight_number VARCHAR(20),
    travel_date DATE NOT NULL,
    observation_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    departure_time TIMESTAMP WITH TIME ZONE,
    arrival_time TIMESTAMP WITH TIME ZONE,
    advance_purchase_days INTEGER NOT NULL,
    fare_class VARCHAR(50),
    base_fare DECIMAL(10, 2),
    taxes DECIMAL(10, 2),
    fees DECIMAL(10, 2),
    airport_fees DECIMAL(10, 2),
    udf DECIMAL(10, 2),
    convenience_charge DECIMAL(10, 2),
    total_fare DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'INR',
    stops INTEGER DEFAULT 0,
    availability VARCHAR(50),
    raw_data JSONB,
    cleaned_value DECIMAL(10, 2),
    outlier_flag BOOLEAN DEFAULT FALSE,
    quality_score DECIMAL(5, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE historical_fares (
    id BIGSERIAL PRIMARY KEY,
    -- Similar schema for purely historical imported reference data
    route VARCHAR(7) REFERENCES routes(route_code),
    airline VARCHAR(100),
    travel_month DATE NOT NULL, -- First day of the month
    average_fare DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'INR',
    source VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE index_values (
    id SERIAL PRIMARY KEY,
    index_date DATE NOT NULL,
    index_type VARCHAR(20) NOT NULL, -- DAILY, WEEKLY, MONTHLY
    base_period VARCHAR(20) NOT NULL, -- e.g., '2026-01'
    index_value DECIMAL(10, 2) NOT NULL,
    daily_change DECIMAL(5, 2),
    weekly_change DECIMAL(5, 2),
    monthly_change DECIMAL(5, 2),
    yoy_change DECIMAL(5, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(index_date, index_type, base_period)
);

CREATE TABLE data_quality_logs (
    id SERIAL PRIMARY KEY,
    observation_id BIGINT REFERENCES fare_observations(id),
    issue_type VARCHAR(100) NOT NULL, -- MISSING_VALUE, OUTLIER, INVALID_DATE, NEGATIVE_FARE
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE backtest_results (
    id SERIAL PRIMARY KEY,
    backtest_period_start DATE NOT NULL,
    backtest_period_end DATE NOT NULL,
    mae DECIMAL(10, 4),
    rmse DECIMAL(10, 4),
    correlation DECIMAL(5, 4),
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_fare_obs_route ON fare_observations(route);
CREATE INDEX idx_fare_obs_airline ON fare_observations(airline);
CREATE INDEX idx_fare_obs_source ON fare_observations(source);
CREATE INDEX idx_fare_obs_travel_date ON fare_observations(travel_date);
CREATE INDEX idx_fare_obs_obs_ts ON fare_observations(observation_timestamp);
CREATE INDEX idx_fare_obs_adv_purch ON fare_observations(advance_purchase_days);
CREATE INDEX idx_fare_obs_src_type ON fare_observations(source_type);

-- Seed Initial Roles
INSERT INTO roles (name, description) VALUES
('Admin', 'Full access to manage sources, run jobs, and configure settings'),
('Analyst', 'Access to run backtests, analyze data, and export reports'),
('Viewer', 'Read-only access to dashboard and analytics');
