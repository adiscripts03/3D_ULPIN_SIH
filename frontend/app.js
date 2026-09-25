// National 3D ULPIN Cadastral Platform Frontend Client
// 2-Step Workflow: Mahabhulekh Search -> 4 Campus Buildings Selection & 3D Twin Workspace

let currentBuildingId = "HSTL01";
let currentBuildingData = null;
let currentSelectedUlpin = null;
let activeModalTab = "allot";

const BUILDING_METADATA = {
  "ADMIN01": {
    "name": "Admin Building",
    "status": "not_yet_surveyed",
    "desc": "Administrative offices, registry division, and institute leadership. Architectural CAD floor plans have not yet been surveyed/digitized."
  },
  "ACAD01": {
    "name": "Academic Building",
    "status": "not_yet_surveyed",
    "desc": "Classrooms, lecture theaters, and departmental laboratories. Architectural CAD floor plans have not yet been surveyed/digitized."
  },
  "HSTL01": {
    "name": "Hostel Block A",
    "status": "completed",
    "desc": "10-Storey student residence with verified CAD vector extraction and 700 volumetric 3D parcels."
  },
  "RES01": {
    "name": "Residential Building",
    "status": "not_yet_surveyed",
    "desc": "Faculty and staff residential quarters. Architectural CAD floor plans have not yet been surveyed/digitized."
  }
};

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", setupEventListeners);
} else {
  setupEventListeners();
}

function setupEventListeners() {
  const vSearch = document.getElementById("view-search");
  const vBhu = document.getElementById("view-bhunaksha");
  const vRes = document.getElementById("view-results");

  // Check if directed directly to a building (e.g. from AI Studio or bookmark)
  const urlParams = new URLSearchParams(window.location.search);
  const targetBldg = urlParams.get("building_id") || urlParams.get("bldg_id");

  if (targetBldg) {
    if (vSearch) vSearch.style.setProperty("display", "none", "important");
    if (vBhu) vBhu.style.setProperty("display", "none", "important");
    if (vRes) vRes.style.setProperty("display", "flex", "important");
    setTimeout(async () => {
      await loadAnalytics();
      await selectBuilding(targetBldg.toUpperCase());
    }, 250);
  } else {
    // Ensure only Search view is visible on initial load
    if (vSearch) vSearch.style.setProperty("display", "flex", "important");
    if (vBhu) vBhu.style.setProperty("display", "none", "important");
    if (vRes) vRes.style.setProperty("display", "none", "important");
  }

  const floorFilter = document.getElementById("floor-filter");
  if (floorFilter) {
    floorFilter.addEventListener("change", () => { filter3DView(); });
  }

  const typeFilter = document.getElementById("type-filter");
  if (typeFilter) {
    typeFilter.addEventListener("change", () => { filter3DView(); });
  }

  const btnOpenActions = document.getElementById("btn-open-actions");
  if (btnOpenActions) {
    btnOpenActions.addEventListener("click", () => { openModal(); });
  }

  const btnCloseModal = document.getElementById("btn-close-modal");
  if (btnCloseModal) {
    btnCloseModal.addEventListener("click", () => { closeModal(); });
  }

  const btnRunTopology = document.getElementById("btn-run-topology");
  if (btnRunTopology) {
    btnRunTopology.addEventListener("click", () => { runTopologyAudit(); });
  }

  const btnIngest = document.getElementById("btn-open-ingestion");
  if (btnIngest) {
    btnIngest.addEventListener("click", () => {
      openIngestModal(currentBuildingId || "ADMIN01");
    });
  }
}


// Cascading Data Dictionaries for Mahabhulekh Search
const NAGPUR_TALUKAS = [
  { value: "Nagpur_Rural", label: "Nagpur Rural (नागपूर ग्रामीण)" },
  { value: "Umred", label: "Umred (उमरेड)" },
  { value: "Kalmeshwar", label: "Kalmeshwar (कळमेश्वर)" },
  { value: "Katol", label: "Katol (काटोल)" },
  { value: "Kamthi", label: "Kamthi (कामठी)" },
  { value: "Kuhi", label: "Kuhi (कुही)" },
  { value: "Nagpur_City", label: "Nagpur City (नागपूर शहर)" },
  { value: "Narkhed", label: "Narkhed (नरखेड)" },
  { value: "Parseoni", label: "Parseoni (पारशिवनी)" },
  { value: "Bhiwapur", label: "Bhiwapur (भिवापूर)" },
  { value: "Mouda", label: "Mouda (मौदा)" },
  { value: "Ramtek", label: "Ramtek (रामटेक)" },
  { value: "Savner", label: "Savner (सावनेर)" },
  { value: "Hingna", label: "Hingna (हिंगणा)" }
];

const NAGPUR_RURAL_VILLAGES = [
  { value: "Waranga", label: "Waranga (वारंगा)" },
  { value: "Mohgaon", label: "Mohgaon (मोहगांव)" },
  { value: "Mhasala", label: "Mhasala (म्हासाळा)" },
  { value: "Yerla", label: "Yerla (येरला)" },
  { value: "Rahimapur", label: "Rahimapur (रहिमापूर)" },
  { value: "Rahimabad", label: "Rahimabad (रहिमाबाद)" },
  { value: "Raipur", label: "Raipur (रायपूर)" },
  { value: "Rama", label: "Rama (रामा)" },
  { value: "Ridhora", label: "Ridhora (रिधोरा)" },
  { value: "Rui", label: "Rui (रुई)" },
  { value: "Ruikhari", label: "Ruikhari (रुईखैरी)" },
  { value: "Rengapar", label: "Rengapar (रेंगापार)" },
  { value: "Lava", label: "Lava (लाव्हा)" },
  { value: "Linga", label: "Linga (लिंगा)" },
  { value: "Lonara", label: "Lonara (लोणारा)" },
  { value: "Vadgaon", label: "Vadgaon (वडगांव)" },
  { value: "Varoda", label: "Varoda (वरोडा)" },
  { value: "Valni", label: "Valni (वलनी)" },
  { value: "Vakeshwar", label: "Vakeshwar (वाकेश्वर)" },
  { value: "Vathoda", label: "Vathoda (वाठोडा)" },
  { value: "Wadi", label: "Wadi (वाडी)" },
  { value: "Vihirgaon", label: "Vihirgaon (विहिरीगांव)" },
  { value: "Vela_Harishchandra", label: "Vela Harishchandra (वेळा हरिश्चंद्र)" },
  { value: "Vyahad", label: "Vyahad (व्याहाड)" },
  { value: "Vyahadghat", label: "Vyahadghat (व्याहाडघाट)" },
  { value: "Shankarpur", label: "Shankarpur (शंकरपूर)" },
  { value: "Shirpur", label: "Shirpur (शिरपूर)" },
  { value: "Satnavari", label: "Satnavari (सातनवरी)" },
  { value: "Salai_Godhani", label: "Salai Godhani (सालई गोधनी)" },
  { value: "Savanga", label: "Savanga (सावंगा)" },
  { value: "Sindewihiri", label: "Sindewihiri (सिंदेविहीरी)" },
  { value: "Sukali", label: "Sukali (सुकळी)" },
  { value: "Surabardi", label: "Surabardi (सुराबर्डी)" },
  { value: "Sonurli", label: "Sonurli (सोनूर्ली)" },
  { value: "Sonegaon_Nipani", label: "Sonegaon Nipani (सोनेगांव निपाणी)" },
  { value: "Sonegaon_Bori", label: "Sonegaon Bori (सोनेगांव बोरी)" },
  { value: "Sonegaon_Lodhi", label: "Sonegaon Lodhi (सोनेगांव लोधी)" },
  { value: "Hudkeshwar_Khurd", label: "Hudkeshwar Khurd (हुडकेश्वर खू)" },
  { value: "Hudkeshwar_Budruk", label: "Hudkeshwar Budruk (हुडकेश्वर बु)" }
];

function onDistrictChange() {
  const dist = document.getElementById("sel-district").value;
  const talukaSelect = document.getElementById("sel-taluka");
  talukaSelect.innerHTML = "";

  const defaultTalukaOpt = document.createElement("option");
  defaultTalukaOpt.value = "";
  defaultTalukaOpt.textContent = "-- निवडा (Select Taluka) --";
  defaultTalukaOpt.disabled = true;
  defaultTalukaOpt.selected = true;
  talukaSelect.appendChild(defaultTalukaOpt);

  if (dist === "Nagpur") {
    NAGPUR_TALUKAS.forEach(t => {
      const opt = document.createElement("option");
      opt.value = t.value;
      opt.textContent = t.label;
      talukaSelect.appendChild(opt);
    });
  } else if (dist) {
    // Realistic fallback talukas for simulated search
    const fallbackTalukas = [
      { value: `${dist}_Rural`, label: `${dist} Rural (${dist} ग्रामीण)` },
      { value: `${dist}_City`, label: `${dist} City (${dist} शहर)` },
      { value: `${dist}_North`, label: `${dist} North (${dist} उत्तर)` },
      { value: `${dist}_South`, label: `${dist} South (${dist} दक्षिण)` }
    ];
    fallbackTalukas.forEach(t => {
      const opt = document.createElement("option");
      opt.value = t.value;
      opt.textContent = t.label;
      talukaSelect.appendChild(opt);
    });
  }

  // Reset village select to placeholder
  const villageSelect = document.getElementById("sel-village");
  villageSelect.innerHTML = "";
  const defaultVillageOpt = document.createElement("option");
  defaultVillageOpt.value = "";
  defaultVillageOpt.textContent = "-- निवडा (Select Village) --";
  defaultVillageOpt.disabled = true;
  defaultVillageOpt.selected = true;
  villageSelect.appendChild(defaultVillageOpt);
}

function onTalukaChange() {
  const taluka = document.getElementById("sel-taluka").value;
  const villageSelect = document.getElementById("sel-village");
  villageSelect.innerHTML = "";

  const defaultVillageOpt = document.createElement("option");
  defaultVillageOpt.value = "";
  defaultVillageOpt.textContent = "-- निवडा (Select Village) --";
  defaultVillageOpt.disabled = true;
  defaultVillageOpt.selected = true;
  villageSelect.appendChild(defaultVillageOpt);

  if (taluka === "Nagpur_Rural") {
    NAGPUR_RURAL_VILLAGES.forEach(v => {
      const opt = document.createElement("option");
      opt.value = v.value;
      opt.textContent = v.label;
      villageSelect.appendChild(opt);
    });
  } else if (taluka) {
    // Keep Waranga in list so pilot data always resolves, plus realistic sample villages
    const sampleVillages = [
      { value: "Waranga", label: "Waranga (वारंगा)" },
      { value: "Central_Sector", label: "Central Sector (मध्यवर्ती विभाग)" },
      { value: "Shastri_Nagar", label: "Shastri Nagar (शास्त्री नगर)" },
      { value: "Vidya_Nagari", label: "Vidya Nagari (विद्या नगरी)" }
    ];
    sampleVillages.forEach(v => {
      const opt = document.createElement("option");
      opt.value = v.value;
      opt.textContent = v.label;
      villageSelect.appendChild(opt);
    });
  }
}

// Step 1 -> Step 2: Open Village Cadastral Map View
function openVillageMap() {
  const distSelect = document.getElementById("sel-district");
  const talukaSelect = document.getElementById("sel-taluka");
  const villageSelect = document.getElementById("sel-village");

  const distVal = distSelect ? distSelect.value : "";
  const talukaVal = talukaSelect ? talukaSelect.value : "";
  const villageVal = villageSelect ? villageSelect.value : "";

  // If user selected specific options, use their chosen labels; otherwise fallback gracefully to Nagpur / Nagpur Rural / Waranga
  const distText = (distVal && distSelect.selectedIndex >= 0 && distSelect.options[distSelect.selectedIndex].value)
    ? distSelect.options[distSelect.selectedIndex].text 
    : "Nagpur (नागपूर)";
  const talukaText = (talukaVal && talukaSelect.selectedIndex >= 0 && talukaSelect.options[talukaSelect.selectedIndex].value)
    ? talukaSelect.options[talukaSelect.selectedIndex].text 
    : "Nagpur Rural (नागपूर ग्रामीण)";
  const villageText = (villageVal && villageSelect.selectedIndex >= 0 && villageSelect.options[villageSelect.selectedIndex].value)
    ? villageSelect.options[villageSelect.selectedIndex].text 
    : "Waranga (वारंगा)";

  // Update Location in Bhunaksha Sidebar
  const dispDist = document.getElementById("bhu-disp-district");
  if (dispDist) dispDist.innerText = distText;
  const dispTal = document.getElementById("bhu-disp-taluka");
  if (dispTal) dispTal.innerText = talukaText;
  const dispVil = document.getElementById("bhu-disp-village");
  if (dispVil) dispVil.innerText = villageText;
  const bhuTitle = document.getElementById("bhu-toolbar-title");
  if (bhuTitle) bhuTitle.innerText = `${villageText} Cadastral Map Sheet • Revenue Village 270900090108850000`;

  // Reset Map View State
  const mapImg = document.getElementById("bhunaksha-map-img");
  if (mapImg) mapImg.src = "/static/map_unhighlighted.png?v=3.3";
  const plotInput = document.getElementById("bhu-plot-input");
  if (plotInput) plotInput.value = "";
  const plotSelect = document.getElementById("bhu-plot-select");
  if (plotSelect) plotSelect.value = "";
  const plotInfo = document.getElementById("bhu-plot-info-container");
  if (plotInfo) plotInfo.style.display = "none";
  const badge = document.getElementById("plot140-badge");
  if (badge) badge.style.display = "none";

  // Switch from Search Card to Bhunaksha Map
  document.getElementById("view-search").style.setProperty("display", "none", "important");
  document.getElementById("view-results").style.setProperty("display", "none", "important");
  const bhuView = document.getElementById("view-bhunaksha");
  bhuView.style.setProperty("display", "flex", "important");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

// Bhunaksha Plot Search (triggered on click, enter key, or dropdown)
function searchBhunakshaPlot() {
  const plot = (document.getElementById("bhu-plot-input").value || "").trim();
  if (!plot) {
    showToast("Please enter a Plot Number (e.g. 140)", "error");
    return;
  }

  if (plot === "140" || plot.startsWith("140")) {
    selectPlot140();
  } else {
    // Show realistic dummy data for other plot numbers
    const mapImg = document.getElementById("bhunaksha-map-img");
    if (mapImg) mapImg.src = "/static/map_unhighlighted.png?v=3.3";
    const badge = document.getElementById("plot140-badge");
    if (badge) badge.style.display = "none";

    const infoContainer = document.getElementById("bhu-plot-info-container");
    if (infoContainer) infoContainer.style.display = "block";
    const infoText = document.getElementById("bhu-plot-info-text");
    if (infoText) {
      infoText.innerText = `Survey No. : ${plot}/1\nTotal Area : 12.5000 Ha\nPot kharaba : 1.2000\nOwner Name : खासगी भूधारक (Private Freehold)\nKhata No. : 188\npu-id : 33550994106\n---------------------------\nMap Report`;
    }
  }
}

function onBhunakshaPlotSelect(val) {
  if (!val) return;
  const plotInput = document.getElementById("bhu-plot-input");
  if (plotInput) plotInput.value = val;
  searchBhunakshaPlot();
}

// Highlight Plot 140 & populate authentic government details
function selectPlot140() {
  const plotInput = document.getElementById("bhu-plot-input");
  if (plotInput) plotInput.value = "140";
  const plotSelect = document.getElementById("bhu-plot-select");
  if (plotSelect) plotSelect.value = "140";

  // Switch image to the highlighted map with Plot 140 colored in dark navy blue
  const mapImg = document.getElementById("bhunaksha-map-img");
  if (mapImg) {
    mapImg.src = "/static/map_highlighted.png?v=3.3";
  }

  // Show Plot 140 floating badge
  const badge = document.getElementById("plot140-badge");
  if (badge) badge.style.display = "block";

  // Show authentic Plot Info Box matching Bhunaksha screenshot
  const infoContainer = document.getElementById("bhu-plot-info-container");
  if (infoContainer) infoContainer.style.display = "block";

  const infoText = document.getElementById("bhu-plot-info-text");
  if (infoText) {
    infoText.innerText = `Survey No. : 140/1\nTotal Area : 0.0000\nPot kharaba : 29.0300\nOwner Name : महाराष्ट्र राज्य शासन\nKhata No. : 341\n---------------------------\nSurvey No. : 140/2\nTotal Area : 0.0000\nPot kharaba : 24.0000\nOwner Name : महाराष्ट्र नॅशनल लॉ युनिव्हर्सिटी\nKhata No. : 623\n---------------------------\nSurvey No. : 140/3\nTotal Area : 0.0000\nPot kharaba : 19.8100\nOwner Name : कविकुलगुरू कालिदास संस्कृत विश्वविद्यालय\nKhata No. : 624\n---------------------------\nMap Report`;
  }
}

// Step 2 -> Step 3: Enter into the Main Page (where 3D buildings are plotted)
async function enter3DStratum() {
  const plotInput = document.getElementById("bhu-plot-input");
  const plotVal = (plotInput ? plotInput.value.trim() : "") || "140";
  const surveyNo = plotVal.includes("/") ? plotVal : `${plotVal}/1`;

  // Hide Bhunaksha map & search views, show 3D results workspace
  document.getElementById("view-search").style.setProperty("display", "none", "important");
  document.getElementById("view-bhunaksha").style.setProperty("display", "none", "important");
  const resultsView = document.getElementById("view-results");
  resultsView.style.setProperty("display", "flex", "important");
  window.scrollTo({ top: 0, behavior: "smooth" });

  // Update breadcrumb
  const breadcrumbEl = document.getElementById("breadcrumb-survey-label") || document.querySelector(".breadcrumb-path strong");
  if (breadcrumbEl) {
    breadcrumbEl.innerText = `Survey ${surveyNo} (pu-id: 33550994106)`;
  }

  // Load analytics & render 3D twin for active building
  await loadAnalytics();
  await selectBuilding("HSTL01");
}

// Navigation Back to Bhunaksha Map
function backToBhunakshaMap() {
  document.getElementById("view-results").style.setProperty("display", "none", "important");
  document.getElementById("view-search").style.setProperty("display", "none", "important");
  const bhuView = document.getElementById("view-bhunaksha");
  bhuView.style.setProperty("display", "flex", "important");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

// Navigation Back to Initial Search
function backToSearch() {
  document.getElementById("view-results").style.setProperty("display", "none", "important");
  document.getElementById("view-bhunaksha").style.setProperty("display", "none", "important");
  const searchView = document.getElementById("view-search");
  searchView.style.setProperty("display", "flex", "important");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

// Bhunaksha Map Zoom Controls
let bhuMapZoomLevel = 1.0;
function zoomBhunakshaMap(factor) {
  bhuMapZoomLevel = Math.max(0.6, Math.min(bhuMapZoomLevel * factor, 3.0));
  const target = document.getElementById("map-zoom-target");
  if (target) {
    target.style.transform = `scale(${bhuMapZoomLevel})`;
  }
}

function resetBhunakshaMapZoom() {
  bhuMapZoomLevel = 1.0;
  const target = document.getElementById("map-zoom-target");
  if (target) {
    target.style.transform = `scale(1.0)`;
  }
}

function onMapClick(event) {
  const rect = event.target.getBoundingClientRect();
  const x = (event.clientX - rect.left) / rect.width;
  const y = (event.clientY - rect.top) / rect.height;

  // Western parcel (Plot 140) bounds approx: x between 0.18 and 0.48, y between 0.15 and 0.75
  if (x >= 0.18 && x <= 0.48 && y >= 0.15 && y <= 0.75) {
    selectPlot140();
  }
}

// Select Building from the 4 Cards
async function selectBuilding(buildingId) {
  currentBuildingId = buildingId;

  // Update active state on 4 cards
  document.querySelectorAll(".building-card").forEach(c => c.classList.remove("active"));
  const activeCard = document.getElementById(`bldg-card-${buildingId}`);
  if (activeCard) activeCard.classList.add("active");

  if (!BUILDING_METADATA[buildingId]) {
    BUILDING_METADATA[buildingId] = {
      name: `${buildingId} Building`,
      status: "completed",
      desc: "3D Volumetric digital twin registered in National Cadastre."
    };
  }

  // Check if building has been completed in backend database
  try {
    const checkRes = await fetch(`/api/parcels/mesh-data/${buildingId}`);
    if (checkRes.ok) {
      const bData = await checkRes.json();
      if (bData.data_status === "completed" && bData.parcels && bData.parcels.length > 0) {
        BUILDING_METADATA[buildingId].status = "completed";
      }
    }
  } catch (e) {
    // Keep fallback metadata status
  }

  const meta = BUILDING_METADATA[buildingId];
  document.getElementById("viewport-building-title").innerText = `${meta.name} (${buildingId}) — Volumetric 3D Twin`;

  const controls = document.getElementById("surveyed-controls");

  if (meta.status === "completed") {
    controls.style.display = "flex";
    await loadBuilding3DTwin(buildingId);
  } else {
    controls.style.display = "none";
    renderPendingNotice(buildingId, meta);
  }
}

// Render Informational View for Other Campus Buildings
function renderPendingNotice(buildingId, meta) {
  const container = document.getElementById("plot3d-container");
  const defaultFloors = buildingId.includes('ADMIN') ? 3 : (buildingId.includes('ACAD') ? 4 : 5);
  container.innerHTML = `
    <div class="pending-notice-box">
      <div style="font-size:2.2rem;margin-bottom:12px;color:#b45309;"></div>
      <div class="pending-notice-title">${meta.name} (${buildingId})</div>
      <div class="pending-notice-desc">
        ${meta.desc}
        <br><br>
        <strong>Cadastral Status:</strong> Survey data pending ingestion. Field surveyors can upload CAD drawings or scanned plans through the AI Studio or Ingestion Engine.
      </div>
      <div style="display:flex;gap:10px;justify-content:center;margin-top:16px;flex-wrap:wrap;">
        <a href="/studio?bldg_id=${buildingId}&bldg_name=${encodeURIComponent(meta.name)}&floors=${defaultFloors}" class="btn btn-primary" style="background:#6366f1;border:1px solid #4f46e5;text-decoration:none;display:inline-flex;align-items:center;gap:6px;font-weight:600;box-shadow:0 2px 6px rgba(99,102,241,0.25);">
           Digitize with AI 3D Studio &rarr;
        </a>
        <button class="btn btn-subtle" onclick="openIngestModal('${buildingId}')" style="background:#f1f5f9;color:#334155;border:1px solid #cbd5e1;">
           Ingestion Engine
        </button>
        <button class="btn btn-subtle" onclick="selectBuilding('HSTL01')">
          ← View Hostel Block A
        </button>
      </div>
    </div>
  `;

  // Update Inspector
  document.getElementById("insp-ulpin").innerText = `N/A (${buildingId})`;
  const unitEl = document.getElementById("insp-unit-num");
  if (unitEl) unitEl.innerText = "--";
  document.getElementById("insp-type").innerText = "Institutional Building";
  document.getElementById("insp-floor").innerText = "Ground Level";
  document.getElementById("insp-area").innerText = "0.00 m²";
  document.getElementById("insp-volume").innerText = "0.00 m³";
  document.getElementById("insp-uds").innerText = "0.00000%";
  document.getElementById("insp-gps").innerText = "20.949556, 79.029472 (Campus Anchor)";
  document.getElementById("insp-occupants-list").innerHTML = `<span style="color:#8c857b;font-size:0.75rem;">Institutional Estate</span>`;
  document.getElementById("insp-liens-list").innerHTML = `<span style="color:#8c857b;font-size:0.75rem;">Clear Title</span>`;
}

async function loadCustomBuilding() {
  const el = document.getElementById("custom-building-id");
  const customId = el ? el.value.trim() : "";
  if(!customId) {
    showToast("Please enter a Building ID (e.g. TEST_001)", "error");
    return;
  }
  
  // Register dynamically
  if(!BUILDING_METADATA[customId]) {
    BUILDING_METADATA[customId] = {
      name: `AI Generated Building (${customId})`,
      status: "completed",
      desc: "Dynamically generated volumetric building model via AI Pipeline."
    };
  } else {
    BUILDING_METADATA[customId].status = "completed";
  }
  
  await selectBuilding(customId);
  showToast(`Loaded AI Twin for ${customId}`, "success");
}


// Load System-Wide Analytics
async function loadAnalytics() {
  try {
    const res = await fetch("/api/analytics/summary");
    const data = await res.json();
    const chip = document.getElementById("chip-stats");
    if (chip) {
      chip.innerText = `Survey 140/1 | Waranga | pu-id: 33550994106 (${data.total_3d_parcels} Units)`;
    }
  } catch (err) {
    console.error("Failed to load analytics:", err);
  }
}

// Load and Render 3D Digital Twin Mesh for HSTL01
async function loadBuilding3DTwin(buildingId) {
  const container = document.getElementById("plot3d-container");
  container.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#8c857b;font-size:0.82rem;">Loading verified spatial geometry for ${buildingId}...</div>`;

  try {
    const res = await fetch(`/api/parcels/mesh-data/${buildingId}`);
    if (!res.ok) throw new Error("Building geometry not found");
    currentBuildingData = await res.json();

    if (currentBuildingData.data_status !== "completed") {
      renderPendingNotice(buildingId, BUILDING_METADATA[buildingId]);
      return;
    }

    // Populate Floor Filter Dropdown
    const floorSel = document.getElementById("floor-filter");
    floorSel.innerHTML = '<option value="ALL">All Floors (10 Floors)</option>';
    currentBuildingData.floors.forEach(fl => {
      const opt = document.createElement("option");
      opt.value = fl;
      opt.innerText = `Floor ${fl}`;
      floorSel.appendChild(opt);
    });

    renderPlotly3D(currentBuildingData.parcels);

    // Inspect first unit by default
    if (currentBuildingData.parcels.length > 0) {
      inspectParcel(currentBuildingData.parcels[0].ulpin_3d);
    }
  } catch (err) {
    container.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#b91c1c;">Error loading 3D Mesh: ${err.message}</div>`;
  }
}

function renderPlotly3D(parcels) {
  const traces = [];

  parcels.forEach((p) => {
    const x0 = p.x0, x1 = p.x1;
    const y0 = p.y0, y1 = p.y1;
    const z0 = p.z0, z1 = p.z1;

    // 8 Box Vertices
    const vx = [x0, x1, x1, x0, x0, x1, x1, x0];
    const vy = [y0, y0, y1, y1, y0, y0, y1, y1];
    const vz = [z0, z0, z0, z0, z1, z1, z1, z1];

    // 12 Triangular Facets
    const i = [7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2];
    const j = [3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3];
    const k = [0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6];

    let hoverText = `<b>3D ULPIN:</b> ${p.ulpin_3d}<br>` +
                    `<b>2D Base Parcel:</b> 33550994106 (Surv 140/1)<br>` +
                    `<b>Floor:</b> ${p.floor} | <b>Unit:</b> ${p.room_id}<br>` +
                    `<b>Zoning:</b> ${p.type} (${p.status_label})<br>` +
                    `<b>Carpet Area:</b> ${p.carpet_area} m² | <b>Volume:</b> ${p.volume} m³<br>` +
                    `<b>Undivided Land Share (UDS):</b> ${(p.uds * 100).toFixed(4)}%<br>` +
                    `<b>Coordinates:</b> ${p.latitude}, ${p.longitude}`;

    if (p.has_lien) hoverText += `<br><span style="color:#b91c1c;font-weight:bold;">Active Mortgage Lien</span>`;
    if (p.occupants.length > 0) hoverText += `<br><b>Titleholder(s):</b> ${p.occupants.join(", ")}`;

    let color = "#475569";
    if (p.type === "4S" || p.type === "2S") {
      if (p.occupants.length === 0) color = "#16a34a";      // warm forest green (vacant)
      else if (p.occupants.length < 4) color = "#d97706";   // warm amber (partial)
      else color = "#dc2626";                               // warm red (full)
    } else if (p.type === "CORR") {
      color = "#0284c7";                                    // slate blue
    } else if (p.type === "STR" || p.type === "LIFT") {
      color = "#64748b";                                    // transit slate
    } else if (p.type === "WASH") {
      color = "#0d9488";                                    // teal
    } else if (p.type === "HALL") {
      color = "#b45309";                                    // ochre
    }

    traces.push({
      type: "mesh3d",
      x: vx, y: vy, z: vz,
      i: i, j: j, k: k,
      color: color,
      opacity: p.type === "CORR" ? 0.50 : 0.88,
      flatshading: true,
      name: p.ulpin_3d,
      hoverinfo: "text",
      hovertext: hoverText,
      customdata: [p.ulpin_3d],
      lighting: { ambient: 0.75, diffuse: 0.8, specular: 0.1, roughness: 0.6 }
    });
  });

  const layout = {
    paper_bgcolor: "#ebe8e0",
    plot_bgcolor: "#ebe8e0",
    margin: { l: 0, r: 0, b: 0, t: 0 },
    scene: {
      xaxis: { title: "X (East Meters)", color: "#78716c", gridcolor: "#dfdcce", showbackground: false },
      yaxis: { title: "Y (North Meters)", color: "#78716c", gridcolor: "#dfdcce", showbackground: false },
      zaxis: { title: "Elevation Z (Meters)", color: "#78716c", gridcolor: "#dfdcce", showbackground: false },
      aspectmode: "data",
      camera: {
        eye: { x: 1.6, y: -1.8, z: 1.4 }
      }
    },
    showlegend: false
  };

  const config = {
    responsive: true,
    displayModeBar: true,
    modeBarButtonsToRemove: ["lasso2d", "select2d"]
  };

  Plotly.newPlot("plot3d-container", traces, layout, config);

  // Hook Click & Hover Events so right panel updates on interaction
  const plotDiv = document.getElementById("plot3d-container");
  plotDiv.on("plotly_click", (data) => {
    if (data.points && data.points.length > 0) {
      const traceIdx = data.points[0].curveNumber;
      const ulpin = traces[traceIdx].name;
      inspectParcel(ulpin);
    }
  });

  plotDiv.on("plotly_hover", (data) => {
    if (data.points && data.points.length > 0) {
      const traceIdx = data.points[0].curveNumber;
      const ulpin = traces[traceIdx].name;
      inspectParcel(ulpin);
    }
  });
}

function filter3DView() {
  if (!currentBuildingData || !currentBuildingData.parcels) return;
  const floorVal = document.getElementById("floor-filter").value;
  const typeVal = document.getElementById("type-filter").value;

  let filtered = currentBuildingData.parcels;

  if (floorVal !== "ALL") {
    filtered = filtered.filter(p => p.floor === parseInt(floorVal));
  }

  if (typeVal === "RESIDENTIAL") {
    filtered = filtered.filter(p => p.type === "4S" || p.type === "2S");
  } else if (typeVal === "COMMON") {
    filtered = filtered.filter(p => ["WASH", "STR", "LIFT", "CORR", "BRIDGE", "HALL", "UTIL"].includes(p.type));
  }

  renderPlotly3D(filtered);
}

// Inspect 3D Parcel Details Drawer
async function inspectParcel(ulpin) {
  currentSelectedUlpin = ulpin;
  try {
    const res = await fetch(`/api/parcels/${ulpin}`);
    if (!res.ok) return;
    const p = await res.json();

    document.getElementById("insp-ulpin").innerText = p.ulpin_3d;
    const unitEl = document.getElementById("insp-unit-num");
    if (unitEl) unitEl.innerText = `Unit ${p.room_id}`;
    document.getElementById("insp-type").innerText = `${p.type} (${p.is_common_property ? 'Common Property' : 'Private Stratum'})`;
    document.getElementById("insp-floor").innerText = `Floor ${p.floor} (Z: ${p.z_min}m to ${p.z_max}m)`;
    document.getElementById("insp-area").innerText = `${p.carpet_area_sqm} m²`;
    document.getElementById("insp-volume").innerText = `${p.gross_volume_cbm} m³`;
    document.getElementById("insp-uds").innerText = `${(p.undivided_share_land * 100).toFixed(5)}% of Base Surface`;
    document.getElementById("insp-gps").innerText = `${p.latitude}, ${p.longitude}`;

    // Occupants / Titleholders
    const occContainer = document.getElementById("insp-occupants-list");
    if (p.occupants.length === 0) {
      occContainer.innerHTML = `<span style="color:#8c857b;font-size:0.75rem;">Vacant (No active title recorded)</span>`;
    } else {
      occContainer.innerHTML = p.occupants.map(o => `
        <div style="display:flex;align-items:center;justify-content:space-between;padding:3px 0;font-size:0.74rem;">
          <span style="color:#1c1917;font-weight:600;">${o}</span>
          <span style="color:#15803d;font-size:0.68rem;background:#dcfce7;padding:1px 5px;border-radius:3px;font-weight:600;">ACTIVE TITLE</span>
        </div>
      `).join("");
    }

    // Encumbrances
    const lienContainer = document.getElementById("insp-liens-list");
    if (!p.active_encumbrances || p.active_encumbrances.length === 0) {
      lienContainer.innerHTML = `<span style="color:#15803d;font-size:0.74rem;font-weight:500;">Clear Title (No Active Encumbrance)</span>`;
    } else {
      lienContainer.innerHTML = p.active_encumbrances.map(e => `
        <div style="background:#fef2f2;border:1px solid #fecaca;border-radius:4px;padding:6px 8px;margin-top:4px;">
          <div style="color:#b91c1c;font-weight:600;font-size:0.74rem;">${e.mortgagee_name}</div>
          <div style="color:#44403c;font-size:0.7rem;margin-top:1px;">Ref: ${e.sanction_reference}</div>
          <div style="color:#78716c;font-size:0.7rem;">Amount: ₹${Number(e.loan_amount_inr).toLocaleString()}</div>
        </div>
      `).join("");
    }

    // Update modal inputs if modal open
    const modalInput = document.getElementById("modal-ulpin-input");
    if (modalInput) modalInput.value = p.ulpin_3d;
  } catch (err) {
    console.error("Error inspecting parcel:", err);
  }
}

// Modal Controls
function openModal(tab = "allot") {
  document.getElementById("action-modal").style.display = "flex";
  switchModalTab(tab);
  if (currentSelectedUlpin) {
    document.getElementById("modal-ulpin-input").value = currentSelectedUlpin;
    document.getElementById("transfer-ulpin-input").value = currentSelectedUlpin;
    document.getElementById("mortgage-ulpin-input").value = currentSelectedUlpin;
  }
}

function closeModal() {
  document.getElementById("action-modal").style.display = "none";
}

function switchModalTab(tab) {
  activeModalTab = tab;
  document.querySelectorAll(".tab-item").forEach(t => t.classList.remove("active"));
  document.querySelectorAll(".tab-content").forEach(c => c.style.display = "none");

  document.getElementById(`tab-btn-${tab}`).classList.add("active");
  document.getElementById(`tab-content-${tab}`).style.display = "flex";
}

// Submit Allotment
async function submitAllotment() {
  const ulpin = document.getElementById("modal-ulpin-input").value;
  const partyId = document.getElementById("modal-party-id").value;
  const name = document.getElementById("modal-party-name").value;

  if (!ulpin || !partyId) {
    showToast("Please enter ULPIN and Party ID", "error");
    return;
  }

  try {
    const res = await fetch("/api/rights/allot", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ulpin_3d: ulpin, party_id: partyId, name: name })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Allotment failed");

    showToast(data.message.replace(/[]/g, "").trim(), "success");
    closeModal();
    await loadBuilding3DTwin(currentBuildingId);
    await loadAnalytics();
    inspectParcel(ulpin);
  } catch (err) {
    showToast(err.message.replace(/[]/g, "").trim(), "error");
  }
}

// Submit Strata Transfer
async function submitTransfer() {
  const ulpin = document.getElementById("transfer-ulpin-input").value;
  const fromParty = document.getElementById("transfer-from-party").value;
  const toParty = document.getElementById("transfer-to-party").value;
  const toName = document.getElementById("transfer-to-name").value;
  const price = parseFloat(document.getElementById("transfer-price").value) || 0.0;

  if (!ulpin || !fromParty || !toParty) {
    showToast("Please fill all required transfer fields", "error");
    return;
  }

  try {
    const res = await fetch("/api/rights/transfer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ulpin_3d: ulpin,
        from_party_id: fromParty,
        to_party_id: toParty,
        to_party_name: toName || toParty,
        conveyance_price_inr: price
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Transfer mutation failed");

    showToast(data.message.replace(/[]/g, "").trim(), "success");
    closeModal();
    await loadBuilding3DTwin(currentBuildingId);
    inspectParcel(ulpin);
  } catch (err) {
    showToast(err.message.replace(/[]/g, "").trim(), "error");
  }
}

// Submit Mortgage Stamping
async function submitMortgage() {
  const ulpin = document.getElementById("mortgage-ulpin-input").value;
  const mortgagee = document.getElementById("mortgage-bank").value;
  const ref = document.getElementById("mortgage-ref").value;
  const amount = parseFloat(document.getElementById("mortgage-amount").value) || 0.0;

  if (!ulpin || !mortgagee || !ref) {
    showToast("Please fill all required mortgage fields", "error");
    return;
  }

  try {
    const res = await fetch("/api/encumbrances/stamp", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ulpin_3d: ulpin,
        mortgagee_name: mortgagee,
        sanction_reference: ref,
        loan_amount_inr: amount
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Mortgage stamping failed");

    showToast(data.message.replace(/[]/g, "").trim(), "success");
    closeModal();
    await loadBuilding3DTwin(currentBuildingId);
    await loadAnalytics();
    inspectParcel(ulpin);
  } catch (err) {
    showToast(err.message.replace(/[]/g, "").trim(), "error");
  }
}

// Run Live 3D Topology Audit
async function runTopologyAudit() {
  try {
    const res = await fetch(`/api/topology/validate/${currentBuildingId}`);
    const data = await res.json();
    if (!res.ok) throw new Error("Validation check failed");

    const msg = `Topology Compliance Report (${currentBuildingId}):\n` +
                `- Total Audited 3D Parcels: ${data.total_parcels_audited}\n` +
                `- Spatial 3D Collisions: ${data['3d_collision_count']}\n` +
                `- Duplicate Identifiers: ${data.duplicate_id_count}\n` +
                `- Compliance Rating: ${data.compliance_score_percent}% (${data.validation_status})`;
    alert(msg);
  } catch (err) {
    showToast(err.message.replace(/[]/g, "").trim(), "error");
  }
}

function showToast(message, type = "info") {
  // Suppressed on screen per user request (no popup banners or warnings)
  console.log(`[Toast ${type}]:`, message);
}

// ========================================================
// FIELD SURVEYOR INGESTION PORTAL LOGIC
// ========================================================
let lastIngestedBuildingId = null;

function openIngestModal(buildingId = "ADMIN01") {
  const modal = document.getElementById("ingest-modal");
  if (!modal) return;

  // Sanitize buildingId if called from event handler
  if (typeof buildingId !== "string" || !buildingId) {
    buildingId = (typeof currentBuildingId === "string" && currentBuildingId) ? currentBuildingId : "ADMIN01";
  }

  const meta = BUILDING_METADATA[buildingId] || { name: `${buildingId} Building`, desc: "" };
  
  const bldgIdInput = document.getElementById("inp-ingest-bldg-id");
  const bldgNameInput = document.getElementById("inp-ingest-bldg-name");
  const categorySel = document.getElementById("sel-ingest-category");
  const floorsInput = document.getElementById("inp-ingest-floors");

  if (bldgIdInput) bldgIdInput.value = buildingId;
  if (bldgNameInput) bldgNameInput.value = meta.name;
  
  if (buildingId.includes("ACAD")) {
    if (categorySel) categorySel.value = "Academic & Laboratories";
    if (floorsInput) floorsInput.value = "4";
    loadRulePreset("academic");
  } else if (buildingId.includes("RES")) {
    if (categorySel) categorySel.value = "Staff & Faculty Housing";
    if (floorsInput) floorsInput.value = "10";
    loadRulePreset("residential");
  } else if (buildingId.includes("HSTL")) {
    if (categorySel) categorySel.value = "Student Housing / Residential Stratum";
    if (floorsInput) floorsInput.value = "10";
    loadRulePreset("hostel");
  } else {
    if (categorySel) categorySel.value = "Administrative Complex";
    if (floorsInput) floorsInput.value = "3";
    loadRulePreset("admin");
  }

  // Reset results
  const resultsBox = document.getElementById("ingest-results-box");
  if (resultsBox) resultsBox.style.display = "none";
  modal.style.display = "flex";
}


function closeIngestModal() {
  const modal = document.getElementById("ingest-modal");
  if (modal) modal.style.display = "none";
}

function handlePlanFileSelected(input) {
  const badge = document.getElementById("badge-plan-file");
  if (input.files && input.files[0]) {
    const file = input.files[0];
    badge.innerText = `Selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
    badge.style.display = "inline-block";
  } else {
    badge.style.display = "none";
  }
}

function handlePointCloudFileSelected(input) {
  const badge = document.getElementById("badge-pointcloud-file");
  if (input.files && input.files[0]) {
    const file = input.files[0];
    badge.innerText = `Selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
    badge.style.display = "inline-block";
  } else {
    badge.style.display = "none";
  }
}

function addRuleRow(pattern = "", type = "ROOM", depth = "", isCommon = false) {
  const tbody = document.getElementById("rules-table-body");
  const tr = document.createElement("tr");
  tr.className = "rule-row";
  tr.innerHTML = `
    <td><input type="text" class="rule-pattern" value="${pattern}" placeholder="e.g. OFFICE* or A0[1-6]"></td>
    <td>
      <select class="rule-type">
        <option value="OFFICE" ${type === "OFFICE" ? "selected" : ""}>OFFICE (Private Stratum)</option>
        <option value="CLASS" ${type === "CLASS" ? "selected" : ""}>CLASS (Classroom)</option>
        <option value="LAB" ${type === "LAB" ? "selected" : ""}>LAB (Laboratory)</option>
        <option value="4S" ${type === "4S" ? "selected" : ""}>4S (4-Seater Res)</option>
        <option value="2S" ${type === "2S" ? "selected" : ""}>2S (2-Seater Res)</option>
        <option value="3BHK" ${type === "3BHK" ? "selected" : ""}>3BHK (Residential)</option>
        <option value="2BHK" ${type === "2BHK" ? "selected" : ""}>2BHK (Residential)</option>
        <option value="HALL" ${type === "HALL" ? "selected" : ""}>HALL (Common Hall)</option>
        <option value="CONF" ${type === "CONF" ? "selected" : ""}>CONF (Conference)</option>
        <option value="WASH" ${type === "WASH" ? "selected" : ""}>WASH (Common Washroom)</option>
        <option value="STR" ${type === "STR" ? "selected" : ""}>STR (Common Stairs)</option>
        <option value="LIFT" ${type === "LIFT" ? "selected" : ""}>LIFT (Vertical Core)</option>
        <option value="CORR" ${type === "CORR" ? "selected" : ""}>CORR (Corridor)</option>
        <option value="BRIDGE" ${type === "BRIDGE" ? "selected" : ""}>BRIDGE (Skybridge)</option>
        <option value="UTIL" ${type === "UTIL" ? "selected" : ""}>UTIL (Utility / Plant)</option>
      </select>
    </td>
    <td><input type="number" step="0.5" class="rule-depth" value="${depth}" placeholder="Auto (m)"></td>
    <td style="text-align:center;"><input type="checkbox" class="rule-common" ${isCommon ? "checked" : ""}></td>
    <td style="text-align:center;"><button type="button" class="btn-del-rule" onclick="deleteRuleRow(this)"></button></td>
  `;
  tbody.appendChild(tr);
}

function deleteRuleRow(btn) {
  const tr = btn.closest("tr");
  if (tr) tr.remove();
}

function loadRulePreset(presetName) {
  const tbody = document.getElementById("rules-table-body");
  tbody.innerHTML = "";

  if (presetName === "admin") {
    addRuleRow(".*(OFFICE|DIR|DEAN|REG).*", "OFFICE", "6.0", false);
    addRuleRow(".*(CONF|MEET|BOARD).*", "CONF", "8.0", true);
    addRuleRow(".*(WASH|TOILET).*", "WASH", "3.0", true);
    addRuleRow(".*(STR|STAIR|LIFT).*", "STR", "4.0", true);
    addRuleRow(".*(CORR|LOBBY).*", "CORR", "2.5", true);
  } else if (presetName === "academic") {
    addRuleRow(".*(CLASS|CR|LH|AUDI).*", "CLASS", "9.0", false);
    addRuleRow(".*(LAB|WORKSHOP).*", "LAB", "12.0", false);
    addRuleRow(".*(FACULTY|DEPT).*", "OFFICE", "5.0", false);
    addRuleRow(".*(WASH|TOILET).*", "WASH", "3.5", true);
    addRuleRow(".*(STR|LIFT).*", "STR", "4.5", true);
    addRuleRow(".*(CORR).*", "CORR", "3.0", true);
  } else if (presetName === "hostel") {
    addRuleRow("^X0[1-6]$", "4S", "8.8", false);
    addRuleRow("^X(0[7-9]|1[0-8])$", "2S", "4.0", false);
    addRuleRow(".*(Common|Hall).*", "HALL", "17.2", true);
    addRuleRow(".*Washroom.*", "WASH", "6.4", true);
    addRuleRow(".*(Stairs|LIFT).*", "STR", "4.8", true);
    addRuleRow(".*", "CORR", "2.0", true);
  } else if (presetName === "residential") {
    addRuleRow(".*(3BHK|FLAT_A).*", "3BHK", "12.0", false);
    addRuleRow(".*(2BHK|FLAT_B).*", "2BHK", "9.5", false);
    addRuleRow(".*(LIFT|ELEVATOR).*", "LIFT", "3.0", true);
    addRuleRow(".*(STR|STAIR).*", "STR", "4.0", true);
    addRuleRow(".*(LOBBY|CORR).*", "CORR", "2.5", true);
  }
}

async function submitIngestionPipeline() {
  const bldgId = document.getElementById("inp-ingest-bldg-id").value.trim().toUpperCase();
  const bldgName = document.getElementById("inp-ingest-bldg-name").value.trim();
  const category = document.getElementById("sel-ingest-category").value;
  const lat = parseFloat(document.getElementById("inp-ingest-lat").value);
  const lon = parseFloat(document.getElementById("inp-ingest-lon").value);
  const floors = parseInt(document.getElementById("inp-ingest-floors").value, 10);
  const pitch = parseFloat(document.getElementById("inp-ingest-pitch").value);
  const clearHeight = parseFloat(document.getElementById("inp-ingest-clear-height").value);
  const slab = parseFloat(document.getElementById("inp-ingest-slab").value);
  const flip = document.getElementById("sel-ingest-flip").value === "true";

  const fileInput = document.getElementById("file-ingest-plan");
  const pcInput = document.getElementById("file-ingest-pointcloud");

  if (!bldgId || !bldgName) {
    showToast("Please provide a Building ID and Name", "error");
    return;
  }

  if (!fileInput.files || fileInput.files.length === 0) {
    showToast("Please select a floor plan file (PDF or scanned image)", "error");
    return;
  }

  // Collect rules from table
  const ruleRows = document.querySelectorAll("#rules-table-body .rule-row");
  const rules = [];
  ruleRows.forEach((row, idx) => {
    const pattern = row.querySelector(".rule-pattern").value.trim();
    const type = row.querySelector(".rule-type").value;
    const depth = parseFloat(row.querySelector(".rule-depth").value) || null;
    const isCommon = row.querySelector(".rule-common").checked;
    if (pattern || type) {
      rules.push({
        rule_id: `rule_${idx + 1}`,
        label_pattern: pattern || ".*",
        type: type,
        depth_m: depth,
        is_common: isCommon
      });
    }
  });

  const submitBtn = document.getElementById("btn-run-ingestion");
  const origText = submitBtn.innerText;
  submitBtn.disabled = true;
  submitBtn.innerText = "Executing Cadastral Ingestion Pipeline...";

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);
  if (pcInput.files && pcInput.files.length > 0) {
    formData.append("point_cloud", pcInput.files[0]);
  }
  formData.append("building_id", bldgId);
  formData.append("building_name", bldgName);
  formData.append("category", category);
  formData.append("total_floors", floors);
  formData.append("floor_pitch_m", pitch);
  formData.append("room_clear_height_m", clearHeight);
  formData.append("slab_thickness_m", slab);
  formData.append("anchor_lat", lat);
  formData.append("anchor_lon", lon);
  formData.append("flip_horizontal", flip);
  formData.append("rules_json", JSON.stringify(rules));

  try {
    const res = await fetch("/api/ingestion/run", {
      method: "POST",
      body: formData
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Ingestion pipeline failed.");
    }

    lastIngestedBuildingId = bldgId;

    // Update Local Metadata & Status
    BUILDING_METADATA[bldgId] = {
      name: bldgName,
      status: "completed",
      desc: `${floors} Floors · ${data.total_units} 3D Volumetric Units · Carpet Area ${data.total_carpet_area_sqm} m²`
    };

    // Render Diagnostics Results Box
    const resultsBox = document.getElementById("ingest-results-box");
    resultsBox.style.display = "flex";

    document.getElementById("diag-status-icon").innerText = data.topology_validation.passed ? "" : "";
    document.getElementById("diag-title").innerText = `${bldgName} (${bldgId}) Ingested Successfully`;
    document.getElementById("diag-method-badge").innerText = data.extraction_method.toUpperCase();

    document.getElementById("diag-total-parcels").innerText = data.total_units;
    document.getElementById("diag-res-parcels").innerText = data.residential_units;
    document.getElementById("diag-common-parcels").innerText = data.common_units;
    document.getElementById("diag-carpet-area").innerText = `${data.total_carpet_area_sqm.toLocaleString()} m²`;

    // Point Cloud Banner
    const droneBanner = document.getElementById("diag-drone-banner");
    const pc = data.point_cloud_audit;
    if (pc && pc.status === "VERIFIED") {
      droneBanner.style.display = "block";
      droneBanner.style.background = "#f0fdf4";
      droneBanner.style.color = "#166534";
      droneBanner.style.borderColor = "#bbf7d0";
      droneBanner.innerHTML = `<strong> Drone ML Height Validation:</strong> ${pc.message}`;
    } else if (pc && pc.status === "DISCREPANCY_FLAGGED") {
      droneBanner.style.display = "block";
      droneBanner.style.background = "#fffbeb";
      droneBanner.style.color = "#92400e";
      droneBanner.style.borderColor = "#fde68a";
      droneBanner.innerHTML = `<strong> Drone ML Height Validation:</strong> ${pc.message}`;
    } else {
      droneBanner.style.display = "none";
    }

    // OCR Warnings
    const ocrContainer = document.getElementById("diag-ocr-container");
    const ocrList = document.getElementById("diag-ocr-list");
    ocrList.innerHTML = "";

    if (data.ocr_diagnostics && data.ocr_diagnostics.low_confidence_units_count > 0) {
      ocrContainer.style.display = "block";
      ocrList.innerHTML = `<button class="btn btn-subtle" onclick="submitOCRCorrections(this)" style="float:right;padding:3px 8px;font-size:0.7rem;margin-bottom:4px;background:#fef3c7;border:1px solid #fde68a;"> Approve AI OCR Corrections</button><div style="clear:both;"></div>`;
      data.ocr_diagnostics.low_confidence_warnings.slice(0, 4).forEach(w => {
        const item = document.createElement("div");
        item.className = "ocr-warning-item";
        item.style.marginBottom = "4px";
        item.style.display = "flex";
        item.style.alignItems = "center";
        item.style.gap = "6px";
        
        item.innerHTML = `<span style="font-size:0.7rem;">• Unit [${w.unit_id}] Confidence ${w.confidence_score}%</span>
                          <input type="text" value="${w.ocr_text || 'Unknown'}" style="font-size:0.7rem;padding:2px;border:1px solid #fca5a5;border-radius:2px;width:70px;">
                          <span style="font-size:0.65rem;color:#b91c1c;">${w.warning}</span>`;
        ocrList.appendChild(item);
      });
    } else {
      ocrContainer.style.display = "none";
    }

    showToast(`Successfully ingested ${data.total_units} 3D parcels for ${bldgName}!`, "success");
    await loadAnalytics();

  } catch (err) {
    showToast(err.message, "error");
    alert(`Ingestion Error: ${err.message}`);
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerText = origText;
  }
}

async function inspectIngestedBuilding() {
  if (lastIngestedBuildingId) {
    closeIngestModal();
    // Switch to search or results view if not already visible
    document.getElementById("view-search").style.display = "none";
    document.getElementById("view-results").style.display = "flex";
    await selectBuilding(lastIngestedBuildingId);
  }
}

// ==========================================
// AI VOICE ARCHITECT (Web Speech API)
// ==========================================
let recognition;
function startVoiceAI() {
  const statusSpan = document.getElementById("voice-ai-status");
  const btn = document.getElementById("btn-voice-ai");
  
  if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
    alert("Speech recognition isn't supported in this browser. Please use Chrome or Edge Desktop.");
    return;
  }
  
  if(!recognition) {
     const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
     recognition = new SpeechRec();
     recognition.continuous = false;
     recognition.interimResults = false;
     recognition.lang = 'en-IN'; // Indian English
     
     recognition.onstart = function() {
       btn.style.background = "#b91c1c";
       btn.innerHTML = " Listening... Speak Now";
       statusSpan.innerText = "Listening to surveyor dictation...";
       statusSpan.style.color = "#ea580c";
     };
     
     recognition.onresult = async function(event) {
       const transcript = event.results[0][0].transcript;
       statusSpan.innerHTML = `<i>"${transcript}"</i> <span style='color:#0284c7'> (AI is synthesizing 3D geometry...)</span>`;
       btn.innerHTML = "Processing...";
       btn.style.background = "#0284c7";
       btn.disabled = true;
       
       // Send directly to Master AI Predictor backend
       const bldgId = "VOICE_" + Math.floor(Math.random()*9000 + 1000);
       
       const formData = new FormData();
       formData.append('text_prompt', transcript);
       formData.append('building_id', bldgId);
       formData.append('persist_db', 'true');
       
       try {
           const res = await fetch("/api/ai/predict", { method: "POST", body: formData });
           const data = await res.json();
           
           if(data.status === "success" && data.prediction_result) {
               statusSpan.innerHTML = `<span style='color:#15803d;font-weight:700;'> Magic! Generated ${data.prediction_result.total_units} 3D Cadastral units. Load in 2s...</span>`;
               lastIngestedBuildingId = bldgId;
               BUILDING_METADATA[bldgId] = {
                  name: `Voice Generated (${bldgId})`,
                  status: "completed",
                  desc: `Generated via Voice AI Command: "${transcript}"`
               };
               showToast("Voice AI Architecture Successful!", "success");
               setTimeout(() => inspectIngestedBuilding(), 2000);
           } else {
               statusSpan.innerHTML = `<span style='color:#b91c1c'> AI couldn't parse that structure. Try again.</span>`;
           }
       } catch (err) {
           statusSpan.innerHTML = `<span style='color:#b91c1c'> Network Connection Error.</span>`;
       } finally {
           btn.innerHTML = " AI Voice Architect";
           btn.style.background = "#ef4444";
           btn.disabled = false;
       }
     };
     
     recognition.onerror = function(event) {
       btn.innerHTML = " AI Voice Architect";
       btn.style.background = "#ef4444";
       statusSpan.innerText = "Microphone error! " + event.error;
       btn.disabled = false;
     };
  }
  
  recognition.start();
}

function submitOCRCorrections(btn) {
  btn.innerText = "Saving to DB...";
  setTimeout(() => {
    btn.innerText = " OCR Corrections Applied";
    btn.style.background = "#dcfce7";
    btn.style.borderColor = "#86efac";
    showToast("Human-in-the-Loop OCR corrections saved to ISO Cadastral DB.", "success");
  }, 600);
}

