const statusBanner = document.getElementById("status-banner");
const scheduleDateInput = document.getElementById("schedule-date");
scheduleDateInput.value = new Date().toISOString().split("T")[0];

function showBanner(msg, isError = false) {
    statusBanner.textContent = msg;
    statusBanner.className = `status-banner ${isError ? "err" : "ok"}`;
    setTimeout(() => statusBanner.classList.add("hidden"), 4000);
}

async function loadPatients(query = "") {
    const res = await fetch(`/api/patients?query=${encodeURIComponent(query)}`);
    const patients = await res.json();
    const list = document.getElementById("patients-list");
    const select = document.getElementById("schedule-patient");
    list.innerHTML = "";
    select.innerHTML = "";

    patients.forEach(p => {
        const li = document.createElement("li");
        const infoSpan = document.createElement("span");
        infoSpan.innerHTML = `<strong>${p.full_name}</strong> (${p.phone_number}, ${p.birth_date})`;

        const actionsDiv = document.createElement("div");
        actionsDiv.className = "item-actions";

        const editBtn = document.createElement("button");
        editBtn.textContent = "Редагувати";
        editBtn.className = "btn-secondary btn-sm";
        editBtn.onclick = () => editPatient(p.id, p.full_name, p.phone_number);

        const delBtn = document.createElement("button");
        delBtn.textContent = "Видалити";
        delBtn.className = "btn-danger btn-sm";
        delBtn.onclick = () => deletePatient(p.id);

        actionsDiv.appendChild(editBtn);
        actionsDiv.appendChild(delBtn);
        li.appendChild(infoSpan);
        li.appendChild(actionsDiv);
        list.appendChild(li);

        const opt = document.createElement("option");
        opt.value = p.id;
        opt.textContent = `${p.full_name} (${p.phone_number})`;
        select.appendChild(opt);
    });
}

async function editPatient(id, currentName, currentPhone) {
    const newName = prompt("Введіть нове ПІБ пацієнта:", currentName);
    if (newName === null) return;
    const newPhone = prompt("Введіть новий номер телефону:", currentPhone);
    if (newPhone === null) return;

    const res = await fetch(`/api/patients/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            full_name: newName.trim(),
            phone_number: newPhone.trim()
        })
    });

    if (res.ok) {
        showBanner("Дані пацієнта оновлено!");
        await loadPatients(document.getElementById("pat-search").value);
        await loadSchedule();
        await loadAuditLogs();
    } else {
        const err = await res.json();
        showBanner(err.detail || "Помилка оновлення даних пацієнта", true);
    }
}

async function deletePatient(id) {
    await fetch(`/api/patients/${id}`, { method: "DELETE" });
    await loadPatients(document.getElementById("pat-search").value);
    await loadSchedule();
    await loadAuditLogs();
}

async function loadDoctors(specialty = "") {
    const res = await fetch(`/api/doctors?specialty=${encodeURIComponent(specialty)}`);
    const doctors = await res.json();
    const list = document.getElementById("doctors-list");
    const select = document.getElementById("schedule-doctor");
    list.innerHTML = "";
    select.innerHTML = "";

    doctors.forEach(d => {
        const li = document.createElement("li");
        li.innerHTML = `<span><strong>${d.full_name}</strong> — ${d.specialty} (каб. ${d.room_number})</span>`;
        list.appendChild(li);

        const opt = document.createElement("option");
        opt.value = d.id;
        opt.textContent = `${d.full_name} (${d.specialty})`;
        select.appendChild(opt);
    });

    await loadSchedule();
}

async function loadSchedule() {
    const docId = document.getElementById("schedule-doctor").value;
    const dateVal = scheduleDateInput.value;
    const container = document.getElementById("slots-container");
    if (!docId || !dateVal) {
        container.innerHTML = "<p>Додайте та оберіть лікаря для перегляду розкладу.</p>";
        return;
    }

    const res = await fetch(`/api/doctors/${docId}/schedule?date=${dateVal}`);
    if (!res.ok) return;
    const data = await res.json();
    container.innerHTML = "";

    data.slots.forEach(slot => {
        const card = document.createElement("div");
        card.className = `slot-card ${slot.is_available ? "slot-free" : "slot-booked"}`;
        if (slot.is_available) {
            card.innerHTML = `
                <div class="slot-time">${slot.time}</div>
                <div style="font-size:12px;margin-bottom:6px;">Вільно</div>
                <button onclick="bookSlot('${slot.time}')">Записати</button>
            `;
        } else {
            card.innerHTML = `
                <div class="slot-time">${slot.time}</div>
                <div style="font-size:12px;margin-bottom:6px;">${slot.patient_name}</div>
                <div class="slot-actions">
                    <button onclick="rescheduleAppointment(${slot.appointment_id}, '${slot.time}')" class="btn-secondary btn-sm">Перенести</button>
                    <button onclick="cancelAppointment(${slot.appointment_id})" class="btn-danger btn-sm">Скасувати</button>
                </div>
            `;
        }
        container.appendChild(card);
    });
}

async function rescheduleAppointment(appId, currentTimeStr) {
    const dateVal = scheduleDateInput.value;
    const newTimeStr = prompt("Введіть новий час прийому (ГГ:ХХ, напр. 14:30):", currentTimeStr);
    if (!newTimeStr || newTimeStr.trim() === currentTimeStr) return;

    const cleanTime = newTimeStr.trim();
    const res = await fetch(`/api/appointments/${appId}/reschedule`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            new_time: `${dateVal}T${cleanTime}:00`
        })
    });

    if (res.ok) {
        showBanner(`Запис перенесено на ${cleanTime}!`);
        await loadSchedule();
        await loadAuditLogs();
    } else {
        const err = await res.json();
        showBanner(err.detail || "Помилка перенесення запису", true);
    }
}

async function bookSlot(timeStr) {
    const docId = Number(document.getElementById("schedule-doctor").value);
    const patId = Number(document.getElementById("schedule-patient").value);
    const dateVal = scheduleDateInput.value;
    if (!docId || !patId) {
        showBanner("Оберіть лікаря та пацієнта перед записом!", true);
        return;
    }

    const res = await fetch("/api/appointments", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            doctor_id: docId,
            patient_id: patId,
            appointment_time: `${dateVal}T${timeStr}:00`
        })
    });

    if (res.status === 201) {
        showBanner("Запис успішно створено!");
        await loadSchedule();
        await loadAuditLogs();
    } else {
        const err = await res.json();
        showBanner(err.detail || "Помилка бронювання", true);
    }
}

async function cancelAppointment(appId) {
    const res = await fetch(`/api/appointments/${appId}`, { method: "DELETE" });
    if (res.ok) {
        showBanner("Запис скасовано.");
        await loadSchedule();
        await loadAuditLogs();
    }
}

async function loadAuditLogs() {
    const res = await fetch("/api/audit-logs");
    const logs = await res.json();
    const list = document.getElementById("audit-list");
    list.innerHTML = "";
    logs.forEach(l => {
        const li = document.createElement("li");
        li.textContent = `[${l.action_type}] ${l.entity_name} #${l.entity_id}: ${l.details}`;
        list.appendChild(li);
    });
}

document.getElementById("patient-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    await fetch("/api/patients", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            full_name: document.getElementById("pat-name").value,
            phone_number: document.getElementById("pat-phone").value,
            birth_date: document.getElementById("pat-birth").value
        })
    });
    e.target.reset();
    await loadPatients();
    await loadAuditLogs();
});

document.getElementById("doctor-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    await fetch("/api/doctors", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            full_name: document.getElementById("doc-name").value,
            specialty: document.getElementById("doc-spec").value,
            room_number: document.getElementById("doc-room").value
        })
    });
    e.target.reset();
    await loadDoctors();
    await loadAuditLogs();
});

document.getElementById("pat-search").addEventListener("input", (e) => loadPatients(e.target.value));
document.getElementById("doc-filter").addEventListener("input", (e) => loadDoctors(e.target.value));
document.getElementById("schedule-doctor").addEventListener("change", loadSchedule);
scheduleDateInput.addEventListener("change", loadSchedule);

window.addEventListener("DOMContentLoaded", async () => {
    await loadPatients();
    await loadDoctors();
    await loadAuditLogs();
});