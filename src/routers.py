from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.schemas import (
    PatientDTO,
    PatientUpdateDTO,
    PatientResponse,
    DoctorDTO,
    DoctorResponse,
    AppointmentCreateDTO,
    AppointmentRescheduleDTO,
    AppointmentResponse,
    AuditLogResponse,
)
from src.services import (
    PatientService,
    DoctorService,
    AppointmentService,
    AuditLogService,
    SlotAlreadyBookedError,
    EntityNotFoundError,
)

api_router = APIRouter(prefix="/api")


@api_router.post("/patients", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
def create_patient(data: PatientDTO, db: Session = Depends(get_db)):
    service = PatientService(db)
    return service.add_patient(data)


@api_router.get("/patients", response_model=List[PatientResponse])
def list_or_search_patients(
    query: Optional[str] = Query(default=None, description="Пошук за ПІБ або телефоном"),
    db: Session = Depends(get_db)
):
    service = PatientService(db)
    return service.search_patients(query)


@api_router.put("/patients/{pat_id}", response_model=PatientResponse)
def update_patient(pat_id: int, data: PatientUpdateDTO, db: Session = Depends(get_db)):
    service = PatientService(db)
    try:
        return service.update_patient(pat_id, data)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@api_router.delete("/patients/{pat_id}")
def delete_patient(pat_id: int, db: Session = Depends(get_db)):
    service = PatientService(db)
    try:
        service.delete_patient(pat_id)
        return {"status": "deleted", "patient_id": pat_id}
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@api_router.post("/doctors", response_model=DoctorResponse, status_code=status.HTTP_201_CREATED)
def create_doctor(data: DoctorDTO, db: Session = Depends(get_db)):
    service = DoctorService(db)
    return service.add_doctor(data)


@api_router.get("/doctors", response_model=List[DoctorResponse])
def list_doctors(
    specialty: Optional[str] = Query(default=None, description="Фільтр за спеціальністю"),
    db: Session = Depends(get_db)
):
    service = DoctorService(db)
    return service.get_all_doctors(specialty)


@api_router.get("/doctors/{doctor_id}/schedule")
def get_doctor_schedule(
    doctor_id: int,
    date: date = Query(..., description="Дата розкладу у форматі YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    service = AppointmentService(db)
    try:
        return service.get_doctor_schedule(doctor_id, date)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@api_router.post(
    "/appointments",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED
)
def create_appointment(dto: AppointmentCreateDTO, db: Session = Depends(get_db)):
    service = AppointmentService(db)
    try:
        return service.create_appointment(
            doc_id=dto.doctor_id,
            pat_id=dto.patient_id,
            time=dto.appointment_time,
            duration_minutes=dto.duration_minutes,
            notes=dto.notes or ""
        )
    except SlotAlreadyBookedError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@api_router.put("/appointments/{app_id}/reschedule", response_model=AppointmentResponse)
def reschedule_appointment(
    app_id: int, dto: AppointmentRescheduleDTO, db: Session = Depends(get_db)
):
    service = AppointmentService(db)
    try:
        return service.reschedule_appointment(app_id, dto.new_time)
    except SlotAlreadyBookedError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@api_router.delete("/appointments/{app_id}")
def cancel_appointment(app_id: int, db: Session = Depends(get_db)):
    service = AppointmentService(db)
    try:
        service.cancel_appointment(app_id)
        return {"status": "cancelled", "appointment_id": app_id}
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@api_router.get("/audit-logs", response_model=List[AuditLogResponse])
def get_audit_logs(db: Session = Depends(get_db)):
    service = AuditLogService(db)
    return service.get_logs()