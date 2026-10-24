import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync(new URL('../public/app.js', import.meta.url), 'utf8');
const selected = source.slice(source.indexOf('function saveSettings()'), source.indexOf('function selectedScenario()'));
const status = source.slice(source.indexOf('async function loadStatus()'), source.indexOf('function renderScenarios()'));
const cloud = 'opencode/deepseek-v4.1-flash-free';
const glm = 'opencode/glm-5.3-flash-free';
const preferenceInit = source.slice(source.indexOf('let savedModel ='), source.indexOf('function saveSettings()'));

function harness() {
  let response;
  const elements = new Map();
  const $ = id => {
    if (!elements.has(id)) elements.set(id, {value: '', textContent: '', disabled: false,
      addEventListener() {}, replaceChildren(...options) { this.options = options; }});
    return elements.get(id);
  };
  const state = {mode: 'conversation', started: false, busy: false, recording: false};
  const context = vm.createContext({$, state, optionIds: [], setBusy() {}, setTimeout() {},
    warmSelectedModel() {}, localStorage: {setItem() {}},
    document: {createElement() { return {}; }},
    api: async () => ({json: async () => response}),
  });
  vm.runInContext('let savedModel = "";\n' + selected + status, context);
  return {$, state, context, setStatus(models, model) {
    response = {models, model, online_models: models.filter(m => [cloud, glm].includes(m)),
      online_model_names: {[cloud]: 'DeepSeek V4.1 Flash', [glm]: 'GLM 5.3 Flash'},
      speech_ready: true, pronunciation_ready: true,
      conversation_ready: true, model_labels: {[cloud]: 'DeepSeek · Free', [glm]: 'GLM 5.3 Flash · Free · OpenCode'}};
  }};
}

test('fresh selection follows the faster GLM default when startup finishes and discloses online text', async () => {
  const h = harness();
  h.setStatus(['qwen3.8:27b'], 'qwen3.8:27b');
  await vm.runInContext('loadStatus()', h.context);
  h.setStatus([glm, cloud, 'qwen3.8:27b'], glm);
  await vm.runInContext('loadStatus()', h.context);
  assert.equal(h.$('model-select').value, glm);
  assert.equal(h.$('connection-text').textContent, 'Online');
  assert.match(h.$('model-detail').textContent, /transcript and selected lesson excerpt go to OpenCode/);
  h.state.mode = 'repeat';
  vm.runInContext('updateModelInfo()', h.context);
  assert.equal(h.$('connection-text').textContent, 'Local');
});

test('the old default moves to GLM once while explicit new and personal choices survive', () => {
  for (const [saved, expected] of [
    [{model: cloud}, glm],
    [{model: cloud, replySpeedVersion: 1}, cloud],
    [{model: 'qwen3:8b'}, 'qwen3:8b'],
    [{model: 'byok/openrouter/test:free'}, 'byok/openrouter/test:free'],
  ]) {
    const context = vm.createContext({optionIds: [], $: () => ({}),
      localStorage: {getItem: () => JSON.stringify(saved)}});
    vm.runInContext(preferenceInit, context);
    assert.equal(vm.runInContext('savedModel', context), expected);
  }
});

test('a learner’s local model choice survives status refreshes', async () => {
  const h = harness();
  h.setStatus([cloud, 'qwen3.8:27b'], cloud);
  await vm.runInContext('loadStatus()', h.context);
  h.$('model-select').value = 'qwen3.8:27b';
  vm.runInContext('saveSettings()', h.context);
  await vm.runInContext('loadStatus()', h.context);
  assert.equal(h.$('model-select').value, 'qwen3.8:27b');
  assert.equal(h.$('connection-text').textContent, 'Local');
  assert.equal(h.$('model-detail').textContent, 'Conversation and audio are processed on your Mac.');
});

test('GLM selection persists and shows the correct online disclosure and model name', async () => {
  const h = harness();
  h.setStatus([cloud, glm, 'qwen3.8:27b'], cloud);
  await vm.runInContext('loadStatus()', h.context);
  h.$('model-select').value = glm;
  vm.runInContext('saveSettings()', h.context);
  await vm.runInContext('loadStatus()', h.context);
  assert.equal(h.$('model-select').value, glm);
  assert.equal(h.$('connection-text').textContent, 'Online');
  assert.equal(h.$('runtime-label').textContent, 'GLM 5.3 Flash · local audio');
  assert.match(h.$('model-detail').textContent, /Audio is processed on your Mac. No paid fallback/);
  h.state.mode = 'repeat';
  vm.runInContext('updateModelInfo()', h.context);
  assert.equal(h.$('connection-text').textContent, 'Local');
});

test('personal model settings never persist the key', async () => {
  const h = harness(); let stored;
  const model = 'byok/openrouter/test/free:free';
  h.state.byokKey = 'test-only-alpha-1234567890';
  h.state.byokModels = [{id:model,name:'Test model',free:true}];h.state.byokFreeOnly=true;
  h.context.localStorage.setItem = (name,value) => { stored=value; };
  h.setStatus([], '');
  await vm.runInContext('loadStatus()',h.context);
  assert.equal(h.$('model-select').value,model);
  vm.runInContext('saveSettings()',h.context);
  assert.equal(stored.includes(h.state.byokKey),false);
  assert.match(h.$('model-detail').textContent,/Free models only/);
});
