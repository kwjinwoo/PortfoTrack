/* PortfoTrack — Trends Analysis UI */

"use strict";

/** Color palette for chart lines. */
var COLORS = [
  "#3498db",
  "#e74c3c",
  "#2ecc71",
  "#f39c12",
  "#9b59b6",
  "#1abc9c",
  "#e67e22",
  "#34495e",
  "#16a085",
  "#c0392b",
];

document.addEventListener("DOMContentLoaded", function () {
  loadTrendData();
});

/**
 * Fetch trend analysis data and render all three charts.
 */
async function loadTrendData() {
  try {
    var response = await fetch("/api/trends/analysis");
    if (!response.ok) {
      showTrendsMessage("데이터를 불러오는데 실패했습니다.", "error");
      return;
    }

    var data = await response.json();

    if (data.metadata.snapshot_count === 0) {
      showTrendsMessage("표시할 스냅샷 데이터가 없습니다.", "info");
      return;
    }

    renderRatioChart(data);
    renderAmountChart(data);
    renderTotalChart(data);
    initComparison(data);
  } catch (err) {
    console.error("Failed to load trend data:", err);
    showTrendsMessage("네트워크 오류가 발생했습니다.", "error");
  }
}

/**
 * Render the asset allocation ratio (percentage) chart.
 */
function renderRatioChart(data) {
  var ctx = document.getElementById("ratio-chart").getContext("2d");
  var labels = data.portfolio_trend.map(function (p) {
    return p.date;
  });

  var datasets = data.asset_trends.map(function (asset, i) {
    return {
      label: asset.asset_name,
      data: asset.data_points.map(function (dp) {
        return (dp.ratio * 100).toFixed(2);
      }),
      borderColor: COLORS[i % COLORS.length],
      backgroundColor: COLORS[i % COLORS.length] + "33",
      fill: true,
      tension: 0.3,
    };
  });

  new Chart(ctx, {
    type: "line",
    data: { labels: labels, datasets: datasets },
    options: {
      responsive: true,
      plugins: {
        title: { display: true, text: "자산별 비율 추이 (%)" },
        tooltip: {
          callbacks: {
            label: function (context) {
              return context.dataset.label + ": " + context.parsed.y + "%";
            },
          },
        },
      },
      scales: {
        y: {
          stacked: true,
          min: 0,
          max: 100,
          ticks: {
            callback: function (value) {
              return value + "%";
            },
          },
        },
      },
    },
  });
}

/**
 * Render the per-asset amount chart.
 */
function renderAmountChart(data) {
  var ctx = document.getElementById("amount-chart").getContext("2d");
  var labels = data.portfolio_trend.map(function (p) {
    return p.date;
  });

  var datasets = data.asset_trends.map(function (asset, i) {
    return {
      label: asset.asset_name,
      data: asset.data_points.map(function (dp) {
        return dp.amount;
      }),
      borderColor: COLORS[i % COLORS.length],
      tension: 0.3,
    };
  });

  new Chart(ctx, {
    type: "line",
    data: { labels: labels, datasets: datasets },
    options: {
      responsive: true,
      plugins: {
        title: { display: true, text: "자산별 평가 금액 추이 (KRW)" },
        tooltip: {
          callbacks: {
            label: function (context) {
              return (
                context.dataset.label +
                ": " +
                Number(context.parsed.y).toLocaleString() +
                "원"
              );
            },
          },
        },
      },
      scales: {
        y: {
          ticks: {
            callback: function (value) {
              return Number(value).toLocaleString();
            },
          },
        },
      },
    },
  });
}

/**
 * Render the total portfolio value chart with change percentage labels.
 */
function renderTotalChart(data) {
  var ctx = document.getElementById("total-chart").getContext("2d");
  var labels = data.portfolio_trend.map(function (p) {
    return p.date;
  });
  var amounts = data.portfolio_trend.map(function (p) {
    return p.total_amount;
  });
  var changePcts = data.portfolio_trend.map(function (p) {
    return p.change_pct;
  });

  new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "전체 포트폴리오",
          data: amounts,
          borderColor: "#2c3e50",
          backgroundColor: "#2c3e5033",
          fill: true,
          borderWidth: 3,
          tension: 0.3,
          changePcts: changePcts,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        title: { display: true, text: "전체 포트폴리오 추이 (KRW)" },
        tooltip: {
          callbacks: {
            label: function (context) {
              var pct = changePcts[context.dataIndex];
              var pctStr = pct > 0 ? "+" + pct.toFixed(1) + "%" : pct.toFixed(1) + "%";
              return (
                "Total: " +
                Number(context.parsed.y).toLocaleString() +
                "원 (" + pctStr + ")"
              );
            },
          },
        },
        datalabels: {
          align: "top",
          anchor: "end",
          offset: 4,
          font: { size: 11, weight: "bold" },
          formatter: function (value, context) {
            var idx = context.dataIndex;
            if (idx === 0) return "";
            var pct = changePcts[idx];
            if (pct > 0) return "+" + pct.toFixed(1) + "%";
            return pct.toFixed(1) + "%";
          },
          color: function (context) {
            var idx = context.dataIndex;
            if (idx === 0) return "#95a5a6";
            var pct = changePcts[idx];
            if (pct > 0) return "#27ae60";
            if (pct < 0) return "#e74c3c";
            return "#95a5a6";
          },
        },
      },
      scales: {
        y: {
          ticks: {
            callback: function (value) {
              return Number(value).toLocaleString();
            },
          },
        },
      },
    },
    plugins: [ChartDataLabels],
  });
}

/**
 * Display a message to the user.
 */
function showTrendsMessage(text, type) {
  var el = document.getElementById("trends-message");
  if (el) {
    el.textContent = text;
    el.className = "message " + type;
  }
}

/**
 * Initialize snapshot comparison dropdowns and event handlers.
 */
function initComparison(data) {
  var fromSelect = document.getElementById("compare-from");
  var toSelect = document.getElementById("compare-to");
  var resultEl = document.getElementById("comparison-result");
  if (!fromSelect || !toSelect || !resultEl) return;

  // Populate dropdowns with snapshot dates
  data.portfolio_trend.forEach(function (p) {
    var optFrom = document.createElement("option");
    optFrom.value = p.date;
    optFrom.textContent = p.date;
    fromSelect.appendChild(optFrom);

    var optTo = document.createElement("option");
    optTo.value = p.date;
    optTo.textContent = p.date;
    toSelect.appendChild(optTo);
  });

  function updateComparison() {
    var fromDate = fromSelect.value;
    var toDate = toSelect.value;
    if (!fromDate || !toDate) {
      resultEl.textContent = "";
      return;
    }

    var fromPoint = data.portfolio_trend.find(function (p) {
      return p.date === fromDate;
    });
    var toPoint = data.portfolio_trend.find(function (p) {
      return p.date === toDate;
    });

    if (!fromPoint || !toPoint) {
      resultEl.textContent = "";
      return;
    }

    var fromAmount = fromPoint.total_amount;
    var toAmount = toPoint.total_amount;
    var pct = fromAmount === 0 ? 0.0 : ((toAmount - fromAmount) / fromAmount) * 100;
    var pctStr = pct > 0 ? "+" + pct.toFixed(1) + "%" : pct.toFixed(1) + "%";
    var color = pct > 0 ? "#27ae60" : pct < 0 ? "#e74c3c" : "#95a5a6";

    resultEl.innerHTML =
      "<strong>" +
      fromDate +
      "</strong>: " +
      fromAmount.toLocaleString() +
      "원 → <strong>" +
      toDate +
      "</strong>: " +
      toAmount.toLocaleString() +
      '원 (<span style="color:' +
      color +
      '">' +
      pctStr +
      "</span>)";
  }

  fromSelect.addEventListener("change", updateComparison);
  toSelect.addEventListener("change", updateComparison);
}
