from datetime import datetime, date
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_

from src.models import Patient, Doctor, Appointment, AuditLog, AppointmentStatus
from src.schemas import PatientDTO, PatientUpdateDTO, DoctorDTO


class SlotAlreadyBookedError(Exception):
    pass


class EntityNotFoundError(Exception):
    pass


class AuditLogService:

    def __init__(self, db_session: Session):
        self.db_session = db_session

    def log_action(self, action: str, entity: str, entity_id: int, details: str) -> AuditLog:
        log_entry = AuditLog(
            action_type=action,
            entity_name=entity,
            entity_id=entity_id,
            timestamp=datetime.utcnow(),
            details=details
        )
        self.db_session.add(log_entry)
        self.db_session.commit()
        self.db_session.refresh(log_entry)
        return log_entry

    def get_logs(self, limit: int = 50) -> List[AuditLog]:
        return (
            self.db_session.query(AuditLog)
            .order_by(AuditLog.timestamp.desc(), AuditLog.id.desc())
            .limit(limit)
            .all()
        )


class PatientService:

    def __init__(self, db_session: Session, audit_service: Optional[AuditLogService] = None):
        self.db_session = db_session
        self.audit_service = audit_service or AuditLogService(db_session)

    def add_patient(self, data: PatientDTO) -> Patient:
        patient = Patient(
            full_name=data.full_name,
            phone_number=data.phone_number,
            birth_date=data.birth_date
        )
        self.db_session.add(patient)
        self.db_session.commit()
        self.db_session.refresh(patient)
        self.audit_service.log_action(
            "CREATE", "Patient", patient.id, f"Додано пацієнта: {patient.full_name}"
        )
        return patient

    def update_patient(self, pat_id: int, data: PatientUpdateDTO) -> Patient:
        patient = self.db_session.query(Patient).filter(Patient.id == pat_id).first()
        if not patient:
            raise EntityNotFoundError(f"Пацієнта з ID {pat_id} не знайдено")
        patient.update_info(data.full_name, data.phone_number)
        self.db_session.commit()
        self.db_session.refresh(patient)
        self.audit_service.log_action(
            "UPDATE", "Patient", patient.id, f"Оновлено дані пацієнта: {patient.full_name}"
        )
        return patient

    def delete_patient(self, pat_id: int) -> bool:
        patient = self.db_session.query(Patient).filter(Patient.id == pat_id).first()
        if not patient:
            raise EntityNotFoundError(f"Пацієнта з ID {pat_id} не знайдено")
        name = patient.full_name
        self.db_session.delete(patient)
        self.db_session.commit()
        self.audit_service.log_action(
            "DELETE", "Patient", pat_id, f"Видалено картку пацієнта: {name}"
        )
        return True

    def search_patients(self, query: Optional[str] = None) -> List[Patient]:
        q = self.db_session.query(Patient)
        if query:
            pattern = f"%{query.strip()}%"
            q = q.filter(
                or_(
                    Patient.full_name.ilike(pattern),
                    Patient.phone_number.ilike(pattern)
                )
            )
        return q.order_by(Patient.full_name.asc()).all()


class DoctorService:

    def __init__(self, db_session: Session, audit_service: Optional[AuditLogService] = None):
        self.db_session = db_session
        self.audit_service = audit_service or AuditLogService(db_session)

    def add_doctor(self, data: DoctorDTO) -> Doctor:
        doctor = Doctor(
            full_name=data.full_name,
            specialty=data.specialty,
            room_number=data.room_number,
            working_hours=data.working_hours
        )
        self.db_session.add(doctor)
        self.db_session.commit()
        self.db_session.refresh(doctor)
        self.audit_service.log_action(
            "CREATE", "Doctor", doctor.id, f"Додано лікаря: {doctor.full_name} ({doctor.specialty})"
        )
        return doctor

    def get_all_doctors(self, specialty: Optional[str] = None) -> List[Doctor]:
        q = self.db_session.query(Doctor)
        if specialty:
            q = q.filter(Doctor.specialty.ilike(f"%{specialty.strip()}%"))
        return q.order_by(Doctor.full_name.asc()).all()


class AppointmentService:

    STANDARD_SLOTS = [
        "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
        "12:00", "12:30", "13:00", "13:30", "14:00", "14:30",
        "15:00", "15:30", "16:00", "16:30"
    ]

    def __init__(self, db_session: Session, audit_service: Optional[AuditLogService] = None):
        self.db_session = db_session
        self.audit_service = audit_service or AuditLogService(db_session)

    def is_slot_available(
        self, doc_id: int, time: datetime, exclude_appointment_id: Optional[int] = None
    ) -> bool:
        q = self.db_session.query(Appointment).filter(
            Appointment.doctor_id == doc_id,
            Appointment.appointment_time == time,
            Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.RESCHEDULED])
        )
        if exclude_appointment_id is not None:
            q = q.filter(Appointment.id != exclude_appointment_id)
        return q.count() == 0

    def create_appointment(
        self,
        doc_id: int,
        pat_id: int,
        time: datetime,
        duration_minutes: int = 30,
        notes: str = ""
    ) -> Appointment:
        doctor = self.db_session.query(Doctor).filter(Doctor.id == doc_id).first()
        if not doctor:
            raise EntityNotFoundError(f"Лікаря з ID {doc_id} не знайдено")

        patient = self.db_session.query(Patient).filter(Patient.id == pat_id).first()
        if not patient:
            raise EntityNotFoundError(f"Пацієнта з ID {pat_id} не знайдено")

        if not self.is_slot_available(doc_id, time):
            raise SlotAlreadyBookedError("Цей час вже зайнятий іншим пацієнтом")

        appointment = Appointment(
            doctor_id=doc_id,
            patient_id=pat_id,
            appointment_time=time,
            duration_minutes=duration_minutes,
            status=AppointmentStatus.SCHEDULED,
            notes=notes
        )
        self.db_session.add(appointment)
        self.db_session.commit()
        self.db_session.refresh(appointment)

        self.audit_service.log_action(
            "CREATE",
            "Appointment",
            appointment.id,
            f"Створено запис пацієнта ID={pat_id} до лікаря ID={doc_id} на {time.isoformat()}"
        )
        return appointment

    def reschedule_appointment(self, app_id: int, new_time: datetime) -> Appointment:
        appointment = self.db_session.query(Appointment).filter(Appointment.id == app_id).first()
        if not appointment:
            raise EntityNotFoundError(f"Запис з ID {app_id} не знайдено")

        if not self.is_slot_available(
            appointment.doctor_id, new_time, exclude_appointment_id=app_id
        ):
            raise SlotAlreadyBookedError("Цей час вже зайнятий іншим пацієнтом")

        old_time = appointment.appointment_time
        appointment.reschedule(new_time)
        self.db_session.commit()
        self.db_session.refresh(appointment)

        self.audit_service.log_action(
            "RESCHEDULE",
            "Appointment",
            appointment.id,
            f"Перенесено запис з {old_time.isoformat()} на {new_time.isoformat()}"
        )
        return appointment

    def cancel_appointment(self, app_id: int) -> bool:
        appointment = self.db_session.query(Appointment).filter(Appointment.id == app_id).first()
        if not appointment:
            raise EntityNotFoundError(f"Запис з ID {app_id} не знайдено")

        appointment.cancel()
        self.db_session.commit()

        self.audit_service.log_action(
            "CANCEL",
            "Appointment",
            appointment.id,
            f"Скасовано запис ID={appointment.id}"
        )
        return True

    def get_doctor_schedule(self, doctor_id: int, target_date: date) -> Dict[str, Any]:
        doctor = self.db_session.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doctor:
            raise EntityNotFoundError(f"Лікаря з ID {doctor_id} не знайдено")

        day_start = datetime.combine(target_date, datetime.min.time())
        day_end = datetime.combine(target_date, datetime.max.time())

        appointments = (
            self.db_session.query(Appointment)
            .filter(
                Appointment.doctor_id == doctor_id,
                Appointment.appointment_time >= day_start,
                Appointment.appointment_time <= day_end,
                Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.RESCHEDULED])
            )
            .all()
        )

        booked_map = {
            app.appointment_time.strftime("%H:%M"): app for app in appointments
        }

        slots = []
        for slot_str in self.STANDARD_SLOTS:
            if slot_str in booked_map:
                app = booked_map[slot_str]
                slots.append({
                    "time": slot_str,
                    "is_available": False,
                    "appointment_id": app.id,
                    "patient_id": app.patient_id,
                    "patient_name": app.patient.full_name if app.patient else "",
                    "status": app.status.value
                })
            else:
                slots.append({
                    "time": slot_str,
                    "is_available": True,
                    "appointment_id": None,
                    "patient_id": None,
                    "patient_name": None,
                    "status": "FREE"
                })

        return {
            "doctor_id": doctor.id,
            "doctor_name": doctor.full_name,
            "specialty": doctor.specialty,
            "date": target_date.isoformat(),
            "slots": slots
        }