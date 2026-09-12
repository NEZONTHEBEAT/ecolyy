# Ecolyy — Smart E-Waste Recycling Platform

Ecolyy is a full-stack e-waste recycling platform designed to connect **users, collection partners, and institutions** through a centralized digital ecosystem for responsible and sustainable e-waste management.

The platform enables users to schedule waste pickups, manage their recycling activities, earn rewards, and track their requests, while partners and institutions can manage collections, documents, locations, and related operations through dedicated dashboards.

## Key Features

### User Platform

* User registration and authentication
* Google Sign-In
* Secure JWT-based authentication
* Profile management
* Address management
* E-waste pickup scheduling
* Pickup tracking and history
* Rewards and wallet management
* Recycling activity management

### Collection Partner

* Partner authentication
* Dedicated partner dashboard
* Pickup management
* Pickup details and tracking
* Document management
* Earnings management
* Partner profile management

### Institution Management

* Institution authentication
* Institution dashboard
* Pickup scheduling and management
* Institution locations
* Certificates and reports
* Profile management

### Admin Dashboard

* Admin authentication
* User management
* Partner management
* Institution management
* Pickup management
* Waste category management
* Rewards management
* Document management
* Dispute management
* Analytics and system settings

## Authentication and Security

* JWT authentication
* Role-Based Access Control (RBAC)
* Google Sign-In
* OTP-based verification
* Protected API endpoints
* Secure password hashing
* Backend-controlled user roles and permissions
* CORS configuration for production frontend

## System Architecture

```text
┌───────────────────────────┐
│        Ecolyy Frontend    │
│     HTML / CSS / JS       │
│       Bootstrap / UI      │
└─────────────┬─────────────┘
              │ REST API
              ▼
┌───────────────────────────┐
│       Ecolyy Backend      │
│          FastAPI          │
│      JWT + RBAC + OTP     │
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│       MongoDB Atlas       │
│          Database         │
└───────────────────────────┘
```

## Tech Stack

### Frontend

* HTML5
* CSS3
* JavaScript
* Bootstrap
* Font Awesome
* GSAP

### Backend

* Python
* FastAPI
* Uvicorn
* Pydantic
* Motor
* PyMongo
* JWT
* Passlib
* Google Authentication

### Database

* MongoDB
* MongoDB Atlas

### Authentication

* JWT
* Google Sign-In
* OTP Verification
* Role-Based Access Control

### Deployment

* Netlify — Frontend
* Render — Backend
* MongoDB Atlas — Database

## Project Structure

```text
ecolyy/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   │
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── admin/
│   ├── institution/
│   ├── partner/
│   ├── user/
│   ├── pages/
│   ├── js/
│   ├── assets/
│   └── index.html
│
├── .gitignore
└── README.md
```

## Live Application

Frontend:

https://ecolyy.netlify.app/

Backend API:

https://ecolyy.onrender.com/

API Documentation:

https://ecolyy.onrender.com/docs

## Local Development

### 1. Clone the Repository

```bash
git clone https://github.com/NEZONTHEBEAT/ecolyy.git
cd ecolyy
```

### 2. Backend Setup

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment on Windows:

```bash
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create your environment file:

```text
.env
```

Configure the required environment variables:

```env
SECRET_KEY=your-secret-key
MONGO_URI=your-mongodb-connection-string
MONGO_DB_NAME=ecolyy
CORS_ORIGINS=http://localhost:5500
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

Start the FastAPI server:

```bash
uvicorn app.main:app --reload
```

Backend will run at:

```text
http://127.0.0.1:8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

### 3. Frontend

Open the `frontend` directory using a local development server.

For example:

```bash
cd frontend
python -m http.server 5500
```

Then open:

```text
http://localhost:5500
```

## User Roles

| Role        | Main Responsibilities                                         |
| ----------- | ------------------------------------------------------------- |
| User        | Schedule pickups, track recycling, manage profile and rewards |
| Partner     | Manage collections, pickups, documents and earnings           |
| Institution | Manage institutional recycling activities and reports         |
| Admin       | Manage users, partners, institutions and platform operations  |

## Core Modules

```text
Authentication
      │
      ├── Google Login
      ├── JWT
      ├── OTP
      └── RBAC
             │
             ▼
       Ecolyy Platform
             │
    ┌────────┼────────┐
    ▼        ▼        ▼
  Users   Partners Institutions
    │        │        │
    └────────┼────────┘
             ▼
       Pickup System
             │
             ▼
        Rewards / Wallet
             │
             ▼
       Admin Management
```

## Project Goals

Ecolyy aims to make e-waste recycling more **accessible, organized, transparent, and technology-driven** by bringing different participants of the recycling ecosystem onto a single platform.

The project focuses on:

* Responsible e-waste disposal
* Convenient pickup scheduling
* Digital recycling management
* Collection partner coordination
* Institutional recycling workflows
* User engagement through rewards
* Centralized administrative control

## Future Improvements

* Real-time pickup tracking
* Push notifications
* Advanced analytics
* AI-powered waste classification
* Automated recycling recommendations
* Payment and incentive integration
* Mobile application
* Automated certificate generation
* Expanded recycling partner network

## Developer

**Kalyan Baraik**

GitHub: `https://github.com/NEZONTHEBEAT`

Portfolio: `https://kalyanbaraikdeveloper.netlify.app/`

## License

This project is developed for educational, portfolio, and demonstration purposes.
