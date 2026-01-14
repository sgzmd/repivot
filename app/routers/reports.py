from fastapi import APIRouter, Depends, Request
from typing import Any
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import MonthlySummary
from ..auth import require_auth
from ..dependencies import templates
from itertools import groupby
from operator import attrgetter

router = APIRouter()


@router.get("/reports", response_class=HTMLResponse)
async def view_reports(
    request: Request, db: Session = Depends(get_db), user: dict = Depends(require_auth)
):
    # Fetch all, order by month desc, person
    summaries = (
        db.query(MonthlySummary)
        .order_by(
            MonthlySummary.month_year.desc(),
            MonthlySummary.person_name,
            MonthlySummary.total_amount.desc(),
        )
        .all()
    )

    # Process data for view: Group by Month -> Person -> List of items + Total
    reports_data: dict[str, Any] = {}

    for month, group_month in groupby(summaries, key=attrgetter("month_year")):
        reports_data[month] = {}
        # Sort by person within month just to be safe for groupby
        month_items = list(group_month)
        month_items.sort(key=attrgetter("person_name"))

        for person, group_person in groupby(month_items, key=attrgetter("person_name")):
            items = list(group_person)
            total = sum(i.total_amount for i in items)
            reports_data[month][person] = {
                "entries": items,
                "total": total,
                "currency": items[0].currency if items else "GBP",
            }

    return templates.TemplateResponse(
        "report.html", {"request": request, "user": user, "reports": reports_data}
    )
