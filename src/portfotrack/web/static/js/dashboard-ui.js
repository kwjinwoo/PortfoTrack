/* PortfoTrack — Dashboard Summary UI */

"use strict";

document.addEventListener("DOMContentLoaded", function () {
  loadDashboardSummary();
});

/**
 * Load the data needed to summarize the current portfolio state.
 */
async function loadDashboardSummary() {
  try {
    const snapshots = await fetchJson("/api/snapshots");
    const latestSnapshot = snapshots.length > 0 ? snapshots[snapshots.length - 1] : null;
    const target = await fetchOptionalJson("/api/targets");

    renderSnapshotSummary(latestSnapshot);
    renderTargetSummary(target);

    if (!latestSnapshot || !target) {
      renderIncompleteSetup(latestSnapshot, target);
      return;
    }

    const report = await fetchOptionalJson(
      `/api/reports/allocation?snapshot_date=${encodeURIComponent(latestSnapshot.date)}`
    );
    renderReportSummary(report);
  } catch (err) {
    renderDashboardError();
  }
}

/**
 * Fetch JSON from a required endpoint.
 */
async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Request failed: ${url}`);
  }
  return response.json();
}

/**
 * Fetch JSON from an endpoint where a missing resource is an empty state.
 */
async function fetchOptionalJson(url) {
  const response = await fetch(url);
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new Error(`Request failed: ${url}`);
  }
  return response.json();
}

/**
 * Render latest snapshot date and total amount when available.
 */
async function renderSnapshotSummary(snapshot) {
  const dateEl = document.getElementById("latest-snapshot-date");
  const totalEl = document.getElementById("latest-snapshot-total");

  if (!snapshot) {
    dateEl.textContent = "없음";
    totalEl.textContent = "첫 스냅샷이 필요합니다.";
    return;
  }

  dateEl.textContent = snapshot.date;

  try {
    const detail = await fetchJson(`/api/snapshots/${encodeURIComponent(snapshot.date)}`);
    const total = detail.items.reduce((sum, item) => sum + item.amount, 0);
    totalEl.textContent = `${formatKrw(total)} KRW`;
  } catch (err) {
    totalEl.textContent = "총액을 불러올 수 없습니다.";
  }
}

/**
 * Render target setup status.
 */
function renderTargetSummary(target) {
  const statusEl = document.getElementById("target-status");
  const countEl = document.getElementById("target-asset-count");

  if (!target) {
    statusEl.textContent = "미설정";
    countEl.textContent = "타겟 배분이 필요합니다.";
    return;
  }

  const count = target.assets.length;
  statusEl.textContent = count > 0 ? "설정됨" : "비어 있음";
  countEl.textContent = `${count}개 자산`;
}

/**
 * Render guidance for incomplete setup states.
 */
function renderIncompleteSetup(snapshot, target) {
  const driftStatus = document.getElementById("drift-status");
  const driftDetail = document.getElementById("drift-detail");
  const guidance = document.getElementById("dashboard-guidance");

  driftStatus.textContent = "대기";

  if (!target) {
    driftDetail.textContent = "타겟 설정 후 비교할 수 있습니다.";
    guidance.textContent = "먼저 타겟 배분을 만들고 현재 금액 스냅샷을 기록하세요.";
    return;
  }

  if (!snapshot) {
    driftDetail.textContent = "스냅샷 기록 후 비교할 수 있습니다.";
    guidance.textContent = "타겟은 준비되었습니다. 현재 포트폴리오 금액을 스냅샷으로 기록하세요.";
    return;
  }

  driftDetail.textContent = "리포트를 만들 수 없습니다.";
  guidance.textContent = "스냅샷과 타겟을 확인한 뒤 리포트를 다시 열어보세요.";
}

/**
 * Render allocation drift status from the report endpoint.
 */
function renderReportSummary(report) {
  const driftStatus = document.getElementById("drift-status");
  const driftDetail = document.getElementById("drift-detail");
  const guidance = document.getElementById("dashboard-guidance");
  const driftPanel = document.getElementById("dashboard-drift-panel");
  const driftList = document.getElementById("dashboard-drift-list");

  if (!report) {
    renderIncompleteSetup(true, null);
    return;
  }

  const outsideItems = report.items.filter((item) => !item.is_within_tolerance);

  if (outsideItems.length === 0) {
    driftStatus.textContent = "범위 내";
    driftDetail.textContent = "모든 자산이 허용 범위 안에 있습니다.";
    guidance.textContent = "현재 상태가 타겟 범위 안에 있습니다. 새 스냅샷을 기록하며 변화를 추적하세요.";
    driftPanel.style.display = "none";
    return;
  }

  driftStatus.textContent = `${outsideItems.length}개 이탈`;
  driftDetail.textContent = "허용 범위 밖 자산을 확인하세요.";
  guidance.textContent = "리포트에서 허용 범위 밖 자산의 차이를 확인하세요.";
  driftPanel.style.display = "block";
  driftList.innerHTML = "";

  for (const item of outsideItems) {
    const li = document.createElement("li");
    const currentPct = formatPercent(item.current_ratio);
    const lowerPct = formatPercent(item.tolerance.lower);
    const upperPct = formatPercent(item.tolerance.upper);
    li.textContent = `${item.asset_name}: 현재 ${currentPct}, 허용 ${lowerPct}~${upperPct}`;
    driftList.appendChild(li);
  }
}

/**
 * Render a concise error state if dashboard data cannot be loaded.
 */
function renderDashboardError() {
  document.getElementById("latest-snapshot-date").textContent = "오류";
  document.getElementById("target-status").textContent = "오류";
  document.getElementById("drift-status").textContent = "오류";
  document.getElementById("dashboard-guidance").textContent =
    "대시보드 데이터를 불러올 수 없습니다. 각 관리 화면에서 데이터를 확인하세요.";
}

/**
 * Format an integer KRW amount for display.
 */
function formatKrw(amount) {
  return amount.toLocaleString("ko-KR");
}

/**
 * Format a ratio as a percentage.
 */
function formatPercent(ratio) {
  return `${(ratio * 100).toFixed(1)}%`;
}
