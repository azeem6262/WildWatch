document.addEventListener("DOMContentLoaded", () => {
  const btnSettings = document.getElementById("btn-settings");
  const modalSettings = document.getElementById("settings-modal");
  const btnSettingsClose = document.getElementById("btn-settings-close");
  const btnSettingsSave = document.getElementById("btn-settings-save");
  const inputApiKey = document.getElementById("gemini-api-key");
  const indicatorSave = document.getElementById("settings-save-indicator");

  // Open settings modal
  btnSettings.addEventListener("click", async () => {
    modalSettings.classList.remove("hidden");
    
    // Fetch current key
    try {
      const response = await fetch(`${API_BASE}/settings/gemini`);
      if (response.ok) {
        const data = await response.json();
        if (data.is_set) {
          inputApiKey.value = data.api_key;
        }
      }
    } catch (e) {
      console.error("Failed to load Gemini API key:", e);
    }
  });

  // Close settings modal
  btnSettingsClose.addEventListener("click", () => {
    modalSettings.classList.add("hidden");
    indicatorSave.style.opacity = "0";
  });

  // Close when clicking outside modal
  modalSettings.addEventListener("click", (e) => {
    if (e.target === modalSettings) {
      modalSettings.classList.add("hidden");
      indicatorSave.style.opacity = "0";
    }
  });

  // Save key
  btnSettingsSave.addEventListener("click", async () => {
    const key = inputApiKey.value.trim();
    
    // Always disabled the button while saving
    btnSettingsSave.disabled = true;
    btnSettingsSave.textContent = "Saving...";

    try {
      const response = await fetch(`${API_BASE}/settings/gemini`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ api_key: key })
      });

      if (response.ok) {
        indicatorSave.style.opacity = "1";
        setTimeout(() => {
          indicatorSave.style.opacity = "0";
        }, 3000);
      } else {
        alert("Failed to save API key.");
      }
    } catch (e) {
      console.error("Failed to save key:", e);
      alert("Error saving API key. Is the backend running?");
    } finally {
      btnSettingsSave.disabled = false;
      btnSettingsSave.textContent = "Save Key";
    }
  });
});
