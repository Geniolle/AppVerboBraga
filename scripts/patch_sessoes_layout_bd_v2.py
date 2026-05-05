from pathlib import Path
import json
import os
import re
import sys
import time

from sqlalchemy import text

ROOT = Path.cwd()

TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
LAYOUT_JS_PATH = ROOT / "static" / "js" / "modules" / "sidebar_sections_layout_v1.js"
AUTOSAVE_JS_PATH = ROOT / "static" / "js" / "modules" / "sidebar_sections_autosave_v1.js"
CSS_PATH = ROOT / "static" / "css" / "modules" / "sidebar_sections_layout_v1.css"

BACKUP_NAME = os.environ.get("APPVERBO_SESSOES_BACKUP_NAME", "diagnostico_sessoes_bd_layout_v2_manual")
BACKUP_ROOT = ROOT / "backups" / BACKUP_NAME
BACKUP_ROOT.mkdir(parents=True, exist_ok=True)

CSS_HREF = "/static/css/modules/sidebar_sections_layout_v1.css?v=20260505-sessoes-db-v2"
SCRIPT_SRC = "/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-sessoes-db-v2"


def fail_v2(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) VALIDAR FICHEIROS
####################################################################################

if not TEMPLATE_PATH.exists():
    fail_v2(f"ficheiro não encontrado: {TEMPLATE_PATH}")

LAYOUT_JS_PATH.parent.mkdir(parents=True, exist_ok=True)
CSS_PATH.parent.mkdir(parents=True, exist_ok=True)


####################################################################################
# (2) DIAGNOSTICAR BD
####################################################################################

def importar_dependencias_bd_v2():
    sys.path.insert(0, str(ROOT))

    from appverbo.core import SessionLocal
    from appverbo.menu_settings import (
        MENU_CONFIG_SIDEBAR_SECTIONS_KEY,
        normalize_sidebar_sections,
    )

    return SessionLocal, MENU_CONFIG_SIDEBAR_SECTIONS_KEY, normalize_sidebar_sections


def parse_json_config_v2(raw_config):
    if isinstance(raw_config, dict):
        return raw_config

    try:
        parsed = json.loads(raw_config or "{}")
    except (TypeError, ValueError, json.JSONDecodeError):
        parsed = {}

    return parsed if isinstance(parsed, dict) else {}


def normalize_key_v2(value) -> str:
    return str(value or "").strip().lower()


def pretty_label_from_key_v2(value) -> str:
    clean_value = normalize_key_v2(value).replace("_", " ").strip()
    if not clean_value:
        return ""
    known_labels = {
        "sistema": "Sistema",
        "geral": "Geral",
        "dados_gerais": "Dados gerais",
        "igreja": "Igreja",
        "tesouraria": "Tesouraria",
    }
    return known_labels.get(normalize_key_v2(value), clean_value[:1].upper() + clean_value[1:])


def get_section_key_from_menu_config_v2(menu_key: str, menu_config: dict) -> str:
    for candidate_key in ("sidebar_section", "menu_section", "section_key", "section"):
        raw_value = menu_config.get(candidate_key)
        if normalize_key_v2(raw_value):
            return normalize_key_v2(raw_value)

    default_map = {
        "administrativo": "sistema",
        "home": "geral",
        "empresa": "dados_gerais",
        "meu_perfil": "igreja",
        "perfil": "igreja",
        "tesouraria": "tesouraria",
    }
    return default_map.get(normalize_key_v2(menu_key), "igreja")


def count_valid_raw_sections_v2(raw_sections) -> int:
    if not isinstance(raw_sections, list):
        return 0

    valid_count = 0

    for raw_section in raw_sections:
        if not isinstance(raw_section, dict):
            continue

        label = str(raw_section.get("label") or "").strip()
        key = str(raw_section.get("key") or "").strip()

        if label and key:
            valid_count += 1

    return valid_count


def diagnosticar_e_corrigir_bd_v2():
    SessionLocal, sidebar_sections_key, normalize_sidebar_sections = importar_dependencias_bd_v2()

    report = {
        "timestamp": int(time.time()),
        "table": "sidebar_menu_settings",
        "sidebar_sections_key": sidebar_sections_key,
        "admin_row_found": False,
        "valid_raw_sections_count": 0,
        "db_correction_applied": False,
        "db_correction_reason": "",
        "raw_admin_sidebar_sections": [],
        "normalized_sidebar_sections": [],
        "menu_rows": [],
    }

    with SessionLocal() as session:
        rows = session.execute(
            text(
                """
                SELECT *
                FROM sidebar_menu_settings
                """
            )
        ).mappings().all()

        admin_row = None
        recovered_seed_sections = []
        seen_recovered_keys = set()

        for row in rows:
            row_dict = dict(row)
            menu_key = normalize_key_v2(row_dict.get("menu_key") or row_dict.get("key"))
            menu_label = str(
                row_dict.get("menu_label")
                or row_dict.get("label")
                or menu_key
            ).strip()

            menu_config = parse_json_config_v2(row_dict.get("menu_config"))
            section_key = get_section_key_from_menu_config_v2(menu_key, menu_config)

            report["menu_rows"].append(
                {
                    "menu_key": menu_key,
                    "menu_label": menu_label,
                    "sidebar_section": section_key,
                    "menu_config_keys": sorted(menu_config.keys()),
                }
            )

            if section_key and section_key not in seen_recovered_keys:
                seen_recovered_keys.add(section_key)
                recovered_seed_sections.append(
                    {
                        "key": section_key,
                        "label": pretty_label_from_key_v2(section_key),
                        "visibility_scope_mode": menu_config.get("visibility_scope_mode") or "all",
                    }
                )

            if menu_key == "administrativo":
                admin_row = row_dict

        if admin_row is None:
            report["db_correction_reason"] = "Menu administrativo não encontrado no BD."
        else:
            report["admin_row_found"] = True
            admin_config = parse_json_config_v2(admin_row.get("menu_config"))
            raw_sections = admin_config.get(sidebar_sections_key)

            report["raw_admin_sidebar_sections"] = raw_sections if isinstance(raw_sections, list) else []
            report["valid_raw_sections_count"] = count_valid_raw_sections_v2(raw_sections)

            normalized_sections = normalize_sidebar_sections(raw_sections)
            report["normalized_sidebar_sections"] = normalized_sections

            if report["valid_raw_sections_count"] <= 0:
                recovered_sections = normalize_sidebar_sections(recovered_seed_sections)

                if recovered_sections:
                    admin_config[sidebar_sections_key] = recovered_sections
                    admin_config["sidebar_global_refresh_version"] = str(int(time.time() * 1000))

                    session.execute(
                        text(
                            """
                            UPDATE sidebar_menu_settings
                            SET menu_config = :menu_config
                            WHERE lower(trim(menu_key)) = :menu_key
                            """
                        ),
                        {
                            "menu_key": "administrativo",
                            "menu_config": json.dumps(admin_config, ensure_ascii=False),
                        },
                    )
                    session.commit()

                    report["db_correction_applied"] = True
                    report["db_correction_reason"] = (
                        "sidebar_sections no BD estava vazio ou sem label/key válidos; "
                        "foi reconstruído a partir das secções dos menus e dos defaults."
                    )
                    report["normalized_sidebar_sections"] = recovered_sections
                else:
                    report["db_correction_reason"] = (
                        "sidebar_sections inválido, mas não foi possível montar recuperação segura."
                    )
            else:
                report["db_correction_reason"] = (
                    "BD contém sessões válidas. O desaparecimento era de renderização no JS/layout."
                )

    report_path = BACKUP_ROOT / "diagnostico_sessoes_bd_v2.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    print("")
    print("===== DIAGNOSTICO BD SESSOES =====")
    print(f"Relatório: {report_path}")
    print(f"Menu administrativo encontrado: {report['admin_row_found']}")
    print(f"Sessões válidas no raw do BD: {report['valid_raw_sections_count']}")
    print(f"Correção no BD aplicada: {report['db_correction_applied']}")
    print(f"Motivo: {report['db_correction_reason']}")
    print("Sessões normalizadas:")
    for section in report["normalized_sidebar_sections"]:
        print(f" - {section.get('key')} | {section.get('label')} | {section.get('visibility_scope_mode')}")
    print("===== FIM DIAGNOSTICO BD SESSOES =====")
    print("")

    return report


####################################################################################
# (3) CONTEUDO JAVASCRIPT DO LAYOUT V2
####################################################################################

LAYOUT_JS_CONTENT = r'''(function () {
  "use strict";

  //###################################################################################
  // (1) NORMALIZACAO
  //###################################################################################

  function normalizarTextoSessoesLayout_v2(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function criarChaveSessoesLayout_v2(valor) {
    return normalizarTextoSessoesLayout_v2(valor)
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_+|_+$/g, "");
  }

  function tituloSessoesLayout_v2(valor, padrao) {
    const texto = String(valor || "").trim();
    return texto || padrao || "";
  }

  function labelPorChaveSessoesLayout_v2(chave) {
    const mapa = {
      sistema: "Sistema",
      geral: "Geral",
      dados_gerais: "Dados gerais",
      igreja: "Igreja",
      tesouraria: "Tesouraria"
    };

    const cleanChave = criarChaveSessoesLayout_v2(chave);

    if (mapa[cleanChave]) {
      return mapa[cleanChave];
    }

    return String(cleanChave || "nova_pasta")
      .replace(/_/g, " ")
      .replace(/^./, function (letra) {
        return letra.toUpperCase();
      });
  }

  //###################################################################################
  // (2) LER CONFIGURACAO VINDO DO BD
  //###################################################################################

  function lerSessoesDoTemplate_v2() {
    const script = document.getElementById("appverbo-sidebar-section-options-v2") ||
      document.getElementById("appverbo-sidebar-section-options-v1");

    if (!script) {
      return [];
    }

    try {
      const parsed = JSON.parse(script.textContent || "[]");
      return Array.isArray(parsed) ? parsed : [];
    } catch (error) {
      console.warn("Não foi possível ler sidebar_section_options do template.", error);
      return [];
    }
  }

  function normalizarSessaoSessoesLayout_v2(sessao) {
    if (!sessao || typeof sessao !== "object") {
      return null;
    }

    const label = tituloSessoesLayout_v2(
      sessao.label || sessao.name || sessao.title,
      ""
    );
    const key = criarChaveSessoesLayout_v2(
      sessao.key || sessao.section_key || sessao.menu_section || label
    );

    if (!label || !key) {
      return null;
    }

    return {
      key: key,
      label: label,
      visibility_scope_mode: tituloSessoesLayout_v2(
        sessao.visibility_scope_mode || sessao.scope_mode || sessao.scope || sessao.visibility,
        "all"
      ),
      visibility_scope_label: tituloSessoesLayout_v2(
        sessao.visibility_scope_label,
        ""
      )
    };
  }

  function obterSessoesBaseSessoesLayout_v2() {
    const sessoesDoBd = lerSessoesDoTemplate_v2()
      .map(normalizarSessaoSessoesLayout_v2)
      .filter(Boolean);

    if (sessoesDoBd.length) {
      return sessoesDoBd;
    }

    return [
      { key: "sistema", label: "Sistema", visibility_scope_mode: "all", visibility_scope_label: "Owner e Legado" },
      { key: "geral", label: "Geral", visibility_scope_mode: "all", visibility_scope_label: "Owner e Legado" },
      { key: "dados_gerais", label: "Dados gerais", visibility_scope_mode: "all", visibility_scope_label: "Owner e Legado" },
      { key: "igreja", label: "Igreja", visibility_scope_mode: "all", visibility_scope_label: "Owner e Legado" },
      { key: "tesouraria", label: "Tesouraria", visibility_scope_mode: "all", visibility_scope_label: "Owner e Legado" }
    ];
  }

  //###################################################################################
  // (3) LOCALIZAR CARD E FORMULARIO
  //###################################################################################

  function obterCardSessoesLayout_v2() {
    const cardPorId = document.getElementById("admin-sidebar-sections-card");

    if (cardPorId) {
      return cardPorId;
    }

    const cards = Array.from(document.querySelectorAll(".card, section"));

    return cards.find(function (card) {
      const texto = normalizarTextoSessoesLayout_v2(card.textContent);
      return texto.includes("sessoes do sidebar") || texto.includes("sessões do sidebar");
    }) || null;
  }

  function obterFormularioSessoesLayout_v2(card) {
    let formulario = card.querySelector('form[action*="/settings/menu/sidebar-sections"]') ||
      card.querySelector('form[action*="sidebar-sections"]');

    if (!formulario) {
      formulario = document.createElement("form");
      formulario.method = "post";
      formulario.action = "/settings/menu/sidebar-sections";
      card.appendChild(formulario);
    }

    formulario.method = "post";
    formulario.action = "/settings/menu/sidebar-sections";

    return formulario;
  }

  function criarCampoOcultoSessoesLayout_v2(nome, valor) {
    const input = document.createElement("input");
    input.type = "hidden";
    input.name = nome;
    input.value = valor || "";
    return input;
  }

  //###################################################################################
  // (4) SISTEMA, ESTADO E ACOES
  //###################################################################################

  function obterSistemaSessoesLayout_v2(sessao) {
    const scope = normalizarTextoSessoesLayout_v2(
      sessao.visibility_scope_mode || sessao.visibility_scope_label
    );

    if (scope === "owner") {
      return "Owner";
    }

    if (scope === "legado") {
      return "Legado";
    }

    return sessao.visibility_scope_label || "Owner e Legado";
  }

  function criarBotaoAcaoSessoesLayout_v2(tipo, titulo, texto) {
    const botao = document.createElement("button");
    botao.type = "button";
    botao.className = "appverbo-sidebar-section-action-btn-v2";
    botao.dataset.sidebarSectionActionV2 = tipo;
    botao.title = titulo;
    botao.setAttribute("aria-label", titulo);
    botao.textContent = texto;
    return botao;
  }

  function atualizarEstadoBotoesSessoesLayout_v2(tbody) {
    const linhas = Array.from(tbody.querySelectorAll("tr.appverbo-sidebar-section-row-v2"));

    linhas.forEach(function (linha, indice) {
      const botaoSubir = linha.querySelector('[data-sidebar-section-action-v2="up"]');
      const botaoDescer = linha.querySelector('[data-sidebar-section-action-v2="down"]');

      if (botaoSubir) {
        botaoSubir.disabled = indice === 0;
      }

      if (botaoDescer) {
        botaoDescer.disabled = indice === linhas.length - 1;
      }
    });
  }

  function marcarAlteradoSessoesLayout_v2(formulario) {
    const aviso = formulario.querySelector(".appverbo-sidebar-section-change-note-v2");

    formulario.dataset.sidebarSectionsChangedV2 = "1";

    if (aviso) {
      aviso.hidden = false;
    }
  }

  function sincronizarLinhaSessoesLayout_v2(linha) {
    const labelInput = linha.querySelector('[name="section_label"]');
    const keyInput = linha.querySelector('[name="section_key"]');
    const sistemaCell = linha.querySelector(".appverbo-sidebar-section-system-cell-v2");

    if (!labelInput || !keyInput) {
      return;
    }

    if (!String(keyInput.value || "").trim() || keyInput.dataset.generatedV2 === "1") {
      keyInput.value = criarChaveSessoesLayout_v2(labelInput.value);
      keyInput.dataset.generatedV2 = "1";
    }

    if (sistemaCell) {
      sistemaCell.textContent = obterSistemaSessoesLayout_v2({
        visibility_scope_mode: linha.dataset.visibilityScopeModeV2 || "all",
        visibility_scope_label: linha.dataset.visibilityScopeLabelV2 || ""
      });
    }
  }

  function atualizarDetalheSessoesLayout_v2(linha) {
    const detalhe = linha.nextElementSibling;

    if (!detalhe || !detalhe.classList.contains("appverbo-sidebar-section-detail-row-v2")) {
      return;
    }

    const keyInput = linha.querySelector('[name="section_key"]');
    const labelInput = linha.querySelector('[name="section_label"]');
    const scopeInput = linha.querySelector('[name="section_visibility_scope_mode"]');
    const texto = detalhe.querySelector(".appverbo-sidebar-section-detail-text-v2");

    if (!texto) {
      return;
    }

    texto.textContent =
      "Chave: " +
      tituloSessoesLayout_v2(keyInput && keyInput.value, criarChaveSessoesLayout_v2(labelInput && labelInput.value)) +
      " | Visibilidade: " +
      tituloSessoesLayout_v2(scopeInput && scopeInput.value, "all");
  }

  function moverLinhaSessoesLayout_v2(linha, direcao) {
    const tbody = linha && linha.parentElement;

    if (!tbody) {
      return;
    }

    const detalhe = linha.nextElementSibling &&
      linha.nextElementSibling.classList.contains("appverbo-sidebar-section-detail-row-v2")
      ? linha.nextElementSibling
      : null;

    if (direcao === "up") {
      const detalheAnterior = linha.previousElementSibling;
      const linhaAnterior = detalheAnterior && detalheAnterior.classList.contains("appverbo-sidebar-section-detail-row-v2")
        ? detalheAnterior.previousElementSibling
        : detalheAnterior;

      if (linhaAnterior && linhaAnterior.classList.contains("appverbo-sidebar-section-row-v2")) {
        tbody.insertBefore(linha, linhaAnterior);
        if (detalhe) {
          tbody.insertBefore(detalhe, linha.nextElementSibling);
        }
      }
    }

    if (direcao === "down") {
      const proximaLinha = detalhe ? detalhe.nextElementSibling : linha.nextElementSibling;

      if (proximaLinha && proximaLinha.classList.contains("appverbo-sidebar-section-row-v2")) {
        const proximoDetalhe = proximaLinha.nextElementSibling &&
          proximaLinha.nextElementSibling.classList.contains("appverbo-sidebar-section-detail-row-v2")
          ? proximaLinha.nextElementSibling
          : null;

        tbody.insertBefore(proximaLinha, linha);
        if (proximoDetalhe) {
          tbody.insertBefore(proximoDetalhe, linha);
        }
      }
    }

    atualizarEstadoBotoesSessoesLayout_v2(tbody);
    marcarAlteradoSessoesLayout_v2(linha.closest("form"));
  }

  function alternarDetalheSessoesLayout_v2(linha) {
    const detalhe = linha.nextElementSibling;

    if (!detalhe || !detalhe.classList.contains("appverbo-sidebar-section-detail-row-v2")) {
      return;
    }

    atualizarDetalheSessoesLayout_v2(linha);
    detalhe.hidden = !detalhe.hidden;
  }

  function editarLinhaSessoesLayout_v2(linha) {
    const labelInput = linha.querySelector('[name="section_label"]');

    if (!labelInput) {
      return;
    }

    labelInput.readOnly = false;
    labelInput.classList.add("appverbo-sidebar-section-label-input-editing-v2");
    labelInput.focus();
    labelInput.select();
  }

  //###################################################################################
  // (5) CRIAR TABELA
  //###################################################################################

  function criarLinhaTabelaSessoesLayout_v2(sessao) {
    const tr = document.createElement("tr");
    tr.className = "appverbo-sidebar-section-row-v2";
    tr.dataset.visibilityScopeModeV2 = sessao.visibility_scope_mode || "all";
    tr.dataset.visibilityScopeLabelV2 = sessao.visibility_scope_label || "";

    const keyInput = criarCampoOcultoSessoesLayout_v2("section_key", sessao.key);
    const scopeInput = criarCampoOcultoSessoesLayout_v2("section_visibility_scope_mode", sessao.visibility_scope_mode || "all");

    const labelInput = document.createElement("input");
    labelInput.type = "text";
    labelInput.name = "section_label";
    labelInput.value = sessao.label;
    labelInput.readOnly = true;
    labelInput.className = "appverbo-sidebar-section-label-input-v2";

    const tdMenu = document.createElement("td");
    tdMenu.className = "appverbo-sidebar-section-menu-cell-v2";
    tdMenu.appendChild(labelInput);
    tdMenu.appendChild(keyInput);
    tdMenu.appendChild(scopeInput);

    const tdSistema = document.createElement("td");
    tdSistema.className = "appverbo-sidebar-section-system-cell-v2";
    tdSistema.textContent = obterSistemaSessoesLayout_v2(sessao);

    const tdEstado = document.createElement("td");
    tdEstado.className = "appverbo-sidebar-section-state-cell-v2";

    const badge = document.createElement("span");
    badge.className = "appverbo-sidebar-section-state-badge-v2";
    badge.textContent = "Ativo";
    tdEstado.appendChild(badge);

    const tdAcoes = document.createElement("td");
    tdAcoes.className = "appverbo-sidebar-section-actions-cell-v2";

    const actions = document.createElement("div");
    actions.className = "appverbo-sidebar-section-actions-v2";
    actions.appendChild(criarBotaoAcaoSessoesLayout_v2("up", "Subir sessão", "↑"));
    actions.appendChild(criarBotaoAcaoSessoesLayout_v2("down", "Descer sessão", "↓"));
    actions.appendChild(criarBotaoAcaoSessoesLayout_v2("view", "Visualizar detalhes", "👁"));
    actions.appendChild(criarBotaoAcaoSessoesLayout_v2("edit", "Editar sessão", "✎"));

    tdAcoes.appendChild(actions);

    tr.appendChild(tdMenu);
    tr.appendChild(tdSistema);
    tr.appendChild(tdEstado);
    tr.appendChild(tdAcoes);

    const detalhe = document.createElement("tr");
    detalhe.className = "appverbo-sidebar-section-detail-row-v2";
    detalhe.hidden = true;

    const detalheCelula = document.createElement("td");
    detalheCelula.colSpan = 4;

    const detalheTexto = document.createElement("div");
    detalheTexto.className = "appverbo-sidebar-section-detail-text-v2";
    detalheCelula.appendChild(detalheTexto);
    detalhe.appendChild(detalheCelula);

    labelInput.addEventListener("input", function () {
      sincronizarLinhaSessoesLayout_v2(tr);
      atualizarDetalheSessoesLayout_v2(tr);
      marcarAlteradoSessoesLayout_v2(tr.closest("form"));
    });

    labelInput.addEventListener("blur", function () {
      labelInput.readOnly = true;
      labelInput.classList.remove("appverbo-sidebar-section-label-input-editing-v2");
      sincronizarLinhaSessoesLayout_v2(tr);
      atualizarDetalheSessoesLayout_v2(tr);
    });

    atualizarDetalheSessoesLayout_v2(tr);

    return {
      row: tr,
      detailRow: detalhe
    };
  }

  function criarTabelaSessoesLayout_v2(formulario, sessoes) {
    const wrapper = document.createElement("div");
    wrapper.className = "appverbo-sidebar-sections-layout-v2";

    const cabecalho = document.createElement("div");
    cabecalho.className = "appverbo-sidebar-sections-header-v2";

    const tituloBloco = document.createElement("div");
    tituloBloco.className = "appverbo-sidebar-sections-title-block-v2";

    const titulo = document.createElement("h2");
    titulo.textContent = "Definições";

    const descricao = document.createElement("p");
    descricao.textContent = "Ative os processos do menu lateral. Um menu só aparece quando estiver ativo aqui.";

    tituloBloco.appendChild(titulo);
    tituloBloco.appendChild(descricao);

    const criarBtn = document.createElement("button");
    criarBtn.type = "button";
    criarBtn.className = "appverbo-sidebar-section-create-btn-v2";
    criarBtn.textContent = "Criar pasta";

    cabecalho.appendChild(tituloBloco);
    cabecalho.appendChild(criarBtn);

    const tableWrap = document.createElement("div");
    tableWrap.className = "appverbo-sidebar-sections-table-wrap-v2";

    const table = document.createElement("table");
    table.className = "appverbo-sidebar-sections-table-v2";

    const thead = document.createElement("thead");
    thead.innerHTML = "<tr><th>MENU LATERAL</th><th>SISTEMA</th><th>ESTADO</th><th>AÇÕES</th></tr>";

    const tbody = document.createElement("tbody");
    tbody.className = "appverbo-sidebar-sections-body-v2";

    sessoes.forEach(function (sessao) {
      const linha = criarLinhaTabelaSessoesLayout_v2(sessao);
      tbody.appendChild(linha.row);
      tbody.appendChild(linha.detailRow);
    });

    table.appendChild(thead);
    table.appendChild(tbody);
    tableWrap.appendChild(table);

    const footer = document.createElement("div");
    footer.className = "appverbo-sidebar-sections-footer-v2";

    const nota = document.createElement("p");
    nota.className = "appverbo-sidebar-section-change-note-v2";
    nota.hidden = true;
    nota.textContent = "Existem alterações por gravar.";

    const gravar = document.createElement("button");
    gravar.type = "submit";
    gravar.className = "action-btn";
    gravar.textContent = "Gravar alterações";

    footer.appendChild(nota);
    footer.appendChild(gravar);

    wrapper.appendChild(criarCampoOcultoSessoesLayout_v2("redirect_menu", "administrativo"));
    wrapper.appendChild(criarCampoOcultoSessoesLayout_v2("redirect_target", "#admin-sidebar-sections-card"));
    wrapper.appendChild(cabecalho);
    wrapper.appendChild(tableWrap);
    wrapper.appendChild(footer);

    criarBtn.addEventListener("click", function () {
      const contador = tbody.querySelectorAll("tr.appverbo-sidebar-section-row-v2").length + 1;
      const novaSessao = {
        key: "nova_pasta_" + contador,
        label: "Nova pasta",
        visibility_scope_mode: "all",
        visibility_scope_label: "Owner e Legado"
      };

      const linha = criarLinhaTabelaSessoesLayout_v2(novaSessao);
      const keyInput = linha.row.querySelector('[name="section_key"]');

      if (keyInput) {
        keyInput.dataset.generatedV2 = "1";
      }

      tbody.appendChild(linha.row);
      tbody.appendChild(linha.detailRow);
      atualizarEstadoBotoesSessoesLayout_v2(tbody);
      editarLinhaSessoesLayout_v2(linha.row);
      marcarAlteradoSessoesLayout_v2(formulario);
    });

    tbody.addEventListener("click", function (event) {
      const botao = event.target.closest("[data-sidebar-section-action-v2]");

      if (!botao) {
        return;
      }

      const acao = botao.dataset.sidebarSectionActionV2;
      const linha = botao.closest("tr.appverbo-sidebar-section-row-v2");

      if (!linha) {
        return;
      }

      if (acao === "up" || acao === "down") {
        moverLinhaSessoesLayout_v2(linha, acao);
      }

      if (acao === "view") {
        alternarDetalheSessoesLayout_v2(linha);
      }

      if (acao === "edit") {
        editarLinhaSessoesLayout_v2(linha);
      }
    });

    atualizarEstadoBotoesSessoesLayout_v2(tbody);

    return wrapper;
  }

  //###################################################################################
  // (6) INSTALAR LAYOUT
  //###################################################################################

  function instalarLayoutSessoes_v2() {
    const card = obterCardSessoesLayout_v2();

    if (!card || card.dataset.sidebarSectionsLayoutV2 === "1") {
      return;
    }

    const formulario = obterFormularioSessoesLayout_v2(card);
    const sessoes = obterSessoesBaseSessoesLayout_v2();

    if (!sessoes.length) {
      return;
    }

    card.dataset.sidebarSectionsLayoutV2 = "1";
    card.classList.add("appverbo-sidebar-sections-card-v2");

    Array.from(card.querySelectorAll(".appverbo-sidebar-sections-layout-v1, .appverbo-sidebar-sections-layout-v2"))
      .forEach(function (elemento) {
        elemento.remove();
      });

    while (formulario.firstChild) {
      formulario.removeChild(formulario.firstChild);
    }

    formulario.appendChild(criarTabelaSessoesLayout_v2(formulario, sessoes));
  }

  function iniciarSessoesLayout_v2() {
    instalarLayoutSessoes_v2();

    window.setTimeout(instalarLayoutSessoes_v2, 100);
    window.setTimeout(instalarLayoutSessoes_v2, 300);
    window.setTimeout(instalarLayoutSessoes_v2, 700);

    document.addEventListener("click", function () {
      window.setTimeout(instalarLayoutSessoes_v2, 50);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciarSessoesLayout_v2);
  } else {
    iniciarSessoesLayout_v2();
  }
})();
'''


####################################################################################
# (4) CONTEUDO JAVASCRIPT NOOP PARA AUTOSAVE ANTIGO
####################################################################################

AUTOSAVE_JS_CONTENT = r'''(function () {
  "use strict";

  //###################################################################################
  // (1) AUTOSAVE ANTIGO DESATIVADO
  //###################################################################################

  function sidebarSectionsAutosaveDesativado_v2() {
    window.APPVERBO_SIDEBAR_SECTIONS_AUTOSAVE_DISABLED_V2 = true;
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", sidebarSectionsAutosaveDesativado_v2);
  } else {
    sidebarSectionsAutosaveDesativado_v2();
  }
})();
'''


####################################################################################
# (5) CONTEUDO CSS
####################################################################################

CSS_CONTENT = r'''/* APPVERBO_SIDEBAR_SECTIONS_LAYOUT_V2_START */

.appverbo-sidebar-sections-card-v2 {
  overflow: hidden;
}

.appverbo-sidebar-sections-layout-v2 {
  width: 100%;
}

.appverbo-sidebar-sections-header-v2 {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
}

.appverbo-sidebar-sections-title-block-v2 h2 {
  margin: 0 0 8px;
  font-size: 20px;
}

.appverbo-sidebar-sections-title-block-v2 p {
  margin: 0;
  color: #52607a;
  font-size: 13px;
}

.appverbo-sidebar-section-create-btn-v2 {
  border: 1px solid #b9cef4;
  background: #edf4ff;
  color: #153f8f;
  font-weight: 700;
  border-radius: 5px;
  padding: 8px 12px;
  cursor: pointer;
  white-space: nowrap;
}

.appverbo-sidebar-section-create-btn-v2:hover {
  background: #dceaff;
}

.appverbo-sidebar-sections-table-wrap-v2 {
  width: 100%;
  overflow-x: auto;
}

.appverbo-sidebar-sections-table-v2 {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.appverbo-sidebar-sections-table-v2 th {
  color: #243557;
  font-size: 10px;
  font-weight: 700;
  text-align: left;
  text-transform: uppercase;
  padding: 10px 6px;
  border-bottom: 1px solid #d5dceb;
}

.appverbo-sidebar-sections-table-v2 td {
  padding: 8px 6px;
  border-bottom: 1px solid #d5dceb;
  vertical-align: middle;
  font-size: 12px;
}

.appverbo-sidebar-sections-table-v2 th:nth-child(1),
.appverbo-sidebar-sections-table-v2 td:nth-child(1) {
  width: 34%;
}

.appverbo-sidebar-sections-table-v2 th:nth-child(2),
.appverbo-sidebar-sections-table-v2 td:nth-child(2) {
  width: 36%;
}

.appverbo-sidebar-sections-table-v2 th:nth-child(3),
.appverbo-sidebar-sections-table-v2 td:nth-child(3) {
  width: 16%;
}

.appverbo-sidebar-sections-table-v2 th:nth-child(4),
.appverbo-sidebar-sections-table-v2 td:nth-child(4) {
  width: 14%;
  text-align: right;
}

.appverbo-sidebar-section-label-input-v2 {
  width: 100%;
  border: 1px solid transparent;
  background: transparent;
  color: #12213a;
  font-size: 12px;
  padding: 6px;
  border-radius: 5px;
}

.appverbo-sidebar-section-label-input-v2:read-only {
  cursor: default;
}

.appverbo-sidebar-section-label-input-editing-v2,
.appverbo-sidebar-section-label-input-v2:focus {
  border-color: #b9cef4;
  background: #ffffff;
  outline: none;
  box-shadow: 0 0 0 2px rgba(36, 84, 176, 0.12);
}

.appverbo-sidebar-section-state-badge-v2 {
  display: inline-flex;
  align-items: center;
  border: 1px solid #9fd9b6;
  background: #e7f8ed;
  color: #04743a;
  border-radius: 999px;
  padding: 3px 8px;
  font-size: 11px;
  font-weight: 700;
}

.appverbo-sidebar-section-actions-v2 {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
  white-space: nowrap;
}

.appverbo-sidebar-section-action-btn-v2 {
  width: 28px;
  height: 28px;
  border: 1px solid #c2d4f7;
  background: #eef5ff;
  color: #1d4f9f;
  border-radius: 7px;
  font-size: 14px;
  line-height: 1;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.appverbo-sidebar-section-action-btn-v2:hover:not(:disabled) {
  background: #dceaff;
}

.appverbo-sidebar-section-action-btn-v2:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.appverbo-sidebar-section-detail-row-v2 td {
  background: #f8fbff;
  color: #52607a;
  font-size: 12px;
  padding: 10px 8px;
}

.appverbo-sidebar-sections-footer-v2 {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 14px;
}

.appverbo-sidebar-section-change-note-v2 {
  margin: 0;
  color: #8a5a00;
  font-size: 12px;
}

@media (max-width: 900px) {
  .appverbo-sidebar-sections-header-v2 {
    flex-direction: column;
    align-items: stretch;
  }

  .appverbo-sidebar-sections-table-v2 {
    min-width: 760px;
  }
}

/* APPVERBO_SIDEBAR_SECTIONS_LAYOUT_V2_END */
'''


####################################################################################
# (6) FUNCOES DE TEMPLATE
####################################################################################

def inserir_css_v2(template: str) -> str:
    if "sidebar_sections_layout_v1.css" in template:
        return re.sub(
            r'/static/css/modules/sidebar_sections_layout_v1\.css\?v=[^"]+',
            CSS_HREF,
            template,
        )

    css_link = f'  <link rel="stylesheet" href="{CSS_HREF}">\n'
    anchor = re.search(
        r'(?m)^.*<link rel="stylesheet" href="/static/css/modules/configurable_items_manager_v1\.css[^"]*">.*\n?',
        template,
    )

    if anchor:
        return template[:anchor.end()] + css_link + template[anchor.end():]

    head_end = template.find("{% endblock %}")
    if head_end == -1:
        fail_v2("não encontrei bloco para inserir CSS.")

    return template[:head_end] + css_link + template[head_end:]


def inserir_json_sessoes_v2(template: str) -> str:
    marker_start = "<!-- APPVERBO_SIDEBAR_SECTIONS_JSON_V2_START -->"
    marker_end = "<!-- APPVERBO_SIDEBAR_SECTIONS_JSON_V2_END -->"

    json_block = f'''        {marker_start}
        <script id="appverbo-sidebar-section-options-v2" type="application/json">{{{{ sidebar_section_options|default([])|tojson }}}}</script>
        {marker_end}
'''

    pattern = re.compile(
        re.escape(marker_start) + r"[\s\S]*?" + re.escape(marker_end),
        re.S,
    )

    if marker_start in template:
        return pattern.sub(json_block.strip(), template)

    menu_tabs_pattern = re.compile(
        r'(?P<tabs><section id="menu-tabs-card"[\s\S]*?</section>\s*)',
        re.S,
    )

    match = menu_tabs_pattern.search(template)
    if match:
        return template[:match.end("tabs")] + "\n" + json_block + template[match.end("tabs"):]

    dynamic_anchor = '<section id="dynamic-process-card"'
    if dynamic_anchor in template:
        return template.replace(dynamic_anchor, json_block + "        " + dynamic_anchor, 1)

    fail_v2("não encontrei local para inserir JSON das sessões.")
    return template


def inserir_js_v2(template: str) -> str:
    if "sidebar_sections_layout_v1.js" in template:
        return re.sub(
            r'/static/js/modules/sidebar_sections_layout_v1\.js\?v=[^"]+',
            SCRIPT_SRC,
            template,
        )

    script_tag = f'<script src="{SCRIPT_SRC}"></script>'

    scripts_block_pattern = re.compile(
        r"(?P<start>\{% block scripts %\}[\s\S]*?)(?P<end>\n\{% endblock %\})",
        re.S,
    )

    match = scripts_block_pattern.search(template)

    if match:
        return (
            template[:match.end("start")]
            + "\n  "
            + script_tag
            + template[match.end("start"):]
        )

    return template.rstrip() + "\n\n{% block scripts %}\n  " + script_tag + "\n{% endblock %}\n"


####################################################################################
# (7) EXECUTAR DIAGNOSTICO E PATCH
####################################################################################

diagnosticar_e_corrigir_bd_v2()

template = TEMPLATE_PATH.read_text(encoding="utf-8")
template = inserir_css_v2(template)
template = inserir_json_sessoes_v2(template)
template = inserir_js_v2(template)

TEMPLATE_PATH.write_text(template, encoding="utf-8")
LAYOUT_JS_PATH.write_text(LAYOUT_JS_CONTENT, encoding="utf-8")
AUTOSAVE_JS_PATH.write_text(AUTOSAVE_JS_CONTENT, encoding="utf-8")
CSS_PATH.write_text(CSS_CONTENT, encoding="utf-8")


####################################################################################
# (8) VALIDAR CONTEUDO
####################################################################################

template_validado = TEMPLATE_PATH.read_text(encoding="utf-8")
layout_js_validado = LAYOUT_JS_PATH.read_text(encoding="utf-8")
autosave_js_validado = AUTOSAVE_JS_PATH.read_text(encoding="utf-8")
css_validado = CSS_PATH.read_text(encoding="utf-8")

if "appverbo-sidebar-section-options-v2" not in template_validado:
    fail_v2("JSON sidebar_section_options não foi incluído no template.")

if SCRIPT_SRC not in template_validado:
    fail_v2("JS sidebar_sections_layout_v1 com cache v2 não foi incluído no template.")

if CSS_HREF not in template_validado:
    fail_v2("CSS sidebar_sections_layout_v1 com cache v2 não foi incluído no template.")

if "function instalarLayoutSessoes_v2" not in layout_js_validado:
    fail_v2("função instalarLayoutSessoes_v2 não foi criada no JS.")

if "sidebarSectionsAutosaveDesativado_v2" not in autosave_js_validado:
    fail_v2("autosave antigo não foi desativado.")

if "APPVERBO_SIDEBAR_SECTIONS_LAYOUT_V2_START" not in css_validado:
    fail_v2("marcador CSS V2 não foi criado.")

print("OK: diagnóstico do BD concluído.")
print("OK: template atualizado para expor sidebar_section_options vindo do BD.")
print("OK: JS layout V2 renderiza sessões a partir do BD.")
print("OK: autosave antigo foi desativado para não gravar linha vazia.")
print("OK: CSS V2 atualizado.")
