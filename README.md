# Input Tracker (Mouse + Keyboard)

A small desktop tool that can:

- Show real-time mouse pixel coordinates (`X`, `Y`)
- Record mouse and keyboard actions
- Save recorded logs to `.jsonl`, `.json`, or `.txt`

## Requirements

- Windows (tested workflow)
- [uv](https://docs.astral.sh/uv/)

## Install (uv)

```powershell
uv sync
```

## Run (uv)

```powershell
uv run input-tracker
```

Alternative:

```powershell
uv run python input_tracker.py
```

## How to use

1. Open the app.
2. Click `Start Recording` or press `F8`.
3. Perform mouse and keyboard actions.
4. Click `Stop Recording` or press `F8` again.
5. Click `Save Log` or press `F9` to export.

## Save location

- Logs are saved automatically to `./log` under the current runtime directory.
- Filename format: `input_log_YYYYMMDD_HHMMSS.jsonl`

## Log format

Each event includes:

- `timestamp`
- `elapsed_seconds`
- `device` (`mouse` or `keyboard`)
- `action` (`move`, `click`, `scroll`, `press`, `release`)
- `detail` (event-specific data)
