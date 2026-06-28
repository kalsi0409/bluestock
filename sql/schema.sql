-- Create Database if not exists
CREATE DATABASE IF NOT EXISTS bluestock_mf;
USE bluestock_mf;

-- 1. Dimension Table: Fund Master
CREATE TABLE IF NOT EXISTS dim_fund (
    amfi_code VARCHAR(20) PRIMARY KEY,
    scheme_name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    sub_category VARCHAR(100),
    risk_grade VARCHAR(50)
);

-- 2. Dimension Table: Date reference
CREATE TABLE IF NOT EXISTS dim_date (
    date_id DATE PRIMARY KEY,
    year INT,
    month INT,
    month_name VARCHAR(20),
    quarter INT,
    day_of_week VARCHAR(20)
);

-- 3. Fact Table: Historical NAV Data
CREATE TABLE IF NOT EXISTS fact_nav (
    nav_id INT AUTO_INCREMENT PRIMARY KEY,
    amfi_code VARCHAR(20),
    date DATE,
    nav DECIMAL(15, 4) NOT NULL,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

-- 4. Fact Table: Investor Transactions
CREATE TABLE IF NOT EXISTS fact_transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    investor_id VARCHAR(50),
    amfi_code VARCHAR(20),
    transaction_date DATE,
    transaction_type ENUM('SIP', 'Lumpsum', 'Redemption'),
    amount DECIMAL(15, 2) NOT NULL,
    units DECIMAL(15, 4) NOT NULL,
    kyc_status VARCHAR(20),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

-- 5. Fact Table: Scheme Performance Profiles
CREATE TABLE IF NOT EXISTS fact_performance (
    performance_id INT AUTO_INCREMENT PRIMARY KEY,
    amfi_code VARCHAR(20),
    return_1y DECIMAL(5, 2),
    return_3y DECIMAL(5, 2),
    return_5y DECIMAL(5, 2),
    expense_ratio DECIMAL(4, 2),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);