"""Persistance (Postgres en production, SQLite en local)."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import pandas as pd
from sqlalchemy import (Boolean, Column, Date, DateTime, Float, Integer, MetaData, String, Table,
                        Text, create_engine, delete, insert, select, update)

from .portfolio import Order, Portfolio, Position

meta = MetaData()

strategies_t = Table(
    "strategies", meta,
    Column("id", String(64), primary_key=True),
    Column("name", String(128), nullable=False),
    Column("description", Text),
    Column("initial_capital", Float, nullable=False),
    Column("cash_eur", Float, nullable=False),
    Column("state", Text, default="{}"),
    Column("created_at", DateTime(timezone=True)),
    Column("updated_at", DateTime(timezone=True)),
)
positions_t = Table(
    "positions", meta,
    Column("strategy_id", String(64), primary_key=True),
    Column("symbol", String(32), primary_key=True),
    Column("quantity", Float, nullable=False),
    Column("avg_cost_eur", Float, nullable=False),
    Column("opened_at", Date),
    Column("last_price_eur", Float),
    Column("value_eur", Float),
)
orders_t = Table(
    "orders", meta,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("strategy_id", String(64), index=True, nullable=False),
    Column("symbol", String(32), nullable=False),
    Column("side", String(8), nullable=False),
    Column("quantity", Float, nullable=False),
    Column("created_at", Date, nullable=False),
    Column("status", String(16), nullable=False),
    Column("filled_at", Date),
    Column("price_local", Float),
    Column("price_eur", Float),
    Column("fees_eur", Float),
    Column("realized_pnl_eur", Float),
    Column("reason", Text),
)
equity_t = Table(
    "equity", meta,
    Column("strategy_id", String(64), primary_key=True),
    Column("date", Date, primary_key=True),
    Column("equity_eur", Float, nullable=False),
    Column("cash_eur", Float, nullable=False),
    Column("invested_eur", Float, nullable=False),
)
journal_t = Table(
    "journal", meta,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("strategy_id", String(64), index=True, nullable=False),
    Column("date", Date, nullable=False),
    Column("note", Text, nullable=False),
)
sentiment_t = Table(
    "sentiment", meta,
    Column("date", Date, primary_key=True),
    Column("symbol", String(32), primary_key=True),
    Column("score", Float, nullable=False),
    Column("summary", Text),
    Column("headlines", Text),
)
market_t = Table(
    "market", meta,
    Column("symbol", String(32), primary_key=True),
    Column("name", String(128)),
    Column("currency", String(8)),
    Column("asset_class", String(32)),
    Column("region", String(32)),
    Column("date", Date),
    Column("close", Float),
    Column("close_eur", Float),
    Column("ret_1d", Float),
    Column("ret_1w", Float),
    Column("ret_1m", Float),
    Column("ret_3m", Float),
    Column("ret_6m", Float),
    Column("rsi14", Float),
    Column("above_sma200", Boolean),
    Column("vol_60d", Float),
)
prices_t = Table(
    "prices", meta,
    Column("symbol", String(32), primary_key=True),
    Column("date", Date, primary_key=True),
    Column("close", Float, nullable=False),
)
runs_t = Table(
    "runs", meta,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("started_at", DateTime(timezone=True)),
    Column("finished_at", DateTime(timezone=True)),
    Column("status", String(16)),
    Column("message", Text),
)


def _url() -> str:
    url = os.getenv("DATABASE_URL", "sqlite:///local.db")
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


def _d(ts) -> object:
    return pd.Timestamp(ts).date() if ts is not None else None


def _now():
    return datetime.now(timezone.utc)


class Store:
    def __init__(self, url: str | None = None):
        self.engine = create_engine(url or _url(), pool_pre_ping=True)
        meta.create_all(self.engine)

    # ------------------------------------------------------------------ runs
    def start_run(self) -> int:
        with self.engine.begin() as c:
            return c.execute(insert(runs_t).values(started_at=_now(), status="running")).inserted_primary_key[0]

    def finish_run(self, run_id: int, status: str, message: str) -> None:
        with self.engine.begin() as c:
            c.execute(update(runs_t).where(runs_t.c.id == run_id)
                      .values(finished_at=_now(), status=status, message=message[-20000:]))

    # ------------------------------------------------------------------ stratégies
    def load(self, strategy, initial_capital: float) -> tuple[Portfolio, dict]:
        with self.engine.begin() as c:
            row = c.execute(select(strategies_t).where(strategies_t.c.id == strategy.id)).mappings().first()
            if row is None:
                c.execute(insert(strategies_t).values(
                    id=strategy.id, name=strategy.name, description=strategy.description,
                    initial_capital=initial_capital, cash_eur=initial_capital, state="{}",
                    created_at=_now(), updated_at=_now()))
                return Portfolio(strategy.id, initial_capital), {}
            pf = Portfolio(strategy.id, row["cash_eur"])
            for p in c.execute(select(positions_t).where(positions_t.c.strategy_id == strategy.id)).mappings():
                pf.positions[p["symbol"]] = Position(p["symbol"], p["quantity"], p["avg_cost_eur"],
                                                     pd.Timestamp(p["opened_at"]))
            for o in c.execute(select(orders_t).where(orders_t.c.strategy_id == strategy.id,
                                                      orders_t.c.status == "pending")).mappings():
                pf.pending.append(Order(o["symbol"], o["side"], o["quantity"], pd.Timestamp(o["created_at"]),
                                        o["reason"] or "", id=o["id"], dirty=False))
            return pf, json.loads(row["state"] or "{}")

    def save(self, strategy, pf: Portfolio, state: dict, market, date, note: str | None) -> None:
        d = _d(date)
        with self.engine.begin() as c:
            c.execute(update(strategies_t).where(strategies_t.c.id == strategy.id).values(
                name=strategy.name, description=strategy.description, cash_eur=pf.cash_eur,
                state=json.dumps(state, ensure_ascii=False, default=str), updated_at=_now()))
            c.execute(delete(positions_t).where(positions_t.c.strategy_id == strategy.id))
            for s, p in pf.positions.items():
                px = market.last_price_eur(s)
                c.execute(insert(positions_t).values(
                    strategy_id=strategy.id, symbol=s, quantity=p.quantity, avg_cost_eur=p.avg_cost_eur,
                    opened_at=_d(p.opened_at), last_price_eur=px, value_eur=p.quantity * (px or p.avg_cost_eur)))
            for o in pf.history + pf.pending:
                if not o.dirty:
                    continue
                vals = dict(strategy_id=strategy.id, symbol=o.symbol, side=o.side, quantity=o.quantity,
                            created_at=_d(o.created_at), status=o.status, filled_at=_d(o.filled_at),
                            price_local=o.price_local, price_eur=o.price_eur, fees_eur=o.fees_eur,
                            realized_pnl_eur=o.realized_pnl_eur, reason=o.reason)
                if o.id is None:
                    o.id = c.execute(insert(orders_t).values(**vals)).inserted_primary_key[0]
                else:
                    c.execute(update(orders_t).where(orders_t.c.id == o.id).values(**vals))
                o.dirty = False
            inv = pf.invested(market)
            c.execute(delete(equity_t).where(equity_t.c.strategy_id == strategy.id, equity_t.c.date == d))
            c.execute(insert(equity_t).values(strategy_id=strategy.id, date=d, equity_eur=pf.cash_eur + inv,
                                              cash_eur=pf.cash_eur, invested_eur=inv))
            if note:
                c.execute(delete(journal_t).where(journal_t.c.strategy_id == strategy.id, journal_t.c.date == d))
                c.execute(insert(journal_t).values(strategy_id=strategy.id, date=d, note=note))
        pf.history.clear()

    # ------------------------------------------------------------------ marché
    def save_market(self, market, snapshots: dict[str, dict], history_days: int = 260) -> None:
        with self.engine.begin() as c:
            for s, snap in snapshots.items():
                a = market.assets[s]
                closes = market.close(s)
                c.execute(delete(market_t).where(market_t.c.symbol == s))
                c.execute(insert(market_t).values(
                    symbol=s, name=a.name, currency=a.currency, asset_class=a.asset_class, region=a.region,
                    date=_d(closes.index[-1]), close=snap["close"], close_eur=market.last_price_eur(s),
                    **{k: snap[k] for k in ("ret_1d", "ret_1w", "ret_1m", "ret_3m", "ret_6m", "rsi14",
                                            "above_sma200", "vol_60d")}))
                c.execute(delete(prices_t).where(prices_t.c.symbol == s))
                tail = closes.iloc[-history_days:]
                c.execute(insert(prices_t), [{"symbol": s, "date": _d(i), "close": float(v)}
                                             for i, v in tail.items()])

    def save_sentiment(self, date, sentiment: dict) -> None:
        d = _d(date)
        with self.engine.begin() as c:
            c.execute(delete(sentiment_t).where(sentiment_t.c.date == d))
            for s in sentiment.values():
                c.execute(insert(sentiment_t).values(date=d, symbol=s.symbol, score=s.score, summary=s.summary,
                                                     headlines=json.dumps(s.headlines, ensure_ascii=False)))
