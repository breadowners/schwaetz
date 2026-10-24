import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync(new URL('../public/listening-ui.js', import.meta.url), 'utf8').replace('export function', 'function');
const episode = {id:'one',title:'Official audio',publisher:'INLL',level:'A2',duration:'03:00',published:'2026-10-23',
  audio_available:true,audio_url:'https://example.test/audio.mp3',publisher_url:'https://example.test/episode',transcript_url:'https://example.test/transcript',
  topics:['Restaurant'],transcript:[{text:'Moien!',translation:'Hello!'}],translation_note:'Study translation',
  questions:[{id:0,prompt:'What was ordered?',options:['Pizza','Soup']},{id:1,prompt:'What did they drink?',options:['Water','Coffee']}]};

function harness() {
  const elements = new Map(), calls = [], errors = [];
  function node() {
    return {value:'',textContent:'',hidden:true,disabled:false,checked:false,currentTime:0,children:[],handlers:{},
      addEventListener(name,fn){this.handlers[name]=fn;}, append(...children){this.children.push(...children);},
      replaceChildren(...children){this.children=children;}, pause(){this.paused=true;}, removeAttribute(name){delete this[name];}};
  }
  const el = id => { if (!elements.has(id)) elements.set(id,node()); return elements.get(id); };
  el('listening-speed').value = '1';
  const context = vm.createContext({AbortController,document:{getElementById:el,createElement:node}});
  vm.runInContext(source,context);
  const api = async (path,options) => {
    calls.push({path,options});
    if (path === '/api/listening') return {json:async()=>({episodes:[episode],books:[]})};
    if (path.endsWith('/check')) return {json:async()=>({correct:true,answer:0,explanation:'The customer chose pizza.'})};
    if (path.endsWith('/translate')) return {json:async()=>({translation:'Hello!'})};
    return {json:async()=>episode};
  };
  const view = context.createListeningView({api,onError:message=>errors.push(message),getModel:()=> 'selected-free-model'});
  return {view,el,calls,errors,context};
}

test('listening reveals feedback only after a choice, then advances one question at a time',async()=>{
  const h=harness(); await h.view.open();
  assert.equal(h.el('listening-check').disabled,true);
  assert.equal(h.el('listening-feedback').textContent,'');
  await h.el('listening-check').handlers.click();
  assert.equal(h.calls.some(call=>call.path.endsWith('/check')),false);
  h.el('listening-options').children[0].children[0].handlers.change();
  await h.el('listening-check').handlers.click();
  assert.match(h.el('listening-feedback').textContent,/Correct.*pizza/);
  assert.equal(h.el('listening-choices').disabled,true);
  assert.match(h.el('listening-score').textContent,/1 of 1 correct/);
  h.el('listening-next').handlers.click();
  assert.equal(h.el('listening-question-text').textContent,'What did they drink?');
  assert.equal(h.el('listening-feedback').textContent,'');
});

test('English stays hidden until requested, and speed and rewind affect the original audio',async()=>{
  const h=harness(); await h.view.open();
  let row=h.el('listening-transcript-lines').children[0];
  assert.equal(row.children[1].hidden,true);
  h.el('listening-english').checked=true; h.el('listening-english').handlers.change();
  row=h.el('listening-transcript-lines').children[0]; assert.equal(row.children[1].hidden,false);
  h.el('listening-speed').value='0.8';h.el('listening-speed').handlers.change();
  assert.equal(h.el('listening-audio').playbackRate,0.8);
  h.el('listening-audio').currentTime=5;h.el('listening-rewind').handlers.click();
  assert.equal(h.el('listening-audio').currentTime,0);
  h.view.close();assert.equal(h.el('listening-audio').paused,true);
});

test('passage translation sends only pasted text and the selected model',async()=>{
  const h=harness();await h.view.open();
  await h.el('listening-translate').handlers.click();
  assert.match(h.el('listening-translation-result').textContent,/Paste a passage/);
  h.el('listening-passage').value='Moien!';await h.el('listening-translate').handlers.click();
  const call=h.calls.find(call=>call.path.endsWith('/translate'));
  assert.deepEqual(JSON.parse(call.options.body),{text:'Moien!',model:'selected-free-model'});
  assert.match(h.el('listening-translation-result').textContent,/generated.*\n\nHello!/);
});

test('a late catalog response cannot reopen listening after leaving the tab',async()=>{
  const h=harness();let resolve;
  const view=h.context.createListeningView({api:()=>new Promise(yes=>{resolve=yes;}),onError:()=>{},getModel:()=>''});
  const loading=view.open();view.close();resolve({json:async()=>({episodes:[episode],books:[]})});await loading;
  assert.equal(h.el('listening-content').hidden,true);
});
