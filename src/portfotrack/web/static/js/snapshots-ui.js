/* PortfoTrack — Snapshot Management UI */

"use strict";

document.addEventListener("DOMContentLoaded", function () {
  loadSnapshots();
  loadTargetAssets();
  setupCreateForm();
  setupAddItemButton();
});

/**
 * Load and display the list of available snapshots.
 */
async function loadSnapshots() {
  const tbody = document.getElementById("snapshot-list");

  try {
    const response = await fetch("/api/snapshots");
    const data = await response.json();

    if (data.length === 0) {
      tbody.innerHTML = '<tr><td colspan="3">저장된 스냅샷이 없습니다.</td></tr>';
      return;
    }

    tbody.innerHTML = data
      .map(
        (s) => `
      <tr>
        <td>${s.date}</td>
        <td>${s.filename}</td>
        <td><button class="btn btn-small" onclick="viewSnapshot('${s.date}')">보기</button></td>
      </tr>
    `
      )
      .join("");
  } catch (err) {
    tbody.innerHTML =
      '<tr><td colspan="3">스냅샷 목록을 불러올 수 없습니다.</td></tr>';
  }
}

/**
 * View snapshot detail by date.
 */
async function viewSnapshot(date) {
  const card = document.getElementById("snapshot-detail-card");
  const dateSpan = document.getElementById("snapshot-detail-date");
  const tbody = document.getElementById("snapshot-detail-items");

  try {
    const response = await fetch(`/api/snapshots/${date}`);
    if (!response.ok) {
      showMessage("snapshot-message", "스냅샷을 불러올 수 없습니다.", "error");
      return;
    }

    const data = await response.json();
    dateSpan.textContent = data.date;
    tbody.innerHTML = data.items
      .map(
        (item) => `
      <tr>
        <td>${item.asset_id}</td>
        <td>${item.label}</td>
        <td>${item.amount.toLocaleString()}</td>
      </tr>
    `
      )
      .join("");

    card.style.display = "block";
  } catch (err) {
    showMessage("snapshot-message", "오류가 발생했습니다.", "error");
  }
}

/**
 * Cached target assets for building select dropdowns.
 * @type {Array<{id: string, name: string, purpose: string}>}
 */
let _cachedAssets = [];

/**
 * Load target assets and populate all asset_id dropdowns.
 */
async function loadTargetAssets() {
  const warning = document.getElementById("no-target-warning");

  try {
    const response = await fetch("/api/targets/assets");
    if (!response.ok) {
      warning.style.display = "block";
      _cachedAssets = [];
      _updateAllAssetSelects();
      return;
    }

    _cachedAssets = await response.json();
    warning.style.display = "none";
    _updateAllAssetSelects();
  } catch (err) {
    warning.style.display = "block";
    _cachedAssets = [];
    _updateAllAssetSelects();
  }
}

/**
 * Build option HTML for asset select dropdowns.
 */
function _buildAssetOptions() {
  if (_cachedAssets.length === 0) {
    return '<option value="">사용 가능한 자산 없음</option>';
  }
  const opts = ['<option value="">-- 자산 선택 --</option>'];
  for (const a of _cachedAssets) {
    opts.push(`<option value="${a.id}">${a.name} (${a.id})</option>`);
  }
  return opts.join("");
}

/**
 * Update all asset_id select elements with current cached assets.
 */
function _updateAllAssetSelects() {
  const selects = document.querySelectorAll(
    '#snapshot-items-container select[name="asset_id"]'
  );
  const html = _buildAssetOptions();
  for (const sel of selects) {
    const current = sel.value;
    sel.innerHTML = html;
    if (current) sel.value = current;
  }
}

/**
 * Set up the create snapshot form submission.
 */
function setupCreateForm() {
  const form = document.getElementById("create-snapshot-form");
  form.addEventListener("submit", async function (e) {
    e.preventDefault();

    const rows = document.querySelectorAll(
      "#snapshot-items-container .item-row"
    );
    const items = [];

    for (const row of rows) {
      const assetId = row.querySelector('[name="asset_id"]').value.trim();
      const label = row.querySelector('[name="label"]').value.trim();
      const amount = parseInt(row.querySelector('[name="amount"]').value, 10);

      if (!assetId || !label || isNaN(amount)) {
        showMessage("snapshot-message", "모든 필드를 올바르게 입력하세요.", "error");
        return;
      }

      items.push({ asset_id: assetId, label: label, amount: amount });
    }

    try {
      const response = await fetch("/api/snapshots", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ items: items }),
      });

      if (response.ok) {
        showMessage("snapshot-message", "스냅샷이 저장되었습니다.", "success");
        form.reset();
        loadSnapshots();
      } else {
        const err = await response.json();
        showMessage(
          "snapshot-message",
          err.error || "저장에 실패했습니다.",
          "error"
        );
      }
    } catch (err) {
      showMessage("snapshot-message", "네트워크 오류가 발생했습니다.", "error");
    }
  });
}

/**
 * Add another item row to the create form.
 */
function setupAddItemButton() {
  const btn = document.getElementById("add-item-btn");
  btn.addEventListener("click", function () {
    const container = document.getElementById("snapshot-items-container");
    const row = document.createElement("div");
    row.className = "item-row";
    row.innerHTML = `
      <label>자산 ID</label>
      <select name="asset_id" required>
        ${_buildAssetOptions()}
      </select>
      <label>라벨</label>
      <input type="text" name="label" required placeholder="예: S&P500">
      <label>금액 (KRW)</label>
      <input type="number" name="amount" required placeholder="예: 5000000">
      <button type="button" class="btn btn-small btn-danger" onclick="this.parentElement.remove()">삭제</button>
    `;
    container.appendChild(row);
  });
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
