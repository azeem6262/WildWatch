// Helper API wrapper
const API_BASE = 'http://localhost:8765';

async function apiFetch(endpoint, options = {}) {
  try {
    const res = await fetch(`${API_BASE}${endpoint}`, options);
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'API Error');
    }
    return await res.json();
  } catch (error) {
    console.error(`API Error on ${endpoint}:`, error);
    throw error;
  }
}

window.API = {
  createSession: (data) => apiFetch('/sessions/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  }),
  getSessions: () => apiFetch('/sessions/'),
  getSession: (id) => apiFetch(`/sessions/${id}`),
  ingestFiles: (data) => apiFetch('/files/ingest', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  }),
  getFiles: (id) => apiFetch(`/files/${id}`),
  overrideSpecies: (fileId, species) => apiFetch(`/files/${fileId}/override`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ species })
  })
};
