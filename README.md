# Jev × Claude: adaptive reasoning effort, decided per step

Two small terminal agents where **Jev** (TypeSafe AI's System One evaluation model, served through Vercel AI Gateway)
scores the complexity of the *next* step and sets Claude's `effort` before every API call.

- `jev_agent.py` — a Claude Code–style coding agent (Bash / Read / Write / Edit tools) with a chat-style terminal UI.
- `music_agent.py` — a music-taste analyst that reads a listening-history CSV, runs pandas analyses and writes a report.
- `generate_library.py` — builds a realistic 8-year listening history (`library.csv`) for the music agent.

Both print a status line before each Claude call, e.g.

```
Jev  LOW → MEDIUM  ✓ APPLIED
      Step 13 · next 1 generation(s) · 402 ms
```

## How it works

1. Before each Claude call, the agent sends Jev a short description of the situation
   (the task, the last tool call and its result, how many steps have run).
2. Jev answers a `score` question with four complexity criteria; the score is normalised to 0–1 and mapped to
   `low` (≤ 0.33 / < 0.4), `medium`, or `high`.
3. When the level changes, the agent appends a mid-conversation system message
   `{"role": "system", "content": [], "output_config": {"effort": "<level>"}}` — the
   `mid-conversation-output-config-2026-07-01` beta — so the effort changes **without invalidating the prompt cache**.
   The same level is also passed as the request-level `output_config.effort`.
4. Claude (`claude-opus-5`) responds with tool calls; the agent executes them and loops until the task is done.

Prompt caching is on (`cache_control` at the request level), tool output is truncated, and each run prints its
token usage and an estimated cost at the end.

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
```

Jev key (Vercel AI Gateway, https://vercel.com → your team → AI Gateway → API Keys):
either `export AI_GATEWAY_API_KEY=vck_...` or put the key on one line in a file named `.jev_key`
next to the script (see `.jev_key.example`). Never commit the real key.

## Run

Coding agent on any repository (demo uses `pallets/itsdangerous`):

```bash
git clone --depth 1 https://github.com/pallets/itsdangerous repo
cd repo
python3 ../jev_agent.py 'hi!' 'inspect this repo and find bugs'   # scripted demo: messages are typed for you
python3 ../jev_agent.py                                           # interactive
```

Music analyst:

```bash
python3 generate_library.py          # writes library.csv (~30k plays, 2016–2023)
python3 music_agent.py library.csv
```

## Measured runs

| Run | Steps | Effort levels | Tokens (in / out / cache read) | Cost |
|---|---|---|---|---|
| jev_agent, itsdangerous bug hunt | 13 | 12× LOW, then MEDIUM → HIGH | 28 / 6,157 / 146,287 | $0.38 |
| jev_agent, earlier take | 13 | LOW…HIGH…MEDIUM | 30 / 2,832 / 102,213 | $0.24 |
| music_agent, 31k-play library | 5 | 2× LOW, 3× MEDIUM | 23,391 / 7,362 / 3,500 | $0.30 |

Costs use Claude Opus 5 list prices (input $5, cache write $6.25, cache read $0.50, output $25 per MTok).
Jev calls cost ~$0.000015 each and take 400–1,000 ms.

## Notes and caveats

- Per-message effort requires a model that supports it (Claude Opus 5, Claude Fable 5.1). On other models the
  agent falls back to request-level `output_config.effort` and marks the line `REQUEST-LEVEL` instead of `APPLIED`.
- Jev's score is a judgement, not a rule: on the same task different runs produce different level sequences.
  The thresholds (0.33 / 0.66 in `jev_agent.py`, 0.4 / 0.7 in `music_agent.py`) are ours and easy to change.
- `library.csv` is synthetic. `generate_library.py` models taste arcs, favourite tracks, replays, quiet days and
  vacations, keeps release years consistent and durations fixed per track, so the data reads as a real export.
- Videos in `demos/` are screen recordings of real runs, sped up between steps with a slow-down on each Jev line.

## Files

```
jev_agent.py          coding agent (~170 lines)
music_agent.py        music analyst
generate_library.py   listening-history generator
requirements.txt
.jev_key.example      where the Jev key goes (copy to .jev_key)
demos/                short demo videos
```
