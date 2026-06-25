/* PortfoTrack — Target Allocation Management UI */

"use strict";

/** Date of the target currently loaded. */
let _targetDate = null;
let _pendingTargetSave = null;

document.addEventListener("DOMContentLoaded", function () {
  loadTarget();
  setupCreateButton();
  setupAddAssetForm();
  setupEditButtons();
});

/**
 * Load and display the current target allocation.
 */
async function loadTarget() {
  const status = document.getElementById("target-status");
  const table = document.getElementById("target-table");
  const tbody = document.getElementById("target-assets");
  const createBtn = document.getElementById("create-target-btn");
  const editBtn = document.getElementById("edit-target-btn");

  try {
    const response = await fetch("/api/targets");

    if (response.status === 404) {
      status.innerHTML = `
        <div class="empty-state">
          <strong>타겟 배분이 아직 없습니다.</strong>
          <p>자산군별 목표 비율과 허용 범위를 먼저 만들어 주세요.</p>
          <div class="empty-state-actions">
            <button type="button" class="btn btn-primary" data-create-target-action>새 타겟 생성</button>
          </div>
        </div>
      `;
      table.style.display = "none";
      createBtn.style.display = "inline-block";
      editBtn.style.display = "none";
      _targetDate = null;
      const action = status.querySelector("[data-create-target-action]");
      action.addEventListener("click", function () {
        createBtn.click();
      });
      return;
    }

    const data = await response.json();
    createBtn.style.display = "none";
    _targetDate = data.date || null;

    if (data.assets.length === 0) {
      status.innerHTML = `
        <div class="empty-state">
          <strong>타겟은 있지만 자산이 비어 있습니다.</strong>
          <p>자산군을 추가해 목표 비율 합계를 100%에 가깝게 맞춰 주세요.</p>
          <div class="empty-state-actions">
            <a class="btn btn-primary" href="#add-asset-card">자산 추가하기</a>
          </div>
        </div>
      `;
      table.style.display = "none";
      editBtn.style.display = "none";
      return;
    }

    status.innerHTML = "";
    table.style.display = "table";
    editBtn.style.display = "inline-block";
    tbody.innerHTML = data.assets
      .map(
        (a) => `
      <tr>
        <td>${a.id}</td>
        <td>${a.name}</td>
        <td>${a.purpose}</td>
        <td>${(a.target_ratio * 100).toFixed(1)}%</td>
        <td>${(a.tolerance.lower * 100).toFixed(1)}% – ${(a.tolerance.upper * 100).toFixed(1)}%</td>
        <td>—</td>
      </tr>
    `
      )
      .join("");
  } catch (err) {
    status.innerHTML = "<p>타겟을 불러올 수 없습니다.</p>";
  }
}

/**
 * Set up the create target button.
 */
function setupCreateButton() {
  const btn = document.getElementById("create-target-btn");
  btn.addEventListener("click", async function () {
    try {
      const response = await fetch("/api/targets", { method: "POST" });
      if (response.ok) {
        showMessage("target-message", "새 타겟이 생성되었습니다.", "success");
        loadTarget();
      } else {
        showMessage("target-message", "타겟 생성에 실패했습니다.", "error");
      }
    } catch (err) {
      showMessage("target-message", "네트워크 오류가 발생했습니다.", "error");
    }
  });
}

/**
 * Set up the add asset form submission.
 */
function setupAddAssetForm() {
  const form = document.getElementById("add-asset-form");
  form.addEventListener("submit", async function (e) {
    e.preventDefault();

    const payload = {
      asset_id: document.getElementById("asset-id").value.trim(),
      asset_name: document.getElementById("asset-name").value.trim(),
      purpose: document.getElementById("asset-purpose").value.trim(),
      target_ratio: percentInputToRatio(document.getElementById("target-ratio").value),
      lower: percentInputToRatio(document.getElementById("lower-bound").value),
      upper: percentInputToRatio(document.getElementById("upper-bound").value),
    };

    if (!payload.asset_id || !payload.asset_name || !payload.purpose) {
      showMessage("target-message", "모든 필드를 입력하세요.", "error");
      return;
    }

    if (isNaN(payload.target_ratio) || isNaN(payload.lower) || isNaN(payload.upper)) {
      showMessage("target-message", "숫자 필드를 올바르게 입력하세요.", "error");
      return;
    }

    try {
      const response = await fetch("/api/targets/assets", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        showMessage("target-message", "자산이 추가되었습니다.", "success");
        form.reset();
        loadTarget();
      } else {
        const err = await response.json();
        showMessage(
          "target-message",
          err.error || "자산 추가에 실패했습니다.",
          "error"
        );
      }
    } catch (err) {
      showMessage("target-message", "네트워크 오류가 발생했습니다.", "error");
    }
  });
}

/* --- Edit target --- */

/**
 * Load current target data into the edit card.
 */
async function editTarget() {
  const card = document.getElementById("target-edit-card");
  const container = document.getElementById("edit-assets-container");

  try {
    const response = await fetch("/api/targets");
    if (!response.ok) {
      showMessage("edit-target-message", "타겟을 불러올 수 없습니다.", "error");
      return;
    }

    const data = await response.json();
    _targetDate = data.date || null;

    container.innerHTML = data.assets
      .map(
        (a) => `
      <div class="asset-row form-grid">
        <div class="form-group">
          <label>자산 ID</label>
          <input type="text" name="asset_id" value="${a.id}" required>
        </div>
        <div class="form-group">
          <label>이름</label>
          <input type="text" name="asset_name" value="${a.name}" required>
        </div>
        <div class="form-group">
          <label>용도</label>
          <input type="text" name="purpose" value="${a.purpose}" required>
        </div>
        <div class="form-group">
          <label>목표 비율 (%)</label>
          <input type="number" name="target_ratio" step="0.1" min="0" max="100" value="${ratioToPercentInput(a.target_ratio)}" required>
        </div>
        <div class="form-group">
          <label>하한 (%)</label>
          <input type="number" name="lower" step="0.1" min="0" max="100" value="${ratioToPercentInput(a.tolerance.lower)}" required>
        </div>
        <div class="form-group">
          <label>상한 (%)</label>
          <input type="number" name="upper" step="0.1" min="0" max="100" value="${ratioToPercentInput(a.tolerance.upper)}" required>
        </div>
        <div class="form-group">
          <button type="button" class="btn btn-small btn-danger" onclick="this.closest('.asset-row').remove()">삭제</button>
        </div>
      </div>
    `
      )
      .join("");

    card.style.display = "block";
  } catch (err) {
    showMessage("edit-target-message", "오류가 발생했습니다.", "error");
  }
}

/**
 * Set up the edit card buttons (edit, add asset, save, cancel).
 */
function setupEditButtons() {
  document
    .getElementById("confirm-target-save-btn")
    .addEventListener("click", async function () {
      if (!_pendingTargetSave) return;
      hideRatioWarning();
      await saveTargetPayload(_pendingTargetSave);
      _pendingTargetSave = null;
    });

  document
    .getElementById("cancel-target-save-btn")
    .addEventListener("click", function () {
      _pendingTargetSave = null;
      hideRatioWarning();
    });

  document.getElementById("edit-target-btn").addEventListener("click", function () {
    editTarget();
  });

  document.getElementById("edit-add-asset-btn").addEventListener("click", function () {
    const container = document.getElementById("edit-assets-container");
    const row = document.createElement("div");
    row.className = "asset-row form-grid";
    row.innerHTML = `
      <div class="form-group">
        <label>자산 ID</label>
        <input type="text" name="asset_id" required placeholder="예: us_equity">
      </div>
      <div class="form-group">
        <label>이름</label>
        <input type="text" name="asset_name" required placeholder="예: US Equity">
      </div>
      <div class="form-group">
        <label>용도</label>
        <input type="text" name="purpose" required placeholder="예: growth">
      </div>
      <div class="form-group">
        <label>목표 비율 (%)</label>
        <input type="number" name="target_ratio" step="0.1" min="0" max="100" required placeholder="예: 60">
      </div>
      <div class="form-group">
        <label>하한 (%)</label>
        <input type="number" name="lower" step="0.1" min="0" max="100" required placeholder="예: 50">
      </div>
      <div class="form-group">
        <label>상한 (%)</label>
        <input type="number" name="upper" step="0.1" min="0" max="100" required placeholder="예: 70">
      </div>
      <div class="form-group">
        <button type="button" class="btn btn-small btn-danger" onclick="this.closest('.asset-row').remove()">삭제</button>
      </div>
    `;
    container.appendChild(row);
  });

  document
    .getElementById("edit-target-save-btn")
    .addEventListener("click", async function () {
      if (!_targetDate) {
        showMessage("edit-target-message", "타겟 날짜를 알 수 없습니다.", "error");
        return;
      }

      const container = document.getElementById("edit-assets-container");
      const rows = container.querySelectorAll(".asset-row");
      const assets = [];

      for (const row of rows) {
        const assetId = row.querySelector('[name="asset_id"]').value.trim();
        const assetName = row.querySelector('[name="asset_name"]').value.trim();
        const purpose = row.querySelector('[name="purpose"]').value.trim();
        const targetRatio = percentInputToRatio(row.querySelector('[name="target_ratio"]').value);
        const lower = percentInputToRatio(row.querySelector('[name="lower"]').value);
        const upper = percentInputToRatio(row.querySelector('[name="upper"]').value);

        if (!assetId || !assetName || !purpose) {
          showMessage("edit-target-message", "모든 텍스트 필드를 입력하세요.", "error");
          return;
        }

        if (isNaN(targetRatio) || isNaN(lower) || isNaN(upper)) {
          showMessage("edit-target-message", "숫자 필드를 올바르게 입력하세요.", "error");
          return;
        }

        assets.push({
          asset_id: assetId,
          asset_name: assetName,
          purpose: purpose,
          target_ratio: targetRatio,
          lower: lower,
          upper: upper,
        });
      }

      if (assets.length === 0) {
        showMessage("edit-target-message", "최소 하나의 자산이 필요합니다.", "error");
        return;
      }

      // Pre-validate total ratio on client side
      const totalRatio = assets.reduce((sum, a) => sum + a.target_ratio, 0);
      const mode = document.querySelector(
        'input[name="target-save-mode"]:checked'
      ).value;
      const payload = { mode: mode, assets: assets };

      if (Math.abs(totalRatio - 1.0) > 0.0001) {
        _pendingTargetSave = payload;
        showRatioWarning(totalRatio);
        return;
      }

      hideRatioWarning();
      await saveTargetPayload(payload);
    });

  document
    .getElementById("edit-target-cancel-btn")
    .addEventListener("click", function () {
      document.getElementById("target-edit-card").style.display = "none";
    });
}

async function saveTargetPayload(payload) {
  try {
    const response = await fetch(`/api/targets/${_targetDate}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (response.ok) {
      const data = await response.json();
      let msg = "타겟이 저장되었습니다.";
      if (data.warnings && data.warnings.length > 0) {
        msg += " ⚠ " + data.warnings.join("; ");
      }
      showMessage("edit-target-message", msg, "success");
      document.getElementById("target-edit-card").style.display = "none";
      loadTarget();
    } else {
      const err = await response.json();
      showMessage(
        "edit-target-message",
        err.error || "저장에 실패했습니다.",
        "error"
      );
    }
  } catch (err) {
    showMessage("edit-target-message", "네트워크 오류가 발생했습니다.", "error");
  }
}

function showRatioWarning(totalRatio) {
  const warning = document.getElementById("target-ratio-warning");
  const detail = document.getElementById("target-ratio-warning-detail");
  const totalPercent = (totalRatio * 100).toFixed(1);
  const gapPercent = Math.abs((1.0 - totalRatio) * 100).toFixed(1);
  const direction = totalRatio > 1.0 ? "초과" : "부족";

  detail.textContent = `현재 합계는 ${totalPercent}%로 100%보다 ${gapPercent}%p ${direction}합니다.`;
  warning.classList.remove("is-hidden");
}

function hideRatioWarning() {
  document.getElementById("target-ratio-warning").classList.add("is-hidden");
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

/**
 * Convert a user-facing percent input into the ratio used by the API.
 */
function percentInputToRatio(value) {
  const percent = parseFloat(value);
  if (isNaN(percent)) {
    return NaN;
  }
  return percent / 100;
}

/**
 * Convert a stored ratio into a compact percent value for edit inputs.
 */
function ratioToPercentInput(ratio) {
  return Number((ratio * 100).toFixed(4)).toString();
}
