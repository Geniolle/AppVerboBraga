(function () {
  'use strict';

  const FIELD_NAME = 'numero_entidade';
  const FIELD_LABEL = 'Nº Entidade';
  const LOG_PREFIX = 'APPVERBO_ENTITY_DEFAULT_RULE_V3_READONLY';

  function log(message, data) {
    try {
      console.log(LOG_PREFIX + ': ' + message, data || {});
    } catch (error) {}
  }

  function normalize(value) {
    try {
      return String(value || '')
        .toLowerCase()
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .replace(/\s+/g, ' ')
        .trim();
    } catch (error) {
      return String(value || '').toLowerCase().trim();
    }
  }

  function cleanValue(value) {
    return String(value || '').trim();
  }

  function isUsableValue(value) {
    const text = cleanValue(value);

    if (!text) return false;
    if (text === 'undefined') return false;
    if (text === 'null') return false;
    if (text === '[object Object]') return false;

    return true;
  }

  function readFromObjectDeep(source, maxDepth) {
    const wantedKeys = [
      'numero_entidade',
      'numeroEntidade',
      'n_entidade',
      'nEntidade',
      'entidade_numero',
      'entidadeNumero',
      'empresa_numero',
      'empresaNumero',
      'empresa_numero_entidade',
      'empresaNumeroEntidade',
      'current_numero_entidade',
      'currentNumeroEntidade',
      'logged_numero_entidade',
      'loggedNumeroEntidade',
      'tenant_number',
      'tenantNumber',
      'company_number',
      'companyNumber',
      'entity_number',
      'entityNumber'
    ];

    const visited = new Set();

    function walk(obj, depth) {
      if (!obj || depth > maxDepth) return '';

      if (typeof obj !== 'object') return '';

      if (visited.has(obj)) return '';
      visited.add(obj);

      for (const key of wantedKeys) {
        try {
          if (Object.prototype.hasOwnProperty.call(obj, key) && isUsableValue(obj[key])) {
            return cleanValue(obj[key]);
          }
        } catch (error) {}
      }

      for (const key of Object.keys(obj)) {
        try {
          const value = obj[key];

          if (!value || typeof value !== 'object') continue;

          const found = walk(value, depth + 1);

          if (found) return found;
        } catch (error) {}
      }

      return '';
    }

    return walk(source, 0);
  }

  function readFromGlobalVariables() {
    const candidates = [
      'APPVERBO_BOOTSTRAP',
      'APPVERBO_PAGE_STATE',
      '__APPVERBO_BOOTSTRAP__',
      '__APPVERBO_PAGE_STATE__',
      'AppVerboBootstrap',
      'AppVerboPageState',
      'currentUser',
      'currentEmpresa',
      'currentCompany',
      'currentEntity',
      'loggedEntity',
      'loggedCompany'
    ];

    for (const name of candidates) {
      try {
        const value = window[name];

        if (!value) continue;

        if (typeof value === 'string' && isUsableValue(value)) {
          return cleanValue(value);
        }

        const found = readFromObjectDeep(value, 4);

        if (found) return found;
      } catch (error) {}
    }

    return '';
  }

  function readFromDataset() {
    const elements = [
      document.documentElement,
      document.body,
      document.querySelector('[data-numero-entidade]'),
      document.querySelector('[data-n-entidade]'),
      document.querySelector('[data-entity-number]'),
      document.querySelector('[data-company-number]'),
      document.querySelector('[data-empresa-numero-entidade]'),
      document.querySelector('[data-empresa-logada]'),
      document.querySelector('[data-entidade-logada]')
    ].filter(Boolean);

    const attrs = [
      'numeroEntidade',
      'nEntidade',
      'entityNumber',
      'companyNumber',
      'empresaNumeroEntidade',
      'empresaLogada',
      'entidadeLogada'
    ];

    for (const element of elements) {
      for (const attr of attrs) {
        try {
          const value = element.dataset && element.dataset[attr];

          if (isUsableValue(value)) return cleanValue(value);
        } catch (error) {}
      }
    }

    return '';
  }

  function readFromInputs() {
    const selectors = [
      '[name="empresa_numero_entidade"]',
      '[name="empresaNumeroEntidade"]',
      '[name="logged_numero_entidade"]',
      '[name="loggedNumeroEntidade"]',
      '[name="current_numero_entidade"]',
      '[name="currentNumeroEntidade"]',
      '[name="entidade_logada"]',
      '[name="empresa_logada"]',
      '[name="tenant_number"]',
      '[name="company_number"]',
      '[name="entity_number"]',
      '[id="empresa_numero_entidade"]',
      '[id="logged_numero_entidade"]',
      '[id="current_numero_entidade"]'
    ];

    for (const selector of selectors) {
      const field = document.querySelector(selector);

      if (!field) continue;

      const value = field.value || field.getAttribute('value') || field.textContent;

      if (isUsableValue(value)) return cleanValue(value);
    }

    return '';
  }

  function readFromMeta() {
    const selectors = [
      'meta[name="numero_entidade"]',
      'meta[name="empresa_numero_entidade"]',
      'meta[name="logged_numero_entidade"]',
      'meta[name="current_numero_entidade"]',
      'meta[name="entity_number"]',
      'meta[name="company_number"]'
    ];

    for (const selector of selectors) {
      const meta = document.querySelector(selector);

      if (!meta) continue;

      const value = meta.getAttribute('content');

      if (isUsableValue(value)) return cleanValue(value);
    }

    return '';
  }

  function readFromVisibleCompanyName() {
    const selectors = [
      '.app-brand',
      '.brand',
      '.brand-name',
      '.sidebar-brand',
      '.navbar-brand',
      '.topbar-brand',
      '.app-logo-text',
      'header strong',
      'aside strong'
    ];

    for (const selector of selectors) {
      const element = document.querySelector(selector);

      if (!element) continue;

      const value = cleanValue(element.textContent);

      if (isUsableValue(value)) return value;
    }

    const fallbackTexts = Array.from(document.querySelectorAll('header, aside, nav'))
      .map(function (element) {
        return cleanValue(element.textContent);
      })
      .filter(Boolean);

    for (const text of fallbackTexts) {
      if (text.includes('Deixa Estar Tech')) return 'Deixa Estar Tech';
    }

    return '';
  }

  function getLoggedEntityValue() {
    return (
      readFromDataset() ||
      readFromMeta() ||
      readFromInputs() ||
      readFromGlobalVariables() ||
      readFromVisibleCompanyName() ||
      ''
    );
  }

  function isEstadoLabel(label) {
    const text = normalize(label.textContent);
    return text === 'estado' || text === 'estado *' || text.startsWith('estado ');
  }

  function findInputForLabel(label) {
    if (!label) return null;

    const forId = label.getAttribute('for');

    if (forId) {
      const byFor = document.getElementById(forId);
      if (byFor) return byFor;
    }

    const ownContainer = label.closest('div, .form-group, .field, .mb-3, .col, .row');

    if (!ownContainer) return null;

    return ownContainer.querySelector('select, input, textarea');
  }

  function findEstadoContainers() {
    const labels = Array.from(document.querySelectorAll('label'));
    const found = [];

    labels.forEach(function (label) {
      if (!isEstadoLabel(label)) return;

      const field = findInputForLabel(label);
      if (!field) return;

      const container =
        field.closest('.form-group, .field, .form-field, .mb-3, .col, .col-md-6, .col-lg-6, div') ||
        label.closest('div');

      if (!container) return;

      found.push({
        label: label,
        field: field,
        container: container
      });
    });

    return found;
  }

  function containerAlreadyProcessed(container) {
    return (
      container.dataset.entityDefaultProcessed === '1' ||
      Boolean(container.closest('.entity-default-pair')) ||
      Boolean(document.querySelector('[name="' + FIELD_NAME + '"]')) ||
      Boolean(document.querySelector('[data-entity-default-field="numero_entidade"]'))
    );
  }

  function createNumeroEntidadeField() {
    const loggedEntityValue = getLoggedEntityValue();

    const wrapper = document.createElement('div');
    wrapper.className = 'generated-entity-number-field';
    wrapper.setAttribute('data-entity-default-field', 'numero_entidade');

    const id = 'numero_entidade_' + Math.random().toString(36).slice(2);

    const label = document.createElement('label');
    label.setAttribute('for', id);
    label.innerHTML = FIELD_LABEL + ' <span class="entity-default-required">*</span>';

    const input = document.createElement('input');
    input.type = 'text';
    input.id = id;
    input.name = FIELD_NAME;
    input.required = true;
    input.readOnly = true;
    input.setAttribute('readonly', 'readonly');
    input.setAttribute('aria-readonly', 'true');
    input.className = 'entity-default-readonly-input';
    input.autocomplete = 'off';
    input.placeholder = 'Entidade da empresa logada';
    input.value = loggedEntityValue;

    wrapper.appendChild(label);
    wrapper.appendChild(input);

    return wrapper;
  }

  function refreshExistingNumeroEntidadeFields() {
    const loggedEntityValue = getLoggedEntityValue();

    if (!loggedEntityValue) return;

    const fields = Array.from(document.querySelectorAll('[name="' + FIELD_NAME + '"]'));

    fields.forEach(function (field) {
      field.value = loggedEntityValue;
      field.readOnly = true;
      field.setAttribute('readonly', 'readonly');
      field.setAttribute('aria-readonly', 'true');
      field.classList.add('entity-default-readonly-input');
    });
  }

  function placeSideBySide(estadoContainer, numeroContainer) {
    const parent = estadoContainer.parentElement;

    if (!parent) {
      estadoContainer.insertAdjacentElement('afterend', numeroContainer);
      return;
    }

    const pair = document.createElement('div');
    pair.className = 'entity-default-pair';
    pair.setAttribute('data-entity-default-pair', 'estado-numero-entidade');

    parent.insertBefore(pair, estadoContainer);
    pair.appendChild(estadoContainer);
    pair.appendChild(numeroContainer);
  }

  function applyRule() {
    const startedAt = Date.now();
    const estados = findEstadoContainers();
    const loggedEntityValue = getLoggedEntityValue();

    let created = 0;

    estados.forEach(function (item) {
      if (containerAlreadyProcessed(item.container)) return;

      item.container.dataset.entityDefaultProcessed = '1';

      const numeroField = createNumeroEntidadeField();

      placeSideBySide(item.container, numeroField);

      created += 1;
    });

    refreshExistingNumeroEntidadeFields();

    log('applyRule', {
      estados: estados.length,
      created: created,
      loggedEntityValue: loggedEntityValue,
      elapsedMs: Date.now() - startedAt
    });
  }

  function scheduleApplyRule(delay) {
    if (window.__appverboEntityDefaultTimer) {
      clearTimeout(window.__appverboEntityDefaultTimer);
    }

    window.__appverboEntityDefaultTimer = setTimeout(applyRule, delay || 250);
  }

  document.addEventListener('DOMContentLoaded', function () {
    scheduleApplyRule(250);
    setTimeout(applyRule, 1000);
    setTimeout(applyRule, 2500);
    setTimeout(applyRule, 5000);
  });

  window.addEventListener('load', function () {
    scheduleApplyRule(250);
  });

  document.addEventListener('click', function () {
    scheduleApplyRule(500);
  }, true);

  document.addEventListener('submit', function (event) {
    const form = event.target;

    if (!(form instanceof HTMLFormElement)) return;

    refreshExistingNumeroEntidadeFields();

    const field = form.querySelector('[name="' + FIELD_NAME + '"]');

    if (!field) return;

    if (!String(field.value || '').trim()) {
      event.preventDefault();
      alert('Não foi possível identificar a entidade da empresa logada.');
    }
  }, true);

  window.AppEntityDefaultRule = {
    applyRule: applyRule,
    findEstadoContainers: findEstadoContainers,
    getLoggedEntityValue: getLoggedEntityValue,
    refreshExistingNumeroEntidadeFields: refreshExistingNumeroEntidadeFields
  };
})();
