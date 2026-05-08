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


####################################################################################
# (3) PATCH appverbo/app.py
####################################################################################

app_text = read_text(app_path)

app_marker = "APPVERBO_DYNAMIC_NO_STORE_MIDDLEWARE_V1_START"

if app_marker not in app_text:
    old_block = '''    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.APP_SECRET_KEY,
        same_site="lax",
        https_only=False,
    )

    app.include_router(auth_router)
'''

    new_block = '''    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.APP_SECRET_KEY,
        same_site="lax",
        https_only=False,
    )

    # APPVERBO_DYNAMIC_NO_STORE_MIDDLEWARE_V1_START
    @app.middleware("http")
    async def appverbo_dynamic_no_store_middleware_v1(request, call_next):
        response = await call_next(request)
        request_path = str(request.url.path or "")

        if not request_path.startswith("/static"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            response.headers["X-AppVerbo-Dynamic-Sync"] = "no-store-v1"

        return response
    # APPVERBO_DYNAMIC_NO_STORE_MIDDLEWARE_V1_END

    app.include_router(auth_router)
'''

    if old_block not in app_text:
        raise RuntimeError("Bloco de SessionMiddleware nao encontrado em appverbo/app.py")

    app_text = app_text.replace(old_block, new_block, 1)

write_text(app_path, app_text)

####################################################################################
# (4) PATCH appverbo/core.py
####################################################################################

core_text = read_text(core_path)

core_marker = "APPVERBO_DYNAMIC_NO_STORE_CORE_MIDDLEWARE_V1_START"

if core_marker not in core_text:
    old_block = '''app.add_middleware(
    SessionMiddleware,
    secret_key=APP_SECRET_KEY,
    same_site="lax",
    https_only=False,
)

__all__ = [
'''

    new_block = '''app.add_middleware(
    SessionMiddleware,
    secret_key=APP_SECRET_KEY,
    same_site="lax",
    https_only=False,
)

# APPVERBO_DYNAMIC_NO_STORE_CORE_MIDDLEWARE_V1_START
@app.middleware("http")
async def appverbo_dynamic_no_store_core_middleware_v1(request, call_next):
    response = await call_next(request)
    request_path = str(request.url.path or "")

    if not request_path.startswith("/static"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        response.headers["X-AppVerbo-Dynamic-Sync"] = "no-store-core-v1"

    return response
# APPVERBO_DYNAMIC_NO_STORE_CORE_MIDDLEWARE_V1_END

__all__ = [
'''

    if old_block not in core_text:
        raise RuntimeError("Bloco de SessionMiddleware nao encontrado em appverbo/core.py")

    core_text = core_text.replace(old_block, new_block, 1)

write_text(core_path, core_text)

####################################################################################
# (5) VALIDAR PATCH
####################################################################################

app_check = read_text(app_path)
core_check = read_text(core_path)

required_app_markers = [
    "APPVERBO_DYNAMIC_NO_STORE_MIDDLEWARE_V1_START",
    "appverbo_dynamic_no_store_middleware_v1",
    'response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"',
    'response.headers["X-AppVerbo-Dynamic-Sync"] = "no-store-v1"',
]

required_core_markers = [
    "APPVERBO_DYNAMIC_NO_STORE_CORE_MIDDLEWARE_V1_START",
    "appverbo_dynamic_no_store_core_middleware_v1",
    'response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"',
    'response.headers["X-AppVerbo-Dynamic-Sync"] = "no-store-core-v1"',
]

for marker in required_app_markers:
    if marker not in app_check:
        raise RuntimeError(f"Validacao falhou em app.py. Marcador ausente: {marker}")

for marker in required_core_markers:
    if marker not in core_check:
        raise RuntimeError(f"Validacao falhou em core.py. Marcador ausente: {marker}")

print("OK: middleware no-store aplicado.")
