"""Script to add a performance summary cell to the Sample Strategy notebook."""
import json

notebook_path = r"C:\Users\Acer\Downloads\cand_proj\Sample Strategy.ipynb"

with open(notebook_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

perf_cell = {
    "cell_type": "code",
    "execution_count": None,
    "id": "perf-summary-001",
    "metadata": {},
    "outputs": [],
    "source": [
        "# -------------------------------\n",
        "# Overall Strategy Performance Summary\n",
        "# -------------------------------\n",
        "import warnings\n",
        "warnings.filterwarnings('ignore')\n",
        "\n",
        "pnl = portfolio_pnl.dropna()\n",
        "trading_days = 252\n",
        "\n",
        "# Core metrics\n",
        "total_return = (1 + pnl).prod() - 1\n",
        "ann_return = (1 + total_return) ** (trading_days / len(pnl)) - 1\n",
        "ann_vol = pnl.std() * np.sqrt(trading_days)\n",
        "sharpe = ann_return / ann_vol if ann_vol != 0 else 0\n",
        "\n",
        "# Max Drawdown\n",
        "cum = (1 + pnl).cumprod()\n",
        "peak = cum.cummax()\n",
        "drawdown = (cum - peak) / peak\n",
        "max_dd = drawdown.min()\n",
        "\n",
        "# Calmar Ratio (ann return / max drawdown)\n",
        "calmar = ann_return / abs(max_dd) if max_dd != 0 else 0\n",
        "\n",
        "# Win rate\n",
        "win_rate = (pnl > 0).sum() / len(pnl)\n",
        "\n",
        "# Profit Factor\n",
        "gross_profit = pnl[pnl > 0].sum()\n",
        "gross_loss = abs(pnl[pnl < 0].sum())\n",
        "profit_factor = gross_profit / gross_loss if gross_loss != 0 else float('inf')\n",
        "\n",
        "print('=' * 50)\n",
        "print('  WALKFORWARD STRATEGY - PERFORMANCE SUMMARY')\n",
        "print('=' * 50)\n",
        "print(f'  Total Return:        {total_return:>10.2%}')\n",
        "print(f'  Annualized Return:   {ann_return:>10.2%}')\n",
        "print(f'  Annualized Volatility:{ann_vol:>9.2%}')\n",
        "print(f'  Sharpe Ratio:        {sharpe:>10.2f}')\n",
        "print(f'  Max Drawdown:        {max_dd:>10.2%}')\n",
        "print(f'  Calmar Ratio:        {calmar:>10.2f}')\n",
        "print(f'  Win Rate:            {win_rate:>10.2%}')\n",
        "print(f'  Profit Factor:       {profit_factor:>10.2f}')\n",
        "print('=' * 50)\n",
        "print(f'\\n  >>> OVERALL SHARPE RATIO: {sharpe:.2f} <<<')\n",
        "print(f'      (The single best measure of risk-adjusted performance)')\n",
    ]
}

# Insert the performance cell before the last empty cell
# Find the cell that has 'rebalance_details' and insert after it
inserted = False
for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] == "code" and "rebalance_details" in "".join(cell.get("source", [])):
        # Check if this is the standalone "rebalance_details" display cell
        src = "".join(cell["source"]).strip()
        if src == "rebalance_details":
            nb["cells"].insert(i + 1, perf_cell)
            inserted = True
            print(f"Inserted performance summary cell after cell index {i}")
            break

if not inserted:
    # Insert before the last cell
    nb["cells"].insert(-1, perf_cell)
    print("Inserted performance summary cell before last cell")

with open(notebook_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1)

print("Notebook saved successfully.")
