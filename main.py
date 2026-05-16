import subprocess
from pathlib import Path

import ollama
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text

console = Console()

DEFAULT_MODEL = "qwen2.5:7b"

SYSTEM_PROMPT = (
    "You are a helpful assistant with access to tools. "
    "Use them when needed to complete tasks accurately."
)

BANNER = """\
     ██╗ █████╗  ██████╗ ███████╗██████╗ ██████╗  ██████╗ ████████╗
     ██║██╔══██╗██╔════╝ ██╔════╝██╔══██╗██╔══██╗██╔═══██╗╚══██╔══╝
     ██║███████║██║  ███╗█████╗  ██████╔╝██████╔╝██║   ██║   ██║
██   ██║██╔══██║██║   ██║██╔══╝  ██╔══██╗██╔══██╗██║   ██║   ██║
╚█████╔╝██║  ██║╚██████╔╝███████╗██║  ██║██████╔╝╚██████╔╝   ██║
 ╚════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═════╝  ╚═════╝    ╚═╝   """

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_shell",
            "description": "Run a shell command and return its stdout/stderr.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Shell command to execute",
                    },
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read and return the contents of a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file, creating it if it does not exist.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file"},
                    "content": {"type": "string", "description": "Content to write"},
                },
                "required": ["path", "content"],
            },
        },
    },
]


def run_shell(command: str) -> str:
    result = subprocess.run(
        command, shell=True, capture_output=True, text=True, timeout=30
    )
    return (result.stdout + result.stderr).strip() or "(no output)"


def read_file(path: str) -> str:
    return Path(path).read_text()


def write_file(path: str, content: str) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return f"Wrote {len(content)} bytes to {path}"


TOOL_HANDLERS = {
    "run_shell": lambda args: run_shell(**args),
    "read_file": lambda args: read_file(**args),
    "write_file": lambda args: write_file(**args),
}


def select_model() -> str:
    try:
        models = ollama.list().models
    except Exception:
        console.print(
            "[bold red]Could not connect to Ollama. Is it running?[/bold red]"
        )
        raise SystemExit(1)

    if not models:
        console.print(
            "[bold red]No local models found. Pull one with 'ollama pull <name>'.[/bold red]"
        )
        raise SystemExit(1)

    names = [m.model for m in models]
    default = DEFAULT_MODEL if DEFAULT_MODEL in names else None

    console.print("[bold]Available models:[/bold]")
    for i, name in enumerate(names, 1):
        tag = " [dim](default)[/dim]" if name == default else ""
        console.print(f"  [cyan]{i}.[/cyan] {name}{tag}", highlight=False)
    console.print()

    while True:
        if default:
            prompt = Text.assemble(
                ("Select model", "bold cyan"),
                (" (Enter for ", "dim"),
                (default, "green"),
                ("):", "dim"),
                " ",
            )
        else:
            prompt = Text.assemble(
                ("Select model", "bold cyan"),
                (f" (enter 1–{len(names)}):", "dim"),
                " ",
            )
        raw = console.input(prompt).strip()

        if not raw:
            if default:
                return default
            console.print(
                f"[yellow]No default available — pick a number between 1 and {len(names)}.[/yellow]"
            )
            continue

        if raw.isdigit() and 1 <= int(raw) <= len(names):
            return names[int(raw) - 1]

        console.print(
            f"[yellow]Invalid choice. Enter a number between 1 and {len(names)}.[/yellow]"
        )


def run_agent_turn(history: list, model: str) -> list:
    while True:
        with console.status("[bold green]Thinking...[/bold green]", spinner="dots"):
            response = ollama.chat(model=model, messages=history, tools=TOOLS)

        msg = response.message
        history.append(msg)

        if not msg.tool_calls:
            console.print(
                Panel(
                    msg.content,
                    title="[bold green]Jägerbot[/bold green]",
                    border_style="green",
                    padding=(1, 2),
                )
            )
            break

        for tc in msg.tool_calls:
            name = tc.function.name
            args = tc.function.arguments
            console.print(f"  [bold yellow]⚡ {name}[/bold yellow] [dim]{args}[/dim]")
            handler = TOOL_HANDLERS.get(name)
            result = handler(args) if handler else f"Unknown tool: {name}"
            preview = result[:300] + ("..." if len(result) > 300 else "")
            console.print(f"  [bold blue]↳[/bold blue] [dim]{preview}[/dim]")
            history.append({"role": "tool", "content": result})

    return history


def main():
    console.print(Rule(style="green"))
    console.print(f"[bold green]{BANNER}[/bold green]")
    console.print(
        Rule("[bold green]Jägerbot[/bold green] [dim]AI Agent[/dim]", style="green")
    )
    console.print()

    model = select_model()

    console.print(
        f"\n[dim]  model: [/dim][green]{model}[/green][dim]  •  type 'exit' or Ctrl+C to quit[/dim]\n",
        highlight=False,
    )

    history = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        try:
            user_input = console.input("[bold cyan]You:[/bold cyan] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye.[/dim]")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            console.print("[dim]Goodbye.[/dim]")
            break

        console.print()
        history.append({"role": "user", "content": user_input})
        history = run_agent_turn(history, model)
        console.print()


if __name__ == "__main__":
    main()
