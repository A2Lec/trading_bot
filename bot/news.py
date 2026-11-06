"""Récupération de titres d'actualité par actif (Yahoo Finance + Google News RSS)."""
from __future__ import annotations

import logging
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import yfinance as yf

from .config import Asset

log = logging.getLogger(__name__)

MAX_HEADLINES = 8
MAX_AGE = timedelta(days=3)


def _yahoo(symbol: str) -> list[dict]:
    items = []
    try:
        for n in yf.Ticker(symbol).news or []:
            c = n.get("content", n)
            title = c.get("title")
            date = c.get("pubDate") or c.get("displayTime")
            if not title:
                continue
            try:
                dt = datetime.fromisoformat(date.replace("Z", "+00:00")) if date else None
            except ValueError:
                dt = None
            items.append({
                "title": title,
                "summary": (c.get("summary") or "")[:300],
                "source": (c.get("provider") or {}).get("displayName", "Yahoo"),
                "date": dt,
                "url": (c.get("canonicalUrl") or {}).get("url"),
            })
    except Exception as e:  # noqa: BLE001
        log.warning("News Yahoo indisponibles pour %s : %s", symbol, e)
    return items


def _google(query: str) -> list[dict]:
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(
        {"q": f"{query} when:3d", "hl": "en-US", "gl": "US", "ceid": "US:en"})
    items = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (paper-trading-bot)"})
        with urllib.request.urlopen(req, timeout=15) as r:
            root = ET.fromstring(r.read())
        for it in root.iter("item"):
            pub = it.findtext("pubDate")
            items.append({
                "title": it.findtext("title") or "",
                "summary": "",
                "source": it.findtext("source") or "Google News",
                "date": parsedate_to_datetime(pub) if pub else None,
                "url": it.findtext("link"),
            })
    except Exception as e:  # noqa: BLE001
        log.warning("Google News indisponible pour %s : %s", query, e)
    return items


def headlines(asset: Asset) -> list[dict]:
    now = datetime.now(timezone.utc)
    items = _yahoo(asset.symbol)
    if len(items) < 4:
        items += _google(f'"{asset.name}"')
    fresh, seen = [], set()
    for it in sorted(items, key=lambda x: x["date"] or now - MAX_AGE, reverse=True):
        key = it["title"].lower()[:80]
        if key in seen or (it["date"] and now - it["date"] > MAX_AGE):
            continue
        seen.add(key)
        fresh.append(it)
    return fresh[:MAX_HEADLINES]
