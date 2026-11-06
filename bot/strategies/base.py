from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from ..llm import Gemini
    from ..market import Market
    from ..portfolio import Portfolio
    from ..sentiment import Sentiment


@dataclass
class Context:
    date: pd.Timestamp
    market: "Market"  # vue tronquée à `date`
    portfolio: "Portfolio"
    sentiment: dict[str, "Sentiment"]
    state: dict  # état persistant propre à la stratégie (JSON)
    llm: "Gemini | None" = None
    backtest: bool = False


@dataclass
class Decision:
    weights: dict[str, float]  # poids cibles (0..1) du portefeuille
    reasons: dict[str, str] = field(default_factory=dict)  # justification par actif
    keep: set[str] = field(default_factory=set)  # actifs à ne pas toucher
    note: str = ""  # commentaire global (journal)


class Strategy:
    id: str = ""
    name: str = ""
    description: str = ""
    needs_llm: bool = False

    def decide(self, ctx: Context) -> Decision | None:
        """Renvoie une décision, ou None pour ne rien changer."""
        raise NotImplementedError
