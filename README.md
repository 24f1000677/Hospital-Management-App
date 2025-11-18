# Hospital Management App - Starter

This is a starter Flask application built for the course constraints:
- Flask backend
- Jinja2 templates + HTML/CSS + Bootstrap (CDN) for frontend
- SQLite (programmatic creation via SQLAlchemy `db.create_all()`)
- Manual server-side validation
- JSON API endpoints (flask routes returning JSON)

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .\.venv\Scripts\activate
pip install -r requirements.txt
python run.py
# open http://127.0.0.1:5000/
```

Default seeded admin account:
- username: admin
- email: admin@example.com
- password: adminpass

# Hospital Management System – Flask Project

A role-based Hospital Management System built using Flask, SQLite, SQLAlchemy, Jinja2, and Bootstrap.  
Implements Admin, Doctor, and Patient workflows as per the official MAD-1 project guidelines.

---

## 📌 Table of Contents
- [Project Overview](#project-overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [API Resources](#api-resources)
- [Installation & Setup](#installation--setup)
- [Demo Video](#demo-video)

---

# Project Overview

This Hospital Management System is a full-stack Flask application that manages hospital workflows for three distinct roles:

- **Admin** – manages doctors, departments, and users  
- **Doctor** – manages availability, appointments, and patient treatment history  
- **Patient** – books/reschedules appointments and views medical history  

The system strictly follows project requirements, wireframes, and validation rules using only permitted technologies.

---

# Features

## 👨‍⚕️ Admin
- Add/Edit/Delete Doctors  
- View all registered patients  
- Add departments  
- Search doctors/patients/departments  
- View appointments  

## 🩺 Doctor
- Manage availability slots  
- View assigned appointments  
- Complete appointments by entering:
  - Visit type  
  - Tests done  
  - Diagnosis  
  - Prescription  
  - Medicines & dosage  
  - Notes  
- View patient medical history  

## 🧑‍💼 Patient
- Register & login  
- Book appointments based on doctor availability  
- Reschedule (only to available slots)  
- Cancel appointments  
- View full treatment history  

## ⭐ Others
- Fully role-based routing  
- Strong input validation (frontend + backend)  
- Templates match provided wireframes  

---

# Tech Stack

### Backend
- Python 3  
- Flask  
- Flask-Login  
- Flask SQLAlchemy  
- SQLite  
- Jinja2  

### Frontend
- HTML5  
- CSS3  
- Bootstrap 5  

### Other
- OpenAPI 3.0 (YAML API specification)  

---

# Project Structure

---

# Database Schema

## **User**
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| username | String | Login name |
| email | String | Unique email |
| password_hash | String | Encrypted password |
| role | String | admin / doctor / patient |

## **Doctor**
| Column | Type |
|--------|------|
| id | PK |
| user_id | FK → user.id |
| department_id | FK |
| specialization | String |
| experience_years | Integer |

## **Patient**
| Column | Type |
|--------|------|
| id | PK |
| user_id | FK |

## **Department**
| Column | Type |
|--------|------|
| id | PK |
| name | String |
| description | String |

## **Availability**
| Column | Type |
|--------|------|
| id | PK |
| doctor_id | FK |
| date | Date |
| start_time | Time |
| end_time | Time |
| is_booked | Boolean |

## **Appointment**
| Column | Type |
|--------|------|
| id | PK |
| patient_id | FK |
| doctor_id | FK |
| department_id | FK |
| date | Date |
| start_time | Time |
| end_time | Time |
| status | String |

## **PatientHistory**
| Column | Type |
|--------|------|
| id | PK |
| patient_id | FK |
| doctor_id | FK |
| visit_date | DateTime |
| visit_type | String |
| diagnosis | Text |
| prescription | Text |
| tests_done | Text |
| medicines | Text |
| notes | Text |

## API Resources

Full API documentation is provided in:


This follows the **OpenAPI 3.0** specification and includes definitions for:

- Authentication  
- Doctor management  
- Availability  
- Appointments  
- Patient history  
- Booking and rescheduling  

---

## Installation & Setup
```bash

### 1. Clone the repository
bash
git clone https://github.com/24f1000677/Hospital-Management-App.git
cd Hospital-Management-App

### 2. Create a virtual environment
bash
python3 -m venv .venv
source .venv/bin/activate

### 3. Install dependencies
pip install -r requirements.txt

### 4. Run the application
python run.py

```
## Your app will be available at:

http://127.0.0.1:5000


## Demo Video

# Drive Link:

https://drive.google.com/file/d/1Lo52cd5Af4uxx-72dyhJjQBgrgD3FHq9/view?usp=sharing

## Author

**Name:** Yuvalakshmi M  
**Roll Number:** 24f1000677  
**Email:** 24f1000677@ds.study.iitm.ac.in  

I am a student enrolled in the IITM BS Degree Program.  
This project was developed as part of the MAD-1 (Application Development) course.
