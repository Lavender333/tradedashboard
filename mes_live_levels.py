from colorama import Fore, Style, init

from mes_levels import (
    RESOLUTION,
    compute_atr,
    compute_levels,
    determine_bias,
    fetch_candles,
    get_client,
)

# Initialize colorama (for colored terminal output)
init(autoreset=True)


# =========================
#  HELPER FUNCTIONS
# =========================

def print_header() -> None:
    """Print the script header."""
    print(Fore.CYAN + Style.BRIGHT + "\n==============================")
    print("  MES LIVE LEVEL HELPER")
    print("==============================\n" + Style.RESET_ALL)


def print_levels(levels) -> None:
    """Display the computed levels."""
    print(Fore.WHITE + Style.BRIGHT + "=== CORE LEVELS ===" + Style.RESET_ALL)
    print(f"Breakout trigger:     {levels.breakout:.1f}")
    print(f"Breakdown line:       {levels.breakdown:.1f}")
    print(f"Dip-buy zone:         {levels.dip_zone[0]:.1f} – {levels.dip_zone[1]:.1f}")
    print(f"Supply / fade zone:   {levels.supply_zone[0]:.1f} – {levels.supply_zone[1]:.1f}\n")


def print_bias_section(bias: str, action: str) -> None:
    """Display the directional bias and next action guidance."""
    if bias.startswith("LONG"):
        color = Fore.GREEN + Style.BRIGHT
    elif bias.startswith("SHORT"):
        color = Fore.MAGENTA + Style.BRIGHT   # PURPLE instead of RED
    else:
        color = Fore.YELLOW + Style.BRIGHT

    print(color + "=== BIAS ===" + Style.RESET_ALL)
    print(color + f"Bias: {bias}" + Style.RESET_ALL)
    print("Next action:")
    print(action + "\n")


# =========================
#  MAIN
# =========================

def main() -> None:
    """Execute the MES level calculation workflow."""
    print_header()
    client = get_client()
    df = fetch_candles(client)

    if len(df) < 20:
        raise RuntimeError("Not enough candle data to compute ATR/levels.")

    atr = compute_atr(df)
    last_close = float(df.iloc[-1]["close"])
    last_time = df.iloc[-1]["time"]

    levels = compute_levels(df, atr)
    bias, action = determine_bias(last_close, levels, atr)

    print(f"Last candle: {last_time}  |  Close: {last_close:.1f}")
    print(f"ATR(14, {RESOLUTION}m): {atr:.2f}\n")

    print_levels(levels)
    print_bias_section(bias, action)

    print(
        Fore.CYAN + "Reminder:" + Style.RESET_ALL,
        "Use only 15–30m candle closes at your levels. No chasing. Let the market come to you.\n",
    )


if __name__ == "__main__":
    main()
