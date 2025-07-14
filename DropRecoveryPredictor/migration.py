import pandas as pd
from sqlalchemy import create_engine
from models import Base

# TODO make pretty and more functional

csv_file = 'predictors/data/A.csv'
data = pd.read_csv(csv_file)

data.rename(columns={
    "Date": "date",
    "Open": "open",
    "High": "high",
    "Low": "low",
    "Close": "close",
    "Volume": "volume",
    "Dividends": "dividends",
    "Stock Splits": "stock_splits"
}, inplace=True)

data['ticker'] = "A"

with open("config.cfg", "r") as file:
    # Most ugly string parsing I could manage, but I don't want to change the config
    sqlalchemy_database_uri = file.read().split(" ")[-1]

engine = create_engine(sqlalchemy_database_uri)
Base.metadata.create_all(engine)

with engine.begin() as connection:
    data.to_sql('stock', connection, if_exists='append', index=False)
