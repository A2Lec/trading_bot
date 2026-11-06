"""Point d'entrée : python -m bot run | backtest"""
from __future__ import annotations

import argparse
import logging

import pandas as pd


def main() -> None:
    p = argparse.ArgumentParser(prog="bot", description="Paper trading bot multi-stratégies")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="Exécution quotidienne (live paper trading)")
    r.add_argument("--only", nargs="*", help="Limiter à certaines stratégies (ids)")
    r.add_argument("--no-llm", action="store_true", help="Ne pas appeler Gemini")

    b = sub.add_parser("backtest", help="Backtest des stratégies techniques")
    b.add_argument("--period", default="5y", help="Historique yfinance : 2y, 5y, 10y, max…")
    b.add_argument("--only", nargs="*")
    b.add_argument("--csv", action="store_true", help="Exporter les courbes de valeur en CSV")

    sub.add_parser("list", help="Lister les stratégies")

    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logging.getLogger("yfinance").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    if args.cmd == "run":
        from .engine import run_daily
        run_daily(args.only, skip_llm=args.no_llm)
    elif args.cmd == "backtest":
        from .backtest import run_backtest
        with pd.option_context("display.width", 200, "display.max_columns", 20):
            print(run_backtest(args.period, only=args.only, csv=args.csv))
    elif args.cmd == "list":
        from .strategies import STRATEGIES
        for s in STRATEGIES:
            print(f"{s.id:16} {s.name:30} {'(Gemini)' if s.needs_llm else ''}\n  {s.description}")


if __name__ == "__main__":
    main()
