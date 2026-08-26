# terraGEM Sensor Simulator

A standalone Python tool that feeds the terraGEM API with realistic
greenhouse sensor data **through the REST API** — it never touches the
database directly. Use it whenever you need a populated development
environment but don't have real hardware or an IoT pipeline available.

It has two phases:

| Phase | Command | What it does |
|---|---|---|
| Initialization | `python -m simulator.initialize` | Creates sensor profiles, greenhouses, sensors and alert thresholds, then backfills **26 hours** of history (5-minute resolution) |
| Real-time | `python -m simulator.live` | Every **5 minutes**, pushes one new reading per active simulated sensor — indefinitely |

---

## Requirements

- Python 3.11+
- A running terraGEM API (`codebase/api`, `python manage.py runserver`)
- A Django account on that API (any regular user works; superuser is not required)

## Setup

```bash
cd codebase/sensor-simulator

python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt  # runtime: requests + pyyaml
pip install -r requirements-dev.txt  # only if you want to run the tests
```

## Configuration

All settings live in `config.yaml` (see the bundled example):

```yaml
api:
  base_url: http://127.0.0.1:8000/api   # where the DRF API runs
  username: mehmet_grower               # any existing API account
  password: StrongPassword123!

simulation:
  backfill_hours: 26        # history depth created by initialize (24h + buffer past midnight)
  backfill_step_minutes: 5  # resolution of backfilled readings
  workers: 8                # parallel HTTP workers used during backfill
  interval_seconds: 300     # live loop cadence (5 minutes)

greenhouses:
  - name: North Tunnel
    description: Polytunnel - tomato rows [sim]
    latitude: 52.09288       # optional
    longitude: 5.10448       # optional
    sensors:                 # sensor type -> count
      air_temperature: 2
      air_humidity: 3
      soil_temperature: 2
      soil_humidity: 2
      co2: 1
      ph: 1
      light_intensity: 1
```

Valid sensor types: `air_temperature`, `soil_temperature`,
`air_humidity`, `soil_humidity`, `co2`, `ph`, `light_intensity`.

> Tip: don't commit real credentials. If you fork this workflow, keep a
> `config.local.yaml` out of version control and pass it via
> `--config config.local.yaml`.

---

## Usage

### Phase 1 — Initialize the world

```bash
python -m simulator.initialize            # uses ./config.yaml
python -m simulator.initialize --config path/to/config.yaml
python -m simulator.initialize --workers 16   # speed up the backfill
```

What it does, in order:

1. **Logs in** and obtains a JWT pair.
2. **Ensures sensor profiles exist** (one catalog profile per sensor
   type; created only if missing).
3. **Creates greenhouses** — matched *by name*, so re-running never
   duplicates them.
4. **Creates sensors** — described as e.g.
   `Air temperature #1 · [sim]`. The `[sim]` tag identifies simulated
   devices; existing ones are reused, not recreated.
5. **Seeds alert thresholds** per sensor (warning/critical bands per
   type) so status badges and the alert system have real limits to work
   with. Light intensity is intentionally left without thresholds.
6. **Backfills history**: 26 hours at 5-minute steps = 313 readings per
   sensor (~9,400 POSTs for a full 30-sensor world). Runs through a
   thread pool with live progress output.

The whole phase is **idempotent** — safe to stop mid-way and re-run;
only missing entities are created.

Example output:

```
profile 'DS18B20' found (#1)
greenhouse 'North Tunnel' created (#3)
sensor 'Air temperature #1 · [sim]' created (#12)
thresholds created: 11
backfilling 11 sensors x 313 readings (26h @ 5min)
backfill progress: 3443/3443
done: {'greenhouses': 1, 'sensors': 11, 'readings_pushed': 3443}
```

### Phase 2 — Live feed

```bash
python -m simulator.live                       # 5-minute cadence from config
python -m simulator.live --interval 10         # faster, handy for demos
python -m simulator.live --max-cycles 3        # exit after N cycles (testing)
```

- Discovers all **active** sensors tagged `[sim]` via the API at startup
  (no provisioning happens here).
- Waits until the next aligned interval boundary, then posts one reading
  per sensor, all stamped with the same timestamp.
- Automatically refreshes the JWT when it expires mid-run.
- Stop with `Ctrl-C`.

Keep it running in a terminal while you work:

```bash
python -m simulator.live          # terminal 1
cd ../web-dashboard && npm run dev    # terminal 2
```

---

## How the signals behave

Values are **deterministic pure functions** of `(sensor identity,
timestamp)` — same input always yields the same reading, so the
backfilled history lines up perfectly with whatever the live loop later
produces, and re-runs are reproducible.

Per-type behaviour over a day:

| Type | Pattern |
|---|---|
| Air temperature | Sine curve peaking mid-afternoon (~21 °C avg, ±3.5 °C), seeded noise |
| Soil temperature | Flatter sine lagging air temp (~19 °C ±1.5 °C) |
| Air humidity | Inverse of temperature (~66 % ±10 %) |
| Soil moisture | Sawtooth: drains ~14 points over 29 h then "irrigates" back up |
| CO₂ | Dips during daylight (photosynthesis), rises at night |
| pH | Nearly flat around 6.3 with tiny noise |
| Light intensity | Daylight bell between 06:00–19:00, exactly zero at night |

Noise changes every 5 minutes (fast) and hourly (slow drift), so charts
look organic rather than noisy or artificially smooth.

---

## Testing the web dashboard end-to-end

1. Start the API: `cd api && python manage.py runserver`
2. Seed data once: `python -m simulator.initialize`
3. Start the live feed: `python -m simulator.live`
4. Start the frontend: `cd ../web-dashboard && npm run dev`
5. Log in at `http://localhost:5173` and check:
   - **Overview**: KPI cards with sparklines and 24 h deltas, trend chart
     fully drawn, today-summary populated. With Live on you'll see values
     move within ≤15 s of each simulator tick.
   - **Alerts**: edit a sensor's threshold in the Sensors drawer to a very
     narrow band (e.g. warning 20.0–20.1) → an alert appears on Overview
     after the next alerts poll.
   - **History**: pick the greenhouse/metric → 144 ten-minute buckets,
     CSV export works.
6. If you ever want a clean slate, delete the tagged items from your
   account (greenhouse deletion cascades to sensors and measurements).

## Running the test suite

```bash
pip install -r requirements-dev.txt
pytest
```

60 tests cover: signal determinism/bounds/realism, JWT login + refresh
flow, payload shapes, config validation, initialization idempotency,
backfill counts/timestamps, and live-loop cycle arithmetic. No network
access is needed — all transport is faked.

---

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `HTTP 401` on every call | Wrong credentials in `config.yaml`, or the account doesn't exist yet (`createsuperuser` or `POST /api/auth/register/`) |
| `HTTP 404` on `/sensor-profiles/` etc. | API not running, or wrong `base_url` (must include `/api`) |
| Dashboard shows no metrics although sensors exist | Sensors may have been created inactive. Re-create them with this simulator (it always requests `is_active: true`) or toggle them on in the dashboard's Sensors page |
| Backfill feels slow | Raise `workers` (8 → 16); the bottleneck is per-request HTTP overhead |

## Project structure

```
sensor-simulator/
├── config.yaml           # configuration (copy & adapt)
├── requirements.txt      # requests, pyyaml
├── requirements-dev.txt  # pytest
├── pytest.ini
├── README.md
├── simulator/
│   ├── client.py         # JWT API client w/ auto-refresh
│   ├── world.py          # config parsing -> greenhouse/sensor plans
│   ├── signals.py        # deterministic per-type value generators
│   ├── initialize.py     # phase 1: provision + backfill
│   └── live.py           # phase 2: interval loop
└── tests/                # 60 tests, no network required
```
