"""Portefeuille simulé et exécution des ordres (logique pure, sans base de données).

Règle d'exécution : une décision prise à la date D (sur la clôture de D) est
exécutée à l'OUVERTURE de la première séance strictement postérieure à D.
Cela évite tout biais d'anticipation (look-ahead).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from .config import FEE_RATE, MIN_FEE, REBALANCE_THRESHOLD, SLIPPAGE
from .market import Market


@dataclass
class Position:
    symbol: str
    quantity: float
    avg_cost_eur: float  # prix de revient unitaire en EUR (frais inclus)
    opened_at: pd.Timestamp


@dataclass
class Order:
    symbol: str
    side: str  # "buy" | "sell"
    quantity: float
    created_at: pd.Timestamp
    reason: str = ""
    status: str = "pending"  # pending | filled | cancelled
    id: int | None = None
    filled_at: pd.Timestamp | None = None
    price_local: float | None = None
    price_eur: float | None = None
    fees_eur: float | None = None
    realized_pnl_eur: float | None = None
    dirty: bool = True  # à persister


@dataclass
class Portfolio:
    strategy_id: str
    cash_eur: float
    positions: dict[str, Position] = field(default_factory=dict)
    pending: list[Order] = field(default_factory=list)
    history: list[Order] = field(default_factory=list)  # ordres traités pendant ce run

    # ------------------------------------------------------------------ valorisation
    def position_value(self, market: Market, symbol: str) -> float:
        p = self.positions.get(symbol)
        if not p:
            return 0.0
        px = market.last_price_eur(symbol)
        return p.quantity * (px if px is not None else p.avg_cost_eur)

    def invested(self, market: Market) -> float:
        return sum(self.position_value(market, s) for s in self.positions)

    def equity(self, market: Market) -> float:
        return self.cash_eur + self.invested(market)

    def weights(self, market: Market) -> dict[str, float]:
        eq = self.equity(market)
        return {s: self.position_value(market, s) / eq for s in self.positions} if eq > 0 else {}

    # ------------------------------------------------------------------ exécution
    def fill_pending(self, market: Market) -> list[Order]:
        """Exécute les ordres en attente dont la séance suivante est disponible.

        Ventes d'abord (libèrent du cash), puis achats (réduits si le cash manque).
        """
        filled: list[Order] = []
        still_pending: list[Order] = []
        fillable: list[tuple[Order, pd.Timestamp, float]] = []
        for o in self.pending:
            nb = market.next_bar_after(o.symbol, o.created_at)
            if nb is None:
                still_pending.append(o)
            else:
                fillable.append((o, nb[0], float(nb[1]["Open"])))

        fillable.sort(key=lambda t: 0 if t[0].side == "sell" else 1)
        for o, date, open_px in fillable:
            if o.side == "sell":
                self._fill_sell(market, o, date, open_px)
            else:
                self._fill_buy(market, o, date, open_px)
            o.dirty = True
            self.history.append(o)
            filled.append(o)
        self.pending = still_pending
        return filled

    def _fill_sell(self, market: Market, o: Order, date, open_px: float) -> None:
        pos = self.positions.get(o.symbol)
        if not pos or pos.quantity <= 0:
            o.status = "cancelled"
            o.reason += " | annulé : pas de position"
            return
        qty = min(o.quantity, pos.quantity)
        px_local = open_px * (1 - SLIPPAGE)
        px_eur = market.to_eur(o.symbol, px_local, date)
        gross = qty * px_eur
        fees = max(gross * FEE_RATE, MIN_FEE)
        self.cash_eur += gross - fees
        o.realized_pnl_eur = gross - fees - qty * pos.avg_cost_eur
        pos.quantity -= qty
        if pos.quantity <= 1e-9 or pos.quantity * px_eur < 1.0:
            del self.positions[o.symbol]
        o.quantity, o.status, o.filled_at = qty, "filled", date
        o.price_local, o.price_eur, o.fees_eur = px_local, px_eur, fees

    def _fill_buy(self, market: Market, o: Order, date, open_px: float) -> None:
        px_local = open_px * (1 + SLIPPAGE)
        px_eur = market.to_eur(o.symbol, px_local, date)
        qty = o.quantity
        cost = qty * px_eur
        fees = max(cost * FEE_RATE, MIN_FEE)
        if cost + fees > self.cash_eur:  # pas assez de cash : on réduit
            qty = max((self.cash_eur - MIN_FEE) / (px_eur * (1 + FEE_RATE)), 0.0)
            cost = qty * px_eur
            fees = max(cost * FEE_RATE, MIN_FEE)
        if qty * px_eur < 10.0:  # montant ridicule : on annule
            o.status = "cancelled"
            o.reason += " | annulé : cash insuffisant"
            return
        self.cash_eur -= cost + fees
        pos = self.positions.get(o.symbol)
        if pos:
            total = pos.quantity * pos.avg_cost_eur + cost + fees
            pos.quantity += qty
            pos.avg_cost_eur = total / pos.quantity
        else:
            self.positions[o.symbol] = Position(o.symbol, qty, (cost + fees) / qty, date)
        o.quantity, o.status, o.filled_at = qty, "filled", date
        o.price_local, o.price_eur, o.fees_eur = px_local, px_eur, fees

    # ------------------------------------------------------------------ décisions -> ordres
    def apply_targets(self, market: Market, date: pd.Timestamp, weights: dict[str, float],
                      reasons: dict[str, str], keep: set[str]) -> list[Order]:
        """Remplace les ordres en attente par ceux qui amènent le portefeuille vers `weights`.

        - `weights` : poids cibles (0..1) ; un actif détenu absent de `weights` et de `keep` est vendu.
        - `keep` : actifs à laisser tels quels.
        """
        for o in self.pending:
            o.status, o.dirty = "cancelled", True
            o.reason += " | remplacé par une nouvelle décision"
            self.history.append(o)
        self.pending = []

        eq = self.equity(market)
        if eq <= 0:
            return []
        total = sum(w for w in weights.values() if w > 0)
        scale = 1.0 / total if total > 1.0 else 1.0  # jamais d'effet de levier

        targets = {s: max(w, 0.0) * scale for s, w in weights.items() if s in market.assets}
        for s in self.positions:
            if s not in targets and s not in keep:
                targets[s] = 0.0

        orders: list[Order] = []
        for s, w in targets.items():
            if s in keep:
                continue
            px = market.last_price_eur(s)
            if px is None or px <= 0:
                continue
            current = self.position_value(market, s)
            target_val = w * eq
            diff = target_val - current
            exiting = w == 0.0 and current > 0
            entering = current == 0 and target_val > 0
            if not (exiting or entering) and abs(diff) < REBALANCE_THRESHOLD * eq:
                continue
            if abs(diff) < 10.0:
                continue
            if exiting:
                qty = self.positions[s].quantity
                side = "sell"
            else:
                side = "buy" if diff > 0 else "sell"
                qty = abs(diff) / px
            orders.append(Order(s, side, qty, pd.Timestamp(date), reasons.get(s, "")))
        self.pending = orders
        return orders
