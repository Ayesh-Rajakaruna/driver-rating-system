# UAH-DriveSet Migration Service

A small Spring Boot microservice with a single REST endpoint that walks an extracted
copy of the [UAH-DriveSet](http://www.robesafe.uah.es/personal/eduardo.romera/uah-driveset/)
dataset on disk and loads it into MySQL, matching the ER diagram we designed
(`drivers`, `trips`, `gps_data`, `imu_data`, `road_segment_readings`, `events`, `trip_labels`).

## 1. Prerequisites

- Java 17+
- Maven 3.8+
- A running MySQL 8 instance
- The dataset extracted locally, with this folder layout:

```
UAH-DRIVESET-v1/
  D1/
    20151111135612-16km-D1-NORMAL-MOTORWAY/
      RAW_GPS.txt
      RAW_ACCELEROMETERS.txt
      SEMANTIC_ONLINE.txt
      EVENTS_LIST_LANE_CHANGES.txt
    20151120175853-16km-D1-AGGRESSIVE-MOTORWAY/
      ...
  D2/
    ...
```

## 2. Create the database

```sql
CREATE DATABASE uah_driveset CHARACTER SET utf8mb4;
```

Tables are auto-created on startup (`spring.jpa.hibernate.ddl-auto: update`).

## 3. Configure

Set these environment variables (or edit `src/main/resources/application.yml` directly):

| Variable       | Default              | Purpose                          |
|----------------|----------------------|-----------------------------------|
| `DB_HOST`      | `localhost`           | MySQL host                        |
| `DB_PORT`      | `3306`                | MySQL port                        |
| `DB_NAME`      | `uah_driveset`        | Database name                     |
| `DB_USERNAME`  | `root`                | MySQL user                        |
| `DB_PASSWORD`  | `root`                | MySQL password                    |
| `DATASET_PATH` | `/data/UAH-DRIVESET-v1` | Default dataset root folder     |

## 4. Run

```bash
mvn spring-boot:run
```

## 5. Trigger the migration (single API call)

```bash
curl -X POST http://localhost:8080/api/v1/migration/start \
  -H "Content-Type: application/json" \
  -d '{"datasetPath": "/absolute/path/to/UAH-DRIVESET-v1"}'
```

Response:

```json
{
  "status": "SUCCESS",
  "driversCreated": 6,
  "tripsProcessed": 58,
  "gpsRowsInserted": 145000,
  "imuRowsInserted": 720000,
  "roadSegmentRowsInserted": 145000,
  "eventRowsInserted": 320,
  "tripLabelsInserted": 58,
  "skippedTrips": [],
  "elapsedTime": "PT42.31S"
}
```

- The call is **idempotent** — trips already present (matched by folder name) are
  skipped on re-run, so you can call it again after dropping new trip folders in
  without re-importing everything.
- Each trip folder is imported in its own transaction, so one malformed/incomplete
  trip folder won't roll back trips that already succeeded.

## 6. Known assumptions / things to verify against your dataset copy

- Trip folder names are parsed with the pattern `{yyyyMMddHHmmss}-{distance}km-{driverCode}-{BEHAVIOR}-{ROAD_TYPE}`
  (e.g. `20151111135612-16km-D1-NORMAL-MOTORWAY`). Folders that don't match this
  pattern are skipped and reported in `skippedTrips`.
- Column offsets for `RAW_GPS.txt`, `RAW_ACCELEROMETERS.txt`, and `SEMANTIC_ONLINE.txt`
  are documented as comments at the top of each parser class in
  `service/parser/`. Different dataset releases have shuffled these columns before —
  double check against the README bundled with your copy and adjust the `col(...)`
  indices if row counts look wrong after a test run.
- `WEATHER_LOG` from the final ER diagram is intentionally **not** implemented here —
  UAH-DriveSet ships no weather data natively, so that table would stay empty without
  a separate external-API enrichment step.
