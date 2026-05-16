import subprocess
from pathlib import Path

import ollama
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

console = Console()

MODEL = "qwen2.5:7b"

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


def run_agent_turn(history: list) -> list:
    while True:
        with console.status("[bold green]Thinking...[/bold green]", spinner="dots"):
            response = ollama.chat(model=MODEL, messages=history, tools=TOOLS)

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
    console.print(
        f"[dim]  model: [/dim][green]{MODEL}[/green][dim]  •  type 'exit' or Ctrl+C to quit[/dim]\n"
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
        history = run_agent_turn(history)
        console.print()


if __name__ == "__main__":
    main()
