def test_patients_api_endpoints(client):
    create_res = client.post("/api/patients", json={
        "full_name": "Сидоренко Павло",
        "phone_number": "+380503334455",
        "birth_date": "1991-03-14"
    })
    assert create_res.status_code == 201
    pat_id = create_res.json()["id"]

    update_res = client.put(f"/api/patients/{pat_id}", json={
        "full_name": "Сидоренко Павло Ігорович",
        "phone_number": "+380509990011"
    })
    assert update_res.status_code == 200
    assert update_res.json()["full_name"] == "Сидоренко Павло Ігорович"

    del_res = client.delete(f"/api/patients/{pat_id}")
    assert del_res.status_code == 200


def test_doctors_api_filter_by_specialty(client):
    r1 = client.post("/api/doctors", json={
        "full_name": "Бондаренко Ігор",
        "specialty": "Хірург",
        "room_number": "302"
    })
    assert r1.status_code == 201

    r2 = client.post("/api/doctors", json={
        "full_name": "Шевченко Марія",
        "specialty": "Терапевт",
        "room_number": "105"
    })
    assert r2.status_code == 201

    res_all = client.get("/api/doctors")
    assert res_all.status_code == 200
    assert len(res_all.json()) == 2

    res_filtered = client.get("/api/doctors?specialty=Терапевт")
    assert res_filtered.status_code == 200
    data = res_filtered.json()
    assert len(data) == 1
    assert data[0]["full_name"] == "Шевченко Марія"


def test_appointment_conflict_returns_409(client):
    doc = client.post("/api/doctors", json={
        "full_name": "Кравчук Олег",
        "specialty": "Невролог",
        "room_number": "210"
    }).json()

    pat1 = client.post("/api/patients", json={
        "full_name": "Ткаченко Андрій",
        "phone_number": "+380971112233",
        "birth_date": "1988-04-12"
    }).json()

    pat2 = client.post("/api/patients", json={
        "full_name": "Мороз Ірина",
        "phone_number": "+380974445566",
        "birth_date": "1994-09-23"
    }).json()

    payload_1 = {
        "doctor_id": doc["id"],
        "patient_id": pat1["id"],
        "appointment_time": "2026-12-01T09:30:00"
    }
    res1 = client.post("/api/appointments", json=payload_1)
    assert res1.status_code == 201
    assert res1.json()["status"] == "SCHEDULED"

    payload_2 = {
        "doctor_id": doc["id"],
        "patient_id": pat2["id"],
        "appointment_time": "2026-12-01T09:30:00"
    }
    res2 = client.post("/api/appointments", json=payload_2)
    assert res2.status_code == 409
    assert "вже зайнятий" in res2.json()["detail"]


def test_nonexistent_entity_returns_404(client):
    res = client.get("/api/doctors/9999/schedule?date=2026-12-01")
    assert res.status_code == 404

    del_res = client.delete("/api/patients/9999")
    assert del_res.status_code == 404