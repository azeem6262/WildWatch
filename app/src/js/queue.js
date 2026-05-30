window.Queue = {
  selectedFolder: null,
  
  reset() {
    this.selectedFolder = null;
    document.getElementById('queue-stats').classList.add('hidden');
    document.getElementById('queue-actions').classList.add('hidden');
    document.querySelector('#drop-zone h3').textContent = "Select SD card folder here";
  }
};

const dropZone = document.getElementById('drop-zone');
const folderInput = document.getElementById('folder-input');

dropZone.onclick = () => folderInput.click();

folderInput.onchange = async (e) => {
  if (!e.target.files.length) return;
  
  const firstFile = e.target.files[0];
  // Extract folder path from the file's absolute path provided by Tauri
  const folderPath = firstFile.path.replace(/[^\\/]+$/, '');
  
  window.Queue.selectedFolder = folderPath;
  document.querySelector('#drop-zone h3').textContent = folderPath;
  
  // Ingest
  try {
    const res = await window.API.ingestFiles({
      session_id: window.appState.currentSessionId,
      folder_path: folderPath
    });
    
    document.getElementById('stat-total').textContent = res.stats.total;
    document.getElementById('stat-photos').textContent = res.stats.photos;
    document.getElementById('stat-videos').textContent = res.stats.videos;
    
    document.getElementById('queue-stats').classList.remove('hidden');
    
    if (res.stats.total > 0) {
      document.getElementById('queue-actions').classList.remove('hidden');
    }
  } catch (err) {
    alert("Ingest error: " + err.message);
  }
};

document.getElementById('btn-start-processing').onclick = () => {
  showScreen('screen-progress');
  window.Progress.start(window.appState.currentSessionId);
};
