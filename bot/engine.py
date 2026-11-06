"""Exécution quotidienne (live paper trading)."""
from __future__ import annotations

import io
import logging
import traceback

import pandas as pd

from .config import HISTORY_PERIOD, INITIAL_CAPITAL, UNIVERSE
from .indicators import snapshot
from .llm import Gemini
from .market import Market
from .sentiment import analyze
from .store import Store
from .strategies import STRATEGIES, Context

log = logging.getLogger(__name__)


def run_daily(only: list[str] | None = None, skip_llm: bool = False) -> None:
    buf = io.StringIO()
    handler = logging.StreamHandler(buf)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logging.getLogger().addHandler(handler)

    store = Store()
    run_id = store.start_run()
    status = "success"
    try:
        log.info("Chargement des cours (%d actifs)…", len(UNIVERSE))
        market = Market.load(UNIVERSE, HISTORY_PERIOD)
        today = pd.Timestamp.now(tz="UTC").tz_localize(None).normalize()
        log.info("Dernière séance disponible : %s", market.last_date().date())

        store.save_market(market, {s: snapshot(market.close(s)) for s in market.symbols})

        strategies = [s for s in STRATEGIES if not only or s.id in only]
        llm = None if skip_llm else Gemini.from_env()
        sentiment = {}
        if llm and any(s.needs_llm for s in strategies):
            sentiment = analyze(llm, list(market.assets.values()))
            store.save_sentiment(today, sentiment)

        for strat in strategies:
            try:
                pf, state = store.load(strat, INITIAL_CAPITAL)
                filled = pf.fill_pending(market)
                for o in filled:
                    log.info("[%s] %s %s %.4f @ %s → %s", strat.id, o.side, o.symbol, o.quantity,
                             o.price_local, o.status)
                note = None
                if strat.needs_llm and llm is None:
                    log.info("[%s] ignorée (pas de Gemini)", strat.id)
                else:
                    ctx = Context(today, market, pf, sentiment, state, llm)
                    decision = strat.decide(ctx)
                    if decision is not None:
                        orders = pf.apply_targets(market, today, decision.weights, decision.reasons, decision.keep)
                        # Journal : seulement quand il se passe quelque chose (ou pour l'agent IA)
                        if decision.note and (orders or strat.needs_llm):
                            note = decision.note
                        log.info("[%s] %d ordre(s) programmé(s)", strat.id, len(orders))
                store.save(strat, pf, state, market, today, note)
                log.info("[%s] valeur %.2f EUR (cash %.2f)", strat.id, pf.equity(market), pf.cash_eur)
            except Exception:  # une stratégie en erreur ne bloque pas les autres
                status = "partial"
                log.error("[%s] erreur :\n%s", strat.id, traceback.format_exc())
    except Exception:
        status = "error"
        log.error("Run échoué :\n%s", traceback.format_exc())
        raise
    finally:
        store.finish_run(run_id, status, buf.getvalue())
        logging.getLogger().removeHandler(handler)
