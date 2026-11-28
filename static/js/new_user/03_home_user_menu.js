// new_user/03_home_user_menu.js: Home (graficos), avatar e menu do utilizador, datas de ausencia.
// Scripts classicos com escopo global partilhado; carregar pela ordem de templates/new_user.html.


//###################################################################################
// (SUBMENU SUPERIOR REUTILIZAVEL) WRAPPER FINO DO CONTROLLER GENERICO
//###################################################################################

function renderHomeCharts() {
  if (!window.Chart) {
    return;
  }

  const entityCanvas = document.getElementById("home-entities-chart");
  if (entityCanvas && !entityCanvas.dataset.chartReady) {
    new Chart(entityCanvas, {
      type: "doughnut",
      data: {
        labels: (dashboardData.entity_status || {}).labels || [],
        datasets: [
          {
            data: (dashboardData.entity_status || {}).values || [],
            backgroundColor: ["#1f7a49", "#d07a31"],
            borderColor: "#ffffff",
            borderWidth: 2
          }
        ]
      },
      options: {
        maintainAspectRatio: false,
        plugins: { legend: { position: "bottom" } }
      }
    });
    entityCanvas.dataset.chartReady = "1";
  }

  const profileCanvas = document.getElementById("home-profiles-chart");
  if (profileCanvas && !profileCanvas.dataset.chartReady) {
    new Chart(profileCanvas, {
      type: "bar",
      data: {
        labels: (dashboardData.users_by_profile || {}).labels || [],
        datasets: [
          {
            label: "Utilizadores",
            data: (dashboardData.users_by_profile || {}).values || [],
            backgroundColor: ["#2f6db4", "#3f84d6", "#58a3ec"],
            borderRadius: 7,
            maxBarThickness: 62
          }
        ]
      },
      options: {
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            ticks: { precision: 0 }
          }
        },
        plugins: { legend: { display: false } }
      }
    });
    profileCanvas.dataset.chartReady = "1";
  }
}

function getInitials(name) {
  const parts = String(name || "").trim().split(/\s+/).filter(Boolean);
  if (!parts.length) {
    return "U";
  }
  if (parts.length === 1) {
    return parts[0].slice(0, 2).toUpperCase();
  }
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function buildAvatarDataUri(name) {
  const initials = getInitials(name);
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" viewBox="0 0 96 96">
      <defs>
        <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#3777dc"/>
          <stop offset="100%" stop-color="#244ea5"/>
        </linearGradient>
      </defs>
      <rect width="96" height="96" rx="48" fill="url(#g)"/>
      <text x="50%" y="55%" text-anchor="middle" dominant-baseline="middle" fill="#ffffff" font-family="Segoe UI, Arial, sans-serif" font-size="34" font-weight="700">${initials}</text>
    </svg>
  `;
  return "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
}

function closeUserDropdown() {
  if (!userDropdownEl || !userMenuTriggerEl) {
    return;
  }
  userDropdownEl.hidden = true;
  userMenuTriggerEl.setAttribute("aria-expanded", "false");
}

function openUserDropdown() {
  if (!userDropdownEl || !userMenuTriggerEl) {
    return;
  }
  userDropdownEl.hidden = false;
  userMenuTriggerEl.setAttribute("aria-expanded", "true");
}

function toggleUserDropdown() {
  if (!userDropdownEl || !userMenuTriggerEl) {
    return;
  }
  const expanded = userMenuTriggerEl.getAttribute("aria-expanded") === "true";
  if (expanded) {
    closeUserDropdown();
  } else {
    openUserDropdown();
  }
}

function isTruthyFlagValue(value) {
  const cleanValue = String(value || "").trim().toLowerCase();
  return ["1", "true", "sim", "yes", "on"].includes(cleanValue);
}

function getDynamicProcessInputType(fieldType) {
  if (fieldType === "email") {
    return "email";
  }
  if (fieldType === "number") {
    return "number";
  }
  if (fieldType === "phone") {
    return "tel";
  }
  if (fieldType === "date") {
    return "date";
  }
  if (fieldType === "time") {
    return "time";
  }
  return "text";
}

function normalizeDateInputValue(rawValue) {
  const cleanValue = String(rawValue || "").trim();
  if (!cleanValue) {
    return "";
  }
  if (/^\d{4}-\d{2}-\d{2}$/.test(cleanValue)) {
    return cleanValue;
  }
  const slashMatch = cleanValue.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (slashMatch) {
    const [, day, month, year] = slashMatch;
    return `${year}-${month}-${day}`;
  }
  return "";
}

function isStartDateField(field) {
  const joined = `${normalizeLookupText(field.key)} ${normalizeLookupText(field.label)}`.trim();
  if (!joined) {
    return false;
  }
  return joined.includes("data inicio") || joined.includes(" inicio") || joined.endsWith("inicio");
}

function isEndDateField(field) {
  const joined = `${normalizeLookupText(field.key)} ${normalizeLookupText(field.label)}`.trim();
  if (!joined) {
    return false;
  }
  return joined.includes("data fim") || joined.includes(" fim") || joined.endsWith("fim");
}

function setupAbsenceDateRangeValidation(sectionFields, inputsByFieldKey) {
  if (!Array.isArray(sectionFields) || !inputsByFieldKey || typeof inputsByFieldKey.get !== "function") {
    return;
  }
  let startDateInputEl = null;
  let endDateInputEl = null;
  sectionFields.forEach((field) => {
    if (normalizeProcessFieldType(field.fieldType) !== "date") {
      return;
    }
    const inputEl = inputsByFieldKey.get(normalizeMenuKey(field.key));
    if (!inputEl) {
      return;
    }
    if (!startDateInputEl && isStartDateField(field)) {
      startDateInputEl = inputEl;
    }
    if (!endDateInputEl && isEndDateField(field)) {
      endDateInputEl = inputEl;
    }
  });
  if (!startDateInputEl || !endDateInputEl) {
    return;
  }

  const syncDateRangeRule = () => {
    const startDateValue = normalizeDateInputValue(startDateInputEl.value);
    const endDateValue = normalizeDateInputValue(endDateInputEl.value);
    if (startDateValue) {
      endDateInputEl.min = startDateValue;
    } else {
      endDateInputEl.removeAttribute("min");
    }
    if (startDateValue && endDateValue && endDateValue < startDateValue) {
      endDateInputEl.setCustomValidity("Data fim não pode ser menor que a data início.");
    } else {
      endDateInputEl.setCustomValidity("");
    }
  };

  startDateInputEl.addEventListener("input", syncDateRangeRule);
  endDateInputEl.addEventListener("input", syncDateRangeRule);
  syncDateRangeRule();
}
