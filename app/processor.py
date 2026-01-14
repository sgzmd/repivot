import pandas as pd
import io
from sqlalchemy.orm import Session
from .models import MonthlySummary


def process_revolut_file(file_content: bytes, person_name: str, db: Session):
    # Load Excel file
    try:
        df = pd.read_excel(io.BytesIO(file_content))
    except Exception as e:
        raise ValueError(f"Failed to read Excel file: {e}")

    # Expected columns check could go here, but strict filtering might be enough

    # Filter for 'Card Payment'
    if "Type" in df.columns:
        df = df[df["Type"] == "Card Payment"].copy()

    # Ensure required columns exist
    # required_cols = [
    #     "Product",
    #     "Amount",
    #     "Fee",
    #     "Currency",
    #     "Description",
    #     "Completed Date",
    # ]  # 'DateDescription' -> Description logic?
    # Prompt says: "Pivot the data by Description (from DateDescription)"
    # But usually Revolut export has 'Description'. Let's assume 'Description' exists or mapped from 'DateDescription'
    # Actually, verify column names. Standard Revolut usually has 'Description'.
    # The prompt mentions "DateDescription". I will look for Description or DateDescription.

    col_map = {"DateDescription": "Description"}
    df.rename(columns=col_map, inplace=True)

    if "Description" not in df.columns:
        # Fallback or error?
        pass

    # Transformation
    # TotalCost = Amount + Fee.
    # Ensure numeric
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)
    df["Fee"] = pd.to_numeric(df["Fee"], errors="coerce").fillna(0)
    df["TotalCost"] = df["Amount"] + df["Fee"]

    # Extract Month-Year. 'DateCompleted' or 'Started'? Prompt says 'Started', 'DateCompleted'.
    # Usually 'DateCompleted' is final.
    date_col = "Completed Date"
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], format="mixed", dayfirst=False)
        df["month_year"] = df[date_col].dt.strftime("%Y-%m")
    else:
        raise ValueError("Could not find date column")

    # Pivot / Aggregate
    # Group by Month, Description, Currency
    # We want to store monthly aggregates.

    # The requirement says: "Pivot the data by Description ... Aggregate: sum(TotalCost)"
    # And "Table: monthly_summaries (Columns: person_name, month_year, description, total_amount, currency)"

    # So we group by (month_year, Description, Currency)

    agg_df = (
        df.groupby(["month_year", "Description", "Currency"])["TotalCost"]
        .sum()
        .reset_index()
    )

    # Upsert Logic
    # Simple approach: Delete existing for this person & months found in file, then insert.
    # Or strict upsert row by row.
    # "If a report for the same Month and Person is uploaded again, overwrite existing records for that month"
    # This implies we should wipe data for the *months present in the file* for this *person*, then insert new.

    months_to_update = agg_df["month_year"].unique()

    for month in months_to_update:
        # Delete existing
        db.query(MonthlySummary).filter(
            MonthlySummary.person_name == person_name,
            MonthlySummary.month_year == month,
        ).delete()

    # Bulk insert
    summaries = []
    for _, row in agg_df.iterrows():
        summaries.append(
            MonthlySummary(
                person_name=person_name,
                month_year=row["month_year"],
                description=row["Description"],
                total_amount=row["TotalCost"],
                currency=row["Currency"],
            )
        )

    db.add_all(summaries)
    db.commit()

    return len(summaries)
