# Real-Time Environmental ETL Pipeline

### 📊 Project Overview

An automated ETL pipeline that fetches real-time weather and air quality metrics for global cities, transforms semi-structured JSON data into an analytical schema, and persists it to a SQL database.

### 🏗️ Architecture

The pipeline follows a modular functional design to ensure scalability and ease of debugging.

### 🛠️ Tech Stack

* **Language:** Python 3.10+
* **Data Handling:** Pandas, SQLAlchemy
* **Storage:** SQLite (Development) / PostgreSQL (Production)
* **Orchestration:** GitHub Actions (Hourly Cron)
* **API:** OpenWeatherMap API

### 🚀 Key Engineering Features

* **Idempotency:** Designed to handle repeated runs without data corruption.
* **Secrets Management:** Utilizes GitHub Secrets and `.env` for API security.
* **Error Resilience:** Implements `try-except` blocks and HTTP status checks to handle API downtime.

---
