/* The common owner alone decides version validity and receipt transitions. */
(() => {
 'use strict';
 const hex = value => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
 const date = value => typeof value === 'string' && /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z$/.test(value) && Number.isFinite(Date.parse(value));
 const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
 const versionValid = value => object(value) && Object.keys(value).sort().join(',') === 'raw_sha256,view_sha256,view_version' && hex(value.raw_sha256) && hex(value.view_sha256) && value.view_version === 'plan-text-v1';
 const sameVersion = (a,b) => a.raw_sha256 === b.raw_sha256 && a.view_sha256 === b.view_sha256 && a.view_version === b.view_version;
 const commentValid = row => object(row) && typeof row.comment_id === 'string' && /^[A-Za-z0-9_-]{1,64}$/.test(row.comment_id) && hex(row.section_id) && typeof row.text === 'string' && [...row.text].length <= 2000;
 const commentsValid = rows => Array.isArray(rows) && rows.length <= 20 && rows.every(commentValid) && new Set(rows.map(row => row.comment_id)).size === rows.length && rows.reduce((n,row) => n+new TextEncoder().encode(row.text).length,0) <= 10240;
 const keys = (value,names) => object(value) && Object.keys(value).sort().join(',') === names.split(',').sort().join(',');
 const bytes = value => new TextEncoder().encode(value).length;
 const producerValid = value => keys(value,'caller_id,runtime,actor_id,identity_basis') && typeof value.caller_id === 'string' && /^[A-Za-z0-9_-]{1,128}$/.test(value.caller_id) && ['claude-code','codex','opencode'].includes(value.runtime) && (value.actor_id === null || hex(value.actor_id)) && value.identity_basis === 'declared';
 const flagsValid = value => keys(value,'redacted,controls_sanitized') && typeof value.redacted === 'boolean' && typeof value.controls_sanitized === 'boolean';
 const noteValid = (value,verification=false) => typeof value === 'string' && (verification || !!value.trim()) && [...value].length <= (verification ? 500 : 1000) && bytes(value) <= (verification ? 1024 : 2048);
 function feedbackValid(value,comments) {
  if (!keys(value,'schema_version,results,verifications') || value.schema_version !== 1 || !Array.isArray(value.results) || value.results.length > 40 || !Array.isArray(value.verifications) || value.verifications.length > 40 || !commentsValid(comments)) return false;
  const ids = new Set(), latest = new Map(), counts = new Map(), results = new Map(), verified = new Set();
  for (const row of value.results) {
   if (!keys(row,'result_id,comment_id,section_id,supersedes_result_id,disposition,response_text,text_flags,producer,recorded_at,artifact_observation') || !hex(row.result_id) || ids.has(row.result_id) || !comments.some(c => c.comment_id === row.comment_id && c.section_id === row.section_id) || !['addressed','not_applied','needs_clarification'].includes(row.disposition) || !noteValid(row.response_text) || !flagsValid(row.text_flags) || !producerValid(row.producer) || !date(row.recorded_at)) return false;
   const observation = row.artifact_observation;
   if (!keys(observation,'status,version,observed_at') || !date(observation.observed_at) || !['available','unavailable'].includes(observation.status) || (observation.status === 'available' ? !versionValid(observation.version) : observation.version !== null)) return false;
   if ((counts.get(row.comment_id) || 0) >= 2 || row.supersedes_result_id !== (latest.get(row.comment_id) || null)) return false;
   ids.add(row.result_id); latest.set(row.comment_id,row.result_id); counts.set(row.comment_id,(counts.get(row.comment_id) || 0)+1); results.set(row.result_id,row);
  }
  for (const row of value.verifications) {
   const result = results.get(row.result_id);
   if (!keys(row,'verification_id,result_id,comment_id,section_id,assessment,note,text_flags,basis,producer,recorded_at') || !hex(row.verification_id) || ids.has(row.verification_id) || !result || verified.has(row.result_id) || row.comment_id !== result.comment_id || row.section_id !== result.section_id || !['confirmed','not_confirmed'].includes(row.assessment) || row.basis !== 'human_instruction_declared' || !noteValid(row.note,true) || !flagsValid(row.text_flags) || !producerValid(row.producer) || !date(row.recorded_at)) return false;
   ids.add(row.verification_id); verified.add(row.result_id);
  }
  return value.results.reduce((n,r) => n+bytes(r.response_text),0) <= 16384 && value.verifications.reduce((n,r) => n+bytes(r.note),0) <= 4096;
 }
 function historyValid(value,currentId) {
  if (value === null) return true;
  return keys(value,'schema_version,complete,reviews') && value.schema_version === 1 && typeof value.complete === 'boolean' && Array.isArray(value.reviews) && value.reviews.length <= 8 && bytes(JSON.stringify(value)) <= 65536 && new Set(value.reviews.map(r => r.review_id)).size === value.reviews.length && value.reviews.every(row => keys(row,'review_id,version,created_at,revision,state,decision_id,delivery_id,consumed_at,comments,feedback') && hex(row.review_id) && row.review_id !== currentId && versionValid(row.version) && date(row.created_at) && Number.isSafeInteger(row.revision) && row.revision >= 0 && row.state === 'consumida' && hex(row.decision_id) && hex(row.delivery_id) && date(row.consumed_at) && feedbackValid(row.feedback,row.comments));
 }
 function reviewValid(value) {
  if (!object(value)) return false;
  const unavailable = value.validity === 'unavailable';
  if (unavailable ? (value.current_version !== null || value.complete !== false || value.redacted !== null || value.controls_sanitized !== null) : (!versionValid(value.current_version) || value.complete !== true || typeof value.redacted !== 'boolean' || typeof value.controls_sanitized !== 'boolean')) return false;
  if (!hex(value.review_id) || !versionValid(value.version) || !Number.isSafeInteger(value.revision) || value.revision < 0 || !['pendiente','entregada','consumida'].includes(value.state) || !['current','version_changed','unavailable'].includes(value.validity) || !date(value.created_at) || !date(value.observed_at) || typeof value.initiative !== 'string' || value.artifact !== 'improvement-plan.md' || !['plan-ok','requested-review'].includes(value.gate_key) || !commentsValid(value.draft_comments)) return false;
  if (value.consumer_registration !== null && (!object(value.consumer_registration) || typeof value.consumer_registration.caller_id !== 'string' || !['claude-code','codex','opencode'].includes(value.consumer_registration.runtime) || !date(value.consumer_registration.registered_at))) return false;
  if (value.decision !== null && (!object(value.decision) || !hex(value.decision.decision_id) || !['approve','request_changes'].includes(value.decision.choice) || !commentsValid(value.decision.comments) || !date(value.decision.submitted_at))) return false;
  if (value.validity === 'current' && !sameVersion(value.version,value.current_version)) return false;
  if (value.sections !== undefined && (!Array.isArray(value.sections) || (unavailable ? value.sections.length !== 0 : value.sections.length < 1) || value.sections.length > 128 || !value.sections.every(row => object(row) && hex(row.section_id) && typeof row.title === 'string' && typeof row.text === 'string' && Number.isInteger(row.level) && row.level >= 0 && row.level <= 6) || new Set(value.sections.map(row => row.section_id)).size !== value.sections.length)) return false;
  if (value.feedback !== undefined && (!feedbackValid(value.feedback,value.decision ? value.decision.comments : []) || ((value.feedback.results.length || value.feedback.verifications.length) && (value.state !== 'consumida' || !object(value.ack) || !object(value.delivery) || value.ack.decision_id !== value.decision.decision_id || value.ack.delivery_id !== value.delivery.delivery_id)))) return false;
  if (value.feedback_history !== undefined && !historyValid(value.feedback_history,value.review_id)) return false;
  return true;
 }
 function controller(els, initialId, opts = {}) {
 const {status, metadata, versionText, sections, feedback, feedbackHistory, buttons} = els;
 const readOnly = !!opts.readOnly, onChange = opts.onChange || (() => {});
 let stopped = false;
 let reviewId = initialId;
 let current = null, inputs = [], blocked = true, closed = false, active = null, activeOperation = null, poll = null;
 let feedbackSnapshot = null, historySnapshot = null;
 function clearPoll() { if (poll !== null) clearTimeout(poll); poll = null; }
 function postActive() { return !!active && ['comments','submit','refresh'].includes(activeOperation); }
 function closedMessage() {
  if (current && current.decision) return 'Panel cerrado. Decisión ya registrada: '+(current.decision.choice === 'approve' ? 'aprobación de la vista' : 'petición de cambios')+'. Estado del recibo: '+current.state+'. Cerrar no modifica ni cancela esta decisión.';
  return 'Panel cerrado. Cerrar no crea una decisión ni cancela envíos anteriores; el borrador se conserva.';
 }
 function controls() {
  const editable = !readOnly && !stopped && current && inputs.length > 0 && !closed && !blocked && current.validity === 'current' && current.state === 'pendiente' && current.decision === null;
  for (const name of ['save','approve','changes']) buttons[name].disabled = !editable || !!active;
  for (const input of inputs) input.disabled = !editable || (!!active && activeOperation !== 'status');
  buttons.refresh.disabled = readOnly || closed || !!active || !hex(reviewId);
  buttons.close.disabled = postActive(); buttons.close.textContent = current && current.decision ? 'Cerrar panel' : 'Cerrar sin decidir';
  buttons.close.hidden = closed; buttons.open.hidden = !closed;
  sections.hidden = closed;
 }
 function schedule() {
  clearPoll();
  if (!opts.noPoll && !stopped && !closed && !document.hidden && !active && hex(reviewId)) poll = setTimeout(() => request('status'),5000);
 }
 function summary(review) {
  const consumer = review.consumer_registration ? 'Consumidor registrado; actividad desconocida.' : 'Sin consumidor registrado.';
  const redaction = review.redacted === null ? 'Redacción actual no disponible.' : review.redacted ? 'Vista redactada: la decisión no acredita lectura de secretos ocultos.' : 'Vista sin valores redactados.';
  const decision = review.decision ? ' Decisión registrada: '+(review.decision.choice === 'approve' ? 'aprobación de la vista' : 'petición de cambios')+' · '+review.decision.submitted_at+'.' : '';
  metadata.textContent = review.initiative+' · '+review.artifact+' · '+consumer+' '+redaction+(review.controls_sanitized ? ' Controles visuales saneados.' : '')+decision+' El hash y la capacidad no autentican a una persona.';
  versionText.textContent = 'Raw SHA-256: '+review.version.raw_sha256+'\nVista SHA-256: '+review.version.view_sha256+'\nVista: '+review.version.view_version+' · Creada: '+review.created_at+' · Leída: '+review.observed_at;
  if (closed) status.textContent = closedMessage();
  else if (review.validity === 'unavailable') status.textContent = 'Plan canónico no disponible. Recibo histórico: '+review.state+'. No permite continuar ni decidir sobre una vista ausente.';
  else if (review.validity === 'version_changed') status.textContent = 'La versión ha cambiado. El borrador de esta pestaña queda invalidado. Carga la versión actual explícitamente.'+(review.decision ? ' Recibo histórico: '+review.state+'.' : '');
  else if (blocked) status.textContent = 'Conflicto: otra pestaña cambió el borrador. Carga la revisión actual antes de decidir.';
  else if (review.state === 'consumida') status.textContent = 'Decisión consumida por el workflow. El ack acredita recepción; no acredita que los comentarios estén atendidos.';
  else if (review.state === 'entregada') status.textContent = 'Decisión entregada; pendiente de confirmación de consumo.';
  else if (review.decision) status.textContent = (review.decision.choice === 'approve' ? 'Vista aprobada.' : 'Cambios solicitados.')+' Decisión pendiente de consumo.';
  else status.textContent = readOnly ? 'Revisión abierta por otro proceso: se muestra en solo lectura, sin controles de escritura.' : 'Versión actual disponible. Comenta las secciones y decide sobre esta vista.';
 }
 function textNode(tag,text) { const node = document.createElement(tag); node.textContent = text; return node; }
 function producerText(producer) {
  return producer.runtime+' · '+producer.caller_id+' · '+(producer.actor_id === null ? 'Actor desconocido' : 'Actor declarado: '+producer.actor_id)+' · Identidad declarada; no acredita una persona ni presencia nativa.';
 }
 function resultNodes(value,comments) {
  if (!comments.length) return [textNode('p','Sin comentarios sellados en esta decisión.')];
  return comments.flatMap(comment => {
   const responses = value.results.filter(row => row.comment_id === comment.comment_id);
   if (!responses.length) {
    const card = document.createElement('article');
    card.append(textNode('h4','Comentario '+comment.comment_id+' · sin respuesta del agente'),textNode('p',comment.text));
    return [card];
   }
   return responses.map(row => {
   const card = document.createElement('article');
   const superseded = value.results.some(other => other.supersedes_result_id === row.result_id);
   const disposition = {addressed:'Atendido (declarado)',not_applied:'No aplicado (declarado)',needs_clarification:'Necesita aclaración (declarado)'}[row.disposition];
   card.append(textNode('h4','Comentario '+row.comment_id+' · '+disposition+(superseded ? ' · Resultado reemplazado' : '')));
   card.append(textNode('p',comment.text),textNode('p','Respuesta del agente:'),textNode('pre',row.response_text));
   card.append(textNode('p','Registrado: '+row.recorded_at+' · '+producerText(row.producer)));
   card.append(textNode('p',row.artifact_observation.status === 'available' ? 'Versión observada: '+row.artifact_observation.version.raw_sha256+' · '+row.artifact_observation.observed_at+'. No prueba el efecto del cambio.' : 'Plan no disponible al registrar este resultado · '+row.artifact_observation.observed_at+'.'));
   const annotation = value.verifications.find(v => v.result_id === row.result_id);
   if (annotation) {
    card.append(textNode('p','Resultado de verify-result (anotación humana opcional): '+(annotation.assessment === 'confirmed' ? 'confirmada' : 'no confirmada')+' (declarada) · '+annotation.recorded_at+'. No crea una puerta ni acredita identidad humana.'));
    card.append(textNode('p',producerText(annotation.producer)));
    if (annotation.note) card.append(textNode('pre',annotation.note));
   } else card.append(textNode('p','Sin verificación humana anotada. La respuesta puede entregarse sin esta anotación.'));
   return card;
   });
  });
 }
 function renderFeedback(review) {
  const comments = review.decision ? review.decision.comments : [];
  const snapshot = JSON.stringify([review.review_id,review.feedback,comments]);
  if (feedback && feedbackSnapshot !== snapshot) {
   feedback.replaceChildren(...(review.feedback === undefined ? [textNode('p','Resultados no disponibles en este bundle.')] : resultNodes(review.feedback,comments)));
   feedbackSnapshot = snapshot;
  }
  const history = review.feedback_history;
  const previous = JSON.stringify([review.review_id,history]);
  if (feedbackHistory && historySnapshot !== previous) {
   const nodes = [];
   if (history === null || history === undefined) nodes.push(textNode('p','Historial de resultados no disponible en esta proyección.'));
   else {
    if (!history.complete) nodes.push(textNode('p','Historial incompleto por límite de lectura; puede haber más resultados.'));
    for (const row of history.reviews) {
     const card = document.createElement('section');
     card.append(textNode('h3','Versión histórica · Revisión '+row.review_id),textNode('p','Raw SHA-256: '+row.version.raw_sha256+' · Vista SHA-256: '+row.version.view_sha256+' · Consumida: '+row.consumed_at));
     card.append(...resultNodes(row.feedback,row.comments)); nodes.push(card);
    }
    if (!history.reviews.length && history.complete) nodes.push(textNode('p','Sin resultados de otras versiones registrados.'));
   }
   feedbackHistory.replaceChildren(...nodes); historySnapshot = previous;
  }
 }
 function render(review) {
  inputs = []; sections.replaceChildren();
  const comments = review.decision ? review.decision.comments : review.draft_comments;
  const identities = new Set(comments.map(comment => comment.comment_id));
  review.sections.forEach((row,index) => {
   const part = document.createElement('section');
   const heading = document.createElement('h3'); heading.textContent = row.title || 'Sección '+(index+1);
   const body = document.createElement('pre'); body.textContent = row.text;
   part.append(heading,body);
   const existing = comments.filter(comment => comment.section_id === row.section_id);
   let suffix = 0, identifier = 'comment-'+index;
   while (identities.has(identifier)) identifier = 'comment-'+index+'-new-'+(++suffix);
   identities.add(identifier);
   const rows = existing.length ? existing : [{comment_id:identifier,text:''}];
   rows.forEach((comment,ordinal) => {
    const label = document.createElement('label'); label.textContent = 'Comentario '+(ordinal+1)+' sobre '+(row.title || 'sección '+(index+1));
    const input = document.createElement('textarea'); input.id = 'review-comment-'+index+'-'+ordinal; label.setAttribute('for',input.id);
    input.dataset.sectionId = row.section_id; input.dataset.commentId = comment.comment_id; input.value = comment.text;
    input.dataset.commentOrder = String(existing.length ? comments.indexOf(comment) : comments.length+index);
    inputs.push(input); part.append(label,input);
   });
   sections.append(part);
  });
 }
 function accept(data,operation) {
  if (!object(data) || data.schema_version !== 1 || !['ok','waiting','version_changed','conflict','unavailable'].includes(data.status)) throw Error('schema');
  if (data.status === 'conflict') {
   blocked = true; status.textContent = 'Conflicto: no se guardó una decisión nueva. Carga la revisión actual.'; return;
  }
  if (data.status === 'unavailable' && data.review === null) {
   blocked = true; status.textContent = 'Revisión no disponible. Puedes continuar mediante la confirmación del workflow existente.'; return;
  }
  const review = data.review;
  if (!reviewValid(review) || (operation !== 'refresh' && review.review_id !== reviewId) || (['view','refresh'].includes(operation) && review.validity === 'current' && !review.sections)) throw Error('schema');
  if ((data.status === 'unavailable' && review.validity !== 'unavailable') || (data.status === 'version_changed' && review.validity !== 'version_changed') || (['ok','waiting'].includes(data.status) && review.validity !== 'current')) throw Error('schema');
  if (operation === 'refresh') { reviewId = review.review_id; inputs = []; sections.replaceChildren(); }
  const changed = data.status === 'version_changed' || review.validity !== 'current' || (operation !== 'refresh' && current && !sameVersion(current.version,review.version));
  const concurrentDraft = operation === 'status' && current && review.revision !== current.revision && !review.decision;
  if (changed) {
   blocked = true;
   for (const input of inputs) input.value = '';
  } else if (concurrentDraft) blocked = true;
  else if (operation !== 'status') blocked = false;
  current = review;
  if (review.validity === 'unavailable') { inputs = []; sections.replaceChildren(); }
  if (review.sections && !changed) render(review);
  renderFeedback(review);
  summary(review);
  onChange(review);
 }
 async function request(operation,payload) {
  if (stopped || active || closed || document.hidden || !hex(reviewId)) return;
  clearPoll();
  const controller = new AbortController(); active = controller; activeOperation = operation; controls();
  const timeout = setTimeout(() => controller.abort(),4000);
  try {
   const response = await fetch('api/review/'+reviewId+'/'+operation, {
    method: payload ? 'POST' : 'GET', credentials:'omit', cache:'no-store', signal:controller.signal,
    ...(payload ? {headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)} : {})
   });
   const data = await response.json(); accept(data,operation);
  } catch {
   blocked = true; status.textContent = closed ? closedMessage() : 'No se pudo actualizar la revisión. Se conserva la última vista recibida; carga la versión actual antes de decidir.';
  } finally {
   clearTimeout(timeout); active = null; activeOperation = null; controls(); schedule();
  }
 }
 function collect() {
  const comments = inputs.filter(input => input.value.length).sort((a,b) => Number(a.dataset.commentOrder)-Number(b.dataset.commentOrder)).map(input => ({comment_id:input.dataset.commentId,section_id:input.dataset.sectionId,text:input.value}));
  if (!commentsValid(comments)) throw Error('limit');
  return comments;
 }
 function mutate(choice) {
  if (!current || blocked || closed || active || current.decision || current.state !== 'pendiente') return;
  let payload;
  try {
   payload = {version:current.version,comments:collect(),expected_revision:current.revision};
   if (choice) payload.choice = choice;
   if (choice === 'request_changes' && !payload.comments.some(row => row.text.trim())) { status.textContent = 'Añade al menos un comentario para pedir cambios.'; return; }
   if (new TextEncoder().encode(JSON.stringify(payload)).length > 16384) throw Error('limit');
  } catch { status.textContent = 'El comentario supera el límite: 2000 caracteres, 20 filas, 10 KiB de texto y 16 KiB de envío.'; return; }
  request(choice ? 'submit' : 'comments',payload);
 }
 buttons.save.addEventListener('click',() => mutate());
 buttons.approve.addEventListener('click',() => mutate('approve'));
 buttons.changes.addEventListener('click',() => mutate('request_changes'));
 buttons.refresh.addEventListener('click',() => request('refresh',{review_id:reviewId}));
 buttons.close.addEventListener('click',() => {
  if (postActive()) return;
  closed = true; clearPoll(); controls(); status.textContent = closedMessage(); buttons.open.focus();
 });
 buttons.open.addEventListener('click',() => { closed = false; controls(); request(current ? 'status' : 'view'); });
 document.addEventListener('visibilitychange',() => {
  if (stopped) return;
  clearPoll(); if (document.hidden) { if (active) active.abort(); } else if (!closed) request(current ? 'status' : 'view');
 });
 controls();
 function obsolete() {
  if (active || (blocked && status.textContent.startsWith('La versión ha cambiado'))) return;
  blocked = true; for (const input of inputs) input.value = '';
  status.textContent = 'La versión ha cambiado. El borrador de esta pestaña queda invalidado. Carga la versión actual explícitamente.'; controls();
 }
 if (opts.startObsolete) obsolete();
 else if (hex(reviewId)) request('view');
 else status.textContent = 'Revisión no disponible. Usa la confirmación del workflow existente.';
 return {obsolete, poke() { if (current) request('status'); }, stop() { stopped = true; clearPoll(); if (active) active.abort(); }, focused: () => inputs.some(input => input === document.activeElement)};
 }
 /* Estado de revisión por iniciativa para las tarjetas de Iniciativas (`page-iniciativas.js`): `api/review-summary` → `{id16: fila}`. */
 globalThis.PanelReview = {leerResumen(done) {
  fetch('api/review-summary',{credentials:'omit',cache:'no-store'}).then(r => { if (!r.ok) throw Error('unavailable'); return r.json(); }).then(d => {
   const rows = {};
   (object(d) && Array.isArray(d.initiatives) ? d.initiatives : []).forEach(row => { if (object(row) && /^[a-f0-9]{16}$/.test(row.initiative_id)) rows[row.initiative_id] = row; });
   done(rows);
  }).catch(() => done({}));
 }};
 const byId = id => document.getElementById(id);
 const legacy = byId('plan-review');
 if (legacy) controller({status:byId('review-status'),metadata:byId('review-metadata'),versionText:byId('review-version'),sections:byId('review-sections'),
  feedback:byId('review-feedback'),feedbackHistory:byId('review-feedback-history'),
  buttons:Object.fromEntries(['save','approve','changes','refresh','close','open'].map(name => [name, byId('review-'+name)]))},legacy.dataset.reviewId);
 /* Plan of ONE initiative (`#plan-revision`): the id16 comes from the server-published page, never from a path or a file name. */
 const STATES = {sin_revision:'sin revisión',pendiente:'pendiente',cambios_pedidos:'cambios pedidos',obsoleta:'obsoleta por cambio de versión',no_disponible:'no disponible'};
 const stateText = (estado,ordinal) => estado === 'aprobada' ? 'aprobada v'+(Number.isSafeInteger(ordinal) && ordinal > 0 ? ordinal : 1) : STATES[estado];
 const host = byId('plan-revision');
 if (host && host.dataset.revision === 'activa') {
  const header = byId('plan-revision-estado'), button = byId('plan-revisar');
  let initiative = host.dataset.initiativeId;
  if (!/^[a-f0-9]{16}$/.test(initiative || '')) {
   try { initiative = JSON.parse(byId('panel-data').textContent).plan_id; } catch { initiative = null; }
  }
  const element = (tag,text) => { const node = document.createElement(tag); if (text !== undefined) node.textContent = text; return node; };
  let mounted = null, mountedId = null, mountedReadOnly = null, busy = false, timer = null, announce = '';
  const fetchJson = async (url,init) => {
   const controller = new AbortController(), guard = setTimeout(() => controller.abort(),4000);
   try { const response = await fetch(url,{credentials:'omit',cache:'no-store',signal:controller.signal,...init}); return await response.json(); }
   finally { clearTimeout(guard); }
  };
  const currentValid = data => object(data) && data.schema_version === 1 && ['ok','unavailable'].includes(data.status) && data.initiative_id === initiative && typeof data.estado === 'string' && data.estado in {...STATES,aprobada:1} && typeof data.escritura === 'boolean' && (data.review_id === null || hex(data.review_id));
  function mount(reviewIdentity,readOnly,obsoleteNow) {
   if (mounted && mountedId === reviewIdentity && mountedReadOnly === readOnly) return;
   if (mounted && mounted.focused()) return;
   if (mounted) mounted.stop();
   const els = {status:element('p'),metadata:element('p'),versionText:element('pre'),sections:element('div'),feedback:element('div'),feedbackHistory:element('div')};
   els.status.setAttribute('role','status'); els.status.setAttribute('aria-live','polite');
   els.feedback.setAttribute('aria-live','polite'); els.feedbackHistory.setAttribute('aria-live','polite');
   const actions = element('div'); actions.className = 'review-actions';
   els.buttons = {};
   for (const [name,label] of [['save','Guardar comentarios'],['approve','Aprobar'],['changes','Pedir correcciones'],['refresh','Cargar versión actual'],['close','Cerrar sin decidir'],['open','Volver a la revisión']]) {
    const control = element('button',label); control.setAttribute('type','button'); control.disabled = name !== 'close' && name !== 'open'; els.buttons[name] = control;
    if (readOnly && ['save','approve','changes','refresh'].includes(name)) control.hidden = true;
    if (name === 'open') control.hidden = true;
    actions.append(control);
   }
   const holder = element('div'); holder.id = 'plan-revision-panel';
   holder.append(els.status,els.metadata,els.versionText,els.sections,actions,element('h3','Respuestas del agente a tus comentarios'),els.feedback,element('h3','Respuestas de versiones anteriores'),els.feedbackHistory);
   const old = byId('plan-revision-panel'); if (old) old.replaceWith(holder); else host.append(holder);
   mounted = controller(els,reviewIdentity,{readOnly,noPoll:true,startObsolete:obsoleteNow,onChange:() => schedule(0,false)}); mountedId = reviewIdentity; mountedReadOnly = readOnly;
  }
  function paint(data,poke) {
   const text = stateText(data.estado,data.version_ordinal);
   header.textContent = 'Estado de la revisión: '+text+(announce ? ' · '+announce : '');
   button.hidden = !(data.estado === 'sin_revision' && data.escritura === false && data.review_id === null) || busy;
   if (hex(data.review_id)) {
    const fresh = !(mounted && mountedId === data.review_id);
    mount(data.review_id,!data.escritura,data.estado === 'obsoleta');
    if (mounted && mountedId === data.review_id && !fresh) { if (data.estado === 'obsoleta') mounted.obsolete(); else if (poke && data.estado !== 'no_disponible') mounted.poke(); }
   }
  }
  async function load(poke = true) {
   timer = null;
   if (busy || document.hidden || !/^[a-f0-9]{16}$/.test(initiative || '')) return;
   try {
    const data = await fetchJson('api/review-current/'+initiative);
    if (!currentValid(data)) throw Error('schema');
    paint(data,poke);
   } catch { header.textContent = 'Estado de la revisión: no se pudo leer; se conserva la última vista.'; }
   schedule(5000);
  }
  function schedule(delay,poke = true) { if (timer !== null) clearTimeout(timer); timer = setTimeout(() => load(poke),delay); }
  button.addEventListener('click',async () => {
   if (busy) return;
   busy = true; button.disabled = true; announce = ''; header.textContent = 'Abriendo la revisión…';
   try {
    const data = await fetchJson('api/review-open/'+initiative,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({initiative_id:initiative})});
    announce = object(data) && data.status === 'ok' && hex(data.review_id) ? 'revisión abierta' : 'no se pudo abrir la revisión'+(object(data) && typeof data.reason === 'string' ? ' ('+data.reason.slice(0,64)+')' : '');
   } catch { announce = 'no se pudo abrir la revisión'; }
   busy = false; button.disabled = false; await load(false); button.focus();
  });
  document.addEventListener('visibilitychange',() => { if (!document.hidden) schedule(0); else if (timer !== null) { clearTimeout(timer); timer = null; } });
  if (initiative) load(); else header.textContent = 'Estado de la revisión: no disponible.';
 }
})();
