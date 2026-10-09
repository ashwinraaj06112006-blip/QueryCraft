const query = document.querySelector('#query');
const statusBox = document.querySelector('#status');
const workbench = document.querySelector('#workbench');

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

async function compile() {
  showStatus('Compiling query...', 'success');
  workbench.classList.add('hidden');
  try {
    const response = await fetch('/api/compile', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({query: query.value})});
    const data = await response.json();
    if (!data.ok) {
      showStatus(`${data.error_type}: ${data.message} ${data.suggestion ? 'Suggestion: ' + data.suggestion : ''}`, 'error');
      return;
    }
    showStatus(data.message, 'success');
    document.querySelector('#tokens').textContent = data.tokens.map(token => `${token.kind}(${token.value})`).join(', ');
    document.querySelector('#ast').textContent = JSON.stringify(data.ast, null, 2);
    document.querySelector('#sql').textContent = data.sql;
    renderTable(data.columns, data.rows);
    workbench.classList.remove('hidden');
  } catch (error) {
    showStatus(`Request failed: ${error.message}`, 'error');
  }
}

document.querySelector('#compile').addEventListener('click', compile);
document.querySelector('#example').addEventListener('click', () => { query.value = 'Show top 5 students by CGPA'; });
