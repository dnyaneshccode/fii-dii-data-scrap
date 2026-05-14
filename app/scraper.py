from datetime import datetime
from time import sleep
from datetime import datetime, timedelta
import requests
import io
import pandas as pd

NSE_URL = "https://www.nseindia.com/reports/fii-dii"
NSE_API_URL = "https://www.nseindia.com/api/fiidiiTradeReact"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "application/json,text/plain,*/*",
    "Referer": NSE_URL,
    "Connection": "keep-alive",
}


def _get_with_retry(session, url, timeout=30, attempts=3):
    last_error = None

    for attempt in range(1, attempts + 1):
        try:
            response = session.get(url, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            last_error = exc
            print(f"NSE request failed ({attempt}/{attempts}): {url} - {exc}")
            if attempt < attempts:
                sleep(2 * attempt)

    raise last_error


def get_session():
    session = requests.Session()
    session.headers.update(HEADERS)
    return session


def _parse_float(value):
    if value is None:
        raise ValueError("Missing numeric value")

    cleaned = str(value).replace(",", "").strip()
    if not cleaned or cleaned in {"-", "--"}:
        raise ValueError(f"Invalid numeric value: {value!r}")

    return float(cleaned)


def _parse_trade_date(value):
    if not value:
        return datetime.today().date()

    cleaned = str(value).strip()
    for date_format in ("%d-%b-%Y", "%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(cleaned, date_format).date()
        except ValueError:
            continue

    raise ValueError(f"Unsupported trade date format: {value!r}")


def _get_rows(payload):
    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict):
        for key in ("data", "records", "items"):
            rows = payload.get(key)
            if isinstance(rows, list):
                return rows

    raise ValueError(f"Unexpected NSE FII/DII response shape: {type(payload).__name__}")


def scrape_fii_dii_data():
    print("calling_scrape_fii_dii_data")
    session = get_session()

    try:
        response = _get_with_retry(session, NSE_API_URL, timeout=30)
    except requests.RequestException:
        print("Direct NSE API call failed. Trying with NSE page warm-up.")
        session.headers.update({"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"})
        _get_with_retry(session, NSE_URL, timeout=30)
        session.headers.update({"Accept": "application/json,text/plain,*/*"})
        response = _get_with_retry(session, NSE_API_URL, timeout=30)

    print("response", response.status_code)

    payload = response.json()
    rows = _get_rows(payload)
    print("NSE_FII_DII_ROWS__", rows)

    records = []

    for row in rows:
        try:
            category = str(row.get("category", "")).strip()
            trade_date = _parse_trade_date(row.get("date"))
            buy_value = _parse_float(row.get("buyValue"))
            sell_value = _parse_float(row.get("sellValue"))
            net_value = _parse_float(row.get("netValue"))

            if not category:
                raise ValueError(f"Missing category in row: {row!r}")

            records.append({
                "trade_date": trade_date,
                "category": category,
                "buy_value": buy_value,
                "sell_value": sell_value,
                "net_value": net_value
            })

            print(trade_date)
            print(category)
            print(buy_value)
            print(sell_value)
            print(net_value)

        except Exception as e:
            print("Skipping row:", row, "error:", str(e))

    if not records:
        raise ValueError("NSE FII/DII API returned no insertable records")

    return records

# DII HISTORICAL DATA

BSE_HISTORICAL_DII_URL = (
    "https://api.bseindia.com/BseIndiaAPI/api/"
    "StockpricesearchData/w"
)

def _safe_float(value):

    if value is None:
        return None

    cleaned = str(value).replace(",", "").strip()

    if cleaned in {"", "-", "--", "null"}:
        return None

    return float(cleaned)


def scrape_historical_dii_data():

    print("calling_scrape_historical_dii_data")

    session = get_session()

    try:

        warmup_response = session.get(
            "https://www.bseindia.com/",
            timeout=20
        )

        print(
            "BSE warmup status:",
            warmup_response.status_code
        )

    except Exception as e:

        print("BSE warmup failed:", str(e))

    session.headers.update({
        "Accept": "application/json, text/plain, */*",
        "Referer": (
            "https://www.bseindia.com/"
            "markets/equity/eqreports/"
            "stockprchistori?flag=1"
        ),
        "Origin": "https://www.bseindia.com",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
    })

    all_records = []

    start_date = datetime(2016, 1, 1).date()
    end_date = datetime.today().date()

    current_date = start_date

    while current_date <= end_date:

        next_date = current_date + timedelta(days=1)

        from_date = current_date.strftime("%d/%m/%Y")
        to_date = next_date.strftime("%d/%m/%Y")

        print(
            f"Fetching BSE daily DII data "
            f"from {from_date} to {to_date}"
        )

        params = {
            "MonthDate": from_date,
            "YearDate": to_date,
            "pageType": 1,
            "Scode": "",
            "Seg": "C",
            "rbType": "D"
        }

        try:

            response = session.get(
                BSE_HISTORICAL_DII_URL,
                params=params,
                timeout=30
            )

            print(
                "STATUS_CODE:",
                response.status_code
            )

            response.raise_for_status()

            try:

                payload = response.json()

            except Exception:

                print(
                    "INVALID_JSON_RESPONSE"
                )

                print(response.text[:500])

                current_date += timedelta(days=1)

                continue

            rows = payload.get("CatStockData", [])

            print(
                f"Rows fetched: {len(rows)}"
            )

            for row in rows:

                try:

                    reporting_date = datetime.strptime(
                        row["REPORTING_DATE"],
                        "%d/%m/%Y"
                    ).date()

                    record = {

                        "reporting_date": reporting_date,

                        "purchase_client": _safe_float(
                            row.get("PURCHASE_CLIENT")
                        ),

                        "sale_client": _safe_float(
                            row.get("SALE_CLIENT")
                        ),

                        "net_client": _safe_float(
                            row.get("NET_CLIENT")
                        ),

                        "purchase_nri": _safe_float(
                            row.get("PURCHASE_NRI")
                        ),

                        "sale_nri": _safe_float(
                            row.get("SALE_NRI")
                        ),

                        "net_nri": _safe_float(
                            row.get("NET_NRI")
                        ),

                        "purchase_own": _safe_float(
                            row.get("PURCHASE_OWN")
                        ),

                        "sale_own": _safe_float(
                            row.get("SALE_OWN")
                        ),

                        "net_own": _safe_float(
                            row.get("NET_OWN")
                        ),

                        "purchase_dii_bsense": _safe_float(
                            row.get("PURCHASE_DII_BSENSE")
                        ),

                        "sale_dii_bsense": _safe_float(
                            row.get("SALE_DII_BSENSE")
                        ),

                        "net_dii_bsense": _safe_float(
                            row.get("NET_DII_BSENSE")
                        ),
                    }

                    all_records.append(record)

                except Exception as row_error:

                    print(
                        "Skipping row:",
                        row,
                        "error:",
                        str(row_error)
                    )

        except Exception as e:

            print(
                f"Failed for {from_date}: {str(e)}"
            )

        current_date += timedelta(days=1)

    print(
        "TOTAL_HISTORICAL_DAILY_DII_RECORDS",
        len(all_records)
    )

    return all_records




NSE_FII_DERIVATIVE_REPORT_URL = (
    "https://www.nseindia.com/api/reports"
)


def scrape_fii_derivatives_data():

    print("calling_scrape_fii_derivatives_data")

    session = get_session()

    session.get(
        "https://www.nseindia.com/",
        timeout=20
    )

    archives_payload = [
        {
            "name": "F&O - FII Derivatives Statistics",
            "type": "archives",
            "category": "derivatives",
            "section": "equity"
        }
    ]

    # Hardcoded for testing
    today = "12-May-2026"

    params = {
        "archives": str(archives_payload).replace("'", '"'),
        "date": today,
        "type": "equity",
        "mode": "single"
    }

    response = session.get(
        NSE_FII_DERIVATIVE_REPORT_URL,
        params=params,
        timeout=60
    )

    print("STATUS_CODE", response.status_code)

    response.raise_for_status()

    print(
        "CONTENT_TYPE",
        response.headers.get("content-type")
    )

    excel_data = io.BytesIO(response.content)

    df = pd.read_excel(
        excel_data,
        sheet_name=0,
        engine="xlrd",
        header=None
    )

    records = []

    current_category = None

    valid_categories = {
        "INDEX FUTURES": "INDEX_FUTURES",
        "INDEX OPTIONS": "INDEX_OPTIONS",
        "STOCK FUTURES": "STOCK_FUTURES",
        "STOCK OPTIONS": "STOCK_OPTIONS",
    }

    skip_contains = [
        "NOTES",
        "VALUE",
        "OPEN INTEREST AT THE END OF DAY",
        "BOTH BUY AND SELL",
        "NO. OF CONTRACTS",
        "AMT IN CRORES",
    ]

    for _, row in df.iterrows():

        raw_values = row.tolist()

        cleaned_values = []

        for value in raw_values:

            if pd.isna(value):

                cleaned_values.append("")

            else:

                cleaned_values.append(
                    str(value).strip()
                )

        non_empty_values = [
            value
            for value in cleaned_values
            if value != ""
        ]

        if not non_empty_values:
            continue

        first_col = non_empty_values[0]

        upper_value = first_col.upper().strip()

        should_skip = any(
            keyword in upper_value
            for keyword in skip_contains
        )

        if should_skip:

            print(
                "Skipping non-data row:",
                first_col
            )

            continue

        try:

            numeric_values = []

            for value in non_empty_values[1:]:

                parsed = _safe_float(value)

                if parsed is not None:

                    numeric_values.append(parsed)

            # Need exactly 6 numeric values
            if len(numeric_values) != 6:

                print(
                    "Skipping invalid row:",
                    non_empty_values
                )

                continue

            # CATEGORY SUMMARY ROW
            if upper_value in valid_categories:

                current_category = valid_categories[
                    upper_value
                ]

                instrument_name = upper_value

                print(
                    "CURRENT_CATEGORY_SET:",
                    current_category
                )

            else:

                # Child rows
                if current_category is None:
                    continue

                instrument_name = first_col

            record = {

                "trade_date":
                    datetime.today().date(),

                "category":
                    current_category,

                "instrument_name":
                    instrument_name,

                "buy_contracts":
                    numeric_values[0],

                "buy_amount_crores":
                    numeric_values[1],

                "sell_contracts":
                    numeric_values[2],

                "sell_amount_crores":
                    numeric_values[3],

                "open_interest_contracts":
                    numeric_values[4],

                "open_interest_amount_crores":
                    numeric_values[5],
            }

            print(
                "PARSED_RECORD",
                record
            )

            records.append(record)

        except Exception as e:

            print(
                "Skipping derivative row:",
                non_empty_values,
                str(e)
            )

    print(
        "TOTAL_FII_DERIVATIVE_RECORDS",
        len(records)
    )

    return records