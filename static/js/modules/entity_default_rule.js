(function () {
  'use strict';

  const FIELD_NAME = 'numero_entidade';
  const HIDDEN_CLIENT_FIELD_NAME = 'numero_cliente';
  const FIELD_LABEL = 'Nº Cliente';
  const STORAGE_KEY = 'APPVERBO_LOGGED_NUMERO_CLIENTE';
  const LOG_PREFIX = 'APPVERBO_ENTITY_DEFAULT_RULE_V5_NUMERO_CLIENTE';

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
        .replace(/[º°]/g, '')
        .replace(/\s+/g, ' ')
        .trim();
    } catch (error) {
      return String(value || '').toLowerCase().trim();
    }
  }

  function cleanValue(value) {
    return String(value || '').trim();
  }

  function isUsableClientNumber(value) {
    const text = cleanValue(value);

    if (!text) return false;
    if (text === 'undefined') return false;
    if (text === 'null') return false;
    if (text === '[object Object]') return false;

    return /\d/.test(text);
  }

  function saveClientNumber(value) {
    if (!isUsableClientNumber(value)) return '';

    const clean = cleanValue(value);

    try {
      window.localStorage.setItem(STORAGE_KEY, clean);
    } catch (error) {}

    return clean;
  }

  function readClientNumberFromStorage() {
    try {
      const value = window.localStorage.getItem(STORAGE_KEY);

      if (isUsableClientNumber(value)) {
        return cleanValue(value);
      }
    } catch (error) {}

    return '';
  }

  function getShellText(doc) {
    const selectors = [
      'header',
      'aside',
      'nav',
      '.sidebar',
      '.topbar',
      '.navbar',
      '.brand',
      '.app-brand',
      '.sidebar-brand',
      '.navbar-brand',
      '.company-name',
      '.tenant-name'
    ];

    const parts = [];

    selectors.forEach(function (selector) {
      const elements = Array.from(doc.querySelectorAll(selector));

      elements.forEach(function (element) {
        const text = cleanValue(element.textContent);

        if (text) parts.push(text);
      });
    });

    return normalize(parts.join(' '));
  }

  function findClientNumberInTables(doc) {
    const shellText = getShellText(doc);
    const tables = Array.from(doc.querySelectorAll('table'));

    for (const table of tables) {
      const headerCells = Array.from(table.querySelectorAll('thead th, tr:first-child th, tr:first-child td'));

      if (!headerCells.length) continue;

      const headers = headerCells.map(function (cell) {
        return normalize(cell.textContent);
      });

      let clientIndex = -1;
      let nameIndex = -1;

      headers.forEach(function (header, index) {
        if (
          clientIndex < 0 &&
          (
            header === 'n cliente' ||
            header === 'numero cliente' ||
            header.includes('n cliente') ||
            header.includes('numero cliente')
          )
        ) {
          clientIndex = index;
        }

        if (
          nameIndex < 0 &&
          (
            header === 'nome' ||
            header.includes('nome') ||
            header.includes('entidade') ||
            header.includes('empresa')
          )
        ) {
          nameIndex = index;
        }
      });

      if (clientIndex < 0) continue;

      const rows = Array.from(table.querySelectorAll('tbody tr'));

      for (const row of rows) {
        const cells = Array.from(row.querySelectorAll('td'));

        if (cells.length <= clientIndex) continue;

        const clientNumber = cleanValue(cells[clientIndex].textContent);
        const rowText = normalize(row.textContent);
        const nameText = nameIndex >= 0 && cells[nameIndex]
          ? normalize(cells[nameIndex].textContent)
          : '';

        if (!isUsableClientNumber(clientNumber)) continue;

        /*
          Se o nome da entidade da linha aparecer no topo/menu da aplicação,
          assumimos que é a entidade logada.
          Exemplo:
          topo: Deixa Estar Tech
          tabela: 1000 | Deixa Estar Tech
        */
        if (nameText && shellText && shellText.includes(nameText)) {
          return saveClientNumber(clientNumber);
        }

        /*
          Fallback seguro:
          se a linha contém o texto visível da empresa logada já conhecido,
          usa o Nº Cliente dessa linha.
        */
        if (shellText && rowText && shellText.includes(rowText)) {
          return saveClientNumber(clientNumber);
        }
      }
    }

    return '';
  }

  function readFromCurrentDocument() {
    const selectors = [
      '[data-numero-cliente]',
      '[data-n-cliente]',
      '[data-client-number]',
      '[data-numero-entidade]',
      '[data-n-entidade]',
      '[data-entity-number]',
      '[name="numero_cliente"]',
      '[name="numeroCliente"]',
      '[name="n_cliente"]',
      '[name="cliente_numero"]',
      '[name="client_number"]',
      '[name="empresa_numero_cliente"]',
      '[name="company_number"]',
      'meta[name="numero_cliente"]',
      'meta[name="client_number"]',
      'meta[name="empresa_numero_cliente"]'
    ];

    for (const selector of selectors) {
      const element = document.querySelector(selector);

      if (!element) continue;

      const value =
        element.value ||
        element.getAttribute('value') ||
        element.getAttribute('content') ||
        element.dataset?.numeroCliente ||
        element.dataset?.nCliente ||
        element.dataset?.clientNumber ||
        element.dataset?.numeroEntidade ||
        element.dataset?.entityNumber ||
        element.textContent;

      if (isUsableClientNumber(value)) {
        return saveClientNumber(value);
      }
    }

    const fromTable = findClientNumberInTables(document);

    if (fromTable) return fromTable;

    return '';
  }

  function getLoggedClientNumber() {
    return (
      readFromCurrentDocument() ||
      readClientNumberFromStorage() ||
      ''
    );
  }

  async function fetchClientNumberFromAdminPage() {
    if (window.__appverboFetchingNumeroCliente) {
      return window.__appverboFetchingNumeroCliente;
    }

    window.__appverboFetchingNumeroCliente = fetch('/users/new?menu=administrativo&admin_tab=entidade', {
      credentials: 'same-origin',
      cache: 'no-store'
    })
      .then(function (response) {
        if (!response.ok) return '';

        return response.text();
      })
      .then(function (html) {
        if (!html) return '';

        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const value = findClientNumberInTables(doc);

        if (value) {
          saveClientNumber(value);
          refreshExistingNumeroEntidadeFields();
        }

        return value;
      })
      .catch(function (error) {
        log('Erro ao buscar Nº Cliente na página de entidades', { error: String(error) });
        return '';
      })
      .finally(function () {
        window.__appverboFetchingNumeroCliente = null;
      });

    return window.__appverboFetchingNumeroCliente;
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
      Boolean(document.querySelector('[data-entity-default-field="numero_cliente"]'))
    );
  }

  function createNumeroClienteField() {
    const numeroCliente = getLoggedClientNumber();

    const wrapper = document.createElement('div');
    wrapper.className = 'generated-entity-number-field';
    wrapper.setAttribute('data-entity-default-field', 'numero_cliente');

    const id = 'numero_cliente_' + Math.random().toString(36).slice(2);

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
    input.placeholder = numeroCliente ? '' : 'A carregar Nº Cliente...';
    input.value = numeroCliente || '';

    const hiddenClient = document.createElement('input');
    hiddenClient.type = 'hidden';
    hiddenClient.name = HIDDEN_CLIENT_FIELD_NAME;
    hiddenClient.value = numeroCliente || '';

    wrapper.appendChild(label);
    wrapper.appendChild(input);
    wrapper.appendChild(hiddenClient);

    return wrapper;
  }

  function refreshExistingNumeroEntidadeFields() {
    const numeroCliente = getLoggedClientNumber();

    const visibleFields = Array.from(document.querySelectorAll('[name="' + FIELD_NAME + '"]'));
    const hiddenFields = Array.from(document.querySelectorAll('[name="' + HIDDEN_CLIENT_FIELD_NAME + '"]'));

    visibleFields.forEach(function (field) {
      field.readOnly = true;
      field.setAttribute('readonly', 'readonly');
      field.setAttribute('aria-readonly', 'true');
      field.classList.add('entity-default-readonly-input');

      if (numeroCliente) {
        field.value = numeroCliente;
        field.placeholder = '';
      } else {
        field.value = '';
        field.placeholder = 'A carregar Nº Cliente...';
      }
    });

    hiddenFields.forEach(function (field) {
      field.value = numeroCliente || '';
    });

    if (!numeroCliente) {
      fetchClientNumberFromAdminPage();
    }
  }

  function placeSideBySide(estadoContainer, numeroContainer) {
    const parent = estadoContainer.parentElement;

    if (!parent) {
      estadoContainer.insertAdjacentElement('afterend', numeroContainer);
      return;
    }

    const pair = document.createElement('div');
    pair.className = 'entity-default-pair';
    pair.setAttribute('data-entity-default-pair', 'estado-numero-cliente');

    parent.insertBefore(pair, estadoContainer);
    pair.appendChild(estadoContainer);
    pair.appendChild(numeroContainer);
  }

  function applyRule() {
    const startedAt = Date.now();
    const estados = findEstadoContainers();
    const numeroCliente = getLoggedClientNumber();

    let created = 0;

    estados.forEach(function (item) {
      if (containerAlreadyProcessed(item.container)) return;

      item.container.dataset.entityDefaultProcessed = '1';

      const numeroField = createNumeroClienteField();

      placeSideBySide(item.container, numeroField);

      created += 1;
    });

    refreshExistingNumeroEntidadeFields();

    log('applyRule', {
      estados: estados.length,
      created: created,
      numeroCliente: numeroCliente,
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
      alert('Não foi possível identificar o Nº Cliente da entidade logada.');
    }
  }, true);

  window.AppEntityDefaultRule = {
    applyRule: applyRule,
    findEstadoContainers: findEstadoContainers,
    getLoggedClientNumber: getLoggedClientNumber,
    fetchClientNumberFromAdminPage: fetchClientNumberFromAdminPage,
    refreshExistingNumeroEntidadeFields: refreshExistingNumeroEntidadeFields
  };
})();
