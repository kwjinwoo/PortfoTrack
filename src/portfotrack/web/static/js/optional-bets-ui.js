/* PortfoTrack — Optional Bets Management UI */

"use strict";

/** Date of the currently loaded optional bet snapshot. */
let _obDate = null;

document.addEventListener("DOMContentLoaded", function () {
    loadLatest();
    loadFileList();
    loadSnapshotList();
    setupCreateButton();
    setupAddForm();
    setupEditButtons();
    setupBreachForm();
});

// ---------------------------------------------------------------------------
// Load & display latest snapshot
// ---------------------------------------------------------------------------

async function loadLatest() {
    const status = document.getElementById("ob-status");
    const table = document.getElementById("ob-table");
    const tbody = document.getElementById("ob-items");
    const createBtn = document.getElementById("create-ob-btn");
    const editBtn = document.getElementById("edit-ob-btn");

    try {
        const response = await fetch("/api/optional-bets/latest");

        if (response.status === 404) {
            status.innerHTML = "<p>옵셔널 벳이 아직 없습니다.</p>";
            table.style.display = "none";
            createBtn.style.display = "inline-block";
            editBtn.style.display = "none";
            _obDate = null;
            return;
        }

        const data = await response.json();
        createBtn.style.display = "none";
        _obDate = data.date || null;

        if (data.items.length === 0) {
            status.innerHTML = "<p>옵셔널 벳이 비어 있습니다. 아이템을 추가하세요.</p>";
            table.style.display = "none";
            editBtn.style.display = "none";
            return;
        }

        status.innerHTML = "";
        table.style.display = "table";
        editBtn.style.display = "inline-block";
        renderItems(tbody, data.items);
        document.getElementById("ob-total").innerHTML =
            "<strong>" + data.items.reduce((s, i) => s + i.amount, 0).toLocaleString() + "</strong>";
    } catch {
        status.innerHTML = "<p class='error'>데이터를 불러오는 중 오류가 발생했습니다.</p>";
    }
}

function renderItems(tbody, items) {
    tbody.innerHTML = items
        .map(
            (item) => `
    <tr>
      <td>${item.asset_id}</td>
      <td>${item.name}</td>
      <td>${(item.cap_ratio * 100).toFixed(1)}%</td>
      <td>${item.amount.toLocaleString()}</td>
      <td>
        <button class="btn btn-sm btn-danger" onclick="removeItem('${item.asset_id}')">삭제</button>
      </td>
    </tr>`
        )
        .join("");
}

// ---------------------------------------------------------------------------
// File list
// ---------------------------------------------------------------------------

async function loadFileList() {
    const list = document.getElementById("ob-file-list");
    try {
        const response = await fetch("/api/optional-bets");
        const data = await response.json();

        if (data.length === 0) {
            list.innerHTML = "<li>파일 없음</li>";
            return;
        }

        list.innerHTML = data
            .map((f) => `<li>${f.date} — ${f.filename}</li>`)
            .join("");
    } catch {
        list.innerHTML = "<li>목록을 불러오는 중 오류 발생</li>";
    }
}

// ---------------------------------------------------------------------------
// Create new snapshot
// ---------------------------------------------------------------------------

function setupCreateButton() {
    const btn = document.getElementById("create-ob-btn");
    btn.addEventListener("click", async function () {
        try {
            const response = await fetch("/api/optional-bets", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ items: [] }),
            });

            if (response.ok) {
                loadLatest();
                loadFileList();
            }
        } catch {
            // ignore
        }
    });
}

// ---------------------------------------------------------------------------
// Add item form
// ---------------------------------------------------------------------------

function setupAddForm() {
    const form = document.getElementById("add-ob-form");
    const msg = document.getElementById("ob-message");

    form.addEventListener("submit", async function (e) {
        e.preventDefault();
        msg.textContent = "";

        const payload = {
            asset_id: document.getElementById("ob-asset-id").value.trim(),
            name: document.getElementById("ob-name").value.trim(),
            cap_ratio: parseFloat(document.getElementById("ob-cap-ratio").value),
            amount: parseInt(document.getElementById("ob-amount").value, 10),
        };

        try {
            const response = await fetch("/api/optional-bets/items", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });

            const data = await response.json();

            if (response.ok) {
                msg.textContent = "아이템이 추가되었습니다.";
                msg.className = "message success";
                form.reset();
                loadLatest();
                loadFileList();
            } else {
                msg.textContent = data.error || "추가 실패";
                msg.className = "message error";
            }
        } catch {
            msg.textContent = "요청 중 오류가 발생했습니다.";
            msg.className = "message error";
        }
    });
}

// ---------------------------------------------------------------------------
// Remove item
// ---------------------------------------------------------------------------

async function removeItem(assetId) {
    try {
        const response = await fetch(`/api/optional-bets/items/${assetId}`, {
            method: "DELETE",
        });

        if (response.ok) {
            loadLatest();
            loadFileList();
        }
    } catch {
        // ignore
    }
}

// ---------------------------------------------------------------------------
// Edit mode
// ---------------------------------------------------------------------------

function setupEditButtons() {
    const editBtn = document.getElementById("edit-ob-btn");
    const editCard = document.getElementById("ob-edit-card");
    const cancelBtn = document.getElementById("edit-ob-cancel-btn");
    const saveBtn = document.getElementById("edit-ob-save-btn");
    const addBtn = document.getElementById("edit-add-ob-btn");

    editBtn.addEventListener("click", async function () {
        editCard.style.display = "block";
        editBtn.style.display = "none";

        const response = await fetch("/api/optional-bets/latest");
        if (!response.ok) return;
        const data = await response.json();
        renderEditForm(data.items);
    });

    cancelBtn.addEventListener("click", function () {
        editCard.style.display = "none";
        document.getElementById("edit-ob-btn").style.display = "inline-block";
        document.getElementById("edit-ob-message").textContent = "";
    });

    addBtn.addEventListener("click", function () {
        const container = document.getElementById("edit-ob-container");
        container.appendChild(createEditRow("", "", 0.05, 0));
    });

    saveBtn.addEventListener("click", async function () {
        const msg = document.getElementById("edit-ob-message");
        msg.textContent = "";

        const rows = document.querySelectorAll("#edit-ob-container .edit-row");
        const items = [];
        for (const row of rows) {
            items.push({
                asset_id: row.querySelector(".edit-asset-id").value.trim(),
                name: row.querySelector(".edit-name").value.trim(),
                cap_ratio: parseFloat(row.querySelector(".edit-cap-ratio").value),
                amount: parseInt(row.querySelector(".edit-amount").value, 10),
            });
        }

        const mode = document.querySelector('input[name="ob-save-mode"]:checked').value;

        if (!_obDate) {
            msg.textContent = "저장할 기존 파일이 없습니다.";
            msg.className = "message error";
            return;
        }

        try {
            const response = await fetch(`/api/optional-bets/${_obDate}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ mode, items }),
            });

            const data = await response.json();

            if (response.ok) {
                msg.textContent = "저장되었습니다.";
                msg.className = "message success";
                editCard.style.display = "none";
                loadLatest();
                loadFileList();
            } else {
                msg.textContent = data.error || "저장 실패";
                msg.className = "message error";
            }
        } catch {
            msg.textContent = "요청 중 오류가 발생했습니다.";
            msg.className = "message error";
        }
    });
}

function renderEditForm(items) {
    const container = document.getElementById("edit-ob-container");
    container.innerHTML = "";
    items.forEach((item) => {
        container.appendChild(
            createEditRow(item.asset_id, item.name, item.cap_ratio, item.amount)
        );
    });
}

function createEditRow(assetId, name, capRatio, amount) {
    const div = document.createElement("div");
    div.className = "edit-row form-grid";
    div.style.marginBottom = "0.5rem";
    div.innerHTML = `
    <input type="text" class="edit-asset-id" value="${assetId}" placeholder="자산 ID">
    <input type="text" class="edit-name" value="${name}" placeholder="이름">
    <input type="number" class="edit-cap-ratio" value="${capRatio}" step="0.01" min="0.01" max="0.99" placeholder="캡 비율">
    <input type="number" class="edit-amount" value="${amount}" min="0" placeholder="금액">
    <button type="button" class="btn btn-sm btn-danger" onclick="this.parentElement.remove()">삭제</button>
  `;
    return div;
}

// ---------------------------------------------------------------------------
// Breach check
// ---------------------------------------------------------------------------

async function loadSnapshotList() {
    const select = document.getElementById("snapshot-select");
    try {
        const response = await fetch("/api/snapshots");
        const data = await response.json();
        for (const snap of data) {
            const option = document.createElement("option");
            option.value = snap.filename;
            option.textContent = snap.date;
            select.appendChild(option);
        }
    } catch {
        // keep only the default option
    }
}

function setupBreachForm() {
    const form = document.getElementById("breach-form");
    const result = document.getElementById("breach-result");

    form.addEventListener("submit", async function (e) {
        e.preventDefault();
        result.innerHTML = "";

        const snapshot = document.getElementById("snapshot-select").value;
        const params = snapshot ? `?snapshot=${encodeURIComponent(snapshot)}` : "";

        try {
            const response = await fetch(
                `/api/optional-bets/breaches${params}`
            );
            const data = await response.json();

            if (!response.ok) {
                result.innerHTML = `<p class="error">${data.error}</p>`;
                return;
            }

            let info = `<p>스냅샷 날짜: <strong>${data.snapshot_date}</strong> | 메인 포트폴리오 총액: <strong>${data.main_portfolio_total.toLocaleString()} KRW</strong></p>`;

            if (data.breaches.length === 0) {
                result.innerHTML = info + "<p class='success'>캡 초과 항목이 없습니다.</p>";
                return;
            }

            let html = info + "<table><thead><tr><th>자산 ID</th><th>이름</th><th>실제 비율</th><th>캡 비율</th></tr></thead><tbody>";
            for (const b of data.breaches) {
                html += `<tr>
          <td>${b.asset_id}</td>
          <td>${b.name}</td>
          <td>${(b.actual_ratio * 100).toFixed(2)}%</td>
          <td>${(b.cap_ratio * 100).toFixed(2)}%</td>
        </tr>`;
            }
            html += "</tbody></table>";
            result.innerHTML = html;
        } catch {
            result.innerHTML = "<p class='error'>체크 중 오류가 발생했습니다.</p>";
        }
    });
}
