from flask import Flask, render_template, request
from sqlalchemy.orm import sessionmaker
from models import Base, Stock
from sqlalchemy import create_engine
import os
from config import DevelopmentConfig, ProductionConfig

app = Flask(__name__)

if os.getenv('FLASK_ENV', 'default') == 'production':
    app.config.from_object(ProductionConfig)
else:
    app.config.from_object(DevelopmentConfig())

# SQLAlchemy setup
engine = create_engine(app.config["SQLALCHEMY_DATABASE_URI"], echo=True)
Session = sessionmaker(bind=engine)

# Create tables
with engine.begin() as connection:
    # Base.metadata.drop_all(connection)  # Drops all tables defined in Base
    Base.metadata.create_all(connection)

@app.route('/')
def home():
    return render_template('pages/landing_page.html')

@app.route('/first_stock')
def first_stock():
    # Create a new session
    session = Session()
    first_hit = session.query(Stock).first()
    return f"It works! {first_hit.ticker} <br> {first_hit.high}"


@app.errorhandler(500)
def internal_error(error):
    #db_session.rollback()
    return render_template('errors/500.html'), 500


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False)

