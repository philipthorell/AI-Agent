import subprocess
from pathlib import Path

import ollama

MODEL = "qwen2.5:7b"

SYSTEM_PROMPT = (
    "You are a helpful assistant with access to tools. "
    "Use them when needed to complete tasks accurately."
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_shell",
            "description": "Run a shell command and return its stdout/stderr.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to execute"},
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
        response = ollama.chat(model=MODEL, messages=history, tools=TOOLS)
        msg = response.message
        history.append(msg)

        if not msg.tool_calls:
            print(f"\nAssistant: {msg.content}\n")
            break

        for tc in msg.tool_calls:
            name = tc.function.name
            args = tc.function.arguments
            print(f"  [tool call] {name}({args})")
            handler = TOOL_HANDLERS.get(name)
            result = handler(args) if handler else f"Unknown tool: {name}"
            print(f"  [tool result] {result[:200]}{'...' if len(result) > 200 else ''}")
            history.append({"role": "tool", "content": result})

    return history


def main():
    print(f"Agent ready  •  model: {MODEL}")
    print("Type 'exit' or press Ctrl+C to quit.\n")

    history = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            print("Goodbye.")
            break

        history.append({"role": "user", "content": user_input})
        history = run_agent_turn(history)


if __name__ == "__main__":
    main()
