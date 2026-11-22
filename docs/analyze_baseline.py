"""Read inherited artifacts only; emit a conservative, reproducible baseline audit."""
import csv
import json
import re
import statistics
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
DOCS = ROOT / "docs"

# Reviewed against each trajectory's first user instruction, not today's grader.
MEMBERS = {
    "cooling-water-flush-plan": "flush_plan.csv chemistry_plan.csv acceptance_matrix.csv schedule.csv resources.json constraint_register.csv MOP.md",
    "data-hall-device-takeoff": "takeoff.csv locations.csv bom.csv register.csv basis.md",
    "division-26-specifications": "specs/ design_basis.xlsx",
    "eor-review-corrections": "disposition_register.csv sheet_index.csv revision_log.csv issue_plan.csv continuation_sheet.md constraint_register.xlsx design_basis.md",
    "foundation-strategy": "foundation_geometry.json ground_improvement_plan.json foundation_schedule.xlsx foundation_feasibility_matrix.md constraint_register.xlsx design_basis.md",
    "frame-extension-method": "construction_sequence.csv stability_check.csv occupancy_report.csv temporary_works.json constraint_register.csv method_note.md",
    "heat-rejection-life-cycle-cost": "CT_SCHEDULE_CUP.dxf CT_SCHEDULE_ANNEX.dxf CT_SCHEDULE_LAB.dxf CT_CALC_CUP.xlsx CT_CALC_ANNEX.xlsx CT_CALC_LAB.xlsx constraint_register.csv design_basis.md",
    "lv-cable-sizing": "wire_schedule.csv E-621_wire_schedule.dxf calc_book.xlsx design_basis.md constraint_register.xlsx",
    "mv-conveyance-study": "conveyance_study.xlsx conveyance_study_report.md|conveyance_study_report.pdf|conveyance_study_report.docx",
    "roof-deck-design": "deck_design.xlsx roof_deck_plan.dxf constraint_register.xlsx design_basis.md",
    "seismic-diaphragm-shear": "design_record.json diaphragm_plan.dxf seismic_calculations.xlsx constraint_register.xlsx design_basis.md",
    "wind-diaphragm-shear": "lateral_schedule.xlsx diaphragm_plan.dxf constraint_register.xlsx calculations.pdf design_basis.md",
}
NAMES = {
    "backfeed-energization-reply": "/filesystem/Halbray_Backfeed_Reply.docx",
    "emergency-spillway-check": "/filesystem/Memo_to_Callaway_Spillway_2026-10-31.docx",
    "engineers-estimate-check": "Correspondence/Client/Memo_to_Callaway_2026-10-31.docx",
    "fill-compaction-acceptance": "/filesystem/Thelbridge_Materials_Acceptance_Fill_Compaction_2026-0708.docx",
    "fire-solve-convergence": "/filesystem/CFDME-2025-041_transient_solve_disposition_revA.docx",
    "fire-test-validation-memo": "output/*.docx (Word memo; filename unspecified)",
    "footing-settlement-verification": "Thelbridge_Verification_Memo_Item051_BlockC.docx",
    "landscape-sheet-revision": "output/* (memo; filename unspecified)",
    "les-mesh-resolution": "/filesystem/CFDME-2025-041_resolution_note_revA.docx",
    "permission-to-operate-memo": "/filesystem/Corwyn_PTO_Memo.docx",
    "pre-application-capacity-response": "/filesystem/ALN-108_PreApplication_Response.docx",
    "shoring-design-verification": "/filesystem/Thelbridge_Verification_Memo_Item048_BlockB.docx",
    "solar-supplemental-review": "Bramwick_Commons_Screen_Memo.docx",
    "solar-witness-test-package": "Municipal_Witness_Test_Package.docx",
}
STATE = {
    "backfeed-energization-reply": "Open one OpenProject work package listing backfeed conditions",
    "permission-to-operate-memo": "Open one OpenProject work package recording determination and owners",
    "pre-application-capacity-response": "File in document-store correspondence; record case call/follow-ups; close case",
    "solar-witness-test-package": "File in document-store municipal commissioning; scheduling items; batch determination; close reconciled case",
}
DOMAINS = {
    "Mechanical": "data-hall-mep-routing fire-test-validation-memo data-hall-mep-routing-offset fire-solve-convergence les-mesh-resolution heat-rejection-life-cycle-cost cooling-water-flush-plan",
    "Structural": "eor-review-corrections wind-diaphragm-shear seismic-diaphragm-shear roof-deck-design",
    "Civil": "foundation-strategy landscape-sheet-revision data-center-site-model engineers-estimate-check footing-settlement-verification frame-extension-method fill-compaction-acceptance shoring-design-verification emergency-spillway-check",
    "Electrical": "solar-supplemental-review solar-witness-test-package mv-conveyance-study data-hall-device-takeoff division-26-specifications pre-application-capacity-response permission-to-operate-memo backfeed-energization-reply lv-cable-sizing",
}
SELF_CHECK = re.compile(r"own checks.*pass|passes every check|checks pass|All checks pass|own re-analysis.*passes|own geometry and code checks pass", re.I)


def line_ref(path, text):
    for number, line in enumerate(path.read_text().splitlines(), 1):
        if text in line:
            return f"{path.relative_to(ROOT)}:{number}"
    raise ValueError(f"Evidence not found: {path}: {text}")


def member_present(required, members):
    return any(any(m.startswith(option) if option.endswith("/") else m == option
                   for m in members) for option in required.split("|"))


def analyze():
    manifest_path = ARTIFACTS / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    rows = []
    for task, entry in sorted(manifest["tasks"].items()):
        base = ARTIFACTS / task
        trajectory = base / "trajectory.json"
        data = json.loads(trajectory.read_text())
        instruction = data["steps"][0]["message"]
        final = (base / "final_message.md").read_text()
        produced = sorted("/" + name for name in entry["files"])
        archive = next((name for name in entry["files"] if name.endswith("/submission.zip")), None)
        members = []
        if archive:
            with zipfile.ZipFile(base / "files" / archive) as package:
                members = [name for name in package.namelist() if not name.endswith("/")]
        if task in MEMBERS:
            expected = MEMBERS[task].split()
            required_path = re.search(r"`(/[^`]+/output/submission\.zip)`", instruction)[1]
            required = required_path + " [members: " + "; ".join(expected) + "]"
            missing = [name for name in expected if not member_present(name, members)]
            present = int(required_path in produced)
            detail = f"archive {present}/1; member requirements {len(expected)-len(missing)}/{len(expected)}"
            if task == "division-26-specifications":
                detail += "; 6 spec sections present; section completeness not audited"
        elif task.startswith("data-hall-mep-routing"):
            required, missing = "output/solution.py (self-contained generator; IFC at argv[1])", []
            present = int(any(name.endswith("/output/solution.py") for name in produced))
            detail = f"generator {present}/1; generated IFC not exported; no re-execution in this audit"
        elif task == "data-center-site-model":
            required, missing = "submission/model.ifc", []
            present = int(any(name.endswith("/submission/model.ifc") for name in produced))
            detail = f"IFC {present}/1; not independently regraded"
        else:
            required, missing = NAMES[task], []
            pattern = required.split(" (")[0]
            if "*" in pattern:
                present = int(any(Path(name).match("*/" + pattern) for name in produced))
            else:
                present = int(any(name == pattern if pattern.startswith("/") else name.endswith("/" + pattern)
                                  for name in produced))
            detail = f"required document {present}/1; content not independently regraded"
        metrics = data.get("final_metrics", {})
        category = "missing deliverable" if not present else "other"
        score = entry.get("reward", "")
        reason = "No causal grader diagnostics exported; score alone cannot identify a calculation/revision/MCP error"
        if not present:
            reason = "Required outer file absent in export; last step unfinished; termination reason not recorded"
        elif score == 1:
            reason = "No score shortfall recorded; other does not denote a proven failure"
        elif task.startswith("data-hall-mep-routing"):
            reason = "Zero recorded reward despite generator and self-check claims; failed gate/cause unverified"
        elif missing:
            category, reason = "missing deliverable", "Archive member missing: " + "; ".join(missing)
        notes = []
        if SELF_CHECK.search(final):
            notes.append("self-check success claim (not independent verification)")
        if task == "seismic-diaphragm-shear":
            notes.append("admits omitted erection deflection case; applicability and score impact unverified")
        if task == "solar-witness-test-package":
            notes.append("last observation: Unauthenticated direct OpenProject requests; no completed package")
        if task in STATE:
            notes.append("external state required; not inferred from local files alone")
        evidence = [line_ref(manifest_path, f'"{task}": {{'), line_ref(trajectory, '"step_id": 1,')]
        if SELF_CHECK.search(final):
            evidence.append(line_ref(base / "final_message.md", SELF_CHECK.search(final)[0]))
        rows.append(dict(
            task=task, task_id=task, discipline=next(k for k, v in DOMAINS.items() if task in v.split()),
            config="baseline (template)", model="google-cloud/claude-opus-5-5", repeat=entry["run"],
            score=score, prompt_tokens=metrics.get("total_prompt_tokens", ""),
            completion_tokens=metrics.get("total_completion_tokens", ""),
            cached_tokens=metrics.get("total_cached_tokens", ""), cost_usd="", time_seconds="",
            turns=sum(s["source"] == "agent" for s in data["steps"]),
            turn_definition="ATIF agent steps; not API calls", tool_calls=sum(len(s.get("tool_calls", [])) for s in data["steps"]),
            ended=entry.get("ended", ""), deliverables_required=required,
            deliverables_produced="; ".join(produced), archive_members="; ".join(members),
            deliverable_comparison=detail, required_external_actions=STATE.get(task, ""),
            failure_category=category, assessment=reason, observations="; ".join(notes),
            evidence="; ".join(evidence),
        ))
    return manifest, rows


def main():
    manifest, rows = analyze()
    path = DOCS / "dev_baseline_analysis.csv"
    with path.open("w", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    scores = [row["score"] for row in rows]
    claims = [row for row in rows if "self-check success" in row["observations"]]
    report = f"""# Inherited baseline audit — not a run of our harness

Source: `artifacts/manifest.json`, created {manifest['created']}; template commit
`{manifest['harness']['commit']}`, model `{manifest['harness']['model_api']}`.
All {len(rows)} recorded rewards belong to that template run (`b96-r1`), not our modified
harness. The current kit warns that its dev-set revision differs. Mean recorded reward:
**{statistics.mean(scores):.6f}**, {scores.count(0.0)} zeroes, {scores.count(1.0)} perfect scores.
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
   Evidence: {line_ref(ARTIFACTS/'foundation-strategy'/'trajectory.json', '"step_id": 73,')};
   {line_ref(ARTIFACTS/'solar-witness-test-package'/'trajectory.json', '"step_id": 22,')}.
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

3. **{len(claims)}/29 final messages match explicit self-check-success language, yet all
   have recorded reward <= {max(r['score'] for r in claims):.6f}.**
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
   Evidence: {line_ref(ARTIFACTS/'pre-application-capacity-response'/'trajectory.json', '"step_id": 90,')};
   {line_ref(ARTIFACTS/'solar-witness-test-package'/'trajectory.json', '"step_id": 22,')}.
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
"""
    (DOCS / "dev_baseline_analysis.md").write_text(report)
    print(f"wrote {len(rows)} tasks; mean recorded template reward {statistics.mean(scores):.6f}")
    print(f"self-check claim cohort: {len(claims)}; missing required outer file: {sum(r['failure_category']=='missing deliverable' for r in rows)}")


if __name__ == "__main__":
    main()
