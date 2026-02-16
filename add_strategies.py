"""Script to add Bollinger Band, RSI, and Breakout strategies to the notebook."""
import json

notebook_path = r"C:\Users\Acer\Downloads\cand_proj\Sample Strategy.ipynb"

with open(notebook_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

# Find the cell containing the strategy code
for cell in nb["cells"]:
    if cell["cell_type"] == "code":
        source_text = "".join(cell["source"])
        if "ma_crossover" in source_text and "Run Walkforward Backtest" in source_text:
            lines = cell["source"]
            new_source = []
            i = 0
            while i < len(lines):
                # Insert new strategies before "# Run Walkforward Backtest"
                if "# Run Walkforward Backtest" in lines[i]:
                    # Remove separator line we're about to re-add
                    if new_source and "# ------" in new_source[-1]:
                        new_source.pop()

                    new_strategies = [
                        "# -------------------------------\n",
                        "# Bollinger Band Reversion Strategies\n",
                        "# -------------------------------\n",
                        "bb_windows = [20, 50]\n",
                        "for w in bb_windows:\n",
                        "    mid = df['CO1 Comdty'].rolling(window=w).mean()\n",
                        "    std = df['CO1 Comdty'].rolling(window=w).std()\n",
                        "    upper = mid + 2 * std\n",
                        "    lower = mid - 2 * std\n",
                        "    price = df['CO1 Comdty']\n",
                        "    # Long when price below lower band, short when above upper, else flat->use previous\n",
                        "    bb_signal = pd.Series(np.where(price.shift(1) < lower.shift(1), 1,\n",
                        "                         np.where(price.shift(1) > upper.shift(1), -1, np.nan)), index=rets.index)\n",
                        "    bb_signal = bb_signal.ffill().fillna(0)\n",
                        "    pnl_strategies[f'{w}D_bollinger'] = bb_signal * rets - tcost * abs(bb_signal.diff())\n",
                        "\n",
                        "# -------------------------------\n",
                        "# RSI Strategies\n",
                        "# -------------------------------\n",
                        "rsi_windows = [14, 28]\n",
                        "for w in rsi_windows:\n",
                        "    delta = df['CO1 Comdty'].diff()\n",
                        "    gain = delta.where(delta > 0, 0).rolling(window=w).mean()\n",
                        "    loss = (-delta.where(delta < 0, 0)).rolling(window=w).mean()\n",
                        "    rs = gain / loss\n",
                        "    rsi = 100 - (100 / (1 + rs))\n",
                        "    # Long when RSI < 30 (oversold), short when RSI > 70 (overbought)\n",
                        "    rsi_signal = pd.Series(np.where(rsi.shift(1) < 30, 1,\n",
                        "                          np.where(rsi.shift(1) > 70, -1, np.nan)), index=rets.index)\n",
                        "    rsi_signal = rsi_signal.ffill().fillna(0)\n",
                        "    pnl_strategies[f'{w}D_rsi'] = rsi_signal * rets - tcost * abs(rsi_signal.diff())\n",
                        "\n",
                        "# -------------------------------\n",
                        "# Donchian Breakout Strategies\n",
                        "# -------------------------------\n",
                        "breakout_windows = [20, 55]\n",
                        "for w in breakout_windows:\n",
                        "    high_w = df['CO1 Comdty'].rolling(window=w).max()\n",
                        "    low_w = df['CO1 Comdty'].rolling(window=w).min()\n",
                        "    price = df['CO1 Comdty']\n",
                        "    # Long on new high, short on new low\n",
                        "    brk_signal = pd.Series(np.where(price.shift(1) >= high_w.shift(2), 1,\n",
                        "                          np.where(price.shift(1) <= low_w.shift(2), -1, np.nan)), index=rets.index)\n",
                        "    brk_signal = brk_signal.ffill().fillna(0)\n",
                        "    pnl_strategies[f'{w}D_breakout'] = brk_signal * rets - tcost * abs(brk_signal.diff())\n",
                        "\n",
                        "# -------------------------------\n",
                        "# Run Walkforward Backtest\n",
                    ]
                    new_source.extend(new_strategies)
                else:
                    new_source.append(lines[i])
                i += 1

            cell["source"] = new_source
            print("Successfully added Bollinger, RSI, and Breakout strategies!")
            break

with open(notebook_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1)

print("Notebook saved.")
