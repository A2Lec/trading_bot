"""Données de marché (yfinance) et conversion de devises.

`Market` contient l'historique complet ; `market.view(date)` renvoie une vue
tronquée à `date` pour que les stratégies ne voient jamais le futur.
"""
from __future__ import annotations

import logging

import pandas as pd
import yfinance as yf

from .config import BASE_CURRENCY, Asset

log = logging.getLogger(__name__)


def _fx_ticker(currency: str) -> str:
    # EURUSD=X = nombre d'USD pour 1 EUR
    return f"{BASE_CURRENCY}{currency}=X"


def download(symbols: list[str], period: str, auto_adjust: bool) -> dict[str, pd.DataFrame]:
    raw = yf.download(
        symbols,
        period=period,
        interval="1d",
        auto_adjust=auto_adjust,
        group_by="ticker",
        progress=False,
        threads=True,
    )
    out: dict[str, pd.DataFrame] = {}
    for s in symbols:
        try:
            df = raw[s] if isinstance(raw.columns, pd.MultiIndex) else raw
        except KeyError:
            log.warning("Pas de données pour %s", s)
            continue
        df = df[["Open", "High", "Low", "Close", "Volume"]].dropna(subset=["Open", "Close"])
        if df.empty:
            log.warning("Pas de données pour %s", s)
            continue
        df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
        df = df[~df.index.duplicated(keep="last")].sort_index()
        out[s] = df
    return out


class Market:
    def __init__(self, assets: dict[str, Asset], bars: dict[str, pd.DataFrame],
                 fx: dict[str, pd.Series], asof: pd.Timestamp | None = None):
        self.assets = assets
        self._bars = bars
        self._fx = fx  # devise -> série (unités de devise pour 1 EUR)
        self.asof = asof

    # ------------------------------------------------------------------ chargement
    @classmethod
    def load(cls, universe: list[Asset], period: str = "2y", auto_adjust: bool = False) -> "Market":
        symbols = [a.symbol for a in universe]
        bars = download(symbols, period, auto_adjust)
        currencies = sorted({a.currency for a in universe if a.currency != BASE_CURRENCY})
        fx_raw = download([_fx_ticker(c) for c in currencies], period, auto_adjust=False) if currencies else {}
        fx = {c: fx_raw[_fx_ticker(c)]["Close"] for c in currencies if _fx_ticker(c) in fx_raw}
        missing_fx = [c for c in currencies if c not in fx]
        if missing_fx:
            raise RuntimeError(f"Taux de change introuvables : {missing_fx}")
        assets = {a.symbol: a for a in universe if a.symbol in bars}
        return cls(assets, bars, fx)

    def view(self, date: pd.Timestamp) -> "Market":
        return Market(self.assets, self._bars, self._fx, asof=pd.Timestamp(date))

    # ------------------------------------------------------------------ accès
    @property
    def symbols(self) -> list[str]:
        return list(self.assets)

    def bars(self, symbol: str) -> pd.DataFrame:
        df = self._bars.get(symbol)
        if df is None:
            return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])
        return df if self.asof is None else df.loc[: self.asof]

    def close(self, symbol: str) -> pd.Series:
        return self.bars(symbol)["Close"]

    def last_close(self, symbol: str) -> float | None:
        c = self.close(symbol)
        return float(c.iloc[-1]) if len(c) else None

    def last_date(self) -> pd.Timestamp:
        return max(self.bars(s).index[-1] for s in self.symbols if len(self.bars(s)))

    def calendar(self) -> pd.DatetimeIndex:
        idx = pd.DatetimeIndex([])
        for df in self._bars.values():
            idx = idx.union(df.index)
        return idx

    def next_bar_after(self, symbol: str, date: pd.Timestamp) -> tuple[pd.Timestamp, pd.Series] | None:
        """Première barre strictement après `date` (et <= asof)."""
        df = self.bars(symbol)
        after = df.loc[df.index > pd.Timestamp(date)]
        if after.empty:
            return None
        return after.index[0], after.iloc[0]

    # ------------------------------------------------------------------ devises
    def fx_rate(self, currency: str, date: pd.Timestamp | None = None) -> float:
        """Unités de `currency` pour 1 EUR à la date donnée (dernière valeur connue)."""
        if currency == BASE_CURRENCY:
            return 1.0
        s = self._fx[currency]
        d = pd.Timestamp(date) if date is not None else self.asof
        if d is not None:
            s = s.loc[:d]
        if s.empty:
            s = self._fx[currency]  # avant le début de l'historique FX : premier taux connu
            return float(s.iloc[0])
        return float(s.iloc[-1])

    def to_eur(self, symbol: str, price_local: float, date: pd.Timestamp | None = None) -> float:
        return price_local / self.fx_rate(self.assets[symbol].currency, date)

    def last_price_eur(self, symbol: str) -> float | None:
        c = self.close(symbol)
        if not len(c):
            return None
        return self.to_eur(symbol, float(c.iloc[-1]), c.index[-1])
