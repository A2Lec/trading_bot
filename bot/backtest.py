"""Backtest des stratégies techniques sur l'historique, avec le même code qu'en live."""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from .config import INITIAL_CAPITAL, UNIVERSE
from .market import Market
from .portfolio import Portfolio
from .strategies import STRATEGIES, Context

log = logging.getLogger(__name__)


def metrics(equity: pd.Series, n_trades: int) -> dict:
    r = equity.pct_change().dropna()
    years = max((equity.index[-1] - equity.index[0]).days / 365.25, 1e-9)
    dd = equity / equity.cummax() - 1
    return {
        "final_eur": round(float(equity.iloc[-1]), 2),
        "total_return": f"{equity.iloc[-1] / equity.iloc[0] - 1:+.1%}",
        "cagr": f"{(equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1:+.1%}",
        "max_drawdown": f"{dd.min():.1%}",
        "sharpe": round(float(r.mean() / r.std() * np.sqrt(252)), 2) if r.std() > 0 else 0.0,
        "trades": n_trades,
    }


def run_backtest(period: str = "5y", warmup: int = 210, only: list[str] | None = None,
                 csv: bool = False) -> pd.DataFrame:
    market = Market.load(UNIVERSE, period, auto_adjust=True)
    cal = market.calendar()
    cal = cal[cal.day_of_week < 5]  # une décision par jour ouvré
    dates = cal[warmup:]
    strategies = [s for s in STRATEGIES if not s.needs_llm and (not only or s.id in only)]
    skipped = [s.id for s in STRATEGIES if s.needs_llm]
    if skipped:
        log.info("Stratégies Gemini non backtestables (pas d'historique de news) : %s", ", ".join(skipped))

    results, curves = {}, {}
    for strat in strategies:
        pf, state, eq, trades = Portfolio(strat.id, INITIAL_CAPITAL), {}, {}, 0
        for d in dates:
            view = market.view(d)
            trades += sum(o.status == "filled" for o in pf.fill_pending(view))
            dec = strat.decide(Context(d, view, pf, {}, state, None, backtest=True))
            if dec is not None:
                pf.apply_targets(view, d, dec.weights, dec.reasons, dec.keep)
            pf.history.clear()
            eq[d] = pf.equity(view)
        curve = pd.Series(eq)
        curves[strat.id] = curve
        results[strat.id] = {"name": strat.name, **metrics(curve, trades)}
        log.info("%s terminé", strat.id)
    df = pd.DataFrame(results).T
    if csv:
        pd.DataFrame(curves).to_csv(f"backtest_{period}.csv")
    return df
