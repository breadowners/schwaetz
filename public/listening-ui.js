export function createListeningView({ api, onError, getModel }) {
  const el = id => document.getElementById(id);
  const audio = el('listening-audio');
  let catalog = null, episode = null, generation = 0, controller = null, translationController = null;
  let questionIndex = 0, selectedChoice = -1, answers = new Map(), active = false;
  const option = (value, label) => { const node = document.createElement('option'); node.value = value; node.textContent = label; return node; };

  function renderQuestion() {
    const question = episode.questions[questionIndex];
    selectedChoice = -1;
    el('listening-choices').disabled = false;
    el('listening-question-position').textContent = `Question ${questionIndex + 1} of ${episode.questions.length} · generated practice`;
    el('listening-question-text').textContent = question.prompt;
    el('listening-options').replaceChildren(...question.options.map((text, index) => {
      const label = document.createElement('label');
      const input = document.createElement('input'); input.type = 'radio'; input.name = 'listening-answer'; input.value = String(index);
      input.addEventListener('change', () => { selectedChoice = index; el('listening-check').disabled = answers.has(question.id); });
      const words = document.createElement('span'); words.textContent = text; label.append(input, words); return label;
    }));
    el('listening-check').disabled = true;
    el('listening-next').hidden = true;
    el('listening-feedback').textContent = '';
    el('listening-score').textContent = answers.size
      ? `${[...answers.values()].filter(Boolean).length} of ${answers.size} correct · practice, not an official test` : '';
  }

  function renderTranscript() {
    const rows = episode.transcript || [];
    el('listening-english-label').hidden = !rows.length;
    el('listening-transcript-note').textContent = rows.length
      ? episode.translation_note
      : 'The full transcript is in the publisher’s episode description. Open it below, then use Translate a passage for English help.';
    el('listening-transcript-link').href = episode.transcript_url;
    el('listening-transcript-lines').replaceChildren(...rows.map(row => {
      const pair = document.createElement('div'); pair.className = 'listening-transcript-row';
      const original = document.createElement('p'); original.textContent = row.text;
      const translation = document.createElement('p'); translation.textContent = row.translation;
      translation.className = 'listening-transcript-english'; translation.hidden = !el('listening-english').checked;
      pair.append(original, translation); return pair;
    }));
  }

  async function loadEpisode() {
    const id = el('listening-episode').value;
    const current = ++generation; controller?.abort(); audio.pause();
    controller = new AbortController();
    el('listening-content').hidden = true; el('listening-status').textContent = 'Loading episode…';
    translationController?.abort(); el('listening-passage').value = ''; el('listening-translation-result').textContent = '';
    try {
      const data = await (await api(`/api/listening/${id}`, { signal: controller.signal })).json();
      if (!active || current !== generation) return;
      episode = data; answers = new Map(); questionIndex = 0;
      el('listening-title').textContent = data.title;
      el('listening-meta').textContent = `${data.publisher} · ${data.level} · ${data.duration} · ${data.published}`;
      el('listening-guide').textContent = data.guide;
      el('listening-source').href = data.publisher_url;
      el('listening-download').href = data.audio_available ? `/api/listening/${id}/audio` : data.audio_url;
      el('listening-download').download = `${id}${data.audio_url.endsWith('.m4a') ? '.m4a' : '.mp3'}`;
      if (data.audio_available) audio.src = `/api/listening/${id}/audio`;
      else audio.removeAttribute('src');
      audio.hidden = !data.audio_available;
      audio.playbackRate = Number(el('listening-speed').value);
      el('listening-rewind').disabled = !data.audio_available;
      el('listening-speed').disabled = !data.audio_available;
      el('listening-status').textContent = data.audio_available ? 'Original INLL recording · no synthetic voice.' : 'Use the official episode link to listen; audio is not downloaded on this server.';
      el('listening-transcript').open = false; el('listening-translation').open = false;
      el('listening-english').checked = false;
      renderQuestion(); renderTranscript(); el('listening-content').hidden = false;
    } catch (error) { if (error.name !== 'AbortError' && current === generation) { el('listening-status').textContent = 'Could not load this episode.'; onError(error.message); } }
  }

  function filterEpisodes() {
    const topic = el('listening-topic').value;
    const items = catalog.episodes.filter(item => !topic || item.topics.includes(topic));
    const previous = el('listening-episode').value;
    el('listening-episode').replaceChildren(...items.map(item => option(item.id, `${item.title} · ${item.level}`)));
    el('listening-episode').value = items.some(item => item.id === previous) ? previous : items[0]?.id || '';
    return loadEpisode();
  }

  async function open() {
    active = true;
    if (catalog) { await filterEpisodes(); return; }
    const current = ++generation; controller = new AbortController();
    try {
      const data = await (await api('/api/listening', { signal: controller.signal })).json();
      if (!active || current !== generation) return;
      catalog = data;
      const topics = [...new Set(data.episodes.flatMap(item => item.topics))];
      el('listening-topic').replaceChildren(option('', 'All topics'), ...topics.map(topic => option(topic, topic)));
      el('listening-topic').value = '';
      el('listening-books').replaceChildren(...data.books.map(book => {
        const item = document.createElement('li'); const link = document.createElement('a');
        link.textContent = book.title; link.href = book.url; link.target = '_blank'; link.rel = 'noreferrer'; item.append(link); return item;
      }));
      await filterEpisodes();
    } catch (error) { if (error.name !== 'AbortError' && current === generation) { el('listening-status').textContent = 'Could not load listening sources.'; onError(error.message); } }
  }

  function close() { active = false; generation++; controller?.abort(); translationController?.abort(); audio.pause(); }
  el('listening-topic').addEventListener('change', filterEpisodes);
  el('listening-episode').addEventListener('change', loadEpisode);
  el('listening-speed').addEventListener('change', () => { audio.playbackRate = Number(el('listening-speed').value); });
  el('listening-rewind').addEventListener('click', () => { audio.currentTime = Math.max(0, audio.currentTime - 10); });
  el('listening-english').addEventListener('change', renderTranscript);
  audio.addEventListener('error', () => { if (active && episode?.audio_available) el('listening-status').textContent = 'Audio could not load. Try the official episode link.'; });
  el('listening-check').addEventListener('click', async () => {
    if (!episode || selectedChoice < 0) return;
    const question = episode.questions[questionIndex], current = generation;
    if (answers.has(question.id)) return;
    el('listening-check').disabled = true;
    el('listening-choices').disabled = true;
    try {
      const response = await api(`/api/listening/${episode.id}/check`, {method:'POST', headers:{'Content-Type':'application/json'},
        body:JSON.stringify({question_id:question.id,choice:selectedChoice}), signal:controller.signal});
      const result = await response.json(); if (current !== generation) return;
      answers.set(question.id, result.correct);
      el('listening-feedback').textContent = `${result.correct ? 'Correct.' : `Not quite. Answer: ${question.options[result.answer]}.`} ${result.explanation}`;
      el('listening-score').textContent = `${[...answers.values()].filter(Boolean).length} of ${answers.size} correct · practice, not an official test`;
      el('listening-next').textContent = questionIndex + 1 === episode.questions.length ? 'Start again' : 'Next question';
      el('listening-next').hidden = false;
    } catch(error) { if (error.name !== 'AbortError' && current === generation) { el('listening-check').disabled = false; el('listening-choices').disabled = false; onError(error.message); } }
  });
  el('listening-next').addEventListener('click', () => {
    questionIndex++;
    if (questionIndex === episode.questions.length) { questionIndex = 0; answers.clear(); }
    renderQuestion();
  });
  el('listening-translate').addEventListener('click', async () => {
    const text = el('listening-passage').value.trim();
    if (!text) { el('listening-translation-result').textContent = 'Paste a passage from the transcript first.'; return; }
    translationController?.abort(); const requestController = new AbortController(); translationController = requestController; const current = generation;
    el('listening-translate').disabled = true; el('listening-translation-result').textContent = 'Translating with your selected model…';
    try {
      const result = await (await api('/api/listening/translate', {method:'POST', headers:{'Content-Type':'application/json'},
        body:JSON.stringify({text,model:getModel()}), signal:requestController.signal})).json();
      if (current === generation) el('listening-translation-result').textContent = `English study translation · generated\n\n${result.translation}`;
    } catch(error) { if (error.name !== 'AbortError' && current === generation) el('listening-translation-result').textContent = error.message; }
    finally { if (translationController === requestController) el('listening-translate').disabled = false; }
  });
  return { open, close };
}
