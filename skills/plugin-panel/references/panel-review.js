/* The common owner alone decides version validity and receipt transitions. */
(() => {
 'use strict';
 const root = document.getElementById('plan-review');
 if (!root) return;
 const status = document.getElementById('review-status');
 const metadata = document.getElementById('review-metadata');
 const versionText = document.getElementById('review-version');
 const sections = document.getElementById('review-sections');
 const buttons = Object.fromEntries(['save','approve','changes','refresh','close','open'].map(name => [name, document.getElementById('review-'+name)]));
 const hex = value => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
 const date = value => typeof value === 'string' && /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z$/.test(value) && Number.isFinite(Date.parse(value));
 const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
 const versionValid = value => object(value) && Object.keys(value).sort().join(',') === 'raw_sha256,view_sha256,view_version' && hex(value.raw_sha256) && hex(value.view_sha256) && value.view_version === 'plan-text-v1';
 const sameVersion = (a,b) => a.raw_sha256 === b.raw_sha256 && a.view_sha256 === b.view_sha256 && a.view_version === b.view_version;
 const commentValid = row => object(row) && typeof row.comment_id === 'string' && /^[A-Za-z0-9_-]{1,64}$/.test(row.comment_id) && hex(row.section_id) && typeof row.text === 'string' && [...row.text].length <= 2000;
 const commentsValid = rows => Array.isArray(rows) && rows.length <= 20 && rows.every(commentValid) && new Set(rows.map(row => row.comment_id)).size === rows.length && rows.reduce((n,row) => n+new TextEncoder().encode(row.text).length,0) <= 10240;
 function reviewValid(value) {
  if (!object(value)) return false;
  const unavailable = value.validity === 'unavailable';
  if (unavailable ? (value.current_version !== null || value.complete !== false || value.redacted !== null || value.controls_sanitized !== null) : (!versionValid(value.current_version) || value.complete !== true || typeof value.redacted !== 'boolean' || typeof value.controls_sanitized !== 'boolean')) return false;
  if (!hex(value.review_id) || !versionValid(value.version) || !Number.isSafeInteger(value.revision) || value.revision < 0 || !['pendiente','entregada','consumida'].includes(value.state) || !['current','version_changed','unavailable'].includes(value.validity) || !date(value.created_at) || !date(value.observed_at) || typeof value.initiative !== 'string' || value.artifact !== 'improvement-plan.md' || !['plan-ok','requested-review'].includes(value.gate_key) || !commentsValid(value.draft_comments)) return false;
  if (value.consumer_registration !== null && (!object(value.consumer_registration) || typeof value.consumer_registration.caller_id !== 'string' || !['claude-code','codex','opencode'].includes(value.consumer_registration.runtime) || !date(value.consumer_registration.registered_at))) return false;
  if (value.decision !== null && (!object(value.decision) || !hex(value.decision.decision_id) || !['approve','request_changes'].includes(value.decision.choice) || !commentsValid(value.decision.comments) || !date(value.decision.submitted_at))) return false;
  if (value.validity === 'current' && !sameVersion(value.version,value.current_version)) return false;
  if (value.sections !== undefined && (!Array.isArray(value.sections) || (unavailable ? value.sections.length !== 0 : value.sections.length < 1) || value.sections.length > 128 || !value.sections.every(row => object(row) && hex(row.section_id) && typeof row.title === 'string' && typeof row.text === 'string' && Number.isInteger(row.level) && row.level >= 0 && row.level <= 6) || new Set(value.sections.map(row => row.section_id)).size !== value.sections.length)) return false;
  return true;
 }
 let reviewId = root.dataset.reviewId;
 let current = null, inputs = [], blocked = true, closed = false, active = null, activeOperation = null, poll = null;
 function clearPoll() { if (poll !== null) clearTimeout(poll); poll = null; }
 function postActive() { return !!active && ['comments','submit','refresh'].includes(activeOperation); }
 function closedMessage() {
  if (current && current.decision) return 'Panel cerrado. Decisión ya registrada: '+(current.decision.choice === 'approve' ? 'aprobación de la vista' : 'petición de cambios')+'. Estado del recibo: '+current.state+'. Cerrar no modifica ni cancela esta decisión.';
  return 'Panel cerrado. Cerrar no crea una decisión ni cancela envíos anteriores; el borrador se conserva.';
 }
 function controls() {
  const editable = current && inputs.length > 0 && !closed && !blocked && current.validity === 'current' && current.state === 'pendiente' && current.decision === null;
  for (const name of ['save','approve','changes']) buttons[name].disabled = !editable || !!active;
  for (const input of inputs) input.disabled = !editable || (!!active && activeOperation !== 'status');
  buttons.refresh.disabled = closed || !!active || !hex(reviewId);
  buttons.close.disabled = postActive(); buttons.close.textContent = current && current.decision ? 'Cerrar panel' : 'Cerrar sin decidir';
  buttons.close.hidden = closed; buttons.open.hidden = !closed;
  sections.hidden = closed;
 }
 function schedule() {
  clearPoll();
  if (!closed && !document.hidden && !active && hex(reviewId)) poll = setTimeout(() => request('status'),5000);
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
  else if (review.state === 'consumida') status.textContent = 'Decisión consumida por el workflow. Se conserva el recibo histórico.';
  else if (review.state === 'entregada') status.textContent = 'Decisión entregada; pendiente de confirmación de consumo.';
  else if (review.decision) status.textContent = (review.decision.choice === 'approve' ? 'Vista aprobada.' : 'Cambios solicitados.')+' Decisión pendiente de consumo.';
  else status.textContent = 'Versión actual disponible. Comenta las secciones y decide sobre esta vista.';
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
  summary(review);
 }
 async function request(operation,payload) {
  if (active || closed || document.hidden || !hex(reviewId)) return;
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
   blocked = true; status.textContent = closed ? closedMessage() : 'No se pudo actualizar la revisión. Carga la versión actual antes de decidir.';
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
  clearPoll(); if (document.hidden) { if (active) active.abort(); } else if (!closed) request(current ? 'status' : 'view');
 });
 controls();
 if (hex(reviewId)) request('view');
 else status.textContent = 'Revisión no disponible. Usa la confirmación del workflow existente.';
})();
