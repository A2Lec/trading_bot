"""Stratégies basées uniquement sur les cours."""
from __future__ import annotations

from ..config import BENCHMARK
from ..indicators import rsi, sma, volatility, ret
from .base import Context, Decision, Strategy


class BuyAndHold(Strategy):
    id = "buy_hold"
    name = "Benchmark MSCI World"
    description = f"Achète {BENCHMARK} une fois et le garde. C'est la référence à battre."

    def decide(self, ctx: Context) -> Decision | None:
        if BENCHMARK in ctx.portfolio.positions or BENCHMARK not in ctx.market.assets:
            return None
        return Decision({BENCHMARK: 0.99}, {BENCHMARK: "Investissement initial du benchmark"})


class TrendFollowing(Strategy):
    id = "trend"
    name = "Suivi de tendance"
    description = ("Détient les actifs dont la MM50 est au-dessus de la MM200 et le cours au-dessus "
                   "de la MM200. Poids égaux, 15 % max par ligne.")
    max_weight = 0.15

    def decide(self, ctx: Context) -> Decision | None:
        signals, reasons = [], {}
        for s in ctx.market.symbols:
            c = ctx.market.close(s)
            s50, s200 = sma(c, 50), sma(c, 200)
            if s50 is None or s200 is None:
                continue
            last = float(c.iloc[-1])
            if s50 > s200 and last > s200:
                signals.append(s)
                reasons[s] = f"Tendance haussière : MM50 {s50:.2f} > MM200 {s200:.2f}, cours {last:.2f}"
            elif s in ctx.portfolio.positions:
                reasons[s] = f"Fin de tendance : MM50 {s50:.2f} / MM200 {s200:.2f}, cours {last:.2f}"
        if not signals:
            return Decision({}, reasons, note="Aucun actif en tendance haussière : 100 % cash")
        w = min(0.98 / len(signals), self.max_weight)
        return Decision({s: w for s in signals}, reasons, note=f"{len(signals)} actifs en tendance")


class Momentum(Strategy):
    id = "momentum"
    name = "Momentum mensuel"
    description = ("Chaque mois, choisit les 5 actifs au meilleur rendement 6 mois ajusté du risque "
                   "(au-dessus de leur MM200), à poids égaux.")
    top_n = 5

    def decide(self, ctx: Context) -> Decision | None:
        month = ctx.date.strftime("%Y-%m")
        if ctx.state.get("last_rebalance") == month:
            return None
        scores = {}
        for s in ctx.market.symbols:
            c = ctx.market.close(s)
            r6, vol, s200 = ret(c, 126), volatility(c, 126), sma(c, 200)
            if r6 is None or not vol or s200 is None or r6 <= 0 or c.iloc[-1] < s200:
                continue
            scores[s] = (r6 / vol, r6)
        ctx.state["last_rebalance"] = month
        top = sorted(scores, key=lambda s: scores[s][0], reverse=True)[: self.top_n]
        reasons = {s: f"Top momentum : +{scores[s][1]:.1%} sur 6 mois, score {scores[s][0]:.2f}" for s in top}
        for s in ctx.portfolio.positions:
            if s not in top:
                reasons[s] = "Sort du top momentum"
        if not top:
            return Decision({}, reasons, note="Aucun momentum positif : cash")
        return Decision({s: 0.95 / len(top) for s in top}, reasons,
                        note=f"Rééquilibrage {month} : {', '.join(top)}")


class MeanReversion(Strategy):
    id = "mean_reversion"
    name = "Retour à la moyenne"
    description = ("Achète les replis (RSI14 < 30) des actifs en tendance de fond haussière "
                   "(cours > MM200). Sort si RSI > 55, après 15 jours, ou stop à -8 %.")
    weight = 0.10
    max_positions = 8

    def decide(self, ctx: Context) -> Decision | None:
        pf, weights, reasons, keep = ctx.portfolio, {}, {}, set()
        for s, pos in pf.positions.items():
            c = ctx.market.close(s)
            r = rsi(c)
            px = ctx.market.last_price_eur(s) or pos.avg_cost_eur
            held = (ctx.date - pos.opened_at).days
            pnl = px / pos.avg_cost_eur - 1
            if r is not None and r > 55:
                reasons[s] = f"Objectif atteint : RSI {r:.0f}"
            elif held >= 15:
                reasons[s] = f"Durée max atteinte ({held} j), P&L {pnl:+.1%}"
            elif pnl < -0.08:
                reasons[s] = f"Stop-loss : {pnl:+.1%}"
            else:
                keep.add(s)
        slots = self.max_positions - len(keep)
        candidates = []
        for s in ctx.market.symbols:
            if s in pf.positions:
                continue
            c = ctx.market.close(s)
            r, s200 = rsi(c), sma(c, 200)
            if r is not None and s200 is not None and r < 30 and c.iloc[-1] > s200:
                candidates.append((r, s))
        for r, s in sorted(candidates)[: max(slots, 0)]:
            weights[s] = self.weight
            reasons[s] = f"Survente RSI {r:.0f} dans une tendance haussière"
        if not weights and not (set(pf.positions) - keep):
            return None
        return Decision(weights, reasons, keep=keep)
