import os
import pandas as pd
import logging
import logging.config
import yfinance as yf
from time import sleep


class RecoveryPredictor:
    DATA_DIR_NAME = 'data'
    COMPANY_DIR = 'companies'


    def __init__(self, base_dir, refresh_data: bool = False):
        start_date = '2014-12-31'
        end_date = '2025-01-01'
        self.base_dir = base_dir

        self.logger = logging.getLogger(__name__)
        ch = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(ch)
        self.logger.debug("Logging started")

        # Load in all stocks we are interested in
        # TODO make it take all files
        file = [x for x in os.listdir(os.path.join(base_dir, self.DATA_DIR_NAME, self.COMPANY_DIR)) if x.endswith('.csv')][0]
        self.stock_df = pd.read_csv(os.path.join(base_dir, self.DATA_DIR_NAME, self.COMPANY_DIR, file))
        self.logger.info('Company data loaded')

        # Refresh the stock data if not all data is present, or we asked for a manual refresh
        len_company_data = len([x for x in os.listdir(os.path.join(base_dir, self.DATA_DIR_NAME)) if os.path.isfile(x)])
        if len_company_data < self.stock_df.shape[0]:
            self.logger.error("Not all stock data is present, loading in missing data")
            self.get_stock_data(start_date=start_date, end_date=end_date)

        elif refresh_data:
            self.logger.info("Getting new stock data")
            self.get_stock_data(overwrite=True, start_date=start_date, end_date=end_date)

        self.logger.info('Class initialization complete')

    def get_stock_data(self, start_date: str, end_date: str, overwrite: bool = False):

        stock_data_dir = os.path.join(self.base_dir, self.DATA_DIR_NAME)

        rate_limiter = 0
        for ticker in self.stock_df['Symbol'].unique():
            stock_file_path = os.path.join(stock_data_dir, f"{ticker}.csv")

            # Check if the file is already present for this company
            if os.path.isfile(stock_file_path) and not overwrite:
                continue

            # I don't want this to log if we are overriding everything anyway
            self.logger.info(f"Found missing stock data for company: {ticker}") if not overwrite else None

            historical_data = yf.Ticker(ticker=ticker).history(start=start_date, end=end_date)
            historical_data.to_csv(stock_file_path)
            rate_limiter += 1

            # Could have just made it wait x seconds per request
            # but this way if you only miss a few trackers it won't take as long if you only miss a few trackers
            if rate_limiter % 5 == 0:
                self.logger.info(f"Triggered self rate limiter")
                return
                # Every time I debug the application it will add 5 new stocks, this way i'll slowly get all 500
                sleep(60)

    def create_price_drop_df(self, one_day_threshold: int, one_week_threshold: int, one_month_threshold: int):
        drop_event_df = pd.DataFrame()

        for index, row in self.stock_df.iterrows():
            try:
                price_history_df = pd.read_csv(os.path.join(self.base_dir, self.DATA_DIR_NAME, f"{row['Symbol']}.csv"))
            except FileNotFoundError:
                self.logger.error(f"File not found for: {row['Symbol']} Skipping")
                continue

            if not 'Date' in price_history_df.columns:
                self.logger.info(f"File {row['Symbol']} dit not contain a Date index, removing file")
                os.remove(os.path.join(self.base_dir, self.DATA_DIR_NAME, f"{row['Symbol']}.csv"))
                continue
            elif price_history_df['Date'].isna().sum() > 5:
                self.logger.info(f"File {row['Symbol']} contained too many NA values, removing file")
                os.remove(os.path.join(self.base_dir, self.DATA_DIR_NAME, f"{row['Symbol']}.csv"))
                continue

            # Get one-day drops
            price_history_df['1 day drop'] = 100 / price_history_df['Close'].shift(1) * price_history_df['Close']

            # Get one-week drops
            price_history_df['1 week drop'] = 100 / price_history_df['Close'].rolling(window=7).max().shift(1) * \
                                              price_history_df['Close']

            # Get one-month drops
            price_history_df['1 month drop'] = 100 / price_history_df['Close'].rolling(window=31).max().shift(1) * \
                                              price_history_df['Close']

            # Get one-day recovery
            price_history_df['1 day recovery'] = 100 / price_history_df['Close'].shift(1)  * price_history_df['Close'].shift(-1)

            price_history_df['1 month recovery'] = 100 / price_history_df['Close'].rolling(window=31).max().shift(1)  * price_history_df['Close'][::-1].rolling(window=31).max()[::-1]

            one_day_drops = price_history_df[price_history_df["1 day drop"] < (100 - one_day_threshold)]
            one_week_drops = price_history_df[price_history_df["1 week drop"] < (100 - one_week_threshold)]
            one_month_drops = price_history_df[price_history_df["1 month drop"] < (100 - one_month_threshold)]

            # Create empty df to temporarily put the drops in
            df = pd.DataFrame(columns=price_history_df.columns)
            df = df.astype(price_history_df.dtypes)

            if not one_day_drops.empty:
                df = pd.concat([df, one_day_drops], ignore_index=True)
            if not one_week_drops.empty:
                df = pd.concat([df, one_week_drops], ignore_index=True)
            if not one_month_drops.empty:
                df = pd.concat([df, one_month_drops], ignore_index=True)

            df = df.drop_duplicates()
            # Add all stock info to this drop df
            for key, value in row.items():
                df[key] = value

            if index == 0:
                drop_event_df = pd.DataFrame(columns=price_history_df.columns)
                drop_event_df = drop_event_df.astype(price_history_df.dtypes)

            drop_event_df = pd.concat([drop_event_df, df], ignore_index=True)

        return drop_event_df
