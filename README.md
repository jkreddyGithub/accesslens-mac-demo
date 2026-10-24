# AccessLens Entitlement Review Demo

A packaged Mac demo for reviewing synthetic access data. The demo records review
decisions locally and does not change real access.

## AI-assisted Python review workflow

The separate Python workflow in [main.py](./main.py) uses LangGraph, a local MCP
server over stdio, and an Ollama model. The MCP server exposes two read-only tools
that return synthetic identity metadata and risk scoring. The configured Ollama
model generates an explanation from those facts. LangGraph then pauses at a
human-review interrupt; enter `APPROVE` or `REVOKE` to resume and record the
decision in in-memory state.

This is a real MCP protocol connection to a local demo server, but the server's
data is synthetic; it does not connect to a company identity system or change
access. The browser app below is a separate demo and is not wired to this
Python workflow.

### Set up the AI workflow

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Install [Ollama](https://ollama.com/download) and ensure its local service is
running (`ollama serve` on Linux, if it is not already running). Then download
the default model:

```sh
# Needed only for the user-local Ollama install in this Codespace.
export PATH="$HOME/.local/bin:$PATH"
ollama pull qwen2.5:3b
```

Run the workflow from this folder. Using the explicit virtual-environment path
ensures the MCP server uses the project's pinned SDK rather than a system-wide
MCP 2.x installation:

```sh
.venv/bin/python main.py
```

Ollama must be reachable at `http://localhost:11434` by default. To use another
model or Ollama host, set `OLLAMA_MODEL` or `OLLAMA_BASE_URL`. For example:

```sh
ollama pull qwen2.5:1.5b
OLLAMA_MODEL=qwen2.5:1.5b python main.py
```

The MCP server is started automatically as a local child process; no separate
server command is needed. For a recording, show both MCP tool calls, the
model-generated explanation, the `PENDING_HUMAN_REVIEW` state, and the final
reviewer decision.

### Recorded walkthrough

The narrated, captioned, 56-second [MCP demo video](./accesslens-mcp-demo.mp4)
explains what MCP means, how the two synthetic read-only tools provide context,
how the local Ollama model generates an explanation, and why a human reviewer
must make the final choice. It is an animated walkthrough, not a raw screen
recording; the spoken narration was generated locally.

## Requirements

- Java 17 or newer
- macOS

## Run the demo

From this folder, run:

```sh
java -version
java -jar access-review-demo.jar
```

Keep the terminal open and visit <http://localhost:8080>.

Demo sign-in credentials and alternate-port instructions are in
[START-HERE.txt](./START-HERE.txt).

To show the browser and AI workflow in one recording, run the Java browser app
and the Python workflow in separate terminals. The two demos remain separate:
the browser app is not connected to the Python MCP/AI workflow.

If port 8080 is already in use, start the app on port 8082:

```sh
java -jar access-review-demo.jar --server.port=8082
```

Then visit <http://localhost:8082>.

## Data and source

Review data is saved locally in the `data` folder, which is intentionally
excluded from this repository. This is a demo build; the complete source and
interview documentation are distributed separately.

Use synthetic data only. Do not use these demo credentials or this application
for production access reviews.
