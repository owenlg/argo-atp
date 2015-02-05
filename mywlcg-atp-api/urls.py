from django.conf.urls.defaults import *

urlpatterns = patterns('mywlcg-atp-api.views',
    (r'^contacts/$', 'contacts'),
    (r'^groupcontacts/$', 'groupcontacts'),
    (r'^sitecontacts/$', 'sitecontacts'),
    (r'^vocontacts/$', 'vocontacts'),
    (r'^servicemap/$', 'servicemap'),
    (r'^site/$', 'site'),
    (r'^siteregionvo/$', 'siteregionvo'),
    (r'^vofeeds/$', 'vofeeds'),
    (r'^search/contacts/json$', 'contacts'),
    (r'^search/contactgroup/json$', 'groupcontacts'),
    (r'^search/contactsite/json$', 'sitecontacts'),
    (r'^search/contactvo/json$', 'vocontacts'),
    (r'^search/servicemap/json$', 'servicemap'),
    (r'^search/site/json$', 'site'),
    (r'^search/siteregionvo/json$', 'siteregionvo'),
    (r'^search/vofeeds/json$', 'vofeeds'),
)