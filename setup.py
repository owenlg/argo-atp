#!/usr/bin/env python

import os
del os.link

from distutils.core import setup
#import glob

setup(name = "argo-atp",
    version = "1.0.0",
    description = "ARGO Aggregated Topology Provider (ATP) database schema, synchronizer, django models and programmatic interface",
    author = "SAM Team",
    author_email = "tom-developers@cern.ch",
    url = "http://tomtools.cern.ch/confluence/display/SAMDOC",
    scripts = ['bin/atp_synchro', 'bin/check_atp_sync', 'bin/atp-createdb'],
    data_files = [
        ('/etc/atp', ['etc/atp_synchro.conf', 'etc/vo_feeds.conf', 'etc/roc.conf', 'etc/atp_db.conf', 'etc/atp_logging_files.conf', 'etc/atp_logging_parameters_config.conf', 'etc/atp_vo_feeds_schema.xsd']),
        ('/etc/cron.d/', ['cron/atp-sync']),
        ('/etc/logrotate.d', ['atp.logrotate']),
        ('/etc/atp_django', ['mywlcg-atp/config/atp.ini.example', 'mywlcg-atp/config/requires.txt']),
        ('/etc/init.d', ['etc/atp-sync']),
        ('/etc/httpd/conf.d', ['apache/xatp-pi.conf']),
        ('/usr/share/atp', ['mywlcg-atp-api/manage']),
        ('/usr/share/atp/apache', ['apache/atp-pi.wsgi']),
    ],
    package_dir = {'atp_synchronizer': 'atp_synchronizer', 'atp': 'mywlcg-atp/atp'},
    packages = ['atp_synchronizer', 'atp', 'atp.orm', 'mywlcg-atp-api'],
    package_data = {'mywlcg-atp-api': ['templates/*', 'templatetags/*']},
#   package_data = {'atp.orm' : ['templates/atp/*.html', 'templates/*.html']},
    long_description = """ARGO Aggregated Topology Provider (ATP) database schema, synchronizer, django models and programmatic interface"""
)


