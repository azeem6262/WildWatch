document.getElementById('form-new-session').onsubmit = async (e) => {
  e.preventDefault();
  const name = document.getElementById('session-name').value;
  const camera_id = document.getElementById('camera-id').value;
  const location = document.getElementById('location-notes').value;

  try {
    const res = await window.API.createSession({ name, camera_id, location });
    window.appState.currentSessionId = res.id;
    
    // Refresh sidebar
    loadSessions();
    
    // Move to queue screen
    showScreen('screen-queue');
    window.Queue.reset();
  } catch (err) {
    alert("Error creating session: " + err.message);
  }
};
