# RiverTerminal 📈

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An open-source Bloomberg Terminal TUI built entirely on free data sources. Fast, information-dense financial data terminal for your console.

## Features

### Phase 1 (Current)
- 📊 **Dashboard**: Market overview with S&P 500, DJIA, NASDAQ, VIX
- 💰 **Quote Screen**: Full ticker details with fundamentals and news
- 📝 **Watchlists**: SQLite-backed, real-time price updates
- 📈 **Charts**: ASCII line charts with multiple timeframes
- 📰 **News Feed**: RSS aggregation from major financial outlets

### Navigation
- **Command Bar**: Type `AAPL <Enter>` to jump to Apple's quote
- **F-Keys**: F1=Dashboard, F2=Quote, F3=Watchlist, F4=Charts, F6=News
- **Keyboard-driven**: Everything accessible without a mouse

## Installation

```bash
# Clone the repository
git clone https://github.com/rivermortgage/riveterminal.git
cd riveterminal

# Install in development mode
pip install -e .

# Run the application
python -m riveterminal
```

## Quick Start

1. **Launch**: `python -m riveterminal`
2. **Navigate**: Use F-keys or command bar
3. **Search stocks**: Type ticker symbols like `AAPL`, `MSFT`, `TSLA`
4. **Add to watchlist**: Press `a` on any quote screen
5. **View charts**: F4 for charts, use 1/2/3 for timeframes

## Data Sources

All data comes from free, publicly available sources:
- **Yahoo Finance**: Stock quotes, fundamentals, news
- **RSS Feeds**: Reuters, CNBC, MarketWatch headlines
- **No API keys required** for basic functionality

## Requirements

- Python 3.12+
- Terminal with color support
- Internet connection for real-time data

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/
isort src/

# Type checking
mypy src/
```

## Contributing

See [SPEC.md](SPEC.md) for the full project specification and roadmap.

## License

MIT License - see [LICENSE](LICENSE) for details.