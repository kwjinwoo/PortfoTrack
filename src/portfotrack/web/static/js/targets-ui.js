/* PortfoTrack — Target Allocation Management UI */

"use strict";

/** Date of the target currently loaded. */
let _targetDate = null;

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
      status.innerHTML = "<p>타겟이 아직 설정되지 않았습니다.</p>";
      table.style.display = "none";
      createBtn.style.display = "inline-block";
      editBtn.style.display = "none";
      _targetDate = null;
      return;
    }

    const data = await response.json();
    createBtn.style.display = "none";
    _targetDate = data.date || null;

    if (data.assets.length === 0) {
      status.innerHTML = "<p>타겟이 비어 있습니다. 자산을 추가하세요.</p>";
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
      target_ratio: parseFloat(document.getElementById("target-ratio").value),
      lower: parseFloat(document.getElementById("lower-bound").value),
      upper: parseFloat(document.getElementById("upper-bound").value),
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
          <label>목표 비율</label>
          <input type="number" name="target_ratio" step="0.01" min="0" max="1" value="${a.target_ratio}" required>
        </div>
        <div class="form-group">
          <label>하한</label>
          <input type="number" name="lower" step="0.01" min="0" max="1" value="${a.tolerance.lower}" required>
        </div>
        <div class="form-group">
          <label>상한</label>
          <input type="number" name="upper" step="0.01" min="0" max="1" value="${a.tolerance.upper}" required>
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
        <label>목표 비율</label>
        <input type="number" name="target_ratio" step="0.01" min="0" max="1" required placeholder="예: 0.6">
      </div>
      <div class="form-group">
        <label>하한</label>
        <input type="number" name="lower" step="0.01" min="0" max="1" required placeholder="예: 0.5">
      </div>
      <div class="form-group">
        <label>상한</label>
        <input type="number" name="upper" step="0.01" min="0" max="1" required placeholder="예: 0.7">
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
        const targetRatio = parseFloat(row.querySelector('[name="target_ratio"]').value);
        const lower = parseFloat(row.querySelector('[name="lower"]').value);
        const upper = parseFloat(row.querySelector('[name="upper"]').value);

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
      if (Math.abs(totalRatio - 1.0) > 0.0001) {
        const proceed = confirm(
          `총 비율이 ${(totalRatio * 100).toFixed(1)}%입니다 (100% 아님). 그래도 저장하시겠습니까?`
        );
        if (!proceed) return;
      }

      const mode = document.querySelector(
        'input[name="target-save-mode"]:checked'
      ).value;

      try {
        const response = await fetch(`/api/targets/${_targetDate}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ mode: mode, assets: assets }),
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
    });

  document
    .getElementById("edit-target-cancel-btn")
    .addEventListener("click", function () {
      document.getElementById("target-edit-card").style.display = "none";
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
