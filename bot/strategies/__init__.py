from .ai import GeminiAgent, SentimentTrend
from .base import Context, Decision, Strategy
from .technical import BuyAndHold, MeanReversion, Momentum, TrendFollowing

# Ajoute ici tes nouvelles stratégies
STRATEGIES: list[Strategy] = [
    BuyAndHold(),
    TrendFollowing(),
    Momentum(),
    MeanReversion(),
    SentimentTrend(),
    GeminiAgent(),
]

__all__ = ["STRATEGIES", "Context", "Decision", "Strategy"]
