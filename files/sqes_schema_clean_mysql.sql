-- 
-- SQES - Seismic Quality Evaluation System
-- MySQL Database Schema
-- 

-- Set standard UTF-8 environments
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

--
-- Table: stations
-- Description: Master table for seismometer station metadata
--
CREATE TABLE stations (
    code VARCHAR(10) NOT NULL COMMENT 'Station code (e.g., BBJI, GSI)',
    network VARCHAR(10) COMMENT 'Network code (e.g., IA)',
    latitude DECIMAL(9,7) COMMENT 'Station latitude in decimal degrees',
    longitude DECIMAL(8,5) COMMENT 'Station longitude in decimal degrees',
    province VARCHAR(50),
    location VARCHAR(100),
    year INT,
    upt VARCHAR(100),
    balai INT,
    digitizer_type VARCHAR(100),
    communication_type VARCHAR(100),
    network_group VARCHAR(100),
    PRIMARY KEY (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Master table containing metadata for all seismometer stations';


--
-- Table: stations_sensor
-- Description: Sensor information for each station channel
--
CREATE TABLE stations_sensor (
    code VARCHAR(50) COMMENT 'Station code',
    location VARCHAR(50) COMMENT 'Location code (e.g., 00)',
    channel VARCHAR(50) COMMENT 'Channel code (e.g., BHE, BHN, BHZ)',
    sensor TEXT COMMENT 'Sensor type/model',
    CONSTRAINT unique_constraint_stations_sensor UNIQUE (code, location, channel)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Sensor type information for each station component/channel';


--
-- Table: stations_sensor_latency
-- Description: Real-time data latency tracking for station channels
--
CREATE TABLE stations_sensor_latency (
    id INT NOT NULL AUTO_INCREMENT,
    net VARCHAR(50),
    sta VARCHAR(50),
    datetime DATETIME,
    channel VARCHAR(50),
    last_time_channel DATETIME,
    latency INT COMMENT 'Latency in seconds',
    color_code VARCHAR(20),
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Tracks data transmission latency for each station channel';


--
-- Table: stations_qc_details
-- Description: Detailed quality control metrics per station component
--
CREATE TABLE stations_qc_details (
    id VARCHAR(100) NOT NULL COMMENT 'Unique identifier (format: CODE_DATE_CHANNEL)',
    code VARCHAR(50),
    date DATE,
    channel VARCHAR(50),
    rms DECIMAL(7,2) COMMENT 'Root Mean Square amplitude',
    amplitude_ratio DECIMAL(7,2) COMMENT 'Ratio between max and min amplitudes',
    availability DECIMAL(5,2) COMMENT 'Data availability percentage (0-100)',
    num_gap INT COMMENT 'Number of data gaps detected',
    num_overlap INT COMMENT 'Number of data overlaps detected',
    num_spikes INT COMMENT 'Number of spikes detected',
    perc_below_nlnm DECIMAL(5,2) COMMENT 'Percentage of PSD below NLNM (New Low Noise Model)',
    perc_above_nhnm DECIMAL(5,2) COMMENT 'Percentage of PSD above NHNM (New High Noise Model)',
    linear_dead_channel DECIMAL(7,2) COMMENT 'Linear dead channel detection metric',
    gsn_dead_channel DECIMAL(7,2) COMMENT 'GSN dead channel detection metric',
    sp_percentage DECIMAL(5,2) COMMENT 'PSD percentage in short period range (0.05-5 Hz)',
    bw_percentage DECIMAL(5,2) COMMENT 'PSD percentage in broadband range (5-20 Hz)',
    lp_percentage DECIMAL(5,2) COMMENT 'PSD percentage in long period range (20-100 Hz)',
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Detailed quality metrics for each station component (E/N/Z) per day';


--
-- Table: stations_data_quality
-- Description: Overall quality score per station per day
--
CREATE TABLE stations_data_quality (
    id INT NOT NULL AUTO_INCREMENT,
    date DATE,
    code VARCHAR(50),
    quality_percentage DECIMAL(5,2) COMMENT 'Overall quality score (0-100%)',
    result TEXT COMMENT 'Quality classification: Baik/Cukup Baik/Buruk/Mati',
    details TEXT COMMENT 'Additional notes or warnings',
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Final quality scores and classifications per station per day';


--
-- Table: stations_dominant_data_quality
-- Description: Most common quality classification per station
--
CREATE TABLE stations_dominant_data_quality (
    code VARCHAR(50) NOT NULL,
    dominant_data_quality TEXT,
    PRIMARY KEY (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Tracks the most frequently occurring quality classification for each station';


--
-- Table: stations_site_quality
-- Description: Site quality assessment metrics
--
CREATE TABLE stations_site_quality (
    code VARCHAR(50) NOT NULL,
    geology TEXT,
    geoval INT,
    vs30 TEXT COMMENT 'Average shear-wave velocity in top 30m',
    vs30val INT,
    photovoltaic TEXT,
    photoval INT,
    hvsr DECIMAL(5,2) COMMENT 'Horizontal-to-Vertical Spectral Ratio',
    hvsrval INT,
    psd DECIMAL(5,2) COMMENT 'Power Spectral Density metric',
    psdval INT,
    score DECIMAL(5,2) COMMENT 'Overall site quality score',
    site_quality TEXT,
    PRIMARY KEY (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Site quality assessment based on geological and environmental factors';


--
-- Table: stations_visit
-- Description: Station maintenance visit tracking
--
CREATE TABLE stations_visit (
    code VARCHAR(50) NOT NULL,
    visit_year VARCHAR(20),
    visit_count BIGINT COMMENT 'Number of visits in the specified year',
    PRIMARY KEY (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Tracks maintenance visits to each station';

SET FOREIGN_KEY_CHECKS = 1;




CREATE TABLE tb_qcdetail (
    id_kode VARCHAR(100) NOT NULL COMMENT 'Unique identifier (format: KODE_TANGGAL_KOMP)',
    kode VARCHAR(10) NOT NULL COMMENT 'Station code (e.g., BBJI, WBNI)',
    tanggal DATE NOT NULL COMMENT 'Processing data date',
    komp VARCHAR(10) NOT NULL COMMENT 'Component/Channel code (e.g., BHZ, HN1)',
    rms DECIMAL(7,2) DEFAULT NULL COMMENT 'Root Mean Square amplitude',
    ratioamp DECIMAL(7,2) DEFAULT NULL COMMENT 'Ratio between max and min amplitudes',
    avail DECIMAL(5,2) DEFAULT NULL COMMENT 'Data availability percentage (0-100)',
    ngap INT DEFAULT NULL COMMENT 'Number of data gaps detected',
    nover INT DEFAULT NULL COMMENT 'Number of data overlaps detected',
    num_spikes INT DEFAULT NULL COMMENT 'Number of spikes detected',
    pct_above DECIMAL(5,2) DEFAULT NULL COMMENT 'Percentage of PSD above NHNM limits',
    pct_below DECIMAL(5,2) DEFAULT NULL COMMENT 'Percentage of PSD below NLNM limits',
    dead_channel_lin DECIMAL(7,2) DEFAULT NULL COMMENT 'Linear dead channel metric',
    dead_channel_gsn DECIMAL(7,2) DEFAULT NULL COMMENT 'GSN dead channel metric',
    diff20_100 DECIMAL(5,2) DEFAULT NULL COMMENT 'PSD percentage in long period range (20-100 Hz)',
    diff5_20 DECIMAL(5,2) DEFAULT NULL COMMENT 'PSD percentage in broadband range (5-20 Hz)',
    diff5 DECIMAL(5,2) DEFAULT NULL COMMENT 'PSD percentage in short period range (0.05-5 Hz)',
    PRIMARY KEY (id_kode),
    -- Performance optimization indexes based on your code's WHERE clauses
    INDEX idx_tanggal_kode (tanggal, kode)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Detailed daily quality control metrics per channel component';



CREATE TABLE tb_qcres (
    kode_res VARCHAR(10) NOT NULL COMMENT 'Station code reference (e.g., BBJI)',
    tanggal_res DATE NOT NULL COMMENT 'The date for which evaluation was calculated',
    percqc DECIMAL(5,2) DEFAULT NULL COMMENT 'Overall QC percentage score (0.00 - 100.00)',
    kualitas VARCHAR(50) DEFAULT NULL COMMENT 'Quality category classification (e.g., Baik, Mati)',
    tipe VARCHAR(50) DEFAULT NULL COMMENT 'Data stream evaluation type descriptor',
    keterangan TEXT DEFAULT NULL COMMENT 'Concatenated array string details or warning messages',
    PRIMARY KEY (kode_res, tanggal_res)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Summary table for daily station quality evaluation analysis results';




CREATE TABLE tb_slmon (
    kode_sensor VARCHAR(10) NOT NULL COMMENT 'Station network sensor code identifier',
    lokasi_sensor VARCHAR(10) DEFAULT '' COMMENT 'Location code (e.g., 00 or blank)',
    sistem_sensor VARCHAR(100) DEFAULT NULL COMMENT 'Sensor system type, maker model descriptor',
    latitude DECIMAL(9,7) DEFAULT NULL COMMENT 'Station latitude location in decimal degrees',
    longitude DECIMAL(8,5) DEFAULT NULL COMMENT 'Station longitude location in decimal degrees',
    PRIMARY KEY (kode_sensor)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Station layout inventory metadata and live monitoring tracking registry';