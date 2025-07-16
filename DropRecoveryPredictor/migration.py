import pandas as pd
from sqlalchemy import create_engine
from models import Base
from os import listdir
from os.path import isfile, join

# Most of the data is also stored locally, this was incase I needed to reset the DB
# This script uploads all the local data to postgres

def upload_to_postgres(df, ticker: str):

    df.rename(columns={
        "Date": "date",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume",
        "Dividends": "dividends",
        "Stock Splits": "stock_splits"
    }, inplace=True)

    df['ticker'] = ticker

    with open("config.cfg", "r") as file:
        # Most ugly string parsing I could manage, but I don't want to change the config
        sqlalchemy_database_uri = file.read().split(" ")[-1]

    engine = create_engine(sqlalchemy_database_uri)
    Base.metadata.create_all(engine)

    with engine.begin() as connection:
        df.to_sql('stock', connection, if_exists='append', index=False)

def main():
    path = 'predictors/data/'
    csv_files = [f for f in listdir(path) if isfile(join(path, f))]

    for file in csv_files:
        df = pd.read_csv(join(path, file))
        upload_to_postgres(df, file.split('.')[0])

if __name__ == '__main__':
    main()