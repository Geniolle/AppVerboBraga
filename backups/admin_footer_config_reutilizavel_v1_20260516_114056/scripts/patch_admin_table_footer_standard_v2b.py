from pathlib import Path
import re

TEMPLATE_PATH = Path("templates/new_user.html")
MACRO_PATH = Path("templates/macros/admin_subprocess.html")
CSS_PATH = Path("static/css/modules/admin_table_footer_standard_v1.css")
JS_PATH = Path("static/js/modules/admin_table_footer_standard_v1.js")

CSS_LINK = '  <link rel="stylesheet" href="/static/css/modules/admin_table_footer_standard_v1.css?v=20260516-admin-table-footer-standard-v2b">'
JS_LINK = '  <script src="/static/js/modules/admin_table_footer_standard_v1.js?v=20260516-admin-table-footer-standard-v2b" defer></script>'

FOOTER_BLOCK = '''      <!-- APPVERBO_ADMIN_SUBPROCESS_TABLE_FOOTER_STANDARD_V1_START -->
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
  Padrao global v2b do rodape de tabelas administrativas.
  Corrige:
  - Sessoes duplicado.
  - Menu com "entradas por pagina" quebrando linha.
  - Diferencas de largura e fonte entre Entidade, Utilizador, Sessoes e Menu.
*/

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

.card .table-limiter,
.card .admin-status-table-footer-v1,
.card .admin-subprocess-table-footer-v1,
.table-limiter,
.admin-status-table-footer-v1,
.admin-subprocess-table-footer-v1 {
  width: 100% !important;
  min-width: 100% !important;
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
  min-width: 230px !important;
  color: #5f6877 !important;
  font-family: inherit !important;
  font-size: 14px !important;
  line-height: 1.2 !important;
  white-space: nowrap !important;
  box-sizing: border-box !important;
}

.admin-status-table-footer-v1 > select {
  flex: 0 0 auto !important;
}

.admin-status-table-footer-v1 > span,
.table-limiter-left span,
.admin-subprocess-table-footer-left-v1 span,
.table-limiter > span,
.admin-subprocess-table-footer-v1 > span {
  display: inline-block !important;
  flex: 0 0 auto !important;
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
  margin-left: auto !important;
  white-space: nowrap !important;
  box-sizing: border-box !important;
}

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

.table-limiter-nav-btn:disabled,
.admin-status-table-footer-v1 .pagination button:disabled,
.admin-subprocess-table-footer-v1 .pagination button:disabled {
  opacity: 0.4 !important;
  cursor: not-allowed !important;
  background: transparent !important;
  color: #7a879d !important;
  border-color: #d9dee8 !important;
}

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

/* APPVERBO_ADMIN_TABLE_FOOTER_STANDARD_V1_END */
'''

JS_CONTENT = '''// APPVERBO_ADMIN_TABLE_FOOTER_STANDARD_V1_START
(function () {
  "use strict";

  //###################################################################################
  // (1) CONFIGURACAO
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
  // (2) LIMPAR DUPLICADOS
  //###################################################################################

  function removerRodapesLegadosSessoesAdminTableFooterStandard_v2b() {
    document.querySelectorAll(LEGACY_SESSOES_SELECTOR).forEach(function (elemento) {
      if (elemento.closest(".admin-subprocess-table-footer-v1")) {
        return;
      }

      elemento.remove();
    });
  }

  function obterTabelaDoRodapeAdminTableFooterStandard_v2b(footer) {
    let cursor = footer.previousElementSibling;

    while (cursor) {
      if (cursor.matches && cursor.matches(FOOTER_SELECTOR)) {
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

  function removerRodapesDuplicadosAdminTableFooterStandard_v2b() {
    const mapa = new Map();

    document.querySelectorAll(FOOTER_SELECTOR).forEach(function (footer) {
      const tabela = obterTabelaDoRodapeAdminTableFooterStandard_v2b(footer);

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

      const preferido = rodapes.find(function (footer) {
        return footer.classList.contains("admin-subprocess-table-footer-v1");
      }) || rodapes.find(function (footer) {
        return footer.classList.contains("table-limiter");
      }) || rodapes[0];

      rodapes.forEach(function (footer) {
        if (footer !== preferido) {
          footer.remove();
        }
      });
    });
  }

  //###################################################################################
  // (3) CONTROLOS DO RODAPE
  //###################################################################################

  function obterControlesRodapeAdminTableFooterStandard_v2b(footer) {
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
  // (4) NORMALIZAR SELECT E TEXTO
  //###################################################################################

  function normalizarOpcoesSelectAdminTableFooterStandard_v2b(select) {
    if (!select) {
      return;
    }

    const valoresPadrao = ["5", "10", "20"];
    const valorAtual = select.value || "5";
    const existentes = new Set();

    Array.from(select.options).forEach(function (option) {
      if (!option.value) {
        option.value = option.textContent.trim();
      }

      existentes.add(option.value);
    });

    valoresPadrao.forEach(function (valor) {
      if (!existentes.has(valor)) {
        const option = document.createElement("option");
        option.value = valor;
        option.textContent = valor;
        select.appendChild(option);
      }
    });

    select.value = valoresPadrao.includes(valorAtual) ? valorAtual : "5";
  }

  function normalizarTextoAdminTableFooterStandard_v2b(footer) {
    footer.querySelectorAll("span").forEach(function (span) {
      const texto = (span.textContent || "").replace(/\\s+/g, " ").trim();

      if (texto.toLowerCase() === "entradas por página") {
        span.textContent = "entradas por página";
      }
    });
  }

  //###################################################################################
  // (5) PAGINACAO
  //###################################################################################

  function aplicarPaginaAdminTableFooterStandard_v2b(tabela, footer, estado) {
    const linhas = Array.from(tabela.querySelectorAll("tbody tr"));
    const controles = obterControlesRodapeAdminTableFooterStandard_v2b(footer);

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

  function iniciarRodapeAdminTableFooterStandard_v2b(footer) {
    if (footer.dataset.appverboAdminTableFooterStandardReadyV2b === "1") {
      return;
    }

    const tabela = obterTabelaDoRodapeAdminTableFooterStandard_v2b(footer);

    if (!tabela) {
      return;
    }

    const controles = obterControlesRodapeAdminTableFooterStandard_v2b(footer);

    if (!controles.select) {
      return;
    }

    normalizarTextoAdminTableFooterStandard_v2b(footer);
    normalizarOpcoesSelectAdminTableFooterStandard_v2b(controles.select);

    const estado = {
      page: 1,
      pageSize: Number.parseInt(controles.select.value || "5", 10) || 5
    };

    footer.dataset.appverboAdminTableFooterStandardReadyV2b = "1";

    controles.select.addEventListener("change", function () {
      estado.page = 1;
      aplicarPaginaAdminTableFooterStandard_v2b(tabela, footer, estado);
    });

    if (controles.botaoAnterior) {
      controles.botaoAnterior.addEventListener("click", function (event) {
        event.preventDefault();
        estado.page -= 1;
        aplicarPaginaAdminTableFooterStandard_v2b(tabela, footer, estado);
      });
    }

    if (controles.botaoSeguinte) {
      controles.botaoSeguinte.addEventListener("click", function (event) {
        event.preventDefault();
        estado.page += 1;
        aplicarPaginaAdminTableFooterStandard_v2b(tabela, footer, estado);
      });
    }

    aplicarPaginaAdminTableFooterStandard_v2b(tabela, footer, estado);
  }

  //###################################################################################
  // (6) INSTALAR
  //###################################################################################

  function instalarRodapesAdminTableFooterStandard_v2b() {
    removerRodapesLegadosSessoesAdminTableFooterStandard_v2b();
    removerRodapesDuplicadosAdminTableFooterStandard_v2b();

    document.querySelectorAll(FOOTER_SELECTOR).forEach(function (footer) {
      iniciarRodapeAdminTableFooterStandard_v2b(footer);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", instalarRodapesAdminTableFooterStandard_v2b);
  }
  else {
    instalarRodapesAdminTableFooterStandard_v2b();
  }

  window.addEventListener("load", instalarRodapesAdminTableFooterStandard_v2b);
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

    for pattern in patterns:
        text = re.sub(pattern, "\n", text, flags=re.IGNORECASE)

    return re.sub(r'\n{3,}', '\n\n', text)

def insert_before_last(text, needle, insertion):
    index = text.lower().rfind(needle.lower())

    if index == -1:
        return text.rstrip() + "\n" + insertion + "\n"

    return text[:index].rstrip() + "\n" + insertion + "\n" + text[index:]

def patch_template():
    text = read_text(TEMPLATE_PATH).replace("\r\n", "\n").replace("\r", "\n")
    text = remove_asset_tags(text)
    text = insert_before_last(text, "</head>", CSS_LINK)
    text = insert_before_last(text, "</body>", JS_LINK)
    write_text(TEMPLATE_PATH, text)
    print(f"OK: template atualizado: {TEMPLATE_PATH}")

def patch_macro():
    text = read_text(MACRO_PATH).replace("\r\n", "\n").replace("\r", "\n")

    old_block_pattern = (
        r'\n?\s*<!-- APPVERBO_ADMIN_SUBPROCESS_TABLE_FOOTER_STANDARD_V1_START -->'
        r'.*?'
        r'<!-- APPVERBO_ADMIN_SUBPROCESS_TABLE_FOOTER_STANDARD_V1_END -->\s*'
    )
    text = re.sub(old_block_pattern, "\n", text, flags=re.DOTALL)

    table_function_match = re.search(
        r'(?s)({%\s*macro\s+render_admin_subprocess_table\(.*?{% endmacro %})',
        text
    )

    if not table_function_match:
        raise SystemExit(f"ERRO: macro render_admin_subprocess_table nao encontrada em {MACRO_PATH}")

    function_text = table_function_match.group(1)

    pattern = r'(?s)(\s*</tbody>\s*</table>\s*</div>)(\s*{%\s*else\s*%})'

    if not re.search(pattern, function_text):
        print("===== CONTEXTO DA MACRO PARA DIAGNOSTICO =====")
        for line_number, line in enumerate(function_text.splitlines(), start=1):
            if "</table>" in line or "{% else %}" in line or "</div>" in line:
                print(f"L{line_number}: {line}")
        raise SystemExit("ERRO: ponto robusto de insercao nao encontrado dentro de render_admin_subprocess_table.")

    function_text = re.sub(
        pattern,
        lambda match: match.group(1) + "\n" + FOOTER_BLOCK + match.group(2),
        function_text,
        count=1
    )

    text = text[:table_function_match.start()] + function_text + text[table_function_match.end():]

    write_text(MACRO_PATH, text)
    print(f"OK: macro atualizado: {MACRO_PATH}")

def validate():
    checks = {
        TEMPLATE_PATH: [
            "admin_table_footer_standard_v1.css?v=20260516-admin-table-footer-standard-v2b",
            "admin_table_footer_standard_v1.js?v=20260516-admin-table-footer-standard-v2b",
        ],
        MACRO_PATH: [
            "APPVERBO_ADMIN_SUBPROCESS_TABLE_FOOTER_STANDARD_V1_START",
            "admin-subprocess-table-footer-v1",
            "Entradas por página",
        ],
        CSS_PATH: [
            "APPVERBO_ADMIN_TABLE_FOOTER_STANDARD_V1_START",
            "min-width: 230px",
            "white-space: nowrap",
            "appverbo-sessoes-entries-per-page-footer-v1",
        ],
        JS_PATH: [
            "APPVERBO_ADMIN_TABLE_FOOTER_STANDARD_V1_START",
            "removerRodapesLegadosSessoesAdminTableFooterStandard_v2b",
            "removerRodapesDuplicadosAdminTableFooterStandard_v2b",
            "instalarRodapesAdminTableFooterStandard_v2b",
        ],
    }

    for path, markers in checks.items():
        content = read_text(path)
        for marker in markers:
            if marker not in content:
                raise SystemExit(f"ERRO: marcador nao encontrado em {path}: {marker}")
            print(f"OK: {path}: {marker}")

    template = read_text(TEMPLATE_PATH)

    if "appverbo_sessoes_entries_per_page_v1.js" in template:
        raise SystemExit("ERRO: template ainda referencia JS legado de Sessoes.")

    if "appverbo_sessoes_entries_per_page_v1.css" in template:
        raise SystemExit("ERRO: template ainda referencia CSS legado de Sessoes.")

    macro = read_text(MACRO_PATH)
    start_count = macro.count("APPVERBO_ADMIN_SUBPROCESS_TABLE_FOOTER_STANDARD_V1_START")
    end_count = macro.count("APPVERBO_ADMIN_SUBPROCESS_TABLE_FOOTER_STANDARD_V1_END")

    if start_count != 1 or end_count != 1:
        raise SystemExit(f"ERRO: macro deve conter exatamente 1 bloco. START={start_count} END={end_count}")

    for path in [TEMPLATE_PATH, MACRO_PATH, CSS_PATH, JS_PATH]:
        content = read_text(path)
        for line_number, line in enumerate(content.splitlines(), start=1):
            for char in line:
                if ord(char) in {0x00C3, 0x00C2, 0xFFFD}:
                    raise SystemExit(f"ERRO: possivel mojibake em {path} linha {line_number}: {line}")

    print("OK: patch v2b validado.")

def main():
    patch_template()
    patch_macro()

    write_text(CSS_PATH, CSS_CONTENT)
    print(f"OK: CSS escrito: {CSS_PATH}")

    write_text(JS_PATH, JS_CONTENT)
    print(f"OK: JS escrito: {JS_PATH}")

    validate()

if __name__ == "__main__":
    main()
