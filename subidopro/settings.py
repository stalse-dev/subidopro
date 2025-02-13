
from pathlib import Path
from datetime import timedelta
import os, io, environ
from google.cloud import secretmanager, storage
from google.oauth2 import service_account
from google.oauth2.service_account import Credentials

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(DEBUG=(bool, False))
env_file = os.path.join(BASE_DIR, ".env")
if os.path.isfile(env_file):
    # Use a local secret file, if provided

    env.read_env(env_file)
# [START_EXCLUDE]
elif os.getenv("TRAMPOLINE_CI", None):
    # Create local settings if running with CI, for unit testing

    placeholder = (
        f"SECRET_KEY=a\n"
        f"DATABASE_URL=sqlite://{os.path.join(BASE_DIR, 'db.sqlite3')}"
    )
    env.read_env(io.StringIO(placeholder))
# [END_EXCLUDE]
elif os.environ.get("GOOGLE_CLOUD_PROJECT", None):
    # Pull secrets from Secret Manager
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")

    client = secretmanager.SecretManagerServiceClient()
    settings_name = os.environ.get("SETTINGS_NAME", "django_settings")
    name = f"projects/{project_id}/secrets/{settings_name}/versions/latest"
    payload = client.access_secret_version(name=name).payload.data.decode("UTF-8")

    env.read_env(io.StringIO(payload))
else:
    raise Exception("No local .env or GOOGLE_CLOUD_PROJECT detected. No secrets found.")



BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = env("SECRET_KEY")  

ALLOWED_HOSTS = ['*']

BASE_URL = env("BASE_URL", default="http://127.0.0.1:8000")


# Application definition

INSTALLED_APPS = [
    #'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'api',
    'users',
    'subidometro',
    'alunos',
]
WSGI_APPLICATION = 'subidopro.wsgi.application'
#ASGI_APPLICATION = 'subidopro.asgi.application'
# CHANNEL_LAYERS = {
#     "default": {
#         "BACKEND": "channels.layers.InMemoryChannelLayer",
#     },
# }

# CHANNEL_LAYERS = {
#     "default": {
#         "BACKEND": "channels_redis.core.RedisChannelLayer",
#         "CONFIG": {
#             "hosts": [("10.0.0.3", 6379)],  # Substitua pelo IP interno do Cloud Memorystore
#         },
#     },
# }


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # Permitir acesso sem autenticação
    ]
}


USE_L10N = True

SECURE_REFERRER_POLICY = None

ROOT_URLCONF = 'subidopro.urls'

AUTHENTICATION_BACKENDS = (

    'django.contrib.auth.backends.ModelBackend', 
    'users.backends.UserBackend',
)

AUTH_USER_MODEL = 'users.User'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]




# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
if os.getenv("USE_CLOUD_SQL_AUTH_PROXY", None):
    DEBUG = True
    MSAL_REDIRECT_URI = "http://localhost:8000/callback"
    DATABASES = {
        
    }
    DATABASES = {   
        "default": {
            "ENGINE": "django.db.backends.postgresql_psycopg2",
            'NAME': "db-subidopro",
            'USER': env("db_user_pro"),
            'PASSWORD': env("db_password_pro"),
            "HOST": "127.0.0.1",
            "PORT": "5432",
        }   
    }
else:
    CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("redis://https://subidopro.uc.r.appspot.com/", 6379)],
        },
    },
}


    SECURE_SSL_REDIRECT = True
    CSRF_TRUSTED_ORIGINS = ["https://subidopro.uc.r.appspot.com"]
    CORS_ALLOWED_ORIGINS = ["https://subidopro.uc.r.appspot.com"]
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

    DEBUG = False
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': "db-subidopro",
            'USER': env("db_user_pro"),
            'PASSWORD': env("db_password_pro"),
            'HOST': '/cloudsql/{}'.format(env("db_instance_pro")),  # Defina corretamente a variável de ambiente
            'PORT': '5432',
        }
    }


AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'pt-br'

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

LOGIN_URL = 'login'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')  # Pasta exclusiva para saída do collectstatic

COMPRESS_ROOT = STATIC_ROOT

COMPRESS_ENABLED = True

STATICFILES_FINDERS = [
    'compressor.finders.CompressorFinder',
]

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),  # Pasta onde você mantém seus arquivos estáticos locais
]

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
