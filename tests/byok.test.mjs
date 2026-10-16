import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync(new URL('../public/app.js', import.meta.url), 'utf8');
const connections = source.slice(source.indexOf('async function connectOwnKey()'), source.indexOf('async function init()'));
const apiSource = source.slice(source.indexOf('async function api('), source.indexOf('async function loadStatus()'));
const ownModel = 'byok/openrouter/test/free:free';
const fakeKey = 'test-only-alpha-1234567890';

function harness() {
  const elements = new Map(), calls = [];
  const $ = id => {
    if (!elements.has(id)) elements.set(id, {value:'', checked:true, hidden:true, addEventListener(){}});
    return elements.get(id);
  };
  const state = {byokKey:'',byokModels:[],byokFreeOnly:true,keyController:null};
  const context = vm.createContext({state,$,AbortController,
    resetSession(){calls.push('reset');}, loadStatus:async()=>{},
    window:{addEventListener(){}}, localStorage:{setItem(){throw new Error('Keys must not be stored');}},
    api:async(path,options)=>{calls.push({path,options});return {json:async()=>({models:[{id:ownModel,name:'Test',free:true}]})};}
  });
  vm.runInContext('let savedModel="";\n'+connections,context);
  return {state,$,context,calls};
}

test('connecting holds the key only in tab memory and immediately clears the input',async()=>{
  const h=harness();h.$('provider-key').value=fakeKey;
  await h.context.connectOwnKey();
  assert.equal(h.$('provider-key').value,'');assert.equal(h.state.byokKey,fakeKey);
  assert.equal(h.calls[0].options.headers['X-Provider-Key'],fakeKey);
  assert.equal(JSON.parse(h.calls[0].options.body).free_only,true);
  assert.equal(vm.runInContext('savedModel',h.context),ownModel);
  h.context.disconnectOwnKey();
  assert.equal(h.state.byokKey,'');assert.equal(h.state.byokModels.length,0);
  assert.equal(h.state.byokFreeOnly,true);
});

test('disconnect cancels a pending connection and prevents a late response from restoring the key',async()=>{
  const h=harness();let resolve;
  h.context.api=()=>new Promise(yes=>{resolve=yes;});h.$('provider-key').value=fakeKey;
  const connect=h.context.connectOwnKey();
  const controller=h.state.keyController;h.context.disconnectOwnKey();
  assert.equal(controller.signal.aborted,true);
  resolve({json:async()=>({models:[{id:ownModel}]})});await connect;
  assert.equal(h.state.byokKey,'');assert.equal(h.state.byokModels.length,0);
});

test('provider credentials are attached only to personal-key turn and warm requests',async()=>{
  const calls=[];
  const context=vm.createContext({state:{byokKey:fakeKey,byokFreeOnly:true},fetch:async(path,options)=>{
    calls.push({path,options});return {ok:true};
  }});
  vm.runInContext(apiSource,context);
  for(const [path,model] of [['/api/turn',ownModel],['/api/warm',ownModel],['/api/turn','local-model'],['/api/pronunciation',ownModel],['/api/status',ownModel]]){
    await context.api(path,{body:JSON.stringify({model})});
  }
  assert.equal(calls[0].options.headers['X-Provider-Key'],fakeKey);
  assert.equal(calls[1].options.headers['X-Provider-Key'],fakeKey);
  for(const call of calls.slice(2)) assert.equal(call.options.headers,undefined);
});
