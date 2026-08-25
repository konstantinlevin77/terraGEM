# 🌿 terraGEM Greenhouse IoT & Analytics API

Welcome to the **terraGEM Backend API** — a high-performance, multi-tenant IoT management and environmental intelligence platform for commercial greenhouse growers.

This backend provides real-time sensor ingestion, microclimate analytics, 24-hour time-series aggregations, and a 2-tier incident alerting system.

---

## 📑 Table of Contents
- [Architecture Highlights](#-architecture-highlights)
- [Quickstart & Local Setup](#-quickstart--local-setup)
- [Authentication & Security](#-authentication--security)
- [API Reference & JSON Contracts](#-api-reference--json-contracts)
  - [1. Authentication](#1-authentication)
  - [2. Greenhouse Fleet Management](#2-greenhouse-fleet-management)
  - [3. Dashboard & Analytics (Frontend Cards & Charts)](#3-dashboard--analytics-frontend-cards--charts)
  - [4. Sensor Profiles & Deployments (Catalog vs. Instance)](#4-sensor-profiles--deployments-catalog-vs-instance)
  - [5. IoT Hardware Measurement Ingest](#5-iot-hardware-measurement-ingest)
  - [6. Incident Thresholds & Alerting](#6-incident-thresholds--alerting)
- [Domain Enums & Standards](#-domain-enums--standards)
- [Running Unit Tests](#-running-unit-tests)
- [CORS Configuration](#-cors-configuration)

---

## 🏛 Architecture Highlights

1. **Strict Multi-Tenancy**: Every resource (`Greenhouse`, `Sensor`, `SensorThreshold`, `Alert`) is strictly scoped to the authenticated user. Growers can never access or leak each other's greenhouse data.
2. **Catalog vs. Instance Model**:
   * **`SensorProfile` (Catalog)**: Reusable hardware blueprint (`name`, `sensor_type`, `unit`, `period`).
   * **`Sensor` (Deployment)**: Physical sensor deployed in a specific greenhouse zone linked to its profile.
3. **Database-Agnostic Aggregations**:
   * 10-minute bucketed 24-hour timelines.
   * Single-query daily summary statistics.
   * Real-time metrics with sparkline data and 24h comparative deltas.

---

## 🚀 Quickstart & Local Setup

### Prerequisites
* Python 3.11+
* `pip` / `virtualenv`

### 1. Clone & Activate Virtual Environment
```bash
cd api
python3 -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Migrations & Create Superuser
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 4. Start Development Server
```bash
python manage.py runserver
```
The API is available at `http://127.0.0.1:8000/api/`.

---

## 🔐 Authentication & Security

All protected endpoints require a JWT token in the `Authorization` header:

```http
Authorization: Bearer <access_token>
```

### Token Lifecycle:
1. Obtain token pair via `POST /api/auth/token/`.
2. Access tokens are valid for **60 minutes**.
3. Refresh expired tokens via `POST /api/auth/token/refresh/`.

---

## 📡 API Reference & JSON Contracts

### 1. Authentication

#### Register a New User
```http
POST /api/auth/register/
Content-Type: application/json
```
```json
{
  "username": "mehmet_grower",
  "email": "grower@example.com",
  "password": "StrongPassword123!",
  "password_confirm": "StrongPassword123!",
  "first_name": "Mehmet",
  "last_name": "Tekman"
}
```
**Response (`201 Created`):**
```json
{
  "id": 1,
  "username": "mehmet_grower",
  "email": "grower@example.com",
  "first_name": "Mehmet",
  "last_name": "Tekman"
}
```

#### Obtain JWT Token Pair
```http
POST /api/auth/token/
Content-Type: application/json
```
```json
{
  "username": "mehmet_grower",
  "password": "StrongPassword123!"
}
```
**Response (`200 OK`):**
```json
{
  "refresh": "eyJhbGciOi...",
  "access": "eyJhbGciOi..."
}
```

#### Refresh Access Token
```http
POST /api/auth/token/refresh/
```
```json
{
  "refresh": "eyJhbGciOi..."
}
```
**Response (`200 OK`):**
```json
{
  "access": "eyJhbGciOi..."
}
```

#### Get Current User Profile
```http
GET /api/auth/me/
Authorization: Bearer <token>
```
**Response (`200 OK`):**
```json
{
  "id": 1,
  "username": "mehmet_grower",
  "email": "grower@example.com",
  "first_name": "Mehmet",
  "last_name": "Tekman",
  "company": "Terra Flora Ag",
  "phone_number": "+905551234567",
  "created_at": "2026-08-25T12:00:00Z",
  "updated_at": "2026-08-25T12:00:00Z"
}
```

---

### 2. Greenhouse Fleet Management

#### List User's Greenhouses
```http
GET /api/greenhouses/
Authorization: Bearer <token>
```
**Response (`200 OK`):**
```json
[
  {
    "id": 1,
    "name": "North Tomato Tunnel",
    "description": "Hydroponic beefsteak tomato section",
    "latitude": 38.4237,
    "longitude": 27.1428,
    "created_at": "2026-08-25T10:00:00Z",
    "updated_at": "2026-08-25T10:00:00Z"
  }
]
```

#### Create a Greenhouse
```http
POST /api/greenhouses/
Authorization: Bearer <token>
```
```json
{
  "name": "Pepper House",
  "description": "Bell pepper drip block",
  "latitude": 38.4250,
  "longitude": 27.1450
}
```

---

### 3. Dashboard & Analytics (Frontend Cards & Charts)

#### 🌟 A. Latest Metrics (Dashboard Cards Widget)
> **Use Case**: Powers the main dashboard cards with real-time value, status badge, 24-hour delta comparison, and a mini sparkline curve.

```http
GET /api/greenhouses/{id}/latest-metrics/
Authorization: Bearer <token>
```
**Response (`200 OK`):**
```json
{
  "greenhouse_id": 1,
  "greenhouse_name": "North Tomato Tunnel",
  "metrics": [
    {
      "sensor_type": "air_temperature",
      "sensor_type_display": "Air Temperature",
      "current_value": 25.5,
      "unit": "celsius",
      "status": "optimal",
      "status_display": "Optimal",
      "delta_24h": -0.1,
      "sparkline": [25.6, 25.4, 25.1, 24.8, 25.2, 25.5]
    },
    {
      "sensor_type": "air_humidity",
      "sensor_type_display": "Air Humidity",
      "current_value": 57.0,
      "unit": "percent",
      "status": "optimal",
      "status_display": "Optimal",
      "delta_24h": -0.5,
      "sparkline": [57.5, 57.8, 57.2, 57.0]
    },
    {
      "sensor_type": "soil_temperature",
      "sensor_type_display": "Soil Temperature",
      "current_value": 19.6,
      "unit": "celsius",
      "status": "optimal",
      "status_display": "Optimal",
      "delta_24h": -0.3,
      "sparkline": [19.9, 19.8, 19.7, 19.6]
    }
  ]
}
```

---

#### 🌟 B. 24-Hour Time Series (Analytics Line Chart)
> **Use Case**: Powers the 24-hour detailed line charts. Automatically groups readings into **10-minute intervals** with `avg`, `min`, `max`, and `reading_count`.

```http
GET /api/greenhouses/{id}/day_overview/
Authorization: Bearer <token>
```
**Response (`200 OK`):**
```json
{
  "greenhouse_id": 1,
  "greenhouse_name": "North Tomato Tunnel",
  "series": [
    {
      "sensor_type": "air_temperature",
      "timeline": [
        {
          "timestamp": "2026-08-24T15:00:00Z",
          "avg_value": 24.55,
          "min_value": 22.1,
          "max_value": 26.8,
          "reading_count": 4
        },
        {
          "timestamp": "2026-08-24T15:10:00Z",
          "avg_value": 24.8,
          "min_value": 22.4,
          "max_value": 27.0,
          "reading_count": 4
        }
      ]
    }
  ]
}
```

---

#### C. Today's Daily Summary
> **Use Case**: Daily min/max/average statistics since `00:00:00` today (calculated in a single database SQL query).

```http
GET /api/greenhouses/{id}/today-summary/
Authorization: Bearer <token>
```
**Response (`200 OK`):**
```json
{
  "greenhouse_id": 1,
  "date": "2026-08-25",
  "metrics": [
    {
      "sensor_type": "air_temperature",
      "unit": "celsius",
      "min_value": 18.2,
      "max_value": 29.4,
      "avg_value": 23.8,
      "reading_count": 96
    },
    {
      "sensor_type": "soil_humidity",
      "unit": "percent",
      "min_value": 45.0,
      "max_value": 82.0,
      "avg_value": 68.4,
      "reading_count": 48
    }
  ]
}
```

---

#### D. Per-Sensor Latest Snapshot
> **Use Case**: Returns every physical sensor deployed in the greenhouse along with its individual last reading.

```http
GET /api/greenhouses/{id}/latest/
Authorization: Bearer <token>
```
**Response (`200 OK`):**
```json
{
  "id": 1,
  "name": "North Tomato Tunnel",
  "description": "Hydroponic beefsteak tomato section",
  "longitude": 27.1428,
  "latitude": 38.4237,
  "sensors": [
    {
      "id": 10,
      "profile": 1,
      "profile_name": "DS18B20",
      "sensor_type": "air_temperature",
      "unit": "celsius",
      "is_active": true,
      "description": "Canopy probe, middle row",
      "latest_measurement": {
        "id": 501,
        "value": 25.4,
        "measurement_time": "2026-08-25T14:45:00Z"
      }
    }
  ]
}
```

---

### 4. Sensor Profiles & Deployments (Catalog vs. Instance)

#### List Supported Hardware Profiles (`SensorProfile`)
```http
GET /api/sensor-profiles/
Authorization: Bearer <token>
```
**Response (`200 OK`):**
```json
[
  {
    "id": 1,
    "name": "DS18B20",
    "sensor_type": "air_temperature",
    "sensor_type_display": "Air Temperature",
    "unit": "celsius",
    "unit_display": "Celsius (°C)",
    "period": 5.0,
    "description": "Dallas 1-Wire waterproof digital temperature sensor",
    "created_at": "2026-08-25T08:00:00Z",
    "updated_at": "2026-08-25T08:00:00Z"
  }
]
```

#### Deploy a Sensor in a Greenhouse (`Sensor`)
```http
POST /api/sensors/
Authorization: Bearer <token>
```
```json
{
  "greenhouse": 1,
  "profile": 1,
  "description": "Row 4, North End",
  "is_active": true
}
```

---

### 5. IoT Hardware Measurement Ingest

Microcontrollers (ESP32, Raspberry Pi, LoRaWAN gateways) send readings via single HTTP POST requests:

```http
POST /api/measurements/
Authorization: Bearer <token>
Content-Type: application/json
```
```json
{
  "sensor": 10,
  "value": 25.4,
  "measurement_time": "2026-08-25T14:45:00Z"
}
```
*(Note: `measurement_time` defaults to current server timestamp if omitted).*

> [!NOTE]
> For security and stability, bulk measurement dumping via `GET /api/measurements/` is intentionally disabled (`405 Method Not Allowed`). Use `/latest-metrics/`, `/day_overview/`, or `/today-summary/` for aggregated data.

---

### 6. Incident Thresholds & Alerting

#### 2-Tier Banded Limits (`SensorThreshold`)
Growers configure safe, warning, and critical operating bands for any sensor:
* **Safe / Optimal Zone**: Between `warning_min` and `warning_max`.
* **Warning Band**: Between warning and critical bounds.
* **Critical Band**: Outside `critical_min` or `critical_max`.

```http
POST /api/thresholds/
Authorization: Bearer <token>
```
```json
{
  "sensor": 10,
  "warning_min": 18.0,
  "warning_max": 30.0,
  "critical_min": 10.0,
  "critical_max": 38.0,
  "is_active": true
}
```

---

#### ⚠️ Active Alerts Widget (`Alert`)
> **Use Case**: Matches the dashboard's *"⚠️ Dikkat - N açık"* notification badge.

```http
GET /api/alerts/active/
Authorization: Bearer <token>
```
**Response (`200 OK`):**
```json
{
  "total_active": 1,
  "alerts": [
    {
      "id": 4,
      "sensor": 10,
      "sensor_type": "air_temperature",
      "sensor_type_display": "Air Temperature",
      "sensor_description": "Canopy probe, middle row",
      "greenhouse_id": 1,
      "greenhouse_name": "North Tomato Tunnel",
      "triggered_value": 41.2,
      "unit": "celsius",
      "severity": "critical",
      "severity_display": "Kritik",
      "status": "active",
      "status_display": "Açık",
      "message": "Temperature exceeded critical limit of 38.0°C",
      "created_at": "2026-08-25T14:20:00Z",
      "updated_at": "2026-08-25T14:20:00Z",
      "resolved_at": null
    }
  ]
}
```

#### Acknowledge an Alert
```http
POST /api/alerts/{id}/acknowledge/
Authorization: Bearer <token>
```
**Response (`200 OK`):**
```json
{
  "id": 4,
  "status": "acknowledged",
  "status_display": "Onaylandı"
}
```

---

## 🏷 Domain Enums & Standards

### `SensorTypeChoices`
| Key | Label |
|---|---|
| `air_temperature` | Air Temperature |
| `air_humidity` | Air Humidity |
| `soil_temperature` | Soil Temperature |
| `soil_humidity` | Soil Humidity |
| `co2` | Carbon Dioxide (CO₂) |
| `ph` | Acidity / pH |
| `light_intensity` | Light Intensity (PAR/Lux) |

### `SensorUnitChoices`
| Key | Symbol / Description |
|---|---|
| `celsius` | °C |
| `percent` | % |
| `ppm` | Parts Per Million (CO₂) |
| `ph` | pH Scale |

### `AlertStatus` & `SeverityLevel`
* **Status**: `active` (*Açık*), `acknowledged` (*Onaylandı*), `resolved` (*Çözüldü*)
* **Severity**: `warning` (*Uyarı*), `critical` (*Kritik*)

---

## 🧪 Running Unit Tests

The backend includes a 22-test suite covering multi-tenancy isolation, authentication, data aggregations, 10-minute bucketing, and threshold validations.

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test api
```

**Expected output:**
```text
Ran 22 tests in 3.8s

OK
```

---

## 🌐 CORS Configuration

Cross-Origin Resource Sharing is enabled for modern frontend development:

| Client Origin | Environment |
|---|---|
| `http://localhost:3000` | React / Next.js / Vite Dev Server |
| `http://127.0.0.1:3000` | Localhost Alternate |
| `http://localhost:5173` | Vite Default |
| `http://localhost:8080` | Vue / Webpack Dev Server |

To add production frontend origins, configure `CORS_ALLOWED_ORIGINS` in [`core/settings.py`](core/settings.py).

---

*Built with ❤️ for sustainable agriculture by the **terraGEM** Engineering Team.*
