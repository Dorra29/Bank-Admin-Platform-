# Active Directory Account Management Portal

A Django-based internal user management platform that integrates with **Microsoft Active Directory through LDAP** to authenticate users and provide role-based access to different parts of the application.

The platform is designed for organizations that need a centralized interface for managing users, assigning tasks, and handling employee workflows while using their existing Active Directory infrastructure for authentication.

## ✨ Features

* 🔐 Active Directory / LDAP authentication
* 👥 AD group-to-application role mapping
* 🛡️ Role-based access control (RBAC)
* 👨‍💼 Administrator dashboard
* 👔 Manager dashboard
* 👤 Employee dashboard
* 📋 User account management
* ✅ Task assignment and tracking
* 🏖️ Employee leave-request workflow
* 🔎 Role-based access restrictions
* 🗄️ Django ORM database management
* 🔗 Integration with an existing Active Directory environment

## 🏗️ Architecture

The application uses Django as the web application layer and Active Directory as the authentication and identity source.

```text
                         Active Directory
                                │
                                │ LDAP
                                ▼
                       Django Authentication
                           Backend
                                │
                         Extract AD Groups
                                │
                                ▼
                     ┌─────────────────────┐
                     │  Role Mapping Layer │
                     └─────────────────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
              ▼                 ▼                 ▼
          Admin Role       Manager Role      Employee Role
              │                 │                 │
              ▼                 ▼                 ▼
       Admin Dashboard   Manager Dashboard  Employee Dashboard
```

## 🔐 Active Directory Integration

Authentication is handled through a custom Django authentication backend using the `ldap3` library.

The authentication flow is:

1. User submits their Active Directory credentials.
2. Django connects to the configured LDAP server.
3. The application searches Active Directory for the user's account.
4. The user's Active Directory group memberships are retrieved.
5. The application maps the user's AD groups to application roles.
6. The user's credentials are verified against Active Directory.
7. The user is redirected to the dashboard corresponding to their role.

This allows the application to use an organization's existing identity infrastructure instead of maintaining a completely separate password database.

## 👥 Active Directory → Application Role Mapping

The application maps Active Directory security groups to application-level roles.

| Active Directory Group | Application Role      | Access                                       |
| ---------------------- | --------------------- | -------------------------------------------- |
| `GG_Admins`            | Administrator         | User management and administrative functions |
| `GG_SupportAdmins`     | Support Administrator | Support and account-management functions     |
| `GG_Managers`          | Manager               | Team management, tasks and leave requests    |
| `GG_Employees`         | Employee              | Employee dashboard and assigned tasks        |

This approach allows administrators to manage access through existing Active Directory group membership.

## 👨‍💼 Administrator Dashboard

Administrators can access administrative functionality for managing users and organizational accounts.

Typical functionality includes:

* Viewing users
* Managing accounts
* Managing roles
* Accessing administrative tools

**Screenshot:**

*Add administrator dashboard screenshot here.*

## 👔 Manager Dashboard

Managers have access to team-oriented functionality.

Features include:

* Task assignment
* Task status management
* Employee-related workflows
* Leave-request management
* Filtering requests by status

**Screenshot:**

*Add manager dashboard screenshot here.*

## 👤 Employee Dashboard

Employees have access to functionality relevant to their own work.

Features include:

* Viewing assigned tasks
* Tracking task status
* Submitting leave requests
* Viewing relevant account information

**Screenshot:**

*Add employee dashboard screenshot here.*

## 📋 Task & Leave Management

The application includes internal workflow functionality for managing employee tasks and leave requests.

Managers can assign tasks and review employee requests, while employees can access their assigned tasks and submit leave requests.

The application uses Django models and relationships to maintain the workflow state.

## 🛠️ Tech Stack

| Technology | Usage                               |
| ---------- | ----------------------------------- |
| Python     | Backend development                 |
| Django     | Web framework                       |
| ldap3      | Active Directory / LDAP integration |
| SQLite     | Development database                |
| Django ORM | Database access                     |
| HTML/CSS   | Frontend                            |
| JavaScript | Client-side functionality           |

## 📁 Django Application Structure

The project is organized into multiple Django applications according to their responsibilities.

```text
accounts/
    Authentication and LDAP integration

core/
    Shared functionality and access-control logic

dashboard/
    General dashboard functionality

admin_panel/
    Administrator functionality

manager_panel/
    Manager functionality

employee_panel/
    Employee functionality
```

This separation keeps authentication, shared logic, and role-specific functionality organized independently.

## 🚀 Installation

### Requirements

* Python 3.x
* Django
* An accessible Active Directory / LDAP server
* LDAP credentials for the configured environment

### 1. Clone the repository

```bash
git clone https://github.com/Dorra29/ad-account-management-portal.git

cd ad-account-management-portal
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file containing the environment-specific configuration.

Example:

```env
SECRET_KEY=your-secret-key
DEBUG=False

LDAP_SERVER=ldap://your-domain-controller
LDAP_BIND_USER=your-service-account
LDAP_BIND_PASSWORD=your-password
LDAP_BASE_DN=DC=example,DC=local
```

**Do not commit real credentials or secrets to the repository.**

### 5. Apply database migrations

```bash
python manage.py migrate
```

### 6. Start the development server

```bash
python manage.py runserver
```

The application will be available at:

```text
http://127.0.0.1:8000
```

## ⚠️ Active Directory Environment

This project requires access to a compatible Active Directory / LDAP environment for the authentication functionality to work.

The repository does **not** include an Active Directory server.

For demonstration purposes, the project can be tested against a dedicated lab environment containing:

* A Windows Server domain controller
* Configured Active Directory users
* Appropriate security groups
* LDAP connectivity between the Django application and the domain controller

## 🔒 Security Considerations

This project is intended as an educational and development project.

For production deployment, additional security measures should be implemented, including:

* Environment-based secret management
* Secure LDAP / LDAPS
* HTTPS
* Production-grade database configuration
* `DEBUG=False`
* Proper logging and monitoring
* Strong password and credential policies
* Network restrictions around the LDAP service
* Automated security and integration testing

No production credentials should ever be committed to source control.

## 🎯 Project Goals

This project was built to explore the integration of web applications with enterprise identity infrastructure.

The main technical objectives were:

* Integrating Django with Active Directory
* Implementing LDAP authentication
* Mapping AD groups to application roles
* Building role-based dashboards
* Implementing authorization controls
* Creating internal employee workflows
* Managing tasks and leave requests
* Structuring a multi-application Django project

## 🔮 Future Improvements

Potential improvements include:

* LDAPS support
* Automated testing for authentication and authorization
* More granular Django permissions
* Audit logging
* User provisioning and deprovisioning workflows
* Password/account-status synchronization
* Docker-based development environment
* Production deployment configuration
* REST API endpoints
* Improved dashboard analytics

