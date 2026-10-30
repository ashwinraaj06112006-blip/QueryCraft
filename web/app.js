const query = document.querySelector('#query');
const statusBox = document.querySelector('#status');
const workbench = document.querySelector('#workbench');
let uploadedSchema = null;

function showStatus(message, type) {
  statusBox.textContent = message;
  statusBox.className = `status ${type}`;
}

function renderTable(columns, rows) {
  const container = document.querySelector('#table');
  if (!rows.length) { container.textContent = 'The query completed successfully, but returned no rows.'; return; }
  const headers = columns.map(column => `<th>${column}</th>`).join('');
  const body = rows.map(row => `<tr>${columns.map(column => `<td>${row[column]}</td>`).join('')}</tr>`).join('');
  container.innerHTML = `<table><thead><tr>${headers}</tr></thead><tbody>${body}</tbody></table>`;
}

function escapeHtml(value) { return String(value).replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char])); }

function renderSchema(schema) {
  const target = document.querySelector('#schema');
  target.innerHTML = `<strong>${escapeHtml(schema.file_name)}</strong> · ${schema.row_count.toLocaleString()} rows · table <code>${schema.table}</code><div class="chips">${schema.columns.map(column => `<span>${escapeHtml(column.name)} <em>${escapeHtml(column.type)}</em></span>`).join('')}</div>`;
  target.classList.remove('hidden');
}

function renderRetrieval(items) {
  const target = document.querySelector('#retrieval');
  target.innerHTML = items.length ? `<div class="chips">${items.map(item => `<span>${escapeHtml(item.name)} <em>${escapeHtml(item.type)} · ${escapeHtml(item.reason)}</em></span>`).join('')}</div>` : 'The fixed demonstration schema does not use schema retrieval.';
}

async function upload() {
  const input = document.querySelector('#dataset');
  if (!input.files.length) { showStatus('Choose a CSV, XLSX or JSON file first.', 'error'); return; }
  const body = new FormData(); body.append('dataset', input.files[0]);
  showStatus('Importing file and deriving schema...', 'success');
  try {
    const response = await fetch('/api/upload', {method: 'POST', body});
    const data = await response.json();
    if (!data.ok) throw new Error(data.message);
    uploadedSchema = data.schema; renderSchema(uploadedSchema);
    query.value = 'Show all records';
    showStatus(data.message + ' You can now query the uploaded data.', 'success');
  } catch (error) { showStatus(`Upload failed: ${error.message}`, 'error'); }
}

async function compile() {
  showStatus('Compiling query...', 'success');
  workbench.classList.add('hidden');
  try {
    const response = await fetch('/api/compile', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({query: query.value, mode: uploadedSchema ? 'uploaded' : 'demo'})});
    const data = await response.json();
    if (!data.ok) {
      showStatus(`${data.error_type}: ${data.message} ${data.suggestion ? 'Suggestion: ' + data.suggestion : ''}`, 'error');
      return;
    }
    showStatus(data.message, 'success');
    document.querySelector('#tokens').textContent = data.tokens.map(token => `${token.kind}(${token.value})`).join(', ');
    document.querySelector('#ast').textContent = JSON.stringify(data.ast, null, 2);
    document.querySelector('#sql').textContent = data.sql;
    renderRetrieval(data.retrieval || []);
    renderTable(data.columns, data.rows);
    workbench.classList.remove('hidden');
  } catch (error) {
    showStatus(`Request failed: ${error.message}`, 'error');
  }
}

document.querySelector('#compile').addEventListener('click', compile);
document.querySelector('#upload').addEventListener('click', upload);
document.querySelector('#example').addEventListener('click', () => { query.value = uploadedSchema ? 'Show top 5 records by salary' : 'Show top 5 students by CGPA'; });
