from sqlalchemy import Column, Integer, String, Float, Date, UniqueConstraint, DateTime
from .database import Base
from datetime import datetime
class FiiDiiData(Base):
    __tablename__ = "fii_dii_data"

    id = Column(Integer, primary_key=True, index=True)

    trade_date = Column(Date, nullable=False)

    category = Column(String, nullable=False)

    buy_value = Column(Float, nullable=False)

    sell_value = Column(Float, nullable=False)

    net_value = Column(Float, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            'trade_date',
            'category',
            name='unique_trade_date_category'
        ),
    )

class HistoricalClientCategoryTurnover(Base):

    __tablename__ = "historical_client_category_turnover"

    id = Column(Integer, primary_key=True, index=True)

    reporting_date = Column(Date, nullable=False)

    purchase_client = Column(Float)
    sale_client = Column(Float)
    net_client = Column(Float)

    purchase_nri = Column(Float)
    sale_nri = Column(Float)
    net_nri = Column(Float)

    purchase_own = Column(Float)
    sale_own = Column(Float)
    net_own = Column(Float)

    purchase_dii_bsense = Column(Float)
    sale_dii_bsense = Column(Float)
    net_dii_bsense = Column(Float)

    source = Column(String, nullable=False, default="BSE")

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    __table_args__ = (
        UniqueConstraint(
            'reporting_date',
            name='uq_historical_client_category_turnover_date'
        ),
    )




class FiiDerivativeStatistics(Base):

    __tablename__ = "fii_derivative_statistics"

    id = Column(Integer, primary_key=True, index=True)

    trade_date = Column(Date, nullable=False)

    category = Column(String, nullable=False)

    instrument_name = Column(String, nullable=False)

    buy_contracts = Column(Float)
    buy_amount_crores = Column(Float)

    sell_contracts = Column(Float)
    sell_amount_crores = Column(Float)

    open_interest_contracts = Column(Float)
    open_interest_amount_crores = Column(Float)

    source = Column(String, default="NSE")

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    __table_args__ = (
        UniqueConstraint(
            'trade_date',
            'category',
            'instrument_name',
            name='uq_fii_derivative_statistics'
        ),
    )