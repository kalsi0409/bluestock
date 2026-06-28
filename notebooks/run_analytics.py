import os
import numpy as np
import pandas as pd
import scipy.stats as stats
import matplotlib.pyplot as plt
import seaborn as sns

# Set visual layouts globally at the start to eliminate active figure warnings
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = (14, 7)
plt.rcParams['figure.dpi'] = 100

print("Initializing Mutual Fund Performance Analytics Engine...")

# Constants & Risk Parameters
Rf_DAILY = 0.065 / 252  # 6.5% Annual Repo Rate Proxy (RBI)
TRADING_DAYS = 252

# Relative directory mapping from Project Root layout
DATA_DIR = os.path.join('data', 'processed')
REPORT_DIR = os.path.join('reports')
os.makedirs(REPORT_DIR, exist_ok=True)

# 1. Ingest Data
print(" Loading datasets from data/processed/...")
fund_master = pd.read_csv(os.path.join(DATA_DIR, '01_fund_master.csv'))
nav_history = pd.read_csv(os.path.join(DATA_DIR, '02_nav_history.csv'), parse_dates=['date'])
benchmarks = pd.read_csv(os.path.join(DATA_DIR, '10_benchmark_indices.csv'), parse_dates=['date'])

# Format NAV wide data: Rows = Dates, Columns = AMFI Codes
nav_wide = nav_history.pivot(index='date', columns='amfi_code', values='nav').sort_index()

# 2. Daily Returns & Benchmark Series Isolation
daily_returns = nav_wide.pct_change(fill_method=None)

# Isolate Nifty 100 series explicitly to avoid column matching friction
nifty100_df = benchmarks[benchmarks['index_name'] == 'NIFTY100'].sort_values('date')
nifty100_series = nifty100_df.set_index('date')['close_value'].pct_change(fill_method=None).dropna()
nifty100_series.name = 'NIFTY100'

# Isolate benchmark data matrices for plotting structures
bench_wide = benchmarks.pivot(index='date', columns='index_name', values='close_value').sort_index()
bench_targets = bench_wide[['NIFTY50', 'NIFTY100']].pct_change(fill_method=None)

# 3. Performance Metrics Processing Engine
print(" Computing risk-adjusted return metrics, Alpha, Beta, and Drawdowns...")
performance_metrics = []

for amfi in nav_wide.columns:
    series = nav_wide[amfi].dropna()
    rets = daily_returns[amfi].dropna()
    
    if len(series) < TRADING_DAYS: 
        continue  # Skip if there's insufficient pricing data
        
    # Max Drawdown Calculation
    running_max = series.cummax()
    drawdowns = (series / running_max) - 1
    max_dd = drawdowns.min()
    
    # Calculate CAGR for 1Yr, 3Yr, 5Yr windows
    nav_end = series.iloc[-1]
    cagr_1y = (nav_end / series.iloc[-TRADING_DAYS]) - 1 if len(series) >= TRADING_DAYS else np.nan
    cagr_3y = (nav_end / series.iloc[-TRADING_DAYS*3])**(1/3) - 1 if len(series) >= TRADING_DAYS*3 else np.nan
    cagr_5y = (nav_end / series.iloc[-TRADING_DAYS*5])**(1/5) - 1 if len(series) >= TRADING_DAYS*5 else np.nan
    
    # Risk Adjusted Metrics: Sharpe & Sortino
    excess_rets = rets - Rf_DAILY
    sharpe = (excess_rets.mean() / rets.std()) * np.sqrt(TRADING_DAYS) if rets.std() > 0 else 0
    
    downside_std = rets[rets < 0].std()
    sortino = (excess_rets.mean() / downside_std) * np.sqrt(TRADING_DAYS) if downside_std > 0 else 0
    
    # Alpha & Beta OLS Linear Regression against NIFTY 100
    aligned = pd.concat([rets, nifty100_series], axis=1, join='inner').dropna()
    if len(aligned) > 30:
        beta, intercept, _, _, _ = stats.linregress(aligned['NIFTY100'], aligned[amfi])
        alpha = intercept * TRADING_DAYS  # Annualized Alpha
    else:
        alpha, beta = np.nan, np.nan
        
    performance_metrics.append({
        'amfi_code': amfi, 'cagr_1y': cagr_1y, 'cagr_3y': cagr_3y, 'cagr_5y': cagr_5y,
        'sharpe_ratio': sharpe, 'sortino_ratio': sortino, 'max_drawdown': max_dd,
        'alpha': alpha, 'beta': beta
    })

df_perf = pd.DataFrame(performance_metrics)

# 4. Composite Scorecard Generation (0–100)
print("Creating rank scaling systems and composite indices...")
scorecard = df_perf.merge(fund_master[['amfi_code', 'scheme_name', 'expense_ratio_pct']], on='amfi_code')

# Compute rank percentiles
scorecard['rank_3y'] = scorecard['cagr_3y'].rank(pct=True)
scorecard['rank_sharpe'] = scorecard['sharpe_ratio'].rank(pct=True)
scorecard['rank_alpha'] = scorecard['alpha'].rank(pct=True)
scorecard['rank_expense'] = scorecard['expense_ratio_pct'].rank(pct=True, ascending=False) # Lower expense is better
scorecard['rank_dd'] = scorecard['max_drawdown'].rank(pct=True) # Less severe drawdown is better

# Apply core weighting metrics formula
scorecard['composite_score'] = (
    0.30 * scorecard['rank_3y'] +
    0.25 * scorecard['rank_sharpe'] +
    0.20 * scorecard['rank_alpha'] +
    0.15 * scorecard['rank_expense'] +
    0.10 * scorecard['rank_dd']
) * 100

scorecard = scorecard.sort_values(by='composite_score', ascending=False).reset_index(drop=True)

# Export processed files to data/processed directory
scorecard.to_csv(os.path.join(DATA_DIR, 'fund_scorecard.csv'), index=False)
scorecard[['amfi_code', 'scheme_name', 'alpha', 'beta']].to_csv(os.path.join(DATA_DIR, 'alpha_beta.csv'), index=False)

# 5. Benchmark Comparison Visual Generator
# =====================================================================
# 5. Benchmark Comparison Visual Generator (Fixed Date Alignment)
# =====================================================================
print("Plotting benchmark comparison chart...")

# Pin down top 5 funds by score
top_5_amfi = scorecard.head(5)['amfi_code'].tolist()

# Pivot indices and format cleanly
bench_wide = benchmarks.pivot(index='date', columns='index_name', values='close_value').sort_index()
bench_targets = bench_wide[['NIFTY50', 'NIFTY100']].pct_change(fill_method=None)

# Find an exact common starting date that exists across both fund NAV history AND benchmarks
three_years_ago = nav_wide.index[-1] - pd.Timedelta(days=3*365)
common_dates = nav_wide.index[
    (nav_wide.index >= three_years_ago) &
    (nav_wide.index.isin(bench_wide.index))
]

if len(common_dates) == 0:
    # Fallback to absolute available intersection slice if tight constraints miss
    start_date = max(nav_wide.index[0], bench_wide.index[0])
else:
    start_date = common_dates[0]

# Slice using the safe start date
funds_slice = nav_wide[top_5_amfi].loc[start_date:].dropna(how='all')
bench_slice = bench_wide[['NIFTY50', 'NIFTY100']].loc[start_date:].dropna()

# Double-check data exists before normalizing to base 100
if len(funds_slice) > 0 and len(bench_slice) > 0:
    funds_norm = (funds_slice / funds_slice.iloc[0]) * 100
    bench_norm = (bench_slice / bench_slice.iloc[0]) * 100

    plt.figure(figsize=(14, 8))
    for amfi in top_5_amfi:
        name = scorecard[scorecard['amfi_code'] == amfi]['scheme_name'].values[0]
        f_ret = daily_returns[amfi].loc[start_date:]
        b_ret = bench_targets['NIFTY100'].loc[start_date:]
        aligned_te = pd.concat([f_ret, b_ret], axis=1, join='inner').dropna()
        
        tracking_error = (aligned_te[amfi] - aligned_te['NIFTY100']).std() * np.sqrt(TRADING_DAYS) if len(aligned_te) > 0 else 0
        plt.plot(funds_norm.index, funds_norm[amfi], label=f"{name} (TE: {tracking_error:.2%})", alpha=0.85)

    plt.plot(bench_norm.index, bench_norm['NIFTY50'], label='NIFTY 50', color='black', linewidth=3, linestyle='--')
    plt.plot(bench_norm.index, bench_norm['NIFTY100'], label='NIFTY 100', color='crimson', linewidth=3, linestyle=':')

    plt.title("Top 5 Funds vs Benchmarks (3-Year Wealth Index Plan with Tracking Error)", fontsize=14, fontweight='bold')
    plt.xlabel("Timeline")
    plt.ylabel("Normalized Growth Core (Base 100)")
    plt.legend(loc='upper left', bbox_to_anchor=(1.01, 1))
    plt.tight_layout()

    plt.savefig(os.path.join(REPORT_DIR, "benchmark_comparison_chart.png"))
    plt.close()
    print(" Day 4 Tasks Complete! Outputs saved to data/processed/ and reports/")
else:
    print("Error: No intersecting data found within the selected date window slices.")

