import pytest
import pandas as pd
import io
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, MonthlySummary
from app.processor import process_revolut_file


# Sample data construction
def create_sample_xls():
    data = {
        "Type": ["Card Payment", "Card Payment", "Free", "Card Payment"],
        "Product": ["Current", "Current", "Current", "Current"],
        "Started": [
            "2023-01-01 10:00:00",
            "2023-01-02 11:00:00",
            "2023-01-03",
            "2023-02-01",
        ],
        "Completed Date": [
            "2023-01-01 10:00:00",
            "2023-01-02 11:00:00",
            "2023-01-03",
            "2023-02-01",
        ],
        "Description": ["Groceries", "Transport", "Fee", "Groceries"],
        "Amount": [10.50, 5.00, 0.00, 20.00],
        "Fee": [0.00, 0.10, 0.00, 0.00],
        "Currency": ["GBP", "GBP", "GBP", "GBP"],
    }
    df = pd.DataFrame(data)

    # Save to bytes
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()


@pytest.fixture
def db_session():
    # In-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_process_revolut_file(db_session):
    content = create_sample_xls()
    person = "Eva"

    count = process_revolut_file(content, person, db_session)

    # We expect 3 Card Payments.
    # But we are aggregating by Month, Description, Currency.
    # Jan: Groceries (10.50), Transport (5.10 with fee). Total 2 rows.
    # Feb: Groceries (20.00). Total 1 row.
    # Total summaries = 3.

    # Wait, 'process_revolut_file' returns count? It returns len(summaries).
    # Grouping:
    # 2023-01, Groceries, GBP -> 10.50
    # 2023-01, Transport, GBP -> 5.10
    # 2023-02, Groceries, GBP -> 20.00

    assert count == 3

    summaries = db_session.query(MonthlySummary).all()
    assert len(summaries) == 3

    s1 = (
        db_session.query(MonthlySummary)
        .filter_by(description="Groceries", month_year="2023-01")
        .first()
    )
    assert s1.total_amount == 10.50
    assert s1.person_name == person

    s2 = (
        db_session.query(MonthlySummary)
        .filter_by(description="Transport", month_year="2023-01")
        .first()
    )
    assert s2.total_amount == 5.10  # 5.00 + 0.10

    s3 = (
        db_session.query(MonthlySummary)
        .filter_by(description="Groceries", month_year="2023-02")
        .first()
    )
    assert s3.total_amount == 20.00


def test_overwrite_logic(db_session):
    content = create_sample_xls()
    person = "Eva"

    process_revolut_file(content, person, db_session)

    # Process again, same file. Should overwrite (delete then insert), so count remains same.
    process_revolut_file(content, person, db_session)

    summaries = db_session.query(MonthlySummary).all()
    assert len(summaries) == 3
