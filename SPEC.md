# RiverTerminal — Open Source Bloomberg Terminal TUI

## Vision
A keyboard-driven terminal UI for financial data, built entirely on free/open data sources. Think Bloomberg Terminal meets hacker aesthetics. Fast, information-dense, no subscriptions.

## Tech Stack
- **Python 3.12+** with **Textual** (modern TUI framework by Textualize)
- **Rich** for rendering tables, charts, panels
- **httpx** for async HTTP
- **SQLite** for local data cache & watchlists
- **plotext** or **asciichartpy** for terminal charts

## Free Data Sources
| Source | Data | Limits |
|--------|------|--------|
| **Yahoo Finance** (yfinance) | Stocks, ETFs, options, fundamentals | Unofficial, generous |
| **FRED API** | Economic indicators (GDP, CPI, unemployment, yields) | 120 req/min, free key |
| **Alpha Vantage** | Intraday/daily prices, forex, crypto | 25 req/day (free tier) |
| **CoinGecko** | Crypto prices, market cap, volume | 10-30 req/min |
| **Finnhub** | Real-time quotes, news, earnings calendar | 60 req/min free |
| **Treasury.gov** | Treasury yields, auction data | Unlimited |
| **RSS/Atom Feeds** | Reuters, Bloomberg, CNBC, WSJ headlines | Unlimited |
| **SEC EDGAR** | Filings, 13F, insider transactions | 10 req/sec |

## Screens / Modules

### 1. Dashboard (HOME)
- Market overview: S&P 500, DJIA, NASDAQ, Russell 2000, VIX
- Treasury yield curve (2Y, 5Y, 10Y, 30Y)
- Crypto top 5
- Forex majors (EUR/USD, GBP/USD, USD/JPY)
- Top movers (gainers/losers)
- Breaking news ticker at bottom

### 2. Quote Screen (QUOTE / F2)
- Enter any ticker → full quote panel
- Price, change, volume, 52-week range, market cap
- Intraday sparkline chart
- Key fundamentals (P/E, EPS, dividend yield, beta)
- Recent news for that ticker

### 3. Watchlist (WATCH / F3)
- Multiple named watchlists (saved to SQLite)
- Real-time price updates (polling)
- Color-coded green/red for up/down
- Add/remove tickers, reorder
- Export to CSV

### 4. Charts (CHART / F4)
- ASCII candlestick or line charts
- Timeframes: 1D, 5D, 1M, 3M, 6M, 1Y, 5Y
- Overlay: SMA(20), SMA(50), SMA(200)
- Volume bars below
- Compare multiple tickers

### 5. Economic Dashboard (ECON / F5)
- FRED data: GDP, CPI, PPI, unemployment, fed funds rate
- Treasury yield curve visualization
- Historical comparison charts
- Key economic calendar events

### 6. News Feed (NEWS / F6)
- Aggregated RSS feeds from major financial outlets
- Filterable by keyword, sector
- Full article preview (fetch & render markdown)
- Ticker-specific news drill-down

### 7. Screener (SCREEN / F7)
- Filter stocks by: market cap, P/E, dividend yield, sector, 52-week performance
- Sort by any column
- Quick-add to watchlist
- Based on cached fundamental data

### 8. Portfolio Tracker (PORT / F8)
- Manual position entry (ticker, shares, cost basis)
- Real-time P&L calculation
- Allocation pie chart (ASCII)
- Daily/total return tracking
- Dividend income tracking

### 9. Crypto Dashboard (CRYPTO / F9)
- Top 50 by market cap
- BTC dominance, total market cap, fear & greed index
- Individual coin deep-dive
- DeFi TVL overview

### 10. Options Chain (OPT / F10)
- Options chain for any equity
- Greeks display (if available)
- Expiration date selector
- Put/call ratio

## Navigation
- **Command bar** at top (Bloomberg-style): type commands like `AAPL <GO>`, `ECON <GO>`
- **F-keys** for quick screen switching
- **Tab** to cycle panels within a screen
- **/** for search anywhere
- **q** or **ESC** to back/quit
- **?** for help overlay

## Architecture
```
riveterminal/
├── pyproject.toml
├── README.md
├── src/
│   └── riveterminal/
│       ├── __init__.py
│       ├── app.py              # Main Textual app
│       ├── config.py           # API keys, settings
│       ├── db.py               # SQLite for watchlists, portfolio, cache
│       ├── screens/
│       │   ├── dashboard.py
│       │   ├── quote.py
│       │   ├── watchlist.py
│       │   ├── chart.py
│       │   ├── economic.py
│       │   ├── news.py
│       │   ├── screener.py
│       │   ├── portfolio.py
│       │   ├── crypto.py
│       │   └── options.py
│       ├── widgets/
│       │   ├── command_bar.py   # Bloomberg-style command input
│       │   ├── ticker_tape.py   # Scrolling news/price ticker
│       │   ├── sparkline.py     # Inline price charts
│       │   ├── yield_curve.py   # Treasury yield visualization
│       │   └── market_panel.py  # Reusable market data panel
│       ├── data/
│       │   ├── yahoo.py
│       │   ├── fred.py
│       │   ├── alphavantage.py
│       │   ├── coingecko.py
│       │   ├── finnhub.py
│       │   ├── treasury.py
│       │   ├── news_feeds.py
│       │   └── sec.py
│       └── utils/
│           ├── formatting.py    # Number formatting, colors
│           ├── cache.py         # Request caching layer
│           └── charts.py        # ASCII chart rendering
├── tests/
│   └── ...
└── config.example.toml
```

## Phase 1 — MVP (What Forge builds first)
1. App skeleton with Textual, command bar, F-key navigation
2. Dashboard screen with market overview (Yahoo Finance)
3. Quote screen with full ticker lookup
4. Watchlist with SQLite persistence
5. Basic ASCII chart (line chart, 1D/1M/1Y)
6. News feed from RSS

## Phase 2 — Data Depth
7. Economic dashboard (FRED integration)
8. Treasury yield curve
9. Crypto dashboard (CoinGecko)
10. Screener with fundamental filters

## Phase 3 — Power Features
11. Portfolio tracker with P&L
12. Options chain
13. Chart overlays (SMA, volume)
14. SEC filings viewer
15. Export capabilities (CSV, PDF)

## Design Principles
- **Information density** — Pack as much data as possible into every screen
- **Speed** — Cache aggressively, async everywhere, never block the UI
- **Keyboard-first** — Every action reachable without a mouse
- **Color-coded** — Green for up, red for down, yellow for warnings, cyan for info
- **Offline-capable** — Cached data available when disconnected
