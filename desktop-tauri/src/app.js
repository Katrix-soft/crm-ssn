// App State Configuration
let apiBaseUrl = localStorage.getItem("katrix_api_base") || "https://api.katrix.com.ar";
let selectedImportFile = null;
let accessToken = localStorage.getItem("katrix_access_token") || "";
let currentUser = null;
let currentSearchPage = 1;
let totalSearchPages = 1;
const searchPageSize = 25;
let systemConfigs = {};
let savedLicenseKey = localStorage.getItem("katrix_license_key") || "";
let licenseData = null; // holds the last validated license response

// Charts instances
let chartRamosInstance = null;
let chartProductoresInstance = null;

// Initialize App
document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  setupEventListeners();
  checkAuth();
});

// Theme Management
function initTheme() {
  const savedTheme = localStorage.getItem("katrix_theme") || "dark";
  document.documentElement.setAttribute("data-theme", savedTheme);
}

function toggleTheme() {
  const currentTheme = document.documentElement.getAttribute("data-theme");
  const newTheme = currentTheme === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", newTheme);
  localStorage.setItem("katrix_theme", newTheme);
}

// Auth Management
async function checkAuth() {
  document.getElementById("apiBase").value = apiBaseUrl;

  // Step 1: Validate license first
  const licenseOk = await checkLicense();
  if (!licenseOk) {
    showLicenseScreen();
    return;
  }

  // Step 2: Check user session
  if (!accessToken) {
    showLoginScreen();
    return;
  }
  
  try {
    const profile = await apiFetch("/auth/me");
    if (profile) {
      currentUser = profile;
      showAppContainer();
      updateProfileUI();
      await loadSystemConfigs();
      loadDashboardData();
    } else {
      logout();
    }
  } catch (error) {
    console.error("Auth validation failed", error);
    const cachedUser = localStorage.getItem("katrix_cached_user");
    if (cachedUser) {
      currentUser = JSON.parse(cachedUser);
      showAppContainer();
      updateProfileUI();
      showToast("Conexión perdida. Iniciando en modo sin conexión.");
      document.getElementById("offlineBar").style.display = "block";
    } else {
      showLoginScreen();
    }
  }
}

// ─── LICENSE FUNCTIONS ────────────────────────────────────────────────────────

function getDeviceId() {
  let id = localStorage.getItem("katrix_device_id");
  if (!id) {
    id = "KTX-" + Math.random().toString(36).substr(2, 8).toUpperCase() + "-" + Date.now();
    localStorage.setItem("katrix_device_id", id);
  }
  return id;
}

function getDeviceName() {
  return JSON.stringify({
    sistema_operativo: navigator.platform || "Desktop",
    usuario: navigator.userAgent.includes("Windows") ? "Win" : "Linux",
    hostname: "katrix-client",
    procesador: navigator.hardwareConcurrency + " cores",
    arquitectura: "x64"
  });
}

async function checkLicense() {
  if (!savedLicenseKey) return false;
  try {
    const res = await fetch(`${apiBaseUrl.replace(/\/$/, "")}/licencias/validar`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        clave: savedLicenseKey,
        dispositivo_id: getDeviceId(),
        email_cliente: "",
        dispositivo_nombre: getDeviceName()
      })
    });
    if (!res.ok) return false;
    const data = await res.json();
    if (data.valid) {
      licenseData = data;
      return true;
    }
    // Invalid license — clear it
    showToast(`Licencia inválida: ${data.message}`, "danger");
    localStorage.removeItem("katrix_license_key");
    savedLicenseKey = "";
    licenseData = null;
    return false;
  } catch (e) {
    // Network error — if key exists, allow offline (don't block)
    console.warn("License check failed (offline?)", e);
    return !!savedLicenseKey; // trust cached key offline
  }
}

async function activateLicense() {
  const input = document.getElementById("licenseActivateInput");
  const errBox = document.getElementById("licenseActivateError");
  const key = (input.value || "").trim().toUpperCase();
  
  errBox.style.display = "none";
  
  if (!key) {
    errBox.textContent = "Ingresá una clave de licencia.";
    errBox.style.display = "block";
    return;
  }
  
  try {
    const res = await fetch(`${apiBaseUrl.replace(/\/$/, "")}/licencias/validar`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        clave: key,
        dispositivo_id: getDeviceId(),
        email_cliente: "",
        dispositivo_nombre: getDeviceName()
      })
    });
    const data = await res.json();
    if (data.valid) {
      licenseData = data;
      savedLicenseKey = key;
      localStorage.setItem("katrix_license_key", key);
      document.getElementById("licenseScreen").style.display = "none";
      showToast(`¡Licencia activada! Bienvenido, ${data.cliente}.`);
      showLoginScreen();
    } else {
      errBox.textContent = data.message || "Clave de licencia inválida.";
      errBox.style.display = "block";
    }
  } catch (e) {
    errBox.textContent = "No se pudo conectar al servidor. Verificá tu conexión.";
    errBox.style.display = "block";
  }
}

async function loadLicenseData() {
  // Try re-validating to get fresh data
  if (savedLicenseKey) {
    try {
      const res = await fetch(`${apiBaseUrl.replace(/\/$/, "")}/licencias/validar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          clave: savedLicenseKey,
          dispositivo_id: getDeviceId(),
          email_cliente: "",
          dispositivo_nombre: getDeviceName()
        })
      });
      if (res.ok) licenseData = await res.json();
    } catch (e) { /* use cached */ }
  }

  const data = licenseData;
  const keyEl = document.getElementById("licenseKeyInput");
  const clientEl = document.getElementById("licenseClientInput");
  const expEl = document.getElementById("licenseExpirationInput");
  const limitEl = document.getElementById("licenseLimitInput");
  const statusEl = document.getElementById("licenseStatusBadge");
  const btnCheck = document.getElementById("btnForceLicenseCheck");

  if (keyEl) keyEl.value = savedLicenseKey || "No activada";
  if (clientEl) clientEl.value = data ? data.cliente : "-";
  if (limitEl) limitEl.value = data ? `${data.limite_dispositivos || "?"} Equipos` : "-";

  if (expEl && data) {
    try {
      const d = new Date(data.fecha_expiracion + "T00:00:00");
      expEl.value = d.toLocaleDateString("es-AR", { day: "numeric", month: "long", year: "numeric" });
    } catch { expEl.value = data.fecha_expiracion; }
  } else if (expEl) expEl.value = "-";

  if (statusEl) {
    statusEl.innerHTML = data && data.valid
      ? `<span class="badge badge-success">Activa</span>`
      : `<span class="badge badge-danger">No válida</span>`;
  }

  if (btnCheck) {
    btnCheck.onclick = async () => {
      btnCheck.disabled = true;
      btnCheck.textContent = "Verificando...";
      await loadLicenseData();
      btnCheck.disabled = false;
      btnCheck.textContent = "Refrescar Licencia Online";
      showToast("Estado de licencia actualizado.");
    };
  }
}

function showLicenseScreen() {
  document.getElementById("licenseScreen").style.display = "flex";
  document.getElementById("loginScreen").style.display = "none";
  document.getElementById("appContainer").style.display = "none";
}

function showLoginScreen() {
  document.getElementById("loginScreen").style.display = "flex";
  document.getElementById("appContainer").style.display = "none";
}

function showAppContainer() {
  document.getElementById("loginScreen").style.display = "none";
  document.getElementById("appContainer").style.display = "flex";
}

function updateProfileUI() {
  if (!currentUser) return;
  document.getElementById("userNameSummary").textContent = currentUser.username || currentUser.usuario || "Usuario";
  document.getElementById("userRoleSummary").textContent = currentUser.role || "Agente";
  document.getElementById("userAvatar").textContent = (currentUser.username || "U")[0].toUpperCase();
  
  // Show admin items if role is admin
  const isAdmin = currentUser.role === "admin" || currentUser.role === "superadmin";
  const adminNavItem = document.querySelector('[data-view="viewAdmin"]');
  if (adminNavItem) {
    adminNavItem.style.display = isAdmin ? "block" : "none";
  }
  const configNavItem = document.querySelector('[data-view="viewConfig"]');
  if (configNavItem) {
    configNavItem.style.display = isAdmin ? "block" : "none";
  }
}

function logout() {
  accessToken = "";
  currentUser = null;
  localStorage.removeItem("katrix_access_token");
  localStorage.removeItem("katrix_cached_user");
  showLoginScreen();
}

// API Wrapper
async function apiFetch(endpoint, options = {}) {
  const url = `${apiBaseUrl.replace(/\/$/, "")}${endpoint}`;
  
  const headers = {
    "Content-Type": "application/json",
    ...options.headers
  };
  
  if (accessToken) {
    headers["Authorization"] = `Bearer ${accessToken}`;
  }
  
  const config = {
    ...options,
    headers
  };
  
  try {
    const response = await fetch(url, config);
    
    if (response.status === 401) {
      // Unauthenticated, trigger logout
      logout();
      throw new Error("Sesión expirada");
    }
    
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `Error del servidor (${response.status})`);
    }
    
    // Return empty json if no content
    if (response.status === 204) return null;
    
    return await response.json();
  } catch (error) {
    console.error(`API Fetch Error: ${endpoint}`, error);
    throw error;
  }
}

// Load Dashboard Data
function loadDashboardData() {
  loadSearchResults();
  loadCarteraData();
  loadMetricsData();
  loadVisitasData();
  loadAdminUsers();
  loadLicenseData();
}

// Navigation Router
function setupEventListeners() {
  // Navigation tabs click handler
  const navItems = document.querySelectorAll(".nav-item");
  navItems.forEach(item => {
    item.addEventListener("click", (e) => {
      e.preventDefault();
      
      const targetView = item.getAttribute("data-view");
      
      // Feature flag check
      if (targetView === "viewCartera" && systemConfigs.permitir_cartera_polizas === "false") {
        showToast("El módulo de Cartera está deshabilitado por el administrador.", "warning");
        return;
      }
      if (targetView === "viewMetrics" && systemConfigs.permitir_metricas_kpi === "false") {
        showToast("El módulo de Métricas está deshabilitado por el administrador.", "warning");
        return;
      }
      if (targetView === "viewCommercial" && systemConfigs.permitir_plan_comercial === "false") {
        showToast("El módulo de Plan Comercial está deshabilitado por el administrador.", "warning");
        return;
      }
      
      // Update active state in sidebar
      navItems.forEach(nav => nav.classList.remove("active"));
      item.classList.add("active");
      
      // Toggle view pages
      const views = document.querySelectorAll(".page-view");
      views.forEach(view => view.classList.remove("active"));
      document.getElementById(targetView).classList.add("active");
      
      // Trigger load data specific to view if needed
      if (targetView === "viewSearch") loadSearchResults();
      if (targetView === "viewCartera") loadCarteraData();
      if (targetView === "viewMetrics") loadMetricsData();
      if (targetView === "viewCommercial") loadVisitasData();
      if (targetView === "viewAdmin") loadAdminUsers();
      if (targetView === "viewConfig") loadConfigView();
      if (targetView === "viewLicense") loadLicenseData();
    });
  });

  // Config toggles change handlers
  const configKeys = [
    "permitir_busqueda_ssn",
    "permitir_importacion_excel",
    "permitir_vaciar_db",
    "permitir_cartera_polizas",
    "permitir_metricas_kpi",
    "permitir_plan_comercial"
  ];
  
  configKeys.forEach(key => {
    const input = document.getElementById(`cfg_${key}`);
    if (input) {
      input.addEventListener("change", async (e) => {
        const newValue = e.target.checked ? "true" : "false";
        try {
          const res = await apiFetch("/configuracion", {
            method: "POST",
            body: JSON.stringify({
              clave: key,
              valor: newValue
            })
          });
          if (res && res.ok) {
            systemConfigs[key] = newValue;
            applyFeatureVisibility();
            showToast(`Configuración de '${key.replace('permitir_', '').replace(/_/g, ' ').toUpperCase()}' actualizada.`);
          } else {
            showToast("No se pudo guardar la configuración", "danger");
            e.target.checked = !e.target.checked;
          }
        } catch (err) {
          showToast("Error al actualizar configuración: " + err.message, "danger");
          e.target.checked = !e.target.checked;
        }
      });
    }
  });

  // Login click handler
  document.getElementById("btnLogin").addEventListener("click", handleLogin);
  document.getElementById("loginPass").addEventListener("keypress", (e) => {
    if (e.key === "Enter") handleLogin();
  });

  // License activation handler
  const btnActivate = document.getElementById("btnActivateLicense");
  if (btnActivate) {
    btnActivate.addEventListener("click", activateLicense);
  }
  const licInput = document.getElementById("licenseActivateInput");
  if (licInput) {
    licInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") activateLicense();
    });
  }


  // Logout handler
  document.getElementById("btnLogout").addEventListener("click", logout);

  // Theme toggle
  document.getElementById("btnThemeToggle").addEventListener("click", toggleTheme);

  // Search actions
  document.getElementById("btnSearch").addEventListener("click", () => {
    currentSearchPage = 1;
    loadSearchResults();
  });
  document.getElementById("searchQuery").addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      currentSearchPage = 1;
      loadSearchResults();
    }
  });

  document.getElementById("btnPrevPage").addEventListener("click", () => {
    if (currentSearchPage > 1) {
      currentSearchPage--;
      loadSearchResults();
    }
  });
  document.getElementById("btnNextPage").addEventListener("click", () => {
    if (currentSearchPage < totalSearchPages) {
      currentSearchPage++;
      loadSearchResults();
    }
  });

  // Live SSN query trigger
  document.getElementById("btnTriggerSSNSearch").addEventListener("click", triggerSSNSearchPrompt);

  // Modal details save handler
  document.getElementById("btnSaveProducerChanges").addEventListener("click", saveProducerChanges);

  // Visitas programming
  document.getElementById("btnNewVisita").addEventListener("click", () => openModal("modalVisitaForm"));
  document.getElementById("btnSaveVisita").addEventListener("click", saveVisitaForm);

  // Admin User Creation
  document.getElementById("btnCreateUser").addEventListener("click", () => openModal("modalUserForm"));
  document.getElementById("btnSaveSystemUser").addEventListener("click", saveSystemUser);

  // Excel/CSV import handler
  const importInput = document.getElementById("btnImportExcel");
  if (importInput) {
    importInput.addEventListener("change", (e) => {
      selectedImportFile = e.target.files[0];
      const fileNameSpan = document.getElementById("importFileName");
      const startBtn = document.getElementById("btnStartImport");
      
      if (selectedImportFile) {
        fileNameSpan.textContent = `Archivo: ${selectedImportFile.name}`;
        fileNameSpan.style.color = "var(--text-color)";
        if (startBtn) startBtn.style.display = "flex";
      } else {
        fileNameSpan.textContent = "Ningún archivo seleccionado (.xlsx, .xlsm, .csv)";
        fileNameSpan.style.color = "var(--text-muted)";
        if (startBtn) startBtn.style.display = "none";
      }
    });
  }

  const startImportBtn = document.getElementById("btnStartImport");
  if (startImportBtn) {
    startImportBtn.addEventListener("click", executeImport);
  }

  // Setup Drag and Drop events on importDropZone
  const dropZone = document.getElementById("importDropZone");
  if (dropZone) {
    dropZone.addEventListener("mouseenter", () => {
      dropZone.style.borderColor = "var(--accent-color)";
      dropZone.style.background = "var(--surface-hover-more, rgba(255, 255, 255, 0.05))";
    });
    dropZone.addEventListener("mouseleave", () => {
      dropZone.style.borderColor = "var(--border-color)";
      dropZone.style.background = "var(--surface-hover)";
    });
    dropZone.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropZone.style.borderColor = "var(--accent-color)";
      dropZone.style.background = "rgba(255, 255, 255, 0.05)";
    });
    dropZone.addEventListener("dragleave", () => {
      dropZone.style.borderColor = "var(--border-color)";
      dropZone.style.background = "var(--surface-hover)";
    });
    dropZone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropZone.style.borderColor = "var(--border-color)";
      dropZone.style.background = "var(--surface-hover)";
      
      const files = e.dataTransfer.files;
      if (files.length > 0) {
        importInput.files = files;
        const event = new Event('change');
        importInput.dispatchEvent(event);
      }
    });
  }

  // DB commands
  document.getElementById("btnCleanDb").addEventListener("click", handleCleanDb);
  document.getElementById("btnForceLicenseCheck").addEventListener("click", loadLicenseData);
}

// Login Handler
async function handleLogin() {
  const usernameInput = document.getElementById("loginUser").value.trim();
  const passwordInput = document.getElementById("loginPass").value;
  const errorDiv = document.getElementById("loginError");
  apiBaseUrl = document.getElementById("apiBase").value.trim();
  
  localStorage.setItem("katrix_api_base", apiBaseUrl);
  
  if (!usernameInput || !passwordInput) {
    errorDiv.textContent = "Ingrese usuario y contraseña";
    errorDiv.style.display = "block";
    return;
  }
  
  errorDiv.style.display = "none";
  document.getElementById("btnLogin").textContent = "Ingresando...";
  document.getElementById("btnLogin").disabled = true;
  
  try {
    const data = await apiFetch("/auth/login", {
      method: "POST",
      body: JSON.stringify({
        username: usernameInput,
        password: passwordInput
      })
    });
    
    if (data && data.access_token) {
      accessToken = data.access_token;
      localStorage.setItem("katrix_access_token", accessToken);
      
      // Fetch me to configure user
      const profile = await apiFetch("/auth/me");
      currentUser = profile;
      localStorage.setItem("katrix_cached_user", JSON.stringify(currentUser));
      
      showAppContainer();
      updateProfileUI();
      await loadSystemConfigs();
      loadDashboardData();
      showToast(`¡Bienvenido, ${currentUser.username}!`);
    }
  } catch (error) {
    errorDiv.textContent = error.message || "Error al iniciar sesión";
    errorDiv.style.display = "block";
  } finally {
    document.getElementById("btnLogin").textContent = "Iniciar Sesión";
    document.getElementById("btnLogin").disabled = false;
  }
}

// Load Search results
async function loadSearchResults() {
  const query = document.getElementById("searchQuery").value.trim();
  const provincia = document.getElementById("searchProvincia").value;
  const estado = document.getElementById("searchEstado").value;
  
  let endpoint = `/pas/?page=${currentSearchPage}&page_size=${searchPageSize}`;
  if (query) endpoint += `&q=${encodeURIComponent(query)}`;
  if (provincia) endpoint += `&provincia=${encodeURIComponent(provincia)}`;
  if (estado) endpoint += `&estado_contacto=${encodeURIComponent(estado)}`;
  
  const tbody = document.getElementById("searchTableBody");
  tbody.innerHTML = `
    <tr>
      <td colspan="6">
        <div class="skeleton-row"></div>
        <div class="skeleton-row" style="animation-delay: 0.2s"></div>
        <div class="skeleton-row" style="animation-delay: 0.4s"></div>
      </td>
    </tr>
  `;
  
  try {
    const data = await apiFetch(endpoint);
    tbody.innerHTML = "";
    
    // Check if there is an exact match in returned items
    const cleaned = query ? query.replace(/\D/g, "") : "";
    let hasExactMatch = false;
    if (cleaned && data && data.items && data.items.length > 0) {
      hasExactMatch = data.items.some(pas => {
        const m = String(pas.matricula || "").replace(/\D/g, "");
        const d = String(pas.documento || "").replace(/\D/g, "");
        const c = String(pas.cuit || "").replace(/\D/g, "");
        return m === cleaned || d === cleaned || c === cleaned;
      });
    }

    if (!data || !data.items || data.items.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center" style="padding: 30px; color: var(--text-muted);">No se encontraron productores asesores.</td></tr>`;
      document.getElementById("searchPaginationInfo").textContent = "Página 1 de 1";
      document.getElementById("btnPrevPage").disabled = true;
      document.getElementById("btnNextPage").disabled = true;
      
      // Auto-trigger SSN query if query is numeric, no exact match, and user confirms
      if (query && !hasExactMatch) {
        if (cleaned.length >= 4 && cleaned.length <= 11) {
          let docType = "DNI";
          if (cleaned.length === 11) {
            docType = "CUIT";
          } else if (cleaned.length >= 4 && cleaned.length <= 6) {
            docType = "MATRICULA";
          }
          
          setTimeout(() => {
            const confirmSearch = confirm(`No se encontró el productor con matrícula o documento "${query}" en la base de datos local.\n\n¿Desea consultar e importar en tiempo real desde la SSN usando ${docType} "${cleaned}"?`);
            if (confirmSearch) {
              triggerSSNSearchWithParam(cleaned, docType);
            }
          }, 200);
        }
      }
      return;
    }
    
    data.items.forEach(pas => {
      const tr = document.createElement("tr");
      
      // State badge logic
      let badgeClass = "badge-info";
      if (pas.estado_contacto === "Activo") badgeClass = "badge-success";
      if (pas.estado_contacto === "Suspendido") badgeClass = "badge-danger";
      if (pas.estado_contacto === "Sin Contactar") badgeClass = "badge-warning";
      
      tr.innerHTML = `
        <td><strong>${pas.matricula}</strong></td>
        <td>${pas.nombre}</td>
        <td>${pas.provincia || "—"}</td>
        <td>${pas.localidad || "—"}</td>
        <td><span class="badge ${badgeClass}">${pas.estado_contacto || "Sin Contactar"}</span></td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="viewProducerDetail('${pas.matricula}')">📁 Ver Ficha</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
    
    // Pagination math
    totalSearchPages = Math.ceil(data.total / searchPageSize) || 1;
    document.getElementById("searchPaginationInfo").textContent = `Página ${currentSearchPage} de ${totalSearchPages} (Total: ${data.total})`;
    
    document.getElementById("btnPrevPage").disabled = currentSearchPage <= 1;
    document.getElementById("btnNextPage").disabled = currentSearchPage >= totalSearchPages;

    // Prompt to search on SSN if list has items but none of them matches exactly the search term
    if (query && !hasExactMatch) {
      if (cleaned.length >= 4 && cleaned.length <= 11) {
        let docType = "DNI";
        if (cleaned.length === 11) {
          docType = "CUIT";
        } else if (cleaned.length >= 4 && cleaned.length <= 6) {
          docType = "MATRICULA";
        }
        
        setTimeout(() => {
          const confirmSearch = confirm(`No se encontró un productor con matrícula o documento exacto "${query}" en la base de datos local.\n\n¿Desea consultar e importar en tiempo real desde la SSN usando ${docType} "${cleaned}"?`);
          if (confirmSearch) {
            triggerSSNSearchWithParam(cleaned, docType);
          }
        }, 200);
      }
    }
    
  } catch (error) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-center" style="padding: 30px; color: var(--danger-color);">Error al cargar resultados: ${error.message}</td></tr>`;
  }
}

// Live SSN query trigger
function triggerSSNSearchPrompt() {
  const query = prompt("Ingrese CUIT, DNI o Matrícula del Productor para consultar la SSN en tiempo real:");
  if (!query) return;
  
  // Clean inputs
  const cleaned = query.replace(/\D/g, "");
  if (cleaned.length < 4 || cleaned.length > 11) {
    alert("Número de documento, CUIT o Matrícula inválido. Debe tener entre 4 y 11 dígitos.");
    return;
  }
  
  let docType = "DNI";
  if (cleaned.length === 11) {
    docType = "CUIT";
  } else if (cleaned.length >= 4 && cleaned.length <= 6) {
    docType = "MATRICULA";
  }
  
  triggerSSNSearchWithParam(cleaned, docType);
}

function triggerSSNSearchWithParam(cleaned, docType) {
  showToast("Iniciando scraping y resolución automatizada de captcha...");
  
  // Show spinner page loader
  const tbody = document.getElementById("searchTableBody");
  tbody.innerHTML = `
    <tr>
      <td colspan="6" class="text-center" style="padding: 40px 20px;">
        <div style="font-size:24px; margin-bottom:12px;">🤖</div>
        <div class="skeleton-row" style="max-width:300px; margin:0 auto 12px auto;"></div>
        <p style="font-size:13px; color:var(--text-muted)">Consultando sitio oficial de la Superintendencia de Seguros de la Nación. Resolviendo captcha automatizado con Capsolver...</p>
      </td>
    </tr>
  `;
  
  apiFetch(`/pas/buscar-ssn/${cleaned}?tipo_doc=${docType}`)
    .then(result => {
      const dataObj = result.data || result;
      if (!dataObj || !dataObj.matricula) {
        showToast("No se encontró el productor en el padrón de la SSN.", "warning");
        loadSearchResults();
        return;
      }
      showToast("¡Productor importado y guardado exitosamente!");
      // Populate results search box
      document.getElementById("searchQuery").value = dataObj.matricula;
      currentSearchPage = 1;
      loadSearchResults();
      
      // Auto open detail
      viewProducerDetail(dataObj.matricula);
    })
    .catch(error => {
      showToast(`Scraping fallido: ${error.message}`, "danger");
      loadSearchResults();
    });
}

// View Producer Details Modal
async function viewProducerDetail(matricula) {
  try {
    const pas = await apiFetch(`/pas/${matricula}`);
    if (!pas) return;
    
    document.getElementById("detailProducerName").textContent = pas.nombre || "Ficha del Productor";
    document.getElementById("detailMatricula").value = pas.matricula || "";
    document.getElementById("detailDocumento").value = pas.documento || pas.cuit || "—";
    document.getElementById("detailProvincia").value = pas.provincia || "—";
    document.getElementById("detailLocalidad").value = pas.localidad || "—";
    document.getElementById("detailCompanias").value = pas.companias || "";
    document.getElementById("detailEstadoGestion").value = pas.estado_contacto || "Sin Contactar";
    document.getElementById("detailObservaciones").value = pas.observaciones || "";
    
    // Expanded fields
    document.getElementById("detailRamo").value = pas.ramo || "—";
    document.getElementById("detailDomicilio").value = pas.domicilio || "—";
    document.getElementById("detailCodPostal").value = pas.cod_postal || "—";
    document.getElementById("detailTelefono").value = pas.telefono || "—";
    document.getElementById("detailEmail").value = pas.email || "—";
    document.getElementById("detailResolucion").value = pas.resolucion || "—";
    document.getElementById("detailFechaResolucion").value = pas.fecha_resolucion || "—";
    
    // Quick Actions
    const btnCall = document.getElementById("btnActionCall");
    const btnWa = document.getElementById("btnActionWhatsapp");
    if (pas.telefono) {
      btnCall.style.display = "flex";
      btnCall.onclick = () => window.open(`tel:${pas.telefono.replace(/\s+/g, '')}`, '_self');
      
      btnWa.style.display = "flex";
      let cleanedPhone = pas.telefono.replace(/\D/g, '');
      if (cleanedPhone.startsWith("0")) cleanedPhone = cleanedPhone.substring(1);
      if (!cleanedPhone.startsWith("54")) cleanedPhone = "549" + cleanedPhone;
      btnWa.onclick = () => window.open(`https://wa.me/${cleanedPhone}`, '_blank');
    } else {
      btnCall.style.display = "none";
      btnWa.style.display = "none";
    }
    
    const btnEmail = document.getElementById("btnActionEmail");
    if (pas.email) {
      btnEmail.style.display = "flex";
      btnEmail.onclick = () => window.open(`https://mail.google.com/mail/?view=cm&fs=1&to=${encodeURIComponent(pas.email)}`, '_blank');
    } else {
      btnEmail.style.display = "none";
    }
    
    // Live Scraper button setup
    const docToScrape = pas.cuit || pas.documento;
    const scrapeBtn = document.getElementById("btnScrapePASDetail");
    if (docToScrape) {
      const cleanedDoc = docToScrape.replace(/\D/g, "");
      if (cleanedDoc.length >= 7 && cleanedDoc.length <= 11) {
        scrapeBtn.style.display = "flex";
        scrapeBtn.onclick = () => runLiveScrapeForPAS(cleanedDoc, cleanedDoc.length === 11 ? "CUIT" : "DNI", pas.matricula);
      } else {
        scrapeBtn.style.display = "none";
      }
    } else {
      scrapeBtn.style.display = "none";
    }
    
    openModal("modalProducerDetail");
  } catch (error) {
    showToast(`Error al obtener detalles: ${error.message}`, "danger");
  }
}

async function runLiveScrapeForPAS(docNumber, docType, currentMatricula) {
  const scrapeBtn = document.getElementById("btnScrapePASDetail");
  const originalText = scrapeBtn.innerHTML;
  scrapeBtn.disabled = true;
  scrapeBtn.innerHTML = `<span>⏳ Buscando...</span>`;
  
  showToast("Consultando SSN en tiempo real. Resolviendo captcha...");
  
  try {
    const result = await apiFetch(`/pas/buscar-ssn/${docNumber}?tipo_doc=${docType}`);
    showToast("¡Ficha de productor actualizada desde la SSN exitosamente!");
    
    // Reload search results in background
    loadSearchResults();
    
    // Refresh modal fields with the updated data
    const newMatricula = result.matricula || currentMatricula;
    await viewProducerDetail(newMatricula);
  } catch (error) {
    showToast(`Fallo al actualizar desde SSN: ${error.message}`, "danger");
  } finally {
    scrapeBtn.disabled = false;
    scrapeBtn.innerHTML = originalText;
  }
}

// Save Producer Changes
async function saveProducerChanges() {
  const matricula = document.getElementById("detailMatricula").value;
  const companias = document.getElementById("detailCompanias").value.trim();
  const estado = document.getElementById("detailEstadoGestion").value;
  const observaciones = document.getElementById("detailObservaciones").value.trim();
  
  try {
    // Save status
    await apiFetch(`/pas/${matricula}/estado`, {
      method: "PUT",
      body: JSON.stringify({ estado_contacto: estado })
    });
    
    // Save observations
    await apiFetch(`/pas/${matricula}/observaciones`, {
      method: "PUT",
      body: JSON.stringify({ observaciones: observaciones })
    });
    
    // Save companias
    await apiFetch(`/pas/${matricula}/companias`, {
      method: "PUT",
      body: JSON.stringify({ companias: companias })
    });
    
    closeModal("modalProducerDetail");
    showToast("Ficha de productor actualizada correctamente");
    loadSearchResults();
  } catch (error) {
    showToast(`Error al guardar cambios: ${error.message}`, "danger");
  }
}

// Cartera and Policies
async function loadCarteraData() {
  try {
    const polizas = await apiFetch("/polizas/");
    const clientes = await apiFetch("/clientes/");
    const siniestros = await apiFetch("/siniestros/");
    
    document.getElementById("statCarteraClientes").textContent = clientes ? clientes.length : 0;
    document.getElementById("statCarteraPolizas").textContent = polizas ? polizas.length : 0;
    document.getElementById("statCarteraSiniestros").textContent = siniestros ? siniestros.length : 0;
    
    const tbody = document.getElementById("carteraTableBody");
    tbody.innerHTML = "";
    
    if (!polizas || polizas.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center" style="padding: 20px; color: var(--text-muted);">No hay pólizas registradas.</td></tr>`;
      return;
    }
    
    polizas.slice(0, 8).forEach(p => {
      const tr = document.createElement("tr");
      
      let badgeClass = "badge-success";
      if (p.estado === "Vencida") badgeClass = "badge-danger";
      if (p.estado === "Anulada") badgeClass = "badge-danger";
      if (p.estado === "Pendiente") badgeClass = "badge-warning";
      
      tr.innerHTML = `
        <td><strong>${p.nro_poliza}</strong></td>
        <td>${p.cliente_nombre || "Cliente " + p.cliente_id}</td>
        <td>${p.compania}</td>
        <td>${p.ramo}</td>
        <td>${p.vigencia_hasta || "—"}</td>
        <td>$${p.premio.toLocaleString()}</td>
        <td><span class="badge ${badgeClass}">${p.estado}</span></td>
      `;
      tbody.appendChild(tr);
    });
    
  } catch (error) {
    console.error("Failed to load portfolio", error);
  }
}

// Metrics data
async function loadMetricsData() {
  try {
    const erp = await apiFetch("/metricas/erp");
    const ranking = await apiFetch("/metricas/productores");
    
    // Draw metrics stats
    const metricsContainer = document.getElementById("metricsErpContainer");
    metricsContainer.innerHTML = `
      <div class="stat-card">
        <div class="stat-icon">📈</div>
        <div class="stat-info">
          <span class="stat-label">Ventas Totales</span>
          <span class="stat-value">$${(erp.ventas_totales || 0).toLocaleString()}</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">🏦</div>
        <div class="stat-info">
          <span class="stat-label">Comisiones Cobradas</span>
          <span class="stat-value">$${(erp.comisiones_totales || 0).toLocaleString()}</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">📊</div>
        <div class="stat-info">
          <span class="stat-label">Ratio de Siniestralidad</span>
          <span class="stat-value">${erp.ratio_siniestralidad || 0}%</span>
        </div>
      </div>
    `;
    
    // Draw charts
    drawRamosChart();
    drawProductoresChart(ranking);
    
  } catch (error) {
    console.error("Failed to load metrics", error);
  }
}

function drawRamosChart() {
  const ctx = document.getElementById("chartRamos").getContext("2d");
  
  if (chartRamosInstance) {
    chartRamosInstance.destroy();
  }
  
  chartRamosInstance = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: ["Automotores", "Combinado Familiar", "Vida", "ART", "Hogar", "Otros"],
      datasets: [{
        data: [45, 20, 15, 10, 5, 5],
        backgroundColor: [
          "#6366f1",
          "#10b981",
          "#f59e0b",
          "#ef4444",
          "#3b82f6",
          "#8b5cf6"
        ],
        borderWidth: 0
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            color: getComputedStyle(document.documentElement).getPropertyValue('--text-color').trim(),
            boxWidth: 12,
            font: { family: 'Inter' }
          }
        }
      }
    }
  });
}

function drawProductoresChart(ranking) {
  const ctx = document.getElementById("chartProductores").getContext("2d");
  
  if (chartProductoresInstance) {
    chartProductoresInstance.destroy();
  }
  
  const labels = ranking && ranking.length > 0 ? ranking.map(r => r.nombre.split(" ")[0]) : ["Carlos", "María", "José", "Ana", "Luis"];
  const values = ranking && ranking.length > 0 ? ranking.map(r => r.produccion) : [120000, 95000, 80000, 75000, 62000];
  
  chartProductoresInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [{
        label: "Producción Emitida ($)",
        data: values,
        backgroundColor: "rgba(99, 102, 241, 0.8)",
        borderRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: getComputedStyle(document.documentElement).getPropertyValue('--text-color').trim() }
        },
        y: {
          grid: { color: "rgba(255, 255, 255, 0.05)" },
          ticks: { color: getComputedStyle(document.documentElement).getPropertyValue('--text-color').trim() }
        }
      }
    }
  });
}

// Commercial schedule
async function loadVisitasData() {
  try {
    const data = await apiFetch("/visitas/");
    const tbody = document.getElementById("visitasTableBody");
    tbody.innerHTML = "";
    
    if (!data || data.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center" style="padding: 20px; color: var(--text-muted);">No hay visitas planificadas.</td></tr>`;
      return;
    }
    
    data.forEach(v => {
      const tr = document.createElement("tr");
      
      let badgeClass = "badge-warning";
      if (v.estado === "realizada") badgeClass = "badge-success";
      if (v.estado === "cancelada") badgeClass = "badge-danger";
      
      tr.innerHTML = `
        <td><strong>${v.nombre}</strong> <span style="font-size:11px;color:var(--text-muted)">(${v.matricula || "S/M"})</span></td>
        <td>${v.fecha || v.mes || "—"}</td>
        <td>${v.campaña || v.productividad || "General"}</td>
        <td><span class="badge ${badgeClass}">${v.estado.toUpperCase()}</span></td>
        <td>${v.estado_org || "Sin observaciones adicionales"}</td>
        <td>
          <button class="btn btn-ghost btn-sm" onclick="completeVisita(${v.id})">✓ Completar</button>
          <button class="btn btn-danger btn-sm" style="padding:6px; margin-left:4px;" onclick="deleteVisita(${v.id})">🗑️</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (error) {
    console.error("Failed to load visits", error);
  }
}

async function saveVisitaForm() {
  const nombre = document.getElementById("visitaPasNombre").value.trim();
  const fecha = document.getElementById("visitaFecha").value;
  const campaña = document.getElementById("visitaProposito").value.trim();
  const notas = document.getElementById("visitaNotas").value.trim();
  
  if (!nombre || !fecha) {
    alert("Ingrese nombre y fecha para la visita.");
    return;
  }
  
  try {
    await apiFetch("/visitas/", {
      method: "POST",
      body: JSON.stringify({
        nombre,
        mes: fecha,
        campaña,
        estado_org: notas,
        matricula: "",
        productividad: "Planificada"
      })
    });
    
    closeModal("modalVisitaForm");
    showToast("Visita programada con éxito");
    loadVisitasData();
    
    // Clear inputs
    document.getElementById("visitaPasNombre").value = "";
    document.getElementById("visitaFecha").value = "";
    document.getElementById("visitaProposito").value = "";
    document.getElementById("visitaNotas").value = "";
  } catch (error) {
    showToast(`Error al programar visita: ${error.message}`, "danger");
  }
}

async function completeVisita(visitaId) {
  try {
    await apiFetch(`/visitas/${visitaId}`, {
      method: "PUT",
      body: JSON.stringify({
        estado: "realizada",
        productividad: "Completada",
        estado_org: "Reunión finalizada con éxito",
        campaña: ""
      })
    });
    showToast("Visita marcada como realizada");
    loadVisitasData();
  } catch (error) {
    showToast(`Error al completar visita: ${error.message}`, "danger");
  }
}

async function deleteVisita(visitaId) {
  if (!confirm("¿Está seguro de eliminar esta visita del cronograma?")) return;
  
  try {
    await apiFetch(`/visitas/${visitaId}`, {
      method: "DELETE"
    });
    showToast("Visita eliminada");
    loadVisitasData();
  } catch (error) {
    showToast(`Error al eliminar visita: ${error.message}`, "danger");
  }
}

// Admin Users
async function loadAdminUsers() {
  if (!currentUser || (currentUser.role !== "admin" && currentUser.role !== "superadmin")) return;
  
  try {
    const users = await apiFetch("/usuarios/");
    const tbody = document.getElementById("adminUsersTableBody");
    tbody.innerHTML = "";
    
    if (!users || users.length === 0) {
      tbody.innerHTML = `<tr><td colspan="4" class="text-center" style="padding: 10px; color: var(--text-muted);">No hay usuarios registrados.</td></tr>`;
      return;
    }
    
    users.forEach(u => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong>${u.usuario}</strong></td>
        <td>${u.email || "—"}</td>
        <td><span class="badge badge-info">${u.rol}</span></td>
        <td>
          <button class="btn btn-danger btn-sm" style="padding: 4px 8px; font-size:11px;" onclick="deleteSystemUser(${u.id})">Eliminar</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (error) {
    console.error("Failed to load admin users", error);
  }
}

async function saveSystemUser() {
  const username = document.getElementById("userFormUsername").value.trim();
  const email = document.getElementById("userFormEmail").value.trim();
  const password = document.getElementById("userFormPassword").value;
  const role = document.getElementById("userFormRole").value;
  
  if (!username || !password) {
    alert("Nombre de usuario y contraseña son requeridos");
    return;
  }
  
  try {
    await apiFetch("/usuarios/", {
      method: "POST",
      body: JSON.stringify({
        usuario: username,
        email: email,
        password: password,
        rol: role,
        matricula: ""
      })
    });
    
    closeModal("modalUserForm");
    showToast("Usuario creado correctamente");
    loadAdminUsers();
    
    // Clear inputs
    document.getElementById("userFormUsername").value = "";
    document.getElementById("userFormEmail").value = "";
    document.getElementById("userFormPassword").value = "";
  } catch (error) {
    showToast(`Error al crear usuario: ${error.message}`, "danger");
  }
}

async function deleteSystemUser(userId) {
  if (!confirm("¿Está seguro de eliminar este usuario? No podrá ingresar al CRM.")) return;
  
  try {
    await apiFetch(`/usuarios/${userId}`, {
      method: "DELETE"
    });
    showToast("Usuario eliminado");
    loadAdminUsers();
  } catch (error) {
    showToast(`Error al eliminar usuario: ${error.message}`, "danger");
  }
}

// Clean SQLite DB
async function handleCleanDb() {
  if (!confirm("⚠️ ATENCIÓN: Esta acción vaciará por completo la tabla de productores locales en SQLite. ¿Desea continuar?")) return;
  
  try {
    await apiFetch("/mantenimiento/vaciar-db", {
      method: "POST"
    });
    showToast("Base de datos local vaciada con éxito");
    loadSearchResults();
  } catch (error) {
    showToast(`Error al limpiar base de datos: ${error.message}`, "danger");
  }
}

// Excel Import
async function executeImport() {
  if (!selectedImportFile) return;
  
  const startBtn = document.getElementById("btnStartImport");
  const fileNameSpan = document.getElementById("importFileName");
  
  const originalText = startBtn.innerHTML;
  startBtn.disabled = true;
  startBtn.innerHTML = `<span>⏳ Procesando Padrón...</span>`;
  
  const formData = new FormData();
  formData.append("file", selectedImportFile);
  
  showToast("Subiendo y procesando padrón. Esto puede demorar unos minutos...");
  
  const url = `${apiBaseUrl.replace(/\/$/, "")}/mantenimiento/importar-excel`;
  const headers = {};
  if (accessToken) {
    headers["Authorization"] = `Bearer ${accessToken}`;
  }
  
  try {
    const response = await fetch(url, {
      method: "POST",
      headers,
      body: formData
    });
    
    if (!response.ok) {
      let errMsg = `Error de red: ${response.status}`;
      try {
        const errJson = await response.json();
        if (errJson.detail) errMsg = errJson.detail;
      } catch(e) {}
      throw new Error(errMsg);
    }
    
    const result = await response.json();
    showToast(`¡Padrón importado! ${result.insertados || 0} registros nuevos/actualizados.`);
    
    // Reset state
    selectedImportFile = null;
    document.getElementById("btnImportExcel").value = "";
    fileNameSpan.textContent = "Ningún archivo seleccionado (.xlsx, .xlsm, .csv)";
    fileNameSpan.style.color = "var(--text-muted)";
    startBtn.style.display = "none";
    
    loadSearchResults();
  } catch (error) {
    showToast(`Fallo en importación: ${error.message}`, "danger");
  } finally {
    startBtn.disabled = false;
    startBtn.innerHTML = originalText;
  }
}




// Modal Helpers
window.openModal = function(modalId) {
  document.getElementById(modalId).style.display = "flex";
};

window.closeModal = function(modalId) {
  document.getElementById(modalId).style.display = "none";
};

// Toast notification
function showToast(message, type = "success") {
  const banner = document.getElementById("toastBanner");
  const msgSpan = document.getElementById("toastMessage");
  
  msgSpan.textContent = message;
  
  if (type === "danger") {
    banner.style.borderColor = "var(--danger-color)";
    banner.style.color = "var(--danger-color)";
    banner.style.background = "var(--danger-bg)";
  } else {
    banner.style.borderColor = "var(--success-color)";
    banner.style.color = "var(--success-color)";
    banner.style.background = "var(--success-bg)";
  }
  
  banner.style.display = "block";
  
  setTimeout(() => {
    banner.style.display = "none";
  }, 4000);
}

// System Config functions
async function loadSystemConfigs() {
  try {
    const data = await apiFetch("/configuracion");
    if (data) {
      systemConfigs = data;
      applyFeatureVisibility();
      
      const configView = document.getElementById("viewConfig");
      if (configView && configView.classList.contains("active")) {
        populateConfigCheckboxes();
      }
    }
  } catch (error) {
    console.error("Error al cargar configuraciones de sistema:", error);
  }
}

function applyFeatureVisibility() {
  const ssnBtn = document.getElementById("btnTriggerSSNSearch");
  if (ssnBtn) {
    if (systemConfigs.permitir_busqueda_ssn === "false") {
      ssnBtn.style.display = "none";
    } else {
      ssnBtn.style.display = "inline-block";
    }
  }

  // Import padron card/field
  const importInput = document.getElementById("btnImportExcel");
  if (importInput) {
    const parentGroup = importInput.closest(".form-group");
    if (parentGroup) {
      parentGroup.style.display = (systemConfigs.permitir_importacion_excel === "false") ? "none" : "block";
    }
  }

  // Clean DB button
  const cleanBtn = document.getElementById("btnCleanDb");
  if (cleanBtn) {
    cleanBtn.style.display = (systemConfigs.permitir_vaciar_db === "false") ? "none" : "inline-block";
  }

  // Sidebar tabs
  const carteraTab = document.querySelector('[data-view="viewCartera"]');
  if (carteraTab) {
    carteraTab.style.display = (systemConfigs.permitir_cartera_polizas === "false") ? "none" : "block";
  }

  const metricsTab = document.querySelector('[data-view="viewMetrics"]');
  if (metricsTab) {
    metricsTab.style.display = (systemConfigs.permitir_metricas_kpi === "false") ? "none" : "block";
  }

  const commercialTab = document.querySelector('[data-view="viewCommercial"]');
  if (commercialTab) {
    commercialTab.style.display = (systemConfigs.permitir_plan_comercial === "false") ? "none" : "block";
  }
}

async function loadConfigView() {
  if (!currentUser || (currentUser.role !== "admin" && currentUser.role !== "superadmin")) return;
  
  try {
    await loadSystemConfigs();
    populateConfigCheckboxes();
  } catch (error) {
    showToast("Error al cargar configuración", "danger");
  }
}

function populateConfigCheckboxes() {
  const keys = [
    "permitir_busqueda_ssn",
    "permitir_importacion_excel",
    "permitir_vaciar_db",
    "permitir_cartera_polizas",
    "permitir_metricas_kpi",
    "permitir_plan_comercial"
  ];
  
  keys.forEach(key => {
    const input = document.getElementById(`cfg_${key}`);
    if (input) {
      input.checked = (systemConfigs[key] === "true");
    }
  });
}

