# E-Governance Document Management System

A web-based Document Management System developed using **Flask** and **MongoDB** for securely storing, managing, and accessing government-related documents. The system supports different user roles, document lifecycle management, audit logging, and expiry notifications.

---

## 📌 Project Overview

The E-Governance Document Management System digitizes the process of storing and managing official documents. Instead of maintaining physical records, users can securely upload, download, update, search, and manage documents through an intuitive web interface.

The project demonstrates the practical implementation of NoSQL database design using MongoDB and full-stack web development using Flask.

---

## 🚀 Features

- User Registration and Login
- Role-Based Authentication (User & Issuer)
- Secure Document Upload
- Document Download
- Document Search
- Document Update
- Document Deletion
- Audit Logging
- Document Approval Workflow
- Expiry Date Management
- Renewal Notification Support
- Dashboard for Users and Issuers
- MongoDB CRUD Operations
- Custom Document ID Generation
- Responsive Flask Web Interface

---

## 🛠 Tech Stack

### Frontend
- HTML5
- CSS3
- Bootstrap
- Jinja2 Templates

### Backend
- Python
- Flask
- Flask-Login
- Flask-PyMongo

### Database
- MongoDB

### Tools
- Visual Studio Code
- MongoDB Compass
- Git
- GitHub

---

## 📂 Project Structure

```
E-Governance-Document-Management-System/
│
├── app.py
├── requirements.txt
├── templates/
├── static/
│   ├── css/
│   ├── js/
│   └── images/
├── documents/
│   ├── routes.py
│   ├── forms.py
│   └── templates/
├── audit/
│   └── audit_logger_utils.py
├── uploads/
├── extensions.py
├── id_generator_utils.py
└── README.md
```

---

## 🗃 Database Collections

The project uses MongoDB with the following collections:

- Users
- Issuers
- Documents
- Audit Logs
- Access Control

Relationships between collections are maintained using MongoDB references where required.

---

## 📄 Main Functionalities

### User

- Register
- Login
- Upload documents
- View personal documents
- Download documents
- Search documents
- Receive expiry notifications

### Issuer

- Login
- Upload documents for users
- Approve documents
- Edit document details
- Manage expiry dates
- View all documents
- Monitor audit logs

---

## 🔐 Security Features

- Password Hashing
- Session-Based Authentication
- Role-Based Authorization
- Secure File Upload
- Audit Trail for Every Operation

---

## 📊 CRUD Operations

The system implements all MongoDB CRUD operations:

- Create Documents
- Read Documents
- Update Documents
- Delete Documents

---

## 📑 Audit Logging

Every important activity is recorded, including:

- Login
- Logout
- Upload
- Download
- View
- Edit
- Delete
- Expiry Notifications

This ensures accountability and traceability.

---

## 🔔 Expiry Notification

Documents with expiry dates are monitored.

The system can notify users when documents are approaching expiration, helping them renew documents before they expire.

---

## ⚙ Installation

### Clone the Repository

```bash
git clone https://github.com/your-username/E-Governance-Document-Management-System.git

cd E-Governance-Document-Management-System
```

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate Environment

Windows

```bash
venv\Scripts\activate
```

Linux / Mac

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure MongoDB

Start MongoDB locally.

Default Connection:

```
mongodb://localhost:27017/e_governance_dms
```

---

## ▶ Run the Project

```bash
python app.py
```

Open your browser:

```
http://127.0.0.1:5050
```

---

## 📸 Screenshots
<img width="1004" height="575" alt="image" src="https://github.com/user-attachments/assets/33a5e358-cc18-4004-a37c-01ffdedab508" />
<img width="1004" height="516" alt="image" src="https://github.com/user-attachments/assets/49296450-cefb-4a22-81d1-1232e877828b" />
<img width="1004" height="509" alt="image" src="https://github.com/user-attachments/assets/a3ad7dd4-945a-4ac1-8680-1334b6a6122e" />
<img width="1004" height="521" alt="image" src="https://github.com/user-attachments/assets/68ea44b3-7b2e-4084-9798-a7457e9b1d8c" />
<img width="1004" height="354" alt="image" src="https://github.com/user-attachments/assets/80eb80f8-8186-4f6b-bdbf-5f675c855f12" />
<img width="1004" height="427" alt="image" src="https://github.com/user-attachments/assets/f0d11876-4f62-492a-b7e7-51a7b7a35558" />
<img width="1004" height="505" alt="image" src="https://github.com/user-attachments/assets/00a1cd3e-094a-4df4-8c7a-283ddbf63f24" />
<img width="1004" height="316" alt="image" src="https://github.com/user-attachments/assets/ecf2ef9d-4b53-453f-b10a-fed809d3bad6" />
<img width="1004" height="412" alt="image" src="https://github.com/user-attachments/assets/065da821-09af-44d8-a087-daa48fd7396f" />
<img width="1004" height="604" alt="image" src="https://github.com/user-attachments/assets/4af28ca1-0de0-46ac-97e8-f384e14b08e5" />
<img width="1004" height="627" alt="image" src="https://github.com/user-attachments/assets/46e70e3c-e171-4c29-a6c9-11c29064cac3" />
<img width="1004" height="506" alt="image" src="https://github.com/user-attachments/assets/b48fd0de-8a7d-43a0-8f13-9f2260cad986" />
<img width="1004" height="633" alt="image" src="https://github.com/user-attachments/assets/7738d796-8824-4952-8223-31d65c97eb19" />
<img width="1004" height="522" alt="image" src="https://github.com/user-attachments/assets/961a3e47-2302-46bd-9041-5c5aa0e33a03" />
<img width="1004" height="496" alt="image" src="https://github.com/user-attachments/assets/9356efa3-bbc0-4c39-9317-d36587801fb2" />
<img width="1004" height="378" alt="image" src="https://github.com/user-attachments/assets/2daab3a9-d4e3-4250-80b6-2f80d0dc9843" />
<img width="1004" height="529" alt="image" src="https://github.com/user-attachments/assets/f35dce68-8cf9-45e3-a648-2e614ed57216" />
<img width="1004" height="488" alt="image" src="https://github.com/user-attachments/assets/63ef67fb-cc44-441b-bf11-3a7cea95ee61" />
<img width="1004" height="413" alt="image" src="https://github.com/user-attachments/assets/49fc4854-f3cf-418d-a0cb-a0a3d81acbce" />

---

## 🎯 Learning Outcomes

- Designed a document-oriented schema using MongoDB.
- Implemented relationships between MongoDB collections.
- Built a complete web application using Flask.
- Integrated MongoDB with Flask.
- Performed CRUD operations efficiently.
- Implemented secure authentication and authorization.
- Developed a responsive GUI for document management.
- Implemented audit logging and document tracking.
- Learned practical NoSQL database design.
- Applied database concepts to a real-world E-Governance application.

---

## 📄 License

This project was developed for educational purposes as part of the Database Systems Lab course.

---
