/* PortfoTrack — Optional Bets Trend Analysis UI */

"use strict";

/** Color palette for chart lines. */
var OB_COLORS = [
    "#e74c3c",
    "#3498db",
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
    loadOptionalBetTrendData();
});

/**
 * Fetch optional bet trend analysis data and render all three charts.
 */
async function loadOptionalBetTrendData() {
    try {
        var response = await fetch("/api/optional-bets/trends/analysis");
        if (!response.ok) {
            showOBTrendsMessage("추이 데이터를 불러오는데 실패했습니다.", "error");
            return;
        }

        var data = await response.json();

        if (data.metadata.snapshot_count === 0) {
            showOBTrendsMessage("표시할 옵셔널 벳 추이 데이터가 없습니다.", "info");
            return;
        }

        renderOBRatioChart(data);
        renderOBAmountChart(data);
        renderOBTotalChart(data);
    } catch (err) {
        console.error("Failed to load optional bet trend data:", err);
        showOBTrendsMessage("네트워크 오류가 발생했습니다.", "error");
    }
}

/**
 * Render the asset allocation ratio (percentage) chart for optional bets.
 */
function renderOBRatioChart(data) {
    var ctx = document.getElementById("ob-ratio-chart").getContext("2d");
    var labels = data.portfolio_trend.map(function (p) {
        return p.date;
    });

    var datasets = data.asset_trends.map(function (asset, i) {
        return {
            label: asset.asset_name || asset.asset_id,
            data: asset.data_points.map(function (dp) {
                return (dp.ratio * 100).toFixed(1);
            }),
            borderColor: OB_COLORS[i % OB_COLORS.length],
            backgroundColor: OB_COLORS[i % OB_COLORS.length] + "33",
            fill: false,
            tension: 0.3,
        };
    });

    new Chart(ctx, {
        type: "line",
        data: { labels: labels, datasets: datasets },
        options: {
            responsive: true,
            plugins: {
                title: { display: false },
                datalabels: { display: false },
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
                    beginAtZero: true,
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
 * Render the asset amount chart for optional bets.
 */
function renderOBAmountChart(data) {
    var ctx = document.getElementById("ob-amount-chart").getContext("2d");
    var labels = data.portfolio_trend.map(function (p) {
        return p.date;
    });

    var datasets = data.asset_trends.map(function (asset, i) {
        return {
            label: asset.asset_name || asset.asset_id,
            data: asset.data_points.map(function (dp) {
                return dp.amount;
            }),
            borderColor: OB_COLORS[i % OB_COLORS.length],
            backgroundColor: OB_COLORS[i % OB_COLORS.length] + "33",
            fill: false,
            tension: 0.3,
        };
    });

    new Chart(ctx, {
        type: "line",
        data: { labels: labels, datasets: datasets },
        options: {
            responsive: true,
            plugins: {
                title: { display: false },
                datalabels: { display: false },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return (
                                context.dataset.label +
                                ": " +
                                Number(context.parsed.y).toLocaleString() +
                                " KRW"
                            );
                        },
                    },
                },
            },
            scales: {
                y: {
                    beginAtZero: true,
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
 * Render the total optional bet value chart.
 */
function renderOBTotalChart(data) {
    var ctx = document.getElementById("ob-total-chart").getContext("2d");
    var labels = data.portfolio_trend.map(function (p) {
        return p.date;
    });
    var totalAmounts = data.portfolio_trend.map(function (p) {
        return p.total_amount;
    });
    var changePcts = data.portfolio_trend.map(function (p) {
        return p.change_pct;
    });

    new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [
                {
                    label: "총 금액",
                    data: totalAmounts,
                    backgroundColor: "#e74c3c66",
                    borderColor: "#e74c3c",
                    borderWidth: 1,
                },
            ],
        },
        options: {
            responsive: true,
            plugins: {
                title: { display: false },
                datalabels: {
                    anchor: "end",
                    align: "top",
                    formatter: function (value, context) {
                        var pct = changePcts[context.dataIndex];
                        if (pct === 0) return "";
                        var sign = pct > 0 ? "+" : "";
                        return sign + pct.toFixed(1) + "%";
                    },
                    color: function (context) {
                        var pct = changePcts[context.dataIndex];
                        return pct >= 0 ? "#2ecc71" : "#e74c3c";
                    },
                    font: { weight: "bold", size: 11 },
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            var amount = Number(context.parsed.y).toLocaleString() + " KRW";
                            var pct = changePcts[context.dataIndex];
                            if (pct === 0) return amount;
                            var sign = pct > 0 ? "+" : "";
                            return amount + " (" + sign + pct.toFixed(1) + "%)";
                        },
                    },
                },
            },
            scales: {
                y: {
                    beginAtZero: true,
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
 * Show a message in the trends section.
 */
function showOBTrendsMessage(text, type) {
    var el = document.getElementById("ob-trends-message");
    if (!el) return;
    el.textContent = text;
    el.className = "message " + (type || "info");
}
