export const VERIFICATION_PROMPT = `Final engineering verification pass:
Re-read the original task instruction and your scratch deliverable checklist
(if missing, reconstruct it outside graded directories where permitted).
Verify EVERY deliverable exists, is non-empty, and has the exact required path,
filename, format, units, entities, fields, and internally consistent numbers.
Re-open files and parse applicable IFC/DXF/XLSX/CSV/JSON with Python; recompute
numeric checks in scripts. Fix gaps and recheck repaired files. Do not count
empty checks or timeouts as success. Respect task restrictions and the remaining
time budget. Then give the final summary of files, key numbers, assumptions,
and any unresolved limitations. Do not substitute this summary for files.`;

export function registerVerification(pi, env = process.env, now = Date.now) {
  let ended = false;
  pi.on('agent_end', () => {
    if (ended) return;
    ended = true;
    const passes = Number(env.VERIFICATION_PASSES ?? '1');
    const deadline = Number(env.TASK_VERIFICATION_DEADLINE_MS);
    if (!Number.isInteger(passes) || passes < 1) return;
    if (!Number.isFinite(deadline) || deadline - now() < 120_000) return;
    pi.sendUserMessage(VERIFICATION_PROMPT, {deliverAs: 'followUp'});
  });
}
