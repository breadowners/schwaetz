import { createListeningView } from './listening-ui.js?v=15';
const $ = id => document.getElementById(id);
const icons = {
  settings: '<path d="m12 3 1.3 2.3 2.6.1 1.3 2.3-1.2 2.3 1.2 2.3-1.3 2.3-2.6.1L12 17l-1.3-2.3-2.6-.1-1.3-2.3L8 10 6.8 7.7l1.3-2.3 2.6-.1L12 3Z"/><circle cx="12" cy="10" r="2.6"/>',
  chat: '<path d="M19 11a7 7 0 0 1-7 7H5l-3 3v-9a8 8 0 0 1 8-8h2a7 7 0 0 1 7 7Z"/><path d="M7 10h7M7 13h4"/>',
  wave: '<path d="M3 10v4M7 6v12M11 3v18M15 7v10M19 5v14M23 10v4"/>',
  book: '<path d="M12 5v15M12 5C9 3 5 3 2 4v15c3-1 7-1 10 1 3-2 7-2 10-1V4c-3-1-7-1-10 1Z"/>',
  restaurant: '<path d="M4 3v7c0 3 6 3 6 0V3M7 3v18M19 3v18M19 3c-4 4-4 9 0 9"/>',
  phone: '<path d="m7 3-4 2c-1 7 9 17 16 16l2-4-5-3-2 2c-3-1-5-3-6-6l2-2-3-5Z"/>',
  train: '<rect x="5" y="3" width="14" height="15" rx="4"/><path d="M5 10h14M12 3v7M8 18l-2 3M16 18l2 3M8 14h1M15 14h1"/>',
  home: '<path d="m3 10 9-7 9 7M5 9v12h14V9M9 21v-7h6v7"/>',
  restart: '<path d="M4 8V3M4 8h5M4 8a8 8 0 1 1-1 8"/>',
  play: '<path d="m9 4 12 8-12 8V4Z"/>',
  pause: '<path d="M8 4v16M16 4v16"/>',
  volume: '<path d="m11 4-5 5H2v6h4l5 5V4ZM15 8a6 6 0 0 1 0 8M18 5a10 10 0 0 1 0 14"/>',
  arrow: '<path d="M4 12h16m-6-6 6 6-6 6"/>',
  mic: '<rect x="9" y="2" width="6" height="13" rx="3"/><path d="M5 10v2a7 7 0 0 0 14 0v-2M12 19v3M8 22h8"/>',
  stop: '<rect x="6" y="6" width="12" height="12" rx="2"/>',
  bulb: '<path d="M8 15a6 6 0 1 1 8 0v3H8v-3ZM9 22h6M8 18h8"/>',
  keyboard: '<rect x="2" y="5" width="20" height="14" rx="2"/><path d="M6 9h1m3 0h1m3 0h1m3 0h1M6 13h1m3 0h1m3 0h1m3 0h1M7 16h10"/>',
  close: '<path d="m6 6 12 12M6 18 18 6"/>',
};
function icon(name) { return `<svg viewBox="0 0 24 24" aria-hidden="true">${icons[name] || icons.chat}</svg>`; }
document.querySelectorAll('[data-icon]').forEach(el => { el.innerHTML = icon(el.dataset.icon); });

const state = { scenarios: [], selected: 'restaurant', mode: 'conversation', started: false, messages: [], status: null,
  busy: false, recording: false, recorder: null, stream: null, chunks: [], lastRecording: null,
  recordingURL: null, playing: null, audioURL: null, generation: 0, controller: null, timer: null,
  audioContext: null, monitor: null, speechAudio: null, speechClip: null,
  vocabulary: [], vocabIndex: 0, vocabGroup: '', pendingReply: false,
  userGesture: false, playedAssistant: false, soundURLs: [], customTarget: '', warmController: null,
  coach: null, heldReply: null, correctionQueue: [], awaitingTutor: false, coachPractised: false, turnController: null,
  byokKey: '', byokModels: [], byokFreeOnly: true, keyController: null };
const optionIds = ['auto-speak', 'spoken-corrections', 'slow-voice', 'show-translations', 'check-transcript', 'auto-stop', 'hands-free'];
let savedModel = '';
try {
  const saved = JSON.parse(localStorage.getItem('schwatz-settings') || '{}');
  optionIds.forEach(id => { if (typeof saved[id] === 'boolean') $(id).checked = saved[id]; });
  if (typeof saved.model === 'string') savedModel = saved.model;
  // Move the previous default to the faster free model once. Subsequent explicit
  // choices, including DeepSeek, are preserved along with local/personal models.
  if (saved.replySpeedVersion !== 1 && savedModel === 'opencode/deepseek-v4.1-flash-free') savedModel = 'opencode/glm-5.3-flash-free';
  if ([1200, 2000, 3000].includes(saved.pauseMs)) $('pause-duration').value = String(saved.pauseMs);
} catch { /* Storage may be unavailable; the app still works. */ }
function saveSettings() { savedModel = $('model-select').value; try { localStorage.setItem('schwatz-settings', JSON.stringify({ ...Object.fromEntries(optionIds.map(id => [id, $(id).checked])), model: savedModel, replySpeedVersion: 1, pauseMs: Number($('pause-duration').value) || 1200 })); } catch {} }
optionIds.forEach(id => $(id).addEventListener('change', saveSettings));
$('pause-duration').addEventListener('change', saveSettings);
$('model-select').addEventListener('change', () => { saveSettings(); updateModelInfo(); if (state.started && state.mode !== 'repeat') warmSelectedModel(); });

function updateModelInfo() {
  if (state.mode === 'listening') { $('connection-text').textContent = 'Listening'; $('runtime-label').textContent = 'INLL · original audio'; return; }
  const selected = $('model-select').value;
  const onlineSelected = (state.status?.online_models || []).includes(selected);
  const online = state.mode !== 'repeat' && onlineSelected;
  const ready = state.mode === 'repeat' ? state.status?.pronunciation_ready : state.status?.speech_ready && state.status?.conversation_ready;
  if (ready) $('connection-text').textContent = online ? 'Online' : 'Local';
  $('model-detail').textContent = selected.startsWith('byok/openrouter/')
    ? `Uses your OpenRouter key for this tab. ${state.byokFreeOnly ? 'Free models only.' : 'Your selected model may charge your provider account.'} Transcripts go to OpenRouter; audio is processed on the app server.`
    : state.status?.public_mode ? 'Connect your own API key. Audio is processed on the app server; the host does not provide conversation tokens.'
    : onlineSelected
    ? 'Free for a limited time. Your transcript and selected lesson excerpt go to OpenCode. Audio is processed on your Mac. No paid fallback.'
    : 'Conversation and audio are processed on your Mac.';
  $('runtime-label').textContent = online ? `${state.status.online_model_names?.[selected] || 'OpenCode'} · ${state.status?.public_mode ? 'server' : 'local'} audio` : state.status?.public_mode ? 'Bring your own key' : 'Local · A2.1';
}

function applyPersonalModels(status) {
  const models = state.byokModels || [];
  status.models = [...models.map(m => m.id), ...status.models];
  status.model_labels = {...status.model_labels, ...Object.fromEntries(models.map(m => [m.id, `${m.name} · ${m.free ? 'Free' : 'Paid'} · Your key`]))};
  status.online_models = [...(status.online_models || []), ...models.map(m => m.id)];
  status.online_model_names = {...status.online_model_names, ...Object.fromEntries(models.map(m => [m.id, m.name]))};
  status.conversation_ready = Boolean(status.models.length);
  if (!status.model && models.length) status.model = models[0].id;
}

function selectedScenario() { return state.scenarios.find(s => s.id === state.selected); }
function showError(message, retry = false) { $('error-text').textContent = message; $('error-box').hidden = false; $('retry-button').hidden = !retry; }
function clearError() { $('error-box').hidden = true; }
function microphoneReady() { return state.mode === 'repeat' || state.coach ? state.status?.pronunciation_ready : state.status?.speech_ready; }
function setBusy(busy, label = 'Thinking of a reply…', detail = 'Your partner is getting ready.') {
  state.busy = busy;
  $('speaking-dock').classList.toggle('correction-mode', Boolean(state.coach));
  $('mic-label').textContent = busy ? label : state.coach ? 'Record & check · optional' : 'Tap to speak';
  $('mic-detail').textContent = busy ? detail : state.coach ? 'Repeat the example to get feedback on your attempt.' : state.status?.public_mode ? 'Audio is processed on the app server.' : 'Audio is processed on your Mac.';
  if (!state.recording) $('mic-button').setAttribute('aria-label', state.coach ? 'Record and check your attempt' : 'Start recording');
  $('mic-button').classList.toggle('busy', busy);
  $('mic-button').disabled = busy || !microphoneReady() || !state.started || (state.coach?.target.length || 0) > 300;
  $('send-typed').disabled = busy || Boolean(state.coach);
  $('send-transcript').disabled = busy;
  $('model-select').disabled = busy || state.recording || state.awaitingTutor;
  $('coach-continue').disabled = busy || state.recording || (state.awaitingTutor && !state.heldReply);
  $('coach-listen').disabled = busy || !state.status?.speech_ready;
  $('type-button').hidden = state.mode === 'repeat' || Boolean(state.coach);
  $('hint-button').hidden = state.mode !== 'conversation' || Boolean(state.coach);
}
async function api(path, options = {}) {
  if (['/api/turn', '/api/warm', '/api/listening/translate'].includes(path) && state.byokKey) {
    const selected = JSON.parse(options.body || '{}').model || '';
    if (selected.startsWith('byok/openrouter/')) options = {...options, headers: {...options.headers,
      'X-Provider-Key': state.byokKey, 'X-Free-Only': String(state.byokFreeOnly)}};
  }
  const response = await fetch(path, options);
  if (!response.ok) {
    let message = `Request failed (${response.status}).`;
    try { const body = await response.json(); message = typeof body.detail === 'string' ? body.detail : 'Please check your input and retry.'; } catch {}
    throw new Error(message);
  }
  return response;
}
async function loadStatus() {
  try {
    state.status = await (await api('/api/status')).json();
    applyPersonalModels(state.status);
    const ready = state.mode === 'listening' || (state.mode === 'repeat' ? state.status.pronunciation_ready : state.status.speech_ready && state.status.conversation_ready);
    $('connection').className = `connection ${ready ? 'ready' : (state.mode === 'repeat' ? state.status.pronunciation_error : state.status.speech_error) ? 'error' : ''}`;
    $('connection-text').textContent = ready ? 'Local' : state.status.speech_loading ? 'Loading' : 'Setup needed';
    $('setup-detail').textContent = `${state.status.recognition}. ${state.status.recognition_warning || ''} ${state.status.speech_error || (state.status.speech_ready ? 'Speech ready.' : 'Speech warming up.')} ${state.status.online_models?.length ? 'Online models ready through OpenCode.' : state.status.online_loading ? 'OpenCode starting.' : state.status.online_error || ''} Sound analysis: ${state.status.pronunciation_ready ? 'ZIPA ready.' : state.status.pronunciation_error || 'Warming up.'}`;
    const previous = savedModel || (state.started ? $('model-select').value : state.status.model);
    $('model-select').replaceChildren(...state.status.models.map(name => { const option = document.createElement('option'); option.value = name; option.textContent = state.status.model_labels?.[name] || name; return option; }));
    $('model-select').value = state.status.models.includes(previous) ? previous : state.status.model;
    updateModelInfo();
    if (state.status.public_mode && !state.byokKey) $('connection-text').textContent = 'Add your key';
    if (!state.busy && !state.recording) setBusy(false);
    const needsKey = state.status.public_mode && !state.byokKey;
    $('start-button').textContent = needsKey ? 'Connect your API key' : 'Start conversation';
    $('start-button').disabled = !needsKey && (!state.status.speech_ready || !state.status.conversation_ready);
    if (state.status.public_mode) {
      $('welcome-footnote').textContent = 'Audio goes to the app server; transcripts go to your provider. Recordings are not saved.';
      $('audio-processing-note').textContent = 'Examples use synthetic Luxembourgish audio. Recordings are processed on the app server, not on your phone. Sound feedback remains experimental.';
    }
    if (!ready || !state.status.pronunciation_ready || state.status.online_loading) setTimeout(loadStatus, 4000);
  } catch {
    $('connection').className = 'connection error'; $('connection-text').textContent = 'Server disconnected';
    $('setup-detail').textContent = 'The local server is disconnected. Start it with npm run dev in speaking-app.';
    setTimeout(loadStatus, 6000);
  }
}
function renderScenarios() {
  $('scenario-select').replaceChildren(...state.scenarios.map(scenario => {
    const option = document.createElement('option'); option.value = scenario.id; option.textContent = scenario.title;
    return option;
  }));
  $('scenario-select').value = state.selected;
}
function stopAudio() {
  if (state.playing) { state.playing.pause(); state.playing.onended = null; state.playing = null; }
  if (state.audioURL) { URL.revokeObjectURL(state.audioURL); state.audioURL = null; }
}
function resetSession() {
  state.generation++;
  state.controller?.abort();
  state.turnController?.abort(); state.turnController = null;
  state.warmController?.abort(); state.warmController = null;
  state.controller = null;
  state.pendingReply = false;
  state.awaitingTutor = false; state.coachPractised = false;
  state.coach = null; state.heldReply = null; state.correctionQueue = [];
  $('coach-panel').hidden = true;
  stopAudio(); cancelRecording();
  state.speechClip = null;
  state.messages = []; state.started = false; state.userGesture = false;
  $('conversation').replaceChildren(); $('conversation').hidden = true; $('welcome').hidden = false;
  $('speaking-dock').hidden = true; $('transcript-check').hidden = true; $('type-panel').hidden = true;
  $('audio-actions').hidden = true; $('export-button').hidden = true; $('repeat-result').replaceChildren();
  if (state.recordingURL) URL.revokeObjectURL(state.recordingURL);
  state.soundURLs.forEach(url => URL.revokeObjectURL(url)); state.soundURLs = [];
  state.recordingURL = null; state.lastRecording = null;
  clearError(); setBusy(false);
}
function selectScenario(id) {
  resetSession(); state.selected = id; renderScenarios();
  const scenario = selectedScenario();
  $('scenario-title').textContent = scenario.title; $('mission').textContent = scenario.mission;
  if (state.mode === 'repeat') openRepeat();
  $('hint-button').hidden = state.mode === 'review';
}
function addMessage(role, content, data = {}) {
  const message = document.createElement('article'); message.className = `message ${role}`;
  const name = document.createElement('div'); name.className = 'message-name'; name.textContent = role === 'user' ? 'You' : 'Schwätz';
  const body = document.createElement('div'); body.className = 'message-body'; body.textContent = content;
  message.append(name, body);
  if (role === 'assistant') {
    const controls = document.createElement('div'); controls.className = 'message-controls';
    const replay = document.createElement('button'); replay.className = 'text-button'; replay.innerHTML = icon('volume') + ' Replay';
    replay.addEventListener('click', () => { state.userGesture = true; playReply(content, false); });
    const translate = document.createElement('button'); translate.className = 'text-button'; translate.textContent = 'English';
    const translation = document.createElement('p'); translation.className = 'translation'; translation.textContent = data.translation || ''; translation.hidden = !$('show-translations').checked;
    translate.addEventListener('click', () => { translation.hidden = !translation.hidden; });
    const practise = document.createElement('button'); practise.className = 'text-button'; practise.textContent = 'Practise these sounds';
    practise.addEventListener('click', () => { setMode('repeat'); useCustomTarget(content); });
    controls.append(replay, translate, practise); message.append(controls, translation);
    // Only show actionable wording feedback. Generic LLM reassurance adds clutter
    // and can incorrectly declare an uncorrected sentence grammatically sound.
    if (data.better_sentence) {
      const feedback = document.createElement('div'); feedback.className = 'wording-feedback';
      const label = document.createElement('strong'); label.textContent = 'Wording · from the transcript';
      const explanation = document.createElement('div'); explanation.textContent = data.feedback;
      feedback.append(label, explanation);
      if (data.better_sentence) {
        const better = document.createElement('div'); better.className = 'better-sentence'; better.textContent = data.better_sentence; feedback.append(better);
        const listen = document.createElement('button'); listen.className = 'text-button'; listen.textContent = 'Hear the correction';
        listen.addEventListener('click', () => playReply(data.better_sentence, false, true)); feedback.append(listen);
      }
      message.append(feedback);
    }
  }
  $('conversation').append(message);
  $('conversation').scrollTop = $('conversation').scrollHeight;
  return message;
}
async function startSession() {
  clearError(); state.userGesture = true;
  if (state.status?.public_mode && !state.byokKey) {
    $('own-key-section').open = true; $('settings-dialog').showModal(); $('provider-key').focus(); return;
  }
  if (!state.status?.speech_ready || !state.status?.conversation_ready) { showError('The models are still getting ready. Please check Settings.'); return; }
  const scenario = selectedScenario(); state.started = true;
  warmSelectedModel();
  $('welcome').hidden = true; $('conversation').hidden = false; $('speaking-dock').hidden = false;
  state.messages = [{ role: 'assistant', content: scenario.opening }];
  addMessage('assistant', scenario.opening, { translation: scenario.translation });
  $('speaking-dock').scrollIntoView({ behavior: 'smooth', block: 'end' });
  await playReply(scenario.opening, true);
}
function warmSelectedModel() {
  state.warmController?.abort();
  const controller = new AbortController(); state.warmController = controller;
  // Begin loading while the opening plays. A failed warm-up is reported by the actual turn.
  api('/api/warm', { method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model: $('model-select').value }), signal: controller.signal }).catch(() => {});
}
async function playReply(text, allowNextRecording, correction = false) {
  if (state.recording || (state.pendingReply && !allowNextRecording && !correction)) return;
  const generation = state.generation;
  stopAudio();
  if (!$('auto-speak').checked && allowNextRecording) { setBusy(false); return; }
  setBusy(true, correction ? 'Listen to the correction' : 'Speaking…', correction ? 'Then repeat the displayed phrase.' : 'Listen, then take your turn.');
  const controller = new AbortController(); state.controller = controller;
  try {
    const slow = correction || $('slow-voice').checked;
    const key = JSON.stringify({ text, slow });
    let blob = state.speechClip?.key === key ? state.speechClip.blob : null;
    if (!blob) {
      const response = await api('/api/speak', { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: key, signal: controller.signal });
      blob = await response.blob();
    }
    if (generation !== state.generation) return;
    // Keep a blocked clip ready so Replay/Listen calls play() during the tap,
    // without another network wait. Safari grants playback per media element.
    state.speechClip = { key, blob };
    const audio = state.speechAudio ||= new Audio();
    state.audioURL = URL.createObjectURL(blob); audio.src = state.audioURL; state.playing = audio;
    audio.onended = () => {
      if (generation !== state.generation) return;
      stopAudio(); setBusy(false);
      if ((allowNextRecording || (correction && state.coach?.target.length <= 300)) && microphoneReady()
          && $('hands-free').checked && state.userGesture && !document.hidden) startRecording();
    };
    audio.onerror = () => { if (generation === state.generation) { stopAudio(); setBusy(false); showError(correction ? 'Audio playback failed. Try Listen.' : 'Audio playback failed. Try Replay.'); } };
    await audio.play();
    if (generation === state.generation) {
      clearError();
      state.playedAssistant = true;
      $('coach-continue').disabled = state.recording || (state.awaitingTutor && !state.heldReply);
      $('mic-button').disabled = !microphoneReady() || (state.coach?.target.length || 0) > 300; $('mic-label').textContent = correction ? 'Record & check · optional' : 'Listening';
      $('mic-detail').textContent = correction ? 'Tap to interrupt the example and check your attempt.' : 'Tap the microphone to interrupt and reply.';
    }
  } catch (error) {
    if (error.name === 'AbortError' || generation !== state.generation) return;
    stopAudio();
    setBusy(false);
    showError(error.name === 'NotAllowedError' ? `Tap ${correction ? 'Listen' : 'Replay'} to enable audio. Safari or your browser needs a tap before playing sound.` : error.message);
  }
}
function correctionsFor(reply, sound) {
  const corrections = [];
  // Phonetic evidence comes only from actual recorded audio, never from Qwen.
  const tip = sound?.tips?.[0];
  if (sound?.outcome === 'possible_difference' && tip?.word) {
    corrections.push({ kind: 'Sound · possible difference', target: `Ech soen: ${tip.word.replace(/[.!?]+$/, '')}.`,
      explanation: `${tip.explanation} ${tip.practice}`, sound: true });
  }
  if (reply.better_sentence?.trim()) corrections.push({ kind: 'Wording · from the transcript',
    target: reply.better_sentence.trim(), explanation: reply.feedback || 'Listen to this version, then repeat it.', sound: false });
  return corrections;
}
async function beginCorrection(corrections, reply) {
  state.correctionQueue = corrections.slice(1); state.heldReply = reply;
  showCoach(corrections[0]);
  if ($('spoken-corrections').checked) await playReply(state.coach.target, false, true);
}
function showCoach(correction) {
  state.coach = correction;
  state.coachPractised = false;
  $('coach-kind').textContent = correction.kind; $('coach-target').textContent = correction.target;
  $('coach-explanation').textContent = correction.explanation;
  $('coach-attempt').hidden = true;
  for (const id of ['coach-heard', 'coach-wording-result', 'coach-result']) $(id).textContent = '';
  $('coach-practice-note').textContent = correction.target.length > 300
    ? 'Listen, then continue. Use a shorter phrase in Sounds to check an attempt.'
    : 'Repeating is optional. Record an attempt below to get feedback.';
  $('coach-continue').textContent = state.awaitingTutor && !state.heldReply ? 'Preparing reply…' : state.correctionQueue.length ? 'Next correction' : 'Continue conversation';
  $('coach-panel').hidden = false; $('type-panel').hidden = true;
  setBusy(false); $('coach-panel').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}
async function continueConversation() {
  if (!state.coach || state.recording || (state.busy && !state.playing)) return;
  if (state.awaitingTutor && !state.heldReply) return;
  stopAudio(); clearError();
  if (state.correctionQueue.length) {
    showCoach(state.correctionQueue.shift());
    if ($('spoken-corrections').checked) await playReply(state.coach.target, false, true);
    return;
  }
  const data = state.heldReply; state.coach = null; state.heldReply = null;
  $('coach-panel').hidden = true; setBusy(false);
  if (!data) { showError('Your partner could not reply. You can retry your last turn.', true); return; }
  state.messages.push({ role: 'assistant', content: data.reply });
  addMessage('assistant', data.reply, data); $('export-button').hidden = false;
  await playReply(data.reply, true);
}
async function retryCorrection(blob, generation, signal) {
  const coach = state.coach;
  const checkWording = coach.sound === false;
  const soundTask = analysePronunciation(blob, coach.target, signal).catch(error => {
    if (error.name === 'AbortError') throw error;
    return { outcome: 'unavailable', summary: error.message, tips: [] };
  });
  const transcriptTask = checkWording
    ? api('/api/transcribe', { method: 'POST', headers: { 'Content-Type': blob.type || 'audio/webm' }, body: blob, signal })
      .then(response => response.json()).catch(error => {
        if (error.name === 'AbortError') throw error;
        return { error: error.message };
      })
    : Promise.resolve(null);
  const [data, transcript] = await Promise.all([soundTask, transcriptTask]);
  if (generation !== state.generation || coach !== state.coach) return;
  setBusy(false);
  const normalise = text => text.normalize('NFC').toLowerCase().replace(/[^\p{L}\p{N}\s]/gu, '').replace(/\s+/g, ' ').trim();
  const heard = transcript?.text?.trim();
  const wordingMatches = Boolean(heard && normalise(heard) === normalise(coach.target));
  $('coach-heard').textContent = heard ? `Transcript: “${heard}” Speech recognition can mishear.` : '';
  $('coach-wording-result').textContent = !checkWording ? '' : heard
    ? wordingMatches ? 'Your transcript matches the corrected sentence.' : 'Your transcript differs from the example. Compare it with the sentence above and try again.'
    : 'The wording check was unavailable. You can still listen, try again, or continue.';
  $('coach-result').textContent = data.outcome === 'no_clear_difference'
    ? 'Sound check: No clear sound mismatch detected. This is not a pronunciation grade.'
    : `Sound check: ${data.summary || 'No reliable result was available. Please try another recording.'}`;
  // A repetition is practice, not a new conversation turn. Keep the held reply.
  const tip = data.tips?.[0];
  if (tip) $('coach-result').textContent += ` ${tip.practice}`;
  $('coach-attempt').hidden = false;
  $('coach-attempt').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  state.coachPractised = data.outcome === 'no_clear_difference' && (!checkWording || wordingMatches);
  if (state.coachPractised && $('hands-free').checked) { await continueConversation(); return; }
  if (data.outcome === 'possible_difference' && $('spoken-corrections').checked) await playReply(coach.target, false, true);
}
async function submitTurn(text, retry = false, recording = null) {
  text = text.trim(); if (!text || state.busy || state.coach) return;
  clearError(); $('transcript-check').hidden = true;
  const generation = state.generation;
  const recordingURL = state.recordingURL;
  if (recording && recordingURL && !state.soundURLs.includes(recordingURL)) state.soundURLs.push(recordingURL);
  let userMessage;
  if (!retry) {
    state.messages.push({ role: 'user', content: text }); userMessage = addMessage('user', text);
  }
  state.pendingReply = true;
  state.awaitingTutor = true;
  setBusy(true, 'Thinking of a reply…', recording ? 'Checking your sounds while your partner prepares a reply.' : 'Your conversation partner is preparing a reply.');
  const controller = new AbortController(); state.controller = controller; state.turnController = controller;
  let earlySoundCoach = false;
  try {
    // Independent audio and text analysis start together. Sound feedback still appears
    // even if the conversation request fails, and neither task can update a reset session.
    const soundTask = (async () => {
      if (!recording) return null;
      let soundFeedback;
      try { soundFeedback = await analysePronunciation(recording, text, controller.signal); }
      catch (error) {
        if (error.name === 'AbortError') throw error;
        soundFeedback = { summary: error.message, outcome: 'unavailable', tips: [] };
      }
      if (generation !== state.generation) return;
      userMessage.append(soundFeedbackElement(soundFeedback, recordingURL));
      $('conversation').scrollTop = $('conversation').scrollHeight;
      // Start sound practice as soon as local analysis finishes, even while the
      // conversation model is thinking. Never replace or infer audio evidence.
      const corrections = correctionsFor({}, soundFeedback);
      if (state.awaitingTutor && state.turnController === controller && corrections.length) {
        earlySoundCoach = true;
        await beginCorrection(corrections, null);
      }
      return soundFeedback;
    })();
    const replyTask = api('/api/turn', { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario: state.selected, messages: state.messages.slice(-24), model: $('model-select').value,
        mode: state.mode === 'review' ? 'review' : 'conversation' }), signal: controller.signal }).then(response => response.json());
    const [data, sound] = await Promise.all([replyTask, soundTask]);
    if (generation !== state.generation) return;
    state.pendingReply = false;
    state.awaitingTutor = false; state.turnController = null;
    if (earlySoundCoach && state.coach) {
      state.heldReply = data;
      state.correctionQueue = correctionsFor(data, null);
      $('coach-continue').textContent = state.correctionQueue.length ? 'Next correction' : 'Continue conversation';
      // A late text reply must not interrupt a recording or a spoken example.
      $('coach-continue').disabled = (state.busy && !state.playing) || state.recording;
      $('model-select').disabled = state.busy || state.recording;
      if (state.coachPractised && $('hands-free').checked && !state.busy && !state.recording) await continueConversation();
      return;
    }
    const corrections = correctionsFor(data, sound);
    if (corrections.length) { await beginCorrection(corrections, data); return; }
    state.messages.push({ role: 'assistant', content: data.reply });
    addMessage('assistant', data.reply, data); $('export-button').hidden = false;
    await playReply(data.reply, true);
  } catch (error) {
    if (error.name === 'AbortError' || generation !== state.generation) return;
    state.pendingReply = false;
    state.awaitingTutor = false; state.turnController = null;
    if (state.coach) $('coach-continue').textContent = 'Continue conversation';
    setBusy(false); showError(error.message, true);
  }
}
function cleanupMicrophone() {
  clearInterval(state.timer); state.timer = null;
  cancelAnimationFrame(state.monitor); state.monitor = null;
  state.stream?.getTracks().forEach(track => track.stop()); state.stream = null;
  state.audioContext?.close().catch(() => {}); state.audioContext = null;
  state.recording = false;
  $('mic-button').classList.remove('recording'); $('mic-button').innerHTML = icon('mic');
  $('mic-button').setAttribute('aria-label', 'Start recording'); $('record-clock').textContent = '';
}
function cancelRecording() {
  if (state.recorder && state.recorder.state !== 'inactive') { state.recorder.onstop = null; state.recorder.stop(); }
  state.recorder = null; cleanupMicrophone();
}
function finishRecording() {
  if (state.recorder?.state === 'recording') state.recorder.stop();
}
async function startRecording() {
  if (state.recording) { finishRecording(); return; }
  if (state.pendingReply && !state.coach) { showError('Please retry your previous reply or start a new conversation.'); return; }
  // Pressing the mic may interrupt spoken output, but must not interrupt an unfinished request.
  if (state.busy && !state.playing) return;
  if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) {
    showError('On a phone, open the private HTTPS address from the phone setup. The microphone needs HTTPS; a plain Wi-Fi IP address will not work.'); return;
  }
  if (!window.MediaRecorder) { showError('This browser cannot record audio. Please use a current Safari, Chrome, or Firefox.'); return; }
  stopAudio(); setBusy(false); clearError(); $('transcript-check').hidden = true;
  state.userGesture = true;
  const generation = state.generation;
  setBusy(true, 'Opening microphone…', '');
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true } });
    if (generation !== state.generation || document.hidden) { stream.getTracks().forEach(t => t.stop()); return; }
    state.stream = stream;
    const mime = ['audio/webm;codecs=opus', 'audio/mp4', 'audio/ogg;codecs=opus', 'audio/webm'].find(t => MediaRecorder.isTypeSupported(t));
    const recorder = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);
    state.recorder = recorder; state.chunks = []; state.recording = true;
    recorder.ondataavailable = event => { if (event.data.size) state.chunks.push(event.data); };
    recorder.onerror = () => { cancelRecording(); setBusy(false); showError('Recording stopped unexpectedly. Please retry.'); };
    recorder.onstop = async () => {
      const blob = new Blob(state.chunks, { type: recorder.mimeType || 'audio/webm' });
      cleanupMicrophone(); state.recorder = null;
      if (generation !== state.generation) return;
      state.lastRecording = blob;
      if (state.recordingURL && !state.soundURLs.includes(state.recordingURL)) URL.revokeObjectURL(state.recordingURL);
      state.recordingURL = URL.createObjectURL(blob); $('audio-actions').hidden = false;
      await recognise(blob, generation);
    };
    recorder.start(200); state.busy = false; $('mic-button').disabled = false; $('mic-button').classList.add('recording');
    $('mic-button').innerHTML = icon('stop'); $('mic-button').setAttribute('aria-label', 'Stop recording and send');
    $('coach-listen').disabled = true; $('coach-continue').disabled = true;
    $('mic-label').textContent = 'Recording';
    $('mic-detail').textContent = $('auto-stop').checked ? 'Pause to finish, or tap to send.' : 'Tap again when you have finished.';
    const started = performance.now();
    state.timer = setInterval(() => {
      const seconds = Math.floor((performance.now() - started) / 1000);
      $('record-clock').textContent = `0:${String(seconds).padStart(2, '0')}`;
      if (seconds >= (state.mode === 'repeat' || state.coach ? 20 : 60)) finishRecording();
    }, 250);
    if ($('auto-stop').checked) monitorSilence(stream, started);
  } catch (error) {
    cleanupMicrophone(); setBusy(false);
    showError(error.name === 'NotAllowedError' ? 'Allow microphone access in your browser, then tap the microphone again.' :
      error.name === 'NotFoundError' ? 'No microphone was found. Connect one or use Type instead.' : `Could not start recording: ${error.message}`);
  }
}
function monitorSilence(stream, started) {
  try {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    const context = new AudioContext(); state.audioContext = context;
    const analyser = context.createAnalyser(); analyser.fftSize = 1024;
    context.createMediaStreamSource(stream).connect(analyser);
    const samples = new Float32Array(analyser.fftSize); let heardSpeech = false, lastSound = started;
    const pauseMs = Number($('pause-duration').value) || 1200;
    function check() {
      if (!state.recording) return;
      analyser.getFloatTimeDomainData(samples);
      const rms = Math.sqrt(samples.reduce((total, sample) => total + sample * sample, 0) / samples.length);
      const now = performance.now();
      if (rms > 0.012) { heardSpeech = true; lastSound = now; }
      if ((heardSpeech && now - lastSound > pauseMs && now - started > pauseMs) || (!heardSpeech && now - started > 15000)) { finishRecording(); return; }
      state.monitor = requestAnimationFrame(check);
    }
    state.monitor = requestAnimationFrame(check);
  } catch { /* The stop button and one-minute cap remain available. */ }
}
async function recognise(blob, generation) {
  setBusy(true, state.coach ? 'Checking your attempt…' : state.mode === 'repeat' ? 'Checking sounds…' : 'Transcribing…', state.status?.public_mode ? 'Your recording is analysed on the app server.' : 'Your recording is analysed on your Mac.');
  const controller = new AbortController(); state.controller = controller;
  try {
    if (state.coach) { await retryCorrection(blob, generation, controller.signal); return; }
    if (state.mode === 'repeat') {
      const data = await analysePronunciation(blob, repeatTarget(), controller.signal);
      if (generation !== state.generation) return;
      setBusy(false); await showRepeatResult(data); return;
    }
    const response = await api('/api/transcribe', { method: 'POST', headers: { 'Content-Type': blob.type || 'audio/webm' }, body: blob, signal: controller.signal });
    const data = await response.json(); if (generation !== state.generation) return;
    setBusy(false);
    if ($('check-transcript').checked) {
      $('heard-text').value = data.text; $('transcript-check').hidden = false; $('heard-text').focus();
    } else await submitTurn(data.text, false, blob);
  } catch (error) {
    if (error.name === 'AbortError' || generation !== state.generation) return;
    setBusy(false); showError(error.message);
  }
}
function groupWords() { return state.vocabulary.filter(item => item.group === state.vocabGroup); }
function repeatTarget() {
  if (state.customTarget) return state.customTarget;
  const word = groupWords()[state.vocabIndex];
  if (!word) return '';
  return word.text.split(/\s+/).length <= 3 ? `Ech soen: ${word.text.replace(/[.!?]+$/, '')}.` : word.text;
}
function useCustomTarget(text) {
  text = text.trim(); if (!text) return;
  cancelRecording(); state.generation++; state.controller?.abort(); stopAudio(); setBusy(false);
  state.customTarget = text; $('repeat-text').textContent = text;
  $('repeat-translation').textContent = 'Your phrase · say it once';
  $('spoken-target').textContent = text; $('repeat-result').replaceChildren();
  $('custom-target').value = text; $('reference-button').disabled = !state.status?.speech_ready;
}
function openRepeat() {
  $('welcome').hidden = true; $('conversation').hidden = true; $('repeat-panel').hidden = false;
  $('speaking-dock').hidden = false; state.started = true;
  $('scenario-title').textContent = 'Listen & repeat'; $('practice-label').textContent = 'Sounds';
  $('hint-button').hidden = true; $('type-button').hidden = true; $('source-button').hidden = true;
  renderWord(); setBusy(false);
}
function renderWord() {
  state.customTarget = ''; $('custom-target').value = '';
  const words = groupWords(); state.vocabIndex = Math.max(0, Math.min(state.vocabIndex, words.length - 1));
  const word = words[state.vocabIndex];
  $('repeat-text').textContent = word?.text || 'No vocabulary found'; $('repeat-translation').textContent = word?.translation || '';
  $('spoken-target').textContent = repeatTarget();
  $('word-position').textContent = `${words.length ? state.vocabIndex + 1 : 0} / ${words.length}`;
  $('repeat-result').replaceChildren(); $('previous-word').disabled = !state.vocabIndex;
  $('next-word').disabled = state.vocabIndex >= words.length - 1; $('reference-button').disabled = !word;
}
async function analysePronunciation(blob, target, signal) {
  return (await api(`/api/pronunciation?target=${encodeURIComponent(target)}`, {
    method: 'POST', headers: { 'Content-Type': blob.type || 'audio/webm' }, body: blob, signal,
  })).json();
}
function soundFeedbackElement(data, recordingURL) {
  const box = document.createElement(state.mode === 'repeat' ? 'section' : 'details'); box.className = `sound-feedback ${data.outcome}`;
  const label = document.createElement(state.mode === 'repeat' ? 'strong' : 'summary'); label.className = 'field-label';
  label.textContent = data.outcome === 'possible_difference' ? 'Possible sound difference · audio' : 'Sound check · audio';
  const summary = document.createElement('p'); summary.textContent = data.summary;
  box.append(label, summary);
  for (const tip of data.tips || []) {
    const card = document.createElement('div'); card.className = 'sound-tip';
    const title = document.createElement('h4'); title.textContent = tip.word;
    const evidence = document.createElement('p'); evidence.textContent = tip.explanation;
    const practice = document.createElement('p'); practice.textContent = tip.practice;
    card.append(title, evidence, practice);
    const target = `Ech soen: ${tip.word.replace(/[.!?]+$/, '')}.`;
    const example = document.createElement('button'); example.className = 'text-button'; example.textContent = 'Hear the target word';
    example.addEventListener('click', () => playReply(target, false, true)); card.append(example);
    const repeat = document.createElement('button'); repeat.className = 'text-button'; repeat.textContent = 'Practise this word';
    repeat.addEventListener('click', () => {
      if (state.recording || state.busy || state.coach) return;
      if (state.mode === 'repeat') { useCustomTarget(target); playReply(target, false, true); }
      else beginCorrection([{ kind: 'Sound · possible difference', target, explanation: `${tip.explanation} ${tip.practice}`, sound: true }], null);
    }); card.append(repeat);
    if (recordingURL) {
      const replay = document.createElement('button'); replay.className = 'text-button'; replay.textContent = 'Compare my recording';
      replay.addEventListener('click', () => replayRecordingPart(recordingURL, tip.start, tip.end)); card.append(replay);
    }
    box.append(card);
  }
  if (data.expected_ipa || data.heard_ipa) {
    const details = document.createElement('details'); const heading = document.createElement('summary'); heading.textContent = 'Compare the sounds (IPA)';
    const expected = document.createElement('p'); expected.textContent = `Dictionary variant: /${data.expected_ipa}/`;
    const heard = document.createElement('p'); heard.textContent = `Model heard: /${data.heard_ipa}/`;
    const note = document.createElement('small'); note.textContent = 'These symbols represent sounds. The model can miss or misidentify a sound; this is not a pronunciation score.';
    details.append(heading, expected, heard, note); box.append(details);
  }
  if (recordingURL && !state.soundURLs.includes(recordingURL)) state.soundURLs.push(recordingURL);
  return box;
}
async function replayRecordingPart(url, start, end) {
  if (state.recording || (state.busy && !state.playing)) return;
  stopAudio(); setBusy(false);
  const audio = new Audio(url); state.playing = audio;
  audio.addEventListener('loadedmetadata', () => { audio.currentTime = Math.min(start, Number.isFinite(audio.duration) ? audio.duration : start); }, { once: true });
  audio.addEventListener('timeupdate', () => { if (audio.currentTime >= end) stopAudio(); });
  audio.onended = stopAudio;
  try { await audio.play(); } catch { stopAudio(); showError('Could not replay that recording.'); }
}
async function showRepeatResult(data) {
  $('repeat-result').replaceChildren(soundFeedbackElement(data, state.recordingURL));
  if (data.outcome === 'possible_difference' && data.tips?.length && $('spoken-corrections').checked) await playReply(repeatTarget(), false, true);
}
const listeningView = createListeningView({ api, onError: showError, getModel: () => $('model-select').value || state.status?.model });
function setMode(mode) {
  listeningView.close();
  resetSession(); state.mode = mode;
  document.querySelectorAll('.mode-tab').forEach(tab => { tab.classList.toggle('active', tab.dataset.mode === mode); tab.setAttribute('aria-current', tab.dataset.mode === mode ? 'page' : 'false'); });
  $('repeat-panel').hidden = true; $('source-button').hidden = false; $('type-button').hidden = false;
  $('listening-panel').hidden = mode !== 'listening';
  $('conversation-options').hidden = mode === 'repeat' || mode === 'listening';
  $('scenario-title').textContent = selectedScenario().title;
  $('practice-label').textContent = 'Speaking';
  $('hint-button').hidden = false;
  $('mission').textContent = mode === 'review' ? `${selectedScenario().mission} Attempt each reply before receiving feedback. This is generated practice, not an official test.` : selectedScenario().mission;
  if (mode === 'repeat') openRepeat();
  if (mode === 'listening') {
    $('welcome').hidden = true; $('practice-label').textContent = 'Listening'; $('scenario-title').textContent = 'Listen & understand';
    listeningView.open();
  }
  history.replaceState(null, '', mode === 'listening' ? '#listening' : location.pathname + location.search);
  loadStatus();
}
$('start-button').addEventListener('click', startSession);
$('scenario-select').addEventListener('change', () => selectScenario($('scenario-select').value));
$('coach-listen').addEventListener('click', () => { if (state.coach && !state.recording) playReply(state.coach.target, false, true); });
$('coach-continue').addEventListener('click', continueConversation);
$('restart-button').addEventListener('click', () => setMode(state.mode));
$('mic-button').addEventListener('click', startRecording);
$('send-transcript').addEventListener('click', () => submitTurn($('heard-text').value, false, state.lastRecording));
$('send-typed').addEventListener('click', () => { const text = $('typed-text').value; $('typed-text').value = ''; submitTurn(text); });
$('typed-text').addEventListener('keydown', event => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); $('send-typed').click(); } });
$('type-button').addEventListener('click', () => { $('type-panel').hidden = !$('type-panel').hidden; if (!$('type-panel').hidden) $('typed-text').focus(); });
$('hint-button').addEventListener('click', () => { if (state.mode === 'review') return; const hint = document.createElement('div'); hint.className = 'hint-message'; hint.textContent = selectedScenario().hint; $('conversation').append(hint); $('conversation').scrollTop = $('conversation').scrollHeight; });
$('retry-button').addEventListener('click', () => {
  if (state.awaitingTutor || state.recording) return;
  if (state.coach) {
    stopAudio(); state.coach = null; state.heldReply = null; state.correctionQueue = [];
    $('coach-panel').hidden = true; setBusy(false);
  }
  submitTurn(state.messages.at(-1)?.content || '', true);
});
$('my-audio-button').addEventListener('click', async () => {
  if (!state.recordingURL || state.recording || (state.busy && !state.playing)) return;
  stopAudio(); setBusy(false); const audio = new Audio(state.recordingURL); state.playing = audio;
  audio.onended = stopAudio; try { await audio.play(); } catch { showError('Could not play your recording.'); }
});
document.querySelectorAll('.mode-tab').forEach(tab => tab.addEventListener('click', () => setMode(tab.dataset.mode)));
$('settings-button').addEventListener('click', () => { loadStatus(); $('settings-dialog').showModal(); });
document.querySelectorAll('.close-dialog').forEach(button => button.addEventListener('click', () => button.closest('dialog').close()));
$('source-button').addEventListener('click', async () => {
  try { const source = await (await api(`/api/source/${state.selected}`)).json(); $('source-path').textContent = `${source.path} · ${source.section}`; $('source-text').textContent = source.text; $('source-dialog').showModal(); } catch (error) { showError(error.message); }
});
$('vocab-group').addEventListener('change', () => { cancelRecording(); state.generation++; state.vocabGroup = $('vocab-group').value; state.vocabIndex = 0; stopAudio(); setBusy(false); renderWord(); });
for (const [id, change] of [['previous-word', -1], ['next-word', 1]]) $(id).addEventListener('click', () => { cancelRecording(); state.generation++; state.vocabIndex += change; stopAudio(); setBusy(false); renderWord(); });
$('reference-button').addEventListener('click', async () => {
  const word = groupWords()[state.vocabIndex]; if (!word || state.recording) return;
  if (state.customTarget || word.text.split(/\s+/).length <= 3) { state.userGesture = true; await playReply(repeatTarget(), false); return; }
  stopAudio(); const audio = new Audio(`/api/reference-audio/${word.id}`); state.playing = audio;
  audio.onended = stopAudio; try { await audio.play(); } catch { showError('The example audio could not play. Please try again.'); }
});
$('use-custom-target').addEventListener('click', () => useCustomTarget($('custom-target').value));
$('practice-recording').addEventListener('change', async event => {
  const file = event.target.files[0]; event.target.value = '';
  if (!file || state.mode !== 'repeat' || state.busy || state.recording) return;
  if (file.size > 8 * 1024 * 1024) { showError('Use a short audio file under 8 MB.'); return; }
  stopAudio(); clearError();
  const generation = state.generation;
  const type = /\.wav$/i.test(file.name) ? 'audio/wav' : /\.(m4a|mp4)$/i.test(file.name) ? 'audio/mp4' : /\.mp3$/i.test(file.name) ? 'audio/mpeg' : file.type;
  const blob = new Blob([file], { type }); state.lastRecording = blob;
  if (state.recordingURL && !state.soundURLs.includes(state.recordingURL)) URL.revokeObjectURL(state.recordingURL);
  state.recordingURL = URL.createObjectURL(blob); $('audio-actions').hidden = false;
  await recognise(blob, generation);
});
$('export-button').addEventListener('click', () => {
  const text = `# ${selectedScenario().title}\n\nGenerated speaking practice. Source: ${selectedScenario().source}\nWording feedback uses transcripts. Experimental sound feedback uses recorded audio separately; this text export contains no recordings or pronunciation grades.\n\n` + state.messages.map(m => `**${m.role === 'user' ? 'Me' : 'Partner'}:** ${m.content}`).join('\n\n');
  const url = URL.createObjectURL(new Blob([text], { type: 'text/markdown' }));
  const link = document.createElement('a'); link.href = url; link.download = `Schwatz-${state.selected}-${new Date().toISOString().slice(0, 10)}.md`; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
});
document.addEventListener('visibilitychange', () => { if (document.hidden) { cancelRecording(); stopAudio(); if (!state.pendingReply) setBusy(false); } });
window.addEventListener('pagehide', () => { cancelRecording(); stopAudio(); });

async function connectOwnKey() {
  if (state.busy || state.recording || state.awaitingTutor) { $('key-status').textContent = 'Finish the current turn before changing your connection.'; return; }
  const input = $('provider-key'); const key = input.value.trim(); input.value = '';
  if (!key) { $('key-status').textContent = 'Enter your OpenRouter API key.'; return; }
  if (key.length < 20 || key.length > 512 || /[^\x21-\x7e]/.test(key)) { $('key-status').textContent = 'Check the API key format. Paste only the key, without spaces or line breaks.'; return; }
  state.keyController?.abort(); const controller = new AbortController(); state.keyController = controller;
  $('connect-key').disabled = true; $('key-status').textContent = 'Checking your key and available models…';
  const freeOnly = $('free-models-only').checked;
  try {
    const response = await api('/api/byok/models', {method: 'POST', headers: {'Content-Type': 'application/json', 'X-Provider-Key': key}, body: JSON.stringify({free_only: freeOnly}), signal: controller.signal});
    const data = await response.json();
    if (state.keyController !== controller || controller.signal.aborted) return;
    if (!data.models.length) throw new Error('No eligible models are available. Your key was not connected.');
    state.byokKey = key; state.byokModels = data.models; state.byokFreeOnly = freeOnly;
    $('disconnect-key').hidden = false; $('key-status').textContent = 'Connected for this tab. Refreshing or disconnecting clears the key.';
    savedModel = data.models[0].id;
    await loadStatus();
  } catch (error) { if (error.name !== 'AbortError' && state.keyController === controller) $('key-status').textContent = error.message; }
  finally { $('connect-key').disabled = false; }
}
function disconnectOwnKey() {
  state.keyController?.abort(); state.keyController = null;
  resetSession(); state.byokKey = ''; state.byokModels = []; state.byokFreeOnly = true;
  $('provider-key').value = ''; $('free-models-only').checked = true;
  $('disconnect-key').hidden = true; $('key-status').textContent = 'Disconnected. The key has been cleared from this tab.';
  savedModel = ''; loadStatus();
}
$('connect-key').addEventListener('click', connectOwnKey);
$('disconnect-key').addEventListener('click', disconnectOwnKey);
$('provider-key').addEventListener('keydown', event => { if (event.key === 'Enter') { event.preventDefault(); connectOwnKey(); } });
window.addEventListener('pagehide', () => { state.keyController?.abort(); state.keyController = null; state.byokKey = ''; state.byokModels = []; });
window.addEventListener('pageshow', event => { if (event.persisted) disconnectOwnKey(); });
async function init() {
  try {
    const [scenarios, words] = await Promise.all([api('/api/scenarios').then(r => r.json()), api('/api/vocabulary').then(r => r.json())]);
    state.scenarios = scenarios; state.vocabulary = words; renderScenarios(); $('mission').textContent = selectedScenario().mission;
    const groups = [...new Set(words.map(w => w.group))]; state.vocabGroup = groups[0] || '';
    $('vocab-group').replaceChildren(...groups.map(group => { const option = document.createElement('option'); option.value = group; option.textContent = group; return option; }));
    setMode(location.hash === '#listening' ? 'listening' : 'conversation');
    if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(() => {});
  } catch (error) { showError(error.message); }
}
init();
