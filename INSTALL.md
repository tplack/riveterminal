# Installation & Quick Start Guide

## Prerequisites

- Python 3.12+
- Terminal with color support
- Internet connection for real-time data

## Installation

### Option 1: Development Installation

```bash
# Clone or navigate to the project directory
cd /Users/tylerplack/.openclaw/workspace-code/projects/riveterminal

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e .
```

### Option 2: Direct Installation

```bash
# If you have the source code
pip install /path/to/riveterminal

# Or if published to PyPI (future)
pip install riveterminal
```

## Running RiverTerminal

```bash
# Activate virtual environment (if using option 1)
source venv/bin/activate

# Run the application
python -m riveterminal

# Alternative
riveterminal
```

## Verification

Test your installation:

```bash
python test_basic.py
```

Expected output:
```
Testing RiverTerminal Phase 1 MVP...
==================================================
✓ All imports successful
✓ Database working - 1 watchlists found
✓ Database add operation working
✓ Database remove operation working
Testing data providers (this may take a moment)...
✓ Yahoo Finance working - AAPL: $XXX.XX
✓ News feeds working - X articles loaded
==================================================
✓ All tests passed! RiverTerminal Phase 1 MVP is ready.
```

## Quick Navigation

Once running:

### F-Key Navigation
- **F1**: Dashboard (market overview)
- **F2**: Quote screen (individual stocks)
- **F3**: Watchlist (your saved stocks)
- **F4**: Charts (price charts)
- **F6**: News (financial news)

### Command Bar
Type commands in the top command bar:
- `AAPL` → View Apple stock quote
- `DASHBOARD` → Go to dashboard
- `NEWS` → View news feed

### General Controls
- **Q** or **Ctrl+C**: Quit application
- **R**: Refresh current screen
- **?**: Show help
- **A**: Add to watchlist (on quote screen)
- **D**: Delete from watchlist
- **Enter**: View details/open links

## Troubleshooting

### Import Errors
- Ensure all dependencies are installed: `pip install -e .`
- Check Python version: `python --version` (must be 3.12+)

### Data Provider Issues
- Internet connection required for real-time data
- Yahoo Finance is the primary data source (free, no API key needed)
- Some news feeds may be temporarily unavailable

### Terminal Display Issues
- Ensure terminal supports color and Unicode characters
- Terminal width should be at least 100 characters for best experience
- Some ASCII charts may not display properly in narrow terminals

### Database Issues
- SQLite database is created automatically in `~/.riveterminal/`
- To reset: `rm -rf ~/.riveterminal/` and restart the application

## File Locations

- **Configuration**: `~/.riveterminal/`
- **Database**: `~/.riveterminal/riveterminal.db`
- **Cache**: `~/.riveterminal/cache/`

## Development

For development work:

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