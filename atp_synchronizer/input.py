##############################################################################
#
# NAME:        input.py
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
#
# CREATED:     23-Nov-2009
#
# NOTES:
#
# MODIFIED:
#
##############################################################################

import re,string
import ldap
import logging

from atp_synchronizer import config

class InputSource (object):
    "An abstract class to define the methods that should be provided by an Input Source."

    def getServices(self):
        "Returns a list of dictionaries containing information about each grid service described in the input source"
        raise NotImplementedError( 'getServices should be overriden in subclass')
        
    def getServiceNames(self):
        "Returns a dictionary with the names of all services in the input source"
        raise NotImplementedError( 'getServiceNames should be overriden in subclass')

    def getServiceFlavours(self):
        "Returns a dictionary with the names of all services flavours in the input source"
        raise NotImplementedError( 'getServiceFlavours should be overriden in subclass')

    def getServiceVOs(self):
        "Returns a dictionary with the service VOs in the input source"
        raise NotImplementedError( 'getServiceVOs should be overriden in subclass')
                
    def getCountries(self):
        "Returns a dictionary with all countries described in the input source"
        raise NotImplementedError( 'getCountries should be overriden in subclass')
 
    def getTiers(self):
        "Returns a dictionary with all tiers described in the input source"
        raise NotImplementedError( 'getTiers should be overriden in subclass')

    def getSites(self):
        "Returns a dictionary with all sites in the input source"
        raise NotImplementedError( 'getSites should be overriden in subclass')
                
    def getSitesDesc(self):
        "Returns a dictionary with the description of all sites in the input source"
        raise NotImplementedError( 'getSitesDesc should be overriden in subclass')

    def getSysAdminsContact(self):
        "Returns a dictionary with the sys admin contact with all sites in the input source"
        raise NotImplementedError( 'getSysAdminsContact should be overriden in subclass')
        
    def getNodes(self):
        "Returns a dictionary with the nodes in the input source"
        raise NotImplementedError( 'getNodes should be overriden in subclass')
                
    def getNewNodes(self, timestamp):
        "Returns a dictionary with the nodes inserted in the input source after a given timestamp"
        raise NotImplementedError( 'getNewNodes should be overriden in subclass')
                                
    def getVOs(self):
        "Returns a dictionary with the  VOs in the input source "
        raise NotImplementedError( 'getVOs should be overriden in subclass')
                
    def getResources(self, rname):
        "Returns a dictionary with the resources of a given type in the input source"
        raise NotImplementedError( 'getResources should be overriden in subclass')

    def getResourceVOs(self, rname):
        "Returns a dictionary with the resources VOs for a given type of resource in the input source"
        raise NotImplementedError( 'getResourcesVOs should be overriden in subclass')


class BDIIInput(InputSource):
    "Class to gather data from a BDII server" 

    __ldap_uri                      = "ldap://bdii.host:2170" 
    __ldap_base                     = "o=grid"
    __ldap_filter                   = """(|(objectClass=GlueSite)(objectClass=GlueService)(objectClass=GlueCE)(objectClass=GlueSA))"""
    __ldap_mpi_filter               = """(&(objectclass=GlueCE)(objectClass=glueCETop)(GlueCEAccessControlBaseRule=VO:ops))"""                 
    __countries                     = {} # 'Unknown' # Default site country
    __tiers                         = {} # '3' # default tier value for a site
    __sitesdesc                     = {} # '' # default site description
    __sysAdminsContact              = {} # 'Unknown' # Default Sys Admin Contact
    __site2realname                 = {} # maps site name from dn to name in GlueSiteName          
    
    __logger                        = None
    
    __vo_dep_services = { # vo dependent services
                         "resourcebroker" : "RB",
                         "lcg-file-catalog" : "LFC_C",
                         "lcg-local-file-catalog" : "LFC_L",
                         "org.glite.filetransfer" : "FTS",
                         "org.glite.wms" : "WMS",
                         "org.glite.wms.wmproxy" : "WMS",
                         "srm_v1" : "SRMv1",
                         "srm_v2" : "SRMv2",
                         "srm" : "SRM",
                         "dummyce" : "CE",   # dummy entry to mark CE as vo specific service
                         "dummyse" : "SE",   # same for SE
                         "dummygce" : "gCE", # same for gCE
                         "dummyarcce" : "ArcCE", # same for ArcCE
                         "dummygrb" : "WMS",  # same for gRB
                         "vobox" : "VOBOX",
                         "dummycreamce" : "CREAMCE"
    }

    __vo_indep_services = { # vo independent srvices
                           "myproxy" : "MyProxy"
    }
    __MPI_flavours = ['MPICH','MPICH2','OPENMPI']

    # precompiled re patterns for extracting info
    __site_pattern = re.compile("mds-vo-name=([^,]*),mds-vo-name=local,o=grid$", re.I)
    __cert_pattern = re.compile("/[^/=]+=[^/]+/") # to recognize certificate subjects
    __node_pattern = re.compile("""
    ^                                       # must match all
    (?:[a-zA-Z]+=)?                         # for chunk key (GlueSEUniqueID=)
    (?:[a-zA-Z]+://)?                       # protocol (optional)
    ((?:[a-zA-Z0-9_-]+\\.)*[a-zA-Z0-9_-]+)  # nodename (required for match)
    (?::(\\d+))?                            # port (optional)
    (?:/(.*))?                              # path (optional)
    $                                       # must match all
    """, re.VERBOSE)
    __comma_split_pattern = re.compile(",+")
    __tier_pattern = re.compile("[0123]")
    __port_pattern = re.compile(":(\d+)/")

    #Private accessory methods
    def __getSiteInfo(self, entry):
        "Returns info about sites"
        if "GlueSiteUniqueID" in entry[1]:
            if "GlueSiteName" in entry[1]:
                # we retrieve the country, tier and site description values
                sitename                          = entry[1]["GlueSiteName"][0].lower()
                self.__countries[sitename]        = self.__getCountry(entry)
                self.__tiers[sitename]            = self.__getTier(entry)
                self.__sitesdesc[sitename]        = self.__getSiteDescription(entry, sitename)
                self.__sysAdminsContact[sitename] = self.__getSysAdmin(entry)
            else:
                self.__logger.warning("BDII - Execution - Could not get site info from %s" % entry[0])
                return 'Unknown'

          
    def __getCountry(self, entry):
        "Extract only the country name from the given string"
        if "GlueSiteLocation" in entry[1]:
            location_list = self.__comma_split_pattern.split(entry[1]["GlueSiteLocation"][0])
            list_len = len(location_list)
            exp=re.compile('[a-zA-Z\']*')
            blocks=exp.findall(location_list[list_len-1])
            result = ''
            for match in blocks:
                if len(match)>0:
                    result = result + match + ' '
            return result[:-1].lower()
        else:
            self.__logger.warning("BDII - Execution - Could not get country name from %s" % entry[0])
            return 'Unknown'


    def __getTier(self, entry):
        "Extract tier value [0123] from the given string"
        if "GlueSiteOtherInfo" in entry[1]:
            blocks = self.__tier_pattern.findall(entry[1]["GlueSiteOtherInfo"][0])
            if len(blocks) > 0:
                return blocks[0]
            else:
                self.__logger.debug("BDII - Execution - Could not get tier from %s" % entry[1]["GlueSiteOtherInfo"])
                return '3'
        else:
            self.__logger.debug("BDII - Execution - Could not get tier from %s" % entry[0])
            return '3'


    def __getSiteDescription(self, entry, sitename):
        "Extract the site description from the given entry"
        if "GlueSiteDescription" in entry[1]:
            return entry[1]["GlueSiteDescription"][0]
        else:
            self.__logger.warning("BDII - Execution - Could not get site description from %s" % entry[0])
            return sitename


    def __getSysAdmin(self, entry):
        "Extract Sys Admin Contact value from the given string"
        if "GlueSiteSysAdminContact" in entry[1]:
            return entry[1]["GlueSiteSysAdminContact"][0]
        else:
            self.__logger.warning("BDII - Execution - Could not get site admins from %s" % entry[0])
            return 'Unknown'


    def __discoverService(self, entry):
        "Return dict with extracted info for given ldap entry"
        service_type = self.__getType(entry)
        if service_type == None: # unrecognized or uninteresting service type
            self.__logger.debug("BDII - Execution - Could not get service type from %s" % entry[1]['objectClass'])
            return None
        site = self.__getSite(entry)
        if site == None:
            self.__logger.debug("BDII - Execution - Could not get site from %s" % entry[0])
            return None    
        node = self.__getNode(entry)
        if node == None:
            self.__logger.debug("BDII - Execution - Could not get node name from %s" % entry[0])
            return None

        vos = []
        if service_type in self.__vo_dep_services.values(): # vo specific
            # Passing a param to getVos specifying if it's an OSG host or not (so it won't add OPS vo)
            vos = self.__getVos(entry)
            if vos == None or len(vos) == 0:
                return None
        info = self.__getOtherInfo(entry)

        if node:
            service_uri = self.__getServiceURI(entry, node, service_type)
            if service_uri == None:
                self.__logger.warning("Could not get service URI for %s" % entry[0])
                return None

        info["site"] = site
        info["node"] = node
        info["serviceuri"] = service_uri
        info["type"] = service_type
        info["vos"]  = vos

        return info
            
            
    def __getType(self, entry):
        "Returns service type by checking various attributes"
        ldap_type = None

        # CE/SE is not published as GlueService
        if "GlueCE" in entry[1]["objectClass"]:
            ldap_type = self.__getCEType(entry)
        elif "GlueSA" in entry[1]["objectClass"]:
            ldap_type = "dummySE"
        elif "GlueSE" in entry[1]["objectClass"]:
            ldap_type = "dummySE"
        elif "GlueService" in entry[1]["objectClass"]: # for GlueService objects
            if "GlueServiceType" in entry[1]:    # get type from GlueServiceType
                ldap_type = entry[1]["GlueServiceType"][0]
                if (ldap_type.lower() == "srm"):
                    if "GlueServiceVersion" in entry[1]:   # differenciate between SRM v1 and v2
                        ldap_service_ver = entry[1]["GlueServiceVersion"][0]
                        if ldap_service_ver[0] == "2":
                            ldap_type = "srm_v2"
                        if ldap_service_ver[0] == "1":
                            ldap_type = "srm_v1"
        elif "GlueSite" in entry[1]["objectClass"]:
            # site name in dn might be wrong -> get the one in GlueSite
            for attr in ["GlueSiteName"]:
                if attr in entry[1]:
                    self.__site2realname[self.__getSite(entry)] = entry[1][attr][0]
                    break # first attribute wins
                                   
        # map type name to database names
        db_type = None
        if ldap_type != None:
            if ldap_type.lower() in self.__vo_indep_services:
                db_type = self.__vo_indep_services[ldap_type.lower()]
            elif ldap_type.lower() in self.__vo_dep_services:
                db_type = self.__vo_dep_services[ldap_type.lower()]
        return db_type            



    def __getSite(self, entry):
        "Returns site name from LDAP entry dn"
        site = self.__extract(self.__site_pattern, entry[0])
        if site in self.__site2realname: # use the real name if available
            site = self.__site2realname[site]
        return site


    def __getServiceURI(self, entry, node, service_type):
        "Extract ServiceURI value from the given string"
        if service_type in ('SE'):
            if "GlueSEAccessProtocolPort" in entry[1].keys():
                port = entry[1]["GlueSEAccessProtocolPort"][0];
                if port:
                    return node + ":" + port
        elif service_type in ('CE', 'CREAMCE', 'ArcCE'):
            if "GlueCEUniqueID" in entry[1].keys():
                port = self.__extract(self.__port_pattern, entry[1]["GlueCEUniqueID"][0])
                if port:
                    return node + ":" + port
        elif service_type in ('SRM', 'SRMv1', 'SRMv2'):
            if "GlueServiceEndpoint" in entry[1].keys():
                port = self.__extract(self.__port_pattern, entry[1]["GlueServiceEndpoint"][0])
                if port:
                    if service_type in ('SRM', 'SRMv1'):
                        return "httpg://" + node + ":" + port + "/srm/managerv1"
                    else:
                        return "httpg://" + node + ":" + port + "/srm/managerv2"
        elif service_type in ('WMS'):
            if "GlueServiceUniqueID" in entry[1].keys():
                port = self.__extract(self.__port_pattern, entry[1]["GlueServiceUniqueID"][0])
                if port:
                    return node + ":" + port
        else:
            if "GlueServiceEndpoint" in entry[1].keys():
                port = self.__extract(self.__port_pattern, entry[1]["GlueServiceEndpoint"][0])
                if port:
                    return node + ":" + port
        return node


    def __getNode(self, entry):
        "Return node name from various attributes"
        for attr in ["GlueServiceAccessPointURL", "GlueServiceEndpoint", "GlueCEUniqueID", "GlueChunkKey", "GlueSEUniqueID"]:
            if attr in entry[1]:
                # extract node from possible url
                node = self.__extract(self.__node_pattern, entry[1][attr][0])
                if node and node.find(".") > 0: # looks like a fqdn
                    return node.lower()
        return None
        
                 
    def __getVos(self, entry):
        "Return list of supported VOs from various attributes"
        for attr in ["GlueServiceAccessControlRule", "GlueCEAccessControlBaseRule", "GlueSAAccessControlBaseRule", "GlueServiceAccessControlBaseRule"]:
            if attr in entry[1]:
                # CE ACL has 'VO:' in front of vo name
                vo_list = []

                for val in entry[1][attr]:
                    if not self.__cert_pattern.search(val):
                        vo = val 
                        if val.find('VO:') >= 0 :
                            vo = val.replace("VO:", "")
                        else:
                            if val.find('VOMS:/') >= 0 :
                                s = val.split('/')
                                vo = s[1]
                                
                        if vo != '' :
                               if (vo not in vo_list):
                                   vo_list.append(vo)
                return vo_list
        return None
                    
    
    def __getOtherInfo(self, entry):
        "return other info for the service (needed for the FCR tables)"
        other = {"dn": entry[0]}

        if "GlueCEUniqueID" in entry[1]:
            res = self.__node_pattern.search(entry[1]["GlueCEUniqueID"][0])
            if res != None:
                other["port"] = res.groups()[1]
                other["queue"] = res.groups()[2]

        if "GlueSA" in entry[1]["objectClass"]:
            if "GlueSALocalID" in entry[1]:
                other["salocalid"] = entry[1]["GlueSALocalID"][0];
            else:
                other["salocalid"] = None
        
        return other


    def __getCEType(self, entry):
        "returns the type of CE: glite or lcg or cream"
        ce_type = None 

        # check for ARC CE
        for attr in ["GlueCEUniqueID", "GlueCEInfoContactString"]:
            if attr in entry[1]:
                if entry[1][attr][0].find("gsiftp://") == 0:
                    ce_type = "dummyArcCE"
                    return ce_type

        # check for lcg CE
        for attr in ["GlueCEUniqueID", "GlueCEInfoContactString"]:
            if attr in entry[1]:
                if entry[1][attr][0].find("/jobmanager-") > 0:
                    ce_type = "dummyCE"
                    return ce_type

        # check for CREAM CE
        for attr in ["GlueCEUniqueID", "GlueCEInfoContactString"]:
            if attr in entry[1]:
                if entry[1][attr][0].find("/ce-cream") > 0 or entry[1][attr][0].find("/cream-") > 0:
                    ce_type = "dummycreamce"
                    return ce_type

        return ce_type


    def __extract(self, pattern, string):
        "Returns the first element extracted from string by pattern"
        result = pattern.search(string)
        if result != None:
            return result.groups()[0]
        else:
            return None


    def __init__(self, config ):
        "Sets the bdii parameters"              
        self.__ldap_uri= config.bdii_ldap_uri
        self.__ldap_base = config.bdii_ldap_base
        self.__ldap_filter = config.bdii_ldap_filter
        self.__logger = config.logger;

    def checkBDII(self):
        "Checks of BDII service is available"
        try:
            ldap_conn = ldap.initialize(self.__ldap_uri)
            ldap_conn.search_s(self.__ldap_base, ldap.SCOPE_SUBTREE, self.__ldap_filter)
            ldap_conn.unbind()
            return True
        except Exception, e:
            return False
                
    def getServices(self):
        "Returns a list of dictionaries containing information about each grid service described in the input source"
        
        ldap_conn = ldap.initialize(self.__ldap_uri)
        ldap_conn.simple_bind_s("", "")
        service_list = []
        for entry in ldap_conn.search_s(self.__ldap_base, ldap.SCOPE_SUBTREE, self.__ldap_filter):
            service = self.__discoverService(entry)
            self.__getSiteInfo(entry)
            if service:
                service_list.append(service)

        ldap_conn.unbind()
        return service_list
    
    def getMPIServices(self):
        """Returns a list containing tuples -CE-host,MPI_host,MPI-flavour for MPI services in BDII"""
        ldap_conn = ldap.initialize(self.__ldap_uri)
        ldap_conn.simple_bind_s("", "")
        CE_services = ldap_conn.search_s(self.__ldap_base, ldap.SCOPE_SUBTREE, self.__ldap_mpi_filter)
        MPI_services_list=[]
        for entry in CE_services:
            if entry[1].has_key('GlueCEHostingCluster'):
                cluster_name=entry[1]['GlueCEHostingCluster']
                search_str="""(&(objectClass=GlueClusterTop)(GlueChunkKey=GlueClusterUniqueID=%s)(objectclass=GlueHostApplicationSoftware)(GlueHostApplicationSoftwareRunTimeEnvironment=MPI-START))"""%cluster_name[0]
                mpi_services_search=ldap_conn.search_s("mds-vo-name=local,o=grid",ldap.SCOPE_SUBTREE,search_str)
            else:
                self.__logger.debug("MPI services - 'GlueCEHostingCluster' key could not be found for BDII entry -  %s" % entry[1])
                continue
            for MPI_entry in mpi_services_search:
                if MPI_entry[1].has_key('GlueInformationServiceURL'):
                        service_uri = MPI_entry[1]['GlueInformationServiceURL'][0].split('://')[1].split(':')[0]
                else:
                        service_uri=''
                for item in self.__MPI_flavours:
                    MPI_lst=[]
                    for software_packages in MPI_entry[1]['GlueHostApplicationSoftwareRunTimeEnvironment']:
                        if set(software_packages) == set(item):
                            if not service_uri in MPI_lst:
                                if service_uri:
                                    MPI_lst.append(service_uri)
                            if not item in MPI_lst:
                                MPI_lst.append(item)
                                break;
                    if MPI_lst:
                        # CE-host,MPI_host,MPI-flavour
                        # MPI_services_list.append([entry[1]['GlueCEInfoHostName'][0],service_uri,item])
                        # CE-host,MPI-flavour
                        MPI_services_list.append([entry[1]['GlueCEInfoHostName'][0],service_uri,item])
        ldap_conn.unbind()
        #for item in MPI_services_list:
        #    print item
        return MPI_services_list
        
        
        
class DBInput(InputSource):
    "Class to gather data from a database" 
    
    __cursor      = None
    __last_query  = None
    __logger      = None
    __var_pattern = re.compile(":(\w+)")
    __node_pattern = re.compile("""
    ^                                       # must match all
    (?:[a-zA-Z]+=)?                         # for chunk key (GlueSEUniqueID=)
    (?:[a-zA-Z]+://)?                       # protocol (optional)
    ((?:[a-zA-Z0-9_-]+\\.)*[a-zA-Z0-9_-]+)  # nodename (required for match)
    (?::(\\d+))?                            # port (optional)
    (?:/(.*))?                              # path (optional)
    $                                       # must match all
    """, re.VERBOSE)
    
    # Oracle DB Queries
#    __ora_get_sites_sql = """SELECT nls_lower(b.infrastname) infrastname, nls_lower(a.sitename) sitename, b.id infrastid, a.id siteid 
#                             FROM site a, infrastructure b 
#                             WHERE a.infrast_id=b.id"""
#    __ora_get_site_bdiis_sql = """SELECT nls_lower(b.infrastname) infrastname, nls_lower(a.sitename) sitename, a.giisurl 
#                                  FROM site a, infrastructure b 
#                                  WHERE a.infrast_id=b.id"""
#    __ora_get_nodes_sql = """SELECT nls_lower(d.infrastname) infrastname, nls_lower(c.sitename) sitename, a.serviceendpoint 
#                             FROM service a, service_site b, site c, infrastructure d
#                             WHERE b.service_id=a.id AND b.site_id=c.id AND c.infrast_id=d.id"""
    __ora_get_vos_sql = """SELECT nls_lower(voname) voname, id void FROM vo"""
    __ora_get_service_flavours_sql = """SELECT nls_lower(flavourname) flavourname, id void FROM service_type_flavour"""    
    __ora_get_servicevos_sql = """SELECT nls_lower(c.hostname) hostname, nls_lower(d.flavourname) flavourname, nls_lower(b.voname) voname, a.service_id, a.vo_id
                                  FROM service_vo a, vo b, service c, service_type_flavour d
                                  WHERE a.vo_id=b.id
                                    AND a.service_id= c.id
                                    AND c.flavour_id= d.id
                                  ORDER BY hostname, flavourname, voname"""
#    __ora_get_service_names_sql = """SELECT nls_lower(flavourname) flavourname, id flavourid
#                                     FROM service_type_flavour"""
    __ora_get_serviceinstances_sql = """SELECT nls_lower(a.hostname) hostname, nls_lower(b.flavourname) flavourname, a.id serviceid 
                                        FROM service a, service_type_flavour b
                                        WHERE a.flavour_id=b.id"""
    __ora_get_downtimes_sql = """SELECT gocdbpk,id,starttimestamp,endtimestamp FROM downtime """

    __ora_get_ops_groups_site_sql = """ SELECT groupname, id FROM groups WHERE group_type_id IN (SELECT id FROM group_type WHERE NLS_LOWER(typename)=NLS_LOWER('Site')) AND isdeleted='N' AND groupname NOT IN (SELECT sitename FROM site WHERE isdeleted='N') ORDER BY groupname"""

    __ora_get_ops_groups_region_sql = """SELECT groupname,id FROM groups WHERE isdeleted='N' AND group_type_id IN (SELECT id from group_type WHERE NLS_LOWER(typename)='region') """
    __ora_get_ops_groups_tier_sql = """SELECT groupname,id FROM groups WHERE isdeleted='N' AND group_type_id IN (SELECT id from group_type WHERE NLS_LOWER(typename)='tier') """
    __ora_get_ops_groups_federation_sql = """SELECT groupname,id FROM groups WHERE isdeleted='N' AND group_type_id IN (SELECT id from group_type WHERE NLS_LOWER(typename)='federation') """
    __ora_get_ops_sites_federation_sql = """SELECT distinct a.sitename,a.id FROM site a, service_site b WHERE a.id=b.site_id AND b.service_id IN (SELECT service_id FROM vo_service_group WHERE groups_id IN (SELECT id FROM groups WHERE group_type_id IN (SELECT id FROM group_type WHERE NLS_LOWER(typename)= NLS_LOWER('Federation'))))"""
    __ora_get_ops_sites_egi_sql = """SELECT sitename,id FROM site WHERE isdeleted='N' AND infrast_id IN (SELECT id FROM infrastructure WHERE NLS_LOWER(infrastname) = 'egi')"""
    __ora_get_ops_sites_osg_sql = """SELECT sitename,id FROM site WHERE isdeleted='N' AND infrast_id IN (SELECT id FROM infrastructure WHERE NLS_LOWER(infrastname) = 'osg')"""
    #__ora_get_groupnames_vofeed = """SELECT DISTINCT a.groupname,a.id FROM groups a, vo_service_group b WHERE a.id=b.groups_id AND b.vo_id IN (SELECT id FROM vo WHERE voname='alice')"""
    #__ora_get_grouptypes_vofeed = "SELECT distinct a.groupname,c.typename, a.id FROM groups a, vo_service_group b,group_type c WHERE a.id=b.groups_id AND b.vo_id IN (SELECT id FROM vo WHERE voname='alice') AND a.group_type_id=c.id"
#    __ora_get_countries_sql = """SELECT nls_lower(countryname) countryname, id countryid, NLS_LOWER(countryabbr) countryabbr
#                                 FROM country"""

    # MySQL DB Queries
#    __mysql_get_sites_sql = """SELECT lower(b.infrastname) infrastname, lower(a.sitename) sitename, b.id infrastid, a.id siteid 
#                               FROM site a, infrastructure b 
#                               WHERE a.infrast_id=b.id"""
#    __mysql_get_site_bdiis_sql = """SELECT lower(b.infrastname) infrastname, lower(a.sitename) sitename, a.giisurl 
#                                    FROM site a, infrastructure b 
#                                    WHERE a.infrast_id=b.id"""
#    __mysql_get_nodes_sql = """SELECT lower(d.infrastname) infrastname, lower(c.sitename) sitename, a.serviceendpoint 
#                               FROM service a, service_site b, site c, infrastructure d
#                               WHERE b.service_id=a.id AND b.site_id=c.id AND c.infrast_id=d.id"""
    __mysql_get_vos_sql = """SELECT lower(voname) voname, id void FROM vo"""
    __mysql_get_service_flavours_sql = """SELECT lower(flavourname) flavourname, id void FROM service_type_flavour"""    
    __mysql_get_servicevos_sql = """SELECT lower(c.hostname) hostname, lower(d.flavourname) flavourname, lower(b.voname) voname, a.service_id, a.vo_id
                                    FROM service_vo a, vo b, service c, service_type_flavour d
                                    WHERE a.vo_id=b.id
                                      AND a.service_id= c.id
                                      AND c.flavour_id= d.id
                                    ORDER BY hostname, flavourname, voname"""
#    __mysql_get_service_names_sql = """SELECT lower(flavourname) flavourname, id flavourid
#                                       FROM service_type_flavour"""
    __mysql_get_serviceinstances_sql = """SELECT lower(a.hostname) hostname, lower(b.flavourname) flavourname, a.id serviceid 
                                          FROM service a, service_type_flavour b
                                          WHERE a.flavour_id=b.id"""
#    __mysql_get_countries_sql = """SELECT lower(countryname) countryname, id countryid, lower(countryabbr) countryabbr
#                                   FROM country"""
    __mysql_get_downtimes_sql = """SELECT gocdbpk,id,starttimestamp,endtimestamp FROM downtime """
    
#    __mysql_get_ops_groups_site_sql = """SELECT groupname,id FROM groups WHERE group_type_id IN (SELECT id from group_type WHERE lower(typename)='site') """
    __mysql_get_ops_groups_site_sql = """SELECT groupname, id FROM groups WHERE group_type_id IN (SELECT id FROM group_type WHERE LOWER(typename)=LOWER('Site')) AND isdeleted='N' AND groupname NOT IN (SELECT sitename FROM site WHERE isdeleted='N') ORDER BY groupname"""

    __mysql_get_ops_groups_region_sql = """SELECT groupname,id FROM groups WHERE isdeleted='N' AND group_type_id IN (SELECT id FROM group_type WHERE lower(typename)='region') """
    __mysql_get_ops_groups_tier_sql = """SELECT groupname,id FROM groups WHERE isdeleted='N' AND group_type_id IN (SELECT id FROM group_type WHERE lower(typename)='tier') """
    __mysql_get_ops_groups_federation_sql = """SELECT groupname,id FROM groups WHERE isdeleted='N' AND group_type_id IN (SELECT id FROM group_type WHERE lower(typename)='federation') """
    __mysql_get_ops_sites_federation_sql = """SELECT distinct a.sitename,a.id FROM site a, service_site b WHERE a.id=b.site_id AND b.service_id IN (SELECT service_id FROM vo_service_group WHERE groups_id IN (SELECT id FROM groups WHERE group_type_id IN (SELECT id FROM group_type WHERE LOWER(typename)= LOWER('Federation'))))"""
    __mysql_get_ops_sites_egi_sql = """SELECT sitename,id FROM site WHERE isdeleted='N' AND infrast_id IN (SELECT id FROM infrastructure WHERE lower(infrastname) = 'egi')"""
    __mysql_get_ops_sites_osg_sql = """SELECT sitename,id FROM site WHERE isdeleted='N' AND infrast_id IN (SELECT id FROM infrastructure WHERE lower(infrastname) = 'osg')"""
    
    def __init__(self, config, cursor ):
        "Sets the DB parameters"
        self.__logger = config.logger
        self.__cursor = cursor
        self.__db_type= config.database_type


    def __getDict(self, query, bind_vars=dict(), nkeys=1):
        "Returns results of a query as a dictionary with first n values as the key"
        self.__runQuery(query, bind_vars)
        result = {}

        if self.__last_query != None:
            return result

        try:
            row = self.__cursor.fetchone()

            while row:
                key = row[:nkeys]
                val = row[nkeys:]
                key = len(key) == 1 and key[0] or key
                val = len(val) == 1 and val[0] or val
                result[key] = val
                row = self.__cursor.fetchone()
        except Exception, info:
            self.__logger.debug("No rows returned")

        return result


    def __runQuery(self, query, bind_vars=dict()):
        "Runs query on database using bind variables"
        # pass only the vars the query mentions or oracle will choke
        qvars = {}
        for var in re.findall(self.__var_pattern, query):
            if var not in bind_vars:
                self.__logger.warning("Undefined bind variable: %s" % var)
                return
            qvars[var] = bind_vars[var]
        self.__last_query = "%s %s" % (query, qvars) # display it on error
        #self.__logger.debug("Executing query: %s" % self.__last_query.strip())
        try:
            self.__cursor.execute(query, qvars)
            self.__last_query = None # clear if no exception
        except Exception, info:
            self.__logger.debug("Generic - RunQuery - Error executing last query: %s" % info)


    def getServiceVOs(self):
        "Gets serviceVOs from DB"
        if self.__db_type == 'mysql':        
            vos = self.__getDict(self.__mysql_get_servicevos_sql, nkeys=3)
        else:
            vos = self.__getDict(self.__ora_get_servicevos_sql, nkeys=3)
        return vos

                    
    def getVOs(self):
        "Gets VOs from DB"
        if self.__db_type == 'mysql': 
            vos = self.__getDict(self.__mysql_get_vos_sql)
        else:
            vos = self.__getDict(self.__ora_get_vos_sql)
        return vos

    def getServiceFlavours(self):
        "Gets service flavours from DB"
        if self.__db_type == 'mysql': 
            vos = self.__getDict(self.__mysql_get_service_flavours_sql)
        else:
            vos = self.__getDict(self.__ora_get_service_flavours_sql)
        return vos


    def getServiceIDs(self):
        "Gets service endpoints and flavours from db"
        if self.__db_type == 'mysql':
            ids = self.__getDict(self.__mysql_get_serviceinstances_sql, nkeys=2)
        else:
            ids = self.__getDict(self.__ora_get_serviceinstances_sql, nkeys=2)
        return ids;

    def getDowntimeIDs(self):
        "Gets existing downtime info. from the db"
        if self.__db_type == 'mysql':
            downtimes = self.__getDict(self.__mysql_get_downtimes_sql, nkeys=1)
        else:
            downtimes = self.__getDict(self.__ora_get_downtimes_sql, nkeys=1)
        return downtimes;

    def getOPS_Sites(self,infrast_name):
        "Gets groups(virtual-sites) from DB"
        if self.__db_type == 'mysql':
            
                ops_sites = self.__getDict(self.__mysql_get_ops_groups_site_sql, nkeys=1)
            
        else:
                ops_sites = self.__getDict(self.__ora_get_ops_groups_site_sql, nkeys=1)
            
        return ops_sites

    def getOPS_PhySites(self,infrast_name):
        "Gets physical sites from DB"
        if self.__db_type == 'mysql':
            if infrast_name.lower()=='egi': 
                ops_sites = self.__getDict(self.__mysql_get_ops_sites_egi_sql, nkeys=1)
            else:
                ops_sites = self.__getDict(self.__mysql_get_ops_sites_osg_sql, nkeys=1)
        else:
            if infrast_name.lower()=='egi': 
                ops_sites = self.__getDict(self.__ora_get_ops_sites_egi_sql, nkeys=1)
            else:
                ops_sites = self.__getDict(self.__ora_get_ops_sites_osg_sql, nkeys=1)
        return ops_sites
    
    def getOPS_Regions(self):
        "Gets groups(regions) from DB"
        if self.__db_type == 'mysql': 
            ops_regions = self.__getDict(self.__mysql_get_ops_groups_region_sql, nkeys=1)
        else:
            ops_regions = self.__getDict(self.__ora_get_ops_groups_region_sql, nkeys=1)
        return ops_regions
    
    def getOPS_Tiers(self):
        "Gets groups(tiers) from DB"
        if self.__db_type == 'mysql': 
            ops_tiers = self.__getDict(self.__mysql_get_ops_groups_tier_sql, nkeys=1)
        else:
            ops_tiers = self.__getDict(self.__ora_get_ops_groups_tier_sql, nkeys=1)
        return ops_tiers
    
    def getOPS_Federations(self):
        "Gets groups(federations) from DB"
        if self.__db_type == 'mysql': 
            ops_federations = self.__getDict(self.__mysql_get_ops_groups_federation_sql, nkeys=1)
        else:
            ops_federations = self.__getDict(self.__ora_get_ops_groups_federation_sql, nkeys=1)
        return ops_federations
    
    def getOPS_SitesInFederation(self):
        "get sites in federations from DB"
        if self.__db_type == 'mysql': 
            ops_siteinfederations = self.__getDict(self.__mysql_get_ops_sites_federation_sql, nkeys=1)
        else:
            ops_siteinfederations = self.__getDict(self.__ora_get_ops_sites_federation_sql, nkeys=1)
        return ops_siteinfederations

    def getGroupnames_VOFeed(self,vo_name):
        "Gets groupnames for a given VO feed"
        groupnames_vofeed = {}
        if self.__db_type == 'mysql':
            self.__mysql_get_groupnames_vofeed = """SELECT DISTINCT a.groupname,a.id FROM groups a, vo_service_group b WHERE a.id=b.groups_id AND b.vo_id in (SELECT id FROM vo WHERE LOWER(voname)=LOWER('%s'))"""%vo_name
            groupnames_vofeed = self.__getDict(self.__mysql_get_groupnames_vofeed, nkeys=1)
        else:
            self.__ora_get_groupnames_vofeed = """SELECT DISTINCT a.groupname,a.id FROM groups a, vo_service_group b WHERE a.id=b.groups_id AND b.vo_id in (SELECT id FROM vo WHERE NLS_LOWER(voname)=NLS_LOWER('%s'))"""%vo_name
            groupnames_vofeed = self.__getDict(self.__ora_get_groupnames_vofeed, nkeys=1)
        return groupnames_vofeed
    
    def getGrouptypes_VOFeed(self,vo_name):
        "Gets group_type for a given VO feed"
        grouptypes_vofeed = {}
        if self.__db_type == 'mysql':
            self.__mysql_get_grouptypes_vofeed = """SELECT DISTINCT c.typename FROM groups a, vo_service_group b,group_type c WHERE a.id=b.groups_id AND b.vo_id IN (SELECT id FROM vo WHERE LOWER(voname)=LOWER('%s')) AND a.group_type_id=c.id"""%vo_name
            grouptypes_vofeed = self.__getDict(self.__mysql_get_grouptypes_vofeed, nkeys=1)
        else:
            self.__ora_get_grouptypes_vofeed = """SELECT DISTINCT c.typename FROM groups a, vo_service_group b,group_type c WHERE a.id=b.groups_id AND b.vo_id IN (SELECT id FROM vo WHERE NLS_LOWER(voname)=NLS_LOWER('%s')) AND a.group_type_id=c.id"""%vo_name
            grouptypes_vofeed = self.__getDict(self.__ora_get_grouptypes_vofeed, nkeys=1)
        return grouptypes_vofeed
    
    def getServiceGroups_VOFeed(self,vo_name):
        "Gets existing service-groups mappings in the given VO feed"
        servicegroups_vofeed = {}
        if self.__db_type == 'mysql':
            self.__mysql_get_servicegroups_vofeed = """SELECT DISTINCT a.hostname, b.flavourname,c.groupname,d.typename,e.id FROM service a ,service_type_flavour b,groups c, group_type d, vo_service_group e WHERE a.isdeleted='N' AND a.flavour_id=b.id AND c.id=e.groups_id  AND c.group_type_id= d.id AND a.id=e.service_id AND e.vo_id IN (SELECT id FROM vo WHERE LOWER(voname) = LOWER('%s'))"""%vo_name
            servicegroups_vofeed = self.__getDict(self.__mysql_get_servicegroups_vofeed, nkeys=4)
        else:
            self.__ora_get_servicegroups_vofeed = """SELECT DISTINCT a.hostname, b.flavourname,c.groupname,d.typename,e.id FROM service a ,service_type_flavour b,groups c, group_type d, vo_service_group e WHERE a.isdeleted='N' AND a.flavour_id=b.id AND c.id=e.groups_id  AND c.group_type_id= d.id AND a.id=e.service_id AND e.vo_id IN (SELECT id FROM vo WHERE NLS_LOWER(voname) = NLS_LOWER('%s'))"""%vo_name
            servicegroups_vofeed = self.__getDict(self.__ora_get_servicegroups_vofeed, nkeys=4)
        return servicegroups_vofeed
    
    def getServices_VOFeed(self,vo_name):
        "Gets existing service-groups mappings in the given VO feed"
        services_vofeed = {}
        if self.__db_type == 'mysql':
            self.__mysql_get_services_vofeed = """SELECT DISTINCT a.hostname,c.flavourname,b.id from service a, vo_service_group b, service_type_flavour c WHERE a.flavour_id=c.id AND a.id=b.service_id AND a.isdeleted='N' AND vo_id in (SELECT id from vo WHERE LOWER(voname) = LOWER('%s'))"""%vo_name
            services_vofeed = self.__getDict(self.__mysql_get_services_vofeed, nkeys=1)
        else:
            self.__ora_get_services_vofeed = """SELECT DISTINCT a.hostname,c.flavourname,b.id from service a, vo_service_group b, service_type_flavour c WHERE a.flavour_id=c.id AND a.id=b.service_id AND a.isdeleted='N' AND vo_id in (SELECT id from vo WHERE NLS_LOWER(voname) = NLS_LOWER('%s'))"""%vo_name
            services_vofeed = self.__getDict(self.__ora_get_services_vofeed, nkeys=1)
        return services_vofeed
