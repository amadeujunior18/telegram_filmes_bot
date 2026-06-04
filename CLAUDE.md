# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# Run the bot
python bot.py

# Run unit tests (no network, no Telegram session required)
python tests/test_parser.py

# Run live metadata test (requires active Telegram session)
python tests/test_metadata.py

# Discover the CHAT_ID to put in .env
python tools/check_chats.py
```

## Environment Setup

Copy `.env-example` to `.env` and fill in:

| Variable | Description |
|---|---|
| `API_ID` / `API_HASH` | From [my.telegram.org](https://my.telegram.org) → API development tools |
| `SESSION_NAME` | Arbitrary session name (e.g. `ZumbiBot`) |
| `CHAT_ID` | Telegram chat/group ID to monitor (use `check_chats.py`) |
| `DOWNLOAD_DIR` | Final HDD path for completed downloads |
| `ENABLE_TMDB` | `True`/`False` — enables `@tmdbinfobot` enrichment |
| `WORKERS` | Parallel download connections per file (4–10 recommended) |

## Architecture

The bot is a **Telethon userbot** (not a bot token — it logs in as your personal account). It monitors a single Telegram chat for video files and downloads them sequentially into an organized media library.

### Startup flow (`bot.py`)
1. Redirects all `__pycache__` to `.py_cache/` via `sys.pycache_prefix` (keeps dirs clean)
2. Calls `init_db()` — creates `queue.db` SQLite file; resets any stalled `downloading` rows to `pending`
3. Calls `register_handlers()` — attaches Telethon event listeners
4. Starts the Telethon client and creates `download_worker()` as a background asyncio task

### Detection pipeline (per incoming media)
`handlers/messages.py` → `services/parser.py` → (optionally) `services/metadata_fetcher.py` → `services/queue_manager.py`

1. **Parser** (`parse_filename`): Runs regex analysis independently on both the filename and the message caption, then picks the better result. Detection priority: S01E01 pattern → anime `Name - NN` pattern → `EP xx` fallback → year-based movie → unknown.
2. **TMDb enrichment** (`fetch_metadata`): Only triggered when `ENABLE_TMDB=True` AND result is `unknown` or a movie without a year. Sends `/filme` or `/serie` to `@tmdbinfobot` via Telethon's `conversation()` API, uses `fuzz.token_sort_ratio ≥ 80%` to pick the best button, clicks it, and parses the detail text for official title, year, genres, and synopsis.
3. **Queue**: Confirmed items are inserted into SQLite with status `pending`.

### Download pipeline
`services/queue_worker.py` polls `queue.db` every 5s for the next `pending` item and calls `services/downloader.py:perform_download` sequentially (one file at a time).

**SSD staging**: files are written first to `%TEMP%` (fast SSD IOPS), then moved atomically to the final HDD path via `shutil.move`. This prevents HDD fragmentation and ensures contiguous writes.

**Parallel chunks** (`fast_download`): Files >20MB are downloaded using `WORKERS` concurrent asyncio tasks, each writing a 16MB chunk to a pre-allocated file on the SSD. Files <20MB use `client.download_media` directly.

**Real-time progress**: `downloader.py` exports a module-level dict `current_download_progress` (`percent`, `speed`, `etr`). The `/fila` command handler in `messages.py` reads this dict directly to show live metrics.

### Output directory structure
```
DOWNLOAD_DIR/
├── Filmes/
│   └── Name (Year)/
│       ├── Name (Year).mp4
│       └── info.txt
├── Series/
│   └── Name/
│       └── Season 01/
│           └── Name - S01E01.mp4
└── Outros/
    └── Name/
        └── Name.mp4
```

### Key modules
| File | Responsibility |
|---|---|
| `config/settings.py` | Loads `.env`, configures rotating logger at `log/bot.log` (30-day retention) |
| `config/session.py` | Instantiates the `TelegramClient` |
| `handlers/messages.py` | Three handlers: `/fila` status, file ingestion, manual "Filme"/"Série"/"Outros" override |
| `services/parser.py` | Stateless regex parser — no I/O, easy to unit-test |
| `services/metadata_fetcher.py` | Live conversation with `@tmdbinfobot`; uses fuzzy match on inline keyboard buttons |
| `services/downloader.py` | SSD staging + parallel chunk download; exports `current_download_progress` |
| `services/queue_manager.py` | SQLite CRUD for the download queue |
| `services/queue_worker.py` | Infinite asyncio loop consuming the queue |
| `utils/text_tools.py` | `clean_release_name` (strips scene tags), `sanitize_filename`, `format_time` |
| `tools/check_chats.py` | One-off script: lists recent dialogs with IDs |
| `tools/debug_imdb.py` | One-off script: manually tests the TMDb bot conversation |
