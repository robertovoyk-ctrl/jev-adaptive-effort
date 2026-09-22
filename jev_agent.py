#!/usr/bin/env python3
"""jev_agent — a Claude Code-style loop where Jev (TypeSafe System One) sets Claude's reasoning effort on every step."""
import json, os, subprocess, sys, time, threading, warnings, datetime
warnings.filterwarnings("ignore")
import requests, anthropic
from rich.console import Console
from rich.text import Text

JEV_URL = "https://ai-gateway.vercel.sh/typesafe/v1/systemone"
def _jev_key():
    k = os.environ.get("AI_GATEWAY_API_KEY")
    if not k:
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".jev_key")
        if os.path.exists(p): k = open(p).read().strip()
    if not k: raise SystemExit("Jev key missing: set AI_GATEWAY_API_KEY or put it in .jev_key next to this script")
    return k

JEV_KEY = _jev_key()
MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-5")      # per-message effort beta: Opus 5 / Fable 5.1
BETA = "mid-conversation-output-config-2026-07-01"
MAX_STEPS = 14
SYSTEM = ("You are a senior code reviewer working in a terminal. Inspect the repository with a handful of tool calls "
          "(read the key source files; do not install packages or run test suites). Then finish with a concise report: "
          "the real bugs or risks you found, each with file:line and a one-line fix. Keep replies short.")
console = Console(highlight=False)
client = anthropic.Anthropic()
CWD = os.path.basename(os.getcwd())

# ---------- Jev: complexity -> effort ----------
CRITERIA = ["Trivial: list files, read one file, run a simple command, reply to a greeting",
            "Routine: small edit, standard check, follow an obvious next step",
            "Moderate: reason across a few files or interpret non-trivial output",
            "Complex: subtle bug hunting, multi-file analysis, design decisions"]

def jev_effort(task, last_action):
    state = f"User message: {task}\nLast assistant action: {last_action or '(starting)'}"
    q = {"complexity": {"type": "score", "instructions": "Rate the complexity of the NEXT step from 0 to 1.", "criteria": CRITERIA}}
    t0 = time.time()
    r = requests.post(JEV_URL, headers={"Authorization": f"Bearer {JEV_KEY}"}, json={"model": "typesafe-ai/jev", "state": state, "questions": q}, timeout=15)
    r.raise_for_status()
    score = r.json()["answers"]["complexity"]["score"] / (len(CRITERIA) - 1)
    return ("low" if score <= 0.33 else "medium" if score <= 0.66 else "high"), int((time.time() - t0) * 1000)

# ---------- tools ----------
TOOLS = [
    {"name": "Bash", "description": "Run a shell command in the working directory and return stdout/stderr.",
     "input_schema": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}},
    {"name": "Read", "description": "Read a text file (optionally a line range).",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "offset": {"type": "integer"}, "limit": {"type": "integer"}}, "required": ["path"]}},
    {"name": "Write", "description": "Write content to a file, creating or overwriting it.",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}},
    {"name": "Edit", "description": "Replace an exact string in a file with a new string (first occurrence).",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "old": {"type": "string"}, "new": {"type": "string"}}, "required": ["path", "old", "new"]}},
]

def run_tool(name, a):
    try:
        if name == "Bash":
            p = subprocess.run(a["command"], shell=True, capture_output=True, text=True, timeout=90)
            return (p.stdout + p.stderr).strip() or f"(exit {p.returncode}, no output)"
        if name == "Read":
            lines = open(a["path"], errors="replace").read().splitlines()
            off, lim = a.get("offset", 0), a.get("limit", 400)
            return "\n".join(f"{i+1:5d}| {l}" for i, l in enumerate(lines[off:off + lim], off))
        if name == "Write":
            open(a["path"], "w").write(a["content"]); return f"wrote {len(a['content'])} bytes to {a['path']}"
        if name == "Edit":
            s = open(a["path"]).read()
            if a["old"] not in s: return "ERROR: old string not found"
            open(a["path"], "w").write(s.replace(a["old"], a["new"], 1)); return f"edited {a['path']}"
    except Exception as e:
        return f"ERROR: {e}"
    return f"ERROR: unknown tool {name}"

# ---------- terminal UI ----------
DIM = "grey50"
def jev_line(prev, level, step, ms):
    console.print(); t = Text("  "); t.append("Jev  ", style="bold green")
    t.append(f"{prev.upper()} → {level.upper()}  " if prev and prev != level else f"{level.upper()}  ", style="bold white")
    t.append("✓ APPLIED", style="bold green"); console.print(t)
    console.print(Text(f"        Step {step} · next 1 generation(s) · {ms} ms", style=DIM))

class Spinner:
    def __init__(self): self.stop = threading.Event(); self.interrupted = False
    def __enter__(self):
        self.t0 = time.time(); threading.Thread(target=self._spin, daemon=True).start(); return self
    def _spin(self):
        while not self.stop.is_set():
            sys.stdout.write(f"\r  \033[2m◦ Working ({int(time.time() - self.t0)}s • esc to interrupt)\033[0m"); sys.stdout.flush(); time.sleep(0.25)
        sys.stdout.write("\r\033[K"); sys.stdout.flush()
    def __exit__(self, *_): self.stop.set(); time.sleep(0.3)

def show_tools(calls):
    """Codex-style collapsed view: reads grouped under 'Explored', commands under 'Ran' with 3 output lines."""
    reads = [(n, a) for n, a, _ in calls if n == "Read"]
    if reads:
        console.print(Text("• ", style=DIM) + Text("Explored", style="bold"))
        for _, a in reads: console.print(Text("  └ ", style=DIM) + Text("Read ", style="cyan") + Text(a["path"]))
    for n, a, out in calls:
        if n == "Read": continue
        head = a.get("command") or a.get("path", "")
        console.print(Text("• ", style=DIM) + Text("Ran " if n == "Bash" else f"{n} ", style="bold") + Text(head[:110], style="bold"))
        lines = out.splitlines() or ["(empty)"]
        for l in lines[:3]: console.print(Text("  └ " if l is lines[0] else "    ", style=DIM) + Text(l[:120], style=DIM))
        if len(lines) > 3: console.print(Text(f"    … +{len(lines) - 3} lines (ctrl + t to view transcript)", style=DIM))

def prompt_box(typed=None):
    """Input box like a CLI; if `typed` is given, animate typing it."""
    console.print(); console.print(Text("╭" + "─" * 100 + "╮", style=DIM))
    sys.stdout.write("\033[2m│\033[0m \033[1m›\033[0m "); sys.stdout.flush()
    if typed is None:
        text = input()
    else:
        for ch in typed: sys.stdout.write(ch); sys.stdout.flush(); time.sleep(0.05 if ch != " " else 0.08)
        time.sleep(0.5); sys.stdout.write("\n"); text = typed
    console.print(Text("╰" + "─" * 100 + "╯", style=DIM))
    return text

def status(level): console.print(Text(f"  Claude-Jev {level} · ~/{CWD} · {MODEL}", style=DIM))

# ---------- agent loop ----------
def report(u):  # Opus 5 list prices per MTok: input 5, cache write 6.25, cache read 0.5, output 25
    cost = (u["input_tokens"] * 5 + u["cache_creation_input_tokens"] * 6.25 + u["cache_read_input_tokens"] * 0.5 + u["output_tokens"] * 25) / 1e6
    console.print(Text(f"  tokens in {u['input_tokens']:,} · cache write {u['cache_creation_input_tokens']:,} · cache read {u['cache_read_input_tokens']:,} · out {u['output_tokens']:,} · est. ${cost:.2f}", style=DIM))

messages, current, usage = [], None, {"input_tokens": 0, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0, "output_tokens": 0}

def turn(task):
    global current
    messages.append({"role": "user", "content": task}); last_action = None
    for step in range(1, MAX_STEPS + 1):
        level, ms = jev_effort(task, last_action)
        if level != current: messages.append({"role": "system", "content": [], "output_config": {"effort": level}})
        jev_line(current, level, step, ms); current = level
        with Spinner():
            resp = client.beta.messages.create(betas=[BETA], output_config={"effort": level}, model=MODEL, max_tokens=8000,
                                               system=SYSTEM, tools=TOOLS, messages=messages, cache_control={"type": "ephemeral"})
        for k in usage: usage[k] += getattr(resp.usage, k, 0) or 0
        messages.append({"role": "assistant", "content": resp.content})
        for b in resp.content:
            if b.type == "text" and b.text.strip(): console.print(Text("• ", style=DIM) + Text(b.text.strip()))
        tool_uses = [b for b in resp.content if b.type == "tool_use"]
        if resp.stop_reason != "tool_use" or not tool_uses:
            console.print(Text(f"  done {datetime.datetime.now().strftime('%-I:%M %p')}", style=DIM)); return
        calls, results = [], []
        for tu in tool_uses:
            out = run_tool(tu.name, tu.input); calls.append((tu.name, tu.input, out))
            results.append({"type": "tool_result", "tool_use_id": tu.id, "content": out[:4000]})
            last_action = f"{tu.name} {json.dumps(tu.input)[:200]} -> {out[:200]}"
        show_tools(calls)
        if step >= MAX_STEPS - 2: results.append({"type": "text", "text": "Tool budget is almost used up: write your final findings report now."})
        messages.append({"role": "user", "content": results})
    console.print("[yellow]  step limit reached[/]")

if __name__ == "__main__":
    console.print(Text("• ", style=DIM) + Text(f"Model changed to Claude-Jev default  ({MODEL}, effort chosen per step by Jev)", style=DIM))
    scripted = sys.argv[1:]            # demo mode: messages are typed automatically; interactive otherwise
    try:
        while True:
            task = prompt_box(scripted.pop(0)) if scripted else prompt_box()
            if not task.strip(): continue
            if task.strip() in ("/exit", "exit", "q"): break
            turn(task); status(current)
            if sys.argv[1:] and not scripted: break
    except (KeyboardInterrupt, EOFError): pass
    except anthropic.APIStatusError as e: console.print(Text(f"  API error {e.status_code}: {str(e)[:120]}", style="red"))
    report(usage)
