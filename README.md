# Crude Oil Multi-Factor Walkforward Strategy

A systematic trading strategy for **Brent Crude Oil (CO1 Comdty)** that dynamically selects the best-performing signal each quarter using a walkforward backtesting framework. The strategy combines momentum, moving-average crossover, and U.S. Dollar Index signals with volatility-scaled position sizing and risk management overlays.

> **Disclaimer:** The strategy logic, hypothesis generation, and research direction were independently developed by the author. AI assistance was utilized for code generation and syntax correction.

---

## 1. Performance Summary

The strategy demonstrates robust out-of-sample performance, significantly outperforming a buy-and-hold approach.

| Metric | Value |
| :--- | :--- |
| **Sharpe Ratio** | 1.11 |
| **Total Return** | 242.29% |
| **Annualized Return** | 15.50% |
| **Max Drawdown** | -16.80% |

### Equity Curve vs Drawdown

![Equity Curve](equity_curve.png)
![Drawdown](drawdown.png)

---

## 2. How It Works

The notebook (`learn.ipynb`) walks through the entire research process from EDA to final strategy. Here's the high-level flow:

```mermaid
graph TD
    A[Raw Price Data (Brent Crude, DXY)] --> B[14 Trading Strategies]
    B --> C[Risk Management Overlays]
    C --> D[Walkforward Backtester]
    D --> E[Portfolio Returns]
```

### Signal Families

| Family | Variants | Description |
| :--- | :--- | :--- |
| **Momentum** | 20D, 30D, 60D, 120D, 200D | Go long if N-day return is positive, short otherwise |
| **MA Crossover** | 6 pairs | Go long when fast MA crosses above slow MA |
| **DXY (Dollar Index)** | 3 pairs | Go long on oil when the dollar is weakening |

### Strategy Parameters

| Parameter | Value |
| :--- | :--- |
| Transaction Cost | 1.5 bps per trade |
| Volatility Target | 15% annualized |
| Stop Loss | -3% cumulative trade return |
| Min Holding Period | 10 days |
| Lookback Period | 12 months |
| Rebalance Frequency | Quarterly |

### Sensitivity Analysis

The stop-loss threshold of -3% was selected based on a sensitivity sweep. Tighter stops (>-2%) caused excessive churn, while looser stops (<-5%) failed to protect against tail risk.

![Stop Loss Sensitivity](stoploss_sensitivity.png)

---

## 3. Key Findings from EDA

Before building strategies, we analyzed the statistical properties of Brent Crude returns to inform our design.

### Price Trends & Volatility
Crude oil exhibits strong trending behavior but also extreme volatility clustering. This justifies the use of trend-following signals combined with volatility-scaled position sizing.

![Price Trends](price_trends.png)

### Autocorrelation
We found **no significant daily return autocorrelation** at any lag. This means short-lookback strategies (1D, 5D, 10D) trade on noise, not signal. We dropped them in favor of longer-term trend following.

![ACF Plot](acf_plot.png)

### Seasonality
Contrary to popular belief, we found **no reliable monthly seasonal pattern** in the 8-year dataset. The strategy therefore does not use calendar-based signals.

![Seasonality Heatmap](seasonality_heatmap.png)

### Return Distribution
The return distribution has **negative skew** and **high kurtosis** (fat tails), meaning crashes are more frequent and severe than rallies. This validated the need for a hard stop loss.

![Return Distribution](return_distribution.png)

---

## 4. Project Structure

| File | Description |
| :--- | :--- |
| `learn.ipynb` | Main notebook: EDA, strategy construction, backtesting, and analysis. |
| `brent_index.xlsx` | Brent Crude Oil front-month futures price data. |
| `dxy.csv` | U.S. Dollar Index (DTWEXBGS) data from FRED. |
| `psw01.xls` | EIA Weekly Petroleum Status Report (inventory data). |
| `Strategy_Report.md` | Detailed research report documenting methodology and findings. |
| `requirements.txt` | Python dependencies. |

---

## 5. Quick Start

### Set up the environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run the notebook

Open `learn.ipynb` in Jupyter or VS Code to reproduce the analysis.

---

## License

This project is for educational and research purposes.
