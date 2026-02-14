/* PortfoTrack — Target Allocation Management UI */

"use strict";

document.addEventListener("DOMContentLoaded", function () {
  loadTarget();
  setupCreateButton();
  setupAddAssetForm();
});

/**
 * Load and display the current target allocation.
 */
async function loadTarget() {
  const status = document.getElementById("target-status");
  const table = document.getElementById("target-table");
  const tbody = document.getElementById("target-assets");
  const createBtn = document.getElementById("create-target-btn");

  try {
    const response = await fetch("/api/targets");

    if (response.status === 404) {
      status.innerHTML = "<p>타겟이 아직 설정되지 않았습니다.</p>";
      table.style.display = "none";
      createBtn.style.display = "inline-block";
      return;
    }

    const data = await response.json();
    createBtn.style.display = "none";

    if (data.assets.length === 0) {
      status.innerHTML = "<p>타겟이 비어 있습니다. 자산을 추가하세요.</p>";
      table.style.display = "none";
      return;
    }

    status.innerHTML = "";
    table.style.display = "table";
    tbody.innerHTML = data.assets
      .map(
        (a) => `
      <tr>
        <td>${a.id}</td>
        <td>${a.name}</td>
        <td>${a.purpose}</td>
        <td>${(a.target_ratio * 100).toFixed(1)}%</td>
        <td>${(a.tolerance.lower * 100).toFixed(1)}% – ${(a.tolerance.upper * 100).toFixed(1)}%</td>
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
