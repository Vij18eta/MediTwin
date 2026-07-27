const API_BASE = `${window.location.origin}/api`;
const pageMode = document.body.dataset.page || "overview";
const requestedPatientId = (document.body.dataset.patientId || "P5").toUpperCase();

const dom = {
  headerPatientContext: document.getElementById("headerPatientContext"),
  siteNav: document.getElementById("siteNav"),
  notificationCount: document.getElementById("notificationCount"),
  heroEyebrow: document.getElementById("heroEyebrow"),
  heroName: document.getElementById("heroName"),
  heroMeta: document.getElementById("heroMeta"),
  heroStatusPill: document.getElementById("heroStatusPill"),
  heroCondition: document.getElementById("heroCondition"),
  heroPrediction: document.getElementById("heroPrediction"),
  heroRiskLabel: document.getElementById("heroRiskLabel"),
  heroDanger: document.getElementById("heroDanger"),
  heroActionLead: document.getElementById("heroActionLead"),
  heroRiskScore: document.getElementById("heroRiskScore"),
  heroRiskPercent: document.getElementById("heroRiskPercent"),
  heartRateValue: document.getElementById("heartRateValue"),
  heartRateState: document.getElementById("heartRateState"),
  spo2Value: document.getElementById("spo2Value"),
  spo2State: document.getElementById("spo2State"),
  temperatureValue: document.getElementById("temperatureValue"),
  temperatureState: document.getElementById("temperatureState"),
  diagnosticPrediction: document.getElementById("diagnosticPrediction"),
  diagnosticRisk: document.getElementById("diagnosticRisk"),
  diagnosticRecommendation: document.getElementById("diagnosticRecommendation"),
  diagnosticWhy: document.getElementById("diagnosticWhy"),
  trendGraph: document.getElementById("trendGraph"),
  graphCaption: document.getElementById("graphCaption"),
  alertPanel: document.getElementById("alertPanel"),
  alertTime: document.getElementById("alertTime"),
  alertMessage: document.getElementById("alertMessage"),
  alertSupportText: document.getElementById("alertSupportText"),
  statusSummary: document.getElementById("statusSummary"),
  priorityMessage: document.getElementById("priorityMessage"),
  patientDirectory: document.getElementById("patientDirectory"),
  simulateButton: document.getElementById("simulateButton"),
  resetButton: document.getElementById("resetButton")
};

let displayedPatientId = requestedPatientId;

function pageLinkForPatient(id) {
  return `/patients/${id.toLowerCase()}`;
}

function formatTime(timestamp) {
  return new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    minute: "2-digit"
  }).format(new Date(timestamp));
}

function setButtonsDisabled(disabled) {
  if (dom.simulateButton) {
    dom.simulateButton.disabled = disabled;
  }
  if (dom.resetButton) {
    dom.resetButton.disabled = disabled;
  }
}

async function fetchJson(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      Accept: "application/json"
    },
    ...options
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Request failed with status ${response.status}`);
  }

  return response.json();
}

function buildNavigation(patients) {
  const links = [
    {
      label: "Overview",
      href: "/",
      active: pageMode === "overview"
    },
    ...patients.map((patient) => ({
      label: patient.id,
      href: pageLinkForPatient(patient.id),
      active: pageMode === "patient" && requestedPatientId === patient.id
    }))
  ];

  dom.siteNav.innerHTML = links
    .map((link) => `<a class="nav-link${link.active ? " active" : ""}" href="${link.href}">${link.label}</a>`)
    .join("");
}

function renderSystemSummary(summary) {
  dom.statusSummary.innerHTML = `
    <div class="summary-card">
      <strong>${summary.stable_count}</strong>
      <span>Stable</span>
    </div>
    <div class="summary-card">
      <strong>${summary.moderate_count}</strong>
      <span>Moderate</span>
    </div>
    <div class="summary-card">
      <strong>${summary.critical_count}</strong>
      <span>Critical</span>
    </div>
  `;

  dom.priorityMessage.textContent = summary.priority_message;
  dom.notificationCount.textContent = String(summary.notification_count);
}

function applyStatusTone(element, label, tone) {
  element.textContent = label;
  element.className = `status-pill status-${tone}`;
}

function renderDirectory(patients, highlightedPatientId) {
  dom.patientDirectory.innerHTML = patients
    .map((patient) => `
      <a class="patient-link${patient.id === highlightedPatientId ? " active-link" : ""}" href="${pageLinkForPatient(patient.id)}">
        <div class="patient-link-top">
          <div>
            <strong>${patient.id} ${patient.name}</strong>
            <p>${patient.current_condition}</p>
          </div>
          <span class="mini-status status-${patient.tone}">${patient.risk_label}</span>
        </div>
        <div class="patient-stats">
          <span>SpO2 ${patient.latest_vitals.spo2.toFixed(1)}%</span>
          <span>HR ${patient.latest_vitals.heart_rate.toFixed(0)} bpm</span>
          <span>Temp ${patient.latest_vitals.temperature.toFixed(1)} C</span>
        </div>
      </a>
    `)
    .join("");
}

function renderHero(patient) {
  document.title = pageMode === "overview"
    ? "MediTwin | Overview"
    : `MediTwin | ${patient.id} ${patient.name}`;

  dom.heroEyebrow.textContent = pageMode === "overview" ? "Priority Patient" : "Patient Detail";
  dom.heroName.textContent = patient.name;
  dom.heroMeta.textContent = `${patient.id} | ${patient.bed} | Age ${patient.age} | ${patient.source_label}`;
  dom.heroCondition.textContent = patient.current_condition;
  dom.heroPrediction.textContent = patient.prediction;
  dom.heroRiskLabel.textContent = patient.risk_label;
  dom.heroDanger.textContent = patient.danger_text;
  dom.heroActionLead.textContent = patient.action;
  dom.heroRiskScore.textContent = `${patient.risk_score} / 100`;
  dom.heroRiskPercent.textContent = `${patient.risk_score}%`;
  applyStatusTone(dom.heroStatusPill, patient.risk_label, patient.tone);

  dom.headerPatientContext.textContent = pageMode === "overview"
    ? `${patient.id} ${patient.name} is highlighted because this patient currently has the highest operational priority.`
    : `${patient.id} is on a dedicated page while still being monitored in parallel with the other patient twins.`;
}

function renderVitals(patient) {
  const latest = patient.latest_vitals;
  const trends = patient.trend_summary;

  dom.heartRateValue.textContent = `${latest.heart_rate.toFixed(0)} bpm`;
  dom.heartRateState.textContent = latest.heart_rate > 110 || latest.heart_rate < 56
    ? "Outside the preferred ICU band."
    : Math.abs(trends.heart_rate) > 8
      ? "Changing quickly across the current trend window."
      : "Within the expected rhythm range.";

  dom.spo2Value.textContent = `${latest.spo2.toFixed(1)}%`;
  dom.spo2State.textContent = latest.spo2 < 94
    ? "Below the preferred oxygenation threshold."
    : trends.spo2 < -1.0
      ? "Trending downward and needs watching."
      : "Oxygen saturation remains acceptable.";

  dom.temperatureValue.textContent = `${latest.temperature.toFixed(1)} C`;
  dom.temperatureState.textContent = latest.temperature >= 38
    ? "Fever signal is active."
    : trends.temperature > 0.25
      ? "Temperature is gradually rising."
      : "Thermal profile is under control.";
}

function renderDiagnostics(patient) {
  dom.diagnosticPrediction.textContent = patient.prediction;
  dom.diagnosticRisk.textContent = `${patient.risk_label} | ${patient.risk_score}/100`;
  dom.diagnosticRecommendation.textContent = patient.action;
  dom.diagnosticWhy.innerHTML = patient.reasons
    .map((reason) => `<li>${reason}</li>`)
    .join("");
}

function renderAlert(patient) {
  if (!patient.alerts.length) {
    dom.alertPanel.hidden = true;
    return;
  }

  dom.alertPanel.hidden = false;
  dom.alertTime.textContent = formatTime(patient.latest_vitals.time);
  dom.alertMessage.textContent = patient.alerts[0];
  dom.alertSupportText.textContent = patient.risk_label === "Critical"
    ? "The AI agents agree that this patient needs urgent clinical review."
    : "An active anomaly is present, so the alert section has been shown.";
}

function renderTrendGraph(patient) {
  const history = patient.history.slice(-12);
  const width = 620;
  const height = 300;
  const leftPad = 36;
  const rightPad = 20;
  const topPad = 24;
  const bottomPad = 34;
  const graphWidth = width - leftPad - rightPad;
  const graphHeight = height - topPad - bottomPad;

  const spo2Values = history.map((sample) => sample.spo2);
  const heartValues = history.map((sample) => sample.heart_rate);
  const spo2Min = Math.min(...spo2Values) - 1;
  const spo2Max = Math.max(...spo2Values) + 1;
  const heartMin = Math.min(...heartValues) - 5;
  const heartMax = Math.max(...heartValues) + 5;

  const xAt = (index) => leftPad + (index / Math.max(history.length - 1, 1)) * graphWidth;
  const ySpo2 = (value) => topPad + (1 - (value - spo2Min) / Math.max(spo2Max - spo2Min, 1)) * graphHeight;
  const yHeart = (value) => topPad + (1 - (value - heartMin) / Math.max(heartMax - heartMin, 1)) * graphHeight;

  const spo2Points = history.map((sample, index) => `${xAt(index)},${ySpo2(sample.spo2)}`).join(" ");
  const heartPoints = history.map((sample, index) => `${xAt(index)},${yHeart(sample.heart_rate)}`).join(" ");
  const fillPoints = `36,${height - bottomPad} ${spo2Points} ${width - rightPad},${height - bottomPad}`;

  const gridLines = [0, 0.25, 0.5, 0.75, 1].map((step) => {
    const y = topPad + step * graphHeight;
    return `<line class="grid-line" x1="${leftPad}" y1="${y}" x2="${width - rightPad}" y2="${y}"></line>`;
  }).join("");

  const xLabels = history.map((sample, index) => {
    if (index !== 0 && index !== history.length - 1 && index !== Math.floor(history.length / 2)) {
      return "";
    }
    return `<text class="axis-label" x="${xAt(index)}" y="${height - 10}" text-anchor="middle">${formatTime(sample.time)}</text>`;
  }).join("");

  const anomalyMarkers = history.map((sample, index) => {
    const anomaly = sample.spo2 < 94 || sample.heart_rate > 110 || sample.temperature >= 38;
    if (!anomaly) {
      return "";
    }
    const y = Math.min(ySpo2(sample.spo2), yHeart(sample.heart_rate));
    return `<circle class="anomaly-point" cx="${xAt(index)}" cy="${y}" r="6"></circle>`;
  }).join("");

  dom.trendGraph.innerHTML = `
    ${gridLines}
    <polygon class="trend-fill" points="${fillPoints}"></polygon>
    <polyline class="trend-line-spo2" points="${spo2Points}"></polyline>
    <polyline class="trend-line-hr" points="${heartPoints}"></polyline>
    ${anomalyMarkers}
    ${xLabels}
  `;

  const anomalyCount = history.filter((sample) => sample.spo2 < 94 || sample.heart_rate > 110 || sample.temperature >= 38).length;
  dom.graphCaption.textContent = `${patient.current_condition} twin: backend-driven SpO2 and heart-rate trend. ${anomalyCount ? `${anomalyCount} anomaly marker(s) highlighted.` : "No anomaly markers are active right now."}`;
}

function renderActivePatient(patient) {
  displayedPatientId = patient.id;
  renderHero(patient);
  renderVitals(patient);
  renderDiagnostics(patient);
  renderAlert(patient);
  renderTrendGraph(patient);
}

function renderOverview(payload) {
  buildNavigation(payload.patients);
  renderSystemSummary(payload.system_summary);
  renderDirectory(payload.patients, payload.priority_patient.id);
  renderActivePatient(payload.priority_patient);
}

function renderPatientView(payload) {
  buildNavigation(payload.patients);
  renderSystemSummary(payload.system_summary);
  renderDirectory(payload.patients, payload.patient.id);
  renderActivePatient(payload.patient);
}

function renderBackendUnavailable(error) {
  setButtonsDisabled(true);
  dom.headerPatientContext.textContent = "Backend unavailable. Start the FastAPI service to enable live multi-agent monitoring.";
  dom.heroName.textContent = "Backend Offline";
  dom.heroMeta.textContent = "Run the Python service on http://127.0.0.1:8000";
  dom.heroCondition.textContent = "No live patient data";
  dom.heroPrediction.textContent = `Connection error: ${error.message}`;
  dom.heroRiskLabel.textContent = "Unavailable";
  dom.heroDanger.textContent = "The frontend is waiting for the Python backend.";
  dom.heroActionLead.textContent = "Start the API server, then refresh this page.";
  dom.heroRiskScore.textContent = "--";
  dom.heroRiskPercent.textContent = "--";
  dom.diagnosticPrediction.textContent = "Waiting for backend";
  dom.diagnosticRisk.textContent = "Unavailable";
  dom.diagnosticRecommendation.textContent = "Run: python backend/run.py";
  dom.diagnosticWhy.innerHTML = "<li>The current UI now expects backend-driven agent responses.</li>";
  dom.alertPanel.hidden = true;
  dom.statusSummary.innerHTML = "";
  dom.priorityMessage.textContent = "No backend response yet.";
  dom.patientDirectory.innerHTML = "";
  dom.trendGraph.innerHTML = "";
  dom.graphCaption.textContent = "No trend data available until the backend is running.";
}

async function refreshView() {
  try {
    setButtonsDisabled(false);
    if (pageMode === "overview") {
      const payload = await fetchJson("/overview");
      renderOverview(payload);
    } else {
      const payload = await fetchJson(`/patients/${requestedPatientId}`);
      renderPatientView(payload);
    }
  } catch (error) {
    renderBackendUnavailable(error);
  }
}

async function simulateSpike() {
  try {
    setButtonsDisabled(true);
    await fetchJson(`/patients/${displayedPatientId}/simulate-spike`, { method: "POST" });
    await refreshView();
  } catch (error) {
    renderBackendUnavailable(error);
  } finally {
    setButtonsDisabled(false);
  }
}

async function resetView() {
  try {
    setButtonsDisabled(true);
    await fetchJson("/reset", { method: "POST" });
    await refreshView();
  } catch (error) {
    renderBackendUnavailable(error);
  } finally {
    setButtonsDisabled(false);
  }
}

function init() {
  if (dom.simulateButton) {
    dom.simulateButton.addEventListener("click", simulateSpike);
  }
  if (dom.resetButton) {
    dom.resetButton.addEventListener("click", resetView);
  }

  refreshView();
  window.setInterval(refreshView, 4000);
}

init();
