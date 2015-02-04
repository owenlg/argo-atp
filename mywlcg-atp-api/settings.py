##############################################################################
#
# NAME:		   settings.py
#
# FACILITY:	   SAM (Service Availability Monitoring)
#
# COPYRIGHT:
#		  Copyright (c) 2009, Members of the EGEE Collaboration.
#	http://www.eu-egee.org/partners/
#		  Licensed under the Apache License, Version 2.0.
#		  http://www.apache.org/licenses/LICENSE-2.0
#		  This software is provided "as is", without warranties
#		  or conditions of any kind, either express or implied.
#
# DESCRIPTION:
#
#
#
# AUTHORS:	   Vibhuti Duggal, BARC
#
# CREATED:	   6-Jul-2012
#
# NOTES:
#
# MODIFIED:
#
##############################################################################

import os
from ConfigParser import RawConfigParser, NoSectionError
from django.core.exceptions import ImproperlyConfigured
# Django settings for app project.

PROJECT_NAME = 'atp'

# Set up some useful paths for later
from os import path as os_path

APP_PATH = os_path.abspath(os_path.split(__file__)[0])

PROJECT_PATH = os_path.abspath(os_path.join(APP_PATH,'..','..'))

CACHE_BACKEND ="locmem:///?timeout=30&max_entries=400"
CACHE_MIDDLEWARE_SECONDS = 5
CACHE_MIDDLEWARE_KEY_PREFIX =''

config = RawConfigParser()
config_file=os_path.join(PROJECT_PATH, 'config', '%s.ini'%PROJECT_NAME)
read_files = config.read(['/etc/atp_django/atp.ini',config_file])

if not read_files:
    raise ImproperlyConfigured("Could not read config file : %s"%config_file)

try:
    DEBUG = config.getboolean('debug','DEBUG')
    TEMPLATE_DEBUG = config.getboolean('debug','TEMPLATE_DEBUG')

    PREFIX = config.get('server', 'PREFIX')

    VIEW_TEST = config.getboolean('debug', 'VIEW_TEST')
    INTERNAL_IPS = tuple(config.get('debug', 'INTERNAL_IPS').split())

    SERVER_EMAIL = config.get('email', 'SERVER_EMAIL')
    EMAIL_HOST = config.get('email', 'EMAIL_HOST')
    ADMINS = tuple(config.items('error mail'))
    MANAGERS = tuple(config.items('404 mail'))

    DATABASES = {
                        'default': {
                                    'NAME': config.get('database', 'DATABASE_NAME'),
                                    'ENGINE': 'django.db.backends.' + config.get('database', 'DATABASE_ENGINE'),
                                    'USER': config.get('database', 'DATABASE_USER'),
                                    'PASSWORD': config.get('database', 'DATABASE_PASSWORD'),
                                    'HOST': config.get('database', 'DATABASE_HOST'),
                                    'PORT': config.get('database', 'DATABASE_PORT')
                                }
               }

    # Make these unique, and don't share it with anybody.
    SECRET_KEY = config.get('secrets','SECRET_KEY')
    # set time zone
    TIME_ZONE = config.get('timezone','TIME_ZONE')
except NoSectionError, e:
    raise ImproperlyConfigured(e)
    
#
# Set DB to use INNODB
#
if DATABASES['default']['NAME'].lower()=='mysql':
    DATABASE['default']['OPTIONS'] = {"init_command": "SET storage_engine=INNODB"}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
#TIME_ZONE = 'America/Chicago'
# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".

#Fixtures directory
FIXTURE_DIRS = (os.path.join(APP_PATH, 'fixtures'))

#TEST RUNNER
TEST_RUNNER = ('atp.tests.test_coverage.run_tests')

# no prefix for debug environment
if DEBUG==True:
    PREFIX=''

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#	  'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
    'pagination.middleware.PaginationMiddleware',
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',

)
TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
)

ROOT_URLCONF = 'mywlcg-atp-api.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os_path.join(PROJECT_PATH, 'templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'mywlcg-atp-api'
)
# Add in manage.py extensions, if it's there
try:
    import django_extensions
    INSTALLED_APPS += ('django_extensions',)
except ImportError:
    pass

