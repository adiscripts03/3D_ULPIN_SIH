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

document.addEventListener("DOMContentLoaded", () => {
  setupEventListeners();
});

function setupEventListeners() {
  document.getElementById("floor-filter").addEventListener("change", () => {
    filter3DView();
  });

  document.getElementById("type-filter").addEventListener("change", () => {
    filter3DView();
  });

  // Action Buttons
  document.getElementById("btn-open-actions").addEventListener("click", () => {
    openModal();
  });

  document.getElementById("btn-close-modal").addEventListener("click", () => {
    closeModal();
  });

  document.getElementById("btn-run-topology").addEventListener("click", () => {
    runTopologyAudit();
  });
}

// Step 1 -> Step 2: Execute Mahabhulekh Search
async function executeSearch() {
  const district = document.getElementById("sel-district").value;
  const taluka = document.getElementById("sel-taluka").value;
  const village = document.getElementById("sel-village").value;
  const surveyNo = document.getElementById("inp-survey-no").value.trim();

  if (!surveyNo) {
    showToast("Please enter a valid Survey / Gat Number", "error");
    return;
  }

  // Switch Views
  document.getElementById("view-search").style.display = "none";
  const resultsView = document.getElementById("view-results");
  resultsView.style.display = "flex";

  showToast("Resolved Land Record: Survey 140/1, Waranga (pu-id: 33550994106)", "success");

  // Load analytics & active building
  await loadAnalytics();
  await selectBuilding("HSTL01");
}

// Step 2 -> Step 1: Return to Search View
function backToSearch() {
  document.getElementById("view-results").style.display = "none";
  document.getElementById("view-search").style.display = "flex";
}

// Select Building from the 4 Cards
async function selectBuilding(buildingId) {
  currentBuildingId = buildingId;

  // Update active state on 4 cards
  document.querySelectorAll(".building-card").forEach(c => c.classList.remove("active"));
  const activeCard = document.getElementById(`bldg-card-${buildingId}`);
  if (activeCard) activeCard.classList.add("active");

  const meta = BUILDING_METADATA[buildingId] || { name: buildingId, status: "not_yet_surveyed" };
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
  container.innerHTML = `
    <div class="pending-notice-box">
      <div style="font-size:2.2rem;margin-bottom:12px;color:#b45309;">🏛️</div>
      <div class="pending-notice-title">${meta.name} (${buildingId})</div>
      <div class="pending-notice-desc">
        ${meta.desc}
        <br><br>
        <strong>Cadastral Model:</strong> 3D digital twin model is currently loaded for Hostel Block A.
      </div>
      <button class="btn btn-primary" onclick="selectBuilding('HSTL01')">
        ← View Hostel Block A (700 3D Units)
      </button>
    </div>
  `;

  // Update Inspector
  document.getElementById("insp-ulpin").innerText = `N/A (${buildingId})`;
  document.getElementById("insp-type").innerText = "Institutional Building";
  document.getElementById("insp-floor").innerText = "Ground Level";
  document.getElementById("insp-area").innerText = "0.00 m²";
  document.getElementById("insp-volume").innerText = "0.00 m³";
  document.getElementById("insp-uds").innerText = "0.00000%";
  document.getElementById("insp-gps").innerText = "20.949556, 79.029472 (Campus Anchor)";
  document.getElementById("insp-occupants-list").innerHTML = `<span style="color:#8c857b;font-size:0.75rem;">Institutional Estate</span>`;
  document.getElementById("insp-liens-list").innerHTML = `<span style="color:#8c857b;font-size:0.75rem;">Clear Title</span>`;
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
                    `<b>Master Parcel:</b> pu-id 33550994106 (Surv 140/1)<br>` +
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

  // Hook Click Event
  document.getElementById("plot3d-container").on("plotly_click", (data) => {
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

    showToast(data.message.replace(/[✅❌⚠️👤🏦]/g, "").trim(), "success");
    closeModal();
    await loadBuilding3DTwin(currentBuildingId);
    await loadAnalytics();
    inspectParcel(ulpin);
  } catch (err) {
    showToast(err.message.replace(/[✅❌⚠️👤🏦]/g, "").trim(), "error");
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

    showToast(data.message.replace(/[✅❌⚠️👤🏦]/g, "").trim(), "success");
    closeModal();
    await loadBuilding3DTwin(currentBuildingId);
    inspectParcel(ulpin);
  } catch (err) {
    showToast(err.message.replace(/[✅❌⚠️👤🏦]/g, "").trim(), "error");
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

    showToast(data.message.replace(/[✅❌⚠️👤🏦]/g, "").trim(), "success");
    closeModal();
    await loadBuilding3DTwin(currentBuildingId);
    await loadAnalytics();
    inspectParcel(ulpin);
  } catch (err) {
    showToast(err.message.replace(/[✅❌⚠️👤🏦]/g, "").trim(), "error");
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
    showToast(err.message.replace(/[✅❌⚠️👤🏦]/g, "").trim(), "error");
  }
}

function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerText = message;
  container.appendChild(toast);
  setTimeout(() => { toast.remove(); }, 3500);
}
