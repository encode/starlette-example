from starlette.config import Config
from starlette.datastructures import CommaSeparatedStrings


config = Config(env_file='.env')

ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=CommaSeparatedStrings, default="127.0.0.1,localhost")
DEBUG = config('DEBUG', cast=bool, default=False)
# DATABASE_URL = config('DATABASE_URL', cast=databases.DatabaseURL, default='sqlite:///db.sqlite')
# TEST_DATABASE_URL = DATABASE_URL.replace(name=f'test_{DATABASE_URL.name}')
# SECRET_KEY = config('SECRET_KEY', cast=Secret)
