# Authorized evaluation plan (not executed)

No model keys or HF token are available. These are reproduction instructions,
not measured comparisons. Never evaluate with `tools/mockproxy`.

## Four isolated configurations

Compare the same workflow with verification disabled/enabled on Claude and
Gemini. This does **not** isolate the workflow from unchanged Pi; that needs a
separate unmodified template checkout. Keep the final submission model unchanged.

From the sibling `ple` directory, after committing the harness changes:

```sh
for variant in claude-v0 claude-v1 gemini-v0 gemini-v1; do
  git clone --no-hardlinks ../my-harness "../ablation-$variant"
done
uv run python - <<'PY'
from pathlib import Path
import yaml
for family, model in [('claude', 'claude-opus-5-5'), ('gemini', 'gemini-3.8-flash')]:
    for passes in (0, 1):
        path = Path(f'../ablation-{family}-v{passes}/submission.yaml')
        config = yaml.safe_load(path.read_text())
        config['name'] = f'pele-{family}-v{passes}'
        config['model_api'] = f'google-cloud/{model}'
        config.setdefault('env', {})['VERIFICATION_PASSES'] = str(passes)
        path.write_text(yaml.safe_dump(config, sort_keys=False))
PY
for variant in claude-v0 claude-v1 gemini-v0 gemini-v1; do
  uv run python -m kit validate "../ablation-$variant"
  git -C "../ablation-$variant" add submission.yaml
  git -C "../ablation-$variant" commit -m "Configure $variant experiment"
done
```

Use new directories; `git clone` refuses existing ones. Record the source and
variant commit SHAs, kit/dev-set revisions and exact model/judge configuration.
Commit the config in each local clone so provenance identifies the variant.
No push is necessary for local evaluation.

**Important:** setting `VERIFICATION_PASSES=0` in the host environment or the
kit's `--env-file` alone does not override `submission.yaml`. `kit/check.py`'s
`runtime()` forwards model variables and declared `sub.env`, not arbitrary host
variables. Likewise `eval/run.py --model` is only for `--url`, not an override
for a submission directory. The variant YAML is the authoritative configuration.

## Runs once access is authorized

Supply an external environment file with an authorized `MODEL_PROXY_URL`,
`MODEL_PROXY_KEY`, approved `HF_TOKEN` and appropriate `JUDGE_*` settings. Use
the same frontier judge across all variants; record its identifier. Do not put
keys in these repositories. Install the kit's documented Harbor prerequisites.

```sh
# From ple; use new output directories for every independent repeat.
for variant in claude-v0 claude-v1 gemini-v0 gemini-v1; do
  uv run python eval/run.py "../ablation-$variant" \
    --env-file /path/outside/repo/authorized.env \
    --out "../ablation-results-$variant-r1" --trials 1 --no-export
done
```

Default task selection is all 29 dev tasks. Start with a matched subset using
`--tasks task-id,task-id` if needed, then run the full set. `--trials` controls
concurrency, **not repetitions**; `--attempts` retries evaluator failures,
**not independent samples**. Repeat the command with fresh `r2`, `r3` outputs.
`--no-export` preserves each checkout's inherited `artifacts/`; the run directory
still contains its own artifacts. Those inherited files are not variant results.
For the final authorized full run on the chosen submission, omit `--no-export`,
regenerate its artifacts and review them with `kit artifacts` before committing.

Normalize actual results into the schema documented in `WRITEUP.md`, including
failed runs and actual cost (blank if unavailable). Report matched task means,
paired deltas, variability, missing files, verification skips, elapsed time and
input/output/cache tokens. Record pricing date; keep judge cost separate. Do not
claim Gemini is cheaper without comparing actual billed cost and task results.

## Gemini compatibility: source review, not an endpoint test

The installed Pi 1.1.0 serve image recognizes `google/gemini-3.8-flash` (1M
context, 65.5K maximum output, thinking and images). With evaluator-provided
`GOOGLE_GEMINI_BASE_URL`, `harness.py:provider()` selects `google-generative-ai`
and appends `/v1beta`; Pi's SDK adapter treats that as an already-versioned URL.
The registered task tools are provider-neutral. Pi's `api/google-shared.js`
converts their schemas to `functionDeclarations`, replays `toolCall` blocks as
`functionCall` and tool results as `functionResponse`, retaining thought
signatures. `api/google-generative-ai.js` converts returned calls back into Pi
`toolCall` blocks. `usesGoogleThinkingLevel()` explicitly matches Gemini 3.8 and
uses discrete levels, not a token thinking budget.

No source-level incompatibility was found with these tools. This is not proof
that the sponsored endpoint accepts every schema or that Gemini executes MCP
correctly: native Gemini transport, real tool calls, quality and cost remain
unverified. The offline fixture implements Anthropic only (plus a probe).
