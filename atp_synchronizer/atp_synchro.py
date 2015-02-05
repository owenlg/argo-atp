#!/usr/bin/python

# ################################################### 
#
# NAME:        atp_synchro
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
#         This application synchronizes the ATP database with information
#         from different topology providers
#
# AUTHORS:     David Collados, CERN
#              Joshi Pradyumna, BARC
#              Pedro Andrade, CERN
#
# CREATED:     23-Nov-2009
#
# NOTES:
#
# MODIFIED:    26-August-2011
#
# #####################################################
import copy
import simplejson
import string
import sys
import urllib
import httplib
import urllib2
import xml.dom.minidom
import yaml
import time,datetime,calendar
import uuid
import os
import stomp
from atp_synchronizer import config
from atp_synchronizer import input
from atp_synchronizer import output
from atp_synchronizer import message_listener
from lxml import etree
import ConfigParser

if sys.version_info[:2] >= (2, 6):
    from xml.etree import ElementTree as ET # for python 2.6 or more 
else:
    from elementtree import ElementTree as ET


# -------
# Process
# -------

def stopExecution(config):
    "Stops the execution of ATP sychronizer due to an error"
    if string.lower(config.database_type)=="mysql":
        config.setAction("Disconnecting from ATP MySQL database")
    else:
        config.setAction("Disconnecting from ATP Oracle database")
    cursor.close()
    conn.close()
    sys.exit(1)


# ------
# Common
# ------

def __confGet(conf, section):
    "Returns the value of the configuration option."
    try:
        return conf.items(section)
    except ConfigParser.Error:
        return None # ignore missing values


def getDataFromXML(url):
    "Extracts XML data from an URL feed."
    output_data = None
    try:
        output_data = urllib2.urlopen(url).read()
    except Exception, e:
        output_data = None
    return output_data


def getDataFromXMLX509(url, u_key_file, u_cert_file, header = {'Python-urllib': ''}):
    "Extracts XML data from an URL feed using X509 certificates."
    class HTTPSClientAuthConnection(httplib.HTTPSConnection):
        def __init__(self, host, timeout=None):
            httplib.HTTPSConnection.__init__(self, host, key_file=u_key_file,cert_file=u_cert_file)
    class HTTPSClientAuthHandler(urllib2.HTTPSHandler):
        def https_open(self, req):
            return self.do_open(HTTPSClientAuthConnection, req)

    output_data = None
    try:
        opener = urllib2.build_opener(urllib2.HTTPHandler(),HTTPSClientAuthHandler())
        req = urllib2.Request(url, None, header)
        output_data = opener.open(req).read()
    except Exception, e:
        output_data = None
    return output_data


def getDataFromJSonFeed(url):
    "Extracts JSON data from an URL feed."
    json_results = None
    try:
        result = urllib2.urlopen(url).read()
        json_results = simplejson.loads(result)
    except Exception, e:
        json_results = None
    return json_results


# ----------------
# CIC Synchronizer
# ----------------

def parseVOs(vo_xml):
    "Parses VO list provided by CIC portal"
    Root = ET.XML(vo_xml)
    idcards = Root.findall("IDCard")
    if len(idcards) > 0:
        vos = []            
        for vo_element in idcards:
            dict_vo_element = dict(vo_element.items())
            if dict_vo_element.has_key('Name')==False or dict_vo_element.has_key('Status')==False:
                config.logger.info("CIC - Validation - vo card does not contain 'Name' and 'Status' attributes for %s" % vo_element)
            else:
                if dict_vo_element['Status'].lower()=='production' and dict_vo_element['Name']!='':
                    vos.append(dict_vo_element['Name'])
        return vos
    else:
        config.logger.error("CIC - Validation - Exiting synchronizer due to invalid VO card")
        config.logger_syslog.error("CIC - Validation - Exiting synchronizer due to invalid VO card")        
        return None
            
def parseVOMS(XML_Element_Feed):
    "Parses users information from VOM server list"
    Voms_List = None
    try:
        Vomses = []
        for voname, voms in XML_Element_Feed.items():
            Root = ET.XML(voms)
            Voms = []
            Voms.append(voname)
            Contacts_List = []
            for element in Root.findall("*/multiRef"):
                Contacts_Dic = {}
                for subelement in element.getchildren():
                    if subelement.text:
                        Contacts_Dic[string.lower(subelement.tag)] = (subelement.text)
                Contacts_List.append(Contacts_Dic)
                Voms.append(Contacts_List)
            if Contacts_List:
                Vomses.append(Voms)
    except Exception, e:
        config.logger.error("CIC - Execution - Error parsing voms contacts")
        config.logger_syslog.error("CIC - Execution - Error parsing voms contacts")
    return Vomses
        
def validateCICPortalVO(config):
    "Validates the availability of VO information from CIC portal"
    vo_xml = getDataFromXML(config.cic_portal_vo_url)
    if vo_xml:
        config.logger.info("CIC - Validation - Parsing vo cards")    
        vos = parseVOs(vo_xml)
        config.logger.info("CIC - Validation - VO cards retreived and parsed correctly")    
        return vos      
    else:
        config.logger.error("CIC - Validation - Exiting synchonizer due to unavailable feed: %s" % config.cic_portal_vo_url)
        config.logger_syslog.error("CIC - Validation - Exiting synchonizer due to unavailable feed: %s" % config.cic_portal_vo_url)        
        return None

def validateVOMS(config):
    "Validates the availability of users information from VOMS"
    voms_list = {}
    for voname,server in config.voms_servers.items():
        voms_xml = getDataFromXMLX509(server, config.x509_user_key, config.x509_user_cert, {'X-VOMS-CSRF-GUARD': ''}) 
        if voms_xml:
            voms_list[voname]=voms_xml
        else:
            config.logger.warning("CIC - Validation - VOMS users could not be retreived for vo %s" % voname)    
    if voms_list:        
        config.logger.info("CIC - Validation - VOMS users retreived correctly")    
        return voms_list      
    else:
        config.logger.error("CIC - Validation - Exiting synchonizer due to unavailable feed: %s" % config.voms_servers.items())
        config.logger_syslog.error("CIC - Validation - Exiting synchonizer due to unavailable feed: %s" % config.voms_servers.items())        
        return None

def synchroCICPortalVO(config, vos, voms, conn, dbInput, dbOutput):
    "Synchronizes the all VO related inforamtion into the DB"
    try:
        exec_time = datetime.datetime.now()
        config.setAction("CIC - Execution - Updating VO cards")
        dbOutput.updateVOs(vos, dbInput)

        config.setAction("CIC - Execution - Parsing VOMS contacts")
        voms_users = parseVOMS(voms)
        config.setAction("CIC - Execution - Inserting VOMS contacts")
        dbOutput.updateVOMSContacts(voms_users, dbInput)

        config.setAction("CIC - Execution - Updating last run time")
        dbOutput.updateSynchronizerlastrun(config.cic_portal_data_provider, dbOutput.cic_synchro_status, exec_time)
        if config.db_commit:
            config.setAction("CIC - Execution - Commiting changes")
            conn.commit()

    except Exception, e:
        config.logger.error("%s - Error - %s" % (config.getAction(), str(e).strip()))
        config.logger_syslog.error("%s - Error - %s" % (config.getAction(), str(e).strip()))
        conn.rollback()


# ---------------------------
# GOCDB Topology Synchronizer
# ---------------------------

def parseElementFeed(config, XML_Element_Feed):
    "Parses sites list from GOCDB"
    Feed_List = None
    try:
        Root = ET.XML(XML_Element_Feed)
        Root_Iter = Root.getiterator()
        Feed_List = []
        for element in Root_Iter:
            Element_List = {}
            if element.keys():
                for name, value in element.items():
                    #print "\t\tName: '%s', Value: '%s'"%(name, value)
                    Element_List[string.lower(name)] = value
                    if element.getchildren():
                        for child in element:
                            Element_List[string.lower(child.tag)] = (child.text)
                Feed_List.append(Element_List)
    except Exception, e:
        config.logger.error("GOCDB Topology - Execution - Error parsing feed ")
        config.logger_syslog.error("GOCDB Topology - Execution - Error parsing feed")
    return Feed_List

def parseServiceEndpoints(config, XML_Element_Feed):
    "Parses services list from GOCDB"
    Feed_List = None
    try:
        Root = ET.XML(XML_Element_Feed)
        Feed_List = []
        for element in Root.findall("SERVICE_ENDPOINT"):
            Element_List = {}
            if element.getchildren():
                for child_element in element.getchildren():
                    Element_List[string.lower(child_element.tag)] = (child_element.text)
            Feed_List.append(Element_List)
    except Exception, e:
        config.logger.error("GOCDB Topology - Execution - Error parsing services")
        config.logger_syslog.error("GOCDB Topology - Execution - Error parsing services")
    return Feed_List

def parseServiceFlavours(config, XML_Element_Feed):
    "Parses service flavours list from GOCDB"
    Feed_List = None
    try:
        Root = ET.XML(XML_Element_Feed)
        Feed_List = []
        for element in Root.findall("SERVICE_TYPE"):
            Element_List = {}
            if element.getchildren():
                for child_element in element.getchildren():
                    Element_List[string.lower(child_element.tag)] = (child_element.text)
            Feed_List.append(Element_List)
    except Exception, e:
        config.logger.error("GOCDB Topology - Execution - Error parsing service flavours")
        config.logger_syslog.error("GOCDB Topology - Execution - Error parsing service flavours")
    return Feed_List

def parseRocContacts(config, XML_Element_Feed):
    "Parses ROC contacts list from GOCDB"
    Feed_List = None
    try:
        Root = ET.XML(XML_Element_Feed)
        Rocs = []
        for element in Root.findall("ROC"):
            Roc = []
            Contacts_List = []            
            for subelement in element.getchildren():
                if string.lower(subelement.tag)=='rocname':
                    Roc.append(subelement.text.encode('latin1','ignore').strip())
                if string.lower(subelement.tag)=='contact':
                    Contacts_Dic = {}
                    for subsubelement in subelement.getchildren():
                        if subsubelement.text:
                            Contacts_Dic[string.lower(subsubelement.tag)] = subsubelement.text.encode('latin1','ignore').strip()
                        else:
                            Contacts_Dic[string.lower(subsubelement.tag)] = ''
                    if not Contacts_Dic.has_key('email'):
                        Contacts_Dic['email'] = ''
                    if not Contacts_Dic.has_key('tel'):
                        Contacts_Dic['tel'] = ''
                    Contacts_List.append(Contacts_Dic)
            Roc.append(Contacts_List)
            Rocs.append(Roc)
    except Exception, e:
        config.logger.error("GOCDB Topology - Execution - Error parsing roc contacts")
        config.logger_syslog.error("GOCDB Topology - Execution - Error parsing roc contacts")
    #print Feed_List
    return Rocs

def parseSiteContacts(config, XML_Element_Feed):
    "Parses site contacts list from GOCDB"
    Feed_List = None
    try:
        Root = ET.XML(XML_Element_Feed)
        Sites = []
        for element in Root.findall("SITE"):
            Site = []
            Contacts_List = []            
            for subelement in element.getchildren():
                if string.lower(subelement.tag)=='short_name':
                    Site.append(subelement.text.encode('latin1','ignore').strip())
                if string.lower(subelement.tag)=='contact':
                    Contacts_Dic = {}
                    for subsubelement in subelement.getchildren():
                        if subsubelement.text:
                            Contacts_Dic[string.lower(subsubelement.tag)] = subsubelement.text.encode('latin1','ignore').strip()
                        else:
                            Contacts_Dic[string.lower(subsubelement.tag)] = ''
                    if not Contacts_Dic.has_key('email'):
                        Contacts_Dic['email'] = ''
                    if not Contacts_Dic.has_key('tel'):
                        Contacts_Dic['tel'] = ''
                    Contacts_List.append(Contacts_Dic)
            Site.append(Contacts_List)
            Sites.append(Site)
    except Exception, e:
        config.logger.error("GOCDB Topology - Execution - Error parsing site contacts")
        config.logger_syslog.error("GOCDB Topology - Execution - Error parsing site contacts")
    return Sites
    
def removeClosedSites(config, xml_feed):
    "Removes sites with certification status closed"
    remove_elements = []
    try:
        # find the elements to be removed
        for item in xml_feed:
            if item['certification_status'].lower()=='closed':
                #print item['name']
                remove_elements.append(item)
        for item in remove_elements:
            xml_feed.remove(item)
        #print "printing GOCDB sites having certification status - closed"
        #for item in parsed_feed:
        #    if item['certification_status'].lower()=='closed':
        #        print item['name']
    except Exception,e:
        config.logger.error("GOCDB Topology - Execution - Error parsing sites for 'certification_status' attribute")
        config.logger_syslog.error("GOCDB Topology - Execution - Error parsing sites for 'certification_status' attribute")
    return xml_feed

def mapGOCDBDowntimeServiceType(config, downtimes, mapping_dict):

    #mapping dict should be something like {'SRM': ['SRM', 'SRMv2']}, check config.py
    config.logger.info("mapping dict is : %s" % str(mapping_dict))
    config.logger.info("len of downtimes before : %s" % str(len(downtimes))) 

    resultDowntimes = []

    for downtime in downtimes:
        
        if downtime['service_type'] in mapping_dict.keys():

            for mapped_service_type in mapping_dict[downtime['service_type']]:

                new_downtime = downtime.copy()
                new_downtime['service_type'] = mapped_service_type
                
                resultDowntimes.append(new_downtime)
        else:
            resultDowntimes.append(downtime)

    config.logger.info("len of downtimes after : %s" % str(len(resultDowntimes))) 
    return resultDowntimes

def dbInterfaceFieldMappings(list_dict_elements, mapping_dictionary, ops_vo):
    "Maps GOCDB attributes to DB columns"
    new_dict_elements = []
    for dict_elements in list_dict_elements:
        new_element = {}
        is_central_lfc = 0

        for map_key in mapping_dictionary:
            if map_key in dict_elements:
                new_element[mapping_dictionary[map_key]] = dict_elements[map_key]
                if dict_elements[map_key] == 'Central-LFC':
                    is_central_lfc = 1
            else:
                new_element[mapping_dictionary[map_key]] = ""

        if is_central_lfc:
            # We do not map OPS to Central-LFCs
            new_element['vo'] = ''
        else:
            if ops_vo:
                new_element['vo'] = 'ops'

        new_dict_elements.append(new_element)
    return new_dict_elements

def addServiceURIFromBDII(config, conn, dbOutput, serviceendpoints_info):
    "Extends service information with endpoints published in BDII"
    bdiiInput = input.BDIIInput(config)
    bdii_services = bdiiInput.getServices()
    output_gocdb_services = []
    for gocdb_service in serviceendpoints_info:
        bdii_gocdb_service_list=[]
        if 'service_type' in gocdb_service:
            if string.lower(gocdb_service['service_type']) in config.db_mapping_gocdb_bdii_serv_type:
                service_type = config.db_mapping_gocdb_bdii_serv_type[string.lower(gocdb_service['service_type'])]
                hostname = gocdb_service['hostname']
                in_bdii = 0
                if (string.lower(service_type) == 'srm'):
                    # The flavour received from GOCDB feed is SRM
                    # creating a clone service entry with service flavour - SRMv2
                    bdii_srm_entry=gocdb_service.copy()
                    bdii_srm_entry['service_type'] = 'SRMv2'
                    bdii_srm_entry['serviceuri'] = gocdb_service['hostname']
                    #modify serviceuri if it is defined in BDII
                    for bdii_service in bdii_services:
                        if (bdii_service['node'] == hostname) and (bdii_service['type'].lower() in ('srm','srmv2')):
                                if bdii_service['serviceuri']: 
                                    bdii_srm_entry['serviceuri'] = bdii_service['serviceuri']
                                    gocdb_service['serviceuri'] = bdii_service['serviceuri']
                                    break
                    if not bdii_gocdb_service_list:
                        bdii_gocdb_service_list.append(gocdb_service)
                        bdii_gocdb_service_list.append(bdii_srm_entry)
                else:
                    for bdii_service in bdii_services:
                        if (bdii_service['node'] == hostname) and (bdii_service['type'].lower() == service_type.lower()):
                            gocdb_service['serviceuri'] = bdii_service['serviceuri']
                            in_bdii = 1
                            break
                    if not in_bdii:
                        gocdb_service['serviceuri'] = gocdb_service['hostname']
            else:
                # make use of gocdb url if defined
                if gocdb_service['url']:
                    gocdb_service['serviceuri'] = gocdb_service['url']
                else:
                    gocdb_service['serviceuri'] = gocdb_service['hostname']

        # check if multiple service flavours (SRM,SRMv1,SRMv2) exists 
        if bdii_gocdb_service_list:
            for service_entry in bdii_gocdb_service_list:
                output_gocdb_services.append(service_entry)
        else:
            output_gocdb_services.append(gocdb_service)
    return output_gocdb_services

    
def configGOCDBTopology(config):
    "Reads ROC information from configuration files"
    try:
        conf_instance = ConfigParser.ConfigParser()
        conf_instance.read(config.roc_config_file)
        read_roc_section=__confGet(conf_instance, 'roc')
        list_roc=[]
        for item in read_roc_section:
            if item[1]:
                list_roc = item[1].split(',')
        return list_roc
    except Exception, e:
        config.logger.error("GOCDB Topology - Configuration - Error reading configuration file")    
        config.logger_syslog.error("GOCDB Topology - Configuration - Error reading configuration file")

def validateGOCDBTopologySites(config, list_roc):
    "Validates availability and content of GOCDB sites feed"
    list_gocdb_sites=[]

    config.logger.info("GOCDB Topology - Validation - retrieving GOCDB sites from %s" % config.gocdb_site_url) 

    for roc in list_roc:
        if roc.lower()!='all':
            topo_url = config.gocdb_site_url + "&roc=" + roc
            gocdb_sites = getDataFromXMLX509(topo_url, config.x509_user_key, config.x509_user_cert)
        else:
            gocdb_sites = getDataFromXMLX509(config.gocdb_site_url, config.x509_user_key, config.x509_user_cert)
        list_gocdb_sites.append(gocdb_sites)

    if list_gocdb_sites[0]:
        config.logger.info("GOCDB Topology - Validation - GOCDB sites correctly retrieved")
        return list_gocdb_sites
    else:
        config.logger.critical("GOCDB Topology - Validation - Stopping ATP execution due to invalid feed: %s" % config.gocdb_site_url)
        config.logger_syslog.critical("GOCDB Topology - Validation - Stopping ATP execution due to invalid feed: %s" % config.gocdb_site_url)                
        return None

def validateGOCDBTopologyServices(config, list_roc):
    "Validates availability and content of GOCDB services feed"
    list_gocdb_services=[]
    for roc in list_roc:
        if roc.lower()!='all':
            topo_url=config.gocdb_serviceendpoint_url + "&roc=" + roc
            gocdb_services = getDataFromXMLX509(topo_url, config.x509_user_key, config.x509_user_cert)
        else:
            gocdb_services = getDataFromXMLX509(config.gocdb_serviceendpoint_url, config.x509_user_key, config.x509_user_cert)
        list_gocdb_services.append(gocdb_services)

    if list_gocdb_services[0]:
        config.logger.info("GOCDB Topology - Validation - GOCDB services endpoints correctly retrieved")        
        return list_gocdb_services
    else:
        config.logger.critical("GOCDB Topology - Validation - Stopping ATP execution due to invalid feed: %s" % config.gocdb_serviceendpoint_url)
        config.logger_syslog.critical("GOCDB Topology - Validation - Stopping ATP execution due to invalid feed: %s" % config.gocdb_serviceendpoint_url)                
        return None

def validateGOCDBTopologyServiceFlavours(config):
    "Validates availability and content of GOCDB service flavours feed"
    gocdb_service_flavours = []
    gocdb_service_flavours = getDataFromXMLX509(config.gocdb_servicetype_url, config.x509_user_key, config.x509_user_cert)
    if gocdb_service_flavours:
        config.logger.info("GOCDB Topology - Validation - GOCDB service flavours correctly retrieved")        
        return gocdb_service_flavours
    else:
        config.logger.critical("GOCDB Topology - Validation - Stopping ATP execution due to invalid feed: %s" % config.gocdb_servicetype_url)
        config.logger_syslog.critical("GOCDB Topology - Validation - Stopping ATP execution due to invalid feed: %s" % config.gocdb_servicetype_url)                
        return None

def validateGOCDBTopologyRocContacts(config, list_roc):
    "Validates availability and content of GOCDB ROC contacts feed"
    list_gocdb_roc_contacts = []
    for roc in list_roc:
        if roc.lower()!='all':
            topo_url=config.gocdb_roccontacts_url + "&roc=" + roc
            gocdb_roc_cont = getDataFromXMLX509(topo_url, config.x509_user_key, config.x509_user_cert)
        else:
            gocdb_roc_cont = getDataFromXMLX509(config.gocdb_roccontacts_url, config.x509_user_key, config.x509_user_cert)
        list_gocdb_roc_contacts.append(gocdb_roc_cont)
    if list_gocdb_roc_contacts[0]:
        config.logger.info("GOCDB Topology - Validation - GOCDB roc contacts correctly retrieved")
        return list_gocdb_roc_contacts
    else:
        config.logger.critical("GOCDB Topology - Validation - Stopping ATP execution due to invalid feed: %s" % config.gocdb_roccontacts_url)
        config.logger_syslog.critical("GOCDB Topology - Validation - Stopping ATP execution due to invalid feed: %s" % config.gocdb_roccontacts_url)                
        return None

def validateGOCDBTopologySiteContacts(config, list_roc):
    "Validates availability and content of GOCDB ROC contacts feed"
    list_gocdb_site_contacts = []
    for roc in list_roc:
        if roc.lower()!='all':
            topo_url=config.gocdb_sitecontacts_url + "&roc=" + roc
            gocdb_site_cont = getDataFromXMLX509(topo_url, config.x509_user_key, config.x509_user_cert)
        else:
            gocdb_site_cont = getDataFromXMLX509(config.gocdb_sitecontacts_url, config.x509_user_key, config.x509_user_cert)
        list_gocdb_site_contacts.append(gocdb_site_cont)
    if list_gocdb_site_contacts[0]:
        config.logger.info("GOCDB Topology - Validation - GOCDB site contacts correctly retrieved")        
        return list_gocdb_site_contacts 
    else:
        config.logger.critical("GOCDB Topology - Validation - Stopping ATP execution due to invalid feed: %s" % config.gocdb_sitecontacts_url)
        config.logger_syslog.critical("GOCDB Topology - Validation - Stopping ATP execution due to invalid feed: %s" % config.gocdb_sitecontacts_url)                
        return None
        
def validateGOCDBBDII(config):
    "Validates availability of BDII"
    bdiiInput = input.BDIIInput(config)
    ldap_conn = bdiiInput.checkBDII()
    if ldap_conn:
        config.logger.info("GOCDB Topology - Validation - BDII is up and running")
        return True
    else:
        config.logger.critical("GOCDB Topology - Validation - Stopping ATP execution due to unreacheble BDII service")
        config.logger_syslog.critical("GOCDB Topology - Validation - Stopping ATP execution due to unreacheble BDII service")
        return None

def synchroGOCDBTopology(config, list_roc, list_gocdb_sites, list_gocdb_services, gocdb_service_flavours, list_gocdb_roc_contacts, list_gocdb_site_contacts, conn, dbOutput, dbInput):
    "Synchronizes GOCDB topology information into the DB"
    try: 
        # this list will contain sites in all the rocs
        roc_sites_list = []
        exec_time = datetime.datetime.now()
        for roc in list_roc:
            config.setAction("GOCDB Topology - Execution - Starting execution for %s ROC" % roc)
            gocdb_sites = list_gocdb_sites[list_roc.index(roc)]
            gocdb_services = list_gocdb_services[list_roc.index(roc)]                             
            gocdb_roc_contacts = list_gocdb_roc_contacts[list_roc.index(roc)]
            gocdb_site_contacts = list_gocdb_site_contacts[list_roc.index(roc)]                             
            config.setAction("GOCDB Topology - Execution - Parsing sites")
            EGI_sites_list = parseElementFeed(config, gocdb_sites)
            if not EGI_sites_list:
                config.logger.warning("GOCDB Topology - Execution - Skiping this region due to non-existing sites")
                config.logger_syslog.warning("GOCDB Topology - Execution - Skiping this region due to non-existing sites")                
                continue                
            config.setAction("GOCDB Topology - Execution - Parsing service endpoints")
            serviceendpoints_info = parseServiceEndpoints(config, gocdb_services)
            if not serviceendpoints_info:
                config.logger.warning("GOCDB Topology - Execution - Skiping this region due to non-existing service endpoints")
                config.logger_syslog.warning("GOCDB Topology - Execution - Skiping this region due to non-existing service endpoints")                                
                continue
            config.setAction("GOCDB Topology - Execution - Parsing service flavours")
            serviceflavours_info = parseServiceFlavours(config, gocdb_service_flavours)
            if not serviceflavours_info:
                config.logger.warning("GOCDB Topology - Execution - Exiting synchronizer due to error parsing service flavours")
                config.logger_syslog.warning("GOCDB Topology - Execution - Exiting synchronizer due to error parsing service flavours")                                
                continue
            config.setAction("GOCDB Topology - Execution - Parsing roc contacts")
            roccontacts_info = parseRocContacts(config, gocdb_roc_contacts)
            if not roccontacts_info:
                config.logger.warning("GOCDB Topology - Execution - Skiping this region due to non-existing roc contacts")
                config.logger_syslog.warning("GOCDB Topology - Execution - Skiping this region due to non-existing roc contacts")                                
                continue
            config.setAction("GOCDB Topology - Execution - Parsing site contatcs")
            sitecontacts_info = parseSiteContacts(config, gocdb_site_contacts)
            if not sitecontacts_info:
                config.logger.warning("GOCDB Topology - Execution - Skiping this region due to non-existing site contatcs")
                config.logger_syslog.warning("GOCDB Topology - Execution - Skiping this region due to non-existing site contatcs")                                
                continue
            config.setAction("GOCDB Topology - Execution - Removing sites with certification status closed")
            EGI_sites_info = removeClosedSites(config, EGI_sites_list)
            config.setAction("GOCDB Topology - Execution - Inserting service flavours")
            dbOutput.updateServiceFlavours(serviceflavours_info, dbInput)
            config.setAction("GOCDB Topology - Execution - Inserting sites")
            mapped_sites_info = dbInterfaceFieldMappings(EGI_sites_info, config.db_mapping_gocdb_site, 0)
            roc_sites_list.append(mapped_sites_info)
            dbOutput.updateSites(mapped_sites_info, config.egi_infrast, config.gocdb_data_provider, dbInput)
            config.setAction("GOCDB Topology - Execution - Extracting service URI information")
            serviceendpoints_with_uri = addServiceURIFromBDII(config, conn, dbOutput, serviceendpoints_info)
            config.setAction("GOCDB Topology - Execution - Inserting service endpoints")
            mapped_serviceendpoints_info = dbInterfaceFieldMappings(serviceendpoints_with_uri, config.db_mapping_gocdb_serviceendpoint, 1)
            dbOutput.updateServiceEndPoints(mapped_serviceendpoints_info, config.egi_infrast, config.gocdb_data_provider, dbInput)
            config.setAction("GOCDB Topology - Execution - Inserting roc contacts")
            dbOutput.updateRocContacts(roccontacts_info, dbInput)
            config.setAction("GOCDB Topology - Execution - Inserting site contacts")
            dbOutput.updateSiteContacts(sitecontacts_info, dbInput)
        config.setAction("GOCDB Topology - Execution - Removing invalid sites, groups and regions")
        dbOutput.deleteInvalidGOCDBEntries(roc_sites_list,config.egi_infrast, config.gocdb_data_provider, dbInput)
        config.setAction("GOCDB Topology - Execution - Updating last run time")
        dbOutput.updateSynchronizerlastrun(config.gocdb_data_provider,dbOutput.gocdb_topo_synchro_status, exec_time)
        if config.db_commit:
            config.setAction("GOCDB Topology - Execution - Commiting changes")
            conn.commit()
    except Exception, e:
        config.logger.error("%s - Error - %s" % (config.getAction(), str(e).strip()))
        config.logger_syslog.error("%s - Error - %s" % (config.getAction(), str(e).strip()))
        conn.rollback()


# ---------------------------
# GOCDB Dowtimes Synchronizer
# ---------------------------

def validateGOCDBDowntimes(config):
    "Validates availability and content of GOCDB downtimes feed"
    #split GOCDB downtime url and insert 'start date' parameter as 'current date - 90 days'
    date_90days_before = datetime.datetime.now() - datetime.timedelta(days=90)
    downtime_url = config.gocdb_downtime_url.split('startdate')[0] + 'startdate=' + date_90days_before.strftime("%Y-%m-%d")
    gocdb_downtimes = getDataFromXMLX509(downtime_url, config.x509_user_key, config.x509_user_cert)

    if gocdb_downtimes:
        config.logger.info("GOCDB Downtimes - Validation - Dowtimes feed correctly retreived")                
        return gocdb_downtimes
    else:
        config.logger.error("GOCDB Downtimes - Validation - Exiting synchonizer due to invalid feed: %s" % config.gocdb_downtime_url)
        config.logger_syslog.error("GOCDB Downtimes - Validation - Exiting synchonizer due to invalid feed: %s" % config.gocdb_downtime_url)        
        return None
    
def synchroGOCDBDowntimes(config, gocdb_downtimes, conn, dbOutput, dbInput):
    "Synchronizes GOCDB downtimes information into the DB"
    try:
        config.setAction("GOCDB Downtimes - Execution - Parsing downtimes")
        downtimes_info = parseElementFeed(config, gocdb_downtimes)
        if not downtimes_info:
            config.logger.error("GOCDB Downtimes - Execution - Exiting synchronizer due to error parsing downtimes")
            config.logger_syslog.error("GOCDB Downtimes - Execution - Exiting synchronizer due to error parsing downtimes")
            return
        
        #fix for SAM-3324
        downtimes_info = mapGOCDBDowntimeServiceType(config, downtimes_info, config.db_mapping_gocdb_downtime_serv_type)

        config.setAction("GOCDB Downtimes - Execution - Inserting downtimes")
        mapped_downtimes_info = dbInterfaceFieldMappings(downtimes_info, config.db_mapping_gocdb_downtime, 0)
        dbOutput.updateDowntimes(mapped_downtimes_info, config.egi_infrast, config.gocdb_data_provider, dbInput)
        if config.db_commit:
            config.setAction("GOCDB Downtimes - Execution - Commiting changes")
            conn.commit()
    except Exception, e:
        config.logger.error("%s - Error - %s" % (config.getAction(), str(e).strip()))
        config.logger_syslog.error("%s - Error - %s" % (config.getAction(), str(e).strip()))
        conn.rollback()


# -------------------------
# OSG Topology Synchronizer
# -------------------------

def osgXmlExtraction(XML_Element_Feed):
    "Parses sites and services information from OSG feed"
    ports = {'CE':2119, 'SRMv1':8443, 'SRMv2':8443, 'GridFtp':2811}
    ResourceGroup_list = None
    try:
        Myroot = ET.XML(XML_Element_Feed)
        ResourceGroup_list = []

        for resourcegroup_ele in Myroot.findall("ResourceGroup"):
            ResourceGroup_dict = {}
            for element in resourcegroup_ele.getchildren():
                if element.text :
                    if string.lower(element.tag) in ('groupname','gridtype'):
                        ResourceGroup_dict[string.lower(element.tag)] = element.text #string.strip(element.text,"\n")
            Resource_list = []
            for resource_ele in resourcegroup_ele.findall("*/Resource"):
                Resource_dict = {}

                for element in resource_ele.getchildren():
                    if string.lower(element.tag)=='name':
                        Resource_dict['resourcename']=element.text
                    if string.lower(element.tag)=='fqdn':
                        Resource_dict['hostname']=element.text
                Services_list = []
                for service_ele in resource_ele.findall("*/Service"):
                    Service= {}
                    Service['name'] = ''
                    for element in service_ele.getchildren():
                        if string.lower(element.tag) in ('name', 'description', 'serviceuri'):
                            Service[string.lower(element.tag)] = element.text
                        if string.lower(element.tag) in ('details') and element.findall("uri_override"):
                            if element.findall("uri_override")[0].text == None:
                                if Service['name'] in ports.keys():
                                    Service['serviceendpoint']="%s:%s" % (Resource_dict['hostname'], ports[Service['name']])
                                else:
                                    Service['serviceendpoint']=Resource_dict['hostname']
                            else:
                                Service['serviceendpoint']=element.findall("uri_override")[0].text
                                # also take hostname when uri_overide is defined
                                Service['hostname']=element.findall("uri_override")[0].text.split(":")[0]
                        else:
                            if Service['name'] in ports.keys():
                                Service['serviceendpoint']="%s:%s" % (Resource_dict['hostname'], ports[Service['name']])
                            else:
                                Service['serviceendpoint']=Resource_dict['hostname']
                    Services_list.append(Service)
                Resource_dict["services"] = Services_list

                for wlcginfo_ele in resource_ele.findall("WLCGInformation"):
                    for element in wlcginfo_ele.getchildren():
                        if string.lower(element.tag) in ('interopmonitoring', 'ksi2kmin', 'ksi2kmax', 'interopbdii', 'ldapurl'):
                            if (element.text != None):
                                Resource_dict[string.lower(element.tag)] = string.strip(element.text,"\n")
                            else:
                                Resource_dict[string.lower(element.tag)] = '0'
                Resource_list.append(Resource_dict)
            
            ResourceGroup_dict["resources"] = Resource_list
            ResourceGroup_list.append(ResourceGroup_dict)
    except Exception ,e:
        config.logger.error("OIM Topology - Execution - Error parsing sites/services feed %s" % str(e).strip())
        config.logger_syslog.error("OIM Topology - Execution - Error parsing sites/services feed %s" % str(e).strip())
    return ResourceGroup_list

def mapDbFields(list_dict_elements, mapping_dictionary):
    "Maps OSG feed attributes with DB columns "
    new_dict_elements = []
    for dict_elements in list_dict_elements:
        new_element = {}
        for ele in dict_elements:
            if type(dict_elements[ele]).__name__ != 'list':
                if ele in mapping_dictionary:
                    new_element[mapping_dictionary[ele]] = dict_elements[ele]
                else:
                    new_element[ele] = dict_elements[ele]
        ele_backup = copy.copy(new_element)
        for res_ele in dict_elements: # For element in ResourceGroup
            if type(dict_elements[res_ele]).__name__ == 'list':
                for resource in dict_elements[res_ele]: # For Resource block in Resources
                    new_element = copy.copy(ele_backup)
                    for r_ele in resource:
                        if type(resource[r_ele]).__name__ != 'list':
                            if r_ele in mapping_dictionary:
                                new_element[mapping_dictionary[r_ele]] = resource[r_ele]
                            else:
                                new_element[r_ele] = resource[r_ele]
                    ele_backup2 = copy.copy(new_element)
                    for res_ele in resource:
                        if type(resource[res_ele]).__name__ == 'list':
                            for service in resource[res_ele]: # For Service block in Services
                                new_element = copy.copy(ele_backup2)
                                for serv_ele in service:
                                    if serv_ele in mapping_dictionary:
                                        new_element[mapping_dictionary[serv_ele]] = service[serv_ele]
                                    else:
                                        new_element[serv_ele] = service[serv_ele]
                                new_element['vo'] = 'ops'
                                # Add the missing expected parameters
                                for map_ele in mapping_dictionary:
                                    if mapping_dictionary[map_ele] not in new_element:
                                        new_element[mapping_dictionary[map_ele]] = ""
                                # Add the new entry to the list
                                new_dict_elements.append(new_element)
    return new_dict_elements

def validateOIM(config):
    "Validates availability of OSG topology feed"
    osg_xml = getDataFromXML(config.osg_topology_url)
    if osg_xml:
        config.logger.info("OSG Topology - Validation - OIM feed correctly retreived")                        
        return osg_xml
    else:
        config.logger.critical("OSG Topology - Validation - Stopping ATP execution due to invalid feed %s" % config.osg_topology_url)
        config.logger_syslog.critical("OSG Topology - Validation - Stopping ATP execution due to invalid feed %s" % config.osg_topology_url)        
        return None

def synchroOIM(config, osg_xml, conn, dbOutput, dbInput):
    "Synchronizes OSG topology information into the DB"
    try:
        exec_time = datetime.datetime.now()
        config.setAction("OSG Topology - Execution - Parsing topology")
        OSG_sites_info = osgXmlExtraction(osg_xml)
        if not OSG_sites_info:
            config.logger.error("OSG Topology - Execution - Exiting synchronizer due to error parsing sites")
            config.logger_syslog.error("OSG Topology - Execution - Exiting synchronizer due to error parsing sites")
            return

        config.setAction("OSG Topology - Execution - Inserting topology")
        mapped_osg_xml = mapDbFields(OSG_sites_info, config.db_mapping_osg)
        # do service type flavour mapping for OSG services
        for item in mapped_osg_xml:
            if 'serviceflavour' in item:
                if string.lower(item['serviceflavour']) in config.db_mapping_osg_servicetype:
                    item['serviceflavour'] = config.db_mapping_osg_servicetype[string.lower(item['serviceflavour'])]
        if mapped_osg_xml:
            dbOutput.updateOSGResources(mapped_osg_xml, config.osg_infrast, config.osg_data_provider, dbInput)
            config.setAction("OSG Topology - Execution - Updating last run time")
            dbOutput.updateSynchronizerlastrun(config.osg_data_provider,dbOutput.osg_synchro_status, exec_time)

            if config.db_commit:
                config.setAction("OSG Topology - Execution - Commiting changes")
                conn.commit()
    except Exception, e:
        config.logger.error("%s - Error - %s" % (config.getAction(), str(e).strip()))
        config.logger_syslog.error("%s - Error - %s" % (config.getAction(), str(e).strip()))
        conn.rollback()


# --------------------------
# OSG Downtimes Synchronizer
# --------------------------

def get_OSGDowntimes(config):
    "Reads OSG downtimes info from messaging system"
    try:
        downtimes_info=[]
        conn_listener = message_listener.WaitForConnectListener(config)

        if os.path.exists(config.msg_broker_list_file)==True:
            broker_list=open(config.msg_broker_list_file,'r').readlines()
            if broker_list:
                msg_broker=broker_list[0]
                broker_host=msg_broker.split(':')[1].split('//')[1]
                broker_port=int(msg_broker.split(':')[2].strip()[:-1])
            config.logger.info("OSG Donwtimes - Validation - Using broker %s:%s from local broker file" % (broker_host,broker_port) )
            conn = stomp.Connection([(broker_host,broker_port)])
        else:
            config.logger.info("OSG Donwtimes - Validation - Using broker %s:%s from configuration file" % (config.msg_broker,int(config.msg_port)) )
            conn = stomp.Connection([(config.msg_broker,int(config.msg_port))])

        conn.start()
        conn.set_listener('connect', conn_listener)
        # destination based on type of subscriber - durable/virtual topic/non-durable
        connect_headers = {}
        if config.msg_client_type=='durable':
            _, destination_type, sub_destination = config.msg_destination.split('/')
            destination = config.msg_destination
            connect_headers['activemq.subscriptionName'] = "%s_%s"%(config.msg_client_name, sub_destination)
        elif config.msg_client_type=='virtual':
            _, destination_type, sub_destination = config.msg_destination.split('/')
            destination = "/queue/%s.%s"%(config.msg_destination_virtual_prefix,sub_destination)
        elif config.msg_client_type == 'non-durable':
            destination = config.msg_destination
        else:
            raise Exception("Unsupported client type : %s"%config.msg_client_type)
        connect_headers['client-id'] = uuid.uuid4().get_hex() 
        connect_headers['client-name'] = config.msg_client_name
        conn.connect(headers = connect_headers, wait = True)
        conn.subscribe(destination=destination, ack='auto', headers=connect_headers)
        time.sleep(0.1)
        downtimes_info=conn_listener.messages
        conn.disconnect()
    except Exception,e:
        config.logger.error("OIM Downtimes - Validation - Error setting up consumer %s" % (str(e).strip()))
        config.logger_syslog.error("OIM Downtimes - Validation - Error setting up consumer %s" % (str(e).strip()))
    return downtimes_info

def parse_osg_downtimes(downtime_info):
    "Parses OSG downtime information from the message body"
    try:
        OSG_downtimes=[]
        downtime_entry={}
        #print downtime_info
        for downtime_item in downtime_info:
            if downtime_item:
                # split item into key:value pair
                downtime_entry_list=downtime_item.split('\n')
                downtime_entry={}
                for item in downtime_entry_list:
                    item_info_key_value=item.split(':',1)
                    if len(item_info_key_value)<2:
                        continue
                    else:
                        if item_info_key_value[0].lower()=='downtimeaffectedservice':
                        # split string into separate infrastructure, site, host and service type
                        # e.g. from /OSG/USCMS-FNAL-WC1-SE/cmssrm.fnal.gov/OSG-SRMv2
                        # seperate OSG, USCMS-FNAL-WC1-SE,cmssrm.fnal.gov part
                            Infrast_Site_Host= item_info_key_value[1].split("/")
                            Infrast_Site_Host=Infrast_Site_Host[1:] # remove initial '/'
                            if len(Infrast_Site_Host)==2: #a site-level downtime
                                downtime_entry['infrastructure']=Infrast_Site_Host[0]
                                downtime_entry['sitename']=Infrast_Site_Host[1]
                                downtime_entry['hostname']=''
                            else:# service level downtime
                                downtime_entry['infrastructure']=Infrast_Site_Host[0]
                                downtime_entry['hostname']=Infrast_Site_Host[2]
                                downtime_entry['servicetype']=Infrast_Site_Host[3]
                                downtime_entry['sitename']=''
                        elif item_info_key_value[0]<> "EOT" :
                            if item_info_key_value[0].lower() in ("messagetime","downtimestart","downtimeend"):
                                # convert to timestamp field
                                str_tmp=item_info_key_value[1].replace('T', ' ').strip()
                                timestamp_tuple=time.strptime(str_tmp,'%Y-%m-%d %H:%M:%S')
                                #UTC timestmap - time.mktime() assumes that the passed tuple is in local time, calendar.timegm() assumes its in GMT/UTC.
                                #downtime_entry[item_info_key_value[0]]=time.mktime(timestamp_tuple)
                                downtime_entry[item_info_key_value[0].lower()]=calendar.timegm(timestamp_tuple)
                            else:
                                downtime_entry[item_info_key_value[0].lower()]=item_info_key_value[1]
                if downtime_entry:
                    OSG_downtimes.append(downtime_entry)
    except Exception, e:
        config.logger.error("OSG Downtimes - Execution - Error parsing downtimes %s" % str(e).strip())
        config.logger_syslog.error("OSG Downtimes - Execution - Error parsing downtimes %s" % str(e).strip())
    return OSG_downtimes

def validateOSGDowntimes(config):
    "Validates availability of OSG downtime information from messaging queue"
    osg_downtimes_info = get_OSGDowntimes(config)
    if bool(osg_downtimes_info) == True:
        config.logger.info("OIM Downtimes - Validation - Dowtimes correctly retrieved")                                
        return osg_downtimes_info
    else:
        config.logger.warning("OIM Downtimes - Validation - Exiting synchonizer due to no downtimes messages found")
        config.logger_syslog.warning("OIM Downtimes - Validation - Exiting synchonizer to no downtimes messages found")
        return None

def synchroOSGDowntimes(config, osg_downtimes_info, conn, dbOutput, dbInput):
    "Synchronizes OSG downtimes information into the DB"
    try:
        parsed_downtimes = parse_osg_downtimes(osg_downtimes_info)
        config.setAction("OIM Downtimes - Execution - Updating downtimes")
        dbOutput.updateOSGDowntimes(parsed_downtimes, config.osg_infrast, config.osg_data_provider, dbInput)
        if config.db_commit:
            config.setAction("OIM Downtimes - Execution - Commiting changes")
            conn.commit()
    except Exception, e:
        config.logger.error("%s - Error - %s" % (config.getAction(), str(e).strip()))
        config.logger_syslog.error("%s - Error - %s" % (config.getAction(), str(e).strip()))
        conn.rollback()


# ----------------------------------
# Gstat (CPU and Tiers) Synchronizer
# ----------------------------------

def validateGstatCPU(config):
    "Validates availability of CPU information from GStat"
    gstat_cpu = getDataFromJSonFeed(config.gstat_cpu_hepspec06_url)
    if gstat_cpu:
        config.logger.info("Gstat CPU - Validation - CPU count correctly retrived")                                        
        return gstat_cpu
    else:
        config.logger.error("Gstat CPU - Validation - Exiting synchonizer due to invalid feed: %s" % config.gstat_cpu_hepspec06_url)
        config.logger_syslog.error("Gstat CPU - Validation - Exiting synchonizer due to invalid feed: %s" % config.gstat_cpu_hepspec06_url)
                 
def synchroGstatCPU(config, gstat_cpu, conn, dbOutput, dbInput):
    "Synchronizes GStat CPU information into the DB"
    try:
        exec_time = datetime.datetime.now()
        config.setAction("Gstat CPU - Execution - Inserting CPU counts")
        dbOutput.updateGSTATCPUCounts(gstat_cpu, config.gstat_data_provider)
        config.setAction("Gstat CPU - Execution - Updating last run time")
        dbOutput.updateSynchronizerlastrun(config.gstat_data_provider, dbOutput.gstat_synchro_status, exec_time)
        if config.db_commit:
                config.setAction("Gstat CPU - Execution - Commiting changes")
                conn.commit()
    except Exception, e:
        config.logger.error("%s - Error - %s" % (config.getAction(), str(e).strip()))
        config.logger_syslog.error("%s - Error - %s" % (config.getAction(), str(e).strip()))
        conn.rollback()

def validateGstatTierFederation(config): 
    "Validates availability of tiers and federations information from GStat"
    gstat_tiers_federations = getDataFromJSonFeed(config.gstat_tier_federation_url)
    if gstat_tiers_federations:
        config.logger.info("Gstat Tier - Validation - Tier and federation correctly retreived")                                        
        return gstat_tiers_federations
    else:
        config.logger.error("Gstat Tier - Validation - Exiting synchonizer due to invalid feed: %s" % config.gstat_tier_federation_url)
        config.logger_syslog.error("Gstat Tier - Validation - Exiting synchonizer due to invalid feed: %s" % config.gstat_tier_federation_url)

def synchroGstatTierFederation(config, gstat_tiers_federations, conn, dbOutput, dbInput):
    "Synchronizes GStat tiers and federations information into the DB"
    try:
        exec_time = datetime.datetime.now()
        config.setAction("Gstat Tier - Execution - Inserting tiers and federations")        
        dbOutput.updateTiers_And_Federations(gstat_tiers_federations, config.gstat_data_provider, dbInput)
        config.setAction("Gstat Tier - Execution - Updating last run time")
        dbOutput.updateSynchronizerlastrun(config.gstat_data_provider,dbOutput.gstat_synchro_status, exec_time)
        if config.db_commit:
            config.setAction("Gstat Tier - Execution - Commiting changes")
            conn.commit()
    except Exception, e:
        config.logger.error("%s - Error - %s" % (config.getAction(), str(e).strip()))
        config.logger_syslog.error("%s - Error - %s" % (config.getAction(), str(e).strip()))
        conn.rollback()


# --------------------
# OSG CPU Synchronizer
# --------------------

def osgKSI2KExtraction(XML_Element_Feed):
    "Parses OSG CPU information from OSG feed"
    ResourceGroup_list = None
    try:

        Myroot = ET.XML(XML_Element_Feed)
        ResourceGroup_list = []

        for resourcegroup_ele in Myroot.findall("ResourceGroup"):
            ResourceGroup_dict = {}
            for element in resourcegroup_ele.getchildren():
                if element.text :
                    if string.lower(element.tag) in ('groupname'):
                        #ResourceGroup_dict[string.lower(element.tag)] = element.text #string.strip(element.text,"\n")
                        OSGgroupname = element.text

            cur_ksi2kmax=0;cur_ksi2kmin=0;cur_hepspec=0
            for resource_ele in resourcegroup_ele.findall("*/Resource"):
                Resource_dict = {}
                for wlcginfo_ele in resource_ele.findall("WLCGInformation"):
                    for element in wlcginfo_ele.getchildren():
                        if string.lower(element.tag) in ('interopmonitoring', 'ksi2kmin', 'ksi2kmax', 'interopbdii','hepspec'):
                            if (element.text != None):
                                Resource_dict[string.lower(element.tag)] = string.strip(element.text,"\n")
                            else:
                                Resource_dict[string.lower(element.tag)] = '0'
                if Resource_dict.has_key('interopmonitoring'):

                    if Resource_dict.has_key('ksi2kmax')and Resource_dict['interopmonitoring']=='True':
                        cur_ksi2kmax= float(Resource_dict['ksi2kmax'])+cur_ksi2kmax
                        Resource_dict['ksi2kmax']= cur_ksi2kmax

                    if Resource_dict.has_key('ksi2kmin')and Resource_dict['interopmonitoring']=='True':
                        cur_ksi2kmin= float(Resource_dict['ksi2kmin'])+cur_ksi2kmin
                        Resource_dict['ksi2kmin']= cur_ksi2kmin

                    if Resource_dict.has_key('hepspec')and Resource_dict['interopmonitoring']=='True':
                        cur_hepspec= float(Resource_dict['hepspec'])+cur_hepspec
                        Resource_dict['hepspec']= cur_hepspec

                    if Resource_dict['interopmonitoring']=='True':
                        if Resource_dict.has_key('hepspec'):
                            ResourceGroup_dict['hepspec']=Resource_dict['hepspec']
                        if Resource_dict.has_key('ksi2kmax'):
                            ResourceGroup_dict['ksi2kmax']=Resource_dict['ksi2kmax']
                        if Resource_dict.has_key('ksi2kmin'):
                            ResourceGroup_dict['ksi2kmin']=Resource_dict['ksi2kmin']
                        ResourceGroup_dict['groupname']= OSGgroupname

            if ResourceGroup_dict.has_key('groupname'):
                if not ResourceGroup_dict.has_key('hepspec'):
                    ResourceGroup_dict['hepspec'] =-1
                if not ResourceGroup_dict.has_key('ksi2kmin'):
                    ResourceGroup_dict['ksi2kmin'] =-1
                if not ResourceGroup_dict.has_key('ksi2kmax'):
                    ResourceGroup_dict['ksi2kmax'] =-1

            if ResourceGroup_dict:
                #print ResourceGroup_dict
                ResourceGroup_list.append(ResourceGroup_dict)
    except Exception ,e:
        config.logger.error("OIM CPU - Execution - Error parsing CPU counts %s" % str(e).strip())
        config.logger_syslog.error("OIM CPU - Execution - Error parsing CPU counts %s" % str(e).strip())
    return ResourceGroup_list

def synchroOIMCPU(config, osg_xml, conn, dbOutput):
    "Synchronizes OSG CPU information into the DB"
    try:
        osg_sites_info = osgKSI2KExtraction(osg_xml)
        if not osg_sites_info:
            config.logger.error("OIM CPU - Execution - Exiting synchonizer due to error parsing CPU counts")
            config.logger_syslog.error("OIM CPU - Execution - Exiting synchonizer due to error parsing CPU counts")
            return
        config.setAction("OIM CPU - Execution - Inserting CPU counts")
        dbOutput.updateOSGKSI2K(osg_sites_info, config.osg_infrast)
        if config.db_commit:
            config.setAction("OIM CPU - Execution - Commiting changes")
            conn.commit()
    except Exception, e:
        config.logger.error("%s - Error - %s" % (config.getAction(), str(e).strip()))
        config.logger_syslog.error("%s - Error - %s" % (config.getAction(), str(e).strip()))
        conn.rollback()


# -----------------
# BDII Synchronizer
# -----------------

def validateBDII(config):
    "Validates availability of BDII"
    bdiiInput = input.BDIIInput(config)
    ldap_conn = bdiiInput.checkBDII()
    if ldap_conn:
        config.logger.info("BDII - Validation - BDII is up and running")
        return True
    else:
        config.logger.critical("BDII - Validation - Exiting synchonizer due to unreacheble BDII service")
        config.logger_syslog.critical("BDII - Validation - Exiting synchonizer due to unreacheble BDII service")
        return None

def validateBDIIServices(config):
    "Parses services information from BDII"
    services = []
    bdiiInput = input.BDIIInput(config)
    bdii_services = bdiiInput.getServices()
    if bdii_services:
        config.logger.info("BDII - Validation - VO mappings correclty retreived")
        return bdii_services
    else:
        config.logger.critical("BDII - Validation - Exiting synchonizer due to problems getting VO mappings from %s/%s" % (config.bdii_ldap_uri, config.bdii_ldap_base))
        config.logger_syslog.critical("BDII - Validation - Exiting synchonizer due to problems getting VO mappings from %s/%s" % (config.bdii_ldap_uri, config.bdii_ldap_base))

def validateBDIIMPI(config):
    "Parses MPI information from BDII"
    services = []
    bdiiInput = input.BDIIInput(config)
    bdii_mpi = bdiiInput.getMPIServices()
    if bdii_mpi:
        config.logger.info("BDII - Validation - MPI services correclty retreived")                                                
        return bdii_mpi
    else:
        config.logger.critical("BDII - Validation - Exiting synchonizer due to problems getting VO mappings from %s/%s" % (config.bdii_ldap_uri, config.bdii_ldap_base))
        config.logger_syslog.critical("BDII - Validation - Exiting synchonizer due to problems getting VO mappings from %s/%s" % (config.bdii_ldap_uri, config.bdii_ldap_base))

def synchroBDII(config, bdii_services, bdii_mpi, vofeeds, conn, dbOutput, dbInput):
    "Synchronizes BDII information into the DB"
    try:
        exec_time = datetime.datetime.now()
        config.setAction("BDII - Execution - Updating service VO mappings")
        dbOutput.updateServiceVOs(bdii_services, vofeeds, dbInput)
        config.setAction("BDII - Execution - Updating MPI services")
        dbOutput.updateMPIServices(bdii_mpi, config.bdii_data_provider)
        config.setAction("BDII - Execution - Updating last run time")
        dbOutput.updateSynchronizerlastrun(config.bdii_data_provider,dbOutput.bdii_synchro_status, exec_time)
        if config.db_commit:
            config.setAction("BDII - Execution - Commiting changes")
            conn.commit()
    except Exception, e:
        config.logger.error("%s - Error - %s" % (config.getAction(), str(e).strip()))
        config.logger_syslog.error("%s - Error - %s" % (config.getAction(), str(e).strip()))
        conn.rollback()
        

# ---------------------
# VO Feeds Synchronizer
# ---------------------

def configVOFeeds(config):
    "Reads VO feeds configuration file"
    vofeeds = []
    conf_instance = ConfigParser.ConfigParser()
    conf_instance.read(config.vofeeds_config_file)
    read_vofeeds_section=__confGet(conf_instance,'vo_feeds')
    for item in read_vofeeds_section:
        if item[0].lower()>0:
            __vofeed_url = item[1].split(',')[0]
            __vofeed_voname = item[0][:item[0].lower().find('_')]
            vofeeds.append([__vofeed_voname, __vofeed_url])
        else:
            config.logger.error("VO Feeds - Configuration - No VO feeds declared in configuration file")
            config.logger_syslog.error("VO Feeds - Configuration - No VO feeds declared in configuration file")            
    return vofeeds
    
def validateVOFeeds(config, vofeeds):
    "Validates availability of VO Feeds"

    # reads gocdb data and rsv data
    gocdb_xml = getDataFromXMLX509(config.gocdb_serviceendpoint_url, config.x509_user_key, config.x509_user_cert)
    if not gocdb_xml:
        config.logger.error("VO Feeds - Validation - Exiting synchonizer due to missing feed: %s" % (config.gocdb_serviceendpoint_url))
        config.logger_syslog.error("VO Feeds - Validation - Exiting synchonizer due to missing feed: %s" % (config.gocdb_serviceendpoint_url))        
        return None
    rsv_xml = getDataFromXML(config.osg_topology_url)
    if not rsv_xml:
        config.logger.error("VO Feeds - Validation - Exiting synchonizer due to missing feed: %s" % (config.osg_topology_url))
        config.logger_syslog.error("VO Feeds - Validation - Exiting synchonizer due to missing feed: %s" % (config.osg_topology_url))        
        return None
    
    vos_to_remove = []    
    for vf in vofeeds:
        vofeed_name = vf[0]
        vofeed_url = vf[1]
        config.setAction("VO Feeds - Validation - Starting validation for %s vo feed" % vofeed_name)
                
        # reads vo feed data
        vofeed_xml = getDataFromXML(vofeed_url)
        if not vofeed_xml:
            config.logger.info("VO Feeds - Validation - Skiping vo feed due to missing feed: %s" % (vofeed_url))
            vos_to_remove.append(vofeed_name)
            continue
        
        # parses xml data to objects
        config.setAction("VO Feeds - Validation - Parsing xml schema")
        xsd_parsed=etree.parse(config.vofeeds_xsd_schema)
        xsd_schema=etree.XMLSchema(xsd_parsed)

        config.setAction("VO Feeds - Validation - Parsing vo feed xml")
        xml_parsed=etree.fromstring(vofeed_xml)
        vofeed_tree = ET.fromstring(vofeed_xml)
        vofeed_servicesflavours = set([ (x.attrib['hostname'].strip(), x.attrib['flavour'].strip() ) for x in vofeed_tree.findall('atp_site/service') ])
        vofeed_sitesservices = [ (x.attrib['name'].strip(), y.attrib['hostname'].strip() ) for x in vofeed_tree.findall('atp_site') for y in x.findall('service') ]
        vofeed_sites = [ ( x.attrib['name'].strip() ) for x in vofeed_tree.findall('atp_site') ]
        
        config.setAction("VO Feeds - Validation - Parsing gocdb xml")        
        goc_tree = ET.fromstring(gocdb_xml)
        gocdb_servicesflavours = set([ (x.findtext('HOSTNAME').strip(), x.findtext('SERVICE_TYPE').strip() ) for x in goc_tree.findall('SERVICE_ENDPOINT') ])
        gocdb_sitesservices = [ ( x.findtext('SITENAME').strip(), x.findtext('HOSTNAME').strip() ) for x in goc_tree.findall('SERVICE_ENDPOINT') ]
        gocdb_hosts = set([ x[0] for x in gocdb_servicesflavours ])

        config.setAction("VO Feeds - Validation - Parsing rsv xml")
        rsv_tree = ET.fromstring(rsv_xml)
        rsv_servicesflavours = set([ ( x.findtext('FQDN').strip(), x.findtext('Services/Service/Name').strip() ) for x in rsv_tree.findall('ResourceGroup/Resources/Resource') if x.findtext('WLCGInformation/InteropMonitoring')=='True'])
        rsv_sitesservices = set([ ( x.findtext('GroupName').strip(), y.findtext('FQDN').strip() ) for x in rsv_tree.findall('ResourceGroup') for y in x.findall('Resources/Resource') if y.findtext('WLCGInformation/InteropMonitoring')=='True' ])
        rsv_hosts = set([ x[0] for x in rsv_servicesflavours ])        

        # check sanity of vo feed according to schema
        config.setAction("VO Feeds - Validation - Checking compliance with schema")
        if xsd_schema.validate(xml_parsed):
            config.logger.info("VO Feeds - Validation - Feed is compliant with schema")
        else:
            config.logger.info("VO Feeds - Validation - Skiping vo feed due to not compliant feed")
            vos_to_remove.append(vofeed_name)
            continue
        
        # check sanity of vo feed services
        config.setAction("VO Feeds - Validation - Checking sanity of services")
        #allowed_flavours = ['CE', 'CREAM-CE', 'OSG-CE', 'SRMv2', 'OSG-SRMv2', 'FTS', 'Local-LFC', 'Central-LFC', 'Squid', 'Frontier']
        for item in vofeed_servicesflavours:
            if item[0] not in gocdb_hosts and item[0] not in rsv_hosts and item[1] != 'Squid' and item[1] != 'Frontier':
                config.logger.warning("VO Feeds - Validation - %s (%s) not registered in GOCDB or RSV" % (item[0], item[1]))
            if item[0] in gocdb_hosts:
                vofeed_site = [ x[0] for x in vofeed_sitesservices if x[1]==item[0] ]
                gocdb_site = [ x[0] for x in gocdb_sitesservices if x[1]==item[0] ]
                if vofeed_site[0] not in gocdb_site:
                    config.logger.warning("VO Feeds - Validation - %s (%s) belongs to site %s in vofeed and to site %s in gocdb" % (item[0], item[1], vofeed_site[0], gocdb_site[0])) 
            if item[0] in rsv_hosts:
                vofeed_site = [ x[0] for x in vofeed_sitesservices if x[1]==item[0] ]
                rsv_site = [ x[0] for x in rsv_sitesservices if x[1]==item[0] ]
                if vofeed_site[0] not in rsv_site:
                    config.logger.warning("VO Feeds - Validation - %s (%s) belongs to site %s in vofeed and to site %s in rsv" % (item[0], item[1], vofeed_site[0], rsv_site[0])) 
            #if item[1] not in allowed_flavours:
            #    config.logger.warning("VO Feeds - Validation - %s service with %s flavour is not allowed" % (item[0], item[1]))

        # check sanity of vo feed groups
        config.setAction("VO Feeds - Validation - Checking sanity of groups")
        for item in vofeed_sites:
            sitegroups = [ ( y.attrib['type'].strip().upper() ) for x in vofeed_tree.findall('atp_site') for y in x.findall('group') if x.attrib['name'].strip() == item ]
            if vofeed_name.upper()+"_SITE" not in sitegroups:
                config.logger.error("VO Feeds - Validation - %s site does not declare site group" % item)
            if vofeed_name.upper()+"_TIER" not in sitegroups:
                config.logger.error("VO Feeds - Validation - %s site does not declare tier group" % item)

    vofeedsvalid = list(vofeeds)
    for item in vos_to_remove:
        for x in vofeedsvalid:
            if item == x[0]:
                vofeedsvalid.remove(x)

    return vofeedsvalid

def extractionVOFeeds(XML_Element_Feed):
    "Parses sites and groups information from VO feed"
    
    sitegroup_list=[]
    try:
        Myroot = ET.XML(XML_Element_Feed)
        vofeed = Myroot.find('vo')
        site_list =[]
        for virtualsites in Myroot.findall("atp_site"):
            siteservices_dict={}
            siteservices_dict['vo']=vofeed.text
            for name, value in virtualsites.items():
                if 'infrast' in virtualsites.keys():
                    if name.lower()=='infrast':
                        siteservices_dict['infrast']=value
                    elif name.lower()=='name':
                        siteservices_dict['atp_site']=value
                else:
                        siteservices_dict['infrast']=''
                        siteservices_dict['atp_site']=value
            
            services_list=[]
            for services in virtualsites.findall('service'):
                services_dict={}
                for name,value in services.items():
                    if name=='flavour':
                        services_dict['flavour']=value
                    elif name == 'hostname':
                        services_dict['hostname']=value
                    elif name =='endpoint':
                        services_dict['endpoint']=value
                services_list.append(services_dict)

                spacetoken_list=[]
                for spacetokens in services.findall('spacetoken'):
                    spacetoken_dict={}
                    for name,value in spacetokens.items():
                        if name=='name':
                            spacetoken_dict['spacetoken_name']=value
                        elif name == 'base_path':
                            spacetoken_dict['spacetoken_path']=value
                    spacetoken_list.append(spacetoken_dict)
                siteservices_dict['spacetokens'] =spacetoken_list
            groups_list=[]
            for groupnames in virtualsites.findall('group'):
                groups_dict={}
                for name,value in groupnames.items():
                    if name=='name':
                        groups_dict['groupname']=value
                    elif name == 'type':
                        groups_dict['grouptype']=value
                groups_list.append(groups_dict)
            siteservices_dict['groups'] =groups_list
            siteservices_dict['service']=services_list
            #print siteservices_dict
            site_list.append(siteservices_dict)
        sitegroup_list.append(site_list)
    except Exception, e:
            config.logger.error("VO Feeds - Execution - Error parsing VO feed")
            config.logger_syslog.error("VO Feeds - Execution - Error parsing VO feed")
    return sitegroup_list


def extractVOFeedsLinks(XML_Element_Feed):
    "Parses site and groups information from VO feed"

    try:
        Myroot = ET.XML(XML_Element_Feed)
        vofeed = Myroot.find('vo')
        site_list =[]
        for virtualsites in Myroot.findall("atp_site"):
            siteservices_dict={}
            for name, value in virtualsites.items():
                if name.lower()=='name':
                    siteservices_dict['atp_site']=value
            for groupnames in virtualsites.findall('group'):
                groups_dict={}
                if groupnames.items()[0][1].find('_Tier') != -1:
                    siteservices_dict['grouptier']=groupnames.items()[1][1]
                if groupnames.items()[0][1].find('_Site') != -1:
                    siteservices_dict['groupsite']=groupnames.items()[1][1]
            site_list.append(siteservices_dict)
    except Exception, e:
            config.logger.error("VO Feeds - Execution - Error parsing VO feed")
            config.logger_syslog.error("VO Feeds - Execution - Error parsing VO feed")
    return site_list

def synchroVOFeeds(config, vofeeds, vofeedsvalid, conn, dbOutput, dbInput):
    "Synchronizes VO feed information into the DB"
    
    try:
        # list of VOs having their own feed of sites/services groupings

        for vf in vofeedsvalid:
            if vf[0].lower()>0:
                __VO_feed_voname = vf[0]
                __VO_feed_url = vf[1]
                config.setAction("VO Feeds - Execution - Starting processing of %s vo feed" % __VO_feed_voname)
                
                config.setAction("VO Feeds - Execution - Getting site-service groups")
                VO_feed_XML = getDataFromXML(__VO_feed_url)
                config.setAction("VO Feeds - Execution - Extracting site-service groups")
                VO_sitegroups_info = extractionVOFeeds(VO_feed_XML)
                if not VO_sitegroups_info:
                    config.logger.error("VO Feeds - Execution - Exiting synchronizer due to problems in extracting site-service groups")
                    config.logger_syslog.error("VO Feeds - Execution - Exiting synchronizer due to problems in extracting site-service groups")
                    return
                VO_sitegroups_link = extractVOFeedsLinks(VO_feed_XML)
                if not VO_sitegroups_link:
                    config.logger.error("VO Feeds - Execution - Exiting synchronizer due to problems in extracting groups link")
                    config.logger_syslog.error("VO Feeds - Execution - Exiting synchronizer due to problems in extracting groups link")
                    return

                config.setAction("VO Feeds - Execution - Updating service-vo mappings")
                dbOutput.updateServiceVOFeeds(VO_sitegroups_info,__VO_feed_voname)
                if config.db_commit:
                    config.setAction("VO Feeds - Execution - Committing changes")
                    conn.commit()
                config.setAction("VO Feeds - Execution - Updating service groups")
                dbOutput.updateVOGroupings(VO_sitegroups_info, __VO_feed_voname, dbInput)
                if config.db_commit:
                    config.setAction("VO Feeds - Execution - Committing changes")
                    conn.commit()
                config.setAction("VO Feeds - Execution - Updating groups link")
                dbOutput.updateVOGroupLinks(VO_sitegroups_link, __VO_feed_voname)
                if config.db_commit:
                    config.setAction("VO Feeds - Execution - Committing changes")
                    conn.commit()
                config.setAction("VO Feeds - Execution - Updating last run time")
                dbOutput.updateSynchronizerlastrun(config.vofeeds_data_provider, dbOutput.vofeeds_synchro_status, datetime.datetime.now())                    
                if config.db_commit:
                    config.setAction("VO Feeds - Execution - Committing changes")
                    conn.commit()

        # set vo-groupings as isdeleted='Y' for VOs not having their feed
        config.setAction("VO Feeds - Execution - Marking service-groups as deleted for vo feeds not declared in vo feeds configuration file")
        vo_feeds_to_keep = []
        for vf in vofeeds:        
            vo_feeds_to_keep.append(vf[0])
        dbOutput.deleteVOGroupings(vo_feeds_to_keep, dbInput)
        if config.db_commit:
            config.setAction("VO Feeds - Execution - Committing changes")
            conn.commit()
        
    except Exception, e:
        config.logger.error("%s - Error - %s" % (config.getAction(), str(e).strip()))
        config.logger_syslog.error("%s - Error - %s" % (config.getAction(), str(e).strip()))
        conn.rollback()


def run(config, conn, dbInput, dbOutput):
    "Executes the enabled synchronizers"
    
    # Reads the configuration file and parse the command line arguments.
    #config = config.Config()

    log_date = datetime.datetime.now()
            
    # # Open database connection to update the information
    # if string.lower(config.database_type)=="mysql":
    #     import MySQLdb
    #     config.setAction("Connecting to ATP MySQL database")
    #     conn = MySQLdb.Connection(user=config.database_user, passwd=config.database_password,host= config.database_host, db=config.database_name)
    # else:
    #     import cx_Oracle
    #     conn = cx_Oracle.Connection(user=config.database_user, password=config.database_password, dsn=config.database_name)
    #     config.setAction("Connecting to ATP Oracle database")
    #     conn.begin() # update everything in a big transaction
    # cursor = conn.cursor()
    # if string.lower(config.database_type)=="mysql":
    #     cursor.execute('SET autocommit=0;')
    #dbInput = input.DBInput(config, cursor)
    #dbOutput = output.DBOutput(config, cursor)

    # Synchronizes VOs from the CIC Portal
    if config.run_synchro_cic_portal == "Y":
        config.setAction("CIC - Validation - Starting validation of VO cards")            
        vos = validateCICPortalVO(config)
        config.setAction("CIC - Validation - Starting validation of VOMS users")            
        voms = validateVOMS(config)
        if vos and voms:
            config.setAction("CIC - Execution - Starting")            
            synchroCICPortalVO(config, vos, voms, conn, dbInput, dbOutput)

    # Synchronizes topology from GOCDB
    if config.run_synchro_gocdb_topo == "Y":
        config.setAction("GOCDB Topology - Configuration - Starting")
        list_roc = configGOCDBTopology(config)
        config.setAction("GOCDB Topology - Validation - Starting sites check")        
        list_gocdb_sites = validateGOCDBTopologySites(config, list_roc)
        config.setAction("GOCDB Topology - Validation - Starting services check")
        list_gocdb_services = validateGOCDBTopologyServices(config, list_roc)
        config.setAction("GOCDB Topology - Validation - Starting service flavours check")
        gocdb_service_flavours = validateGOCDBTopologyServiceFlavours(config)
        config.setAction("GOCDB Topology - Validation - Starting roc contacts check")
        list_gocdb_roc_contacts = validateGOCDBTopologyRocContacts(config, list_roc)
        config.setAction("GOCDB Topology - Validation - Starting site contacts check")
        list_gocdb_site_contacts = validateGOCDBTopologySiteContacts(config, list_roc)
        config.setAction("GOCDB Topology - Validation - Starting BDII check")
        bdii_conn = validateGOCDBBDII(config)
        if list_gocdb_sites and list_gocdb_services and gocdb_service_flavours and list_gocdb_roc_contacts and list_gocdb_site_contacts and bdii_conn:
            config.setAction("GOCDB Topology - Execution - Starting")            
            synchroGOCDBTopology(config, list_roc, list_gocdb_sites, list_gocdb_services, gocdb_service_flavours, list_gocdb_roc_contacts, list_gocdb_site_contacts, conn, dbOutput, dbInput)   
        else:
            stopExecution(config)

    # Synchronizes downtimes from GOCDB
    if config.run_synchro_gocdb_downtime == "Y":
        config.setAction("GOCDB Downtimes - Validation - Starting")
        gocdb_downtimes = validateGOCDBDowntimes(config)
        if gocdb_downtimes:
            config.setAction("GOCDB Downtimes - Execution - Starting")
            synchroGOCDBDowntimes(config, gocdb_downtimes, conn, dbOutput, dbInput)

    # Synchronizes topology from OSG
    if config.run_synchro_osg == "Y":
        config.setAction("OSG Topology - Validation - Starting")
        osg_xml = validateOIM(config)
        if osg_xml:
            config.setAction("OSG Topology - Execution - Starting")
            synchroOIM(config, osg_xml, conn, dbOutput, dbInput)

            # OSG KSI2K and HEPSPEC06 numbers
            config.setAction("OIM CPU - Execution - Starting")
            synchroOIMCPU(config, osg_xml, conn, dbOutput)
        else:
            stopExecution(config)

    # Synchronizes downtimes from OSG
    if config.run_synchro_osg_downtime == "Y":
        config.setAction("OSG Downtimes - Validation - Starting")
        osg_downtimes_info = validateOSGDowntimes(config)
        if osg_downtimes_info:
            config.setAction("OSG Downtimes - Execution - Starting")            
            synchroOSGDowntimes(config, osg_downtimes_info, conn, dbOutput, dbInput)

    # Synchronizes CPU information from GSTAT
    if config.run_synchro_gstat == "Y":
        # Gstat CPU counts and HEPSPEC06 numbers
        config.setAction("Gstat CPU - Validation - Starting")
        gstat_cpu = validateGstatCPU(config)
        if gstat_cpu:
            config.setAction("Gstat CPU - Execution - Starting")
            synchroGstatCPU(config, gstat_cpu, conn, dbOutput, dbInput)
        # Gstat tiers and federations
        config.setAction("Gstat Tier - Validation - Starting")
        gstat_tiers_federations = validateGstatTierFederation(config)
        if gstat_tiers_federations:
            config.setAction("Gstat Tier - Execution - Starting")
            synchroGstatTierFederation(config, gstat_tiers_federations, conn, dbOutput, dbInput)

    # Synchronizes VO mappings from BDII
    if config.run_synchro_bdii == "Y":
        config.setAction("BDII - Configuration - Starting")
        vofeeds = configVOFeeds(config)
        config.setAction("BDII - Validation - Starting BDII check")
        bdii_conn = validateBDII(config)
        if bdii_conn:
            config.setAction("BDII - Validation - Starting BDII services check")            
            bdii_services = validateBDIIServices(config)
            config.setAction("BDII - Validation - Starting BDII mpi check")            
            bdii_mpi = validateBDIIMPI(config)
        if bdii_services and bdii_mpi:
            config.setAction("BDII - Execution - Starting")
            synchroBDII(config, bdii_services, bdii_mpi, vofeeds, conn, dbOutput, dbInput)

    # Synchronizes topology from VO feeds
    if config.run_synchro_vo_feeds == "Y":
        config.setAction("VO Feeds - Configuration - Starting")
        vofeeds = configVOFeeds(config)
        config.setAction("VO Feeds - Validation - Starting")        
        vofeedsvalid = validateVOFeeds(config, vofeeds)
        config.setAction("VO Feeds - Execution - Starting")
        synchroVOFeeds(config, vofeeds, vofeedsvalid, conn, dbOutput, dbInput)        

    return 0

