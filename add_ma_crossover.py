"""Script to add Moving Average Crossover strategy to the Sample Strategy notebook."""
import json

notebook_path = r"C:\Users\Acer\Downloads\cand_proj\Sample Strategy.ipynb"

with open(notebook_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

# Find the cell containing the strategy code (the one with 'lookback_days')
for cell in nb["cells"]:
    if cell["cell_type"] == "code":
        source_text = "".join(cell["source"])
        if "lookback_days" in source_text and "pnl_strategies" in source_text:
            # Find the line index after the mean reversion block (after the for loop)
            new_source = []
            i = 0
            lines = cell["source"]
            while i < len(lines):
                new_source.append(lines[i])
                # Insert MA crossover code after the for loop ends (after the empty line following meanrev)
                if "# Run Walkforward Backtest" in lines[i]:
                    # Insert the MA crossover code BEFORE the Run Walkforward Backtest comment
                    # Remove the last added line (the comment) and the separator before it
                    new_source.pop()  # remove "# Run Walkforward Backtest"
                    # Check if previous line is the separator
                    if new_source and "# ------" in new_source[-1]:
                        new_source.pop()  # remove separator line
                    
                    ma_crossover_code = [
                        "# -------------------------------\n",
                        "# Moving Average Crossover Strategies\n",
                        "# -------------------------------\n",
                        "ma_pairs = [(5, 20), (10, 50), (20, 100), (50, 200)]  # (short_window, long_window)\n",
                        "for short_w, long_w in ma_pairs:\n",
                        "    short_ma = df['CO1 Comdty'].rolling(window=short_w).mean()\n",
                        "    long_ma = df['CO1 Comdty'].rolling(window=long_w).mean()\n",
                        "    # Go long when short MA > long MA, else short\n",
                        "    ma_signal = pd.Series(np.where(short_ma.shift(1) > long_ma.shift(1), 1, -1), index=rets.index)\n",
                        "    pnl_strategies[f\"{short_w}_{long_w}_ma_crossover\"] = ma_signal * rets - tcost * abs(ma_signal.diff())\n",
                        "\n",
                        "# -------------------------------\n",
                        "# Run Walkforward Backtest\n",
                    ]
                    new_source.extend(ma_crossover_code)
                i += 1
            
            cell["source"] = new_source
            print("Successfully added MA crossover strategy!")
            break

with open(notebook_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1)

print("Notebook saved.")
