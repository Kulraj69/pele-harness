# Pi engineering harness

**Status: not yet evaluated on the dev set.** Offline mock checks validate
plumbing, not engineering accuracy or model performance. `artifacts/` contains
inherited upstream outputs, not outputs from this modified harness. They are
stale and must be regenerated before submission.

An offline audit of the inherited run, with conservative per-task classifications
and recorded template-only scores, is in `docs/dev_baseline_analysis.md` and `.csv`.
It is not an evaluation of this harness's changes; agent costs are unrecorded.

## Design

The baseline remains Pi 1.1.0 on `google-cloud/claude-opus-5-5`.
`serve.py` accepts the competition WebSocket session through `taskbridge.py`.
`harness.py` starts an isolated headless Pi session with the task instruction,
model endpoint, and engineering workflow addendum. `task-tools.ts` redirects
read/write/edit/bash into the task container; MCP servers use the same relay.

The addendum prioritizes inventory, an exact deliverable checklist outside graded
directories, governing revisions, MCP discovery, scripted calculations and units,
early drafts, and re-opening outputs. Final text supplements required files.
Grounding: the kit's `docs/protocol.md` and `docs/artifacts.md` (only declared
deliverables are graded and some graders ignore final messages), the template's
`AGENTS.md`, and the public starter notebook's reported missing-file and
post-repair verification failures. These are motivations, not evidence of gains.

`verification.mjs`, registered by `task-tools.ts`, queues a follow-up on the first
`agent_end` only. `VERIFICATION_PASSES: "1"` in `submission.yaml` enables it;
`"0"` disables it. Positive integer values are capped at one extra pass.
It requires at least 120 seconds before the deadline passed by `harness.py`,
which already reserves 90 seconds for shutdown. Missing/invalid deadlines skip
verification. It requests an instruction/checklist audit, repairs, rechecking,
and a final summary; it does not guarantee correctness. Thinking remains `max`;
Pi's retry and compaction defaults are unchanged.

## Run with the official kit

Requires Docker and uv. From the sibling `ple` kit directory:

```sh
uv run python -m kit validate ../my-harness
uv run python -m kit build ../my-harness --rebuild
uv run python -m kit check ../my-harness
uv run python -m kit artifacts ../my-harness
```

Real model calls need `MODEL_PROXY_URL` and `MODEL_PROXY_KEY`; the kit's
LiteLLM/Vertex proxy also needs a project and Google credentials. Keep credentials
outside this repository. For dev evaluation, install Harbor with
`uv tool install harbor==0.20.0 --with websockets`, obtain approved HF dataset
access, and supply `HF_TOKEN` plus model/judge access:

```sh
uv run python eval/run.py ../my-harness --env-file /path/outside/repo/local.env
```

## Offline tests

The scripted `tools/mockproxy/` fixture is not a model and must never be used as
a competition endpoint. Start it in another terminal from this repository:

```sh
python tools/mockproxy/server.py
```

From the kit directory:

```sh
MODEL_PROXY_URL=http://localhost:4000 MODEL_PROXY_KEY=offline-mock-only \
  uv run python -m kit check ../my-harness
```

The key is a non-secret fixture value. The kit maps localhost to
`host.docker.internal`; the fixture binds `0.0.0.0` for Docker access. Do not
expose it publicly. It scripts file creation and a read on the verification turn.
The mock awaits Pi's asynchronous deferred MCP discovery; the offline MCP check
calls the actual task tool and writes its returned secret, not a canned value.

From this repository:

```sh
node --test verification.test.mjs
python -m unittest discover -s tools/mockproxy -p 'test_*.py' -v
```

Node tests cover exactly-once scheduling, disabled/invalid settings, and deadline
boundaries. Mock tests cover scripted messages and errors; the kit check exercises
Anthropic SSE, Pi, Docker, and the WebSocket/file relay.

## Files

| File | Purpose |
|---|---|
| `submission.yaml` | The model, and the install and start commands |
| `serve.py` | The WebSocket endpoint: hands each task to `harness.solve` |
| `harness.py` | Runs Pi on each task. Edit `NOTE` (prompt), `THINKING`, or `UNKNOWN_MODEL` (limits for a model Pi doesn't know) |
| `task-tools.ts` | Points Pi's `read`, `write`, `edit` and `bash` tools at the task container |
| `taskbridge.py` | The competition protocol |
| `package.json`, `package-lock.json` | Pi 1.1.0 and every package it uses, pinned. To upgrade, edit `package.json`, run `npm install --package-lock-only`, commit both |
| `artifacts/` | The dev-set artifacts the portal grades, one folder per dev task |
| `AGENTS.md` | The full rules, for a coding agent working on your entry |
