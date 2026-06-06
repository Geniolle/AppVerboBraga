file_path = 'static/js/modules/appverbo_navigation_smooth_v7.js'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update urlIndicaAdminV7
old_urlIndica = """  function urlIndicaAdminV7(url) {
    return Boolean(
      url &&
      url.pathname === "/users/new" &&
      cleanValueV7(url.searchParams.get("menu")) === "administrativo"
    );
  }"""

new_urlIndica = """  function urlIndicaAdminV7(url) {
    if (!url || url.pathname !== "/users/new") {
      return false;
    }
    const menu = cleanValueV7(url.searchParams.get("menu"));
    return menu === "administrativo" || menu === "sessoes";
  }"""

if old_urlIndica in content:
    content = content.replace(old_urlIndica, new_urlIndica)
    print("urlIndicaAdminV7 updated successfully")
else:
    # Try with different whitespaces/newlines
    print("urlIndicaAdminV7 signature not matched directly. Checking with regex.")
    import re
    pattern = r'function\s+urlIndicaAdminV7\s*\(\s*url\s*\)\s*\{\s*return\s+Boolean\s*\(\s*url\s*&&\s*url\.pathname\s*===\s*"/users/new"\s*&&\s*cleanValueV7\s*\(\s*url\.searchParams\.get\(\s*"menu"\s*\)\s*\)\s*===\s*"administrativo"\s*\);\s*\}'
    if re.search(pattern, content):
        content = re.sub(pattern, new_urlIndica, content)
        print("urlIndicaAdminV7 updated via regex")
    else:
        print("urlIndicaAdminV7 NOT updated")

# 2. Add resolveMenuKeyForTabV7 helper and update buildAdminSubprocessUrlV7
old_buildUrl = """  function buildAdminSubprocessUrlV7(tab) {
    const currentUrl = getCurrentUrlV7();
    const url = currentUrl
      ? new URL(currentUrl.toString())
      : new URL("/users/new", window.location.origin);

    url.pathname = "/users/new";
    url.searchParams.set("menu", "administrativo");"""

new_buildUrl = """  function resolveMenuKeyForTabV7(tab) {
    const cleanTab = cleanValueV7(tab);
    if (cleanTab === "entidade" || cleanTab === "utilizador") {
      return "administrativo";
    }
    if (cleanTab === "sessoes" || cleanTab === "menu" || cleanTab === "definicoes") {
      return "sessoes";
    }
    return "administrativo";
  }

  function buildAdminSubprocessUrlV7(tab) {
    const currentUrl = getCurrentUrlV7();
    const url = currentUrl
      ? new URL(currentUrl.toString())
      : new URL("/users/new", window.location.origin);

    url.pathname = "/users/new";
    const menuKey = resolveMenuKeyForTabV7(tab);
    url.searchParams.set("menu", menuKey);"""

if old_buildUrl in content:
    content = content.replace(old_buildUrl, new_buildUrl)
    print("buildAdminSubprocessUrlV7 updated successfully")
else:
    print("buildAdminSubprocessUrlV7 signature not matched directly")

# Also update the fallback return at the end of buildAdminSubprocessUrlV7:
# return "/users/new?menu=administrativo";
old_fallback = 'return "/users/new?menu=administrativo";'
new_fallback = 'return "/users/new?menu=" + resolveMenuKeyForTabV7(tab);'
if old_fallback in content:
    content = content.replace(old_fallback, new_fallback)
    print("buildAdminSubprocessUrlV7 fallback return updated successfully")

# 3. Update activeMenu replacement in initialization fallback
old_init_history = """      if (window.history && typeof window.history.replaceState === "function") {
        window.history.replaceState(window.history.state, document.title, "/users/new?menu=administrativo");
      }"""

new_init_history = """      const activeMenu = getActiveSidebarMenuKeyV7() || "administrativo";
      if (window.history && typeof window.history.replaceState === "function") {
        window.history.replaceState(window.history.state, document.title, "/users/new?menu=" + activeMenu);
      }"""

if old_init_history in content:
    content = content.replace(old_init_history, new_init_history)
    print("inicializarV7 history replace updated successfully")

# 4. Update isAdminSidebarMenuActive check
old_active_check = 'const isAdminSidebarMenuActive = getActiveSidebarMenuKeyV7() === "administrativo";'
new_active_check = """const activeMenuKey = getActiveSidebarMenuKeyV7();
      const isAdminSidebarMenuActive = activeMenuKey === "administrativo" || activeMenuKey === "sessoes";"""

if old_active_check in content:
    content = content.replace(old_active_check, new_active_check)
    print("isAdminSidebarMenuActive check updated successfully")

# 5. Update menuButton click handler
old_menu_click = """    if (menuButton && cleanValueV7(menuButton.getAttribute("data-menu")) === "administrativo") {
      window.setTimeout(function () {
        if (hasCustomSubprocessLinksV7()) {
          exitAdminProcessOnlyModeV7();
          markReadyV7();
          return;
        }

        if (window.history && typeof window.history.replaceState === "function") {
          window.history.replaceState(window.history.state, document.title, "/users/new?menu=administrativo");
        }

        renderAdminProcessOnlyV7();
        markReadyV7();
      }, 0);"""

new_menu_click = """    const activeMenuKeyClick = menuButton ? cleanValueV7(menuButton.getAttribute("data-menu")) : "";
    if (menuButton && (activeMenuKeyClick === "administrativo" || activeMenuKeyClick === "sessoes")) {
      window.setTimeout(function () {
        if (hasCustomSubprocessLinksV7()) {
          exitAdminProcessOnlyModeV7();
          markReadyV7();
          return;
        }

        if (window.history && typeof window.history.replaceState === "function") {
          window.history.replaceState(window.history.state, document.title, "/users/new?menu=" + activeMenuKeyClick);
        }

        renderAdminProcessOnlyV7();
        markReadyV7();
      }, 0);"""

if old_menu_click in content:
    content = content.replace(old_menu_click, new_menu_click)
    print("menuButton click handler updated successfully")

# Save the updated content
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Patch completed!")
