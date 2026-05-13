from sqlalchemy.orm import Session
from .models import FiiDiiData
from .models import FiiDerivativeStatistics
from .models import HistoricalClientCategoryTurnover
def insert_fii_dii_data(db: Session, records: list):
    inserted_count = 0
    skipped_count = 0

    for item in records:

        existing = db.query(FiiDiiData).filter(
            FiiDiiData.trade_date == item["trade_date"],
            FiiDiiData.category == item["category"]
        ).first()

        if not existing:

            record = FiiDiiData(
                trade_date=item["trade_date"],
                category=item["category"],
                buy_value=item["buy_value"],
                sell_value=item["sell_value"],
                net_value=item["net_value"]
            )

            db.add(record)
            inserted_count += 1
        else:
            skipped_count += 1

    db.commit()

    print(
        "FII/DII DB insert summary:",
        {
            "received": len(records),
            "inserted": inserted_count,
            "already_exists": skipped_count,
        },
    )

    return inserted_count



def insert_historical_dii_data(
    db: Session,
    records: list
):

    inserted_count = 0
    skipped_count = 0

    existing_dates = {
        row[0]
        for row in db.query(
            HistoricalClientCategoryTurnover.reporting_date
        ).all()
    }

    for item in records:

        reporting_date = item["reporting_date"]

        if reporting_date in existing_dates:

            skipped_count += 1

            continue

        try:

            record = HistoricalClientCategoryTurnover(
                **item
            )

            db.add(record)

            inserted_count += 1

            existing_dates.add(reporting_date)

        except Exception as e:

            print(
                "Insert failed for:",
                reporting_date,
                str(e)
            )

    db.commit()

    print(
        "Historical Daily DII DB insert summary:",
        {
            "received": len(records),
            "inserted": inserted_count,
            "already_exists": skipped_count,
        },
    )

    return inserted_count



def insert_fii_derivatives_data(
    db: Session,
    records: list
):

    inserted_count = 0
    skipped_count = 0

    existing_records = {
        (
            row.trade_date,
            row.category,
            row.instrument_name
        )
        for row in db.query(
            FiiDerivativeStatistics
        ).all()
    }

    for item in records:

        unique_key = (
            item["trade_date"],
            item["category"],
            item["instrument_name"]
        )

        if unique_key in existing_records:

            skipped_count += 1

            continue

        try:

            record = FiiDerivativeStatistics(
                **item
            )

            db.add(record)

            inserted_count += 1

            existing_records.add(unique_key)

        except Exception as e:

            print(
                "Insert failed:",
                item,
                str(e)
            )

    db.commit()

    print(
        "FII Derivatives insert summary:",
        {
            "received": len(records),
            "inserted": inserted_count,
            "already_exists": skipped_count,
        },
    )

    return inserted_count