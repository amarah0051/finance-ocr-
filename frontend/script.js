const form = document.getElementById('upload-form');
const statusBox = document.getElementById('status');
const submitBtn = document.getElementById('submit-btn');
const fileInput = document.getElementById('pdf');
const fileMsg = document.querySelector('.file-msg');

function setStatus(message, isError = false) {
  statusBox.style.display = 'block';
  statusBox.className = 'status'; // Reset classes
  statusBox.classList.add(isError ? 'error' : 'success');
  statusBox.innerHTML = message;
}

// Update file message when a file is selected
fileInput.addEventListener('change', (e) => {
  if (fileInput.files.length > 0) {
    fileMsg.textContent = fileInput.files[0].name;
    fileMsg.style.color = 'var(--text-main)';
    fileMsg.style.fontWeight = '600';
  } else {
    fileMsg.textContent = 'or drag and drop here';
    fileMsg.style.color = 'var(--text-mute)';
    fileMsg.style.fontWeight = '400';
  }
});

form.addEventListener('submit', async (e) => {
  e.preventDefault();

  const workbookId = document.getElementById('workbookId').value.trim();

  if (!fileInput.files.length) {
    setStatus('Please choose a PDF file.', true);
    return;
  }

  const formData = new FormData();
  formData.append('pdf', fileInput.files[0]);
  if (workbookId) {
    formData.append('workbook_id', workbookId);
  }

  // UI Loading State
  submitBtn.disabled = true;
  submitBtn.querySelector('.btn-text').textContent = 'Processing...';
  submitBtn.querySelector('.loader').style.display = 'block';
  statusBox.style.display = 'none';

  try {
    const response = await fetch('/api/upload', {
      method: 'POST',
      body: formData,
    });

    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.detail || 'Upload failed');
    }

    setStatus(
      `<strong>Success!</strong> Extraction completed.<br>` +
      `Workbook ID: <code>${result.workbook_id}</code><br>` +
      `Rows added: <strong>${result.rows_added}</strong><br>` +
      `<a href="${result.download_url}" target="_blank">Download Updated Excel</a>`
    );
  } catch (error) {
    setStatus(`<strong>Error:</strong> ${error.message}`, true);
  } finally {
    submitBtn.disabled = false;
    submitBtn.querySelector('.btn-text').textContent = 'Process & Generate';
    submitBtn.querySelector('.loader').style.display = 'none';
  }
});
