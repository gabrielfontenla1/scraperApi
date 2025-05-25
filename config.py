import os

class Config:
    DEBUG = False
    TESTING = False
    HOST = '0.0.0.0'
    PORT = int(os.environ.get('PORT', 5001))
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*')

class ProductionConfig(Config):
    ENV = 'production'

class DevelopmentConfig(Config):
    ENV = 'development'
    DEBUG = True

class TestingConfig(Config):
    TESTING = True 