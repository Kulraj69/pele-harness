# Submission gate review

**NOT READY TO SUBMIT.** Reviewed against the locally saved `rules.md`,
`Submission Requirements.md` and `Evaluation.md` in the parent workspace.
Those competition documents take precedence over the inherited `AGENTS.md`
where its portal, model list or submission-count instructions conflict.

Fresh clone: `https://github.com/Kulraj69/pele-harness`, branch
`devin/1795400000-pele-harness`, commit
`ee6eb4530109d3c2d70fc2638dc5b53574ebe9fc`. Local follow-up fixes are separate
commits; this document is not a claim that they are pushed or submitted.

| Item | Status | Evidence / remaining work |
| --- | --- | --- |
| Root `submission.yaml`, `serve.py`, `harness.py`, README | PASS | Present in fresh clone; kit validates YAML. |
| Allowed final model; baseline retained | PASS | Pi 1.1.0, `google-cloud/claude-opus-5-5`. Experiment instructions use separate clones. |
| Software license | PASS | Root Apache-2.0 `LICENSE`; inherited copyright headers retained. |
| Writeup/documentation CC BY 4.0 winners' obligation | TODO | Root Apache software license exists; explicitly arrange documentation licensing before submission. |
| WebSocket/tool plumbing and rebuild | PASS (mock only) | Fresh `kit build --rebuild`, smoke and MCP pass after restarting the stale mock on port 4000. No engineering reasoning tested. |
| Real endpoint check and reproducibility | TODO | No model key/HF token; no modified-harness dev run. Mock success is insufficient for submission. |
| Unpacked dev artifacts | TODO | Inherited template directory exists; `kit artifacts` exits 0 but reports 28/29 usable, foundation empty, stale dev revision and changed harness. Regenerate all authorized dev outputs. Solar witness also lacks its required document in the independent audit. |
| Artifact size/file limits | PASS | Fresh clone: 26,597,206 bytes across 100 regular files; below 512 MiB and 10,000 files. |
| No artifact symlinks or Git LFS | PASS | Zero symlinks in `artifacts/`; zero tracked LFS pointer files in the repository. |
| Secrets | PASS scoped / TODO review | No tracked `.env`, private-key filename, private-key marker or common provider-token pattern found. This is not an exhaustive credential audit. GitGuardian flags inherited fixture password hashes; deliberately unchanged, not treated as live credentials. Review any future exports for credentials and restricted inputs. |
| Competition data rights/security | TODO | Preserve competition-only use. Check organizer permissions before adding/redistributing any source task data; do not infer permission from the required exported-artifact format. Inherited artifacts were not modified. |
| Writeup length and all five sections | PASS draft | 1,455 whitespace-separated words; sections follow the five Stage 1 criteria. TODO text is not completed empirical evidence. |
| Media Gallery cover | TODO | `docs/cover.png` exists; not attached to a submitted Kaggle Writeup. |
| Architecture figure | PASS draft | `docs/architecture.png` exists and is referenced. |
| Score-vs-cost figure | TODO | `docs/score-vs-cost.png` honestly shows template score only, cost unknown. Obtain real measured score/cost points. |
| 29-task failure breakdown | TODO | Template-only 29-task audit and conservative figure exist; 27 rows have no proven causal category (including two perfect runs). Obtain modified-harness failure evidence. |
| Controlled ablations, failed idea, cross-model evidence, engineer comparison | TODO | No real runs/review. `ABLATIONS.md` describes four variants; it supplies no results. |
| Project Links and final 40-character SHA | TODO | Repository URL is included in draft; pin the final evaluated commit SHA at the top once code and real artifacts are final. |
| Public repository / private App permissions | TODO | Fresh GitHub clone succeeded with this machine's Git credentials; anonymous GitHub API check was rate-limited, so public visibility and organizer App access were not independently established. Confirm public availability at competition close. |
| Judge disclosure | TODO | Record real `JUDGE_MODEL` and endpoint/setup for future dev scores, especially any local/open-weight judge; inherited scores are not ours. |
| Official Kaggle Writeup submitted before deadline | TODO | No submission made here; one team submission, editable before the deadline. Confirm current official timeline and eligibility separately. |

## Runtime and cost review

- Pi's serve-image `pi-ai/dist/types.d.ts` defines tool blocks as `toolCall`
  and stop reasons as `pending`, `stop`, `length`, `toolUse`, `error`, `aborted`,
  `deferred`. The local fix excludes both failed states from reply counts and
  summary updates; usage is still recorded. Truncated successful text can still
  be a best-effort fallback, not proof of task completion.
- Verification is first-`agent_end`, at most once, enabled only by a positive
  integer count and a finite deadline at least 120 seconds away. Missing task
  limits set deadline `0`, so verification fails closed. Fractional, nonnumeric,
  infinite and nonpositive counts disable it. Larger positive integers do not
  create additional passes.
- The deadline is task wall time minus 90 seconds, computed before catalog
  probing. `taskbridge.run_process()` enforces a single timeout for the entire
  Pi process, including queued follow-ups, and kills its process group. A short
  task reserves at most 25% in that helper; the verification check is more
  conservative and skips. Ending at/after the verification cutoff cannot start
  a pass. A pass begun earlier can be interrupted; the previous summary is
  preserved across failed/interim tool turns, but files still need real review.
- Native Anthropic `api/anthropic-messages.js` defaults cache retention to
  `short`, adds `cache_control: {type: 'ephemeral'}` to the non-OAuth system
  prompt and newest user/tool-result content block. The harness does not disable
  it. `cacheWarming: 'off'` is not the prompt-cache retention switch.
  NOTE is static within a task and the follow-up is appended as a user turn;
  neither deliberately replaces the earlier prefix. Compaction, changing MCP
  tool catalogs, endpoint policy, minimum length and cache expiry can still
  affect hits. No actual cache savings or real endpoint billing were measured.
  An instrumented mock check on the updated local harness observed ephemeral
  system/newest-block marks in all nine native requests, with identical
  system/tools/first-user prefix hashes within each smoke/MCP task, including
  the verification turn. Evidence log outside the repository:
  `/home/ubuntu/pele/verify-cache-mock.log` (hashes/marks, not retained prompts).
- Gemini tool/schema/thinking support is source-reviewed in `ABLATIONS.md`;
  a native Gemini endpoint check remains TODO.
