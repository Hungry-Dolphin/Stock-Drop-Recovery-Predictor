from flask import Flask, render_template, request
from sqlalchemy.orm import sessionmaker
from models import Base, Stock
from sqlalchemy import create_engine
import os
from tests import test
from config import DevelopmentConfig, ProductionConfig
from sqlalchemy.orm import scoped_session
import datetime as datetime
from predictors.debugging_model import DebuggingModel
from pandas.tseries.offsets import BDay
from datetime import timedelta
from sqlalchemy import func

class FlaskApp:
    def __init__(self, config_dir:str = 'config.cfg'):
        self.app = Flask(__name__)
        env = os.getenv('FLASK_ENV', 'development').lower()

        if env == 'production':
            self.app.config.from_object(ProductionConfig())
        else:
            self.app.config.from_object(DevelopmentConfig(config_dir=config_dir))
            # Register test blueprint only when not in production
            self.app.register_blueprint(test)

        # SQLAlchemy setup
        self.engine = create_engine(self.app.config["SQLALCHEMY_DATABASE_URI"], echo=True)
        self.session = scoped_session(sessionmaker(bind=self.engine))

        # init model
        self.prediction_model = DebuggingModel(self.app.config["SQLALCHEMY_DATABASE_URI"])
        self.prediction_model.update_model()

        # Set session within the app so it can be used in blueprints
        self.app.db_session = self.session
        self.app.engine = self.engine

        self.set_database()
        self.register_routes()
        self.register_error_handlers()


    def set_database(self):

        # Create tables
        with self.engine.begin() as connection:
            # Base.metadata.drop_all(connection)  # Drops all tables defined in Base
            Base.metadata.create_all(connection)

    def register_routes(self):
        @self.app.route('/')
        def home():
            return render_template('pages/landing_page.html')

        @self.app.route('/update_model')
        def update_model():
            self.prediction_model.update_model()
            return render_template('pages/landing_page.html')

        @self.app.route('/latest_data')
        def latest_data():
            results = self.session.query(
                Stock.ticker,
                func.max(Stock.date).label('most_recent_data')
            ).group_by(Stock.ticker).all()
            return render_template('pages/general/stock_data.html', results=results)

        @self.app.route('/predict', methods=['GET', 'POST'])
        def predict():
            if request.method != 'POST':
                return render_template('pages/prediction/predict.html')

            ticker = request.form.get('ticker')
            if not ticker:
                print("No ticker provided.")
                return render_template('pages/prediction/predict.html')

            ticker = str(ticker).upper()
            print(f"Received ticker: {ticker}")

            latest_stock = (
                self.session.query(Stock)
                .filter_by(ticker=ticker)
                .order_by(Stock.date.desc())
                .first()
            )
            latest_b_day = datetime.date.today() - BDay(1)
            latest_stock_date = latest_stock.date if latest_stock else None

            if latest_stock:
                #TODO alert the user if new data needed to be fetched

                # We could see if the dates are equal but since we sometimes upload testing data this is more robust
                if latest_stock.date < latest_b_day:
                    print("The latest stock date is not the last business day")
                    stock_data = self.prediction_model.get_stock_data(
                        str(ticker),
                        latest_stock.date.strftime("%Y-%m-%d"),
                        (latest_b_day + timedelta(days=1)).strftime("%Y-%m-%d")
                    )
                    # TODO find out if we just dont have the stock or if its random input
                    drop = self.prediction_model.detect_and_predict_drop(stock_data, ticker)
                    if not drop.empty:
                        return render_template(
                            'pages/prediction/predict.html',
                            ticker=ticker,
                            latest_update=latest_stock_date,
                            drop=drop
                        )

            else:
                print(f"No stock data found for ticker: {ticker}")
                latest_stock_date = None

            return render_template(
                'pages/prediction/predict.html',
                ticker=ticker,
                latest_update=latest_stock_date
            )




    def register_error_handlers(self):
        @self.app.errorhandler(500)
        def internal_error(error):
            #db_session.rollback()
            return render_template('errors/500.html'), 500

        @self.app.errorhandler(404)
        def not_found_error(error):
            return render_template('errors/404.html'), 404

    def run(self, **kwargs):
        self.app.run(**kwargs)


if __name__ == '__main__':
    stock_app = FlaskApp()
    stock_app.run(host='0.0.0.0', debug=False)

