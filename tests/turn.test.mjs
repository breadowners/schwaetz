import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync(new URL('../public/app.js', import.meta.url), 'utf8');
const submitSource = source.slice(source.indexOf('async function submitTurn('), source.indexOf('function cleanupMicrophone('));
const coachSource = source.slice(source.indexOf('function correctionsFor('), source.indexOf('async function submitTurn('));
const deferred = () => {
  let resolve, reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
};
const tick = () => new Promise(resolve => setImmediate(resolve));
const reply = { reply: 'Natierlech.', translation: 'Of course.', feedback: '', better_sentence: '' };

function harness() {
  const sounds = deferred(), tutor = deferred();
  const cards = [], calls = [], errors = [], played = [];
  const elements = new Map();
  const state = { busy: false, generation: 0, messages: [], selected: 'restaurant', mode: 'conversation',
    recordingURL: 'blob:first-recording', soundURLs: [], pendingReply: false };
  const context = {
    state, AbortController,
    $: id => {
      if (!elements.has(id)) elements.set(id, { value: 'chosen-model', hidden: false, checked: id !== 'hands-free', textContent: '', scrollTop: 0, scrollHeight: 1, scrollIntoView() {} });
      return elements.get(id);
    },
    clearError() {},
    stopAudio() {},
    setBusy(busy) { state.busy = busy; },
    showError(message) { errors.push(message); },
    addMessage(role, text, data) {
      const card = { role, text, data, children: [], append(child) { this.children.push(child); } };
      cards.push(card); return card;
    },
    soundFeedbackElement(data, url) { return { data, url }; },
    analysePronunciation(blob, target, signal) {
      calls.push({ task: 'sounds', blob, target, signal }); return sounds.promise;
    },
    api(path, options) { calls.push({ task: 'reply', path, options }); return tutor.promise; },
    async playReply(text) { played.push(text); state.busy = false; },
  };
  vm.createContext(context); vm.runInContext(coachSource + submitSource, context);
  return { ...context, context, sounds, tutor, cards, calls, errors, played,
    submit: (...args) => context.submitTurn(...args),
    answer: (data = reply) => tutor.resolve({ json: async () => data }) };
}

test('audio analysis and reply start together; sound evidence appears before the reply', async () => {
  const h = harness(); const recording = { type: 'audio/webm' };
  const turn = h.submit('Ech hätt gär Waasser.', false, recording);
  assert.deepEqual(h.calls.map(call => call.task), ['sounds', 'reply']);
  assert.equal(h.calls[0].blob, recording);
  assert.equal(h.calls[0].target, 'Ech hätt gär Waasser.');
  assert.equal(JSON.parse(h.calls[1].options.body).model, 'chosen-model');
  h.sounds.resolve({ summary: 'A possible vowel difference.', tips: [] }); await tick();
  assert.equal(h.cards[0].children[0].data.summary, 'A possible vowel difference.');
  assert.equal(h.cards.length, 1);
  h.answer(); await turn;
  assert.equal(h.cards[1].role, 'assistant'); assert.deepEqual(h.played, ['Natierlech.']);
});

const mismatch = { outcome: 'possible_difference', tips: [{word: 'Brout', explanation: 'Possible difference.', practice: 'Try the example.'}] };

test('sound coaching begins before a slow tutor replies and cannot discard the pending turn', async () => {
  const h = harness(); const turn = h.submit('Ech soen Brout.', false, {});
  h.sounds.resolve(mismatch); await tick();
  assert.equal(h.state.awaitingTutor, true);
  assert.equal(h.state.coach.target, 'Ech soen: Brout.');
  assert.deepEqual(h.played, ['Ech soen: Brout.']);
  await h.context.continueConversation();
  assert.equal(h.state.coach.target, 'Ech soen: Brout.');
  assert.equal(h.state.messages.length, 1);
  h.answer(); await turn;
  assert.equal(h.state.awaitingTutor, false);
  assert.equal(h.state.heldReply.reply, reply.reply);
  assert.equal(h.played.length, 1);
  await h.context.continueConversation();
  assert.deepEqual(h.played, ['Ech soen: Brout.', reply.reply]);
});

test('a reply arriving during repetition preserves the recording and queues wording after sounds', async () => {
  const h = harness(); const turn = h.submit('Ech soen Brout.', false, {});
  h.sounds.resolve(mismatch); await tick();
  h.state.recording = true; h.state.busy = true;
  h.answer({...reply, better_sentence: 'Ech hätt gär Brout.'}); await turn;
  assert.equal(h.state.recording, true); assert.equal(h.state.busy, true);
  assert.equal(h.state.coach.target, 'Ech soen: Brout.');
  assert.equal(h.state.correctionQueue[0].target, 'Ech hätt gär Brout.');
  assert.equal(h.played.length, 1);
});

test('hands-free practice can finish before the tutor; its held reply resumes when ready', async () => {
  const h = harness(); h.$('hands-free').checked = true;
  const turn = h.submit('Ech soen Brout.', false, {});
  h.sounds.resolve(mismatch); await tick();
  h.context.analysePronunciation = async () => ({outcome: 'no_clear_difference', tips: []});
  await h.context.retryCorrection('actual-repeat', h.state.generation, null);
  assert.equal(h.state.coachPractised, true);
  assert.equal(h.state.messages.length, 1);
  h.answer(); await turn;
  assert.equal(h.state.coach, null);
  assert.equal(h.state.messages.length, 2);
  assert.deepEqual(h.played, ['Ech soen: Brout.', reply.reply]);
});

test('reset aborts the tutor even when correction playback owns the current controller', async () => {
  const h = harness(); const turn = h.submit('Ech soen Brout.', false, {});
  h.sounds.resolve(mismatch); await tick();
  h.state.controller = new AbortController();
  h.state.generation++; h.state.turnController.abort();
  assert.equal(h.calls.find(c => c.task === 'reply').options.signal.aborted, true);
  h.answer(); await turn;
  assert.equal(h.state.heldReply, null); assert.equal(h.cards.length, 1);
});

test('tutor failure preserves early sound practice and allows a later retry', async () => {
  const h = harness(); const turn = h.submit('Ech soen Brout.', false, {});
  h.sounds.resolve(mismatch); await tick();
  h.tutor.reject(new Error('Tutor unavailable')); await turn;
  assert.equal(h.state.awaitingTutor, false);
  assert.equal(h.state.coach.target, 'Ech soen: Brout.');
  assert.deepEqual(h.errors, ['Tutor unavailable']);
  await h.context.continueConversation();
  assert.equal(h.state.coach, null);
  assert.match(h.errors.at(-1), /retry your last turn/);
});

test('late sound evidence from a failed turn cannot start coaching for a newer pending turn', async () => {
  const h = harness(); const turn = h.submit('Ech soen Brout.', false, {});
  h.tutor.reject(new Error('Tutor unavailable')); await turn;
  h.state.awaitingTutor = true; h.state.turnController = new AbortController();
  h.sounds.resolve(mismatch); await tick();
  assert.equal(h.cards[0].children.length, 1);
  assert.equal(h.state.coach, undefined);
  assert.equal(h.played.length, 0);
});

test('a failed reply preserves delayed sound evidence and its original recording', async () => {
  const h = harness(); const turn = h.submit('Moien.', false, {});
  h.tutor.reject(new Error('Tutor unavailable')); await turn;
  assert.equal(h.state.pendingReply, false);
  h.state.recordingURL = 'blob:new-recording';
  h.sounds.resolve({ summary: 'Your recorded sounds.', tips: [] }); await tick();
  assert.equal(h.cards[0].children[0].url, 'blob:first-recording');
  assert.deepEqual(h.errors, ['Tutor unavailable']); assert.equal(h.cards.length, 1);
});

test('a failed sound assessment is explicit and does not lose the conversation', async () => {
  const h = harness(); const turn = h.submit('Moien.', false, {});
  h.sounds.reject(new Error('Sound analysis unavailable')); h.answer(); await turn;
  assert.equal(h.cards[0].children[0].data.outcome, 'unavailable');
  assert.equal(h.cards[0].children[0].data.summary, 'Sound analysis unavailable');
  assert.equal(h.cards[1].text, 'Natierlech.');
});

test('reset aborts both requests and suppresses stale feedback and playback', async () => {
  const h = harness(); const turn = h.submit('Moien.', false, {});
  h.state.generation++; h.state.controller.abort();
  assert.equal(h.calls[0].signal.aborted, true);
  assert.equal(h.calls[1].options.signal.aborted, true);
  h.sounds.resolve({ summary: 'Stale evidence', tips: [] }); h.answer(); await turn;
  assert.equal(h.cards[0].children.length, 0); assert.equal(h.cards.length, 1);
  assert.equal(h.played.length, 0);
});

test('typed turns do not claim or request sound analysis', async () => {
  const h = harness(); const turn = h.submit('Moien.');
  assert.deepEqual(h.calls.map(call => call.task), ['reply']);
  h.answer(); await turn; assert.equal(h.cards[0].children.length, 0);
});

test('retry preserves the learner attempt without duplicating its message', async () => {
  const h = harness(); h.state.messages.push({ role: 'user', content: 'Moien.' });
  const turn = h.submit('Moien.', true); h.answer(); await turn;
  assert.equal(h.state.messages.length, 2);
  assert.equal(h.cards.length, 1); assert.equal(h.cards[0].role, 'assistant');
});

test('wording correction is spoken before the held reply; continuing resumes exactly once', async () => {
  const h = harness();
  const data = { ...reply, feedback: 'Put the separable part at the end.', better_sentence: 'Den Zuch fiert um 2 Auer fort.' };
  const turn = h.submit('Den Zuch fortfiert um 2 Auer.'); h.answer(data); await turn;
  assert.deepEqual(h.played, [data.better_sentence]);
  assert.equal(h.cards.length, 1); assert.equal(h.state.messages.length, 1);
  assert.equal(h.state.coach.target, data.better_sentence);
  await h.context.continueConversation();
  assert.deepEqual(h.played, [data.better_sentence, data.reply]);
  assert.equal(h.state.messages.length, 2); assert.equal(h.state.coach, null);
  await h.context.continueConversation(); assert.equal(h.state.messages.length, 2);
});

test('recorded sound tips play the target word and queue wording separately', async () => {
  const h = harness(); const turn = h.submit('Ech soen Brout.', false, {});
  h.sounds.resolve({ outcome: 'possible_difference', tips: [{ word: 'Brout', explanation: 'Possible vowel difference.', practice: 'Round your lips.' }] });
  h.answer({ ...reply, better_sentence: 'Ech hätt gär Brout.', feedback: 'Use this wording.' }); await turn;
  assert.equal(h.state.coach.sound, true); assert.deepEqual(h.played, ['Ech soen: Brout.']);
  await h.context.continueConversation();
  assert.equal(h.state.coach.sound, false); assert.equal(h.cards.length, 1);
  await h.context.continueConversation(); assert.equal(h.cards.length, 2);
});

test('correction repetition checks actual audio against its target without another Qwen turn', async () => {
  const h = harness(); const data = { ...reply, better_sentence: 'Moien.' };
  const turn = h.submit('Moien'); h.answer(data); await turn;
  const before = h.calls.length;
  h.context.analysePronunciation = async (blob, target) => {
    assert.equal(blob, 'retry-recording'); assert.equal(target, 'Moien.');
    return { outcome: 'no_clear_difference', tips: [] };
  };
  await h.context.retryCorrection('retry-recording', h.state.generation, null);
  assert.equal(h.calls.length, before); assert.equal(h.state.heldReply.reply, data.reply);
  assert.match(h.$('coach-result').textContent, /No clear sound mismatch/);
  assert.equal(h.state.messages.length, 1);
});

test('hands-free repeat resumes the held reply only when no clear mismatch is detected', async () => {
  for (const outcome of ['no_clear_difference', 'uncertain']) {
    const h = harness();
    h.$('hands-free').checked = true;
    h.state.coach = {target: 'Moien.'}; h.state.heldReply = reply; h.state.correctionQueue = [];
    h.context.analysePronunciation = async () => ({outcome, summary: 'Experimental result.', tips: []});
    await h.context.retryCorrection('actual-recording', h.state.generation, null);
    assert.equal(h.state.coach === null, outcome === 'no_clear_difference');
    assert.equal(h.played.includes(reply.reply), outcome === 'no_clear_difference');
    assert.equal(h.calls.length, 0);
  }
});

test('reset during correction analysis discards stale results and playback', async () => {
  const h = harness(); const sound = deferred();
  h.state.coach = { target: 'Ech soen: Brout.' };
  h.context.analysePronunciation = () => sound.promise;
  const attempt = h.context.retryCorrection({}, h.state.generation, null);
  h.state.generation++; h.state.coach = null;
  sound.resolve({ outcome: 'possible_difference', summary: 'Stale', tips: [{ practice: 'Stale' }] }); await attempt;
  assert.equal(h.played.length, 0); assert.equal(h.$('coach-result').textContent, '');
});

test('uncertain audio gets no invented correction and spoken correction preference is respected', async () => {
  const h = harness();
  assert.equal(h.context.correctionsFor(reply, { outcome: 'uncertain', tips: [{ word: 'Brout' }] }).length, 0);
  h.$('spoken-corrections').checked = false;
  const turn = h.submit('Moien'); h.answer({ ...reply, better_sentence: 'Moien.' }); await turn;
  assert.equal(h.played.length, 0); assert.equal(h.state.coach.target, 'Moien.');
});
