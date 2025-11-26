from colorama import Fore, Style, init

from mes_levels import get_snapshot

# Initialize colorama (for colored terminal output)
init(autoreset=True)


# =========================
#  HELPER FUNCTIONS
# =========================

def print_header() -> None:
    """Print the script header."""
    print(Fore.CYAN + Style.BRIGHT + "\n==============================")
    print("  ES LIVE LEVEL HELPER")
    print("==============================\n" + Style.RESET_ALL)


def print_levels(levels) -> None:
    """Display the computed levels."""
    print(Fore.WHITE + Style.BRIGHT + "=== CORE LEVELS ===" + Style.RESET_ALL)
    print(f"Breakout trigger:     {levels['breakout']:.1f}")
    print(f"Breakdown line:       {levels['breakdown']:.1f}")
    print(f"Dip-buy zone:         {levels['dip_low']:.1f} – {levels['dip_high']:.1f}")
    print(
        f"Supply / fade zone:   {levels['supply_low']:.1f} – {levels['supply_high']:.1f}\n"
    )


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
    """Execute the ES level calculation workflow."""
    print_header()
    snap = get_snapshot()

    if "error" in snap:
        print(Fore.RED + f"Error: {snap['error']}" + Style.RESET_ALL)
        return

    print(f"Last candle: {snap['last_time']}  |  Close: {snap['last_close']:.2f}")
    print(f"ATR(14): {snap['atr']:.2f}\n")

    print_levels(snap["levels"])
    print_bias_section(snap["bias"], snap["action"])

    print(
        Fore.CYAN + "Reminder:" + Style.RESET_ALL,
        "Use only 15–30m candle closes at your levels. No chasing. Let the market come to you.\n",
    )


if __name__ == "__main__":
    main()
