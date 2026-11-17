import time


def test_end_to_end_admin_workflow(client):
    doc = client.post("/api/doctors", json={
        "full_name": "Савченко Наталія",
        "specialty": "Офтальмолог",
        "room_number": "112"
    }).json()

    pat = client.post("/api/patients", json={
        "full_name": "Гнатюк Дмитро",
        "phone_number": "+380667778899",
        "birth_date": "2001-07-10"
    }).json()

    sched_before = client.get(f"/api/doctors/{doc['id']}/schedule?date=2026-12-05").json()
    slot_10_00 = next(s for s in sched_before["slots"] if s["time"] == "10:00")
    assert slot_10_00["is_available"] is True

    appointment = client.post("/api/appointments", json={
        "doctor_id": doc["id"],
        "patient_id": pat["id"],
        "appointment_time": "2026-12-05T10:00:00"
    }).json()

    rescheduled = client.put(
        f"/api/appointments/{appointment['id']}/reschedule",
        json={"new_time": "2026-12-05T11:30:00"}
    )
    assert rescheduled.status_code == 200
    assert rescheduled.json()["status"] == "RESCHEDULED"

    cancelled = client.delete(f"/api/appointments/{appointment['id']}")
    assert cancelled.status_code == 200

    logs_res = client.get("/api/audit-logs")
    assert logs_res.status_code == 200
    actions = [log["action_type"] for log in logs_res.json()]
    assert "CREATE" in actions
    assert "RESCHEDULE" in actions
    assert "CANCEL" in actions


def test_nfr_performance_validation(client):
    t_ui_start = time.perf_counter()
    ui_response = client.get("/")
    ui_load_time = time.perf_counter() - t_ui_start
    assert ui_response.status_code == 200
    assert ui_load_time < 2.0

    for i in range(25):
        client.post("/api/patients", json={
            "full_name": f"Тестовий Пацієнт {i}",
            "phone_number": f"+3805000000{i:02d}",
            "birth_date": "1995-05-15"
        })

    t_search_start = time.perf_counter()
    search_res = client.get("/api/patients?query=Пацієнт 15")
    search_duration = time.perf_counter() - t_search_start
    assert search_res.status_code == 200
    assert len(search_res.json()) == 1
    assert search_duration < 3.0