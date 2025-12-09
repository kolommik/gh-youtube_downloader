# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

YouTube Video Downloader — CLI-утилита на Python для скачивания видео с YouTube с выбором качества.

**Статус**: ✅ Реализация завершена

## Tech Stack

- **Python**: 3.11+
- **uv**: Управление зависимостями и запуск проекта
- **yt-dlp**: Библиотека для загрузки видео (современная альтернатива youtube-dl)
- **argparse**: CLI интерфейс
- **python-dotenv**: Управление конфигурацией

## Project Structure

```
gh-youtube_downloader/
  pyproject.toml          # uv configuration and dependencies
  .env.example            # Example configuration file
  .env                    # Local configuration (gitignored)
  src/
      downloader/
          main.py         # Main entry point - standalone CLI script
```

**Note**: Упрощенная структура - нет __init__.py и __main__.py, только main.py для простоты.

## Commands

### Running the Application

```bash
# Интерактивный режим (без параметров)
cd src
uv run python downloader/main.py

# С параметрами URL и качества
cd src
uv run python downloader/main.py --url "https://youtube.com/watch?v=..." --quality 720p

# С параметром только URL (качество выбирается интерактивно)
cd src
uv run python downloader/main.py --url "https://youtube.com/watch?v=..."

# Справка
cd src
uv run python downloader/main.py --help
```

### Development Setup

```bash
# Install dependencies
uv sync

# Run the application
cd src
uv run python downloader/main.py
```

## Core Architecture

### main.py Structure

1. **CLI Argument Parsing** (`argparse`)
   - `--url`: YouTube video URL (optional, falls back to `input()`)
   - `--quality`: Quality selection (index or resolution like "720p", optional)

2. **Video Information Extraction**
   - Fetch available formats using yt-dlp
   - Filter: only mp4 formats with both video+audio
   - Extract resolutions (1080p, 720p, 480p, etc.)

3. **Interactive Quality Selection**
   - Display numbered list of available qualities
   - User inputs number to select format
   - If `--quality` provided as CLI arg, skip interactive selection

4. **Download Manager**
   - Download selected format as mp4
   - Use original YouTube filename
   - Show download progress
   - Save to directory specified in `DOWNLOAD_DIR` from `.env`

### Configuration (.env)

```
DOWNLOAD_DIR=/path/to/downloads
```

## Implementation Notes

### Video Format Selection Logic

- Use yt-dlp's format filtering to get only mp4 formats with video+audio
- Present formats sorted by resolution (highest to lowest)
- Handle case when requested quality not available (show available options)

### Error Handling

- Invalid YouTube URL → clear error message
- Network errors → graceful failure with error message
- Missing `DOWNLOAD_DIR` → use `./downloads` as fallback
- Invalid quality parameter → fall back to interactive selection
- KeyboardInterrupt (Ctrl+C) → graceful exit with code 130

### Progress Display

- Use yt-dlp's built-in progress hooks
- Show: percentage, download speed, ETA

## Out of Scope

The following features are explicitly NOT included:
- Audio-only downloads
- Playlist downloads
- YouTube authentication/login
- Format conversion (only mp4)
- Subtitle downloads

## Dependencies (pyproject.toml)

Required packages:
- yt-dlp (modern alternative to youtube-dl)
- python-dotenv
- Standard library: argparse, os, sys
