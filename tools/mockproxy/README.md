# Offline plumbing fixture

This is a scripted test double, not a language model. Its successful kit stages
prove container, SSE, Pi tool, and WebSocket plumbing only. It must never be used
for a competition submission or reported as engineering performance.

Start from any directory:

```sh
python /home/ubuntu/pele/my-harness/tools/mockproxy/server.py
```

From `/home/ubuntu/pele/ple`:

```sh
MODEL_PROXY_URL=http://localhost:4000 MODEL_PROXY_KEY=offline-mock-only \
  uv run python -m kit check ../my-harness
```

The key is an arbitrary non-secret fixture value; no authentication or external
model service is used. The kit rewrites localhost to host.docker.internal and
allows that endpoint through its local egress proxy. Bind the fixture to 0.0.0.0
so Docker can reach it. Do not expose this development server publicly.

The standard-library server implements `/v1/messages` (JSON and Anthropic SSE)
and `/v1/chat/completions` (only the kit connectivity probe). Smoke instructions
produce Pi's `write` tool call; its successful result produces a final text turn.
The harness verification follow-up produces a `read` call, then another final
text turn. The hook's exactly-once behavior is tested by `verification.test.mjs`.
An advertised `secret_word` MCP tool can likewise be called and its returned word
written. Deferred tools are searched through Pi's `codemode` tool when present.
Unknown tools, missing MCP tools and failed tool results fail explicitly.
No task files are accessed by the fixture itself.

The MCP stage still warns: Pi advertises `codemode`, but its first discovery
returns no `secret_word` tool while MCP initialization/listing is occurring.
The relay log confirms initialization and listing occurred, but no tools/call
or output file. We did not change the harness or fabricate the MCP word.

Tests: `python -m unittest -v test_server` from this directory.
Keep runtime logs outside the harness repository. Inherited artifact warnings
remain until a real dev-set evaluation replaces the upstream outputs.
