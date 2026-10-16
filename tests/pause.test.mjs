import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync(new URL('../public/app.js', import.meta.url), 'utf8');
const monitor = source.slice(source.indexOf('function monitorSilence('), source.indexOf('async function recognise('));

test('automatic sending respects quick and longer learner pauses', () => {
  for (const duration of [1200, 2000, 3000]) {
    let now = 1000, amplitude = .1, next, stopped = 0;
    const analyser = {getFloatTimeDomainData(samples) { samples.fill(amplitude); }};
    class AudioContext {
      createAnalyser() { return analyser; }
      createMediaStreamSource() { return {connect() {}}; }
    }
    const context = vm.createContext({state: {recording: true}, window: {AudioContext},
      $: () => ({value: String(duration)}), Float32Array,
      performance: {now: () => now}, requestAnimationFrame(fn) { next = fn; return 1; },
      finishRecording() { stopped++; },
    });
    vm.runInContext(monitor + '\nmonitorSilence({}, 0);', context);
    next();
    amplitude = 0; now = 1000 + duration - 20; next();
    assert.equal(stopped, 0, 'do not cut off a pause earlier than selected');
    now = 1000 + duration + 20; next();
    assert.equal(stopped, 1);
  }
});
