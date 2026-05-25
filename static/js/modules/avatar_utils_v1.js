// APPVERBO_AVATAR_UTILS_V1_MODULE_START
(function registerAvatarUtilsV1Module() {
  "use strict";

  window.APPVERBO_CREATE_AVATAR_UTILS_API_V1 = function createAvatarUtilsApiV1() {
    //###################################################################################
    // (1) INICIAIS
    //###################################################################################
    function getInitials(name) {
      const parts = String(name || "").trim().split(/\s+/).filter(Boolean);
      if (!parts.length) {
        return "U";
      }
      if (parts.length === 1) {
        return parts[0].slice(0, 2).toUpperCase();
      }
      return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }

    //###################################################################################
    // (2) SVG DATA URI
    //###################################################################################
    function buildAvatarDataUri(name) {
      const initials = getInitials(name);
      const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" viewBox="0 0 96 96">
      <defs>
        <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#3777dc"/>
          <stop offset="100%" stop-color="#244ea5"/>
        </linearGradient>
      </defs>
      <rect width="96" height="96" rx="48" fill="url(#g)"/>
      <text x="50%" y="55%" text-anchor="middle" dominant-baseline="middle" fill="#ffffff" font-family="Segoe UI, Arial, sans-serif" font-size="34" font-weight="700">${initials}</text>
    </svg>
  `;
      return "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
    }

    return {
      getInitials,
      buildAvatarDataUri
    };
  };
})();
// APPVERBO_AVATAR_UTILS_V1_MODULE_END
