window.Progress = {
  start(sessionId) {
    const evtSource = new EventSource(`http://localhost:8765/detect/${sessionId}`);
    
    document.getElementById('progress-fill').style.width = '0%';
    document.getElementById('progress-percent').textContent = '0.0%';
    
    evtSource.onmessage = function(event) {
      const data = JSON.parse(event.data);
      
      if (data.type === 'progress') {
        document.getElementById('progress-fill').style.width = `${data.percent}%`;
        document.getElementById('progress-percent').textContent = `${data.percent}%`;
        document.getElementById('progress-count').textContent = `${data.done} / ${data.total}`;
        document.getElementById('current-filename').textContent = data.current_file;
        document.getElementById('current-stage').textContent = data.stage;
      } 
      else if (data.type === 'result') {
        if (data.result !== 'Absent') {
          const el = document.getElementById('live-animals');
          el.textContent = parseInt(el.textContent) + 1;
        } else {
          const el = document.getElementById('live-empty');
          el.textContent = parseInt(el.textContent) + 1;
        }
      }
      else if (data.type === 'error') {
        const el = document.getElementById('live-errors');
        el.textContent = parseInt(el.textContent) + 1;
      }
      else if (data.type === 'complete') {
        evtSource.close();
        window.Results.load(sessionId);
      }
    };
    
    evtSource.onerror = function() {
      evtSource.close();
      alert("Lost connection to processing backend.");
    };
  }
};
