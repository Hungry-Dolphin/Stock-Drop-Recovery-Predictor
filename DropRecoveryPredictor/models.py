from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import declarative_base, Mapped, mapped_column

Base = declarative_base()

class Stock(Base):
    __tablename__ = 'stock'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[str] = mapped_column(DateTime, nullable=False)
    ticker: Mapped[str] = mapped_column(String, nullable=False)
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[int] = mapped_column(Integer, nullable=False)
    dividends: Mapped[float] = mapped_column(Float, nullable=False)
    stock_splits: Mapped[float] = mapped_column(Float, nullable=False)
