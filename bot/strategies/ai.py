"""Stratégies utilisant Gemini."""
from __future__ import annotations

import json
import logging

from pydantic import BaseModel, Field

from ..indicators import sma, snapshot
from .base import Context, Decision, Strategy

log = logging.getLogger(__name__)


class SentimentTrend(Strategy):
    id = "sentiment"
    name = "Sentiment Gemini + tendance"
    description = ("Achète quand Gemini juge les actualités nettement positives (score ≥ 0,4) "
                   "et que le cours est au-dessus de sa MM50. Sort si le sentiment devient négatif "
                   "(≤ -0,2) ou si le cours casse la MM50 de plus de 3 %.")
    needs_llm = True
    weight = 0.12

    def decide(self, ctx: Context) -> Decision | None:
        if not ctx.sentiment:
            return None
        pf, weights, reasons, keep = ctx.portfolio, {}, {}, set()
        for s in pf.positions:
            sent = ctx.sentiment.get(s)
            c = ctx.market.close(s)
            m50 = sma(c, 50)
            if sent and sent.score <= -0.2:
                reasons[s] = f"Sentiment négatif ({sent.score:+.2f}) : {sent.summary}"
            elif m50 and c.iloc[-1] < m50 * 0.97:
                reasons[s] = "Cours sous la MM50 (-3 %)"
            else:
                keep.add(s)
        candidates = []
        for s, sent in ctx.sentiment.items():
            if s in pf.positions or sent.score < 0.4:
                continue
            c = ctx.market.close(s)
            m50 = sma(c, 50)
            if m50 and c.iloc[-1] > m50:
                candidates.append((sent.score, s))
        slots = int(0.96 / self.weight) - len(keep)
        for score, s in sorted(candidates, reverse=True)[: max(slots, 0)]:
            weights[s] = self.weight
            reasons[s] = f"Sentiment {score:+.2f} : {ctx.sentiment[s].summary}"
        if not weights and not (set(pf.positions) - keep):
            return None
        return Decision(weights, reasons, keep=keep)


class _Alloc(BaseModel):
    symbol: str
    weight: float = Field(description="Poids cible entre 0 et 0.25")
    reason: str = Field(description="Justification courte en français")


class _AgentOutput(BaseModel):
    allocations: list[_Alloc] = Field(description="Actifs à détenir. Les actifs absents seront vendus.")
    market_view: str = Field(description="Analyse globale du marché en 2-4 phrases, en français")


AGENT_SYSTEM = """Tu es un gérant de portefeuille swing (horizon de quelques jours à quelques semaines).
Tu gères un portefeuille fictif en EUR, sans levier ni vente à découvert.
Règles :
- Poids par actif entre 0 et 0.25, somme des poids <= 1 (le reste est du cash).
- Évite de trop trader : chaque transaction coûte ~0,15 %. Ne change une position que pour une vraie raison.
- Diversifie entre classes d'actifs et régions quand c'est pertinent.
- Appuie-toi sur les données fournies (tendance, momentum, RSI, volatilité, actualités), pas sur des suppositions.
- Tu peux rester majoritairement en cash si le contexte est défavorable."""


class GeminiAgent(Strategy):
    id = "gemini_agent"
    name = "Agent Gemini"
    description = ("Gemini reçoit chaque jour le portefeuille, les indicateurs techniques et l'analyse "
                   "des actualités, puis décide lui-même de l'allocation en justifiant ses choix.")
    needs_llm = True

    def decide(self, ctx: Context) -> Decision | None:
        if ctx.llm is None:
            return None
        m, pf = ctx.market, ctx.portfolio
        rows = []
        for s in m.symbols:
            snap = snapshot(m.close(s))
            a = m.assets[s]
            sent = ctx.sentiment.get(s)
            rows.append({
                "symbol": s, "name": a.name, "class": a.asset_class, "region": a.region,
                **{k: (round(v, 4) if isinstance(v, float) else v) for k, v in snap.items()
                   if k not in ("sma50", "sma200")},
                "news_score": round(sent.score, 2) if sent else None,
                "news": sent.summary if sent else None,
            })
        eq = pf.equity(m)
        holdings = [{"symbol": s, "weight": round(pf.position_value(m, s) / eq, 4),
                     "pnl": round((m.last_price_eur(s) or p.avg_cost_eur) / p.avg_cost_eur - 1, 4),
                     "since": p.opened_at.strftime("%Y-%m-%d")} for s, p in pf.positions.items()]
        prompt = (
            f"Date : {ctx.date:%Y-%m-%d}\n"
            f"Valeur du portefeuille : {eq:.2f} EUR, cash : {pf.cash_eur / eq:.1%}\n"
            f"Positions actuelles : {json.dumps(holdings, ensure_ascii=False)}\n"
            f"Note précédente : {ctx.state.get('last_view', 'aucune')}\n\n"
            "Données de marché (rendements en fraction, ret_1m = 1 mois, vol_60d annualisée) :\n"
            f"{json.dumps(rows, ensure_ascii=False)}\n\n"
            "Donne l'allocation cible complète."
        )
        try:
            out: _AgentOutput = ctx.llm.json(prompt, _AgentOutput, system=AGENT_SYSTEM)
        except Exception as e:  # noqa: BLE001
            log.error("Agent Gemini : %s", e)
            return None
        weights, reasons = {}, {}
        for al in out.allocations:
            if al.symbol in m.assets and al.weight > 0:
                weights[al.symbol] = min(float(al.weight), 0.25)
                reasons[al.symbol] = al.reason
        for s in pf.positions:
            reasons.setdefault(s, "Retiré de l'allocation par l'agent")
        ctx.state["last_view"] = out.market_view
        return Decision(weights, reasons, note=out.market_view)
