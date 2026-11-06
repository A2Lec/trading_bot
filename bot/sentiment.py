"""Analyse du sentiment des actualités par Gemini."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from pydantic import BaseModel, Field

from .config import Asset
from .llm import Gemini, GeminiUnavailable
from .news import headlines

log = logging.getLogger(__name__)


@dataclass
class Sentiment:
    symbol: str
    score: float  # -1 (très négatif) .. +1 (très positif)
    summary: str
    headlines: list[dict]


class _Item(BaseModel):
    symbol: str
    score: float = Field(description="Impact attendu sur le cours à 1-4 semaines, de -1 à +1. 0 si neutre ou sans info.")
    summary: str = Field(description="Une ou deux phrases en français expliquant le score.")


class _Batch(BaseModel):
    items: list[_Item]


SYSTEM = (
    "Tu es un analyste financier. Pour chaque actif, évalue l'impact probable des actualités "
    "récentes sur son cours dans les 1 à 4 semaines. Sois prudent : la plupart des news sont "
    "du bruit, réserve les scores extrêmes (|score| > 0.6) aux événements réellement majeurs "
    "(résultats, guidance, régulation, M&A, choc macro). Sans actualité pertinente : score 0."
)


def analyze(llm: Gemini, assets: list[Asset], batch_size: int = 10) -> dict[str, Sentiment]:
    news = {a.symbol: headlines(a) for a in assets}
    results: dict[str, Sentiment] = {}
    for i in range(0, len(assets), batch_size):
        batch = assets[i:i + batch_size]
        blocks = []
        for a in batch:
            lines = [f"- [{h['source']}] {h['title']}" + (f" — {h['summary']}" if h["summary"] else "")
                     for h in news[a.symbol]] or ["(aucune actualité récente)"]
            blocks.append(f"### {a.symbol} — {a.name} ({a.asset_class}, {a.region})\n" + "\n".join(lines))
        prompt = "Analyse les actifs suivants. Renvoie un élément par actif.\n\n" + "\n\n".join(blocks)
        try:
            out: _Batch = llm.json(prompt, _Batch, system=SYSTEM)
        except GeminiUnavailable as e:
            log.error("Analyse de sentiment interrompue : %s", e)
            if llm.error:  # erreur définitive : inutile de tenter les lots suivants
                break
            continue
        for it in out.items:
            if it.symbol in news:
                results[it.symbol] = Sentiment(
                    it.symbol, max(-1.0, min(1.0, float(it.score))), it.summary,
                    [{"title": h["title"], "source": h["source"], "url": h["url"]} for h in news[it.symbol]],
                )
    log.info("Sentiment calculé pour %d/%d actifs", len(results), len(assets))
    return results
