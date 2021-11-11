from os import pardir, path
# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = path.dirname(path.dirname(path.abspath(path.join(__file__, pardir))))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '5iofLt=!Yl9q_6F$BQ0(8rITMVkzGw%sK#&WeZyx@)CXDR2*gd'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

INSTALLED_APPS = (
    'django_influxdb',
)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': path.join(BASE_DIR, 'db.sqlite3'),
    }
}

INFLUXDB_DEFAULT_BUCKET = "django_influxdb"
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "test"
INFLUXDB_ORG = "django_influxdb"

INSTALLED_APPS = [
    'django_influxdb',
]
