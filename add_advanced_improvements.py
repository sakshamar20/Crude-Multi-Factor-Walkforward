"""
Script to implement three major improvements:
1. Volatility Scaling (Risk Parity) - position sizing based on recent vol
2. Top-N Strategy Ensembling - pick top 3 strategies instead of single winner
3. Regime Filter - allow momentum only in trending, mean reversion only in sideways
"""
import json

notebook_path = r"C:\Users\Acer\Downloads\cand_proj\Sample Strategy.ipynb"

with open(notebook_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

# =====================================================
# 1. MODIFY THE BACKTESTER CLASS for Top-N Ensembling
# =====================================================
new_backtester_source = [
    "from dataclasses import dataclass, field\n",
    "from typing import Callable, List, Dict\n",
    "\n",
    "import numpy as np\n",
    "import pandas as pd\n",
    "from dateutil.relativedelta import relativedelta\n",
    "pd.options.plotting.backend = 'plotly'\n",
    "\n",
    "\n",
    "@dataclass\n",
    "class WalkforwardBacktester:\n",
    '    """\n',
    "    A Walkforward Backtester with Top-N strategy ensembling.\n",
    "    Instead of picking a single winner, selects the top_n strategies\n",
    "    and averages their returns for diversification.\n",
    "\n",
    "    Attributes\n",
    "    ----------\n",
    "    pnl_df : pd.DataFrame\n",
    "        DataFrame of PnL/returns for multiple strategies.\n",
    "    lookback_period : str\n",
    "        Lookback period for evaluating strategy performance (e.g., '24ME').\n",
    "    rebalance_freq : str\n",
    "        Frequency of rebalance (e.g., '3ME').\n",
    "    top_n : int\n",
    "        Number of top strategies to ensemble (default=3).\n",
    "    score_func : Callable\n",
    "        Function to score each strategy. Defaults to Sharpe ratio.\n",
    '    """\n',
    "\n",
    "    pnl_df: pd.DataFrame\n",
    "    lookback_period: str\n",
    "    rebalance_freq: str\n",
    "    top_n: int = 3\n",
    "    score_func: Callable[[pd.Series], float] = field(default=None)\n",
    "    periods: List = None\n",
    "    lookback_start_skip_check: bool = False\n",
    "    rebalances: List[Dict[str, any]] = field(default_factory=list)\n",
    "\n",
    "    def __post_init__(self):\n",
    "        self.score_func = self.score_func or self._sharpe_ratio\n",
    "        self.portfolio_pnl = pd.Series(index=self.pnl_df.index, dtype=np.float64)\n",
    "\n",
    "    def _sharpe_ratio(self, returns: pd.Series) -> float:\n",
    "        return returns.mean() / returns.std() if returns.std() != 0 else 0\n",
    "\n",
    "    def _select_top_n_strategies(self, lookback_df: pd.DataFrame):\n",
    '        """Select the top_n strategies by score and return their names + scores."""\n',
    "        strategy_scores = lookback_df.apply(self.score_func)\n",
    "        top_strategies = strategy_scores.nlargest(self.top_n).index.tolist()\n",
    "        return top_strategies, strategy_scores\n",
    "\n",
    "    def run_backtest(self) -> pd.Series:\n",
    '        """\n',
    "        Run the walkforward backtest. At each rebalance, select the top_n strategies\n",
    "        and average their returns for the forward period.\n",
    '        """\n',
    '        freq_letter = self.rebalance_freq[-1] if self.rebalance_freq[-1] != "E" else self.rebalance_freq[-2]\n',
    '        assert freq_letter == "M", "rebalance freq must be in months"\n',
    "\n",
    "        self.periods = pd.date_range(\n",
    "            start=self.pnl_df.index[0],\n",
    "            end=self.pnl_df.index[-1] + relativedelta(months=int(self.rebalance_freq.replace('ME','').replace('M',''))),\n",
    "            freq=self.rebalance_freq\n",
    "        )\n",
    "\n",
    "        for start_date, end_date in zip(self.periods[:-1], self.periods[1:]):\n",
    "            lookback_end = start_date - pd.Timedelta(days=1)\n",
    "            lookback_start = lookback_end - relativedelta(months=int(self.lookback_period.replace('ME','').replace('M','')))\n",
    "\n",
    "            if (lookback_start < self.pnl_df.index[0]) and (not self.lookback_start_skip_check):\n",
    "                continue\n",
    "\n",
    "            lookback_df = self.pnl_df.loc[lookback_start:lookback_end]\n",
    "            top_strats, strategy_scores = self._select_top_n_strategies(lookback_df)\n",
    "\n",
    "            # Average the returns of the top_n strategies (equal weight ensemble)\n",
    "            ensemble_returns = self.pnl_df[top_strats].loc[start_date:end_date].mean(axis=1)\n",
    "\n",
    "            self.rebalances.append({\n",
    "                'start_date': start_date,\n",
    "                'end_date': end_date,\n",
    "                'lookback_start': lookback_start,\n",
    "                'lookback_end': lookback_end,\n",
    "                'top_strategies': top_strats,\n",
    "                'strategy_scores': strategy_scores,\n",
    "                'lookback_df': lookback_df,\n",
    "                'ensemble_mean_returns': ensemble_returns.mean(),\n",
    "                'ensemble_std': ensemble_returns.std()\n",
    "            })\n",
    "\n",
    "            self.portfolio_pnl.loc[start_date:end_date] = ensemble_returns\n",
    "\n",
    "        return self.portfolio_pnl\n",
    "\n",
    "    def get_rebalance_details(self) -> pd.DataFrame:\n",
    "        return pd.DataFrame(self.rebalances)\n",
    "\n",
    "\n",
]

# =====================================================
# 2. FIND AND REPLACE THE BACKTESTER CELL
# =====================================================
for cell in nb["cells"]:
    if cell["cell_type"] == "code":
        src = "".join(cell["source"])
        if "class WalkforwardBacktester" in src:
            cell["source"] = new_backtester_source
            print("Updated WalkforwardBacktester with Top-N ensembling!")
            break

# =====================================================
# 3. ADD VOLATILITY SCALING + REGIME FILTER to strategy cell
# =====================================================
for cell in nb["cells"]:
    if cell["cell_type"] == "code":
        src = "".join(cell["source"])
        if "apply_holding_period" in src and "Run Walkforward Backtest" in src:
            lines = cell["source"]
            new_source = []

            for line in lines:
                # Insert volatility scaling after tcost line
                if "tcost = 0.00015" in line:
                    new_source.append(line)
                    vol_scaling_code = [
                        "\n",
                        "# -------------------------------\n",
                        "# Volatility Scaling (Risk Parity)\n",
                        "# -------------------------------\n",
                        "target_annual_vol = 0.15  # Target 15% annualized volatility\n",
                        "rolling_vol = rets.rolling(20).std() * np.sqrt(252)  # 20-day annualized vol\n",
                        "vol_scalar = (target_annual_vol / rolling_vol).clip(0.25, 3.0)  # Cap between 0.25x and 3x\n",
                        "\n",
                        "# -------------------------------\n",
                        "# Regime Detection (200-day SMA)\n",
                        "# -------------------------------\n",
                        "sma_200 = df['CO1 Comdty'].rolling(200).mean()\n",
                        "trending = df['CO1 Comdty'] > sma_200       # Price above 200 SMA = trending up\n",
                        "sideways = ~trending                         # Price below 200 SMA = sideways/down\n",
                    ]
                    new_source.extend(vol_scaling_code)
                    continue

                # Apply vol scaling to momentum PnL line
                if 'pnl_strategies[f"{m}D_momentum"]' in line:
                    new_source.append("    # Apply regime filter: momentum only allowed in trending markets\n")
                    new_source.append("    momentum_signal = momentum_signal.where(trending.shift(1), 0)\n")
                    new_source.append("    # Apply volatility scaling\n")
                    new_source.append('    pnl_strategies[f"{m}D_momentum"] = (momentum_signal * vol_scalar) * rets - tcost * abs(momentum_signal.diff()) \n')
                    continue

                # Apply vol scaling to mean reversion PnL line
                if 'pnl_strategies[f"{m}D_meanrev"]' in line:
                    new_source.append("    # Apply regime filter: mean reversion only in sideways markets\n")
                    new_source.append("    meanrev_signal = meanrev_signal.where(sideways.shift(1), 0)\n")
                    new_source.append("    # Apply volatility scaling\n")
                    new_source.append('    pnl_strategies[f"{m}D_meanrev"] = (meanrev_signal * vol_scalar) * rets - tcost * abs(meanrev_signal.diff())\n')
                    continue

                # Apply vol scaling to MA crossover
                if 'pnl_strategies[f"{short_w}_{long_w}_ma_crossover"]' in line:
                    new_source.append('    pnl_strategies[f"{short_w}_{long_w}_ma_crossover"] = (ma_signal * vol_scalar) * rets - tcost * abs(ma_signal.diff())\n')
                    continue

                # Apply vol scaling to Bollinger
                if "pnl_strategies[f'{w}D_bollinger']" in line:
                    new_source.append("    pnl_strategies[f'{w}D_bollinger'] = (bb_signal * vol_scalar) * rets - tcost * abs(bb_signal.diff())\n")
                    continue

                # Apply vol scaling to RSI
                if "pnl_strategies[f'{w}D_rsi']" in line:
                    new_source.append("    pnl_strategies[f'{w}D_rsi'] = (rsi_signal * vol_scalar) * rets - tcost * abs(rsi_signal.diff())\n")
                    continue

                # Apply vol scaling to breakout
                if "pnl_strategies[f'{w}D_breakout']" in line:
                    new_source.append("    pnl_strategies[f'{w}D_breakout'] = (brk_signal * vol_scalar) * rets - tcost * abs(brk_signal.diff())\n")
                    continue

                # Update backtester instantiation to include top_n
                if "backtester = WalkforwardBacktester(" in line:
                    new_source.append("backtester = WalkforwardBacktester(\n")
                    continue
                if "    lookback_period='24M'," in line:
                    new_source.append("    lookback_period='24M',\n")
                    continue
                if "    rebalance_freq='3M'" in line:
                    new_source.append("    rebalance_freq='3M',\n")
                    new_source.append("    top_n=3  # Ensemble top 3 strategies\n")
                    continue

                new_source.append(line)

            cell["source"] = new_source
            print("Added volatility scaling + regime filter to strategies!")
            break

# =====================================================
# 4. UPDATE rebalance_details display cell
# =====================================================
for cell in nb["cells"]:
    if cell["cell_type"] == "code":
        src = "".join(cell["source"]).strip()
        if src == "rebalance_details":
            cell["source"] = [
                "# Show rebalance details with top strategies selected\n",
                "rebalance_details\n",
            ]
            print("Updated rebalance_details cell!")
            break

with open(notebook_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1)

print("All three improvements saved to notebook!")
