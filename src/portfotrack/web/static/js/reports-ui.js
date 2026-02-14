/* PortfoTrack — Allocation Report UI */

"use strict";

document.addEventListener("DOMContentLoaded", function () {
  loadSnapshotOptions();
  setupReportForm();
});

/**
 * Load available snapshot dates into the select dropdown.
 */
async function loadSnapshotOptions() {
  const select = document.getElementById("snapshot-date-select");

  try {
    const response = await fetch("/api/snapshots");
    const data = await response.json();

    data.forEach(function (s) {
      const option = document.createElement("option");
      option.value = s.date;
      option.textContent = s.date;
      select.appendChild(option);
    });
  } catch (err) {
    console.error("Failed to load snapshots:", err);
  }
}

/**
 * Set up the report generation form.
 */
function setupReportForm() {
  const form = document.getElementById("report-form");
  form.addEventListener("submit", async function (e) {
    e.preventDefault();

    const snapshotDate = document.getElementById("snapshot-date-select").value;
    if (!snapshotDate) {
      showMessage("report-message", "스냅샷을 선택하세요.", "error");
      return;
    }

    try {
      const response = await fetch(
        `/api/reports/allocation?snapshot_date=${snapshotDate}`
      );

      if (!response.ok) {
        const err = await response.json();
        showMessage(
          "report-message",
          err.error || "리포트 생성에 실패했습니다.",
          "error"
        );
        return;
      }

      const data = await response.json();
      displayReport(data);
    } catch (err) {
      showMessage("report-message", "네트워크 오류가 발생했습니다.", "error");
    }
  });
}

/**
 * Render the allocation report.
 */
function displayReport(report) {
  const card = document.getElementById("report-result-card");
  const dateSpan = document.getElementById("report-date");
  const summary = document.getElementById("report-summary");
  const tbody = document.getElementById("report-items");
  const footer = document.getElementById("report-footer");

  dateSpan.textContent = report.snapshot_date;

  // Summary
  summary.innerHTML = `
    <p><strong>총 포트폴리오:</strong> ${report.total_portfolio_amount.toLocaleString()} KRW</p>
    <p><strong>상태:</strong> ${report.is_complete ? "✓ 모든 자산 허용치 내" : "✗ 일부 자산 허용치 초과"}</p>
  `;

  // Items
  tbody.innerHTML = report.items
    .map(function (item) {
      const currentPct = (item.current_ratio * 100).toFixed(1);
      const targetPct = (item.target_ratio * 100).toFixed(1);
      const fillPct = item.target_ratio > 0
        ? Math.min((item.current_ratio / item.target_ratio) * 100, 100).toFixed(0)
        : 0;
      const fillClass = item.is_within_tolerance ? "within" : "outside";
      const statusIcon = item.is_within_tolerance ? "✓" : "✗";

      let neededStr;
      if (item.target_amount_needed > 0) {
        neededStr = "+" + item.target_amount_needed.toLocaleString();
      } else if (item.target_amount_needed < 0) {
        neededStr = item.target_amount_needed.toLocaleString();
      } else {
        neededStr = "0";
      }

      return `
        <tr>
          <td>
            <strong>${item.asset_name}</strong>
            <br><small>${item.asset_id}</small>
          </td>
          <td>${item.current_amount.toLocaleString()}</td>
          <td>${currentPct}%</td>
          <td>${targetPct}%</td>
          <td>
            <div class="progress-bar">
              <div class="progress-fill ${fillClass}" style="width: ${fillPct}%"></div>
            </div>
            <small>${(item.tolerance.lower * 100).toFixed(1)}% – ${(item.tolerance.upper * 100).toFixed(1)}%</small>
          </td>
          <td>${neededStr} KRW</td>
          <td class="${item.is_within_tolerance ? "status-ok" : "status-warn"}">${statusIcon}</td>
        </tr>
      `;
    })
    .join("");

  // Footer
  if (report.total_additional_needed > 0) {
    footer.innerHTML = `<p><strong>추가 필요 자본:</strong> ${report.total_additional_needed.toLocaleString()} KRW</p>`;
  } else {
    footer.innerHTML = "<p><strong>모든 목표 달성 ✓</strong></p>";
  }

  card.style.display = "block";
}

/**
 * Show a status message.
 */
function showMessage(elementId, text, type) {
  const el = document.getElementById(elementId);
  el.textContent = text;
  el.className = `message ${type}`;
  setTimeout(() => {
    el.textContent = "";
    el.className = "message";
  }, 5000);
}
