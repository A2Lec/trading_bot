from __future__ import annotations

import numpy as np
import pandas as pd


def sma(s: pd.Series, n: int) -> float | None:
    return float(s.iloc[-n:].mean()) if len(s) >= n else None


def rsi(s: pd.Series, n: int = 14) -> float | None:
    if len(s) < n + 1:
        return None
    delta = s.diff().dropna()
    gain = delta.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    if loss.iloc[-1] == 0:
        return 100.0
    rs = gain.iloc[-1] / loss.iloc[-1]
    return float(100 - 100 / (1 + rs))


def ret(s: pd.Series, n: int) -> float | None:
    if len(s) <= n:
        return None
    return float(s.iloc[-1] / s.iloc[-1 - n] - 1)


def volatility(s: pd.Series, n: int = 60) -> float | None:
    """Volatilité annualisée (rendements journaliers)."""
    if len(s) <= n:
        return None
    r = s.pct_change().dropna().iloc[-n:]
    return float(r.std() * np.sqrt(252))


def snapshot(s: pd.Series) -> dict:
    """Résumé des indicateurs pour un actif (utilisé par le dashboard et Gemini)."""
    last = float(s.iloc[-1]) if len(s) else None
    s50, s200 = sma(s, 50), sma(s, 200)
    return {
        "close": last,
        "ret_1d": ret(s, 1),
        "ret_1w": ret(s, 5),
        "ret_1m": ret(s, 21),
        "ret_3m": ret(s, 63),
        "ret_6m": ret(s, 126),
        "rsi14": rsi(s, 14),
        "sma50": s50,
        "sma200": s200,
        "above_sma200": (last > s200) if (last is not None and s200) else None,
        "vol_60d": volatility(s, 60),
    }
