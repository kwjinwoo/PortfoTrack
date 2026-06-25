/* PortfoTrack — Snapshot Management UI */

"use strict";

document.addEventListener("DOMContentLoaded", function () {
  loadSnapshots();
  loadTargetAssets();
  setupCreateForm();
  setupAddItemButton();
  setupEditButtons();
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
      tbody.innerHTML = `
        <tr>
          <td colspan="3">
            <div class="empty-state">
              <strong>저장된 스냅샷이 없습니다.</strong>
              <p>현재 포트폴리오 금액을 기록하면 리포트와 추이를 볼 수 있습니다.</p>
              <div class="empty-state-actions">
                <a class="btn btn-primary" href="#create-snapshot-form">스냅샷 기록하기</a>
              </div>
            </div>
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = data
      .map(
        (s) => `
      <tr>
        <td>${s.date}</td>
        <td>${s.filename}</td>
        <td>
          <button class="btn btn-small" onclick="viewSnapshot('${s.date}')">보기</button>
          <button class="btn btn-small btn-secondary" onclick="editSnapshot('${s.date}')">편집</button>
        </td>
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
    row.className = "item-row snapshot-item-row";
    row.innerHTML = `
      <div class="form-group">
        <label>자산 ID</label>
        <select name="asset_id" required>
          ${_buildAssetOptions()}
        </select>
      </div>
      <div class="form-group">
        <label>라벨</label>
        <input type="text" name="label" required placeholder="예: S&P500">
      </div>
      <div class="form-group">
        <label>금액 (KRW)</label>
        <input class="amount-input" type="number" name="amount" inputmode="numeric" required placeholder="예: 5000000">
      </div>
      <div class="row-action">
        <button type="button" class="btn btn-small btn-danger" onclick="this.closest('.item-row').remove()">삭제</button>
      </div>
    `;
    container.appendChild(row);
  });
}

/* --- Edit snapshot --- */

/** Date of the snapshot currently being edited. */
let _editingDate = null;

/**
 * Load a snapshot for editing.
 */
async function editSnapshot(date) {
  const card = document.getElementById("snapshot-edit-card");
  const dateSpan = document.getElementById("edit-snapshot-date");
  const container = document.getElementById("edit-items-container");

  try {
    const response = await fetch(`/api/snapshots/${date}`);
    if (!response.ok) {
      showMessage("edit-message", "스냅샷을 불러올 수 없습니다.", "error");
      return;
    }

    const data = await response.json();
    _editingDate = date;
    dateSpan.textContent = data.date;

    container.innerHTML = data.items
      .map(
        (item) => `
      <div class="item-row snapshot-item-row">
        <div class="form-group">
          <label>자산 ID</label>
          <select name="asset_id" required>${_buildAssetOptionsWithSelected(item.asset_id)}</select>
        </div>
        <div class="form-group">
          <label>라벨</label>
          <input type="text" name="label" required value="${item.label}">
        </div>
        <div class="form-group">
          <label>금액 (KRW)</label>
          <input class="amount-input" type="number" name="amount" inputmode="numeric" required value="${item.amount}">
        </div>
        <div class="row-action">
          <button type="button" class="btn btn-small btn-danger" onclick="this.closest('.item-row').remove()">삭제</button>
        </div>
      </div>
    `
      )
      .join("");

    card.style.display = "block";
  } catch (err) {
    showMessage("edit-message", "오류가 발생했습니다.", "error");
  }
}

/**
 * Build asset select options with a pre-selected value.
 */
function _buildAssetOptionsWithSelected(selectedId) {
  if (_cachedAssets.length === 0) {
    return `<option value="${selectedId}" selected>${selectedId}</option>`;
  }
  const opts = ['<option value="">-- 자산 선택 --</option>'];
  for (const a of _cachedAssets) {
    const sel = a.id === selectedId ? " selected" : "";
    opts.push(`<option value="${a.id}"${sel}>${a.name} (${a.id})</option>`);
  }
  return opts.join("");
}

/**
 * Set up the edit card buttons (add item and save).
 */
function setupEditButtons() {
  document.getElementById("edit-add-item-btn").addEventListener("click", function () {
    const container = document.getElementById("edit-items-container");
    const row = document.createElement("div");
    row.className = "item-row snapshot-item-row";
    row.innerHTML = `
      <div class="form-group">
        <label>자산 ID</label>
        <select name="asset_id" required>${_buildAssetOptions()}</select>
      </div>
      <div class="form-group">
        <label>라벨</label>
        <input type="text" name="label" required placeholder="예: S&P500">
      </div>
      <div class="form-group">
        <label>금액 (KRW)</label>
        <input class="amount-input" type="number" name="amount" inputmode="numeric" required placeholder="예: 5000000">
      </div>
      <div class="row-action">
        <button type="button" class="btn btn-small btn-danger" onclick="this.closest('.item-row').remove()">삭제</button>
      </div>
    `;
    container.appendChild(row);
  });

  document.getElementById("edit-save-btn").addEventListener("click", async function () {
    if (!_editingDate) return;

    const container = document.getElementById("edit-items-container");
    const rows = container.querySelectorAll(".item-row");
    const items = [];

    for (const row of rows) {
      const assetId = row.querySelector('[name="asset_id"]').value.trim();
      const label = row.querySelector('[name="label"]').value.trim();
      const amount = parseInt(row.querySelector('[name="amount"]').value, 10);

      if (!assetId || !label || isNaN(amount)) {
        showMessage("edit-message", "모든 필드를 올바르게 입력하세요.", "error");
        return;
      }

      items.push({ asset_id: assetId, label: label, amount: amount });
    }

    if (items.length === 0) {
      showMessage("edit-message", "최소 하나의 항목이 필요합니다.", "error");
      return;
    }

    const mode = document.querySelector('input[name="save-mode"]:checked').value;

    try {
      const response = await fetch(`/api/snapshots/${_editingDate}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode: mode, items: items }),
      });

      if (response.ok) {
        showMessage("edit-message", "스냅샷이 저장되었습니다.", "success");
        loadSnapshots();
      } else {
        const err = await response.json();
        showMessage("edit-message", err.error || "저장에 실패했습니다.", "error");
      }
    } catch (err) {
      showMessage("edit-message", "네트워크 오류가 발생했습니다.", "error");
    }
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
