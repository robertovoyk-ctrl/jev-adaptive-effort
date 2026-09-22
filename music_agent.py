#!/usr/bin/env python3
"""
Jev-powered music taste analyzer.
Adaptive reasoning: Jev scores each step, Claude shifts LOW → MEDIUM → HIGH mid-run.

Requires:
  pip install anthropic requests rich
  export ANTHROPIC_API_KEY=your-key

Usage:
  python music_agent.py library.csv
"""

import sys, os, json, time, csv
import warnings; warnings.filterwarnings("ignore")
import anthropic, requests
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.table import Table

console = Console()

def _jev_key():
    k = os.environ.get("AI_GATEWAY_API_KEY")
    if not k:
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".jev_key")
        if os.path.exists(p): k = open(p).read().strip()
    if not k: raise SystemExit("Jev key missing: set AI_GATEWAY_API_KEY or put it in .jev_key next to this script")
    return k

JEV_KEY = _jev_key()
JEV_URL = "https://ai-gateway.vercel.sh/typesafe/v1/systemone"

SYSTEM = (
    "You are a music taste analyst. You have tools to read and analyze a CSV music library. "
    "The CSV has columns: timestamp, artist, track, genre, duration_sec, play_count. "
    "Analyze the user's listening history deeply: patterns, phases, obsessions, gaps, "
    "and predict what they'd love next. Be specific — name real artists and tracks. "
    "Be brutally honest about what the data says about them as a listener."
)

MAX_STEPS = 14

TOOLS = [
    {
        "name": "read_file",
        "description": "Read the contents of the music library CSV file. Returns first N lines.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the CSV file"},
                "max_lines": {"type": "integer", "description": "Max lines to read (default 50)", "default": 50}
            },
            "required": ["path"]
        }
    },
    {
        "name": "analyze_data",
        "description": "Run a Python analysis on the CSV and return results. Write pandas code that prints results.",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Python code using pandas. The CSV is at the path in variable LIBRARY_PATH. Print results."}
            },
            "required": ["code"]
        }
    },
    {
        "name": "final_report",
        "description": "Submit the final music taste analysis report.",
        "input_schema": {
            "type": "object",
            "properties": {
                "report": {"type": "string", "description": "The complete analysis report"}
            },
            "required": ["report"]
        }
    }
]

# ── Jev classifier ──────────────────────────────────────────────
def classify_step(messages, tool_name=None):
    """Ask Jev to score this step 0-1, map to reasoning effort."""
    try:
        # describe the situation Jev has to judge: what just happened (last tool call + result), not the user's wording
        last_content = "(starting: open the library file)"
        last_tool = None
        for m in reversed(messages):
            c = m.get("content")
            if m["role"] == "assistant" and not isinstance(c, str):
                for block in c:
                    if getattr(block, "type", None) == "tool_use":
                        last_tool = f"{block.name}: {str(block.input.get('code') or block.input.get('path') or '')[:160]}"
                if last_tool: break
        if last_tool:
            res = ""
            for m in reversed(messages):
                c = m.get("content")
                if m["role"] == "user" and isinstance(c, list) and c and isinstance(c[0], dict) and c[0].get("type") == "tool_result":
                    res = str(c[0].get("content", ""))[:160]; break
            last_content = f"last step {last_tool} -> {res}"

        n_steps = len([m for m in messages if m["role"] == "assistant"])
        criteria = ["Trivial: open the file, look at the first rows, count things",
                    "Routine: a standard groupby / top-N summary",
                    "Moderate: compare periods, find phases or shifts in taste",
                    "Complex: synthesise everything into insights and specific predictions"]
        resp = requests.post(JEV_URL, json={
            "model": "typesafe-ai/jev",
            "state": f"Music-library analysis. Steps done: {n_steps}. Latest context: {last_content}",
            "questions": {"complexity": {"type": "score",
                                         "instructions": "Rate the complexity of the NEXT analysis step from 0 to 1.",
                                         "criteria": criteria}}
        }, headers={"Authorization": f"Bearer {JEV_KEY}"}, timeout=15)
        resp.raise_for_status()
        score = resp.json()["answers"]["complexity"]["score"] / (len(criteria) - 1)
    except Exception as e:
        console.print(f"  [yellow]Jev unavailable ({str(e)[:60]}), defaulting to low[/]")
        score = 0.3

    if score < 0.4:
        return "low", score
    elif score < 0.7:
        return "medium", score
    else:
        return "high", score

# ── Tool execution ──────────────────────────────────────────────
def execute_tool(name, inp, library_path):
    if name == "read_file":
        path = inp.get("path", library_path)
        max_lines = inp.get("max_lines", 50)
        try:
            with open(path) as f:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        break
                    lines.append(line.rstrip())
            return f"[{len(lines)} lines read]\n" + "\n".join(lines)
        except Exception as e:
            return f"Error: {e}"

    elif name == "analyze_data":
        code = inp["code"]
        import subprocess, tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(f'LIBRARY_PATH = "{library_path}"\n')
            f.write("import pandas as pd\nimport numpy as np\n")
            f.write(code)
            tmp = f.name
        try:
            result = subprocess.run(
                ["python3", tmp], capture_output=True, text=True, timeout=30
            )
            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]: {result.stderr[-500:]}"
            return output[:3000] if output else "(no output)"
        except subprocess.TimeoutExpired:
            return "Error: analysis timed out (30s)"
        finally:
            os.unlink(tmp)

    elif name == "final_report":
        return "Report submitted."

    return "Unknown tool."

# ── Display helpers ─────────────────────────────────────────────
EFFORT_COLORS = {"low": "green", "medium": "yellow", "high": "red bold"}

def show_step(step, effort, score, tool_name, tool_input_preview):
    color = EFFORT_COLORS.get(effort, "white")
    badge = Text(f" {effort.upper()} ", style=f"on {color.split()[0]} bold white")

    header = Text()
    header.append(f"  Step {step:>2}  ", style="bold cyan")
    header.append(badge)
    header.append(f"  score={score:.2f}  ", style="dim")
    header.append(f"→ {tool_name}", style="bold white")
    console.print(header)

    if tool_input_preview:
        preview = tool_input_preview[:120].replace("\n", " ")
        console.print(f"           {preview}", style="dim")

def show_tools():
    table = Table(title="Tools", show_header=True, header_style="bold cyan",
                  border_style="dim", padding=(0, 1))
    table.add_column("Tool", style="bold")
    table.add_column("Description", style="dim")
    for t in TOOLS:
        table.add_row(t["name"], t["description"][:60])
    console.print(table)

def prompt_box(library_path):
    """Animated task display."""
    task = f"Analyze music library: {library_path}"
    text = Text()
    console.print()
    for ch in f"  ♫  {task}":
        text.append(ch, style="bold magenta")
        console.print(text, end="\r")
        time.sleep(0.02)
    console.print()
    console.print()

# ── Main agent loop ─────────────────────────────────────────────
def run(library_path):
    console.print(Panel(
        "[bold cyan]Jev Music Analyzer[/] — adaptive reasoning for music taste",
        subtitle="typesafe-ai/jev + claude-opus-5 · effort via mid-conversation-output-config beta",
        border_style="cyan"
    ))
    show_tools()
    prompt_box(library_path)

    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": f"Analyze this music library in depth: {library_path}\n\nDig into patterns across years, find phases of taste, obsessions, abandoned artists, and predict 10 artists and specific tracks they'd love but have never listened to. Be specific and brutally honest."}]

    input_tokens_total = 0
    output_tokens_total = 0
    cache_read_total = 0
    cache_write_tokens_total = 0
    efforts = []
    step = 0

    while step < MAX_STEPS:
        step += 1

        # Jev classification
        tool_hint = None
        effort, score = classify_step(messages, tool_hint)
        if effort != (efforts[-1] if efforts else None):   # effort change: mid-conversation system message, cache stays warm
            messages.append({"role": "system", "content": [], "output_config": {"effort": effort}})
        efforts.append(effort)

        # Call Claude with adaptive effort
        try:
            response = client.beta.messages.create(
                model="claude-opus-5",
                max_tokens=16000,
                system=[{
                    "type": "text",
                    "text": SYSTEM,
                    "cache_control": {"type": "ephemeral"}
                }],
                tools=TOOLS,
                messages=messages,
                betas=["mid-conversation-output-config-2026-07-01"],
                output_config={"effort": effort}
            )
        except Exception as e:
            console.print(f"  [red]API Error: {e}[/]")
            console.print("  [dim]messages: " + " | ".join(f"{i}:{m['role']}:{[getattr(b,'type',b.get('type') if isinstance(b,dict) else 'str') for b in (m['content'] if isinstance(m['content'],list) else [m['content']])]}" for i,m in enumerate(messages)) + "[/]")
            break

        # Token accounting
        usage = response.usage
        input_tokens_total += usage.input_tokens
        output_tokens_total += usage.output_tokens
        cache_read_total += getattr(usage, "cache_read_input_tokens", 0) or 0
        cache_write_tokens_total += getattr(usage, "cache_creation_input_tokens", 0) or 0

        # Process response
        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
        text_blocks = [b for b in response.content if b.type == "text"]

        if tool_use_blocks:
            results = []
            final = None
            for tool in tool_use_blocks:          # Claude may call several tools in one turn: run them all
                preview = ""
                if tool.name == "analyze_data":
                    preview = tool.input.get("code", "")[:120]
                elif tool.name == "read_file":
                    preview = f"path={tool.input.get('path', '')} lines={tool.input.get('max_lines', 50)}"
                elif tool.name == "final_report":
                    preview = "submitting report..."
                show_step(step, effort, score, tool.name, preview)
                result = execute_tool(tool.name, tool.input, library_path)
                if tool.name == "final_report":
                    final = tool.input["report"]
                results.append({"type": "tool_result", "tool_use_id": tool.id, "content": result})

            if final is not None:
                console.print()
                console.print(Panel(final, title="♫ Music Taste Analysis", border_style="magenta", padding=(1, 2)))
                break

            # Append to conversation: every tool_use gets its tool_result in the same user message
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": results})

        elif text_blocks:
            console.print()
            for b in text_blocks:
                console.print(b.text)
            break

        if response.stop_reason == "end_turn":
            break

    # Summary
    console.print()
    console.print("─" * 50)

    effort_counts = {}
    for e in efforts:
        effort_counts[e] = effort_counts.get(e, 0) + 1
    effort_str = ", ".join(f"{v}×{k.upper()}" for k, v in sorted(effort_counts.items(), key=lambda x: ["low","medium","high"].index(x[0])))

    cache_write_total = sum(1 for _ in ())  # tracked below
    total_cost = (input_tokens_total * 5 + output_tokens_total * 25 + cache_read_total * 0.5 + cache_write_tokens_total * 6.25) / 1_000_000

    console.print(f"  [cyan]Steps:[/]  {step}  ({effort_str})")
    console.print(f"  [cyan]Tokens:[/] {input_tokens_total:,} in / {output_tokens_total:,} out / {cache_read_total:,} cached")
    console.print(f"  [cyan]Cost:[/]   ${total_cost:.2f}")
    console.print("─" * 50)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        console.print("[red]Usage: python music_agent.py <library.csv>[/]")
        sys.exit(1)
    run(sys.argv[1])
