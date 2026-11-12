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
        li.innerHTML = `
            <span><strong>${p.full_name}</strong> (${p.phone_number}, ${p.birth_date})</span>
            <button onclick="deletePatient(${p.id})" style="background:#dc2626;padding:4px 8px;">Видалити</button>
        `;
        list.appendChild(li);

        const opt = document.createElement("option");
        opt.value = p.id;
        opt.textContent = `${p.full_name} (${p.phone_number})`;
        select.appendChild(opt);
    });
}

async function deletePatient(id) {
    await fetch(`/api/patients/${id}`, { method: "DELETE" });
    await loadPatients();
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

    if (doctors.length > 0) {
        await loadSchedule();
    }
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
                <button onclick="cancelAppointment(${slot.appointment_id})" style="background:#dc2626;">Скасувати</button>
            `;
        }
        container.appendChild(card);
    });
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