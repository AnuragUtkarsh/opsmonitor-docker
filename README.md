# OpsMonitor — Infrastructure Dashboard

A containerized infrastructure inventory dashboard built as a hands-on DevOps portfolio project.

## Features

- Server inventory backed by MySQL
- Create, update and delete server records
- Track server status and environment
- Search and filter the inventory
- Dashboard summary metrics
- Audit history for inventory changes
- Nginx reverse proxy
- Flask REST API served by Gunicorn
- Docker Compose health checks and persistent database storage

## Architecture

```text
Browser
   |
   v
Nginx :8080
   |
   v
Flask + Gunicorn API
   |
   v
MySQL 8.0
   |
   v
Persistent Docker Volume
```

## Technology Stack

- RHEL 9.7 lab environment
- Docker Engine and Docker Compose
- Python, Flask and Gunicorn
- MySQL 8.0
- Nginx
- HTML, CSS and JavaScript
- REST APIs

## Project Structure

```text
opsmonitor-docker/
├── app/
│   ├── app.py
│   └── requirements.txt
├── mysql/
│   └── init.sql
├── nginx/
│   └── default.conf
├── .dockerignore
├── .env.example
├── .gitignore
├── Dockerfile
├── compose.yaml
└── README.md
```

## Run Locally

### Prerequisites

- Docker Engine
- Docker Compose plugin

### 1. Configure environment

Create a local `.env` file using `.env.example` as a reference.

```bash
cp .env.example .env
chmod 600 .env
```

Set strong, unique passwords in `.env`. Never commit this file.

### 2. Build and start

```bash
docker compose up -d --build
docker compose ps
```

### 3. Open the dashboard

Visit `http://localhost:8080`.

### 4. Test the API

```bash
curl http://localhost:8080/health
curl http://localhost:8080/api/status
curl http://localhost:8080/api/summary
curl http://localhost:8080/api/servers
curl http://localhost:8080/api/audit
```

## Learning Outcomes

- Containerizing a Python web application
- Multi-container orchestration with Docker Compose
- Service discovery and container networking
- Health checks and persistent volumes
- REST API CRUD operations
- SQL-backed audit logging
- Reverse proxy configuration
- Environment-based configuration

## Security Notes

This is a learning project, not a production-ready management platform. Authentication, authorization and CSRF protection should be implemented before use in a shared or production environment. Do not expose the dashboard publicly without suitable security controls.

## Future Improvements

- Authentication and role-based access
- Automated tests and CI/CD pipeline
- Container image vulnerability scanning
- HTTPS and production deployment hardening
- Real host-health monitoring

## Author

Built as a hands-on DevOps learning and portfolio project.
