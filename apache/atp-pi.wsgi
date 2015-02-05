##############################################################################
#
# NAME:        atp_django.wsgi
#
# FACILITY:    SAM (Service Availability Monitoring)
#
# COPYRIGHT:
#         Copyright (c) 2009, Members of the EGEE Collaboration.
#         http://www.eu-egee.org/partners/
#         Licensed under the Apache License, Version 2.0.
#         http://www.apache.org/licenses/LICENSE-2.0
#         This software is provided "as is", without warranties
#         or conditions of any kind, either express or implied.
#
# DESCRIPTION:
#
#         ATP Django interfaces config file.
#
# AUTHORS:     Vibhuti Duggal, BARC
#
# CREATED:     6-Jul-2012
#
# NOTES:
#
# MODIFIED:
#
##############################################################################

import os,sys

#redirect stdout to std error
sys.stdout=sys.stderr
from distutils.sysconfig import get_python_lib

sys.path.append(get_python_lib())
sys.path.append(get_python_lib() + '/mywlcg-atp-api/')
os.environ['DJANGO_SETTINGS_MODULE'] = 'mywlcg-atp-api.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
