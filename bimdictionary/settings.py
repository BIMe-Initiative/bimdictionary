import environ

root = environ.Path(__file__) - 2
env = environ.Env()
environ.Env.read_env()

SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG', default=False)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')

INSTALLED_APPS = [

    # Needs to be first to prevent jquery error in admin
    'dal',
    'dal_select2',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.flatpages',
    'django.contrib.postgres',

    'crispy_forms',
    'debug_toolbar',
    'django_countries',
    'django_extensions',
    'easy_thumbnails',
    'froala_editor',
    'markup_deprecated',
    'raven.contrib.django.raven_compat',
    'rest_framework',
    'storages',

    'core.apps.CoreConfig',
    'dictionary.apps.DictionaryConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

ROOT_URLCONF = 'bimdictionary.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'bimdictionary.wsgi.application'

DATABASES = {
    'default': env.db(),
}

CACHES = {
    'default': env.cache(),
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

AUTH_USER_MODEL = 'core.UserProfile'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LOGIN_REDIRECT_URL = 'index'

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',),
}

SITE_ID = 2

STATICFILES_STORAGE = env('STATICFILES_STORAGE')
STATICFILES_DIRS = [root('static')]
DEFAULT_FILE_STORAGE = env('DEFAULT_FILE_STORAGE')
AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID', default='xxx')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY', default='xxx')
AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME
AWS_PRELOAD_METADATA = True
STATIC_URL = env('STATIC_URL')
STATIC_ROOT = root('staticfiles')

EMAIL_CONFIG = env.email_url('EMAIL_URL', default='consolemail://')
vars().update(EMAIL_CONFIG)

FROALA_EDITOR_PLUGINS = [
    'align',
    'code_beautifier',
    'code_view',
    'image',
    'image_manager',
    'link',
    'lists',
    'quote',
    'table',
    'url',
]
FROALA_UPLOAD_PATH = 'uploads'
FROALA_EDITOR_OPTIONS = {'key': env('FROALA_KEY')}
INTERNAL_IPS = ['127.0.0.1']

RAVEN_CONFIG = {
    'dsn': env('RAVEN_DSN')
}

CRISPY_TEMPLATE_PACK = 'bootstrap4'

HTTPS = env('HTTPS', default=False)

