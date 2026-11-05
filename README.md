# CRM-система для управління записами до лікаря (Hospital CRM)

Внутрішня CRM-система (Customer Relationship Management) для медичного закладу, призначена для автоматизації ведення бази пацієнтів і лікарів, керування розкладом прийомів та усунення накладок у графіку (подвійного бронювання).

---

## 1. Архітектура та базова структура проекту (Етап Лабораторної №4)

Проект побудовано за **модульною монолітною архітектурою** мовою Python з використанням фреймворку FastAPI та ORM SQLAlchemy. Вихідний код розділено на ізольовані шари відповідно до принципів **SOLID**:

```text
hospital-crm/
├── docs/                   # Проектна документація
│   ├── lab1_requirements.pdf
│   └── lab2_architecture.pdf
├── src/                    # Вихідний код базової структури програми
│   ├── __init__.py
│   ├── database.py         # Підключення до СКБД та генератор сесій get_db()
│   ├── models.py           # ORM-сутності (Patient, Doctor, Appointment, AuditLog)
│   ├── schemas.py          # Pydantic DTO-схеми для валідації даних
│   ├── services.py         # Класи бізнес-логіки (PatientService, DoctorService, AppointmentService, AuditLogService)
│   └── main.py             # Точка входу FastAPI-додатка
├── tests/                  # Автоматизовані тести системи
│   └── __init__.py
├── .gitignore              # Виключення службових файлів із Git
└── README.md               # Документація проекту
```

### Дотримання принципів SOLID у коді
- **S (Single Responsibility Principle):** Кожен сервісний клас відповідає виключно за власну бізнес-сутність (`PatientService` — картки пацієнтів, `DoctorService` — облік лікарів, `AppointmentService` — перевірка слотів і запис, `AuditLogService` — журнал дій адміністратора).
- **O (Open/Closed Principle):** Розширення статусів запису через `AppointmentStatus` (Enum) та налаштування слотів розкладу не потребують модифікації існуючих методів перевірки.
- **L (Liskov Substitution Principle):** Схеми відповідей (`PatientResponse`, `DoctorResponse`) розширюють базові DTO-схеми (`PatientDTO`, `DoctorDTO`) зі збереженням контракту даних.
- **I (Interface Segregation Principle):** Окремі вузькоспеціалізовані DTO для створення (`PatientDTO`), оновлення (`PatientUpdateDTO`) та перенесення запису (`AppointmentRescheduleDTO`).
- **D (Dependency Inversion Principle):** Сервіси бізнес-логіки залежать від абстракції сесії БД (`Session`), яка передається через конструктор, а не від жорстко закодованого драйвера СКБД.

---

## 2. Ролі та розподіл обов'язків у проекті

Проект розробляється індивідуально за моделлю **Full-Stack розробника**:
- **Виконавець:** Білий Олександр Сергійович (студент групи ІМ-42).
- **Обов'язки за ролями:**
  - *Database / DevOps Engineer:* Налаштування підключення до PostgreSQL, проектування ORM-моделей та зв'язків «один-до-багатьох».
  - *Backend Developer:* Реалізація сервісного шару бізнес-логіки, перевірки вільних слотів (`is_slot_available`) та логування дій.
  - *Frontend Developer:* Розробка клієнтської панелі адміністратора та інтерактивного календаря.
  - *QA Engineer:* Написання модульних, компонентних і системних тестів.

---

## 3. Організація роботи з Git

Розробка ведеться з використанням підходу **Feature Branching**:
- `main` — стабільна гілка проекту.
- `feature/core-models` — розробка ORM-моделей (`models.py`), підключення до БД (`database.py`) та DTO-схем (`schemas.py`).
- `feature/services-layer` — реалізація бізнес-логіки (`services.py`) та базової ініціалізації додатка (`main.py`).

---

## 4. Інструкція зі встановлення та запуску (Базова структура)

1. Клонувати репозиторій:
   ```bash
   git clone https://github.com/SashaBilyi/hospitalCRM.git
   cd hospitalCRM
   ```
2. Створити та активувати віртуальне середовище:
   ```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # Linux / macOS:
   source venv/bin/activate
   ```
3. Встановити базові залежності:
   ```bash
   pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic
   ```
4. Запустити сервер:
   ```bash
   uvicorn src.main:app --reload
   ```
5. Перевірити стан сервера у браузері: `http://localhost:8000/health`