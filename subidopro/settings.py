
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
    payload = client.access_secret_version(name=name, timeout=3600).payload.data.decode("UTF-8")

    env.read_env(io.StringIO(payload))
else:
    raise Exception("No local .env or GOOGLE_CLOUD_PROJECT detected. No secrets found.")

# if os.environ.get("GOOGLE_CLOUD_PROJECT", None):
#     project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
#     settings_name = os.environ.get("SETTINGS_NAME", "django_settings")
#     name = f"projects/{project_id}/secrets/{settings_name}/versions/latest"

#     client = secretmanager.SecretManagerServiceClient()

#     # Adicionando timeout na requisição
#     payload = client.access_secret_version(request={"name": name}, timeout=30).payload.data.decode("UTF-8")

#     env.read_env(io.StringIO(payload))



BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = env("SECRET_KEY")  

ALLOWED_HOSTS = ['*']

BASE_URL = env("BASE_URL", default="http://127.0.0.1:8000")


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    'api',
    'users',
    'subidometro',
    'alunos',
]
WSGI_APPLICATION = 'subidopro.wsgi.application'


MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

CORS_ALLOW_ALL_ORIGINS = True
CSRF_COOKIE_SAMESITE = "None"
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = "None"
SESSION_COOKIE_SECURE = True
CORS_ALLOW_CREDENTIALS = True
from corsheaders.defaults import default_headers

CORS_ALLOW_HEADERS = list(default_headers)
CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]  # Permitir todos os métodos HTTP



REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_COOKIE": "access_token",  # Nome do cookie para o access token
    "AUTH_COOKIE_REFRESH": "refresh_token",  # Nome do cookie para o refresh token
    "AUTH_COOKIE_HTTP_ONLY": True,
    "AUTH_COOKIE_SECURE": False,  # Mude para True se estiver usando HTTPS
    "AUTH_COOKIE_SAMESITE": "Lax",
}

# Configurações do Cookie
JWT_AUTH_COOKIE = "access_token"
JWT_AUTH_REFRESH_COOKIE = "refresh_token"
JWT_AUTH_SAMESITE = "Lax"  # Ajuste conforme necessário
JWT_AUTH_HTTPONLY = True  # Impede que o JavaScript acesse o token
JWT_AUTH_SECURE = False  # Troque para True em produção com HTTPS


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
            'NAME': "subidopro",
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
    CSRF_TRUSTED_ORIGINS = ["https://subidopro.uc.r.appspot.com", "http://localhost:3000", "https://localhost:3000"]
    CORS_ALLOWED_ORIGINS = ["https://subidopro.uc.r.appspot.com"]
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

    DEBUG = False
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': "subidopro",
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

# URL base para arquivos estáticos
STATIC_URL = '/static/'

# Diretório onde os arquivos estáticos serão coletados durante `collectstatic`
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # Use 'staticfiles' para a coleta

# Diretórios adicionais onde Django procura arquivos estáticos
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),  # Somente a pasta onde você coloca os arquivos estáticos
]


# Compressor de arquivos estáticos (se estiver usando o compressor)
# COMPRESS_ENABLED = True
# COMPRESS_ROOT = os.path.join(BASE_DIR, 'static')  # Diretório onde os arquivos comprimidos são salvos

# STATICFILES_FINDERS = [
#     'compressor.finders.CompressorFinder',  # Adiciona o CompressorFinder
# ]
# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
