# Jägerbot — Local AI Agent

A terminal-based AI agent that runs entirely offline on your machine using [Ollama](https://ollama.com) local models. Features a colorful TUI, multi-turn conversation, and built-in tools for shell execution and file I/O.

```
     ██╗ █████╗  ██████╗ ███████╗██████╗ ██████╗  ██████╗ ████████╗
     ██║██╔══██╗██╔════╝ ██╔════╝██╔══██╗██╔══██╗██╔═══██╗╚══██╔══╝
     ██║███████║██║  ███╗█████╗  ██████╔╝██████╔╝██║   ██║   ██║
██   ██║██╔══██║██║   ██║██╔══╝  ██╔══██╗██╔══██╗██║   ██║   ██║
╚█████╔╝██║  ██║╚██████╔╝███████╗██║  ██║██████╔╝╚██████╔╝   ██║
 ╚════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═════╝  ╚═════╝    ╚═╝
```

## Features

- **Fully local** — no API keys or internet connection required; all inference runs through Ollama
- **Model picker** — lists your locally available models at startup; defaults to `qwen2.5:7b` if present
- **Tool use** — the agent can run shell commands, read files, and write files to complete tasks
- **Rich TUI** — coloured panels, spinners, and tool-call previews via the `rich` library
- **Persistent context** — full conversation history is kept in-session so the model can follow up on prior messages

## Preview
![GIF Preview](previews/AI-Agent-Preview.gif)

## Requirements

- Python 3.12+
- [Ollama](https://ollama.com) running locally with at least one model pulled
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Python Dependencies

| Package | Purpose |
|---------|---------|
| `ollama` | Python client for the Ollama API |
| `rich` | Terminal formatting and TUI components |

## Installation

```bash
# Clone the repo
git clone <repo-url>
cd AI-Agent

# Install dependencies with uv
uv sync

# Or with pip
pip install .
```

Make sure Ollama is running and you have a model available:

```bash
ollama pull qwen2.5:7b   # default model, or any model you prefer
ollama serve             # if not already running
```

## Usage

```bash
uv run main.py
# or
python main.py
```

On startup you will be shown a list of your local Ollama models and prompted to pick one. After that, type any message and press Enter to chat.

| Command | Action |
|---------|--------|
| `exit` / `quit` | End the session |
| `Ctrl+C` | End the session |

## Built-in Tools

The agent has access to three tools it can invoke autonomously:

| Tool | Description |
|------|-------------|
| `run_shell` | Execute a shell command and return stdout/stderr (30 s timeout) |
| `read_file` | Read the contents of a file by path |
| `write_file` | Write content to a file, creating parent directories as needed |

## Project Structure

```
AI-Agent/
├── main.py          # Agent logic, TUI, tool definitions
├── pyproject.toml   # Project metadata and dependencies
└── uv.lock          # Locked dependency versions
```
