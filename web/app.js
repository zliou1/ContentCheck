const historyKey = "content-risk-gateway-history-v1";
const textTab = document.querySelector("#text-tab");
const imageTab = document.querySelector("#image-tab");
const textArea = document.querySelector("#text-input-area");
const imageArea = document.querySelector("#image-input-area");
const form = document.querySelector("#scan-form");
const fileInput = document.querySelector("#image");
const textInput = document.querySelector("#text");
let mode = "text";
let selectedFile = null;

function safeHistory() { try { return JSON.parse(localStorage.getItem(historyKey)) || []; } catch { return []; } }
function setMode(nextMode) {
  mode = nextMode; const textMode = mode === "text";
  textTab.classList.toggle("active", textMode); imageTab.classList.toggle("active", !textMode);
  textTab.setAttribute("aria-selected", textMode); imageTab.setAttribute("aria-selected", !textMode);
  textArea.hidden = !textMode; imageArea.hidden = textMode;
  textInput.required = textMode; document.querySelector("#scan-button").textContent = textMode ? "Run text scan" : "Run image scan";
}
function decisionClass(decision) { return ["allow", "review", "block"].includes(decision) ? decision : "review"; }
function renderResult(result) {
  document.querySelector("#empty-result").hidden = true; document.querySelector("#result").hidden = false; document.querySelector("#error").hidden = true;
  const decision = decisionClass(result.decision); const badge = document.querySelector("#decision-badge"); badge.textContent = result.decision; badge.className = `decision-badge ${decision}`;
  document.querySelector("#risk-score").textContent = result.risk_score; const meter = document.querySelector("#meter-fill"); meter.style.width = `${result.risk_score}%`; meter.style.background = decision === "block" ? "var(--red)" : decision === "review" ? "var(--amber)" : "var(--green)";
  const categories = document.querySelector("#categories"); categories.innerHTML = ""; (result.categories.length ? result.categories : ["No categories triggered"]).forEach(category => { const chip = document.createElement("span"); chip.className = "chip"; chip.textContent = category.replaceAll("_", " "); categories.append(chip); });
  const reasons = document.querySelector("#reasons"); reasons.innerHTML = ""; result.reasons.forEach(reason => { const item = document.createElement("li"); item.textContent = reason; reasons.append(item); });
  document.querySelector("#result-policy").textContent = `${result.policy.id} · v${result.policy.version}`; document.querySelector("#trace-id").textContent = result.trace_id;
}
function saveResult(type, result) {
  const entry = { id: crypto.randomUUID(), type, at: new Date().toISOString(), result: { decision: result.decision, risk_score: result.risk_score, categories: result.categories, reasons: result.reasons, policy: result.policy, trace_id: result.trace_id } };
  localStorage.setItem(historyKey, JSON.stringify([entry, ...safeHistory()].slice(0, 50))); renderHistory();
}
function renderHistory() {
  const container = document.querySelector("#history"); const entries = safeHistory(); container.innerHTML = "";
  if (!entries.length) { container.innerHTML = '<p class="empty-history">No scans yet.</p>'; return; }
  entries.forEach(entry => { const row = document.createElement("div"); row.className = "history-row"; row.tabIndex = 0; const d = new Date(entry.at);
    row.innerHTML = `<span class="history-type">${entry.type === "image" ? "Image scan" : "Text scan"}</span><span class="history-meta">${d.toLocaleString()} · ${entry.result.policy.id}</span><span class="history-score">${entry.result.risk_score}/100</span><span class="mini-badge ${decisionClass(entry.result.decision)}">${entry.result.decision}</span>`;
    const show = () => renderResult(entry.result); row.addEventListener("click", show); row.addEventListener("keydown", event => { if (event.key === "Enter") show(); }); container.append(row);
  });
}
function displayError(message) { document.querySelector("#result").hidden = true; document.querySelector("#empty-result").hidden = true; const error = document.querySelector("#error"); error.textContent = message; error.hidden = false; }
function imageToBase64(file) { return new Promise((resolve, reject) => { const reader = new FileReader(); reader.onload = () => resolve(reader.result.split(",")[1]); reader.onerror = reject; reader.readAsDataURL(file); }); }
async function gatewayHealth() { try { const response = await fetch("/health"); if (!response.ok) throw Error(); document.querySelector(".status").className = "status ok"; document.querySelector("#status-text").textContent = "Gateway online"; } catch { document.querySelector(".status").className = "status fail"; document.querySelector("#status-text").textContent = "Gateway unavailable"; } }

textTab.addEventListener("click", () => setMode("text")); imageTab.addEventListener("click", () => setMode("image"));
textInput.addEventListener("input", () => { document.querySelector("#character-count").textContent = textInput.value.length.toLocaleString(); });
fileInput.addEventListener("change", () => { const file = fileInput.files[0]; if (!file) return; if (file.size > 4 * 1024 * 1024) { displayError("Choose an image smaller than 4 MB."); fileInput.value = ""; return; } selectedFile = file; document.querySelector("#preview-image").src = URL.createObjectURL(file); document.querySelector("#image-name").textContent = file.name; document.querySelector("#image-preview").hidden = false; });
document.querySelector("#remove-image").addEventListener("click", () => { selectedFile = null; fileInput.value = ""; document.querySelector("#image-preview").hidden = true; });
document.querySelector("#clear-history").addEventListener("click", () => { if (confirm("Clear all locally stored scan results?")) { localStorage.removeItem(historyKey); renderHistory(); } });
form.addEventListener("submit", async event => { event.preventDefault(); const button = document.querySelector("#scan-button"); const policy_id = document.querySelector("#policy").value; let endpoint, payload;
  try { if (mode === "text") { endpoint = "/v1/scan/text"; payload = { text: textInput.value.trim(), policy_id }; if (!payload.text) throw Error("Enter text to scan."); } else { endpoint = "/v1/scan/image"; if (!selectedFile) throw Error("Choose an image to scan."); payload = { image_base64: await imageToBase64(selectedFile), policy_id }; }
    button.disabled = true; button.textContent = "Scanning…"; const response = await fetch(endpoint, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }); const data = await response.json(); if (!response.ok) throw Error(data.detail || "The gateway could not complete this scan."); renderResult(data); saveResult(mode, data);
  } catch (error) { displayError(error.message || "Unable to run the scan."); } finally { button.disabled = false; button.textContent = mode === "text" ? "Run text scan" : "Run image scan"; }
});

setMode("text"); renderHistory(); gatewayHealth();
