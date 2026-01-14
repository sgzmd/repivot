from sqlalchemy import Column, Integer, String, Float, UniqueConstraint
from .database import Base


class MonthlySummary(Base):
    __tablename__ = "monthly_summaries"

    id = Column(Integer, primary_key=True, index=True)
    person_name = Column(String, index=True)
    month_year = Column(String, index=True)  # Format: YYYY-MM
    description = Column(String)
    total_amount = Column(Float)
    currency = Column(String)

    __table_args__ = (
        UniqueConstraint(
            "person_name", "month_year", "description", name="d_p_m_desc_uc"
        ),
    )
