// APPVERBO_HOME_CHARTS_RENDERER_V1_MODULE_START
(function registerHomeChartsRendererV1Module() {
  "use strict";

  window.APPVERBO_CREATE_HOME_CHARTS_RENDERER_API_V1 = function createHomeChartsRendererApiV1() {
    function renderHomeCharts(dashboardData = {}) {
      if (!window.Chart) {
        return;
      }

      const entityCanvas = document.getElementById("home-entities-chart");
      if (entityCanvas && !entityCanvas.dataset.chartReady) {
        new Chart(entityCanvas, {
          type: "doughnut",
          data: {
            labels: (dashboardData.entity_status || {}).labels || [],
            datasets: [
              {
                data: (dashboardData.entity_status || {}).values || [],
                backgroundColor: ["#1f7a49", "#d07a31"],
                borderColor: "#ffffff",
                borderWidth: 2
              }
            ]
          },
          options: {
            maintainAspectRatio: false,
            plugins: { legend: { position: "bottom" } }
          }
        });
        entityCanvas.dataset.chartReady = "1";
      }

      const profileCanvas = document.getElementById("home-profiles-chart");
      if (profileCanvas && !profileCanvas.dataset.chartReady) {
        new Chart(profileCanvas, {
          type: "bar",
          data: {
            labels: (dashboardData.users_by_profile || {}).labels || [],
            datasets: [
              {
                label: "Utilizadores",
                data: (dashboardData.users_by_profile || {}).values || [],
                backgroundColor: ["#2f6db4", "#3f84d6", "#58a3ec"],
                borderRadius: 7,
                maxBarThickness: 62
              }
            ]
          },
          options: {
            maintainAspectRatio: false,
            scales: {
              y: {
                beginAtZero: true,
                ticks: { precision: 0 }
              }
            },
            plugins: { legend: { display: false } }
          }
        });
        profileCanvas.dataset.chartReady = "1";
      }
    }

    return {
      renderHomeCharts
    };
  };
})();
// APPVERBO_HOME_CHARTS_RENDERER_V1_MODULE_END
