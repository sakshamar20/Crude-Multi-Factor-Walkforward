"""
Script to add stop-loss / take-profit logic to the strategy notebook.
- Stop loss: exit position when cumulative loss from entry reaches -2%
- Take profit: exit position when cumulative gain from entry reaches +4%
- After exit, go flat (0) until the next signal change triggers a new entry
"""
import json

notebook_path = r"C:\Users\Acer\Downloads\cand_proj\Sample Strategy.ipynb"

with open(notebook_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

# The stop-loss/take-profit function to inject
sl_tp_function = [
    "def apply_stop_loss_take_profit(signal, prices, stop_loss=-0.02, take_profit=0.04):\n",
    '    """Apply stop-loss and take-profit rules to a signal.\n',
    "    When a position is entered, track cumulative return from entry price.\n",
    "    Exit (go flat) if return hits stop_loss or take_profit.\n",
    "    Stay flat until signal changes direction for a new entry.\n",
    "    \n",
    "    Parameters:\n",
    "        signal: pd.Series of positions (+1, -1, or 0)\n",
    "        prices: pd.Series of asset prices (same index as signal)\n",
    "        stop_loss: exit threshold for losses (e.g., -0.02 = -2%)\n",
    "        take_profit: exit threshold for gains (e.g., 0.04 = +4%)\n",
    '    """\n',
    "    filtered = signal.copy().astype(float)\n",
    "    entry_price = None\n",
    "    current_pos = 0\n",
    "    stopped_out = False  # True when SL/TP triggered, waiting for new signal\n",
    "    \n",
    "    for i in range(len(filtered)):\n",
    "        raw_signal = filtered.iloc[i]\n",
    "        price = prices.iloc[i]\n",
    "        \n",
    "        if pd.isna(price) or pd.isna(raw_signal):\n",
    "            filtered.iloc[i] = current_pos\n",
    "            continue\n",
    "        \n",
    "        # If we're stopped out, stay flat until signal changes\n",
    "        if stopped_out:\n",
    "            if raw_signal != current_pos and raw_signal != 0:\n",
    "                # New signal direction -> re-enter\n",
    "                current_pos = raw_signal\n",
    "                entry_price = price\n",
    "                stopped_out = False\n",
    "            else:\n",
    "                filtered.iloc[i] = 0\n",
    "                continue\n",
    "        \n",
    "        # Check if entering a new position\n",
    "        if current_pos == 0 and raw_signal != 0:\n",
    "            current_pos = raw_signal\n",
    "            entry_price = price\n",
    "            filtered.iloc[i] = current_pos\n",
    "            continue\n",
    "        \n",
    "        # If in a position, check SL/TP\n",
    "        if current_pos != 0 and entry_price is not None and entry_price != 0:\n",
    "            pnl_pct = current_pos * (price - entry_price) / entry_price\n",
    "            \n",
    "            if pnl_pct <= stop_loss:  # Stop loss hit\n",
    "                filtered.iloc[i] = 0\n",
    "                current_pos = 0\n",
    "                entry_price = None\n",
    "                stopped_out = True\n",
    "                continue\n",
    "            elif pnl_pct >= take_profit:  # Take profit hit\n",
    "                filtered.iloc[i] = 0\n",
    "                current_pos = 0\n",
    "                entry_price = None\n",
    "                stopped_out = True\n",
    "                continue\n",
    "        \n",
    "        # Check for signal direction change (new entry)\n",
    "        if raw_signal != current_pos and raw_signal != 0:\n",
    "            current_pos = raw_signal\n",
    "            entry_price = price\n",
    "        \n",
    "        filtered.iloc[i] = current_pos\n",
    "    \n",
    "    return filtered\n",
    "\n",
    "stop_loss = -0.02   # -2% stop loss\n",
    "take_profit = 0.04  # +4% take profit\n",
    "\n",
]

# Find the strategy cell and inject the SL/TP function + apply it to each strategy
for cell in nb["cells"]:
    if cell["cell_type"] == "code":
        source_text = "".join(cell["source"])
        if "apply_holding_period" in source_text and "Run Walkforward Backtest" in source_text:
            lines = cell["source"]
            new_source = []
            
            # Track whether we've inserted the SL/TP function
            sl_tp_inserted = False
            
            for line in lines:
                # Insert SL/TP function right after the holding period's min_hold line
                if "min_hold = 5" in line and not sl_tp_inserted:
                    new_source.append(line)
                    new_source.append("\n")
                    new_source.extend(sl_tp_function)
                    sl_tp_inserted = True
                    continue
                
                # After each apply_holding_period call, add SL/TP call
                if "= apply_holding_period(" in line:
                    new_source.append(line)
                    # Extract the variable name (e.g., "momentum_signal", "ma_signal", etc.)
                    var_name = line.strip().split("=")[0].strip()
                    indent = line[:len(line) - len(line.lstrip())]
                    new_source.append(f"{indent}{var_name} = apply_stop_loss_take_profit({var_name}, df['CO1 Comdty'], stop_loss, take_profit)\n")
                    continue
                
                new_source.append(line)
            
            cell["source"] = new_source
            print("Successfully added stop-loss/take-profit logic!")
            break

with open(notebook_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1)

print("Notebook saved.")
