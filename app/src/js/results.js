window.Results = {
  currentSessionId: null,
  
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
      
      files.forEach(f => {
        if (f.status === 'done') {
          if (f.animal_detected) animals++;
          else empty++;
          
          const tr = document.createElement('tr');
          tr.innerHTML = `
            <td>${f.filename}</td>
            <td>${f.file_type}</td>
            <td>${f.file_date || '-'}</td>
            <td>${f.csv_result}</td>
            <td>${f.csv_count}</td>
            <td>${(f.detection_confidence * 100).toFixed(1)}%</td>
          `;
          tbody.appendChild(tr);
        }
      });
      
      document.getElementById('res-total').textContent = (animals + empty);
      document.getElementById('res-animals').textContent = animals;
      document.getElementById('res-empty').textContent = empty;
      
    } catch (err) {
      alert("Error loading results: " + err.message);
    }
  }
};

document.getElementById('btn-export-csv').onclick = () => {
  if (window.Results.currentSessionId) {
    window.location.href = `http://localhost:8765/export/csv/${window.Results.currentSessionId}`;
  }
};
