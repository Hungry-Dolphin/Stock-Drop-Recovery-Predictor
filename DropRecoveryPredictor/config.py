import os
from configparser import ConfigParser

class Config:
    SQLALCHEMY_DATABASE_URI = None
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    def __init__(self, config_dir):
        super().__init__()
        config = ConfigParser()
        config.read(config_dir)
        if 'default' in config:
            self.SQLALCHEMY_DATABASE_URI = config['default'].get('SQLALCHEMY_DATABASE_URI', self.SQLALCHEMY_DATABASE_URI)

class ProductionConfig(Config):
    def __init__(self):
        super().__init__()
        self.SQLALCHEMY_DATABASE_URI = os.environ.get(
            'SQLALCHEMY_DATABASE_URI', self.SQLALCHEMY_DATABASE_URI
        )
