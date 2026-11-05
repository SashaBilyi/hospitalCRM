import enum
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from src.database import Base


class AppointmentStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    RESCHEDULED = "RESCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(150), nullable=False, index=True)
    phone_number = Column(String(30), nullable=False, index=True)
    birth_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    appointments = relationship(
        "Appointment", back_populates="patient", cascade="all, delete-orphan"
    )

    def update_info(self, full_name: str, phone: str) -> None:
        self.full_name = full_name
        self.phone_number = phone


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(150), nullable=False, index=True)
    specialty = Column(String(100), nullable=False, index=True)
    room_number = Column(String(20), nullable=False)
    working_hours = Column(String(50), nullable=False, default="09:00-17:00")

    appointments = relationship(
        "Appointment", back_populates="doctor", cascade="all, delete-orphan"
    )

    def get_schedule(self, target_date: date):
        return [
            app for app in self.appointments
            if app.appointment_time.date() == target_date
            and app.status != AppointmentStatus.CANCELLED
        ]


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    appointment_time = Column(DateTime, nullable=False, index=True)
    duration_minutes = Column(Integer, nullable=False, default=30)
    status = Column(
        Enum(AppointmentStatus),
        default=AppointmentStatus.SCHEDULED,
        nullable=False
    )
    notes = Column(String(500), nullable=True, default="")

    doctor = relationship("Doctor", back_populates="appointments")
    patient = relationship("Patient", back_populates="appointments")

    def reschedule(self, new_time: datetime) -> None:
        self.appointment_time = new_time
        self.status = AppointmentStatus.RESCHEDULED

    def cancel(self) -> None:
        self.status = AppointmentStatus.CANCELLED


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    action_type = Column(String(50), nullable=False)
    entity_name = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    details = Column(String(500), nullable=False)