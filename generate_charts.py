"""Generate performance charts for the README."""
import sys
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# --- Load data ---
df = pd.read_excel(r"C:\Users\Acer\Downloads\cand_proj\brent_index.xlsx", parse_dates=['date'], index_col='date')
rets = df['CO1 Comdty'].pct_change()
tcost = 0.00015

# --- Volatility scaling ---
target_annual_vol = 0.15
rolling_vol = rets.rolling(20).std() * np.sqrt(252)
vol_scalar = (target_annual_vol / rolling_vol).clip(0.25, 3.0)

# --- Regime detection ---
sma_200 = df['CO1 Comdty'].rolling(200).mean()
trending = df['CO1 Comdty'] > sma_200
sideways = ~trending

# --- Helper functions ---
def apply_holding_period(signal, min_hold=5):
    filtered = signal.copy()
    last_trade_idx = -min_hold
    current_pos = 0
    for i in range(len(filtered)):
        if pd.isna(filtered.iloc[i]):
            filtered.iloc[i] = current_pos
            continue
        if filtered.iloc[i] != current_pos:
            if (i - last_trade_idx) >= min_hold:
                current_pos = filtered.iloc[i]
                last_trade_idx = i
            else:
                filtered.iloc[i] = current_pos
        else:
            filtered.iloc[i] = current_pos
    return filtered

def apply_stop_loss_take_profit(signal, prices, stop_loss=-0.02, take_profit=0.04):
    filtered = signal.copy().astype(float)
    entry_price = None
    current_pos = 0
    stopped_out = False
    for i in range(len(filtered)):
        raw_signal = filtered.iloc[i]
        price = prices.iloc[i]
        if pd.isna(price) or pd.isna(raw_signal):
            filtered.iloc[i] = current_pos
            continue
        if stopped_out:
            if raw_signal != current_pos and raw_signal != 0:
                current_pos = raw_signal
                entry_price = price
                stopped_out = False
            else:
                filtered.iloc[i] = 0
                continue
        if current_pos == 0 and raw_signal != 0:
            current_pos = raw_signal
            entry_price = price
            filtered.iloc[i] = current_pos
            continue
        if current_pos != 0 and entry_price is not None and entry_price != 0:
            pnl_pct = current_pos * (price - entry_price) / entry_price
            if pnl_pct <= stop_loss or pnl_pct >= take_profit:
                filtered.iloc[i] = 0
                current_pos = 0
                entry_price = None
                stopped_out = True
                continue
        if raw_signal != current_pos and raw_signal != 0:
            current_pos = raw_signal
            entry_price = price
        filtered.iloc[i] = current_pos
    return filtered

min_hold = 5
stop_loss = -0.02
take_profit = 0.04

# --- Build strategies ---
lookback_days = [2, 4, 8, 16, 32, 64, 128, 256]
pnl_strategies = pd.DataFrame(index=rets.index)

for m in lookback_days:
    rolling_ret = (1 + rets).rolling(window=m).apply(np.prod, raw=True).shift(1) - 1
    
    momentum_signal = pd.Series(np.where(rolling_ret > 0, 1, -1), index=rets.index)
    momentum_signal = apply_holding_period(momentum_signal, min_hold)
    momentum_signal = apply_stop_loss_take_profit(momentum_signal, df['CO1 Comdty'], stop_loss, take_profit)
    momentum_signal = momentum_signal.where(trending.shift(1), 0)
    pnl_strategies[f"{m}D_momentum"] = (momentum_signal * vol_scalar) * rets - tcost * abs(momentum_signal.diff())
    
    meanrev_signal = pd.Series(np.where(rolling_ret > 0, -1, 1), index=rets.index)
    meanrev_signal = apply_holding_period(meanrev_signal, min_hold)
    meanrev_signal = apply_stop_loss_take_profit(meanrev_signal, df['CO1 Comdty'], stop_loss, take_profit)
    meanrev_signal = meanrev_signal.where(sideways.shift(1), 0)
    pnl_strategies[f"{m}D_meanrev"] = (meanrev_signal * vol_scalar) * rets - tcost * abs(meanrev_signal.diff())

ma_pairs = [(2,10),(5,20),(10,50),(20,100),(50,200),(100,300)]
for short_w, long_w in ma_pairs:
    short_ma = df['CO1 Comdty'].rolling(window=short_w).mean()
    long_ma = df['CO1 Comdty'].rolling(window=long_w).mean()
    ma_signal = pd.Series(np.where(short_ma.shift(1) > long_ma.shift(1), 1, -1), index=rets.index)
    ma_signal = apply_holding_period(ma_signal, min_hold)
    ma_signal = apply_stop_loss_take_profit(ma_signal, df['CO1 Comdty'], stop_loss, take_profit)
    pnl_strategies[f"{short_w}_{long_w}_ma_crossover"] = (ma_signal * vol_scalar) * rets - tcost * abs(ma_signal.diff())

bb_windows = [20, 50]
for w in bb_windows:
    mid = df['CO1 Comdty'].rolling(window=w).mean()
    std = df['CO1 Comdty'].rolling(window=w).std()
    upper = mid + 2 * std
    lower = mid - 2 * std
    price = df['CO1 Comdty']
    bb_signal = pd.Series(np.where(price.shift(1) < lower.shift(1), 1,
                 np.where(price.shift(1) > upper.shift(1), -1, np.nan)), index=rets.index)
    bb_signal = bb_signal.ffill().fillna(0)
    bb_signal = apply_holding_period(bb_signal, min_hold)
    bb_signal = apply_stop_loss_take_profit(bb_signal, df['CO1 Comdty'], stop_loss, take_profit)
    pnl_strategies[f'{w}D_bollinger'] = (bb_signal * vol_scalar) * rets - tcost * abs(bb_signal.diff())

rsi_windows = [14, 28]
for w in rsi_windows:
    delta = df['CO1 Comdty'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=w).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=w).mean()
    rs = gain / loss
    rsi_val = 100 - (100 / (1 + rs))
    rsi_signal = pd.Series(np.where(rsi_val.shift(1) < 30, 1,
                  np.where(rsi_val.shift(1) > 70, -1, np.nan)), index=rets.index)
    rsi_signal = rsi_signal.ffill().fillna(0)
    rsi_signal = apply_holding_period(rsi_signal, min_hold)
    rsi_signal = apply_stop_loss_take_profit(rsi_signal, df['CO1 Comdty'], stop_loss, take_profit)
    pnl_strategies[f'{w}D_rsi'] = (rsi_signal * vol_scalar) * rets - tcost * abs(rsi_signal.diff())

breakout_windows = [20, 55]
for w in breakout_windows:
    high_w = df['CO1 Comdty'].rolling(window=w).max()
    low_w = df['CO1 Comdty'].rolling(window=w).min()
    price = df['CO1 Comdty']
    brk_signal = pd.Series(np.where(price.shift(1) >= high_w.shift(2), 1,
                  np.where(price.shift(1) <= low_w.shift(2), -1, np.nan)), index=rets.index)
    brk_signal = brk_signal.ffill().fillna(0)
    brk_signal = apply_holding_period(brk_signal, min_hold)
    brk_signal = apply_stop_loss_take_profit(brk_signal, df['CO1 Comdty'], stop_loss, take_profit)
    pnl_strategies[f'{w}D_breakout'] = (brk_signal * vol_scalar) * rets - tcost * abs(brk_signal.diff())

# --- Run walkforward backtest (Top-3 ensemble) ---
from dateutil.relativedelta import relativedelta

top_n = 3
portfolio_pnl = pd.Series(index=rets.index, dtype=np.float64)

def sharpe_ratio(returns):
    return returns.mean() / returns.std() if returns.std() != 0 else 0

periods = pd.date_range(start=pnl_strategies.index[0],
                        end=pnl_strategies.index[-1] + relativedelta(months=3),
                        freq='3M')

rebalance_strats = []
for start_date, end_date in zip(periods[:-1], periods[1:]):
    lookback_end = start_date - pd.Timedelta(days=1)
    lookback_start = lookback_end - relativedelta(months=24)
    if lookback_start < pnl_strategies.index[0]:
        continue
    lookback_df = pnl_strategies.loc[lookback_start:lookback_end]
    scores = lookback_df.apply(sharpe_ratio)
    top_strats = scores.nlargest(top_n).index.tolist()
    ensemble_rets = pnl_strategies[top_strats].loc[start_date:end_date].mean(axis=1)
    portfolio_pnl.loc[start_date:end_date] = ensemble_rets
    rebalance_strats.append({'period': f"{start_date.strftime('%Y-%m')}", 'top_strategies': top_strats})

pnl = portfolio_pnl.dropna()
trading_days = 252

# --- Compute metrics ---
total_return = (1 + pnl).prod() - 1
ann_return = (1 + total_return) ** (trading_days / len(pnl)) - 1
ann_vol = pnl.std() * np.sqrt(trading_days)
sharpe = ann_return / ann_vol if ann_vol != 0 else 0
cum = (1 + pnl).cumprod()
peak = cum.cummax()
drawdown = (cum - peak) / peak
max_dd = drawdown.min()
calmar = ann_return / abs(max_dd) if max_dd != 0 else 0
win_rate = (pnl > 0).sum() / len(pnl)
gross_profit = pnl[pnl > 0].sum()
gross_loss = abs(pnl[pnl < 0].sum())
profit_factor = gross_profit / gross_loss if gross_loss != 0 else float('inf')

print(f"Total Return: {total_return:.2%}")
print(f"Ann Return: {ann_return:.2%}")
print(f"Sharpe: {sharpe:.2f}")
print(f"Max DD: {max_dd:.2%}")
print(f"Win Rate: {win_rate:.2%}")
print(f"Profit Factor: {profit_factor:.2f}")

# --- Style ---
plt.style.use('dark_background')
fig_color = '#0d1117'
accent = '#58a6ff'
accent2 = '#f0883e'
accent3 = '#3fb950'
grid_color = '#21262d'

out_dir = r"C:\Users\Acer\Downloads\cand_proj\images"
import os
os.makedirs(out_dir, exist_ok=True)

# ==============================
# CHART 1: Cumulative Returns
# ==============================
fig, ax = plt.subplots(figsize=(14, 6))
fig.patch.set_facecolor(fig_color)
ax.set_facecolor(fig_color)
ax.plot(cum.index, cum.values, color=accent, linewidth=1.8, label='Portfolio (Top-3 Ensemble)')
ax.fill_between(cum.index, 1, cum.values, alpha=0.08, color=accent)
ax.axhline(y=1, color='#484f58', linewidth=0.8, linestyle='--')
ax.set_title('Cumulative Returns — Crude Multi-Factor Walkforward', fontsize=16, fontweight='bold', color='white', pad=15)
ax.set_xlabel('Date', color='#8b949e', fontsize=11)
ax.set_ylabel('Growth of $1', color='#8b949e', fontsize=11)
ax.tick_params(colors='#8b949e')
ax.grid(True, alpha=0.15, color=grid_color)
ax.legend(loc='upper left', fontsize=10, facecolor=fig_color, edgecolor=grid_color)
for spine in ax.spines.values(): spine.set_color(grid_color)
plt.tight_layout()
plt.savefig(os.path.join(out_dir, 'cumulative_returns.png'), dpi=150, bbox_inches='tight', facecolor=fig_color)
plt.close()
print("Saved cumulative_returns.png")

# ==============================
# CHART 2: Drawdown
# ==============================
fig, ax = plt.subplots(figsize=(14, 4))
fig.patch.set_facecolor(fig_color)
ax.set_facecolor(fig_color)
ax.fill_between(drawdown.index, 0, drawdown.values, color='#f85149', alpha=0.5)
ax.plot(drawdown.index, drawdown.values, color='#f85149', linewidth=0.8)
ax.set_title('Underwater (Drawdown) Chart', fontsize=14, fontweight='bold', color='white', pad=12)
ax.set_ylabel('Drawdown %', color='#8b949e', fontsize=11)
ax.tick_params(colors='#8b949e')
ax.grid(True, alpha=0.15, color=grid_color)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.0%}'))
for spine in ax.spines.values(): spine.set_color(grid_color)
plt.tight_layout()
plt.savefig(os.path.join(out_dir, 'drawdown.png'), dpi=150, bbox_inches='tight', facecolor=fig_color)
plt.close()
print("Saved drawdown.png")

# ==============================
# CHART 3: Rolling Sharpe Ratio
# ==============================
rolling_sharpe = pnl.rolling(126).apply(lambda x: x.mean()/x.std() * np.sqrt(252) if x.std() != 0 else 0)
fig, ax = plt.subplots(figsize=(14, 4))
fig.patch.set_facecolor(fig_color)
ax.set_facecolor(fig_color)
ax.plot(rolling_sharpe.index, rolling_sharpe.values, color=accent2, linewidth=1.2)
ax.axhline(y=0, color='#484f58', linewidth=0.8, linestyle='--')
ax.axhline(y=1, color=accent3, linewidth=0.8, linestyle='--', alpha=0.5, label='Sharpe = 1')
ax.fill_between(rolling_sharpe.index, 0, rolling_sharpe.values, 
                where=rolling_sharpe.values > 0, alpha=0.15, color=accent3)
ax.fill_between(rolling_sharpe.index, 0, rolling_sharpe.values,
                where=rolling_sharpe.values < 0, alpha=0.15, color='#f85149')
ax.set_title('Rolling 6-Month Sharpe Ratio', fontsize=14, fontweight='bold', color='white', pad=12)
ax.set_ylabel('Sharpe Ratio', color='#8b949e', fontsize=11)
ax.tick_params(colors='#8b949e')
ax.grid(True, alpha=0.15, color=grid_color)
ax.legend(loc='upper left', fontsize=9, facecolor=fig_color, edgecolor=grid_color)
for spine in ax.spines.values(): spine.set_color(grid_color)
plt.tight_layout()
plt.savefig(os.path.join(out_dir, 'rolling_sharpe.png'), dpi=150, bbox_inches='tight', facecolor=fig_color)
plt.close()
print("Saved rolling_sharpe.png")

# ==============================
# CHART 4: Strategy selection over time
# ==============================
fig, ax = plt.subplots(figsize=(14, 5))
fig.patch.set_facecolor(fig_color)
ax.set_facecolor(fig_color)

# Individual strategy cumulative returns (faded)
for col in pnl_strategies.columns[:10]:
    strat_cum = (1 + pnl_strategies[col].dropna()).cumprod()
    ax.plot(strat_cum.index, strat_cum.values, alpha=0.15, linewidth=0.6, color='#8b949e')

# Portfolio on top
ax.plot(cum.index, cum.values, color=accent, linewidth=2.2, label='Ensemble Portfolio', zorder=10)
ax.set_title('Ensemble Portfolio vs Individual Strategies', fontsize=14, fontweight='bold', color='white', pad=12)
ax.set_ylabel('Growth of $1', color='#8b949e', fontsize=11)
ax.tick_params(colors='#8b949e')
ax.grid(True, alpha=0.15, color=grid_color)
ax.legend(loc='upper left', fontsize=10, facecolor=fig_color, edgecolor=grid_color)
for spine in ax.spines.values(): spine.set_color(grid_color)
plt.tight_layout()
plt.savefig(os.path.join(out_dir, 'ensemble_vs_individual.png'), dpi=150, bbox_inches='tight', facecolor=fig_color)
plt.close()
print("Saved ensemble_vs_individual.png")

# Save metrics to a file for the README
with open(os.path.join(out_dir, 'metrics.txt'), 'w') as f:
    f.write(f"total_return={total_return:.2%}\n")
    f.write(f"ann_return={ann_return:.2%}\n")
    f.write(f"ann_vol={ann_vol:.2%}\n")
    f.write(f"sharpe={sharpe:.2f}\n")
    f.write(f"max_dd={max_dd:.2%}\n")
    f.write(f"calmar={calmar:.2f}\n")
    f.write(f"win_rate={win_rate:.2%}\n")
    f.write(f"profit_factor={profit_factor:.2f}\n")

print("\nAll charts generated!")
