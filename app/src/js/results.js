window.Results = {
  currentSessionId: null,
  currentReviewId: null,
  
  async load(sessionId) {
    this.currentSessionId = sessionId;
    showScreen('screen-results');
    
    try {
      const session = await window.API.getSession(sessionId);
      document.getElementById('results-session-name').textContent = `${session.name} (${session.camera_id})`;
      
      const files = await window.API.getFiles(sessionId);
      
      let animals = 0;
      let empty = 0;
      
      const tbody = document.getElementById('results-tbody');
      tbody.innerHTML = '';
      
      const { convertFileSrc } = window.__TAURI__.core;
      
      files.forEach(f => {
        if (f.status === 'done') {
          if (f.animal_detected) animals++;
          else empty++;
          
          let speciesDisplayHtml = `
            <input type="text" 
                   class="inline-species-input" 
                   data-id="${f.id}" 
                   value="${f.csv_result.replace(/"/g, '&quot;')}" 
                   title="Click to edit">
          `;
          
          if (f.manually_verified) {
            speciesDisplayHtml += `<span class="verified-icon" title="Manually Verified">✓</span>`;
          } else if (f.needs_review) {
            speciesDisplayHtml += `<span class="review-icon" title="Needs Review">⚠️</span>`;
          }
          
          let thumbnailSrc = '';
          let previewSrc = '';
          if (f.best_frame_path) {
            thumbnailSrc = `http://localhost:8765/files/image/serve?path=${encodeURIComponent(f.best_frame_path)}`;
            previewSrc = f.best_frame_path;
          } else if (f.file_type === 'photo') {
            thumbnailSrc = `http://localhost:8765/files/image/serve?path=${encodeURIComponent(f.filepath)}`;
            previewSrc = f.filepath;
          }
          
          const tr = document.createElement('tr');
          tr.id = `row-${f.id}`;
          
          const tdThumb = document.createElement('td');
          tdThumb.className = 'thumb-cell';
          if (thumbnailSrc) {
            const img = document.createElement('img');
            img.src = thumbnailSrc;
            img.className = 'thumbnail-img';
            img.dataset.id = f.id;
            img.dataset.path = previewSrc;
            img.dataset.filename = f.filename;
            img.dataset.source = f.species_source || 'speciesnet';
            img.dataset.conf = (f.detection_confidence * 100).toFixed(1);
            img.onclick = () => window.Results.openPreviewModal(img);
            tdThumb.appendChild(img);
          } else {
            tdThumb.innerHTML = `<div class="thumbnail-placeholder"></div>`;
          }
          
          const thumbHtml = tdThumb.innerHTML;

          const confValue = f.detection_confidence * 100;
          let confClass = 'conf-low';
          if (confValue >= 80) confClass = 'conf-high';
          else if (confValue >= 60) confClass = 'conf-med';

          tr.innerHTML = `
            <td>${f.filename}</td>
            <td><span class="type-badge ${f.file_type.toLowerCase()}">${f.file_type}</span></td>
            <td>${f.file_date || '-'}</td>
            <td class="species-cell" id="species-cell-${f.id}">${speciesDisplayHtml}</td>
            <td>${f.csv_count}</td>
            <td><span class="${confClass}">${confValue.toFixed(1)}%</span></td>
          `;
          
          tr.prepend(tdThumb);
          tbody.appendChild(tr);
        }
      });
      
      document.getElementById('res-total').textContent = (animals + empty);
      document.getElementById('res-animals').textContent = animals;
      document.getElementById('res-empty').textContent = empty;
      
      // Attach events to thumbnails
      document.querySelectorAll('.thumbnail-img').forEach(img => {
        img.onclick = () => window.Results.openPreviewModal(img);
      });
      
      // Attach events to inline inputs
      document.querySelectorAll('.inline-species-input').forEach(input => {
        input.addEventListener('change', (e) => window.Results.saveOverride(e.target.dataset.id, e.target.value));
        input.addEventListener('keydown', (e) => {
          if (e.key === 'Enter') input.blur();
        });
      });
      
    } catch (err) {
      alert("Error loading results: " + err.message);
    }
  },
  
  openPreviewModal(imgEl) {
    this.currentReviewId = imgEl.dataset.id;
    const imgUrl = `http://localhost:8765/files/image/serve?path=${encodeURIComponent(imgEl.dataset.path)}`;
    
    document.getElementById('preview-filename').textContent = imgEl.dataset.filename;
    document.getElementById('preview-image').src = imgUrl;
    document.getElementById('preview-source').textContent = imgEl.dataset.source;
    document.getElementById('preview-confidence').textContent = imgEl.dataset.conf + '%';
    
    const tableInput = document.querySelector(`.inline-species-input[data-id="${this.currentReviewId}"]`);
    const previewInput = document.getElementById('preview-species-input');
    previewInput.value = tableInput ? tableInput.value : '';
    
    document.getElementById('preview-modal').classList.remove('hidden');
    
    const row = document.getElementById(`row-${this.currentReviewId}`);
    if (row) row.classList.add('reviewing-row');
  },
  
  closePreviewModal() {
    document.getElementById('preview-modal').classList.add('hidden');
    if (this.currentReviewId) {
      const row = document.getElementById(`row-${this.currentReviewId}`);
      if (row) row.classList.remove('reviewing-row');
    }
    this.currentReviewId = null;
  },
  
  async saveOverride(fileId, newSpecies) {
    if (!newSpecies || newSpecies.trim() === '') return;
    
    try {
      const res = await window.API.overrideSpecies(fileId, newSpecies);
      
      // Update inline input value
      const tableInput = document.querySelector(`.inline-species-input[data-id="${fileId}"]`);
      if (tableInput) tableInput.value = res.new_species;
      
      // Update overlay input if open
      if (this.currentReviewId == fileId) {
        document.getElementById('preview-species-input').value = res.new_species;
        const ind = document.getElementById('preview-save-indicator');
        ind.style.opacity = 1;
        setTimeout(() => ind.style.opacity = 0, 2000);
      }
      
      // Replace warning flag with checkmark
      const cell = document.getElementById(`species-cell-${fileId}`);
      if (cell) {
        const warn = cell.querySelector('.review-icon');
        if (warn) warn.remove();
        if (!cell.querySelector('.verified-icon')) {
          cell.innerHTML += `<span class="verified-icon" title="Manually Verified">✓</span>`;
        }
      }
      
    } catch(err) {
      alert("Failed to override: " + err.message);
    }
  }
};

// Preview Modal Events
document.getElementById('btn-preview-close').onclick = () => window.Results.closePreviewModal();
document.getElementById('preview-modal').onclick = (e) => {
  if (e.target.id === 'preview-modal') window.Results.closePreviewModal();
};
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && !document.getElementById('preview-modal').classList.contains('hidden')) {
    window.Results.closePreviewModal();
  }
});

// Overlay Input Edit
document.getElementById('preview-species-input').addEventListener('change', (e) => {
  if (window.Results.currentReviewId) {
    window.Results.saveOverride(window.Results.currentReviewId, e.target.value);
  }
});
document.getElementById('preview-species-input').addEventListener('keydown', (e) => {
  if (e.key === 'Enter') e.target.blur();
});

document.getElementById('btn-export-csv').onclick = async () => {
  if (window.Results.currentSessionId) {
    try {
      const response = await fetch(`http://localhost:8765/export/csv/${window.Results.currentSessionId}`);
      if (!response.ok) throw new Error("Failed to export CSV");
      
      alert("Export complete! The CSV file has been saved and the folder is now open on your screen.");
    } catch (err) {
      alert("Error exporting CSV: " + err.message);
    }
  }
};
