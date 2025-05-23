# Transaction Inquiry & Notification Service

This Django-based API provides endpoints for **transaction inquiries** and **asynchronous notification delivery**. It supports caching of transaction reports and enables detailed tracking of notification requests.

---

## Features

### Transaction Inquiry
- API to query transactions from MongoDB.
- Cached versions of transaction reports can be generated for performance optimization.

### Transaction Caching
- Use the following management command to **cache transaction reports**:
  
  ```bash
  python manage.py cache_transactions
  ```

- Cached reports are stored in MongoDB and can be queried similarly via the inquiry API.

### Notification System
- Supports asynchronous notification delivery via:
  - `email`
  - `sms`
  - `bot`
- Notifications are queued using **Celery** and stored in MongoDB.
- API supports querying notification requests, both by list and by specific `messageId`.

---

## Build and Run with Docker

This project includes Docker support. To build and start the entire application stack (Django app, MongoDB, Redis, Celery), follow these steps:

1. Make sure Docker and Docker Compose are installed on your system.
2. In the root of the project (where `docker-compose.yml` is located), run:

```bash
docker-compose up --build
```

## Logs

- All logs are saved to the file:

  ```
  logs.log
  ```

- This includes:
  - Execution results of the `cache_transactions` command.
  - Asynchronous notification sending details.
  - Errors and internal server issues.

---

## Requirements

- Python 3.12+
- Django 4.x
- MongoDB
- Celery + Redis (for async task handling)

---