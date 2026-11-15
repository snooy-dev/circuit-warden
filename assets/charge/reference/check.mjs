import assert from 'node:assert/strict';
import './controller.js';
const Model = globalThis.ChargeTransition;
for (const start of [false, true]) {
  for (const delay of [.02, .08, .16, .3, .45]) {
    const m = new Model(); m.value = start ? 1 : 0; m.target = m.value;
    m.setActive(!start); m.update(delay);
    const before = [m.value, m.velocity];
    m.setActive(start);
    assert.deepEqual([m.value, m.velocity], before, '반전 순간 위치·속도 연속');
    m.setActive(start);
    assert.deepEqual([m.value, m.velocity], before, '같은 입력 중복');
    m.update(2);
    assert.equal(m.value, start ? 1 : 0);
  }
}
const run = hz => {
  const m = new Model();
  for (const [active, duration] of [[true,.125],[false,.125],[true,.25],[false,.5],[true,1]]) {
    m.setActive(active);
    for (let i = 0; i < duration * hz; i++) m.update(1 / hz);
  }
  return m;
};
const a = run(48), b = run(144);
assert.ok(Math.abs(a.value - b.value) < 1e-10);
assert.ok(Math.abs(a.velocity - b.velocity) < 1e-10);
const rapid = new Model();
for (let i = 0; i < 1000; i++) {
  rapid.setActive(i % 2 === 0); rapid.update(.01);
  assert.ok(rapid.value >= 0 && rapid.value <= 1 && Number.isFinite(rapid.velocity));
}
rapid.setActive(false); rapid.update(2); assert.equal(rapid.value,0);
assert.throws(() => rapid.update(NaN), RangeError);
assert.throws(() => rapid.update(-1), RangeError);
console.log('PASS: 양방향 10개 반전 시점, 중복 입력, 48/144Hz 일치, 1000회 연타, 종착점');
