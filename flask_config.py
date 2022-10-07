import os
from flask import Config

class DevelopmentConfig(Config):
  ENV = 'development'
  DEBUG = True
  TESTING = True
  SERVER_NAME = 'localhost:12678'
  SECRET_KEY = os.getenv('FLASK_SECRET_KEY')


class ProductionConfig(Config):
  ENV = 'production'
  SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
  DEBUG = False
  TESTING = False