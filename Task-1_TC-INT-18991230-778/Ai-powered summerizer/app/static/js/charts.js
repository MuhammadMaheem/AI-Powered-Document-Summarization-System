/**
 * Chart.js integration for the word frequency bar chart.
 *
 * Exposes a single function renderFreqChart(topWords) that can be
 * called from main.js after the API response arrives.
 */

let _freqChart = null;

function renderFreqChart(topWords) {
  const canvas = document.getElementById("freqChart");
  if (!canvas) return;

  const isDark = document.documentElement.getAttribute("data-theme") !== "light";
  const gridColor   = isDark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.06)";
  const labelColor  = isDark ? "#9ba3c4" : "#4a4f6a";
  const barColor    = isDark ? "#7c6aff" : "#5b4fe8";
  const barHover    = isDark ? "#9580ff" : "#4a3fd4";

  const labels = topWords.map(function (w) { return w.word; });
  const data   = topWords.map(function (w) { return w.count; });

  if (_freqChart) {
    _freqChart.destroy();
    _freqChart = null;
  }

  _freqChart = new Chart(canvas, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [{
        label: "Frequency",
        data: data,
        backgroundColor: barColor,
        hoverBackgroundColor: barHover,
        borderRadius: 5,
        borderSkipped: false,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: function (ctx) {
              return "  " + ctx.parsed.y + " occurrences";
            },
          },
        },
      },
      scales: {
        x: {
          ticks: { color: labelColor, font: { size: 11, family: "Inter" } },
          grid: { color: gridColor },
        },
        y: {
          ticks: { color: labelColor, font: { size: 11, family: "Inter" }, precision: 0 },
          grid: { color: gridColor },
        },
      },
    },
  });
}
