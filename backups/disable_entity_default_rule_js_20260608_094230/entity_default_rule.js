/**
 * Regra global de entidade
 *
 * Sempre que um formulário tiver o campo Estado,
 * o sistema garante o campo Nº Entidade ao lado.
 *
 * Campo visual: Nº Entidade
 * Campo enviado para backend: numero_entidade
 */

(function () {
  const ENTITY_FIELD_NAME = 'numero_entidade';
  const ENTITY_FIELD_LABEL = 'Nº Entidade';

  const saveButtonWords = [
    'guardar',
    'salvar',
    'gravar',
    'criar',
    'adicionar',
    'registar',
    'registrar'
  ];

  function normalizeText(value) {
    return String(value || '')
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .trim();
  }

  function isSaveForm(form) {
    const buttons = Array.from(
      form.querySelectorAll('button, input[type="submit"], input[type="button"]')
    );

    const text = normalizeText(
      buttons
        .map((button) => button.innerText || button.value || '')
        .join(' ')
    );

    return saveButtonWords.some((word) => text.includes(word));
  }

  function isEstadoField(field) {
    const name = normalizeText(field.getAttribute('name'));
    const id = normalizeText(field.getAttribute('id'));
    const aria = normalizeText(field.getAttribute('aria-label'));

    let labelText = '';

    if (field.id) {
      const label = document.querySelector(`label[for="${field.id}"]`);
      if (label) {
        labelText = normalizeText(label.innerText);
      }
    }

    const parentText = normalizeText(
      field.closest('div, .form-group, .field, .col, .row')?.innerText || ''
    );

    return (
      name === 'estado' ||
      id === 'estado' ||
      aria === 'estado' ||
      labelText === 'estado' ||
      parentText.includes('estado')
    );
  }

  function formAlreadyHasEntityNumber(form) {
    return Boolean(
      form.querySelector(
        `[name="${ENTITY_FIELD_NAME}"], [name="numeroEntidade"], [data-entity-default-field="numero_entidade"]`
      )
    );
  }

  function getFieldContainer(field) {
    return (
      field.closest('.form-group, .field, .form-field, .mb-3, .col, .col-md-6, .col-lg-6') ||
      field.parentElement
    );
  }

  function guessEntityPrefix() {
    const pageText = normalizeText(
      `${document.title} ${window.location.pathname} ${document.body.innerText.slice(0, 300)}`
    );

    if (pageText.includes('extrato')) return 'EXT';
    if (pageText.includes('tesouraria')) return 'TES';
    if (pageText.includes('utilizador') || pageText.includes('usuario')) return 'USR';
    if (pageText.includes('musica')) return 'MUS';
    if (pageText.includes('evento')) return 'EVT';
    if (pageText.includes('departamento')) return 'DEP';

    return 'ENT';
  }

  function createEntityField(estadoField) {
    const prefix = guessEntityPrefix();
    const wrapper = document.createElement('div');

    wrapper.className = 'entity-default-field generated-entity-number-field';
    wrapper.setAttribute('data-entity-default-field', 'numero_entidade');

    const id = `${estadoField.id || 'estado'}_numero_entidade`;

    wrapper.innerHTML = `
      <label for="${id}">
        ${ENTITY_FIELD_LABEL} <span class="entity-default-required">*</span>
      </label>
      <input
        type="text"
        id="${id}"
        name="${ENTITY_FIELD_NAME}"
        required
        autocomplete="off"
        placeholder="Ex.: ${prefix}-000001"
      />
    `;

    return wrapper;
  }

  function ensureEntityNumberField() {
    const forms = Array.from(document.querySelectorAll('form'));

    forms.forEach((form) => {
      if (!isSaveForm(form)) return;
      if (formAlreadyHasEntityNumber(form)) return;

      const fields = Array.from(
        form.querySelectorAll('input, select, textarea')
      );

      const estadoField = fields.find(isEstadoField);

      if (!estadoField) return;

      const estadoContainer = getFieldContainer(estadoField);

      if (!estadoContainer) return;

      const entityField = createEntityField(estadoField);

      estadoContainer.insertAdjacentElement('afterend', entityField);
    });
  }

  function validateEntityNumberOnSubmit() {
    document.addEventListener('submit', function (event) {
      const form = event.target;

      if (!(form instanceof HTMLFormElement)) return;
      if (!isSaveForm(form)) return;

      const entityField = form.querySelector(`[name="${ENTITY_FIELD_NAME}"]`);

      if (!entityField) return;

      if (!String(entityField.value || '').trim()) {
        event.preventDefault();
        entityField.focus();
        alert('O campo Nº Entidade é obrigatório.');
      }
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    ensureEntityNumberField();
    validateEntityNumberOnSubmit();

    const observer = new MutationObserver(function () {
      ensureEntityNumberField();
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  });

  window.AppEntityDefaultRule = {
    ensureEntityNumberField
  };
})();