# Inherited baseline audit — not a run of our harness

Source: `artifacts/manifest.json`, created 2026-10-20T03:33:56Z; template commit
`6ab05b9f5f256b4ce148c20498b255712fdfbf26`, model `google-cloud/claude-opus-5-5`.
All 29 recorded rewards belong to that template run (`b96-r1`), not our modified
harness. The current kit warns that its dev-set revision differs. Mean recorded reward:
**0.491242**, 4 zeroes, 2 perfect scores.
This is a descriptive single-run mean, not a replicated benchmark or improvement claim.

## Method and missing measurements

`dev_baseline_analysis.csv` has one row per manifest task. Required file contracts
were reviewed from each trajectory's first user instruction, not inferred from
the files that happened to exist. Exact archive members were inspected with
`zipfile`; flexible document names stay flexible. `specs/` presence is checked,
but completeness against its project task order is not established. Required
external application actions are listed separately, not treated as ordinary files.
Instruction evidence is the first user step; JSON embeds that instruction on one
physical line. CSV evidence uses repository-relative **file:line** references.

`turns` counts ATIF agent steps (including tool-only steps), not model API requests.
Token totals are recorded for **3/29** tasks only. **No model cost or whole-run
duration is recorded** in these exported trajectories/manifest: blanks mean unknown,
not zero. Engineering dollar estimates and solver runtimes in task content are
not model bills or harness durations. `ended=ok` appears for all 29, including the
two unfinished traces; it does not prove completion or rule out truncated export.
No timeout is confirmed. Discipline labels are mapped by task ID to the local kit
catalog; that catalog's revision is newer than these artifacts.

## Top observed patterns (not mutually exclusive)

1. **2/29 missing outer deliverables; both reward 0.**
   `foundation-strategy` requires a ZIP with six members, yet exports none; its
   last three steps continue design parameter searches rather than packaging.
   `solar-witness-test-package` requires a Word package plus case actions, yet
   exports none; its last recorded tool result is Unauthenticated. End-of-run
   reasons are not recorded, so neither is labeled a confirmed timeout.
   Evidence: artifacts/foundation-strategy/trajectory.json:1719;
   artifacts/solar-witness-test-package/trajectory.json:498.
   Existing early-draft/checklist guidance already targets missing files.

2. **2/29 zero-score generator tasks despite files and claimed checks.**
   Both MEP routing tasks export `solution.py`, so these are not missing-file
   failures. Both final messages claim successful schema/clash checks and admit
   guessed IFC types/property names. Runtime, extraction, geometry/semantic gates
   and compliance remain possibilities; no actual failing gate is identified.
   Evidence: `artifacts/data-hall-mep-routing/final_message.md:1,28-36`;
   `artifacts/data-hall-mep-routing-offset/final_message.md:1,18`.
   Do not present a schema/clash/connectivity hypothesis as a confirmed cause
   without a grader report or independent re-execution.

3. **9/29 final messages match explicit self-check-success language, yet all
   have recorded reward <= 0.382609.**
   These are the two routing tasks, device takeoff, Division 26 specifications,
   EOR corrections, MV conveyance, roof deck, seismic and wind diaphragm tasks.
   This is a reproducible text-cohort observation, not proof that the checks
   themselves were wrong. EOR checks include clause existence; takeoff checks
   validate arithmetic without independently establishing device counts.
   Evidence: `artifacts/eor-review-corrections/final_message.md:1`;
   `artifacts/data-hall-device-takeoff/final_message.md:1`;
   `artifacts/roof-deck-design/final_message.md:1`.
   New guidance: audit assumptions against source evidence, not just regenerate
   numbers from the same implementation; distinguish syntax from semantics.

4. **1 explicit known-case exception accepted for cost.**
   Seismic diaphragm reports 4.4–4.7 in versus a 4.0 in limit and declines a
   $5–6k repair; reward is 0.315966. The agent says the case is not listed, so
   its governing applicability and contribution to the score remain unverified.
   Evidence: `artifacts/seismic-diaphragm-shear/final_message.md:27`.
   New guidance: establish whether a case is mandatory from source documents;
   satisfy hard constraints before optimizing cost, never guess grader leniency.

5. **4 task instructions require external application state as well as documents.**
   Backfeed/PTO require work packages; pre-application requires filing and case
   closure; witness testing requires scheduling records, filing and closure.
   Witness stops at unauthenticated direct HTTP. Counterevidence: pre-application
   explicitly reads back a closed case and identical stored bytes, yet scores
   only 0.230769. Thus external-state failure is not a general explanation of
   low scores, and `bash` calls alone do not imply MCP was unused.
   Evidence: artifacts/pre-application-capacity-response/trajectory.json:2311;
   artifacts/solar-witness-test-package/trajectory.json:498.
   New guidance: checklist required state mutations and verify persisted state;
   never substitute a proposed action in prose for an explicitly required action.

## Classification limits and figures

Primary CSV categories are **missing deliverable (2)** and **other (27)**.
Other includes two perfect runs with no shortfall; it means no proven specific
failure for that row. No calc error, ignored revision, wrong path/format, MCP
non-use or timeout is asserted from reward alone. All 11 exported ZIPs contain
the reviewed member-name requirements (including a variable `specs/` directory);
file presence is not proof of workbook/schema or engineering correctness.
No hidden task data, grader, or real engineering rerun was accessed.

`make_figures.py --results docs/dev_baseline_analysis.csv` labels the series
**baseline (template)**. Costs are unknown, so the score-cost surface displays
recorded scores with an explicit cost-unavailable notice, not fabricated zero-cost
points. The breakdown uses conservative primary labels on sub-perfect rows,
not inferred root causes. Our harness's evaluation remains TODO.

Reproduce from the repository root:

```sh
python docs/analyze_baseline.py
uv run --with matplotlib==3.10.9 python docs/make_figures.py --results docs/dev_baseline_analysis.csv
```
