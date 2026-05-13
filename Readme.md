# FII / DII Data Scraper Service

## Overview

This service is built using:

- :contentReference[oaicite:0]{index=0}
- :contentReference[oaicite:1]{index=1}
- APScheduler
- SQLAlchemy
- Requests

The application fetches FII/FPI and DII trading activity data from NSE and stores it into PostgreSQL.

Source API:

[NSE FII/DII API](https://www.nseindia.com/api/fiidiiTradeReact?utm_source=chatgpt.com)

Reference Page:

[NSE FII/DII Reports Page](https://www.nseindia.com/reports/fii-dii?utm_source=chatgpt.com)

The application supports:

- Daily automatic data fetch using scheduler
- Manual trigger API
- Duplicate prevention
- Retry handling for NSE blocking/rate limiting
- Database persistence

---

# How the Application Works

The application works in two ways:

1. Automatic Scheduler
2. Manual API Trigger

---

# 1. Automatic Scheduler

The scheduler is configured in:

```python
app/scheduler.py
```

The scheduler runs every day automatically at:

```python
hour=19,
minute=0
```

This means:

- The job runs daily at 7:00 PM
- It uses the server/local machine timezone

Since the machine timezone is:

```text
Asia/Calcutta
```

the scheduler executes every day at:

```text
7:00 PM IST
```

Important:

The scheduler only works while the FastAPI application is running.

If the application/server is stopped:
- scheduler will not run
- no automatic data fetch will happen

---

# Scheduler Flow

Every day at 7:00 PM IST:

1. Scheduler triggers the job
2. Application calls NSE API
3. FII/DII data is fetched
4. Data is parsed
5. Data is inserted into PostgreSQL
6. Duplicate records are skipped automatically
7. Logs are printed

---

# Scheduler Configuration

Current scheduler configuration:

```python
scheduler.add_job(
    run_daily_job,
    trigger='cron',
    hour=19,
    minute=0
)
```

---

# 2. Manual Run

The application also provides a manual API endpoint.

File:

```python
app/main.py
```

Endpoint:

```python
/run-now
```

If the application is running locally, open:

```text
http://127.0.0.1:8000/run-now
```

This immediately performs:

- NSE API call
- Data fetch
- Data processing
- Database insert

without waiting for the scheduler.

---

# Manual Run Use Cases

Manual run is useful for:

- Testing
- Debugging
- Verifying NSE API response
- Checking DB insert behavior
- Running data fetch before scheduler time
- Production support verification

---

# NSE Data Source

The application fetches data from:

```text
https://www.nseindia.com/api/fiidiiTradeReact
```

This API provides:

- FII/FPI trading activity
- DII trading activity
- Capital Market Segment data
- Combined NSE + BSE + MSEI values

---

# When NSE Updates the Data

Typically, NSE updates FII/DII cash market data:

- After market close
- Usually during evening hours

Because of this, scheduler timing at:

```text
7:00 PM IST
```

is considered a reasonable and safe fetch time.

---

# Database Duplicate Protection

The database has a unique constraint configured on:

```text
trade_date + category
```

This prevents duplicate records from being inserted.

Example:

| trade_date | category |
|---|---|
| 2026-05-12 | FII/FPI |
| 2026-05-12 | DII |

If the same date and category already exist:
- insert will be skipped
- duplicate rows will not be created

---

# Example Duplicate Prevention Logs

Example log:

```text
FII/DII DB insert summary:
{
    'received': 2,
    'inserted': 0,
    'already_exists': 2
}
```

Meaning:

- 2 records were fetched from NSE
- Both records already existed in DB
- No duplicate rows were inserted

This is expected behavior and confirms duplicate protection is working correctly.

---

# Example Successful Insert Logs

```text
FII/DII DB insert summary:
{
    'received': 2,
    'inserted': 2,
    'already_exists': 0
}
```

Meaning:

- 2 records fetched
- Both records inserted successfully
- No duplicates found

---

# Retry Handling

NSE sometimes blocks automated requests or returns temporary failures like:

- 401
- 403
- 429
- 503

To handle this, the scraper includes:

- Session handling
- Browser headers
- Retry logic
- Delayed retries

This improves reliability and reduces NSE blocking issues.

---

# Database Table

Main table:

```text
fii_dii_data
```

Columns:

| Column | Description |
|---|---|
| id | Primary key |
| trade_date | Trading date |
| category | FII/FPI or DII |
| buy_value | Buy amount |
| sell_value | Sell amount |
| net_value | Net buy/sell |
| source | Data source |
| exchange_group | NSE+BSE+MSEI |

---

# Project Structure

```text
app/
│
├── main.py
├── scheduler.py
├── scraper.py
├── crud.py
├── database.py
├── models.py
```

---

# Main Components

## main.py

Responsible for:
- FastAPI application
- API endpoints
- Scheduler startup

---

## scheduler.py

Responsible for:
- Daily cron execution
- Running scheduled jobs
- Triggering scraper flow

---

## scraper.py

Responsible for:
- Calling NSE API
- Parsing API response
- Retry handling
- Session management

---

## crud.py

Responsible for:
- Database insert logic
- Duplicate checks
- Commit handling

---

## database.py

Responsible for:
- PostgreSQL connection
- SQLAlchemy engine
- Session creation

---

## models.py

Responsible for:
- Database schema
- Table definitions
- Constraints

---

# Running the Application

Start FastAPI server:

```bash
uvicorn app.main:app --reload
```

---

# Verify Server

Open:

```text
http://127.0.0.1:8000
```

Expected response:

```json
{
  "status": "running"
}
```

---

# Trigger Manual Data Fetch

Open:

```text
http://127.0.0.1:8000/run-now
```

---

# Important Notes

## Scheduler Dependency

Automatic scheduler only works while application is running.

If FastAPI server is stopped:
- scheduler stops
- no automatic data collection occurs

---

## NSE API Dependency

Application depends on NSE API availability.

If NSE:
- changes API response
- blocks requests
- changes authentication/cookies

then scraper updates may be required.

---

# Recommended Future Improvements

Future production improvements:

- Structured logging
- Alembic migrations
- Docker deployment
- Redis queue
- Celery workers
- Monitoring/alerts
- Historical backfill support
- Bulk insert optimization
- PostgreSQL UPSERT support

---

# Summary

This application:

- Fetches daily FII/DII cash market data
- Stores data into PostgreSQL
- Prevents duplicate inserts
- Supports automatic scheduled execution
- Supports manual execution
- Handles NSE retry scenarios
- Uses production-style layered architecture
