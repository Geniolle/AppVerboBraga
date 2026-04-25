(function () {
  const emailInput = document.getElementById("email");
  const entitySelect = document.getElementById("entity_id");
  const countrySelect = document.getElementById("country");
  const phoneInput = document.getElementById("primary_phone");

  function extractDomain(value) {
    const email = String(value || "").trim().toLowerCase();
    const atIndex = email.indexOf("@");
    if (atIndex < 0) {
      return "";
    }
    return email.slice(atIndex + 1).trim();
  }

  function resolveEntityIdByEmail(value) {
    const email = String(value || "").trim().toLowerCase();
    if (!email || email.indexOf("@") < 0) {
      return "";
    }

    const options = Array.from(entitySelect.options).filter((option) => option.value);
    const exactMatches = options.filter((option) => {
      const candidate = String(option.dataset.entityEmail || "").trim().toLowerCase();
      return candidate && candidate === email;
    });
    if (exactMatches.length === 1) {
      return exactMatches[0].value;
    }
    if (exactMatches.length > 1) {
      return "";
    }

    const domain = extractDomain(email);
    if (!domain) {
      return "";
    }
    const domainMatches = options.filter((option) => {
      const candidate = String(option.dataset.entityEmail || "").trim().toLowerCase();
      const candidateDomain = extractDomain(candidate);
      return candidateDomain && candidateDomain === domain;
    });
    if (domainMatches.length === 1) {
      return domainMatches[0].value;
    }
    if (domainMatches.length > 1) {
      return "";
    }

    if (options.length === 1) {
      return options[0].value;
    }
    return "";
  }

  function autoSelectEntity() {
    const resolvedId = resolveEntityIdByEmail(emailInput.value);
    if (!resolvedId) {
      return;
    }
    entitySelect.value = resolvedId;
  }

  if (emailInput && entitySelect) {
    emailInput.addEventListener("input", autoSelectEntity);
    emailInput.addEventListener("change", autoSelectEntity);
    autoSelectEntity();
  }

  function syncPhoneCountryHint() {
    if (!countrySelect || !phoneInput) {
      return;
    }
    const selectedOption = countrySelect.options[countrySelect.selectedIndex];
    const placeholder = String(selectedOption?.dataset.phonePlaceholder || "").trim();
    const callingCode = String(selectedOption?.dataset.callingCode || "").trim();
    if (placeholder) {
      phoneInput.placeholder = placeholder;
    }
    if (!phoneInput.value.trim() && callingCode) {
      phoneInput.value = `${callingCode} `;
    }
  }

  if (countrySelect && phoneInput) {
    countrySelect.addEventListener("change", syncPhoneCountryHint);
    syncPhoneCountryHint();
  }
})();
