from datetime import date, datetime
import pytest

from src.models import Patient, Doctor, Appointment, AppointmentStatus
from src.schemas import PatientDTO, PatientUpdateDTO, DoctorDTO
from src.services import (
    PatientService,
    DoctorService,
    AppointmentService,
    SlotAlreadyBookedError,
    EntityNotFoundError,
)


def test_patient_model_update_info():
    patient = Patient(
        full_name="Іваненко Іван",
        phone_number="+380501112233",
        birth_date=date(1990, 5, 15)
    )
    patient.update_info("Іваненко Іван Петрович", "+380679998877")
    assert patient.full_name == "Іваненко Іван Петрович"
    assert patient.phone_number == "+380679998877"


def test_appointment_model_reschedule_and_cancel():
    initial_time = datetime(2026, 11, 20, 10, 0)
    new_time = datetime(2026, 11, 20, 14, 30)
    app_obj = Appointment(
        doctor_id=1,
        patient_id=1,
        appointment_time=initial_time,
        duration_minutes=30,
        status=AppointmentStatus.SCHEDULED
    )

    app_obj.reschedule(new_time)
    assert app_obj.appointment_time == new_time
    assert app_obj.status == AppointmentStatus.RESCHEDULED

    app_obj.cancel()
    assert app_obj.status == AppointmentStatus.CANCELLED


def test_patient_service_crud_and_search(db_session):
    service = PatientService(db_session)
    created = service.add_patient(
        PatientDTO(
            full_name="Коваленко Олена",
            phone_number="+380631234567",
            birth_date=date(1985, 8, 20)
        )
    )
    assert created.id is not None

    found_by_name = service.search_patients("Коваленко")
    assert len(found_by_name) == 1
    assert found_by_name[0].phone_number == "+380631234567"

    found_by_phone = service.search_patients("1234567")
    assert len(found_by_phone) == 1

    updated = service.update_patient(
        created.id,
        PatientUpdateDTO(full_name="Коваленко Олена Сергіївна", phone_number="+380630000000")
    )
    assert updated.full_name == "Коваленко Олена Сергіївна"

    assert service.delete_patient(created.id) is True
    assert len(service.search_patients("Коваленко")) == 0


def test_appointment_service_slot_availability_and_conflict(db_session):
    doc_service = DoctorService(db_session)
    pat_service = PatientService(db_session)
    app_service = AppointmentService(db_session)

    doc = doc_service.add_doctor(
        DoctorDTO(full_name="Д-р Мельник", specialty="Кардіолог", room_number="101")
    )
    pat1 = pat_service.add_patient(
        PatientDTO(full_name="Пацієнт 1", phone_number="+380501111111", birth_date=date(1992, 1, 1))
    )
    pat2 = pat_service.add_patient(
        PatientDTO(full_name="Пацієнт 2", phone_number="+380502222222", birth_date=date(1995, 2, 2))
    )

    slot_time = datetime(2026, 11, 25, 11, 0)
    assert app_service.is_slot_available(doc.id, slot_time) is True

    app_service.create_appointment(doc.id, pat1.id, slot_time)
    assert app_service.is_slot_available(doc.id, slot_time) is False

    with pytest.raises(SlotAlreadyBookedError):
        app_service.create_appointment(doc.id, pat2.id, slot_time)


def test_service_raises_entity_not_found(db_session):
    pat_service = PatientService(db_session)
    with pytest.raises(EntityNotFoundError):
        pat_service.delete_patient(9999)