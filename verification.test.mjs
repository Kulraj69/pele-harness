import assert from 'node:assert/strict';
import test from 'node:test';
import {registerVerification, VERIFICATION_PROMPT} from './verification.mjs';

function fixture(env = {}) {
  const sent = [];
  let end;
  const pi = {
    on(event, handler) { assert.equal(event, 'agent_end'); end = handler; },
    sendUserMessage(...args) { sent.push(args); },
  };
  registerVerification(pi, {TASK_VERIFICATION_DEADLINE_MS: '500000', ...env}, () => 1000);
  return {sent, end: () => end()};
}

test('queues exactly one follow-up even if configured count exceeds one', () => {
  const f = fixture({VERIFICATION_PASSES: '5'});
  f.end(); f.end(); f.end();
  assert.deepEqual(f.sent, [[VERIFICATION_PROMPT, {deliverAs: 'followUp'}]]);
});

test('default count enables a single pass', () => {
  const f = fixture();
  f.end();
  assert.equal(f.sent.length, 1);
});

test('disabled, invalid and insufficient-budget cases never queue', () => {
  for (const env of [
    {VERIFICATION_PASSES: '0'}, {VERIFICATION_PASSES: '-1'},
    {VERIFICATION_PASSES: 'invalid'}, {TASK_VERIFICATION_DEADLINE_MS: ''},
    {VERIFICATION_PASSES: '1.5'}, {VERIFICATION_PASSES: 'Infinity'},
    {TASK_VERIFICATION_DEADLINE_MS: 'NaN'},
    {TASK_VERIFICATION_DEADLINE_MS: '120999'}, {TASK_VERIFICATION_DEADLINE_MS: '0'},
  ]) {
    const f = fixture(env);
    f.end(); f.end();
    assert.equal(f.sent.length, 0, JSON.stringify(env));
  }
});

test('exactly 120 seconds available is sufficient', () => {
  const f = fixture({TASK_VERIFICATION_DEADLINE_MS: '121000'});
  f.end();
  assert.equal(f.sent.length, 1);
});

test('missing deadline fails closed', () => {
  let handler;
  registerVerification({on: (_, cb) => { handler = cb; }, sendUserMessage: () => assert.fail('unexpected follow-up')}, {});
  handler();
});

test('an end at or after the process cutoff never queues verification', () => {
  for (const now of [500000, 500001, 600000]) {
    let handler;
    registerVerification({on: (_, cb) => { handler = cb; }, sendUserMessage: () => assert.fail('late follow-up')},
      {TASK_VERIFICATION_DEADLINE_MS: '500000'}, () => now);
    handler();
  }
});
