# Crude Oil Multi-Factor Walkforward Strategy

A systematic trading strategy for **Brent Crude Oil (CO1 Comdty)** that dynamically selects the best-performing signal each quarter using a walkforward backtesting framework. The strategy combines momentum, moving-average crossover, and U.S. Dollar Index signals with volatility-scaled position sizing and risk management overlays.

> **Disclaimer:** The strategy logic, hypothesis generation, and research direction were independently developed by the author. AI assistance was utilized for code generation and syntax correction.

---

## 1. Performance Summary

The strategy demonstrates robust out-of-sample performance, significantly outperforming a buy-and-hold approach.

| Metric                      | Value   |
| :-------------------------- | :------ |
| **Sharpe Ratio**      | 1.11    |
| **Total Return**      | 242.29% |
| **Annualized Return** | 15.50%  |
| **Max Drawdown**      | -16.80% |

### Equity Curve vs Drawdown

![Equity Curve](equity_curve.png)
![Drawdown](drawdown.png)

---

## 2. How It Works

The notebook (`Strategy.ipynb`) walks through the entire research process from EDA to final strategy

### Signal Families

| Family                       | Variants                  | Description                                          |
| :--------------------------- | :------------------------ | :--------------------------------------------------- |
| **Momentum**           | 20D, 30D, 60D, 120D, 200D | Go long if N-day return is positive, short otherwise |
| **MA Crossover**       | 6 pairs                   | Go long when fast MA crosses above slow MA           |
| **DXY (Dollar Index)** | 3 pairs                   | Go long on oil when the dollar is weakening          |

### Strategy Parameters

| Parameter           | Value                       |
| :------------------ | :-------------------------- |
| Transaction Cost    | 1.5 bps per trade           |
| Volatility Target   | 15% annualized              |
| Stop Loss           | -3% cumulative trade return |
| Min Holding Period  | 10 days                     |
| Lookback Period     | 12 months                   |
| Rebalance Frequency | Quarterly                   |

---

## 4. Project Structure

| File                   | Description                                                           |
| :--------------------- | :-------------------------------------------------------------------- |
| `Strategy.ipynb`     | Main notebook: EDA, strategy construction, backtesting, and analysis. |
| `brent_index.xlsx`   | Brent Crude Oil front-month futures price data.                       |
| `dxy.csv`            | U.S. Dollar Index (DTWEXBGS) data from FRED.                          |
| `psw01.xls`          | EIA Weekly Petroleum Status Report (inventory data).                  |
| `Strategy_Report.md` | Detailed research report documenting methodology and findings.        |
| `requirements.txt`   | Python dependencies.                                                  |

---

## 5. Quick Start

### Set up the environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run the notebook

Open Strategy.ipynb in Jupyter or VS Code to reproduce the analysis.

---

## License

This project is for educational and research purposes.
