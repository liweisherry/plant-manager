/* ── Gemini Key helper ──────────────────────────────────────────────────────── */
function geminiHeaders() {
  const key = localStorage.getItem("gemini_api_key") || "";
  return key ? { "X-Gemini-Key": key } : {};
}

/* ── Photo preview ─────────────────────────────────────────────────────────── */
document.querySelectorAll('input[type="file"][accept="image/*"]').forEach((input) => {
  input.addEventListener("change", () => {
    const file = input.files[0];
    if (!file) return;
    const existing = input.parentElement.querySelector(".preview-img");
    if (existing) existing.remove();
    const img = document.createElement("img");
    img.src = URL.createObjectURL(file);
    img.className = "preview-img";
    img.style.cssText =
      "max-height:160px;border-radius:6px;margin-top:0.5rem;object-fit:contain;";
    img.onload = () => URL.revokeObjectURL(img.src);
    input.parentElement.appendChild(img);
  });
});

/* ── Loading state on AI / upload forms ───────────────────────────────────── */
document.querySelectorAll("form").forEach((form) => {
  form.addEventListener("submit", () => {
    const btn = form.querySelector('button[type="submit"]');
    if (!btn) return;
    btn.disabled = true;
    btn.textContent = "处理中…";
  });
});

/* ── Plant name autocomplete + care tips ──────────────────────────────────── */
(function () {
  const nameInput    = document.getElementById("name");
  const speciesInput = document.getElementById("species");
  const datalist     = document.getElementById("name-datalist");
  const nameHint     = document.getElementById("name-hint");
  const tipsSection  = document.getElementById("care-tips-section");
  const tipsContent  = document.getElementById("care-tips-content");
  const tipsLabel    = document.getElementById("care-tips-plant-name");

  if (!nameInput || !datalist) return;

  // zh → {en, latin} 映射，用于选中后填入学名
  const suggestMap = {};
  let suggestTimer = null;
  let lastTipsName = "";

  // ── 联想：输入时查词库 ──────────────────────────────────────────────────────
  nameInput.addEventListener("input", () => {
    clearTimeout(suggestTimer);
    const q = nameInput.value.trim();
    if (q.length < 1) { datalist.innerHTML = ""; return; }

    suggestTimer = setTimeout(async () => {
      try {
        const res  = await fetch("/api/suggest?q=" + encodeURIComponent(q));
        const data = await res.json();
        datalist.innerHTML = "";
        data.forEach((item) => {
          const opt = document.createElement("option");
          opt.value = item.zh;
          // label 显示在下拉里（英文 + 学名）
          opt.label = item.en + (item.latin ? "  ·  " + item.latin : "");
          datalist.appendChild(opt);
          suggestMap[item.zh] = item;
        });
      } catch (e) {
        console.warn("suggest error:", e);
      }
    }, 250);
  });

  // ── 选中：自动填入学名并显示提示 ──────────────────────────────────────────
  nameInput.addEventListener("change", () => {
    const val  = nameInput.value.trim();
    const item = suggestMap[val];
    if (item) {
      if (speciesInput && !speciesInput.value) {
        speciesInput.value = item.latin || item.en || "";
      }
      if (nameHint) {
        nameHint.textContent =
          item.en + (item.latin ? "  |  " + item.latin : "");
      }
      fetchCareTips(val, item.latin || "");
    }
  });

  // ── 养护建议（Gemini，有配额时才有效）──────────────────────────────────────
  async function fetchCareTips(name, species) {
    if (!tipsSection || !tipsContent || !tipsLabel) return;
    if (!name || name === lastTipsName) return;
    lastTipsName = name;

    tipsSection.hidden = false;
    tipsLabel.textContent = name;
    tipsContent.innerHTML = '<p class="tips-loading">加载中…</p>';

    try {
      const url =
        "/api/care-tips?name=" + encodeURIComponent(name) +
        "&species=" + encodeURIComponent(species);
      const res  = await fetch(url, { headers: geminiHeaders() });
      const data = await res.json();
      if (data.error) {
        tipsContent.innerHTML = '<p class="tips-error">AI 服务暂不可用</p>';
        return;
      }
      renderTips(data);
    } catch (_) {
      tipsContent.innerHTML = '<p class="tips-error">获取失败，请稍后再试</p>';
    }
  }

  const TIPS_LABELS = {
    water:         { icon: "💧", label: "浇水" },
    light:         { icon: "☀️",  label: "光照" },
    temperature:   { icon: "🌡️",  label: "温度" },
    humidity:      { icon: "💦",  label: "湿度" },
    fertilize:     { icon: "🌿",  label: "施肥" },
    common_issues: { icon: "⚠️",  label: "常见问题" },
  };

  function renderTips(data) {
    tipsContent.innerHTML = "";
    Object.entries(TIPS_LABELS).forEach(([key, { icon, label }]) => {
      if (!data[key]) return;
      const card = document.createElement("div");
      card.className = "tips-card";
      card.innerHTML =
        '<div class="tips-card__header">' + icon + " " + label + "</div>" +
        '<div class="tips-card__body">' + data[key] + "</div>";
      tipsContent.appendChild(card);
    });
  }
})();
