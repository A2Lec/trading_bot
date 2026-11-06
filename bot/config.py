"""Configuration : univers d'actifs, paramètres de simulation."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Asset:
    symbol: str  # ticker Yahoo Finance
    name: str
    currency: str  # devise de cotation
    asset_class: str  # equity / etf / commodity / bond / crypto
    region: str


# Univers multi-marchés. Ajoute / retire des lignes librement.
# Attention : éviter les tickers cotés en pence (GBp, Londres) sauf à gérer la conversion /100.
UNIVERSE: list[Asset] = [
    # --- Actions US
    Asset("AAPL", "Apple", "USD", "equity", "US"),
    Asset("MSFT", "Microsoft", "USD", "equity", "US"),
    Asset("NVDA", "Nvidia", "USD", "equity", "US"),
    Asset("AMZN", "Amazon", "USD", "equity", "US"),
    Asset("GOOGL", "Alphabet", "USD", "equity", "US"),
    Asset("JPM", "JPMorgan Chase", "USD", "equity", "US"),
    Asset("XOM", "ExxonMobil", "USD", "equity", "US"),
    # --- Actions Europe
    Asset("MC.PA", "LVMH", "EUR", "equity", "Europe"),
    Asset("TTE.PA", "TotalEnergies", "EUR", "equity", "Europe"),
    Asset("AIR.PA", "Airbus", "EUR", "equity", "Europe"),
    Asset("SAP.DE", "SAP", "EUR", "equity", "Europe"),
    Asset("ASML.AS", "ASML", "EUR", "equity", "Europe"),
    Asset("NESN.SW", "Nestlé", "CHF", "equity", "Europe"),
    Asset("NOVO-B.CO", "Novo Nordisk", "DKK", "equity", "Europe"),
    # --- Actions Asie
    Asset("7203.T", "Toyota", "JPY", "equity", "Asia"),
    Asset("TSM", "TSMC (ADR)", "USD", "equity", "Asia"),
    # --- ETF indices
    Asset("IWDA.AS", "iShares MSCI World", "EUR", "etf", "World"),
    Asset("SPY", "S&P 500 ETF", "USD", "etf", "US"),
    Asset("QQQ", "Nasdaq 100 ETF", "USD", "etf", "US"),
    Asset("EWJ", "MSCI Japan ETF", "USD", "etf", "Asia"),
    Asset("EEM", "MSCI Emerging Markets ETF", "USD", "etf", "EM"),
    # --- Obligations
    Asset("TLT", "US Treasury 20+ ans ETF", "USD", "bond", "US"),
    Asset("IEF", "US Treasury 7-10 ans ETF", "USD", "bond", "US"),
    # --- Matières premières
    Asset("GLD", "Or (ETF)", "USD", "commodity", "World"),
    Asset("SLV", "Argent (ETF)", "USD", "commodity", "World"),
    Asset("USO", "Pétrole WTI (ETF)", "USD", "commodity", "World"),
    # --- Crypto
    Asset("BTC-USD", "Bitcoin", "USD", "crypto", "Crypto"),
    Asset("ETH-USD", "Ethereum", "USD", "crypto", "Crypto"),
    Asset("SOL-USD", "Solana", "USD", "crypto", "Crypto"),
]

ASSETS = {a.symbol: a for a in UNIVERSE}

# Actif de référence pour la stratégie « acheter et garder »
BENCHMARK = "IWDA.AS"

BASE_CURRENCY = "EUR"
INITIAL_CAPITAL = float(os.getenv("INITIAL_CAPITAL") or "10000")

# Coûts de transaction simulés
FEE_RATE = 0.001  # 0,10 % du montant
SLIPPAGE = 0.0005  # 0,05 % de prix défavorable
MIN_FEE = 1.0  # frais minimum par ordre, en EUR

# On ne trade pas un écart inférieur à ce % du portefeuille (évite le micro-rééquilibrage)
REBALANCE_THRESHOLD = 0.02

HISTORY_PERIOD = "2y"

GEMINI_MODEL = os.getenv("GEMINI_MODEL") or "gemini-flash-latest"
