from pathlib import Path

####################################################################################
# (1) CAMINHOS
####################################################################################

app_path = Path("appverbo/app.py")
core_path = Path("appverbo/core.py")

####################################################################################
# (2) FUNCOES AUXILIARES
####################################################################################

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def insert_before_once(text: str, marker: str, insertion: str, already_marker: str, file_label: str) -> str:
    if already_marker in text:
        return text

    index = text.find(marker)

    if index < 0:
        raise RuntimeError(f"Marcador de insercao nao encontrado em {file_label}: {marker}")

    return text[:index] + insertion + text[index:]


####################################################################################
# (3) PATCH appverbo/app.py
####################################################################################

app_text = read_text(app_path)

app_insertion = '''
    # APPVERBO_DYNAMIC_NO_STORE_MIDDLEWARE_V2_START
    @app.middleware("http")
    async def appverbo_dynamic_no_store_middleware_v2(request, call_next):
        response = await call_next(request)
        request_path = str(request.url.path or "")

        if not request_path.startswith("/static"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            response.headers["X-AppVerbo-Dynamic-Sync"] = "no-store-v2"

        return response
    # APPVERBO_DYNAMIC_NO_STORE_MIDDLEWARE_V2_END

'''

app_text = insert_before_once(
    text=app_text,
    marker="    app.include_router(",
    insertion=app_insertion,
    already_marker="APPVERBO_DYNAMIC_NO_STORE_MIDDLEWARE_V2_START",
    file_label="appverbo/app.py",
)

write_text(app_path, app_text)

####################################################################################
# (4) PATCH appverbo/core.py
####################################################################################

core_text = read_text(core_path)

core_insertion = '''
# APPVERBO_DYNAMIC_NO_STORE_CORE_MIDDLEWARE_V2_START
@app.middleware("http")
async def appverbo_dynamic_no_store_core_middleware_v2(request, call_next):
    response = await call_next(request)
    request_path = str(request.url.path or "")

    if not request_path.startswith("/static"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        response.headers["X-AppVerbo-Dynamic-Sync"] = "no-store-core-v2"

    return response
# APPVERBO_DYNAMIC_NO_STORE_CORE_MIDDLEWARE_V2_END

'''

core_text = insert_before_once(
    text=core_text,
    marker="__all__ = [",
    insertion=core_insertion,
    already_marker="APPVERBO_DYNAMIC_NO_STORE_CORE_MIDDLEWARE_V2_START",
    file_label="appverbo/core.py",
)

write_text(core_path, core_text)

####################################################################################
# (5) VALIDAR PATCH
####################################################################################

app_check = read_text(app_path)
core_check = read_text(core_path)

required_app_markers = [
    "APPVERBO_DYNAMIC_NO_STORE_MIDDLEWARE_V2_START",
    "appverbo_dynamic_no_store_middleware_v2",
    'response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"',
    'response.headers["X-AppVerbo-Dynamic-Sync"] = "no-store-v2"',
]

required_core_markers = [
    "APPVERBO_DYNAMIC_NO_STORE_CORE_MIDDLEWARE_V2_START",
    "appverbo_dynamic_no_store_core_middleware_v2",
    'response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"',
    'response.headers["X-AppVerbo-Dynamic-Sync"] = "no-store-core-v2"',
]

for marker in required_app_markers:
    if marker not in app_check:
        raise RuntimeError(f"Validacao falhou em app.py. Marcador ausente: {marker}")

for marker in required_core_markers:
    if marker not in core_check:
        raise RuntimeError(f"Validacao falhou em core.py. Marcador ausente: {marker}")

print("OK: middleware no-store aplicado com patch robusto.")
