import pandas as pd
import logging
import logging.config
import yfinance as yf
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta

class RecoveryPredictor:
    model = None

    def __init__(self, db_uri: str, debug: bool = False):
        # Set up logging
        self.logger = logging.getLogger(__name__)
        ch = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(ch)
        self.logger.debug("Logging started")
        self.debug = debug
        if debug:
            self.logger.debug("Debug enabled started")

        # Set up db connection
        self.engine = create_engine(db_uri)
        self.logger.info("Connected to database")

        # Load in all stocks we are interested in
        self.stock_df = None
        self.fill_stock_df()

        self.logger.info('Class initialization complete')

    def fill_stock_df(self):
        if self.debug:
            filter_date = datetime.now() - timedelta(days=365)
            query = f"SELECT * FROM stock WHERE date >= '{filter_date.strftime("%Y-%m-%d %H:%M:%S")}'"
            self.stock_df = pd.read_sql(query, self.engine)
        else:
            self.stock_df = pd.read_sql("SELECT * FROM stock", self.engine)
        self.logger.info('Company data loaded from PostgreSQL')

    def get_stock_data(self, ticker: str, start_date: str, end_date: str, overwrite: bool = False):
        self.logger.debug(f"Checking stock data for {ticker}")

        # See if our existing data qualifies
        existing_data = self.stock_df[self.stock_df["ticker"] == ticker].copy()

        if not overwrite and not existing_data.empty:
            existing_dates = pd.to_datetime(existing_data["date"])
            all_required_dates = pd.date_range(start=start_date, end=end_date, freq="B")

            if all(d in set(existing_dates) for d in all_required_dates):
                self.logger.info(f"All required data already present for {ticker}")
                return None  # No need to fetch

        try:
            historical_data = yf.Ticker(ticker=ticker).history(start=start_date, end=end_date)
            if historical_data.empty:
                self.logger.warning(f"No data returned from Yahoo for {ticker}")
                return None

            historical_data.reset_index(inplace=True)
            historical_data = historical_data.fillna(0)
            historical_data['ticker'] = ticker
            historical_data['Date'] = pd.to_datetime(historical_data['Date']).dt.tz_localize(None)
            historical_data.rename(columns={
                'Date': 'date', 'Open': 'open', 'High': 'high','Low': 'low', 'Close': 'close', 'Volume': 'volume',
                'Dividends': 'dividends', 'Stock Splits': 'stock_splits'
            }, inplace=True)

            # Only keep columns we care about
            new_data = historical_data[[
                'date', 'ticker', 'open', 'high', 'low', 'close', 'volume', 'dividends', 'stock_splits'
            ]]

            # If overwrite, drop old and replace
            with self.engine.begin() as conn:
                if overwrite:
                    conn.execute(
                        text("DELETE FROM stock WHERE ticker = :ticker"),
                        {"ticker": ticker}
                    )
                    self.logger.info(f"Removed all stock data for {ticker}")

                if not existing_data.empty and not overwrite:
                    new_data = new_data[~new_data['date'].isin(existing_data['date'])]

                new_data.to_sql("stock", conn, if_exists="append", index=False)
                self.logger.info(f"Appended {len(new_data)} new rows for {ticker}")

            # Update in-memory price_df
            self.stock_df = pd.concat([self.stock_df, new_data], ignore_index=True)

            # Return all new rows
            return new_data

        except Exception as e:
            self.logger.error(f"Failed to fetch data for {ticker}: {e}")

    def create_price_drop_df(self, one_day_threshold: int, one_week_threshold: int, one_month_threshold: int):
        drop_event_df = pd.DataFrame()
        for ticker in self.stock_df['ticker'].unique():
            if ticker == 'TEST' and not self.debug:
                continue

            # The false is not needed but the price drop df is only made with existing data
            df = self.find_ticker_drops(ticker, one_day_threshold, one_week_threshold, one_month_threshold, False)
            drop_event_df = pd.concat([drop_event_df, df], ignore_index=True)

        return drop_event_df

    def find_ticker_drops(self, ticker: str, one_day_threshold: int, one_week_threshold: int, one_month_threshold: int, new_data: bool = False):
        if new_data:
            # Update this one with the new data we got
            self.fill_stock_df()
        price_history_df = self.stock_df[self.stock_df['ticker'] == ticker].copy()

        if price_history_df.empty or 'date' not in price_history_df.columns:
            self.logger.warning(f"No valid data for {ticker}")
            return None

        # Get one-day drops
        price_history_df['1 day drop'] = 100 / price_history_df['close'].shift(1) * price_history_df['close']

        # Get one-week drops
        price_history_df['1 week drop'] = 100 / price_history_df['close'].rolling(window=7).max().shift(1) * \
                                          price_history_df['close']

        # Get one-month drops
        price_history_df['1 month drop'] = 100 / price_history_df['close'].rolling(window=31).max().shift(1) * \
                                          price_history_df['close']

        # Get one-day recovery
        price_history_df['1 day recovery'] = 100 / price_history_df['close'].shift(1)  * price_history_df['close'].shift(-1)

        price_history_df['1 month recovery'] = 100 / price_history_df['close'].rolling(window=31).max().shift(1)  * price_history_df['close'][::-1].rolling(window=31).max()[::-1]

        one_day_drops = price_history_df[price_history_df["1 day drop"] < (100 - one_day_threshold)]
        one_week_drops = price_history_df[price_history_df["1 week drop"] < (100 - one_week_threshold)]
        one_month_drops = price_history_df[price_history_df["1 month drop"] < (100 - one_month_threshold)]

        df = pd.concat([one_day_drops, one_week_drops, one_month_drops]).drop_duplicates()

        if df.empty:
            # No drops found
            return None

        if not df.empty:
            latest_row = df.sort_values('date', ascending=False).iloc[0]
            self.logger.info(f"Latest drop detected is on {latest_row['date'].date()} for ticker {latest_row['ticker']}")
        else:
            self.logger.info("No drops detected.")

        return df
