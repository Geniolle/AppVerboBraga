(function () {
  'use strict';

  const FIELD_NAME = 'numero_entidade';
  const FIELD_LABEL = 'Nº Entidade';
  const LOG_PREFIX = 'APPVERBO_ENTITY_DEFAULT_RULE_V2';

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

  function isEstadoLabel(label) {
    const text = normalize(label.textContent);
    return text === 'estado' || text === 'estado *' || text.startsWith('estado ');
  }

  function getPrefix() {
    const pageText = normalize([
      window.location.pathname,
      window.location.search,
      document.title,
      document.querySelector('h1')?.textContent || '',
      document.querySelector('h2')?.textContent || '',
      document.querySelector('.active')?.textContent || ''
    ].join(' '));

    if (pageText.includes('extrato')) return 'EXT';
    if (pageText.includes('tesouraria')) return 'TES';
    if (pageText.includes('utilizador') || pageText.includes('usuario')) return 'USR';
    if (pageText.includes('musica')) return 'MUS';
    if (pageText.includes('evento')) return 'EVT';
    if (pageText.includes('departamento')) return 'DEP';

    return 'ENT';
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
    const prefix = getPrefix();

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
    input.autocomplete = 'off';
    input.placeholder = 'Ex.: ' + prefix + '-000001';

    wrapper.appendChild(label);
    wrapper.appendChild(input);

    return wrapper;
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

    let created = 0;

    estados.forEach(function (item) {
      if (containerAlreadyProcessed(item.container)) return;

      item.container.dataset.entityDefaultProcessed = '1';

      const numeroField = createNumeroEntidadeField();

      placeSideBySide(item.container, numeroField);

      created += 1;
    });

    log('applyRule', {
      estados: estados.length,
      created: created,
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
    log('DOMContentLoaded');
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

    const field = form.querySelector('[name="' + FIELD_NAME + '"]');

    if (!field) return;

    if (!String(field.value || '').trim()) {
      event.preventDefault();
      field.focus();
      alert('O campo Nº Entidade é obrigatório.');
    }
  }, true);

  window.AppEntityDefaultRule = {
    applyRule: applyRule,
    findEstadoContainers: findEstadoContainers
  };
})();
