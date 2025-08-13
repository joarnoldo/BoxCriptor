import os

SECRET_KEY = os.environ.get('SECRET_KEY', '123456')
MONGO_URI = os.environ.get(
    'MONGO_URI',
    'mongodb://root:123456@localhost:27017/boxcriptorDB?authSource=admin'
)
