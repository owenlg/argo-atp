import string
from string import lower
import time, calendar
from datetime import datetime,date,timedelta
from operator import itemgetter, setitem
from itertools import groupby

from django.db import connection, DatabaseError
from django.db.models import Count, Max
from django.db.models.query_utils import Q
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseBadRequest, Http404, HttpResponseNotFound
from django.views.decorators.cache import cache_page
from atp.orm.models import *

# Contacts
# {code}/atp/contacts?[name]&[dn]&[email]&[output]{code}
# ** Optional
# *** *name:* contact name
# *** *dn:* contact certifcate dn
# *** *email:* contact email address
# *** *output:* output format; possible values are: xml, json; default: json

@cache_page(60)
def contacts(request):
    # Params
    name = request.GET.get("name") or 0
    dn = request.GET.get("dn") or 0
    email = request.GET.get("email") or 0
    output = lower(request.GET.get("output") or "json")
    # Body
    values = {}
    qset = Q()
    if name:
	qset = Q(name__icontains=name)
    if dn:
	qset = qset & Q(dn__iexact=dn)
    if email:
	qset = qset & Q(email__icontains=email)

    values["contacts"] = Contact.objects.filter(qset).order_by('name')\
				.values_list('name','telephone','dn','email')
    # Output
    if output == "xml":
        return render_to_response('ws_contacts_xml',values,mimetype = 'application/xml',)
    else:
        return render_to_response('ws_contacts_json',values,mimetype = 'application/json',)


# Group Contacts
# {code}/atp/groupcontacts?[name]&[dn]&[email]&[groupname]&[role]&[output]{code}
# ** Optional
# *** *name:* contact name
# *** *dn:* contact certifcate dn
# *** *email:* contact email address
# *** *groupname:* region to which the contact belongs (e.g. NGI_IT)
# *** *role:* contact role
# *** *output:* output format; possible values are: xml, json; default: json

@cache_page(60)
def groupcontacts(request):
    # Params
    name = request.GET.get("name") or 0
    groupname = request.GET.get("groupname") or 0
    dn = request.GET.get("dn") or 0
    role = request.GET.get("role") or 0
    email = request.GET.get("email") or 0
    output = lower(request.GET.get("output") or "json")
    # Body
    values = {}
    qset = Q()
    if name:
	qset = Q(contact__name__icontains=name)
    if dn:
	qset = qset & Q(contact__dn__iexact=dn)
    if email:
	qset = qset & Q(contact__email__icontains=email)
    if groupname:
	qset = qset & Q(groups__groupname__iexact=groupname)
    if role:
	qset = qset & Q(role__icontains=role)
    values["contacts"] = ContactGroup.objects.filter(qset).order_by('contact__name')\
				.values_list('contact__name','contact__dn',
						'contact__telephone','contact__email',
						'groups__groupname','role')
    values["field"] = "group"
    # Output
    if output == "xml":
        return render_to_response('ws_contacts_xml',values,mimetype = 'application/xml',)
    else:
        return render_to_response('ws_contacts_json',values,mimetype = 'application/json',)


# Site Contacts
# {code}/atp/sitecontacts?[name]&[dn]&[email]&[sitename]&[role]&[output]{code}
# ** Optional
# *** *name:* contact name
# *** *dn:* contact certifcate dn
# *** *email:* contact email address
# *** *sitename:* site to which the contact belongs (e.g. CERN-PROD)
# *** *role:* contact role
# *** *output:* output format; possible values are: xml, json; default: json

@cache_page(60)
def sitecontacts(request):
    # Params
    name = request.GET.get("name") or 0
    sitename = request.GET.get("sitename") or 0
    dn = request.GET.get("dn") or 0
    role = request.GET.get("role") or 0
    email = request.GET.get("email") or 0
    output = lower(request.GET.get("output") or "json")
    # Body
    values = {}
    qset = Q()
    if name:
	qset = Q(contact__name__icontains=name)
    if dn:
	qset = qset & Q(contact__dn__iexact=dn)
    if email:
	qset = qset & Q(contact__email__icontains=email)
    if sitename:
	qset = qset & Q(site__sitename__iexact=sitename)
    if role:
	qset = qset & Q(role__icontains=role)
    values["contacts"] = ContactSite.objects.filter(qset).order_by('contact__name')\
				.values_list('contact__name','contact__dn',
						'contact__telephone','contact__email',
						'site__sitename','role')
    values["field"] = "site"
    # Output
    if output == "xml":
        return render_to_response('ws_contacts_xml',values,mimetype = 'application/xml',)
    else:
        return render_to_response('ws_contacts_json',values,mimetype = 'application/json',)


# VO Contacts
# {code}/atp/vocontacts?[name]&[dn]&[email]&[voname]&[role]&[output]{code}
# ** Optional
# *** *name:* contact name
# *** *dn:* contact certifcate dn
# *** *email:* contact email address
# *** *voname:* vo to which the contact belongs (e.g. atlas)
# *** *role:* contact role
# *** *output:* output format; possible values are: xml, json; default: json

@cache_page(60)
def vocontacts(request):
    # Params
    name = request.GET.get("name") or 0
    voname = request.GET.get("voname") or 0
    dn = request.GET.get("dn") or 0
    role = request.GET.get("role") or 0
    email = request.GET.get("email") or 0
    output = lower(request.GET.get("output") or "json")
    # Body
    values = {}
    qset = Q()
    if name:
	qset = Q(contact__name__icontains=name)
    if dn:
	qset = qset & Q(contact__dn__iexact=dn)
    if email:
	qset = qset & Q(contact__email__icontains=email)
    if voname:
	qset = qset & Q(vo__voname__iexact=voname)
    if role:
	qset = qset & Q(role__icontains=role)
    values["contacts"] = ContactVo.objects.filter(qset).order_by('contact__name')\
				.values_list('contact__name','contact__dn',
						'contact__telephone','contact__email',
						'vo__voname')
    values["field"] = "vo"
    # Output
    if output == "xml":
        return render_to_response('ws_contacts_xml',values,mimetype = 'application/xml',)
    else:
        return render_to_response('ws_contacts_json',values,mimetype = 'application/json',)


# Service
# {code}/atp/servicemap?[site]&[flavourname]&[voname]&[hostname]&[serviceendpoint]&[ismonitored]&[isinproduction]&[output]{code}
# ** Optional
# *** *site:* name of the site (e.g. CERN-PROD)
# *** *flavourname:* service flavour name (e.g. CREAM-CE)
# *** *voname:* vo name (e.g. ops)
# *** *hostname:* hostname
# *** *serviceendpoint:* service endpoint
# *** *ismonitored:* if the service is monitored; possible values are: 'Y' or 'N'
# *** *isinproduction:* if the service is in production; possible values are: 'Y' or 'N'
# *** *output:* output format; possible values are: xml, json; default: json

@cache_page(60)
def servicemap(request):
    # Params
    output = lower(request.GET.get("output") or "json")
    flavourname = request.GET.get("flavourname") or 0
    sitename = request.GET.get("site") or 0
    voname = request.GET.get("voname") or 0
    ismonitored = request.GET.get("ismonitored") or 0
    isinproduction = request.GET.get("isinproduction") or 0
    hostname = request.GET.get("hostname") or 0
    serviceendpoint = request.GET.get("serviceendpoint") or 0
    # Body
    filters = {'isdeleted': 'N'}
    
    if flavourname:
        filters['flavour__flavourname'] = flavourname
    if serviceendpoint:
        filters['serviceendpoint'] = serviceendpoint
    if sitename:
        filters['site__sitename'] = sitename
    if voname:
        filters['vo__voname'] = voname
    if hostname:
        filters['hostname'] = hostname

    on_yes = {'on': 'Y', 'off': 'N'}
    if ismonitored:
        filters['ismonitored'] = on_yes.get(ismonitored, ismonitored)
    if isinproduction:
        filters['isinproduction'] = on_yes.get(isinproduction, isinproduction)

    ser = Service.objects.filter(**filters).select_related()
    context = {
        'services': ser.order_by('hostname')
    }
    if output == "xml":
        return render_to_response('ws_servicemap_xml', context, mimetype='application/xml')
    return render_to_response('ws_servicemap_json', context, mimetype='application/json')


# Sites
# {code}/atp/site?[sitename]&[siteoffname]&[countryname]&[infrastructure]&[infrasttype]&[ismonitored]&[output]{code}
# ** Optional
# *** *sitename:* name of the site (e.g. CERN-PROD)
# *** *siteoffname:* official name of the site
# *** *countryname:* name of the country (e.g SWITZERLAND)
# *** *infrastructure:* name of the infrastructure (e.g. EGI)
# *** *infrasttype:*
# *** *ismonitored:* if the service is monitored; possible values are: 'Y' or 'N'
# *** *output:* output format; possible values are: xml, json; default: json

@cache_page(60)
def site(request):
    # Params
    output = lower(request.GET.get("output") or "json")
    countryname = request.GET.get("countryname") or 0
    sitename = request.GET.get("sitename") or 0
    siteoffname = request.GET.get("siteoffname") or 0
    ismonitored = request.GET.get("ismonitored") or 0
    infrastructure = request.GET.get("infrastructure") or 0
    infrasttype = request.GET.get("infrasttype") or 0
    # Body
    values={'sites':[]}
    qset = Q(isdeleted__iexact='N')
    if infrastructure:
        qset = qset & Q(infrast__infrastname__icontains=infrastructure)
    if sitename: 
        qset = qset & Q(sitename__iexact=sitename)
    if countryname: 
        qset = qset & Q(country__countryname__icontains=countryname)
    if siteoffname:
        qset = qset & Q(siteoffname__icontains=siteoffname)
    if ismonitored:
        if ismonitored == "on":
            ismonitored = "Y"    
        qset = qset & Q(ismonitored__iexact=str(ismonitored))
    if infrasttype:
        qset = qset & Q(infrasttype__icontains=infrasttype)
    values['sites'] = Site.objects.filter(qset).order_by('sitename')\
                        .values_list('sitename','sitedesc', 
                                        'infrast__infrastname','country__countryname',
                                        'giisurl', 'latitude','longitude','certifstatus',
                                        'infrasttype','contactemail','contacttel',
                                        'ismonitored')
    # Output
    if output == "xml":
        return render_to_response('ws_sites_xml',values,mimetype = 'application/xml',)
    else:
        return render_to_response('ws_sites_json',values,mimetype = 'application/json',)


# Sites in Region
# {code}/atp/siteregionvo/?[site]&[region]&[output]{code}
# ** Optional
# *** *site:* name of the site (e.g. CERN-PROD)
# *** *region:* name of the region (e.g NGI_IT)
# *** *output:* output format; possible values are: xml, json; default: json

@cache_page(60)
def siteregionvo(request):
    # Params
    output = lower(request.GET.get("output") or "json")
    region = request.GET.get("region") or 0
    sitename = request.GET.get("site") or 0
    certifstatus = request.GET.get("certifstatus") or 0
    # Body
    values={'sites':[]}
    qset = Q(groups__group_type__typename__icontains="Region",isdeleted__iexact='N',site__isdeleted__iexact='N')
    if sitename:
        qset = qset & Q(site__sitename__icontains=sitename)
    if region:
	    qset = qset & Q(groups__groupname__iexact=region)
    if certifstatus:
	    qset = qset & Q(site__certifstatus__iexact=certifstatus)

    siteregion_obj=SiteGroup.objects.filter(qset)
    siteregionvo_list=[]
    for item in siteregion_obj:
            # site-region object
            service_obj= Service.objects.filter(site__sitename__iexact=item.site).order_by('site')
            if service_obj:
                region_dict=['']*4
                for service_item in service_obj:
                    volist=[]
                    for vo_item in service_item.vo.all():
                        if vo_item.voname not in volist:
                            volist.append(vo_item.voname)
                region_dict[2]=str(item.site.infrast)
                region_dict[0]=str(item.site)
                region_dict[1]=str(item.groups)
                region_dict[3]=volist
                siteregionvo_list.append(region_dict)
    values['sites'] = siteregionvo_list 
    # Output
    if output == "xml":
        return render_to_response('ws_siteregionvo_xml',values,mimetype = 'application/xml',)
    else:
        return render_to_response('ws_siteregionvo_json',values,mimetype = 'application/json',)        
        
        
# VO Feeds
# {code}/atp/vofeeds?[sitename]&[hostname]&[flavourname]&[voname]&[vogroups]&[vogrouptype]&[ismonitored]&[isinproduction]&[output]{code}
# ** Optional
# *** *sitename:* name of the site (e.g. CERN-PROD)
# *** *hostname:* hostname
# *** *flavourname:* service flavour name (e.g. CREAM-CE)
# *** *voname:* vo name (e.g. ops)
# *** *vogroups:* group name for given vo (e.g. T0-CERN)
# *** *vogrouptype:* group type for given vo (e.g. Tier-1)
# *** *ismonitored:* if the service is monitored; possible values are: 'Y' or 'N'
# *** *isinproduction:* if the service is in production; possible values are: 'Y' or 'N'
# *** *output:* output format; possible values are: xml, json; default: json

@cache_page(60)
def vofeeds(request):
    output = lower(request.GET.get("output", "json"))
    voname = request.GET.get("vo")
    sitename = request.GET.get("atp_site")
    flavourname = request.GET.get("flavourname")
    hostname = request.GET.get("hostname")
    vogrouptype = request.GET.get("vogrouptype")
    vogroups = request.GET.get("vogroups")
    ismonitored = request.GET.get("ismonitored")
    isinproduction = request.GET.get("isinproduction")

    filters = {'isdeleted': 'N'}
    if voname:
        filters['vo__voname'] = voname
    if sitename:
        filters['service__site__sitename'] = sitename
    if flavourname:
        filters['service__flavour__flavourname'] = flavourname
    if hostname:
        filters['service__hostname'] = hostname

    if vogrouptype:
        filters['groups__group_type__typename'] = vogrouptype
    if vogroups:
        filters['groups__groupname'] = vogroups

    on_yes = {'on': 'Y', 'off': 'N'}
    if ismonitored:
        filters['service__ismonitored'] = on_yes.get(ismonitored, ismonitored)
    if isinproduction:
        filters['service__isinproduction'] = on_yes.get(isinproduction, isinproduction)

    vsg = VoServiceGroup.objects.filter(**filters).select_related()
    context = {
        'service_groups': vsg.order_by('service__site__sitename')
    }

    if output == "xml":
        return render_to_response('ws_vofeeds_xml', context, mimetype='application/xml')
    return render_to_response('ws_vofeeds_json', context, mimetype='application/json')
