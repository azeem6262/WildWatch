// Global State
window.appState = {
  currentSessionId: null
};

// Screen Routing
function showScreen(screenId) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById(screenId).classList.add('active');
  
  if (window.Results && typeof window.Results.closeReviewModal === 'function') {
    window.Results.closeReviewModal();
  }
}

// Sidebar initialization
async function loadSessions() {
  try {
    const sessions = await window.API.getSessions();
    const list = document.getElementById('session-list');
    list.innerHTML = '';
    sessions.forEach(s => {
      const li = document.createElement('li');
      li.textContent = `${s.name} (${s.camera_id})`;
      li.onclick = () => window.Results.load(s.id);
      list.appendChild(li);
    });
  } catch (err) {
    console.error("Failed to load sessions", err);
  }
}

document.getElementById('btn-new-session').onclick = () => {
  showScreen('screen-new-session');
  document.getElementById('form-new-session').reset();
};

// Init
loadSessions();
