// Evita duplicados si el script se ejecuta más de una vez
window._boxcriptorCharts = window._boxcriptorCharts || {};

(function () {
  function fmt(x) {
    try {
      return new Intl.NumberFormat('es-CR', { style: 'currency', currency: 'CRC', maximumFractionDigits: 0 }).format(x || 0);
    } catch (e) {
      return 'CRC ' + (x || 0).toFixed(0);
    }
  }

  fetch(window.BOXCRIPTOR_STATS_URL || "/estadisticas/data")
    .then(r => r.json())
    .then(payload => {
      // KPIs
      const k90 = document.getElementById('kpi-total-90');
      const k12 = document.getElementById('kpi-total-12');
      const kpm = document.getElementById('kpi-prom-mes');
      if (k90) k90.textContent = fmt(payload.categorias90.total90);
      if (k12) k12.textContent = fmt(payload.monthly.total12);
      if (kpm) kpm.textContent = fmt(payload.monthly.promedioMensual12);

      const ctxM = document.getElementById('chartMonthly')?.getContext('2d');
      if (ctxM) {
        if (window._boxcriptorCharts.monthly) window._boxcriptorCharts.monthly.destroy();
        window._boxcriptorCharts.monthly = new Chart(ctxM, {
          type: 'line',
          data: {
            labels: payload.monthly.labels,
            datasets: [{
              label: 'Gasto mensual (CRC)',
              data: payload.monthly.data,
              tension: 0.25,
              fill: true
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: { y: { beginAtZero: true } },
            plugins: {
              legend: { display: false },
              tooltip: { callbacks: { label: (ctx) => fmt(ctx.parsed.y) } }
            }
          }
        });
      }

      // Categorías
      const ctxC = document.getElementById('chartCategorias')?.getContext('2d');
      if (ctxC) {
        if (window._boxcriptorCharts.categorias) window._boxcriptorCharts.categorias.destroy();
        window._boxcriptorCharts.categorias = new Chart(ctxC, {
          type: 'doughnut',
          data: {
            labels: payload.categorias90.labels,
            datasets: [{ data: payload.categorias90.data }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { position: 'bottom' },
              tooltip: { callbacks: { label: (ctx) => `${ctx.label}: ${fmt(ctx.parsed)}` } }
            }
          }
        });
      }

      // Proveedores
      const ctxP = document.getElementById('chartProveedores')?.getContext('2d');
      if (ctxP) {
        if (window._boxcriptorCharts.proveedores) window._boxcriptorCharts.proveedores.destroy();
        window._boxcriptorCharts.proveedores = new Chart(ctxP, {
          type: 'bar',
          data: {
            labels: payload.proveedores6m.labels,
            datasets: [{ label: 'Gasto (CRC)', data: payload.proveedores6m.data }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: { y: { beginAtZero: true } },
            plugins: {
              legend: { display: false },
              tooltip: { callbacks: { label: (ctx) => fmt(ctx.parsed.y) } }
            }
          }
        });
      }
    })
    .catch(err => console.error('Error cargando estadísticas:', err));
})();
