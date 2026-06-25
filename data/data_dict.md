# Data Dictionary - Bluestock Mutual Fund Analytics Database

## 1. Table: dim_fund (Dimension Table)
Contains master configurations for each mapped mutual fund scheme.

| Column Name | Data Type | Key Type | Business Definition | Source Reference |
| :--- | :--- | :--- | :--- | :--- |
| amfi_code | VARCHAR(20) | Primary Key | Unique code allocated by AMFI to reference schemas | Live API/Filename |
| scheme_name | VARCHAR(255) | None | Standard descriptive name of the mutual fund asset | Live API |
| category | VARCHAR(100) | None | High-level asset allocation group (e.g., Equity Large Cap) | Generated Data |
| sub_category| VARCHAR(100) | None | Sub-class category (e.g., Growth, Dividend) | Generated Data |
| risk_grade | VARCHAR(50) | None | Calculated investment risk index tier assigned to fund | Generated Data |

## 2. Table: fact_nav (Fact Table)
Stores sequential historical tracking data for asset evaluations.

| Column Name | Data Type | Key Type | Business Definition | Source Reference |
| :--- | :--- | :--- | :--- | :--- |
| nav_id | INT | Primary Key | Auto-incrementing identifier row sequence index | Database Native |
| amfi_code | VARCHAR(20) | Foreign Key | Mapping link directly tying records to dim_fund | Data Cleaning Step |
| date | DATE | None | Evaluated pricing timeline market validation day | Live API Data |
| nav | DECIMAL(15,4)| None | Net Asset Value valuation price per unit on specified day | Live API Data |