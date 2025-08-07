import os

SECRET_KEY = os.environ.get('SECRET_KEY', 'SECRET_KEY_BOXCRIPTOR')
MONGO_URI   = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/boxcriptor')
