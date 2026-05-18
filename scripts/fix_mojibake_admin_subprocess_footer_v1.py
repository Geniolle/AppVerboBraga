from __future__ import annotations

from pathlib import Path


ROOT = Path.cwd()
TARGET = ROOT / "templates" / "macros" / "admin_subprocess.html"


####################################################################################
# (1) FUNCOES BASE
####################################################################################

def read_text_v1(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Ficheiro nao encontrado: {path}")
    return path.read_text(encoding="utf-8")


def write_text_v1(path: Path, content: str) -> None:
    if not content.endswith("\n"):
        content += "\n"
    path.write_text(content, encoding="utf-8", newline="\n")


def get_suspicious_lines_v1(content: str) -> list[tuple[int, str]]:
    bad_tokens = ("Ã", "Â", "�")
    result = []

    for line_number, line in enumerate(content.splitlines(), start=1):
        if any(token in line for token in bad_tokens):
            result.append((line_number, line))

    return result


####################################################################################
# (2) CORRIGIR MOJIBAKE COMUM EM PORTUGUES
####################################################################################

def fix_common_mojibake_v1(content: str) -> str:
    replacements = {
        "Ã€": "À",
        "Ã": "Á",
        "Ã‚": "Â",
        "Ãƒ": "Ã",
        "Ã‡": "Ç",
        "Ãˆ": "È",
        "Ã‰": "É",
        "ÃŠ": "Ê",
        "ÃŒ": "Ì",
        "Ã": "Í",
        "Ã“": "Ó",
        "Ã”": "Ô",
        "Ã•": "Õ",
        "Ãš": "Ú",
        "Ãœ": "Ü",
        "Ã¡": "á",
        "Ã ": "à",
        "Ã¢": "â",
        "Ã£": "ã",
        "Ã§": "ç",
        "Ã©": "é",
        "Ãª": "ê",
        "Ã­": "í",
        "Ã³": "ó",
        "Ã´": "ô",
        "Ãµ": "õ",
        "Ãº": "ú",
        "Ã¼": "ü",
        "AÃ‡Ã•ES": "AÇÕES",
        "AÃ‡Ã\x95ES": "AÇÕES",
        "AÃ‡OES": "AÇÕES",
        "AÃ§Ãµes": "Ações",
        "AÃ§Ã£o": "Ação",
        "aÃ§Ã£o": "ação",
        "PÃ¡gina": "Página",
        "PrÃ³xima": "Próxima",
        "pÃ¡gina": "página",
        "registos": "registos",
        "Sessoes": "Sessões",
        "sessao": "sessão",
        "Sessao": "Sessão",
        "InformaÃ§Ãµes": "Informações",
        "ConfiguraÃ§Ã£o": "Configuração",
        "DescriÃ§Ã£o": "Descrição",
        "VisualizaÃ§Ã£o": "Visualização",
        "EdiÃ§Ã£o": "Edição",
        "CabeÃ§alho": "Cabeçalho",
        "NÃ£o": "Não",
        "nÃ£o": "não",
        "Â«": "«",
        "Â»": "»",
        "Âº": "º",
        "Âª": "ª",
        "Â°": "°",
        "Â ": " ",
        "\ufeff": "",
    }

    fixed = content

    for old, new in replacements.items():
        fixed = fixed.replace(old, new)

    fixed = fixed.replace("Â", "")

    return fixed


####################################################################################
# (3) EXECUTAR CORRECAO
####################################################################################

def main_v1() -> None:
    original = read_text_v1(TARGET)
    before = get_suspicious_lines_v1(original)

    print("Linhas suspeitas antes:", len(before))

    fixed = fix_common_mojibake_v1(original)
    after = get_suspicious_lines_v1(fixed)

    if after:
        print("ERRO: ainda existem linhas suspeitas depois da correcao:")
        for line_number, line in after:
            print(f"L{line_number}: {line}")
        raise RuntimeError("Ainda existe mojibake em templates/macros/admin_subprocess.html")

    write_text_v1(TARGET, fixed)

    print("OK: mojibake corrigido em templates/macros/admin_subprocess.html")


if __name__ == "__main__":
    main_v1()
