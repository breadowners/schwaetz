import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync(new URL('../public/app.js', import.meta.url), 'utf8');
const player = source.slice(source.indexOf('async function playReply('), source.indexOf('function correctionsFor('));

function harness() {
  const calls = [], audios = [], errors = [];
  const state = { generation: 0, recording: false, pendingReply: false, coach: { target: 'Brout' }, userGesture: true };
  const elements = new Map();
  const context = {
    state, AbortController, document: { hidden: false },
    $: id => { if (!elements.has(id)) elements.set(id, { checked: false }); return elements.get(id); },
    setBusy(value) { state.busy = value; }, stopAudio() { state.playing = null; },
    microphoneReady: () => true,
    showError: message => errors.push(message),
    clearError() { errors.length = 0; },
    startRecording() { calls.push('microphone'); },
    api: async (path, options) => { calls.push({path, body: JSON.parse(options.body)}); return {blob: async () => 'wav'}; },
    URL: {createObjectURL: () => 'blob:example'},
    Audio: class { constructor(url) { this.url = url; audios.push(this); } async play() {} },
  };
  context.$('hands-free').checked = true;
  vm.createContext(context); vm.runInContext(player, context);
  return { context, state, elements, calls, audios, errors };
}

test('correction audio uses the target and slower voice even when ordinary replies are muted', async () => {
  const h = harness();
  await h.context.playReply('Ech soen: Brout.', false, true);
  assert.equal(h.calls[0].path, '/api/speak');
  assert.equal(h.calls[0].body.text, 'Ech soen: Brout.'); assert.equal(h.calls[0].body.slow, true);
  assert.equal(h.audios.length, 1); assert.equal(h.state.busy, true);
  h.audios[0].onended(); assert.equal(h.state.busy, false);
  assert.equal(h.calls.includes('microphone'), true);
});

test('correction playback waits for a tap when hands-free is off or the phrase is too long', async () => {
  for (const longPhrase of [false, true]) {
    const h = harness();
    h.context.$('hands-free').checked = longPhrase;
    if (longPhrase) h.state.coach.target = 'a'.repeat(301);
    await h.context.playReply(h.state.coach.target, false, true);
    h.audios[0].onended();
    assert.equal(h.calls.includes('microphone'), false);
  }
});

test('reset while correction audio is being generated prevents stale playback', async () => {
  const h = harness(); let resolve;
  h.context.api = () => new Promise(yes => { resolve = yes; });
  const playback = h.context.playReply('Moien.', false, true);
  h.state.generation++;
  resolve({blob: async () => 'wav'}); await playback;
  assert.equal(h.audios.length, 0);
});

test('browser autoplay refusal points to Listen and leaves the correction available', async () => {
  const h = harness();
  h.context.Audio = class { async play() { const error = new Error(); error.name = 'NotAllowedError'; throw error; } };
  await h.context.playReply('Moien.', false, true);
  assert.match(h.errors[0], /Tap Listen/); assert.equal(h.state.busy, false);
  assert.equal(h.state.coach.target, 'Brout');
});

test('sound correction can speak while the independent tutor request is pending', async () => {
  const h = harness(); h.state.pendingReply = true;
  await h.context.playReply('Ech soen: Brout.', false, true);
  assert.equal(h.audios.length, 1);
  assert.equal(h.calls[0].path, '/api/speak');
  assert.equal(h.state.pendingReply, true);
});

test('a blocked clip can replay synchronously on a tap and later replies reuse the permitted player', async () => {
  const h = harness();
  let permitted = false, attempts = 0;
  h.context.Audio = class {
    constructor() { h.audios.push(this); }
    async play() {
      attempts++;
      if (!permitted) { const error = new Error(); error.name = 'NotAllowedError'; throw error; }
    }
  };
  await h.context.playReply('Moien.', false, true);
  assert.equal(attempts, 1);
  assert.equal(h.state.playing, null, 'a rejected player must not appear to be speaking');
  permitted = true;
  const replay = h.context.playReply('Moien.', false, true);
  assert.equal(attempts, 2, 'play must be called before leaving the tap handler');
  await replay;
  assert.equal(h.errors.length, 0, 'successful manual playback clears the autoplay message');
  assert.equal(h.calls.filter(c => c.path === '/api/speak').length, 1, 'reuse the ready clip');
  await h.context.playReply('Merci.', false, true);
  assert.equal(h.audios.length, 1, 'keep the same element for subsequent automatic replies');
  assert.equal(attempts, 3);
});

test('changing voice speed generates a new clip instead of replaying the old speed', async () => {
  const h = harness();
  await h.context.playReply('Moien.', false);
  h.context.$('slow-voice').checked = true;
  await h.context.playReply('Moien.', false);
  const requests = h.calls.filter(c => c.path === '/api/speak');
  assert.deepEqual(requests.map(c => c.body.slow), [false, true]);
  assert.equal(h.audios.length, 1);
});
