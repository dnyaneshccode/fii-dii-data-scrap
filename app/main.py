from fastapi import FastAPI
from .database import engine, Base, SessionLocal
from .scheduler import (
    scheduler,
    run_daily_job,
    run_historical_dii_job,
    run_fii_derivatives_job
)

app = FastAPI()

Base.metadata.create_all(bind=engine)

scheduler.start()


@app.get("/")
def health_check():
    return {"status": "running"}


@app.get("/run-now")
def run_now():

    run_daily_job()

    return {"message": "Data fetched successfully"}


@app.get("/run-historical-dii")
def run_historical_dii():

    run_historical_dii_job()

    return {
        "message":
        "Historical DII data fetched successfully"
    }

@app.get("/run-fii-derivatives")
def run_fii_derivatives():

    run_fii_derivatives_job()

    return {
        "message":
        "FII derivative data fetched successfully"
    }