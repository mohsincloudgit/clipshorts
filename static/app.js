// ViralShorts Studio PRO Frontend Application

document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const urlInput = document.getElementById("video-url");
  const btnPaste = document.getElementById("btn-paste");
  const durationSelect = document.getElementById("clip-duration");
  const reframeSelect = document.getElementById("reframe-mode");
  const captionSelect = document.getElementById("caption-style");
  const aiProviderSelect = document.getElementById("ai-provider");

  // Advanced feature elements
  const toggleAntiCopyright = document.getElementById("toggle-anti-copyright");
  const btnUploadLogo = document.getElementById("btn-upload-logo");
  const logoFileInput = document.getElementById("logo-file-input");
  const logoPositionSelect = document.getElementById("logo-position");
  const logoPreviewBox = document.getElementById("logo-preview-box");
  const logoPreviewImg = document.getElementById("logo-preview-img");
  const btnRemoveLogo = document.getElementById("btn-remove-logo");
  const logoLoadedBadge = document.getElementById("logo-loaded-badge");

  const btnAnalyze = document.getElementById("btn-analyze");
  const btnAutoCreate = document.getElementById("btn-auto-create");
  const btnRefreshClips = document.getElementById("btn-refresh-clips");

  const progressCard = document.getElementById("progress-card");
  const progressStep = document.getElementById("progress-step");
  const progressPct = document.getElementById("progress-pct");
  const progressBarFill = document.getElementById("progress-bar-fill");

  const videoInfoBanner = document.getElementById("video-info-banner");
  const videoThumb = document.getElementById("video-thumb");
  const videoTitle = document.getElementById("video-title");
  const videoChannel = document.getElementById("video-channel");

  const momentsSection = document.getElementById("moments-section");
  const momentsGrid = document.getElementById("moments-grid");

  const clipsGrid = document.getElementById("clips-grid");
  const clipsEmptyState = document.getElementById("clips-empty-state");

  // Queue Elements
  const queueCount = document.getElementById("queue-count");
  const queueTableBody = document.getElementById("queue-table-body");
  const btnRefreshQueue = document.getElementById("btn-refresh-queue");

  // Schedule Modal Elements
  const scheduleModal = document.getElementById("schedule-modal");
  const btnCloseSchedule = document.getElementById("btn-close-schedule");
  const btnCancelSchedule = document.getElementById("btn-cancel-schedule");
  const btnConfirmSchedule = document.getElementById("btn-confirm-schedule");
  const schedClipId = document.getElementById("sched-clip-id");
  const schedTitle = document.getElementById("sched-title");
  const schedTags = document.getElementById("sched-tags");
  const schedDesc = document.getElementById("sched-desc");
  const schedDatetime = document.getElementById("sched-datetime");
  const titleVariantsBox = document.getElementById("title-variants-box");
  const platYoutube = document.getElementById("plat-youtube");
  const platInstagram = document.getElementById("plat-instagram");
  const platTiktok = document.getElementById("plat-tiktok");

  // Settings Modal Elements
  const settingsModal = document.getElementById("settings-modal");
  const btnOpenSettings = document.getElementById("btn-open-settings");
  const btnCloseSettings = document.getElementById("btn-close-settings");
  const btnCancelSettings = document.getElementById("btn-cancel-settings");
  const btnSaveSettings = document.getElementById("btn-save-settings");
  const inputGeminiKey = document.getElementById("input-gemini-key");
  const inputGroqKey = document.getElementById("input-groq-key");
  const inputOpenaiKey = document.getElementById("input-openai-key");

  let activeLogoPath = null;
  let currentAnalysisData = null;

  // Load API keys from localStorage
  inputGeminiKey.value = localStorage.getItem("gemini_api_key") || "";
  inputGroqKey.value = localStorage.getItem("groq_api_key") || "";
  inputOpenaiKey.value = localStorage.getItem("openai_api_key") || "";

  // 1. Check System Status
  async function checkSystem() {
    try {
      const res = await fetch("/api/system");
      const data = await res.json();
      const statusText = document.getElementById("system-status-text");
      const diagFfmpeg = document.getElementById("diag-ffmpeg");

      const diagFirebase = document.getElementById("diag-firebase");
      const firebaseBadge = document.getElementById("firebase-badge");
      const firebaseFileStatus = document.getElementById("firebase-file-status");

      if (data.firebase_active) {
        if (diagFirebase) {
          diagFirebase.textContent = "Connected ✓ (Cloud Firestore)";
          diagFirebase.style.color = "#10b981";
        }
        if (firebaseBadge) {
          firebaseBadge.textContent = "Connected ✓";
          firebaseBadge.style.color = "#10b981";
        }
        if (firebaseFileStatus) {
          firebaseFileStatus.textContent = "serviceAccountKey.json active ✓";
          firebaseFileStatus.style.color = "#10b981";
        }
      } else {
        if (diagFirebase) {
          diagFirebase.textContent = "Local Storage (Upload key below)";
          diagFirebase.style.color = "#f59e0b";
        }
      }

      if (data.ffmpeg_ready) {
        statusText.textContent = "FFmpeg Ready";
        diagFfmpeg.textContent = "Installed & Active";
        diagFfmpeg.style.color = "#10b981";
      } else {
        statusText.textContent = "FFmpeg Missing (Auto-Installs)";
        diagFfmpeg.textContent = "Will Auto-Download on 1st Cut";
        diagFfmpeg.style.color = "#f59e0b";
      }
    } catch (e) {
      console.error("System check error", e);
    }
  }

  // Firebase Key Upload
  const btnUploadFirebaseKey = document.getElementById("btn-upload-firebase-key");
  const firebaseKeyFile = document.getElementById("firebase-key-file");
  const firebaseFileStatus = document.getElementById("firebase-file-status");

  if (btnUploadFirebaseKey && firebaseKeyFile) {
    btnUploadFirebaseKey.addEventListener("click", () => firebaseKeyFile.click());
    firebaseKeyFile.addEventListener("change", async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      const fd = new FormData();
      fd.append("file", file);
      try {
        btnUploadFirebaseKey.textContent = "Connecting...";
        const res = await fetch("/api/upload-firebase-credentials", { method: "POST", body: fd });
        const data = await res.json();
        btnUploadFirebaseKey.textContent = "📁 Upload serviceAccountKey.json";
        if (data.firebase_connected) {
          firebaseFileStatus.textContent = "serviceAccountKey.json connected ✓";
          firebaseFileStatus.style.color = "#10b981";
          alert("🔥 Firebase Cloud Firestore connected successfully!");
          checkSystem();
        } else {
          alert("Key uploaded, but could not connect to Firebase. Check project permissions.");
        }
      } catch (err) {
        btnUploadFirebaseKey.textContent = "📁 Upload serviceAccountKey.json";
        alert("Upload error: " + err.message);
      }
    });
  }

  // 2. Logo Upload Handling
  btnUploadLogo.addEventListener("click", () => logoFileInput.click());
  logoFileInput.addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      btnUploadLogo.textContent = "Uploading...";
      const res = await fetch("/api/upload-logo", {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      btnUploadLogo.textContent = "📁 Change Logo";

      if (res.ok) {
        activeLogoPath = data.path;
        logoPreviewImg.src = data.url;
        logoPreviewBox.classList.remove("hidden");
        logoLoadedBadge.classList.remove("hidden");
      } else {
        alert("Logo upload failed: " + (data.detail || "Error"));
      }
    } catch (err) {
      btnUploadLogo.textContent = "📁 Upload Logo";
      alert("Error uploading logo: " + err.message);
    }
  });

  btnRemoveLogo.addEventListener("click", () => {
    activeLogoPath = null;
    logoPreviewImg.src = "";
    logoPreviewBox.classList.add("hidden");
    logoLoadedBadge.classList.add("hidden");
    logoFileInput.value = "";
    btnUploadLogo.textContent = "📁 Upload Logo";
  });

  // 3. Paste Button & Samples
  btnPaste.addEventListener("click", async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) urlInput.value = text.trim();
    } catch (err) {
      alert("Please allow clipboard permission or paste manually.");
    }
  });

  document.querySelectorAll(".sample-tag").forEach(tag => {
    tag.addEventListener("click", () => {
      urlInput.value = tag.getAttribute("data-url");
    });
  });

  // 4. Settings Modal & Tabs
  document.querySelectorAll(".modal-tab").forEach(tab => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".modal-tab").forEach(t => t.classList.remove("active"));
      document.querySelectorAll(".tab-pane").forEach(p => p.classList.add("hidden"));
      tab.classList.add("active");
      const targetId = tab.getAttribute("data-tab");
      const targetPane = document.getElementById(targetId);
      if (targetPane) targetPane.classList.remove("hidden");
    });
  });

  // Social Config elements
  const btnUploadYtSecrets = document.getElementById("btn-upload-yt-secrets");
  const ytSecretsFile = document.getElementById("yt-secrets-file");
  const ytFileStatus = document.getElementById("yt-file-status");
  const inputIgUserId = document.getElementById("input-ig-user-id");
  const inputIgToken = document.getElementById("input-ig-token");
  const inputFbPageId = document.getElementById("input-fb-page-id");
  const inputFbToken = document.getElementById("input-fb-token");
  const inputTtToken = document.getElementById("input-tt-token");
  const inputWebhookUrl = document.getElementById("input-webhook-url");

  async function loadSocialSettings() {
    try {
      const res = await fetch("/api/social-config");
      const cfg = await res.json();
      if (inputIgUserId) inputIgUserId.value = cfg.instagram?.ig_user_id || "";
      if (inputIgToken) inputIgToken.value = cfg.instagram?.access_token || "";
      if (inputFbPageId) inputFbPageId.value = cfg.facebook?.page_id || "";
      if (inputFbToken) inputFbToken.value = cfg.facebook?.page_access_token || "";
      if (inputTtToken) inputTtToken.value = cfg.tiktok?.access_token || "";
      if (inputWebhookUrl) inputWebhookUrl.value = cfg.webhook?.url || "";
      if (cfg.youtube?.enabled && ytFileStatus) {
        ytFileStatus.textContent = "client_secrets.json connected ✓";
        ytFileStatus.style.color = "#10b981";
      }
    } catch(e) {
      console.error("Failed to load social config", e);
    }
  }

  if (btnUploadYtSecrets) {
    btnUploadYtSecrets.addEventListener("click", () => ytSecretsFile.click());
    ytSecretsFile.addEventListener("change", async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      const fd = new FormData();
      fd.append("file", file);
      try {
        btnUploadYtSecrets.textContent = "Uploading...";
        const res = await fetch("/api/upload-youtube-secrets", { method: "POST", body: fd });
        btnUploadYtSecrets.textContent = "📁 Upload client_secrets.json";
        if (res.ok) {
          ytFileStatus.textContent = "client_secrets.json connected ✓";
          ytFileStatus.style.color = "#10b981";
          alert("YouTube client_secrets.json uploaded successfully!");
        } else {
          alert("Upload failed.");
        }
      } catch (err) {
        btnUploadYtSecrets.textContent = "📁 Upload client_secrets.json";
        alert("Upload error: " + err.message);
      }
    });
  }

  btnOpenSettings.addEventListener("click", () => {
    loadSocialSettings();
    settingsModal.classList.remove("hidden");
  });
  btnCloseSettings.addEventListener("click", () => settingsModal.classList.add("hidden"));
  btnCancelSettings.addEventListener("click", () => settingsModal.classList.add("hidden"));

  btnSaveSettings.addEventListener("click", async () => {
    // Save AI Keys
    localStorage.setItem("gemini_api_key", inputGeminiKey.value.trim());
    localStorage.setItem("groq_api_key", inputGroqKey.value.trim());
    localStorage.setItem("openai_api_key", inputOpenaiKey.value.trim());

    // Save Social Config
    const socialPayload = {
      youtube: { client_secrets: "client_secrets.json", enabled: true },
      instagram: {
        ig_user_id: inputIgUserId ? inputIgUserId.value.trim() : "",
        access_token: inputIgToken ? inputIgToken.value.trim() : "",
        enabled: Boolean(inputIgToken && inputIgToken.value)
      },
      facebook: {
        page_id: inputFbPageId ? inputFbPageId.value.trim() : "",
        page_access_token: inputFbToken ? inputFbToken.value.trim() : "",
        enabled: Boolean(inputFbToken && inputFbToken.value)
      },
      tiktok: {
        access_token: inputTtToken ? inputTtToken.value.trim() : "",
        enabled: Boolean(inputTtToken && inputTtToken.value)
      },
      webhook: {
        url: inputWebhookUrl ? inputWebhookUrl.value.trim() : "",
        enabled: Boolean(inputWebhookUrl && inputWebhookUrl.value)
      }
    };

    try {
      await fetch("/api/social-config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(socialPayload)
      });
    } catch (e) {
      console.error("Error saving social config", e);
    }

    settingsModal.classList.add("hidden");
    alert("All settings & connected accounts saved successfully!");
  });

  function getActiveApiKey(provider) {
    if (provider === "gemini") return localStorage.getItem("gemini_api_key") || "";
    if (provider === "groq") return localStorage.getItem("groq_api_key") || "";
    if (provider === "openai") return localStorage.getItem("openai_api_key") || "";
    return "";
  }

  function getDurationRange() {
    const val = durationSelect.value;
    if (val === "20-45") return [20, 45];
    if (val === "50-90") return [50, 90];
    return [30, 60];
  }

  function updateProgress(step, pct) {
    progressCard.classList.remove("hidden");
    progressStep.textContent = step;
    progressPct.textContent = `${pct}%`;
    progressBarFill.style.width = `${pct}%`;
  }

  function hideProgress() {
    progressCard.classList.add("hidden");
  }

  // 5. Analyze Viral Moments & SEO First
  btnAnalyze.addEventListener("click", async () => {
    const url = urlInput.value.trim();
    if (!url) {
      alert("Please enter a YouTube video URL first!");
      return;
    }

    const [minDur, maxDur] = getDurationRange();
    const provider = aiProviderSelect.value;
    const key = getActiveApiKey(provider);

    updateProgress("Extracting video transcript, analyzing viral hooks & SEO tags...", 35);
    btnAnalyze.disabled = true;

    try {
      const res = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url,
          min_duration: minDur,
          max_duration: maxDur,
          max_clips: 6,
          ai_provider: provider,
          api_key: key
        })
      });

      const data = await res.json();
      btnAnalyze.disabled = false;
      hideProgress();

      if (!res.ok) {
        alert("Analysis failed: " + (data.detail || "Unknown error"));
        return;
      }

      currentAnalysisData = data;
      renderAnalysisResults(data);
    } catch (e) {
      btnAnalyze.disabled = false;
      hideProgress();
      alert("Request error: " + e.message);
    }
  });

  function renderAnalysisResults(data) {
    if (data.video) {
      videoThumb.src = data.video.thumbnail || "https://placehold.co/140x80/151822/f59e0b?text=Video";
      videoTitle.textContent = data.video.title;
      videoChannel.textContent = data.video.uploader;
      videoInfoBanner.classList.remove("hidden");
    }

    momentsGrid.innerHTML = "";
    if (data.moments && data.moments.length > 0) {
      momentsSection.classList.remove("hidden");
      data.moments.forEach((m, idx) => {
        const seo = m.seo || {};
        const card = document.createElement("div");
        card.className = "moment-card";
        card.innerHTML = `
          <div class="moment-card-header">
            <span class="viral-badge">🔥 ${m.viral_score}/100 Score</span>
            <span class="timestamp-pill">⏱️ ${m.duration}s</span>
          </div>
          <h4 class="moment-title">${m.title}</h4>
          <div class="moment-hook">"${m.hook_text}"</div>
          <p class="moment-reason">${m.reason}</p>
          <div style="font-size:12px; color:var(--accent-cyan); background:#11141c; padding:6px 10px; border-radius:6px;">
            🏷️ <strong>Tags:</strong> ${seo.tags_comma_separated ? seo.tags_comma_separated.slice(0, 50) + '...' : '#shorts #viral'}
          </div>
          <button class="btn btn-primary btn-sm btn-render-single" data-idx="${idx}">
            ✂️ Render 9:16 Short (Shield + Logo)
          </button>
        `;
        momentsGrid.appendChild(card);
      });

      document.querySelectorAll(".btn-render-single").forEach(btn => {
        btn.addEventListener("click", async () => {
          const idx = parseInt(btn.getAttribute("data-idx"));
          const moment = data.moments[idx];
          await renderSingleMoment(moment, btn);
        });
      });
    } else {
      alert("No viral clips found for this video length.");
    }
  }

  // 6. Render Single Short
  async function renderSingleMoment(moment, btnElement) {
    const url = urlInput.value.trim();
    const reframeMode = reframeSelect.value;
    const captionStyle = captionSelect.value;
    const antiCopyright = toggleAntiCopyright.checked;
    const logoPos = logoPositionSelect.value;

    if (btnElement) {
      btnElement.disabled = true;
      btnElement.textContent = "Rendering...";
    }
    updateProgress(`Rendering "${moment.title}" with Anti-Copyright Shield...`, 65);

    try {
      const res = await fetch("/api/render-clip", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url,
          clip: moment,
          reframe_mode: reframeMode,
          caption_style: captionStyle,
          logo_path: activeLogoPath,
          logo_position: logoPos,
          logo_opacity: 0.85,
          anti_copyright: antiCopyright
        })
      });

      const data = await res.json();
      hideProgress();
      if (btnElement) {
        btnElement.disabled = false;
        btnElement.textContent = "✅ Rendered!";
      }

      if (!res.ok) {
        alert("Render failed: " + (data.detail || "FFmpeg error"));
        return;
      }

      await loadClips();
      document.getElementById("clips-section").scrollIntoView({ behavior: "smooth" });
    } catch (err) {
      hideProgress();
      if (btnElement) btnElement.disabled = false;
      alert("Render failed: " + err.message);
    }
  }

  // 7. Auto-Create All Viral Shorts
  btnAutoCreate.addEventListener("click", async () => {
    const url = urlInput.value.trim();
    if (!url) {
      alert("Please enter a YouTube video URL first!");
      return;
    }

    const [minDur, maxDur] = getDurationRange();
    const reframeMode = reframeSelect.value;
    const captionStyle = captionSelect.value;
    const provider = aiProviderSelect.value;
    const key = getActiveApiKey(provider);
    const antiCopyright = toggleAntiCopyright.checked;
    const logoPos = logoPositionSelect.value;

    btnAutoCreate.disabled = true;
    updateProgress("Starting Automated Pipeline with Protection Shield...", 5);

    try {
      const res = await fetch("/api/create-all", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url,
          min_duration: minDur,
          max_duration: maxDur,
          max_clips: 4,
          reframe_mode: reframeMode,
          caption_style: captionStyle,
          ai_provider: provider,
          api_key: key,
          logo_path: activeLogoPath,
          logo_position: logoPos,
          logo_opacity: 0.85,
          anti_copyright: antiCopyright
        })
      });

      const { job_id } = await res.json();
      pollJob(job_id);
    } catch (e) {
      btnAutoCreate.disabled = false;
      hideProgress();
      alert("Failed to start job: " + e.message);
    }
  });

  async function pollJob(jobId) {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/api/jobs/${jobId}`);
        const job = await res.json();

        updateProgress(job.step, job.progress);

        if (job.status === "completed") {
          clearInterval(interval);
          btnAutoCreate.disabled = false;
          hideProgress();
          await loadClips();
          document.getElementById("clips-section").scrollIntoView({ behavior: "smooth" });
        } else if (job.status === "failed") {
          clearInterval(interval);
          btnAutoCreate.disabled = false;
          hideProgress();
          alert("Job failed: " + job.error);
        }
      } catch (err) {
        console.error("Polling error", err);
      }
    }, 2000);
  }

  // 8. Load & Render Generated Shorts Gallery
  async function loadClips() {
    try {
      const res = await fetch("/api/clips");
      const clips = await res.json();

      if (!clips || clips.length === 0) {
        clipsEmptyState.style.display = "block";
        return;
      }

      clipsEmptyState.style.display = "none";
      const existingCards = clipsGrid.querySelectorAll(".clip-card");
      existingCards.forEach(c => c.remove());

      clips.forEach(clip => {
        const card = document.createElement("div");
        card.className = "clip-card";
        const seo = clip.seo || {};

        card.innerHTML = `
          <div class="video-container">
            <video controls preload="metadata" playsinline>
              <source src="${clip.file_url}" type="video/mp4">
              Your browser does not support video playback.
            </video>
          </div>
          <div class="clip-details">
            <div class="moment-card-header">
              <span class="viral-badge">🔥 ${clip.viral_score}/100</span>
              <span class="timestamp-pill">⏱️ ${clip.duration}s</span>
            </div>
            <h4 class="clip-title">${clip.title}</h4>
            <div style="font-size:12px; color:var(--text-muted);">
              🛡️ Anti-Copyright: <strong>${clip.anti_copyright ? 'Protected ✓' : 'Standard'}</strong>
            </div>
            <div class="clip-actions">
              <a href="${clip.file_url}" download="${clip.filename}" class="btn btn-primary btn-sm" style="flex:1;">
                ⬇️ Download
              </a>
              <button class="btn btn-schedule btn-sm btn-open-schedule-modal" data-clip="${encodeURIComponent(JSON.stringify(clip))}">
                📅 Schedule Post
              </button>
              <button class="btn btn-secondary btn-sm btn-copy-meta" data-caption="${encodeURIComponent(seo.tags_comma_separated || clip.suggested_caption || clip.title)}">
                📋 Tags
              </button>
            </div>
          </div>
        `;
        clipsGrid.appendChild(card);
      });

      // Bind schedule buttons
      document.querySelectorAll(".btn-open-schedule-modal").forEach(btn => {
        btn.addEventListener("click", () => {
          const clipData = JSON.parse(decodeURIComponent(btn.getAttribute("data-clip")));
          openScheduleModal(clipData);
        });
      });

      // Bind copy tags
      document.querySelectorAll(".btn-copy-meta").forEach(btn => {
        btn.addEventListener("click", () => {
          const text = decodeURIComponent(btn.getAttribute("data-caption"));
          navigator.clipboard.writeText(text);
          btn.textContent = "Copied! ✨";
          setTimeout(() => { btn.textContent = "📋 Tags"; }, 2000);
        });
      });
    } catch (e) {
      console.error("Error loading clips", e);
    }
  }

  // 9. Open Schedule Modal with Clickbait Hooks & SEO Tags
  function openScheduleModal(clip) {
    const seo = clip.seo || {};
    schedClipId.value = clip.id;
    schedTitle.value = clip.title;
    schedTags.value = seo.tags_comma_separated || "shorts, viral, trending, fyp";
    schedDesc.value = seo.youtube_description || clip.suggested_caption || clip.title;

    // Set default schedule time to tomorrow 6:00 PM local
    const now = new Date();
    now.setHours(now.getHours() + 2);
    schedDatetime.value = now.toISOString().slice(0, 16);

    // Populate Clickbait Title Variants
    titleVariantsBox.innerHTML = "<span style='font-size:11px; color:var(--text-muted);'>Click to select high-CTR title variant:</span>";
    const variants = seo.title_variants || [clip.title];
    variants.forEach(v => {
      const pill = document.createElement("div");
      pill.className = "title-variant-pill";
      pill.textContent = "💡 " + v;
      pill.addEventListener("click", () => {
        schedTitle.value = v;
      });
      titleVariantsBox.appendChild(pill);
    });

    scheduleModal.classList.remove("hidden");
  }

  btnCloseSchedule.addEventListener("click", () => scheduleModal.classList.add("hidden"));
  btnCancelSchedule.addEventListener("click", () => scheduleModal.classList.add("hidden"));

  btnConfirmSchedule.addEventListener("click", async () => {
    const clipId = schedClipId.value;
    const title = schedTitle.value.trim();
    const tags = schedTags.value.trim();
    const description = schedDesc.value.trim();
    const scheduledTime = schedDatetime.value;

    const platFacebook = document.getElementById("plat-facebook");

    const platforms = [];
    if (platYoutube.checked) platforms.push("youtube");
    if (platInstagram.checked) platforms.push("instagram");
    if (platFacebook && platFacebook.checked) platforms.push("facebook");
    if (platTiktok.checked) platforms.push("tiktok");

    if (platforms.length === 0) {
      alert("Please select at least one platform (YouTube, Instagram, or TikTok)!");
      return;
    }

    try {
      btnConfirmSchedule.disabled = true;
      btnConfirmSchedule.textContent = "Adding to Queue...";

      const res = await fetch("/api/schedule", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          clip_id: clipId,
          title,
          tags,
          description,
          platforms,
          scheduled_time: scheduledTime || new Date().toISOString()
        })
      });

      const data = await res.json();
      btnConfirmSchedule.disabled = false;
      btnConfirmSchedule.textContent = "🚀 Confirm & Add to Queue";

      if (res.ok) {
        scheduleModal.classList.add("hidden");
        alert("🎉 Short successfully queued for automated publishing!");
        await loadScheduledQueue();
        document.getElementById("scheduled-section").scrollIntoView({ behavior: "smooth" });
      } else {
        alert("Scheduling failed: " + (data.detail || "Error"));
      }
    } catch (err) {
      btnConfirmSchedule.disabled = false;
      btnConfirmSchedule.textContent = "🚀 Confirm & Add to Queue";
      alert("Error: " + err.message);
    }
  });

  // 10. Load Scheduled Queue Table
  async function loadScheduledQueue() {
    try {
      const res = await fetch("/api/scheduled-posts");
      const posts = await res.json();

      queueCount.textContent = posts.length;

      if (!posts || posts.length === 0) {
        queueTableBody.innerHTML = `
          <tr>
            <td colspan="5" class="empty-queue-msg">No posts in the schedule queue yet. Click "📅 Schedule Post" on any generated short above!</td>
          </tr>
        `;
        return;
      }

      queueTableBody.innerHTML = "";
      posts.forEach(p => {
        const tr = document.createElement("tr");
        const plats = p.platforms.map(pl => {
          if (pl === "youtube") return "🔴 YouTube";
          if (pl === "instagram") return "📸 Instagram";
          if (pl === "facebook") return "📘 Facebook";
          if (pl === "tiktok") return "🎵 TikTok";
          return pl;
        }).join(", ");

        const statusClass = p.status === "published" ? "status-badge-published" : "status-badge-pending";

        tr.innerHTML = `
          <td><strong>${p.title}</strong></td>
          <td>${plats}</td>
          <td>${p.scheduled_time.replace("T", " ")}</td>
          <td><span class="${statusClass}">${p.status.toUpperCase()}</span></td>
          <td>
            <button class="btn btn-secondary btn-sm btn-delete-post" data-id="${p.id}">
              🗑️ Cancel
            </button>
          </td>
        `;
        queueTableBody.appendChild(tr);
      });

      document.querySelectorAll(".btn-delete-post").forEach(btn => {
        btn.addEventListener("click", async () => {
          const id = btn.getAttribute("data-id");
          if (confirm("Cancel this scheduled post?")) {
            await fetch(`/api/delete-scheduled/${id}`, { method: "DELETE" });
            await loadScheduledQueue();
          }
        });
      });
    } catch (e) {
      console.error("Error loading queue", e);
    }
  }

  btnRefreshClips.addEventListener("click", loadClips);
  btnRefreshQueue.addEventListener("click", loadScheduledQueue);

  // Initialize
  checkSystem();
  loadClips();
  loadScheduledQueue();
});
