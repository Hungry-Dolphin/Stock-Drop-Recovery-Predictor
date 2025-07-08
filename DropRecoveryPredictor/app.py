from flask import Flask, render_template, request
from sqlalchemy.orm import sessionmaker
from models import Base, Stock
from sqlalchemy import create_engine
import os
from tests import test
from config import DevelopmentConfig, ProductionConfig
from sqlalchemy.orm import scoped_session
import datetime as datetime
from app.debugging_model import DebuggingModel

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

        @self.app.route('/predict', methods=['GET', 'POST'])
        def predict():
            ticker, latest = None, None
            if request.method == 'POST':
                ticker = request.form.get('ticker')
                print(f"Received ticker: {ticker}")
                latest = self.session.query(Stock).filter_by(ticker=str(ticker)).order_by(Stock.date.desc()).first()
                if latest:
                   if not latest.date == datetime.date.today():
                       print("The latest date is not today")
                       self.prediction_model.get_stock_data(str(ticker), "2020-01-01", datetime.date.today().strftime("%Y-%m-%d"))

                latest = latest.date if latest else None

            return render_template(
                'pages/prediction/predict.html',
                ticker=ticker,
                latest_update=latest)


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

