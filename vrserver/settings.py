"""
Django settings for vrserver project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '@s%koi@9h6kl=8_9afog!7w)e3$nrhh39gs#h+d92@vbste-sx'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'south',
    'djcelery',
    'kombu.transport.django',
    'sfmmanager',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    #'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'vrserver.urls'

WSGI_APPLICATION = 'vrserver.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

"""
#see django-pyodbc-azure documentation
#https://pypi.python.org/pypi/django-pyodbc-azure/1.0.7
DATABASES = {
    'default': {
        'ENGINE': 'sql_server.pyodbc',
        'NAME': 'uclvrcore_sql',
        'USER': 'uclvrcore',
        'PASSWORD': '%Qw[UCL]',
        'HOST': 'ht27bi0nul.database.windows.net',
        'PORT': '1433',

        'OPTIONS': {
            'driver': 'SQL Server Native Client 11.0',
            'MARS_Connection': True,
        },
    },
}
"""

# https-only cookies
#SESSION_COOKIE_SECURE = True

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/home/azureuser/static/'
STATIC_ROOT = '/home/azureuser/static/'
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "static"),
    '/home/azureuser/static/',
)
#custom settings

MEDIA_ROOT = os.path.join(BASE_DIR, 'uclvr_data')

#celery configuration
#CELERY_IMPORTS = ['vrserver.sfmmanager.tasks']
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
#CELERY_RESULT_SERIALIZER = 'json'
#CELERY_RESULT_BACKEND = 'database'
#CELERY_RESULT_DBURI = 'db.sqlite3'
BROKER_URL = 'django://'

