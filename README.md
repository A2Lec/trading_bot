# Paper Trading Bot

Bot de **paper trading** multi-marchés et multi-stratégies. Il tourne une fois par jour (horizon swing) et utilise **Gemini** pour analyser l'actualité. Un dashboard mobile permet de suivre les résultats.

```
GitHub Actions (cron 22:17 UTC)          Vercel
┌──────────────────────────────┐   ┌──────────────────────────┐
│ python -m bot run            │   │ web/ — Next.js (PWA)     │
│  1. cours yfinance + FX      │   │  stratégies, positions,  │
│  2. news → Gemini → score    │   │  ordres, marché, logs    │
│  3. 6 stratégies → ordres    │   │                          │
└──────────────┬───────────────┘   └────────────┬─────────────┘
               └──────► Postgres (Neon) ◄────────┘
```

Tout tient dans les offres gratuites : GitHub Actions, Neon et Vercel Hobby. Seuls les appels Gemini consomment tes crédits API.

## Fonctionnement

- **Univers** : environ 30 actifs (actions US, Europe et Asie, ETF indices, obligations, or et argent, pétrole, crypto). À modifier dans `bot/config.py`.
- **Portefeuille simulé en EUR** : 10 000 € par stratégie, conversion des devises au taux du jour, frais de 0,10 % (minimum 1 €), slippage de 0,05 %, quantités fractionnaires, pas de levier.
- **Pas de look-ahead** : une décision prise sur la clôture du jour J s'exécute à l'**ouverture de la séance suivante**.
- **Ordres en attente** : chaque nouvelle décision remplace les ordres pas encore exécutés (week-end, jour férié…).

### Stratégies (`bot/strategies/`)

| id | Stratégie | Gemini |
|---|---|---|
| `buy_hold` | Benchmark : achète le MSCI World et le garde | |
| `trend` | Suivi de tendance (MM50 > MM200) | |
| `momentum` | Top 5 du rendement 6 mois ajusté du risque, rééquilibré chaque mois | |
| `mean_reversion` | Achat des replis (RSI < 30) en tendance haussière | |
| `sentiment` | Sentiment des news ≥ 0,4 et cours > MM50 | ✓ |
| `gemini_agent` | Gemini décide seul de l'allocation à partir des indicateurs et des news | ✓ |

Pour ajouter une stratégie : crée une classe qui hérite de `Strategy`, implémente `decide(ctx)` (elle renvoie des poids cibles ou `None`), puis ajoute-la à la liste `STRATEGIES` dans `bot/strategies/__init__.py`.

## Mise en route

### 1. Base de données (Neon, gratuit)
Sur Vercel : **Storage → Create Database → Neon (Postgres)**. Copie la chaîne de connexion `DATABASE_URL`.

### 2. Secrets GitHub
Dans le dépôt : **Settings → Secrets and variables → Actions → New repository secret**
- `DATABASE_URL` : chaîne de connexion Neon
- `GEMINI_API_KEY` : clé Google AI Studio

Facultatif, dans l'onglet *Variables* : `GEMINI_MODEL` pour imposer un modèle (ex. `gemini-2.5-pro`). Sans cette variable, le bot choisit automatiquement le modèle Flash stable le plus récent disponible pour ta clé. Le modèle utilisé est indiqué dans le log de chaque run.

### 3. Premier run
Onglet **Actions → Daily run → Run workflow**. Le bot crée les tables et programme les premiers ordres, qui seront exécutés au run suivant. Ensuite, il tourne tout seul chaque soir.

### 4. Dashboard (Vercel)
**Add New → Project** → importe ce dépôt :
- **Root Directory** : `web`
- Variables d'environnement : `DATABASE_URL` (ajoutée automatiquement si Neon est relié au projet) et `DASHBOARD_PASSWORD` (mot de passe d'accès)

Sur le téléphone, ouvre l'URL puis **Partager → Sur l'écran d'accueil** pour l'installer comme une app.

## En local

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python -m bot list                    # liste des stratégies
python -m bot backtest --period 5y    # backtest des stratégies techniques
python -m bot run --no-llm            # run quotidien, sans Gemini (SQLite local.db par défaut)
```

Le backtest est aussi disponible dans GitHub (**Actions → Backtest**). Les stratégies Gemini ne sont pas backtestables, faute d'historique de news.

## Limites connues

- yfinance est une source non officielle : un ticker peut parfois manquer un jour ; le bot continue avec les autres.
- Les dividendes ne sont pas versés en live (les cours sont bruts) ; les splits d'actions ne sont pas gérés.
- Les tâches cron de GitHub peuvent partir avec quelques minutes de retard, ce qui est sans importance pour du swing.
- Paper trading uniquement : aucun ordre réel n'est passé.
