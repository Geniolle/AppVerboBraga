from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path


####################################################################################
# (1) CONFIGURACAO
####################################################################################

PROJECT_ROOT = Path.cwd()

MACRO_PATH = PROJECT_ROOT / "templates" / "macros" / "admin_subprocess_v2.html"
CSS_PATH = PROJECT_ROOT / "static" / "css" / "modules" / "admin_subprocesses_v2.css"


####################################################################################
# (2) FUNCOES AUXILIARES
####################################################################################

def now_stamp_v1() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def read_text_v1(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text_v1(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def backup_file_v1(path: Path, suffix: str) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"Ficheiro nao encontrado para backup: {path}")

    backup_path = path.with_name(path.name + f".bak_{suffix}_{now_stamp_v1()}")
    shutil.copy2(path, backup_path)
    return backup_path


def require_file_v1(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Ficheiro obrigatorio nao encontrado: {path}")


####################################################################################
# (3) REWRITE DO MACRO V2
####################################################################################

def build_macro_v1() -> str:
    return """{% macro render_admin_subprocess_v2(subprocess) %}
{% if subprocess %}
<div
  class="admin-subprocess-v2"
  id="admin-subprocess-v2-{{ subprocess.key }}"
  data-admin-subprocess-v2-root
  data-subprocess-key="{{ subprocess.key }}"
>
  {% if subprocess.flash_message %}
  <div class="admin-subprocess-v2-alert admin-subprocess-v2-alert-{{ subprocess.flash_category or 'success' }}">
    {{ subprocess.flash_message }}
  </div>
  {% endif %}

  {% if subprocess.tabs %}
  <div class="admin-subprocess-v2-card admin-subprocess-v2-tabs-card">
    <div class="admin-subprocess-v2-tabs" role="tablist" aria-label="{{ subprocess.label }}">
      {% for tab in subprocess.tabs %}
      <button
        type="button"
        class="admin-subprocess-v2-tab{% if tab.active %} active{% endif %}"
        data-admin-subprocess-v2-tab-trigger
        data-tab-key="{{ tab.key }}"
      >
        {{ tab.label }}
      </button>
      {% endfor %}
    </div>
  </div>
  {% endif %}

  {% if subprocess.primary_action %}
  <div class="admin-subprocess-v2-card admin-subprocess-v2-toolbar-card">
    <div class="admin-subprocess-v2-toolbar">
      <a
        href="{{ subprocess.primary_action.href or '#' }}"
        class="admin-subprocess-v2-create-button"
        {% if subprocess.primary_action.target %}data-target="{{ subprocess.primary_action.target }}"{% endif %}
      >
        {{ subprocess.primary_action.label }}
      </a>
    </div>
  </div>
  {% endif %}

  {% if subprocess.summary_sections %}
    {% for section in subprocess.summary_sections %}
    <div class="admin-subprocess-v2-card admin-subprocess-v2-summary-card">
      <div class="admin-subprocess-v2-section-header">
        <div class="admin-subprocess-v2-section-title-wrap">
          <h3 class="admin-subprocess-v2-section-title">{{ section.title }}</h3>
          {% if section.subtitle %}
          <div class="admin-subprocess-v2-section-subtitle">{{ section.subtitle }}</div>
          {% endif %}
        </div>

        {% if section.search %}
        <div class="admin-subprocess-v2-search">
          <input
            type="text"
            class="admin-subprocess-v2-search-input"
            placeholder="{{ section.search.placeholder or 'Procurar' }}"
            value="{{ section.search.value or '' }}"
          />
        </div>
        {% endif %}
      </div>

      {% if section.rows %}
      <div class="admin-subprocess-v2-table-wrap">
        <table class="admin-subprocess-v2-table admin-subprocess-v2-summary-table">
          <thead>
            <tr>
              {% for col in section.columns %}
              <th>{{ col.label }}</th>
              {% endfor %}
            </tr>
          </thead>
          <tbody>
            {% for row in section.rows %}
            <tr>
              {% for col in section.columns %}
                {% set cell_value = row.get(col.key, '') %}
                {% if col.key == 'status' %}
                <td>
                  <span class="admin-subprocess-v2-status-pill {% if (cell_value|string|lower) in ['inactive', 'inativo', 'inativa'] %}admin-subprocess-v2-status-pill-inactive{% else %}admin-subprocess-v2-status-pill-active{% endif %}">
                    {{ cell_value }}
                  </span>
                </td>
                {% elif col.key == 'actions' %}
                <td>
                  <div class="admin-subprocess-v2-actions">
                    {% for action in cell_value or [] %}
                    <a
                      href="{{ action.href or '#' }}"
                      class="admin-subprocess-v2-action-btn {% if action.kind == 'delete' %}admin-subprocess-v2-action-btn-delete{% endif %}"
                      title="{{ action.label or '' }}"
                    >
                      {{ action.icon or '•' }}
                    </a>
                    {% endfor %}
                  </div>
                </td>
                {% else %}
                <td>{{ cell_value }}</td>
                {% endif %}
              {% endfor %}
            </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>

      <div class="admin-subprocess-v2-summary-footer">
        <div class="admin-subprocess-v2-summary-footer-left">
          <label class="admin-subprocess-v2-summary-page-size-label">
            <select class="admin-subprocess-v2-summary-page-size-select">
              <option value="5" selected>5</option>
              <option value="10">10</option>
              <option value="25">25</option>
              <option value="50">50</option>
            </select>
            <span>entradas por página</span>
          </label>
        </div>

        <div class="admin-subprocess-v2-summary-footer-right">
          <button type="button" class="admin-subprocess-v2-pagination-btn" disabled>&lsaquo;</button>
          <span class="admin-subprocess-v2-pagination-page is-active">1</span>
          <button type="button" class="admin-subprocess-v2-pagination-btn" disabled>&rsaquo;</button>
        </div>
      </div>
      {% else %}
      <div class="admin-subprocess-v2-empty-state">
        {{ section.empty_message or 'Sem registos.' }}
      </div>

      <div class="admin-subprocess-v2-summary-footer">
        <div class="admin-subprocess-v2-summary-footer-left">
          <label class="admin-subprocess-v2-summary-page-size-label">
            <select class="admin-subprocess-v2-summary-page-size-select">
              <option value="5" selected>5</option>
              <option value="10">10</option>
              <option value="25">25</option>
              <option value="50">50</option>
            </select>
            <span>entradas por página</span>
          </label>
        </div>

        <div class="admin-subprocess-v2-summary-footer-right">
          <button type="button" class="admin-subprocess-v2-pagination-btn" disabled>&lsaquo;</button>
          <span class="admin-subprocess-v2-pagination-page is-active">1</span>
          <button type="button" class="admin-subprocess-v2-pagination-btn" disabled>&rsaquo;</button>
        </div>
      </div>
      {% endif %}
    </div>
    {% endfor %}
  {% endif %}

  {% if subprocess.list_sections %}
    {% for section in subprocess.list_sections %}
    <div class="admin-subprocess-v2-card admin-subprocess-v2-list-card">
      <div class="admin-subprocess-v2-section-header">
        <div class="admin-subprocess-v2-section-title-wrap">
          <h3 class="admin-subprocess-v2-section-title">{{ section.title }}</h3>
          {% if section.total is not none %}
          <div class="admin-subprocess-v2-list-total">Total: {{ section.total }}</div>
          {% endif %}
        </div>

        {% if section.search %}
        <div class="admin-subprocess-v2-search">
          <input
            type="text"
            class="admin-subprocess-v2-search-input"
            placeholder="{{ section.search.placeholder or 'Procurar' }}"
            value="{{ section.search.value or '' }}"
          />
        </div>
        {% endif %}
      </div>

      {% if section.rows %}
      <div class="admin-subprocess-v2-table-wrap">
        <table class="admin-subprocess-v2-table">
          <thead>
            <tr>
              {% for col in section.columns %}
              <th>{{ col.label }}</th>
              {% endfor %}
            </tr>
          </thead>
          <tbody>
            {% for row in section.rows %}
            <tr>
              {% for col in section.columns %}
                {% set cell_value = row.get(col.key, '') %}
                {% if col.key == 'status' %}
                <td>
                  <span class="admin-subprocess-v2-status-pill {% if (cell_value|string|lower) in ['inactive', 'inativo', 'inativa'] %}admin-subprocess-v2-status-pill-inactive{% else %}admin-subprocess-v2-status-pill-active{% endif %}">
                    {{ cell_value }}
                  </span>
                </td>
                {% elif col.key == 'actions' %}
                <td>
                  <div class="admin-subprocess-v2-actions">
                    {% for action in cell_value or [] %}
                    <a
                      href="{{ action.href or '#' }}"
                      class="admin-subprocess-v2-action-btn {% if action.kind == 'delete' %}admin-subprocess-v2-action-btn-delete{% endif %}"
                      title="{{ action.label or '' }}"
                    >
                      {{ action.icon or '•' }}
                    </a>
                    {% endfor %}
                  </div>
                </td>
                {% else %}
                <td>{{ cell_value }}</td>
                {% endif %}
              {% endfor %}
            </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
      {% else %}
      <div class="admin-subprocess-v2-empty-state">
        {{ section.empty_message or 'Sem registos.' }}
      </div>
      {% endif %}

      <div class="admin-subprocess-v2-list-footer">
        <div class="admin-subprocess-v2-list-footer-left">
          <label class="admin-subprocess-v2-page-size-label">
            <select class="admin-subprocess-v2-page-size-select">
              <option value="5" selected>5</option>
              <option value="10">10</option>
              <option value="25">25</option>
              <option value="50">50</option>
            </select>
            <span>entradas por página</span>
          </label>
        </div>

        <div class="admin-subprocess-v2-list-footer-right">
          <button type="button" class="admin-subprocess-v2-pagination-btn" disabled>&lsaquo;</button>
          <span class="admin-subprocess-v2-pagination-page is-active">1</span>
          <button type="button" class="admin-subprocess-v2-pagination-btn" disabled>&rsaquo;</button>
        </div>
      </div>
    </div>
    {% endfor %}
  {% endif %}
</div>
{% endif %}
{% endmacro %}
"""


def patch_macro_v1() -> None:
    content = build_macro_v1()
    write_text_v1(MACRO_PATH, content)


####################################################################################
# (4) REWRITE DO CSS V2
####################################################################################

def build_css_v1() -> str:
    return """
.admin-subprocess-v2 {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.admin-subprocess-v2-card {
  background: #f8fafc;
  border: 1px solid #c8d3e6;
  border-radius: 12px;
  padding: 14px;
}

.admin-subprocess-v2-tabs {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  border-bottom: 1px solid #c8d3e6;
  padding-bottom: 12px;
}

.admin-subprocess-v2-tab {
  border: 1px solid #c8d3e6;
  background: #ffffff;
  color: #1c3563;
  font-size: 12px;
  font-weight: 600;
  line-height: 1.2;
  border-radius: 8px;
  padding: 7px 14px;
  cursor: pointer;
}

.admin-subprocess-v2-tab.active {
  background: #1f5fbf;
  border-color: #1f5fbf;
  color: #ffffff;
}

.admin-subprocess-v2-toolbar {
  display: flex;
  align-items: center;
  justify-content: flex-start;
}

.admin-subprocess-v2-create-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 30px;
  padding: 6px 16px;
  border-radius: 6px;
  border: 1px solid #1f5fbf;
  background: #1f5fbf;
  color: #ffffff;
  text-decoration: none;
  font-size: 12px;
  font-weight: 700;
  line-height: 1.2;
}

.admin-subprocess-v2-create-button:hover {
  background: #194fa0;
  border-color: #194fa0;
  color: #ffffff;
}

.admin-subprocess-v2-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.admin-subprocess-v2-section-title-wrap {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.admin-subprocess-v2-section-title {
  margin: 0;
  color: #0f2850;
  font-size: 17px;
  line-height: 1.25;
  font-weight: 700;
}

.admin-subprocess-v2-section-subtitle,
.admin-subprocess-v2-list-total {
  color: #38527a;
  font-size: 12px;
  line-height: 1.35;
}

.admin-subprocess-v2-search {
  margin-left: auto;
}

.admin-subprocess-v2-search-input {
  width: 190px;
  max-width: 100%;
  height: 32px;
  border-radius: 18px;
  border: 1px solid #b7c7e2;
  background: #ffffff;
  padding: 0 14px;
  color: #1c3563;
  font-size: 12px;
  outline: none;
}

.admin-subprocess-v2-table-wrap {
  width: 100%;
  overflow-x: auto;
}

.admin-subprocess-v2-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 720px;
}

.admin-subprocess-v2-table th {
  text-align: left;
  color: #0f2850;
  font-size: 11px;
  line-height: 1.2;
  font-weight: 700;
  padding: 10px 12px;
  border-bottom: 1px solid #d5deed;
  text-transform: uppercase;
}

.admin-subprocess-v2-table td {
  color: #1c3563;
  font-size: 12px;
  line-height: 1.35;
  padding: 10px 12px;
  border-bottom: 1px solid #d5deed;
  vertical-align: middle;
}

.admin-subprocess-v2-actions {
  display: flex;
  gap: 6px;
  align-items: center;
}

.admin-subprocess-v2-action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 6px;
  border: 1px solid #b7c7e2;
  background: #edf3ff;
  color: #1f5fbf;
  text-decoration: none;
  font-size: 12px;
  font-weight: 700;
}

.admin-subprocess-v2-action-btn:hover {
  background: #dfeaff;
}

.admin-subprocess-v2-action-btn-delete {
  border-color: #efb7b7;
  background: #fff1f1;
  color: #c53030;
}

.admin-subprocess-v2-action-btn-delete:hover {
  background: #ffe3e3;
  border-color: #e59a9a;
  color: #a61e1e;
}

.admin-subprocess-v2-status-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 44px;
  height: 22px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  line-height: 1;
  border: 1px solid transparent;
}

.admin-subprocess-v2-status-pill-active {
  background: #dff4e8;
  border-color: #9bd0ae;
  color: #1f7a45;
}

.admin-subprocess-v2-status-pill-inactive {
  background: #fdeaea;
  border-color: #e3a2a2;
  color: #c53030;
}

.admin-subprocess-v2-empty-state {
  color: #5a6f91;
  font-size: 13px;
  line-height: 1.4;
  padding: 6px 0 10px 0;
}

.admin-subprocess-v2-summary-footer,
.admin-subprocess-v2-list-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding-top: 12px;
  flex-wrap: wrap;
}

.admin-subprocess-v2-summary-page-size-label,
.admin-subprocess-v2-page-size-label {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #5a6f91;
  font-size: 12px;
  line-height: 1.2;
}

.admin-subprocess-v2-summary-page-size-select,
.admin-subprocess-v2-page-size-select {
  min-width: 58px;
  height: 30px;
  border: 1px solid #b7c7e2;
  border-radius: 8px;
  background: #ffffff;
  color: #1c3563;
  font-size: 12px;
  padding: 0 8px;
}

.admin-subprocess-v2-summary-footer-right,
.admin-subprocess-v2-list-footer-right {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.admin-subprocess-v2-pagination-btn {
  width: 26px;
  height: 26px;
  border-radius: 999px;
  border: 1px solid #d5deed;
  background: #f3f6fb;
  color: #8aa0c2;
  font-size: 13px;
  cursor: pointer;
}

.admin-subprocess-v2-pagination-btn:disabled {
  opacity: 0.75;
  cursor: default;
}

.admin-subprocess-v2-pagination-page {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 999px;
  background: #ffffff;
  border: 1px solid #d5deed;
  color: #1c3563;
  font-size: 12px;
  font-weight: 700;
}

.admin-subprocess-v2-pagination-page.is-active {
  background: #1f5fbf;
  border-color: #1f5fbf;
  color: #ffffff;
}
"""


def patch_css_v1() -> None:
    content = build_css_v1().strip() + "\n"
    write_text_v1(CSS_PATH, content)


####################################################################################
# (5) VALIDAR
####################################################################################

def validate_v1() -> None:
    macro_content = read_text_v1(MACRO_PATH)
    css_content = read_text_v1(CSS_PATH)

    required_macro = [
        "admin-subprocess-v2-status-pill-inactive",
        "admin-subprocess-v2-action-btn-delete",
        "admin-subprocess-v2-summary-footer",
        "admin-subprocess-v2-summary-page-size-select",
        "admin-subprocess-v2-pagination-page is-active",
    ]

    required_css = [
        ".admin-subprocess-v2-status-pill-inactive",
        ".admin-subprocess-v2-action-btn-delete",
        ".admin-subprocess-v2-summary-footer",
        ".admin-subprocess-v2-summary-page-size-select",
        ".admin-subprocess-v2-pagination-page.is-active",
    ]

    missing_macro = [item for item in required_macro if item not in macro_content]
    missing_css = [item for item in required_css if item not in css_content]

    if missing_macro:
        raise RuntimeError("Marcadores ausentes no macro: " + ", ".join(missing_macro))

    if missing_css:
        raise RuntimeError("Marcadores ausentes no CSS: " + ", ".join(missing_css))

    print("OK: badge Inativo configurado para vermelho.")
    print("OK: botao delete/lixo configurado para vermelho.")
    print("OK: rodape com entradas por pagina e paginacao adicionado aos cards-resumo.")


####################################################################################
# (6) EXECUCAO
####################################################################################

def main() -> None:
    require_file_v1(MACRO_PATH)
    require_file_v1(CSS_PATH)

    macro_backup = backup_file_v1(MACRO_PATH, "summary_cards_status_and_pagination_v1")
    css_backup = backup_file_v1(CSS_PATH, "summary_cards_status_and_pagination_v1")

    print(f"OK: backup criado: {macro_backup}")
    print(f"OK: backup criado: {css_backup}")

    patch_macro_v1()
    patch_css_v1()
    validate_v1()

    print("OK: patch summary cards V2 concluido.")


if __name__ == "__main__":
    main()
