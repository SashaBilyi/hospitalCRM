from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from src.models import AppointmentStatus


class PatientDTO(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=150)
    phone_number: str = Field(..., min_length=5, max_length=30)
    birth_date: date


class PatientUpdateDTO(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=150)
    phone_number: str = Field(..., min_length=5, max_length=30)


class PatientResponse(PatientDTO):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DoctorDTO(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=150)
    specialty: str = Field(..., min_length=2, max_length=100)
    room_number: str = Field(..., min_length=1, max_length=20)
    working_hours: str = Field(default="09:00-17:00", max_length=50)


class DoctorResponse(DoctorDTO):
    id: int
    model_config = ConfigDict(from_attributes=True)


class AppointmentCreateDTO(BaseModel):
    doctor_id: int
    patient_id: int
    appointment_time: datetime
    duration_minutes: int = Field(default=30, ge=15, le=120)
    notes: Optional[str] = ""


class AppointmentRescheduleDTO(BaseModel):
    new_time: datetime


class AppointmentResponse(BaseModel):
    id: int
    doctor_id: int
    patient_id: int
    appointment_time: datetime
    duration_minutes: int
    status: AppointmentStatus
    notes: Optional[str] = ""
    model_config = ConfigDict(from_attributes=True)


class AuditLogResponse(BaseModel):
    id: int
    action_type: str
    entity_name: str
    entity_id: int
    timestamp: datetime
    details: str
    model_config = ConfigDict(from_attributes=True)