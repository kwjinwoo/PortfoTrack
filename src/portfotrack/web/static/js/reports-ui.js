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
  const emptyState = document.getElementById("report-empty-state");

  try {
    const response = await fetch("/api/snapshots");
    const data = await response.json();

    if (data.length === 0) {
      if (emptyState) {
        emptyState.style.display = "block";
      }
      select.disabled = true;
      return;
    }

    if (emptyState) {
      emptyState.style.display = "none";
    }
    select.disabled = false;

    data.forEach(function (s) {
      const option = document.createElement("option");
      option.value = s.date;
      option.textContent = s.date;
      select.appendChild(option);
    });
  } catch (err) {
    console.error("Failed to load snapshots:", err);
    if (emptyState) {
      emptyState.style.display = "block";
    }
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
    <p><strong>상태:</strong> ${report.is_complete ? "모든 자산 허용치 내" : "일부 자산 허용치 초과"}</p>
  `;
  displayJudgement(report);

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
 * Render a judgement-first summary before the report table.
 */
function displayJudgement(report) {
  const driftCount = document.getElementById("report-drift-count");
  const driftCountDetail = document.getElementById("report-drift-count-detail");
  const largestOver = document.getElementById("report-largest-over");
  const largestOverDetail = document.getElementById("report-largest-over-detail");
  const largestUnder = document.getElementById("report-largest-under");
  const largestUnderDetail = document.getElementById("report-largest-under-detail");
  const highlights = document.getElementById("report-drift-highlights");

  const outsideItems = report.items.filter((item) => !item.is_within_tolerance);
  const overItems = report.items
    .map((item) => ({
      item: item,
      gap: item.current_ratio - item.tolerance.upper,
    }))
    .filter((entry) => entry.gap > 0)
    .sort((a, b) => b.gap - a.gap);
  const underItems = report.items
    .map((item) => ({
      item: item,
      gap: item.tolerance.lower - item.current_ratio,
    }))
    .filter((entry) => entry.gap > 0)
    .sort((a, b) => b.gap - a.gap);

  driftCount.textContent = `${outsideItems.length}개`;
  driftCountDetail.textContent = `${report.items.length}개 자산 중`;
  renderGapCard(largestOver, largestOverDetail, overItems[0], "상한 초과");
  renderGapCard(largestUnder, largestUnderDetail, underItems[0], "하한 미달");

  if (outsideItems.length === 0) {
    highlights.innerHTML = "<p>현재 모든 자산이 설정한 허용 범위 안에 있습니다.</p>";
    return;
  }

  highlights.innerHTML = `
    <h4>확인할 자산</h4>
    <ul>
      ${outsideItems.map(renderDriftHighlight).join("")}
    </ul>
  `;
}

/**
 * Render the largest gap card when a matching item exists.
 */
function renderGapCard(valueEl, detailEl, entry, label) {
  if (!entry) {
    valueEl.textContent = "없음";
    detailEl.textContent = "-";
    return;
  }

  valueEl.textContent = entry.item.asset_name;
  detailEl.textContent = `${label} ${formatPercentPoint(entry.gap)}`;
}

/**
 * Render one out-of-range asset as a plain-language status item.
 */
function renderDriftHighlight(item) {
  const current = formatPercent(item.current_ratio);
  const lower = formatPercent(item.tolerance.lower);
  const upper = formatPercent(item.tolerance.upper);
  let status = "허용 범위 밖";
  if (item.current_ratio > item.tolerance.upper) {
    status = `상한보다 ${formatPercentPoint(item.current_ratio - item.tolerance.upper)} 높음`;
  } else if (item.current_ratio < item.tolerance.lower) {
    status = `하한보다 ${formatPercentPoint(item.tolerance.lower - item.current_ratio)} 낮음`;
  }

  return `
    <li>
      <strong>${item.asset_name}</strong>
      <span>${status} · 현재 ${current}, 허용 ${lower}~${upper}</span>
    </li>
  `;
}

/**
 * Format a ratio as a percentage.
 */
function formatPercent(ratio) {
  return `${(ratio * 100).toFixed(1)}%`;
}

/**
 * Format a ratio gap as a percentage-point value.
 */
function formatPercentPoint(ratio) {
  return `${(ratio * 100).toFixed(1)}%p`;
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
