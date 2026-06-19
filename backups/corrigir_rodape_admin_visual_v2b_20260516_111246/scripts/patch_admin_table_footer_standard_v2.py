from pathlib import Path
import re

TEMPLATE_PATH = Path("templates/new_user.html")
MACRO_PATH = Path("templates/macros/admin_subprocess.html")
CSS_PATH = Path("static/css/modules/admin_table_footer_standard_v1.css")
JS_PATH = Path("static/js/modules/admin_table_footer_standard_v1.js")

CSS_LINK = '  <link rel="stylesheet" href="/static/css/modules/admin_table_footer_standard_v1.css?v=20260516-admin-table-footer-standard-v2">'
JS_LINK = '  <script src="/static/js/modules/admin_table_footer_standard_v1.js?v=20260516-admin-table-footer-standard-v2" defer></script>'

MACRO_FOOTER_BLOCK = '''      <!-- APPVERBO_ADMIN_SUBPROCESS_TABLE_FOOTER_STANDARD_V1_START -->
      <div
        class="table-limiter admin-subprocess-table-footer-v1"
        data-appverbo-table-limiter-v1
        data-appverbo-subprocess="{{ state.config.key }}"
        data-appverbo-status="{{ status_value }}"
      >
        <div class="table-limiter-left admin-subprocess-table-footer-left-v1">
          <select
            class="table-limiter-select admin-subprocess-page-size-v1"
            aria-label="Entradas por página ({{ title }})"
          >
            <option value="5" selected>5</option>
            <option value="10">10</option>
            <option value="20">20</option>
          </select>
          <span>entradas por página</span>
        </div>
        <div class="table-limiter-right admin-subprocess-table-footer-right-v1">
          <button
            class="table-limiter-nav-btn admin-subprocess-prev-v1"
            type="button"
            aria-label="Página anterior"
          >&#8249;</button>
          <span class="table-limiter-page admin-subprocess-page-v1">1</span>
          <button
            class="table-limiter-nav-btn admin-subprocess-next-v1"
            type="button"
            aria-label="Próxima página"
          >&#8250;</button>
        </div>
      </div>
      <!-- APPVERBO_ADMIN_SUBPROCESS_TABLE_FOOTER_STANDARD_V1_END -->
'''

CSS_CONTENT = '''/* APPVERBO_ADMIN_TABLE_FOOTER_STANDARD_V1_START */

/*
  Padrao global v2 do rodape de tabelas administrativas.
  Objetivo:
  - Entidade, Utilizador, Sessoes e Menu com o mesmo rodape.
  - Remover diferencas visuais entre subprocessos.
  - Impedir quebra de linha em "entradas por pagina".
  - Ocultar rodape legado de Sessoes para evitar duplicacao.
*/

/* Compatibilidade: esconder rodapes legados especificos de Sessoes. */
.appverbo-sessoes-entries-per-page-v1,
.appverbo_sessoes_entries_per_page_v1,
.appverbo-sessoes-entries-per-page-footer-v1,
.appverbo_sessoes_entries_per_page_footer_v1,
.sessoes-entries-per-page-footer-v1,
.sessoes_entries_per_page_footer_v1,
[data-appverbo-sessoes-entries-per-page-v1],
[data-sessoes-entries-per-page],
[data-sessoes-entries-per-page-v1] {
  display: none !important;
}

/* Container principal do rodape. */
.card .table-limiter,
.card .admin-status-table-footer-v1,
.card .admin-subprocess-table-footer-v1,
.table-limiter,
.admin-status-table-footer-v1,
.admin-subprocess-table-footer-v1 {
  width: 100% !important;
  min-width: 100% !important;
  max-width: 100% !important;
  margin: 10px 0 0 0 !important;
  padding: 0 !important;
  border-top: 0 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: space-between !important;
  gap: 12px !important;
  flex-direction: row !important;
  flex-wrap: nowrap !important;
  font-family: inherit !important;
  font-size: 14px !important;
  color: #5f6877 !important;
  line-height: 1.2 !important;
  box-sizing: border-box !important;
}

/* Lado esquerdo: select + texto. */
.card .table-limiter-left,
.card .admin-subprocess-table-footer-left-v1,
.table-limiter-left,
.admin-subprocess-table-footer-left-v1 {
  display: inline-flex !important;
  align-items: center !important;
  justify-content: flex-start !important;
  gap: 8px !important;
  flex: 0 0 auto !important;
  width: auto !important;
  min-width: 220px !important;
  max-width: none !important;
  color: #5f6877 !important;
  font-family: inherit !important;
  font-size: 14px !important;
  line-height: 1.2 !important;
  white-space: nowrap !important;
  box-sizing: border-box !important;
}

/* Utilizador usa select e span diretamente dentro do footer. */
.admin-status-table-footer-v1 > select {
  flex: 0 0 auto !important;
}

.admin-status-table-footer-v1 > span {
  display: inline-block !important;
  flex: 0 0 auto !important;
  width: auto !important;
  min-width: max-content !important;
  max-width: none !important;
  color: #5f6877 !important;
  font-family: inherit !important;
  font-size: 14px !important;
  line-height: 1.2 !important;
  white-space: nowrap !important;
}

/* Texto "entradas por pagina" nunca pode quebrar em duas linhas. */
.table-limiter-left span,
.admin-subprocess-table-footer-left-v1 span,
.table-limiter > span,
.admin-status-table-footer-v1 > span,
.admin-subprocess-table-footer-v1 > span {
  display: inline-block !important;
  width: auto !important;
  min-width: max-content !important;
  max-width: none !important;
  white-space: nowrap !important;
  overflow: visible !important;
  text-overflow: clip !important;
  color: #5f6877 !important;
  font-family: inherit !important;
  font-size: 14px !important;
  line-height: 1.2 !important;
}

/* Select padrao. */
.table-limiter-select,
.table-limiter select,
.admin-status-table-footer-v1 select,
.admin-subprocess-table-footer-v1 select {
  flex: 0 0 auto !important;
  width: auto !important;
  min-width: 84px !important;
  max-width: none !important;
  height: 34px !important;
  min-height: 34px !important;
  max-height: 34px !important;
  margin: 0 !important;
  padding: 0 10px !important;
  border: 1px solid #cfd5df !important;
  border-radius: 8px !important;
  background: #ffffff !important;
  color: #253046 !important;
  font-family: inherit !important;
  font-size: 14px !important;
  font-weight: 400 !important;
  line-height: 1.2 !important;
  box-sizing: border-box !important;
}

/* Lado direito: paginacao. */
.card .table-limiter-right,
.card .admin-subprocess-table-footer-right-v1,
.card .admin-status-table-footer-v1 .pagination,
.table-limiter-right,
.admin-subprocess-table-footer-right-v1,
.admin-status-table-footer-v1 .pagination {
  display: inline-flex !important;
  align-items: center !important;
  justify-content: flex-end !important;
  gap: 10px !important;
  flex: 0 0 auto !important;
  width: auto !important;
  min-width: 0 !important;
  max-width: none !important;
  margin-left: auto !important;
  white-space: nowrap !important;
  box-sizing: border-box !important;
}

/* Botoes de navegacao. */
.table-limiter-nav-btn,
.admin-status-table-footer-v1 .pagination button,
.admin-subprocess-table-footer-v1 .pagination button {
  width: 30px !important;
  min-width: 30px !important;
  max-width: 30px !important;
  height: 30px !important;
  min-height: 30px !important;
  max-height: 30px !important;
  margin: 0 !important;
  padding: 0 !important;
  border: 1px solid #d3dced !important;
  border-radius: 999px !important;
  background: transparent !important;
  color: #2f6db4 !important;
  font-family: inherit !important;
  font-size: 18px !important;
  font-weight: 700 !important;
  line-height: 1 !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  box-sizing: border-box !important;
  cursor: pointer !important;
}

.table-limiter-nav-btn:hover,
.admin-status-table-footer-v1 .pagination button:hover,
.admin-subprocess-table-footer-v1 .pagination button:hover {
  background: #eef3ff !important;
  color: #1f4eb7 !important;
  border-color: #becdf0 !important;
}

.table-limiter-nav-btn:disabled,
.admin-status-table-footer-v1 .pagination button:disabled,
.admin-subprocess-table-footer-v1 .pagination button:disabled {
  opacity: 0.4 !important;
  cursor: not-allowed !important;
  background: transparent !important;
  color: #7a879d !important;
  border-color: #d9dee8 !important;
}

/* Pagina atual. */
.table-limiter-page,
.admin-status-table-footer-v1 .pagination button.active,
.admin-subprocess-table-footer-v1 .pagination button.active {
  min-width: 30px !important;
  width: 30px !important;
  max-width: 30px !important;
  height: 30px !important;
  min-height: 30px !important;
  max-height: 30px !important;
  padding: 0 !important;
  border-radius: 999px !important;
  background: #2f6db4 !important;
  color: #ffffff !important;
  border: 1px solid #2f6db4 !important;
  font-family: inherit !important;
  font-size: 14px !important;
  font-weight: 700 !important;
  line-height: 1 !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  box-sizing: border-box !important;
}

/* Ajuste responsivo sem quebrar o texto. */
@media (max-width: 720px) {
  .card .table-limiter,
  .card .admin-status-table-footer-v1,
  .card .admin-subprocess-table-footer-v1,
  .table-limiter,
  .admin-status-table-footer-v1,
  .admin-subprocess-table-footer-v1 {
    align-items: flex-start !important;
    flex-direction: column !important;
    flex-wrap: nowrap !important;
  }

  .card .table-limiter-left,
  .card .admin-subprocess-table-footer-left-v1,
  .table-limiter-left,
  .admin-subprocess-table-footer-left-v1 {
    min-width: 0 !important;
  }

  .table-limiter-right,
  .admin-subprocess-table-footer-right-v1,
  .admin-status-table-footer-v1 .pagination {
    margin-left: 0 !important;
  }
}

/* APPVERBO_ADMIN_TABLE_FOOTER_STANDARD_V1_END */
'''

JS_CONTENT = '''// APPVERBO_ADMIN_TABLE_FOOTER_STANDARD_V1_START
(function () {
  "use strict";

  //###################################################################################
  // (1) IDENTIFICADORES GLOBAIS
  //###################################################################################

  const FOOTER_SELECTOR = [
    ".table-limiter",
    ".admin-status-table-footer-v1",
    ".admin-subprocess-table-footer-v1"
  ].join(",");

  const LEGACY_SESSOES_SELECTOR = [
    ".appverbo-sessoes-entries-per-page-v1",
    ".appverbo_sessoes_entries_per_page_v1",
    ".appverbo-sessoes-entries-per-page-footer-v1",
    ".appverbo_sessoes_entries_per_page_footer_v1",
    ".sessoes-entries-per-page-footer-v1",
    ".sessoes_entries_per_page_footer_v1",
    "[data-appverbo-sessoes-entries-per-page-v1]",
    "[data-sessoes-entries-per-page]",
    "[data-sessoes-entries-per-page-v1]"
  ].join(",");

  //###################################################################################
  // (2) TESTAR SE ELEMENTO E RODAPE PADRONIZADO
  //###################################################################################

  function elementoEhRodapeAdminTableFooterStandard_v2(elemento) {
    if (!elemento || !elemento.matches) {
      return false;
    }

    return elemento.matches(FOOTER_SELECTOR);
  }

  //###################################################################################
  // (3) REMOVER RODAPES LEGADOS DE SESSOES
  //###################################################################################

  function removerRodapesLegadosSessoesAdminTableFooterStandard_v2() {
    document.querySelectorAll(LEGACY_SESSOES_SELECTOR).forEach(function (elemento) {
      if (elemento.closest(".admin-subprocess-table-footer-v1")) {
        return;
      }

      elemento.remove();
    });
  }

  //###################################################################################
  // (4) LOCALIZAR TABELA DO RODAPE
  //###################################################################################

  function obterTabelaDoRodapeAdminTableFooterStandard_v2(footer) {
    let cursor = footer.previousElementSibling;

    while (cursor) {
      if (elementoEhRodapeAdminTableFooterStandard_v2(cursor)) {
        cursor = cursor.previousElementSibling;
        continue;
      }

      if (cursor.matches && cursor.matches("table")) {
        return cursor;
      }

      if (cursor.querySelector) {
        const tabelaInterna = cursor.querySelector("table");

        if (tabelaInterna) {
          return tabelaInterna;
        }
      }

      cursor = cursor.previousElementSibling;
    }

    return null;
  }

  //###################################################################################
  // (5) REMOVER RODAPES DUPLICADOS PARA A MESMA TABELA
  //###################################################################################

  function obterRodapePreferidoAdminTableFooterStandard_v2(rodapes) {
    const porSubprocesso = rodapes.find(function (footer) {
      return footer.classList.contains("admin-subprocess-table-footer-v1");
    });

    if (porSubprocesso) {
      return porSubprocesso;
    }

    const porTableLimiter = rodapes.find(function (footer) {
      return footer.classList.contains("table-limiter");
    });

    if (porTableLimiter) {
      return porTableLimiter;
    }

    return rodapes[0] || null;
  }

  function removerRodapesDuplicadosAdminTableFooterStandard_v2() {
    const mapa = new Map();

    document.querySelectorAll(FOOTER_SELECTOR).forEach(function (footer) {
      const tabela = obterTabelaDoRodapeAdminTableFooterStandard_v2(footer);

      if (!tabela) {
        return;
      }

      if (!mapa.has(tabela)) {
        mapa.set(tabela, []);
      }

      mapa.get(tabela).push(footer);
    });

    mapa.forEach(function (rodapes) {
      if (rodapes.length <= 1) {
        return;
      }

      const preferido = obterRodapePreferidoAdminTableFooterStandard_v2(rodapes);

      rodapes.forEach(function (footer) {
        if (footer !== preferido) {
          footer.remove();
        }
      });
    });
  }

  //###################################################################################
  // (6) LOCALIZAR CONTROLOS DO RODAPE
  //###################################################################################

  function obterControlesRodapeAdminTableFooterStandard_v2(footer) {
    const select = footer.querySelector("select");
    const botoes = Array.from(footer.querySelectorAll("button"));

    let botaoAnterior = footer.querySelector(".table-limiter-nav-btn:first-of-type");
    let botaoSeguinte = footer.querySelector(".table-limiter-nav-btn:last-of-type");

    if (!botaoAnterior && botoes.length > 0) {
      botaoAnterior = botoes[0];
    }

    if (!botaoSeguinte && botoes.length > 1) {
      botaoSeguinte = botoes[botoes.length - 1];
    }

    let paginaAtual = footer.querySelector(".table-limiter-page");

    if (!paginaAtual) {
      paginaAtual = footer.querySelector(".pagination .active");
    }

    return {
      select,
      botaoAnterior,
      botaoSeguinte,
      paginaAtual
    };
  }

  //###################################################################################
  // (7) NORMALIZAR TEXTO E OPCOES
  //###################################################################################

  function normalizarTextoRodapeAdminTableFooterStandard_v2(footer) {
    footer.querySelectorAll("span").forEach(function (span) {
      const textoNormalizado = (span.textContent || "").replace(/\\s+/g, " ").trim();

      if (textoNormalizado.toLowerCase() === "entradas por página") {
        span.textContent = "entradas por página";
      }
    });
  }

  function normalizarOpcoesSelectAdminTableFooterStandard_v2(select) {
    if (!select) {
      return;
    }

    const valoresPadrao = ["5", "10", "20"];
    const valorAtual = select.value || "5";
    const valoresExistentes = new Set();

    Array.from(select.options).forEach(function (option) {
      if (!option.value) {
        option.value = option.textContent.trim();
      }

      valoresExistentes.add(option.value);
    });

    valoresPadrao.forEach(function (valor) {
      if (!valoresExistentes.has(valor)) {
        const option = document.createElement("option");
        option.value = valor;
        option.textContent = valor;
        select.appendChild(option);
      }
    });

    if (valoresPadrao.includes(valorAtual)) {
      select.value = valorAtual;
    }
    else {
      select.value = "5";
    }
  }

  //###################################################################################
  // (8) APLICAR PAGINA NA TABELA
  //###################################################################################

  function aplicarPaginaAdminTableFooterStandard_v2(tabela, footer, estado) {
    const linhas = Array.from(tabela.querySelectorAll("tbody tr"));
    const controles = obterControlesRodapeAdminTableFooterStandard_v2(footer);

    estado.pageSize = Number.parseInt(controles.select ? controles.select.value : "5", 10) || 5;

    const totalPaginas = Math.max(1, Math.ceil(linhas.length / estado.pageSize));

    if (estado.page > totalPaginas) {
      estado.page = totalPaginas;
    }

    if (estado.page < 1) {
      estado.page = 1;
    }

    const inicio = (estado.page - 1) * estado.pageSize;
    const fim = inicio + estado.pageSize;

    linhas.forEach(function (linha, index) {
      linha.style.display = index >= inicio && index < fim ? "" : "none";
    });

    if (controles.paginaAtual) {
      controles.paginaAtual.textContent = String(estado.page);
    }

    if (controles.botaoAnterior) {
      controles.botaoAnterior.disabled = estado.page <= 1;
    }

    if (controles.botaoSeguinte) {
      controles.botaoSeguinte.disabled = estado.page >= totalPaginas;
    }
  }

  //###################################################################################
  // (9) INICIAR UM RODAPE
  //###################################################################################

  function iniciarRodapeAdminTableFooterStandard_v2(footer) {
    if (footer.dataset.appverboAdminTableFooterStandardReadyV2 === "1") {
      return;
    }

    const tabela = obterTabelaDoRodapeAdminTableFooterStandard_v2(footer);

    if (!tabela) {
      return;
    }

    const controles = obterControlesRodapeAdminTableFooterStandard_v2(footer);

    if (!controles.select) {
      return;
    }

    normalizarTextoRodapeAdminTableFooterStandard_v2(footer);
    normalizarOpcoesSelectAdminTableFooterStandard_v2(controles.select);

    const estado = {
      page: 1,
      pageSize: Number.parseInt(controles.select.value || "5", 10) || 5
    };

    footer.dataset.appverboAdminTableFooterStandardReadyV2 = "1";

    controles.select.addEventListener("change", function () {
      estado.page = 1;
      aplicarPaginaAdminTableFooterStandard_v2(tabela, footer, estado);
    });

    if (controles.botaoAnterior) {
      controles.botaoAnterior.addEventListener("click", function (event) {
        event.preventDefault();
        estado.page -= 1;
        aplicarPaginaAdminTableFooterStandard_v2(tabela, footer, estado);
      });
    }

    if (controles.botaoSeguinte) {
      controles.botaoSeguinte.addEventListener("click", function (event) {
        event.preventDefault();
        estado.page += 1;
        aplicarPaginaAdminTableFooterStandard_v2(tabela, footer, estado);
      });
    }

    aplicarPaginaAdminTableFooterStandard_v2(tabela, footer, estado);
  }

  //###################################################################################
  // (10) INSTALAR EM TODAS AS TABELAS ADMINISTRATIVAS
  //###################################################################################

  function instalarRodapesAdminTableFooterStandard_v2() {
    removerRodapesLegadosSessoesAdminTableFooterStandard_v2();
    removerRodapesDuplicadosAdminTableFooterStandard_v2();

    document.querySelectorAll(FOOTER_SELECTOR).forEach(function (footer) {
      iniciarRodapeAdminTableFooterStandard_v2(footer);
    });
  }

  //###################################################################################
  // (11) INICIAR
  //###################################################################################

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", instalarRodapesAdminTableFooterStandard_v2);
  }
  else {
    instalarRodapesAdminTableFooterStandard_v2();
  }

  window.addEventListener("load", instalarRodapesAdminTableFooterStandard_v2);
})();
// APPVERBO_ADMIN_TABLE_FOOTER_STANDARD_V1_END
'''

def read_text(path):
    return path.read_text(encoding="utf-8-sig")

def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")

def remove_asset_tags(text):
    patterns = [
        r'\s*<link\b[^>]*admin_table_footer_standard_v1\.css[^>]*>\s*\n?',
        r'\s*<script\b[^>]*admin_table_footer_standard_v1\.js[^>]*>\s*</script>\s*\n?',
        r'\s*<link\b[^>]*appverbo_sessoes_entries_per_page_v1\.css[^>]*>\s*\n?',
        r'\s*<script\b[^>]*appverbo_sessoes_entries_per_page_v1\.js[^>]*>\s*</script>\s*\n?',
    ]

    updated = text
    for pattern in patterns:
        updated = re.sub(pattern, "\n", updated, flags=re.IGNORECASE)

    updated = re.sub(r'\n{3,}', '\n\n', updated)
    return updated

def insert_before_last(text, needle, insertion):
    index = text.lower().rfind(needle.lower())
    if index == -1:
        return text.rstrip() + "\n" + insertion + "\n"
    return text[:index].rstrip() + "\n" + insertion + "\n" + text[index:]

def patch_template():
    text = read_text(TEMPLATE_PATH)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = remove_asset_tags(text)

    text = insert_before_last(text, "</head>", CSS_LINK)
    text = insert_before_last(text, "</body>", JS_LINK)

    write_text(TEMPLATE_PATH, text)
    print(f"OK: template atualizado: {TEMPLATE_PATH}")

def patch_macro():
    text = read_text(MACRO_PATH)
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    block_pattern = (
        r'\n?\s*<!-- APPVERBO_ADMIN_SUBPROCESS_TABLE_FOOTER_STANDARD_V1_START -->'
        r'.*?'
        r'<!-- APPVERBO_ADMIN_SUBPROCESS_TABLE_FOOTER_STANDARD_V1_END -->\s*'
    )
    text = re.sub(block_pattern, "\n", text, flags=re.DOTALL)

    needle = "      </div>\n    {% else %}"
    replacement = "      </div>\n" + MACRO_FOOTER_BLOCK + "    {% else %}"

    if needle not in text:
        raise SystemExit(f"ERRO: ponto de insercao nao encontrado em {MACRO_PATH}")

    text = text.replace(needle, replacement, 1)

    write_text(MACRO_PATH, text)
    print(f"OK: macro atualizado: {MACRO_PATH}")

def validate_no_mojibake(paths):
    suspicious = {
        0x00C3: "U+00C3",
        0x00C2: "U+00C2",
        0xFFFD: "U+FFFD",
    }

    found = False

    for path in paths:
        text = read_text(path)

        for line_number, line in enumerate(text.splitlines(), start=1):
            for char in line:
                if ord(char) in suspicious:
                    found = True
                    print(f"ERRO: {path} L{line_number}: {suspicious[ord(char)]}")
                    print(line)

    if found:
        raise SystemExit("ERRO: possivel mojibake encontrado.")

def validate_required_content():
    checks = {
        TEMPLATE_PATH: [
            "admin_table_footer_standard_v1.css?v=20260516-admin-table-footer-standard-v2",
            "admin_table_footer_standard_v1.js?v=20260516-admin-table-footer-standard-v2",
        ],
        MACRO_PATH: [
            "APPVERBO_ADMIN_SUBPROCESS_TABLE_FOOTER_STANDARD_V1_START",
            "admin-subprocess-table-footer-v1",
            "Entradas por página",
        ],
        CSS_PATH: [
            "APPVERBO_ADMIN_TABLE_FOOTER_STANDARD_V1_START",
            "min-width: 220px",
            "white-space: nowrap",
            "appverbo-sessoes-entries-per-page-footer-v1",
        ],
        JS_PATH: [
            "APPVERBO_ADMIN_TABLE_FOOTER_STANDARD_V1_START",
            "function removerRodapesLegadosSessoesAdminTableFooterStandard_v2",
            "function removerRodapesDuplicadosAdminTableFooterStandard_v2",
            "function instalarRodapesAdminTableFooterStandard_v2",
        ],
    }

    for path, markers in checks.items():
        text = read_text(path)
        for marker in markers:
            if marker not in text:
                raise SystemExit(f"ERRO: marcador nao encontrado em {path}: {marker}")
            print(f"OK: {path}: {marker}")

    template_text = read_text(TEMPLATE_PATH)

    if "appverbo_sessoes_entries_per_page_v1.js" in template_text:
        raise SystemExit("ERRO: template ainda referencia JS legado de entradas por pagina de Sessoes.")

    if "appverbo_sessoes_entries_per_page_v1.css" in template_text:
        raise SystemExit("ERRO: template ainda referencia CSS legado de entradas por pagina de Sessoes.")

    macro_text = read_text(MACRO_PATH)
    starts = macro_text.count("APPVERBO_ADMIN_SUBPROCESS_TABLE_FOOTER_STANDARD_V1_START")
    ends = macro_text.count("APPVERBO_ADMIN_SUBPROCESS_TABLE_FOOTER_STANDARD_V1_END")

    if starts != 1 or ends != 1:
        raise SystemExit(f"ERRO: macro deve conter 1 bloco padrao. Encontrado START={starts}, END={ends}")

    print("OK: referencias legadas removidas do template.")
    print("OK: macro contem apenas um bloco de rodape padrao.")

def main():
    patch_template()
    patch_macro()

    write_text(CSS_PATH, CSS_CONTENT)
    print(f"OK: CSS padrao v2 escrito: {CSS_PATH}")

    write_text(JS_PATH, JS_CONTENT)
    print(f"OK: JS padrao v2 escrito: {JS_PATH}")

    validate_required_content()
    validate_no_mojibake([TEMPLATE_PATH, MACRO_PATH, CSS_PATH, JS_PATH])

    print("OK: patch v2 aplicado e validado.")

if __name__ == "__main__":
    main()
