##############################################################################
#
# NAME:        output.py
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
# MODIFIED:     July 29,2010
#
##############################################################################

import re
import string
from datetime import datetime
import os

class OutputSource (object):
    "An abstract class to define the methods that should be provided by an Output source"

    def updateSites(self, GOCDB_Sites, Infrast_name, Data_Provider):
        "Updates sites info. in output source with the data from the input sources"
        raise NotImplementedError( 'updateSites should be overriden in subclass')

    def updateServiceEndPoints(self, GOCDB_ServiceEndPoints, Infrast_name, Data_Provider):
        "Updates service endpoints in output source with the data from the input sources"
        raise NotImplementedError( 'updateServiceEndPoints should be overriden in subclass')

    def updateServiceFlavours(self, GOCDB_ServiceFlavours, Infrast_name, Data_Provider):
        "Updates service flavours in output source with the data from the input sources"
        raise NotImplementedError( 'updateServiceFlavours should be overriden in subclass')

    def updateDowntimes(self, GOCDB_Downtimes, Infrast_name, Data_Provider):
        "Updates downtimes in output source with the data from the input sources"
        raise NotImplementedError( 'updateDowntimes should be overriden in subclass')
    
    def updateGSTATCPUCounts(self, SiteCPU_Feed, Data_Provider):
        "Updates site CPU counts in output source with the data from the input sources"
        raise NotImplementedError( 'updateGSTATCPUCounts should be overriden in subclass')

    def updateOSGResources(self, OSG_resources_list, Infrast_name, Data_Provider):
        "Updates OSG resources list in output source with the data from the input sources"
        raise NotImplementedError( 'updateOSGResources should be overriden in subclass')

    def updateOSGKSI2K(self, OSG_resources_list):
        "Updates OSG KSI2K values in output source with the data from the input sources"
        raise NotImplementedError( 'updateOSGKSI2K should be overriden in subclass')

    def updateServiceVOs(self, services, dbInput):
        "Updates the service VOs in output source with the data from the input sources"
        raise NotImplementedError( 'updateServiceVOs should be overriden in subclass')

    def updateVOs(self, vos):
        "Updates the VOs in output source with the data from the input sources"
        raise NotImplementedError( 'updateVOs should be overriden in subclass')

    def updateTiers_And_Federations(self, TierFederation_info, Data_Provider):
        """Updates Tier and Federation information in the database"""
        raise NotImplementedError( 'updateTiers_And_Federations should be overriden in subclass')

    def updateServiceVOFeeds(self,VO_Feed_list,voname):
        """Updates service vo mappings from the VO feed"""
        raise NotImplementedError( 'updateServiceVOFeeds should be overriden in subclass')

    def updateVOGroupings(self,VO_sitegroups_list):
        """updates VO groupings in the database"""
        raise NotImplementedError( 'updateVOGroupings should be overriden in subclass')

    def updateMPIServices(self, MPI_services, data_provider):
        """updates MPI services in the database"""
        raise NotImplementedError( 'updateMPIServices should be overriden in subclass')
    
class DBOutput(OutputSource):

    __limit                = 1000
    __config               = None
    __cursor               = None
    __logger               = None
    __last_query           = None
    __service2id           = {}
    __vo2id                = {}
    __allVOs               = {}
    __DowntimesInDB        = {}
    __sites2id             = {}
    __group_sites2id       = {}
    __group_regions2id     = {}
    __group_tiers2id       = {}
    __group_federations2id = {}
    __vofeeds_groupname2id = {}
    __vofeeds_grouptypes   = {}
    __var_pattern          = re.compile(":(\w+)")
    
    bdii_synchro_status               = 'N'
    gocdb_topo_synchro_status         = 'N'
    gocdb_downtime_synchro_status     = 'N'
    gstat_synchro_status              = 'N'
    osg_synchro_status                = 'N'
    osg_downtime_synchro_status       = 'N'
    cic_synchro_status                = 'N'
    vofeeds_synchro_status            = 'N'
    
    __mysql_create_servicevo_sql = """INSERT INTO service_vo(service_id, vo_id) VALUES (%s, %s)"""
    __ora_create_servicevo_sql   = """INSERT INTO service_vo(service_id, vo_id) VALUES (:service_id, :vo_id)"""
    
    def __runQuery(self, query, bind_vars):
        "run query on database using bind variables"

        if self.__config.database_type == 'mysql':
            bind_var_values=(bind_vars)
            self.__last_query = "%s %s" % (query, bind_var_values) # display it on error
            #self.__logger.debug("Generic - Run Query - %s" % self.__last_query.strip())
            try:
                self.__cursor.execute(query, bind_var_values)
                self.__last_query = None # clear if no exception
            except Exception, info:
                self.__logger.error("Generic - Run Query - %s" % (str(info) + ':' + str(bind_var_values)))
        else:
            qvars = {}
            for var in re.findall(self.__var_pattern, query):
                if var not in bind_vars:
                    self.__logger.error("Generic - Run Query - Undefined bind variable: %s when executing query: %s - bind_vars: %s" % (var, query, bind_vars))
                    return
                qvars[var] = bind_vars[var]
            self.__last_query = "%s %s" % (query, qvars) # display it on error
            #self.__logger.debug("Executing query: %s" % self.__last_query.strip())
            try:
                self.__cursor.execute(query, qvars)
                self.__last_query = None # clear if no exception
            except Exception, info:
                self.__logger.error("Generic - Run Query - Error %s" % (str(info) + ':' + str(qvars)))


    def __init__(self, config, cursor ):
        "Sets the DB parameters"
        self.__logger = config.logger
        self.__cursor = cursor
        self.__config = config


    def updateSynchronizerlastrun(self, synchro_name, synchro_status,sync_update_timestamp):
        """ records state of last sucessful run of all ATP synchronizers with timestamp"""
        try:
            if self.__config.database_type != 'mysql':
                synchro_list=[]
                synchro_list.append (synchro_name)
                synchro_list.append (synchro_status)
                synchro_list.append (sync_update_timestamp)
                self.__cursor.callproc('SYNCHRONIZER_LASTRUN_UPDATE', synchro_list)
                self.__last_query = None # clear if no exception
            else:
                self.__cursor.execute("""CALL SYNCHRONIZER_LASTRUN_UPDATE(%s,%s,%s)""",(synchro_name,synchro_status,sync_update_timestamp))
                self.__last_query = None # clear if no exception

        except Exception, info:
            self.__logger.error("DB error while executing last query: %s" % info)

    def updateVOs(self, vosInCICDB, dbInput):
        "updates the VO information"

        # reset VO synchronizer state
        self.cic_synchro_status = 'N'

        # get the existing list of vos in the DB
        self.__vosInDB = dbInput.getVOs()
      
        # add or update VOs found in the CIC feed
        new_vos = []
        for v in vosInCICDB:
            vo = v.lower()
            if vo not in [x.lower() for x in self.__vosInDB.keys()]:
                # This VO is not defined in the DB, so we must add it
                new_vos.append(v)
            if self.__config.database_type == 'mysql':
                try:
                    self.__cursor.execute("""CALL VO_UPDATE(%s)""",v)
                    self.__last_query = None # clear if no exception
                except Exception, info:
                    self.__logger.error("DB error while executing VO_UPDATE procedure for VO - %s. Error message is: %s" %(v,info))
            else:
                try:
                    import cx_Oracle
                    self.__cursor.callproc('VO_UPDATE', [v])
                    self.__last_query = None # clear if no exception
                except Exception, info:
                    self.__logger.error("DB error while executing VO_UPDATE procedure for VO- %s. Error message is: %s" % (v, info))
        self.__logger.debug("CIC - Execution - New VOs added: %s" % new_vos)

        # gets all the VOs we have now
        if len(new_vos) > 0 :
            self.__vosInDB = dbInput.getVOs()
        self.__logger.debug("CIC - Execution - VOs in the DB: %s" % self.__vosInDB)

        # remove VOs that are in the DB but not in the CIC feed
        for v in vosInCICDB:
            if v in self.__vosInDB.keys():
                del self.__vosInDB[v]
        
        # check if there are vos to be deleted
        if self.__vosInDB:
            for key,value in self.__vosInDB.items():
                #key-vo-name, value-vo-id
                if self.__config.database_type != 'mysql':
                    import cx_Oracle
                    delete_entry=[]
                    delete_entry.append(value)
                    try:
                        self.__cursor.callproc('MARK_VOGROUPS_AS_DELETED', delete_entry)
                        self.__last_query = None # clear if no exception
                        #if procedure_result.getvalue()!=1.0:
                        #    self.__logger.error("Possible problem in executing 'MARK_VOGROUPS_AS_DELETED' procedure for entry %s" % delete_entry)
                    except Exception, info:
                        self.__logger.error("DB error while executing MARK_VOGROUPS_AS_DELETED procedure with parameters %s. Error message is: %s" % (delete_entry, info))
                else:
                    try:
                        self.__cursor.execute("""CALL MARK_VOGROUPS_AS_DELETED(%s)""",(value))
                        self.__last_query = None # clear if no exception
                        #self.__cursor.execute('SELECT @sucess_flag')
                        #if self.__cursor.fetchone()[0]!=1:
                        #    self.__logger.error("Possible problem in executing 'MARK_VOGROUPS_AS_DELETED' procedure for entry (%s)" % (value))
                    except Exception, info:
                        self.__logger.error("DB error while executing MARK_VOGROUPS_AS_DELETED(%s). Error message is: %s" % (value, info))
  
        # set VO synchronizer state
        self.cic_synchro_status = 'Y'

    def updateVOMSContacts(self, VOMSContacts, dbInput):
        "updates voms contatcs information"

        # reset VO synchronizer state
        self.cic_synchro_status = 'N'

        new_voms = []
        for vomses in VOMSContacts:
            new_voms.append(vomses[0])
            for voms in vomses[1]:
                if self.__config.database_type == 'mysql':
                    try:
                        self.__cursor.execute("""CALL VOMS_CONTACTS_UPDATE(%s,%s,%s)""",(vomses[0],voms['dn'].encode('latin1','ignore'),voms['mail'].encode('latin1','ignore')))
                        self.__last_query = None 
                    except Exception, info:
                        self.__logger.error("DB error while executing VOMS_CONTACTS_UPDATE procedure for voms contact. Error message is: %s." %(info))
                else:
                    sf_entry = []
                    sf_entry.append(vomses[0])
                    sf_entry.append(voms['dn'].encode('latin1','ignore'))
                    sf_entry.append(voms['mail'].encode('latin1','ignore'))
                    try:
                        import cx_Oracle
                        self.__cursor.callproc('VOMS_CONTACTS_UPDATE', sf_entry)
                        self.__last_query = None 
                    except Exception, info:
                        self.__logger.error("DB error while executing VOMS_CONTACTS_UPDATE procedure for voms contact. Error message is: %s." % (info))

        self.__logger.debug("CIC - Execution - VOMS contacts updated for VOs: %s",new_voms)

        # set VO synchronizer state
        self.cic_synchro_status = 'Y'

    def updateServiceFlavours(self, GOCDB_ServiceFlavours, dbInput):
        "updates the service flavours information"

        # reset VO synchronizer state
        self.cic_synchro_status = 'N'

        # get the existing list of vos in the DB
        self.__serviceFlavoursInDB = dbInput.getServiceFlavours()

        # add or update 
        new_service_flavours = []
        for sf in GOCDB_ServiceFlavours:
            sfl = sf['service_type_name'].lower()
            if sfl not in [x.lower() for x in self.__serviceFlavoursInDB.keys()]:
                new_service_flavours.append(sf)

                # updates service flavour
                if self.__config.database_type == 'mysql':
                    try:
                        self.__cursor.execute("""CALL SERVICE_FLAVOUR_UPDATE(%s)""",(sf['service_type_name']))
                        self.__last_query = None 
                    except Exception, info:
                        self.__logger.error("DB error while executing SERVICE_FLAVOUR_UPDATE procedure for service flavour %s. Error message is: %s," %(sf['service_type_name'],info))
                else:
                    sf_entry = []
                    sf_entry.append(sf['service_type_name'])
                    try:
                        import cx_Oracle
                        self.__cursor.callproc('SERVICE_FLAVOUR_UPDATE', sf_entry)
                        self.__last_query = None 
                    except Exception, info:
                        self.__logger.error("DB error while executing SERVICE_FLAVOUR_UPDATE procedure for service flavour %s. Error message is: %s," % (sf_entry, info))

        self.__logger.debug("GOCDB Topology - Execution - Service flavours added: %s" % new_service_flavours)

        # set VO synchronizer state
        self.cic_synchro_status = 'Y'

    def deleteInvalidGOCDBEntries(self, Sites_list, Infrast_name, Data_Provider, dbInput):
        # get the existing list of Phy. sites in the DB
        self.__sites2id = dbInput.getOPS_PhySites(Infrast_name)

        # get the existing list of groups(virtual-sites) in the DB
        self.__group_sites2id = dbInput.getOPS_Sites(Infrast_name)
        
        # get the existing list of groups(regions) in the DB
        self.__group_regions2id = dbInput.getOPS_Regions()
        
        # regions - OSG and Unknown always exists.So, don't consider them when setting isdeleted='Y' or isdeleted='N'  
        if self.__group_regions2id.has_key('OSG'):
            del self.__group_regions2id['OSG'] 
        if self.__group_regions2id.has_key('Unknown'):
            del self.__group_regions2id['Unknown']
        
        for roc_sites in Sites_list:
            for site in roc_sites:
                # remove entry if it exists in the feed
                if site['sitename'] in self.__sites2id.keys():
                    del self.__sites2id[site['sitename']]

                if site['sitename'] in self.__group_sites2id.keys():
                    del self.__group_sites2id[site['sitename']]

                if site['roc'] in self.__group_regions2id.keys():
                    del self.__group_regions2id[site['roc']]
        
        # check if there are phy. sites to be deleted
        if self.__sites2id:
            self.__logger.info('GOCDB Topology - Execution - The following sites are no longer valid and will be marked as deleted')
            for key,value in self.__sites2id.items():
                self.__logger.info('GOCDB Topology - Execution - %s' % key)
                #key-site, value-id
                if self.__config.database_type != 'mysql':
                    import cx_Oracle
                    delete_entry=[]
                    delete_entry.append(value)
                    try:
                        self.__cursor.callproc('MARK_SITES_AS_DELETED', delete_entry)
                        self.__last_query = None # clear if no exception
                        #if procedure_result.getvalue()!=1.0:
                        #    self.__logger.debug("Possible problem in executing 'MARK_SITES_AS_DELETED' procedure for entry %s" % delete_entry)
                    except Exception, info:
                        self.__logger.error("DB error while executing MARK_SITES_AS_DELETED procedure with parameters %s. Error message is: %s" % (delete_entry, info))
                else:
                    try:
                        self.__cursor.execute("""CALL MARK_SITES_AS_DELETED(%s)""",(value))
                        self.__last_query = None # clear if no exception
                        #self.__cursor.execute('SELECT @sucess_flag')
                        #if self.__cursor.fetchone()[0]!=1:
                        #    self.__logger.debug("Possible problem in executing 'MARK_SITES_AS_DELETED' procedure for entry (%s)" % (value))
                    except Exception, info:
                        self.__logger.error("DB error while executing MARK_SITES_AS_DELETED(%s). Error message is: %s" % (value, info))
                        
        # check if there are groups(virtual-sites) to be deleted
        if self.__group_sites2id:
            self.__logger.info('GOCDB Topology - Execution - The following sites/groups are no longer valid and will be marked as deleted')
            for key,value in self.__group_sites2id.items():
                self.__logger.info('GOCDB Topology - Execution - %s' % key)
                #key-virtual-site, value-groups-id
                if self.__config.database_type != 'mysql':
                    import cx_Oracle
                    delete_entry=[]
                    delete_entry.append(value)
                    delete_entry.append('site')
                    try:
                        self.__cursor.callproc('MARK_GROUPS_AS_DELETED', delete_entry)
                        self.__last_query = None # clear if no exception
                        #if procedure_result.getvalue()!=1.0:
                        #    self.__logger.debug("Possible problem in executing 'MARK_GROUPS_AS_DELETED' procedure for entry %s" % delete_entry)
                    except Exception, info:
                        self.__logger.error("DB error while executing MARK_GROUPS_AS_DELETED procedure with parameters %s. Error message is: %s" % (delete_entry, info))
                else:
                    try:
                        self.__cursor.execute("""CALL MARK_GROUPS_AS_DELETED(%s,%s)""",(value,'site'))
                        self.__last_query = None # clear if no exception
                        #self.__cursor.execute('SELECT @sucess_flag')
                        #if self.__cursor.fetchone()[0]!=1:
                        #    self.__logger.debug("Possible problem in executing 'MARK_GROUPS_AS_DELETED' procedure for entry (%s,%s)" % (value,'site'))
                    except Exception, info:
                        self.__logger.error("DB error while executing MARK_GROUPS_AS_DELETED(%s,%s). Error message is: %s" % (value,'site', info))
  
      # check if there are groups(regions) to be deleted
        if self.__group_regions2id:
            self.__logger.info('GOCDB Topology - Execution - The following regions are no longer valid and will be marked as deleted')
            for key,value in self.__group_regions2id.items():
                self.__logger.info('GOCDB Topology - Execution - %s' % key)
                #key-region, value-groups-id
                if self.__config.database_type != 'mysql':
                    import cx_Oracle
                    delete_entry=[]
                    delete_entry.append(value)
                    delete_entry.append('region')
                    try:
                        self.__cursor.callproc('MARK_GROUPS_AS_DELETED', delete_entry)
                        self.__last_query = None # clear if no exception
                        #if procedure_result.getvalue()!=1.0:
                        #    self.__logger.debug("Possible problem in executing 'MARK_GROUPS_AS_DELETED' procedure for entry %s" % delete_entry)
                    except Exception, info:
                        self.__logger.error("DB error while executing MARK_GROUPS_AS_DELETED procedure with parameters %s. Error message is: %s" % (delete_entry, info))
                else:
                    try:
                        self.__cursor.execute("""CALL MARK_GROUPS_AS_DELETED(%s,%s)""",(value,'region'))
                        self.__last_query = None # clear if no exception
                        #self.__cursor.execute('SELECT @sucess_flag')
                        #if self.__cursor.fetchone()[0]!=1:
                        #    self.__logger.debug("Possible problem in executing 'MARK_GROUPS_AS_DELETED' procedure for entry (%s,%s)" % (value,'region'))
                    except Exception, info:
                        self.__logger.error("DB error while executing MARK_GROUPS_AS_DELETED(%s,%s). Error message is: %s" % (value,'region', info))
            
    def updateSites(self, GOCDB_Sites, Infrast_name, Data_Provider, dbInput):
        "updates sites information in ATP DB"

        # reset GOCDB topo synchronizer state
        self.gocdb_topo_synchro_status = 'N'
        
#        # get the existing list of Phy. sites in the DB
#        self.__sites2id = dbInput.getOPS_PhySites(Infrast_name)
#
#        # get the existing list of groups(virtual-sites) in the DB
#        self.__group_sites2id = dbInput.getOPS_Sites(Infrast_name)
#
#        # get the existing list of groups(regions) in the DB
#        self.__group_regions2id = dbInput.getOPS_Regions()
#        
#        # regions - OSG and Unknown always exists.So, don't consider them when setting isdeleted='Y' or isdeleted='N'  
#        if self.__group_regions2id.has_key('OSG'):
#            del self.__group_regions2id['OSG'] 
#        if self.__group_regions2id.has_key('Unknown'):
#            del self.__group_regions2id['Unknown']
        
        for site in GOCDB_Sites:
            # do not run the loop for the sites having 'certification' status as 'closed'.
            #if site['certifstatus'].lower() == 'closed':
            #    continue
            # change certifstatus to 'Y or 'N' depending on site is certified or not
            if site['certifstatus'] and site['certifstatus'].lower() == 'certified':
               site['certifstatus'] = 'Y'
            else:
                site['certifstatus'] = 'N'

            #check if siteoffname and country - not None
            if not site['siteoffname']:
                site['siteoffname'] =''
            if not site['countryname']:
                site['countryname'] =''

#            # remove entry if it exists in the feed
#            if site['sitename'] in self.__sites2id.keys():
#                del self.__sites2id[site['sitename']]
#
#            if site['sitename'] in self.__group_sites2id.keys():
#                del self.__group_sites2id[site['sitename']]
#
#            if site['roc'] in self.__group_regions2id.keys():
#                del self.__group_regions2id[site['roc']]
                
            if self.__config.database_type != 'mysql':
                import cx_Oracle
                procedure_result = self.__cursor.var(cx_Oracle.NUMBER)
                #prepare a site-entry list to be passed to oracle procedure
                site_entry = []
                site_entry.append(Infrast_name)
                site_entry.append(site['sitename'])
                site_entry.append(str(site['siteoffname'].decode('ascii','ignore')))
                site_entry.append('')
                site_entry.append(Data_Provider)
                site_entry.append(str(site['countryname'].decode('ascii','ignore')))
                site_entry.append(site['certifstatus'])
                site_entry.append(site['infrasttype'])
                site_entry.append(site['latitude'])
                site_entry.append(site['longitude'])
                site_entry.append(site['contactemail'])
                site_entry.append(site['contacttel'])
                site_entry.append(site['timezone'])
                site_entry.append(site['giisurl'])
                site_entry.append(site['gocsiteid'])
                site_entry.append(site['roc'])
                site_entry.append(site['gocdbprimarykey'])
                site_entry.append(site['site_abbr'])
                site_entry.append(procedure_result)# place holder for output result parameter

                try:
                    # truncate tmp_sites table used for handling change of sitename issue for GOCDB
                    #self.__cursor.callproc('TRUNCATE_TMP_SITES');
                    #self.__cursor.execute('COMMIT');
                    self.__cursor.callproc('SITE_UPDATE', site_entry)
                    self.__last_query = None # clear if no exception
                    if procedure_result.getvalue()!=1.0:
                        self.__logger.debug("Possible problem in executing 'SITE_UPDATE' procedure for entry %s" % site_entry)
                except Exception, info:
                    self.__logger.error("DB error while executing SITE_UPDATE procedure with parameters %s. Error message is: %s" % (site_entry, info))
            else:
                try:
                    self.__cursor.execute("""CALL SITE_UPDATE(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,@sucess_flag)""",(Infrast_name,site['sitename'],str(site['siteoffname'].decode('ascii','ignore')),'',Data_Provider,str(site['countryname'].decode('ascii','ignore')),site['certifstatus'],site['infrasttype'],site['latitude'],site['longitude'],site['contactemail'],site['contacttel'],site['timezone'],site['giisurl'],site['gocsiteid'],site['roc'],site['gocdbprimarykey'],site['site_abbr']))
                    self.__last_query = None # clear if no exception
                    self.__cursor.execute('SELECT @sucess_flag')
                    if self.__cursor.fetchone()[0]!=1:
                        self.__logger.debug("Possible problem in executing 'SITE_UPDATE' procedure for entry (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)" % (Infrast_name, site['sitename'], str(site['siteoffname'].decode('ascii','ignore')), '', Data_Provider, str(site['countryname'].decode('ascii','ignore')), site['certifstatus'], site['infrasttype'], site['latitude'], site['longitude'], site['contactemail'], site['contacttel'], site['timezone'], site['giisurl'], site['gocsiteid'], site['roc'], site['gocdbprimarykey'], site['site_abbr']))
                except Exception, info:
                    self.__logger.error("DB error while executing SITE_UPDATE(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s). Error message is: %s" % (Infrast_name, site['sitename'], str(site['siteoffname'].decode('ascii','ignore')), '', Data_Provider, str(site['countryname'].decode('ascii','ignore')), site['certifstatus'], site['infrasttype'], site['latitude'], site['longitude'], site['contactemail'], site['contacttel'], site['timezone'], site['giisurl'], site['gocsiteid'], site['roc'], site['gocdbprimarykey'], site['site_abbr'], info))
        
#        # check if there are phy. sites to be deleted
#        if self.__sites2id:
#            self.__logger.info('GOCDB Topology - Execution - The following sites are no longer valid and will be marked as deleted')
#            for key,value in self.__sites2id.items():
#                self.__logger.info('GOCDB Topology - Execution - %s' % key)
#                #key-site, value-id
#                if self.__config.database_type != 'mysql':
#                    import cx_Oracle
#                    delete_entry=[]
#                    delete_entry.append(value)
#                    try:
#                        self.__cursor.callproc('MARK_SITES_AS_DELETED', delete_entry)
#                        self.__last_query = None # clear if no exception
#                        #if procedure_result.getvalue()!=1.0:
#                        #    self.__logger.debug("Possible problem in executing 'MARK_SITES_AS_DELETED' procedure for entry %s" % delete_entry)
#                    except Exception, info:
#                        self.__logger.error("DB error while executing MARK_SITES_AS_DELETED procedure with parameters %s. Error message is: %s" % (delete_entry, info))
#                else:
#                    try:
#                        self.__cursor.execute("""CALL MARK_SITES_AS_DELETED(%s)""",(value))
#                        self.__last_query = None # clear if no exception
#                        #self.__cursor.execute('SELECT @sucess_flag')
#                        #if self.__cursor.fetchone()[0]!=1:
#                        #    self.__logger.debug("Possible problem in executing 'MARK_SITES_AS_DELETED' procedure for entry (%s)" % (value))
#                    except Exception, info:
#                        self.__logger.error("DB error while executing MARK_SITES_AS_DELETED(%s). Error message is: %s" % (value, info))
#                        
#        # check if there are groups(virtual-sites) to be deleted
#        if self.__group_sites2id:
#            self.__logger.info('GOCDB Topology - Execution - The following sites/groups are no longer valid and will be marked as deleted')
#            for key,value in self.__group_sites2id.items():
#                self.__logger.info('GOCDB Topology - Execution - %s' % key)
#                #key-virtual-site, value-groups-id
#                if self.__config.database_type != 'mysql':
#                    import cx_Oracle
#                    delete_entry=[]
#                    delete_entry.append(value)
#                    delete_entry.append('site')
#                    try:
#                        self.__cursor.callproc('MARK_GROUPS_AS_DELETED', delete_entry)
#                        self.__last_query = None # clear if no exception
#                        #if procedure_result.getvalue()!=1.0:
#                        #    self.__logger.debug("Possible problem in executing 'MARK_GROUPS_AS_DELETED' procedure for entry %s" % delete_entry)
#                    except Exception, info:
#                        self.__logger.error("DB error while executing MARK_GROUPS_AS_DELETED procedure with parameters %s. Error message is: %s" % (delete_entry, info))
#                else:
#                    try:
#                        self.__cursor.execute("""CALL MARK_GROUPS_AS_DELETED(%s,%s)""",(value,'site'))
#                        self.__last_query = None # clear if no exception
#                        #self.__cursor.execute('SELECT @sucess_flag')
#                        #if self.__cursor.fetchone()[0]!=1:
#                        #    self.__logger.debug("Possible problem in executing 'MARK_GROUPS_AS_DELETED' procedure for entry (%s,%s)" % (value,'site'))
#                    except Exception, info:
#                        self.__logger.error("DB error while executing MARK_GROUPS_AS_DELETED(%s,%s). Error message is: %s" % (value,'site', info))
#  
#      # check if there are groups(regions) to be deleted
#        if self.__group_regions2id:
#            self.__logger.info('GOCDB Topology - Execution - The following regions are no longer valid and will be marked as deleted')
#            for key,value in self.__group_regions2id.items():
#                self.__logger.info('GOCDB Topology - Execution - %s' % key)
#                #key-region, value-groups-id
#                if self.__config.database_type != 'mysql':
#                    import cx_Oracle
#                    delete_entry=[]
#                    delete_entry.append(value)
#                    delete_entry.append('region')
#                    try:
#                        self.__cursor.callproc('MARK_GROUPS_AS_DELETED', delete_entry)
#                        self.__last_query = None # clear if no exception
#                        #if procedure_result.getvalue()!=1.0:
#                        #    self.__logger.debug("Possible problem in executing 'MARK_GROUPS_AS_DELETED' procedure for entry %s" % delete_entry)
#                    except Exception, info:
#                        self.__logger.error("DB error while executing MARK_GROUPS_AS_DELETED procedure with parameters %s. Error message is: %s" % (delete_entry, info))
#                else:
#                    try:
#                        self.__cursor.execute("""CALL MARK_GROUPS_AS_DELETED(%s,%s)""",(value,'region'))
#                        self.__last_query = None # clear if no exception
#                        #self.__cursor.execute('SELECT @sucess_flag')
#                        #if self.__cursor.fetchone()[0]!=1:
#                        #    self.__logger.debug("Possible problem in executing 'MARK_GROUPS_AS_DELETED' procedure for entry (%s,%s)" % (value,'region'))
#                    except Exception, info:
#                        self.__logger.error("DB error while executing MARK_GROUPS_AS_DELETED(%s,%s). Error message is: %s" % (value,'region', info))
                
        self.gocdb_topo_synchro_status = 'Y'


    def updateServiceEndPoints(self, GOCDB_ServiceEndPoints, Infrast_name, Data_Provider, dbInput):
        "updates Service End-points information in ATP DB"
        
        #reset GOCDB topo synchronizer state
        self.gocdb_topo_synchro_status = 'N'

        for service_pt in GOCDB_ServiceEndPoints:
            # change core attribute state from 'NO'- N and 'Yes' - 'Y'
            if service_pt['iscore']=='NO':
                service_pt['iscore']='N'
            else:
                service_pt['iscore']='Y'
            if not service_pt['ismonitored']:
                service_pt['ismonitored'] = 'N'
            if service_pt['servicetype'].lower() in ('srmv2','srmv1','srm'):
                if not service_pt['serviceuri']:
                        service_pt['serviceuri']=service_pt['hostname']
            #prepare a service end-point entry list to be passed to oracle procedure
            if self.__config.database_type != 'mysql':
                import cx_Oracle
                procedure_result = self.__cursor.var(cx_Oracle.NUMBER)
                serviceendpt_entry = []
                serviceendpt_entry.append(Infrast_name)
                serviceendpt_entry.append(service_pt['sitename'])
                serviceendpt_entry.append(service_pt['serviceuri'])
                serviceendpt_entry.append(service_pt['servicetype'])# service-flavour
                serviceendpt_entry.append(service_pt['ipv4'])
                serviceendpt_entry.append(service_pt['hostname'])
                serviceendpt_entry.append(service_pt['isinproduction'])
                serviceendpt_entry.append(service_pt['iscore'])
                if service_pt['ismonitored']:
                    serviceendpt_entry.append(service_pt['ismonitored'])
                else:
                    serviceendpt_entry.append('')
                serviceendpt_entry.append(Data_Provider)
                serviceendpt_entry.append(service_pt['gocdbprimarykey'])
                serviceendpt_entry.append(procedure_result)# place holder for output result parameter

                try:
                    self.__cursor.callproc('SERVICE_UPDATE', serviceendpt_entry)
                    self.__last_query = None # clear if no exception
                    if procedure_result.getvalue()!=1.0:
                        self.__logger.debug("Possible problem in executing 'SERVICE_UPDATE' procedure for entry %s" % serviceendpt_entry)
                except Exception, info:
                    self.__logger.error("DB error while executing SERVICE_UPDATE procedure with parameters %s. Error message is: %s" % (serviceendpt_entry, info))
            else: 
                try:
                    self.__cursor.execute("""CALL SERVICE_UPDATE(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,@sucess_flag)""",(Infrast_name,service_pt['sitename'],service_pt['serviceuri'],service_pt['servicetype'],service_pt['ipv4'],service_pt['hostname'],service_pt['isinproduction'],service_pt['iscore'],service_pt['ismonitored'],Data_Provider,service_pt['gocdbprimarykey']))
                    self.__last_query = None # clear if no exception
                    self.__cursor.execute('SELECT @sucess_flag')
                    if self.__cursor.fetchone()[0]!=1:
                        self.__logger.debug("Possible problem in executing 'SERVICE_UPDATE' procedure for entry (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)" % (Infrast_name, service_pt['sitename'], service_pt['serviceuri'], service_pt['servicetype'], service_pt['ipv4'], service_pt['hostname'], service_pt['isinproduction'], service_pt['iscore'], service_pt['ismonitored'], Data_Provider, service_pt['gocdbprimarykey']))
                except Exception, info:
                    self.__logger.error("DB error while executing SERVICE_UPDATE(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s). Error message is: %s" % (Infrast_name, service_pt['sitename'], service_pt['serviceuri'], service_pt['servicetype'], service_pt['ipv4'], service_pt['hostname'], service_pt['isinproduction'], service_pt['iscore'], service_pt['ismonitored'], Data_Provider, service_pt['gocdbprimarykey'], info))

            #service_vo procedure
            if service_pt['vo']:
                if self.__config.database_type != 'mysql':
                    import cx_Oracle
                    procedure_result = self.__cursor.var(cx_Oracle.NUMBER)
                    servicevo_entry = []
                    servicevo_entry.append(service_pt['hostname'])
                    servicevo_entry.append(service_pt['servicetype'])
                    servicevo_entry.append(service_pt['vo'])
                    servicevo_entry.append(procedure_result)# place holder for output result parameter

                    try:
                        self.__cursor.callproc('SERVICE_VO_INSERT', servicevo_entry)
                        self.__last_query = None # clear if no exception
                        if procedure_result.getvalue()!=1.0:
                            self.__logger.debug("Possible problem in executing 'SERVICE_VO_INSERT' procedure for entry %s" % servicevo_entry)
                    except Exception, info:
                        self.__logger.error("DB error while executing SERVICE_VO_INSERT procedure with parameters %s. Error message is: %s" % (servicevo_entry, info))
                else:
                    try:
                        self.__cursor.execute("""CALL SERVICE_VO_INSERT(%s,%s,%s,@sucess_flag)""",(service_pt['hostname'],service_pt['servicetype'],service_pt['vo']))
                        self.__last_query = None # clear if no exception
                        self.__cursor.execute('SELECT @sucess_flag')
                        if self.__cursor.fetchone()[0]!=1:
                            self.__logger.debug("Possible problem in executing 'SERVICE_VO_INSERT' procedure for entry (%s,%s,%s)" % (service_pt['hostname'], service_pt['servicetype'], service_pt['vo']))
                    except Exception, info:
                        self.__logger.error("DB error while executing SERVICE_VO_INSERT(%s,%s,%s). Error message is: %s" % (service_pt['hostname'], service_pt['servicetype'], service_pt['vo'], info))

        self.gocdb_topo_synchro_status = 'Y'


    def updateRocContacts(self, GOCDB_RocContacts, dbInput):
        "updates the roc contatcs information"

        # reset VO synchronizer state
        self.gocdb_topo_synchro_status = 'N'

        for rocs in GOCDB_RocContacts:
            if rocs[0] == 'UKI':
                rocs[0] = 'NGI_UK'
            
            for roc in rocs[1]:
                if self.__config.database_type == 'mysql':
                    try:
                        self.__cursor.execute("""CALL ROC_CONTACTS_UPDATE(%s,%s,%s,%s,%s,%s)""",(rocs[0],roc['certdn'],roc['forename']+' '+roc['surname'],roc['email'],roc['tel'],roc['role_name']))
                        self.__last_query = None 
                    except Exception, info:
                        self.__logger.error("DB error while executing ROC_CONTACTS_UPDATE procedure for roc contact. Error message is: %s," %(info))
                else:
                    sf_entry = []
                    sf_entry.append(rocs[0])
                    sf_entry.append(roc['certdn'])
                    sf_entry.append(roc['forename']+' '+roc['surname'])
                    sf_entry.append(roc['email'])
                    sf_entry.append(roc['tel'])
                    sf_entry.append(roc['role_name'])
                    try:
                        import cx_Oracle
                        self.__cursor.callproc('ROC_CONTACTS_UPDATE', sf_entry)
                        self.__last_query = None 
                    except Exception, info:
                        self.__logger.error("DB error while executing ROC_CONTACTS_UPDATE procedure for roc contact. Error message is: %s," % (info))

        self.__logger.debug("GOCDB Topology - Execution - Roc contacts added")

        # set VO synchronizer state
        self.gocdb_topo_synchro_status = 'Y'


    def updateSiteContacts(self, GOCDB_SiteContacts, dbInput):
        "updates the site contatcs information"

        # reset VO synchronizer state
        self.gocdb_topo_synchro_status = 'N'
        infrastructure = 'EGI';

        for sites in GOCDB_SiteContacts:

            for site in sites[1]: 
                if self.__config.database_type == 'mysql':
                    try:
                        self.__cursor.execute("""CALL SITE_CONTACTS_UPDATE(%s,%s,%s,%s,%s,%s,%s)""",(infrastructure, sites[0],site['certdn'],site['forename']+' '+site['surname'],site['email'],site['tel'],site['role_name']))
                        self.__last_query = None 
                    except Exception, info:
                        self.__logger.error("DB error while executing SITE_CONTACTS_UPDATE procedure for site contact. Error message is: %s," %(info))
                else:
                    sf_entry = []
                    sf_entry.append(infrastructure)
                    sf_entry.append(sites[0])
                    sf_entry.append(site['certdn'])
                    sf_entry.append(site['forename']+' '+site['surname'])
                    sf_entry.append(site['email'])
                    sf_entry.append(site['tel'])
                    sf_entry.append(site['role_name'])
                    try:
                        import cx_Oracle
                        self.__cursor.callproc('SITE_CONTACTS_UPDATE', sf_entry)
                        self.__last_query = None 
                    except Exception, info:
                        self.__logger.error("DB error while executing SITE_CONTACTS_UPDATE procedure for site contact %s. Error message is: %s," % (sf_entry, info))

        self.__logger.debug("GOCDB Topology - Execution - Site contacts added")

        # set VO synchronizer state
        self.gocdb_topo_synchro_status = 'Y'    
                
    def updateDowntimes(self, GOCDB_Downtimes, Infrast_name, Data_Provider, dbInput):
        "updates Downtimes information in ATP DB"

        #reset GOCDB downtime synchronizer state
        self.gocdb_downtime_synchro_status = 'N'
        #get the existing list of vos in the DB
        self.__DowntimesInDB = dbInput.getDowntimeIDs()
        # remove duplicate entries of gocdbpk in DB
        try:
            if self.__config.database_type != 'mysql':            
                self.__cursor.callproc('CHK_DUPLICATE_GOCDB_DOWNTIMES')
            else:
                self.__cursor.execute("""CALL CHK_DUPLICATE_GOCDB_DOWNTIMES""")
            self.__last_query = None # clear if no exception
        except Exception, info:
            self.__logger.error("DB error while executing last query: %s" % info)
        
        for down_time in GOCDB_Downtimes:
                if down_time['gocdbprimarykey'] in self.__DowntimesInDB.keys():
                        del self.__DowntimesInDB[down_time['gocdbprimarykey']]
    
        for down_time in GOCDB_Downtimes:
             #prepare a downtime-entry list to be passed to oracle procedure
            if self.__config.database_type != 'mysql':
                import cx_Oracle
                procedure_result = self.__cursor.var(cx_Oracle.NUMBER)
                downtime_entry = []
                downtime_entry.append(datetime.utcfromtimestamp(float(down_time['starttimestamp'])))
                downtime_entry.append(datetime.utcfromtimestamp(float(down_time['endtimestamp'])))
                downtime_entry.append(down_time['classification'])
                downtime_entry.append(int(down_time['gocdowntimeid']))
                downtime_entry.append(int(0)) # osg_downtime_id
                downtime_entry.append(down_time['severity'])
                downtime_entry.append(down_time['description'][:1000].encode('latin1','ignore'))
                downtime_entry.append(Infrast_name)
                downtime_entry.append(down_time['hostname'])# downtime for a host
                downtime_entry.append(down_time['sitename']) # downtime for a site
                downtime_entry.append(down_time['gocdbprimarykey'])
                downtime_entry.append(down_time['servicetype'])
                downtime_entry.append(procedure_result)# place holder for output result parameter
            # execute oracle/mysql downtime_update procedure
            try:
                    if self.__config.database_type == 'mysql':
                        self.__cursor.execute("""CALL DOWNTIME_UPDATE(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,@sucess_flag)""",(datetime.utcfromtimestamp(float(down_time['starttimestamp'])),datetime.utcfromtimestamp(float(down_time['endtimestamp'])),down_time['classification'],int(down_time['gocdowntimeid']),int(0),down_time['severity'],down_time['description'][:1000].encode('latin1','ignore'),Infrast_name,down_time['hostname'],down_time['sitename'],down_time['gocdbprimarykey'],down_time['servicetype']))
                        self.__last_query = None # clear if no exception
                        # pl. refer to http://mysql-python.sourceforge.net/MySQLdb-1.2.2/public/MySQLdb.cursors.BaseCursor-class.html#callproc
                        self.__cursor.execute('SELECT @sucess_flag')
                        if self.__cursor.fetchone()[0]!=1:
                            self.__logger.debug("Possible problem in executing GOCDB 'DOWNTIME_UPDATE' procedure for entry (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)" % (datetime.utcfromtimestamp(float(down_time['starttimestamp'])), datetime.utcfromtimestamp(float(down_time['endtimestamp'])), down_time['classification'], int(down_time['gocdowntimeid']),int(0), down_time['severity'], down_time['description'][:1000].encode('latin1','ignore'), Infrast_name, down_time['hostname'], down_time['sitename'], down_time['gocdbprimarykey'], down_time['servicetype']))
                    else:
                        self.__cursor.callproc('DOWNTIME_UPDATE', downtime_entry)
                        self.__last_query = None # clear if no exception
                        if procedure_result.getvalue()!=1.0:
                            self.__logger.debug("Possible problem in executing 'DOWNTIME_UPDATE' procedure for entry %s" % downtime_entry)
            except Exception, info:
                self.__logger.error("DB error while executing the last query: %s" % info  + ":" + str(down_time))
        # delete downtimes that exists in ATP DB but are absent in the GOCDB downtimes feed
        for item in self.__DowntimesInDB:
                if self.__config.database_type != 'mysql':
                        import cx_Oracle
                        procedure_result = self.__cursor.var(cx_Oracle.NUMBER)
                        remove_downtime_entry = []
                        remove_downtime_entry.append(self.__DowntimesInDB[item][0])
                        remove_downtime_entry.append(procedure_result)
                        self.__cursor.callproc('MARK_DOWNTIMES_AS_DELETED',remove_downtime_entry)
                        self.__last_query = None # clear if no exception
                        if procedure_result.getvalue()!=1.0:
                            self.__logger.debug("Possible problem in executing 'MARK_DOWNTIMES_AS_DELETED' procedure for entry %s" % self.__DowntimesInDB[item])
                else:
                        self.__cursor.execute("""CALL MARK_DOWNTIMES_AS_DELETED(%s,@sucess_Flag)"""%(self.__DowntimesInDB[item][0]))
                        self.__last_query = None # clear if no exception
                        # pl. refer to http://mysql-python.sourceforge.net/MySQLdb-1.2.2/public/MySQLdb.cursors.BaseCursor-class.html#callproc
                        self.__cursor.execute('SELECT @sucess_flag')
                        if self.__cursor.fetchone()[0]!=1:
                                self.__logger.debug("Possible problem in executing 'MARK_DOWNTIMES_AS_DELETED' procedure for entry %s" %self.__DowntimesInDB[item][0])
        
        #set GOCDB downtime synchronizer state
        self.gocdb_downtime_synchro_status = 'Y'
        
    def updateGSTATCPUCounts(self, Gstat_Feed, Data_Provider):
        """updates site CPU counts and HEPSPEC06 information in ATP DB"""
        
        #reset gstat synchronizer state
        self.gstat_synchro_status = 'N'
        gstat_sitename=''; gstat_phycpu = 0; gstat_logcpu = 0; gstat_ksi2k = 0; gstat_hspec06 = 0
        for site_entry in Gstat_Feed:
            for key, value in site_entry.items():
                #logical CPU, ksi2k, phy. CPU, hep_spec06 in sequence
                #if key.lower() == 'sitename':
                if key.lower() == 'Sitename'.lower():
                    gstat_sitename = (value.encode('latin1','ignore')) # sitename
                #if key.lower() == 'phycpu':
                if key.lower() == 'PhyCPU'.lower():
                    gstat_phycpu = value
                #if key.lower() == 'logcpu':
                if key.lower() == 'LogCPU'.lower():
                    gstat_logcpu = value
                if key.lower() == 'ksi2k'.lower():
                    gstat_ksi2k = value
                #if key.lower() == 'hepspec06':
                if key.lower() == 'HEPSPEC06'.lower():
                    gstat_hspec06 = value
            if not gstat_sitename:
                gstat_sitename=''    
            if not gstat_phycpu:
                    gstat_phycpu = -1
            if not gstat_logcpu:
                    gstat_logcpu = -1
            if not gstat_ksi2k:
                    gstat_ksi2k = -1
            if not gstat_hspec06:
                    gstat_hspec06 = -1    
            if self.__config.database_type != 'mysql':
                import cx_Oracle
                procedure_result = self.__cursor.var(cx_Oracle.NUMBER)
                cpucount_entry = []
                cpucount_entry.append(gstat_sitename)
                cpucount_entry.append(gstat_logcpu)
                cpucount_entry.append(gstat_phycpu)
                cpucount_entry.append(gstat_ksi2k)
                cpucount_entry.append(gstat_hspec06)
                cpucount_entry.append(procedure_result)# place holder for output result parameter
            try:
                if self.__config.database_type == 'mysql':
                    self.__cursor.execute("""CALL SITE_CAPACITY_UPDATE(%s,%s,%s,%s,%s,@sucess_flag)""",(gstat_sitename, gstat_logcpu, gstat_phycpu, gstat_ksi2k, gstat_hspec06))
                    self.__last_query = None # clear if no exception
                    # pl. refer to http://mysql-python.sourceforge.net/MySQLdb-1.2.2/public/MySQLdb.cursors.BaseCursor-class.html#callproc
                    self.__cursor.execute('SELECT @sucess_flag')
                    if self.__cursor.fetchone()[0]!=1:
                        self.__logger.debug("Possible problem in executing gstat 'SITE_CAPACITY_UPDATE' procedure for entry %s,%s,%s,%s,%s" % (gstat_sitename, gstat_logcpu, gstat_phycpu, gstat_ksi2k, gstat_hspec06))
                else:
                    self.__cursor.callproc('SITE_CAPACITY_UPDATE', cpucount_entry)
                    self.__last_query = None # clear if no exception
                    if procedure_result.getvalue()!=1.0:
                        self.__logger.debug("Possible problem in executing gstat 'SITE_CAPACITY_UPDATE' procedure for entry %s" % cpucount_entry)
            except Exception, info:
                self.__logger.error("DB error while executing last query: %s for entry -%s,%s,%s,%s,%s " % (info, gstat_sitename,gstat_logcpu,gstat_phycpu,gstat_ksi2k,gstat_hspec06))
        #set gstat synchronizer state
        self.gstat_synchro_status = 'Y'

    def updateTiers_And_Federations(self, Tier_Federation_Info, Data_Provider, dbInput):
        """updates Tier and Federation information in ATP DB"""
        
        #reset gstat synchronizer state
        self.gstat_synchro_status = 'N'
        
        #get the existing list of groups(virtual-sites) in the DB
        self.__group_tiers2id = dbInput.getOPS_Tiers()

        #get the existing list of groups(federations) in the DB
        self.__group_federations2id = dbInput.getOPS_Federations()
        
        #get the existing list of sites in federations in the DB
        self.__sites_federations2id = dbInput.getOPS_SitesInFederation()
  
        for tier_fed_entry in Tier_Federation_Info:
            list_tierfed =[]
            #for key,value in tier_fed_entry.items():
                #print key,value
            list_tierfed = []
            list_tierfed.append(tier_fed_entry['Tier'])
            list_tierfed.append(tier_fed_entry['Federation'])
            list_tierfed.append(tier_fed_entry['FederationAccountingName'])
            list_tierfed.append(tier_fed_entry['Site'])
            list_tierfed.append(tier_fed_entry['Infrastructure'])
            list_tierfed.append(tier_fed_entry['Country'])

            # remove entry if it exists in the feed
            if tier_fed_entry['Tier'] in self.__group_tiers2id.keys():
                del self.__group_tiers2id[tier_fed_entry['Tier']]

            if tier_fed_entry['Federation'] in self.__group_federations2id.keys():
                del self.__group_federations2id[tier_fed_entry['Federation']]
        
            if tier_fed_entry['Site'] in self.__sites_federations2id.keys():
                del self.__sites_federations2id[tier_fed_entry['Site']]
            
            if self.__config.database_type != 'mysql':
                import cx_Oracle
                procedure_result = self.__cursor.var(cx_Oracle.NUMBER)
                list_tierfed.append(procedure_result)# place holder for output result parameter
            try:
                if self.__config.database_type == 'mysql':
                    self.__cursor.execute("""CALL TIER_FEDERATION_INSERT(%s,%s,%s,%s,%s,%s,@sucess_flag)""",(tier_fed_entry['Tier'], tier_fed_entry['Federation'], tier_fed_entry['FederationAccountingName'],tier_fed_entry['Site'], tier_fed_entry['Infrastructure'],tier_fed_entry['Country']))
                    self.__last_query = None # clear if no exception
                    # pl. refer to http://mysql-python.sourceforge.net/MySQLdb-1.2.2/public/MySQLdb.cursors.BaseCursor-class.html#callproc
                    self.__cursor.execute('SELECT @sucess_flag')
                    if self.__cursor.fetchone()[0]!=1:
                        self.__logger.debug("Possible problem in executing gstat 'TIER_FEDERATION_INSERT' procedure for entry %s,%s,%s,%s,%s,%s" % (tier_fed_entry['Tier'], tier_fed_entry['Federation'], tier_fed_entry['FederationAccountingName'],tier_fed_entry['Site'], tier_fed_entry['Infrastructure'],tier_fed_entry['Country']))
                else:
                    self.__cursor.callproc('TIER_FEDERATION_INSERT', list_tierfed)
                    self.__last_query = None # clear if no exception
                    if procedure_result.getvalue()!=1.0:
                        self.__logger.debug("Possible problem in executing gstat 'TIER_FEDERATION_INSERT' procedure for entry %s" % list_tierfed)
            except Exception, info:
                self.__logger.error("DB error while executing last query: %s" % info  + ":" + str(list_tierfed))

        #check if there are any sites in federation that no longer exists
        if self.__sites_federations2id:
            self.__logger.info('Gstat Tier - Execution - The following sites in federation are no longer valid and will be deleted')
            #print self.__sites_federations2id
            for key,value in self.__sites_federations2id.items():
                self.__logger.info('Gstat Tier - Execution - %s' % key)
                #key-site, value-id
                if self.__config.database_type != 'mysql':
                    import cx_Oracle
                    delete_entry=[]
                    delete_entry.append(value)
                    try:
                        self.__cursor.callproc('DELETE_SITES_IN_FEDERATION', delete_entry)
                        self.__last_query = None # clear if no exception
                        #if procedure_result.getvalue()!=1.0:
                        #    self.__logger.debug("Possible problem in executing 'DELETE_SITES_IN_FEDERATION' procedure for entry %s" % delete_entry)
                    except Exception, info:
                        self.__logger.error("DB error while executing DELETE_SITES_IN_FEDERATION procedure with parameters %s. Error message is: %s" % (delete_entry, info))
                else:
                    try:
                        self.__cursor.execute("""CALL DELETE_SITES_IN_FEDERATION(%s)""",(value))
                        self.__last_query = None # clear if no exception
                        #self.__cursor.execute('SELECT @sucess_flag')
                        #if self.__cursor.fetchone()[0]!=1:
                        #    self.__logger.debug("Possible problem in executing 'DELETE_SITES_IN_FEDERATION' procedure for entry (%s)" % (value))
                    except Exception, info:
                        self.__logger.error(" DB error while executing DELETE_SITES_IN_FEDERATION(%s). Error message is: %s" % (value, info))
                
        # check if there are groups(tiers) to be deleted
        if self.__group_tiers2id:
            self.__logger.info('Gstat Tier - Execution - The following tiers are no longer valid and will be marked as deleted')
            for key,value in self.__group_tiers2id.items():
                self.__logger.info('Gstat Tier - Execution - %s' % key)
                #key-tier, value-groups-id
                if self.__config.database_type != 'mysql':
                    import cx_Oracle
                    delete_entry=[]
                    delete_entry.append(value)
                    delete_entry.append('tier')
                    try:
                        self.__cursor.callproc('MARK_GROUPS_AS_DELETED', delete_entry)
                        self.__last_query = None # clear if no exception
                        #if procedure_result.getvalue()!=1.0:
                        #    self.__logger.debug("Possible problem in executing 'MARK_GROUPS_AS_DELETED' procedure for entry %s" % delete_entry)
                    except Exception, info:
                        self.__logger.error("DB error while executing MARK_GROUPS_AS_DELETED procedure with parameters %s. Error message is: %s" % (delete_entry, info))
                else:
                    try:
                        self.__cursor.execute("""CALL MARK_GROUPS_AS_DELETED(%s,%s)""",(value,'tier'))
                        self.__last_query = None # clear if no exception
                        #self.__cursor.execute('SELECT @sucess_flag')
                        #if self.__cursor.fetchone()[0]!=1:
                        #    self.__logger.debug("Possible problem in executing 'MARK_GROUPS_AS_DELETED' procedure for entry (%s,%s)" % (value,'tier'))
                    except Exception, info:
                        self.__logger.error("DB error while executing MARK_GROUPS_AS_DELETED(%s,%s). Error message is: %s" % (value,'tier', info))

        # check if there are groups(federations) to be deleted
        if self.__group_federations2id:
            self.__logger.info('Gstat Tier - Execution - The following federations are no longer valid and will be marked as deleted')
            for key,value in self.__group_federations2id.items():
                self.__logger.info('Gstat Tier - Execution - %s' % key)
                #key-federation, value-groups-id
                if self.__config.database_type != 'mysql':
                    import cx_Oracle
                    delete_entry=[]
                    delete_entry.append(value)
                    delete_entry.append('federation')
                    try:
                        self.__cursor.callproc('MARK_GROUPS_AS_DELETED', delete_entry)
                        self.__last_query = None # clear if no exception
                        #if procedure_result.getvalue()!=1.0:
                        #    self.__logger.debug("Possible problem in executing 'MARK_GROUPS_AS_DELETED' procedure for entry %s" % delete_entry)
                    except Exception, info:
                        self.__logger.error("DB error while executing MARK_GROUPS_AS_DELETED procedure with parameters %s. Error message is: %s" % (delete_entry, info))
                else:
                    try:
                        self.__cursor.execute("""CALL MARK_GROUPS_AS_DELETED(%s,%s)""",(value,'federation'))
                        self.__last_query = None # clear if no exception
                        #self.__cursor.execute('SELECT @sucess_flag')
                        #if self.__cursor.fetchone()[0]!=1:
                        #    self.__logger.debug("Possible problem in executing 'MARK_GROUPS_AS_DELETED' procedure for entry (%s,%s)" % (value,'federation'))
                    except Exception, info:
                        self.__logger.error("DB error while executing MARK_GROUPS_AS_DELETED(%s,%s). Error message is: %s" % (value,'federation', info))

        #set gstat synchronizer state
        self.gstat_synchro_status = 'Y'
        
    def updateOSGResources(self, OSG_resources_list, Infrast_name, Data_Provider, dbInput):
        "updates OSG resources in ATP DB"
        #reset OSG synchronizer state
        self.osg_synchro_status = 'N'

        #get the existing list of Phy. sites in the DB
        self.__sites2id = dbInput.getOPS_PhySites(Infrast_name)

        #get the existing list of groups(virtual-sites) in the DB
        self.__group_sites2id = dbInput.getOPS_Sites(Infrast_name)

        for site_entry in OSG_resources_list:
            if site_entry['InteropMonitoring'].lower()=='True'.lower():

                if site_entry['gridtype'].lower() == 'osg production resource':
                    Infrast_Type = 'Production';
                elif site_entry['gridtype'].lower() == 'osg integration test bed resource':
                    Infrast_Type = 'PPS';
                else:
                    Infrast_Type = 'Other';

                # site update procedure
                if self.__config.database_type != 'mysql':
                    import cx_Oracle
                    procedure_result = self.__cursor.var(cx_Oracle.NUMBER)
                    osg_site_entry = []
                    osg_site_entry.append(Infrast_name)
                    osg_site_entry.append(site_entry['sitename'])
                    osg_site_entry.append('') #offname
                    osg_site_entry.append('OSG site')
                    osg_site_entry.append(Data_Provider)
                    osg_site_entry.append('')# country name
                    osg_site_entry.append('Y') # certification status
                    osg_site_entry.append(Infrast_Type);
                    # rest of the parameters from GOCDB feed are absent
                    for i in range(10):
                        osg_site_entry.append('')
                    osg_site_entry.append(procedure_result)# place holder for output result parameter
                    
                # remove entry if it exists in the feed
                if site_entry['sitename'] in self.__group_sites2id.keys():
                    del self.__group_sites2id[site_entry['sitename']]
                
                if site_entry['sitename'] in self.__sites2id.keys():
                    del self.__sites2id[site_entry['sitename']]

                try:
                    # execute site_update procedure
                    if self.__config.database_type == 'mysql':
                        self.__cursor.execute("""CALL SITE_UPDATE(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,@sucess_flag)""",(Infrast_name,site_entry['sitename'],'','OSG_site',Data_Provider,'','Y',Infrast_Type,'','','','','','','','','',''))
                        self.__last_query = None # clear if no exception
                        # pl. refer to http://mysql-python.sourceforge.net/MySQLdb-1.2.2/public/MySQLdb.cursors.BaseCursor-class.html#callproc
                        self.__cursor.execute('SELECT @sucess_flag')
                        if self.__cursor.fetchone()[0]!=1:
                            self.__logger.debug("Possible problem in executing OSG 'SITE_UPDATE' procedure for entry (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)" % (Infrast_name, site_entry['sitename'], '', 'OSG_site', Data_Provider, '', 'Y', '', '', '', '', '', '', '', '', '', '', ''))
                    else:
                        self.__cursor.callproc('SITE_UPDATE', osg_site_entry)
                        self.__last_query = None # clear if no exception
                        if procedure_result.getvalue()!=1.0:
                            self.__logger.debug("Possible problem in executing OSG 'SITE_UPDATE' procedure for entry %s" % osg_site_entry)
                except Exception, info:
                    self.__logger.error("DB error while executing last query: %s" % info + ":" + str(site_entry))


                #service_update procedure
                if self.__config.database_type != 'mysql':
                    import cx_Oracle
                    procedure_result = self.__cursor.var(cx_Oracle.NUMBER)
                    service_entry = []
                    service_entry.append(Infrast_name)
                    service_entry.append(site_entry['sitename'])
                    service_entry.append(site_entry['serviceendpoint'])
                    service_entry.append(site_entry['serviceflavour'])
                    service_entry.append('') #ipv4
                    service_entry.append(site_entry['hostname'])
                    service_entry.append('Y') #is_in_prod
                    service_entry.append('N') #is_core
                    service_entry.append('Y') #is_monitored
                    service_entry.append(Data_Provider)
                    service_entry.append('') # gocdbprimarykey is absent
                    service_entry.append(procedure_result)# place holder for output result parameter
                # execute service_update oracle procedure
                try:
                    if self.__config.database_type == 'mysql':
                        self.__cursor.execute("""CALL SERVICE_UPDATE(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,@sucess_flag)""",(Infrast_name,site_entry['sitename'],site_entry['serviceendpoint'],site_entry['serviceflavour'],'',site_entry['hostname'],'Y','N','Y',Data_Provider,''))
                        self.__last_query = None # clear if no exception
                        # pl. refer to http://mysql-python.sourceforge.net/MySQLdb-1.2.2/public/MySQLdb.cursors.BaseCursor-class.html#callproc
                        self.__cursor.execute('SELECT @sucess_flag')
                        if self.__cursor.fetchone()[0]!=1:
                            self.__logger.debug("Possible problem in executing OSG 'SERVICE_UPDATE' procedure for entry (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)" % (Infrast_name,site_entry['sitename'],site_entry['serviceendpoint'],site_entry['serviceflavour'],'',site_entry['hostname'],'Y','N','Y',Data_Provider,''))
                    else:
                        self.__cursor.callproc('SERVICE_UPDATE', service_entry)
                        self.__last_query = None # clear if no exception
                        if procedure_result.getvalue()!=1.0:
                            self.__logger.debug("Possible problem in executing OSG 'SERVICE_UPDATE' procedure for entry %s" % service_entry)
                except Exception, info:
                    self.__logger.error("DB error while executing last query: %s" % info + ":" + str(site_entry))

                #service_vo procedure
                if self.__config.database_type != 'mysql':
                    import cx_Oracle
                    procedure_result = self.__cursor.var(cx_Oracle.NUMBER)
                    servicevo_entry = []
                    servicevo_entry.append(site_entry['hostname'])
                    servicevo_entry.append(site_entry['serviceflavour'])
                    servicevo_entry.append(site_entry['vo'])
                    servicevo_entry.append(procedure_result)# place holder for output result parameter
                try:
                    if self.__config.database_type == 'mysql':
                        self.__cursor.execute("""CALL SERVICE_VO_INSERT(%s,%s,%s,@sucess_flag)""",(site_entry['hostname'],site_entry['serviceflavour'],site_entry['vo']))
                        self.__last_query = None # clear if no exception
                        # pl. refer to http://mysql-python.sourceforge.net/MySQLdb-1.2.2/public/MySQLdb.cursors.BaseCursor-class.html#callproc
                        self.__cursor.execute('SELECT @sucess_flag')
                        if self.__cursor.fetchone()[0]!=1:
                            self.__logger.debug("Possible problem in executing OSG 'SERVICE_VO_INSERT' procedure for entry (%s,%s,%s)" % (site_entry['hostname'], site_entry['serviceflavour'], site_entry['vo']))
                    else:
                        self.__cursor.callproc('SERVICE_VO_INSERT', servicevo_entry)
                        self.__last_query = None # clear if no exception
                        if procedure_result.getvalue()!=1.0:
                            self.__logger.debug("Possible problem in executing OSG 'SERVICE_VO_INSERT' procedure for entry %s" % servicevo_entry)
                except Exception, info:
                    self.__logger.error("DB error while executing last query: %s" % info + ":" + str(site_entry) )
        
        # check if there are phy. sites to be deleted
        if self.__sites2id:
            self.__logger.info('OSG Topology - Execution - The following sites are no longer valid and will be marked as deleted')
            for key,value in self.__sites2id.items():
                self.__logger.info('OSG Topology - Execution - %s' % key)
                #key-site, value-id
                if self.__config.database_type != 'mysql':
                    import cx_Oracle
                    delete_entry=[]
                    delete_entry.append(value)
                    try:
                        self.__cursor.callproc('MARK_SITES_AS_DELETED', delete_entry)
                        self.__last_query = None # clear if no exception
                        #if procedure_result.getvalue()!=1.0:
                        #    self.__logger.debug("Possible problem in executing 'MARK_SITES_AS_DELETED' procedure for entry %s" % delete_entry)
                    except Exception, info:
                        self.__logger.error("DB error while executing MARK_SITES_AS_DELETED procedure with parameters %s. Error message is: %s" % (delete_entry, info))
                else:
                    try:
                        self.__cursor.execute("""CALL MARK_SITES_AS_DELETED(%s)""",(value))
                        self.__last_query = None # clear if no exception
                        #self.__cursor.execute('SELECT @sucess_flag')
                        #if self.__cursor.fetchone()[0]!=1:
                        #    self.__logger.debug("Possible problem in executing 'MARK_SITES_AS_DELETED' procedure for entry (%s)" % (value))
                    except Exception, info:
                        self.__logger.error("DB error while executing MARK_SITES_AS_DELETED(%s). Error message is: %s" % (value, info))
                
                
        # check if there are groups(virtual-sites) to be deleted
        if self.__group_sites2id:
            for key,value in self.__group_sites2id.items():
                #key-virtual-site, value-groups-id
                if self.__config.database_type != 'mysql':
                    import cx_Oracle
                    delete_entry=[]
                    delete_entry.append(value)
                    delete_entry.append('site')
                    try:
                        self.__cursor.callproc('MARK_GROUPS_AS_DELETED', delete_entry)
                        self.__last_query = None # clear if no exception
                        #if procedure_result.getvalue()!=1.0:
                        #    self.__logger.debug("Possible problem in executing 'MARK_GROUPS_AS_DELETED' procedure for entry %s" % delete_entry)
                    except Exception, info:
                        self.__logger.error("DB error while executing MARK_GROUPS_AS_DELETED procedure with parameters %s. Error message is: %s" % (delete_entry, info))
                else:
                    try:
                        self.__cursor.execute("""CALL MARK_GROUPS_AS_DELETED(%s,%s)""",(value,'site'))
                        self.__last_query = None # clear if no exception
                        #self.__cursor.execute('SELECT @sucess_flag')
                        #if self.__cursor.fetchone()[0]!=1:
                        #    self.__logger.debug("Possible problem in executing 'MARK_GROUPS_AS_DELETED' procedure for entry (%s,%s)" % (value,'site'))
                    except Exception, info:
                        self.__logger.error("DB error while executing MARK_GROUPS_AS_DELETED(%s,%s). Error message is: %s" % (value,'site', info))

        #set OSG synchronizer state
        self.osg_synchro_status = 'Y'

    def updateOSGDowntimes(self, OSG_Downtimes, Infrast_name, Data_Provider, dbInput):
        "updates Downtimes information in ATP DB"
        #reset OSG downtime synchronizer state
        self.osg_downtime_synchro_status = 'N'

        self.__logger.info("number of downtimes : %s" % str(len(OSG_Downtimes)))
        self.__logger.info("here are the downtimes : %s" % str(OSG_Downtimes))

        for down_time in OSG_Downtimes:
            self.__logger.debug("Storing OSG Downtime: %s" % str(down_time))
            # OSG downtimes if action is create. Later on handle cancel and modify
            if down_time['action'].lower().strip()=='create':
                #prepare a downtime-entry list to be passed to oracle procedure
                if self.__config.database_type != 'mysql':
                    import cx_Oracle
                    procedure_result = self.__cursor.var(cx_Oracle.NUMBER)
                    downtime_entry = []
                    downtime_entry.append(datetime.utcfromtimestamp(float(down_time['downtimestart'])))
                    downtime_entry.append(datetime.utcfromtimestamp(float(down_time['downtimeend'])))
                    downtime_entry.append(down_time['downtimeclassification'].strip())
                    downtime_entry.append(int(0)) # GOCDB downtimeid
                    downtime_entry.append(int(down_time['downtimeid']))
                    downtime_entry.append(down_time['downtimeseverity'])
                    downtime_entry.append(down_time['downtimedescription'][:1000].encode('latin1','ignore'))
                    downtime_entry.append(Infrast_name)
                    downtime_entry.append(down_time['hostname'])# downtime for a host
                    downtime_entry.append(down_time['sitename']) # downtime for a site
                    downtime_entry.append('') # gocdbpk absent
                    downtime_entry.append(down_time['servicetype'])
                    downtime_entry.append(procedure_result)# place holder for output result parameter

                try:
                    if self.__config.database_type == 'mysql':
                            self.__cursor.execute("""CALL DOWNTIME_UPDATE(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,@sucess_flag)""",(datetime.utcfromtimestamp(float(down_time['downtimestart'])),datetime.utcfromtimestamp(float(down_time['downtimeend'])),down_time['downtimeclassification'].strip(),int(0),int(down_time['downtimeid']),down_time['downtimeseverity'],down_time['downtimedescription'][:1000].encode('latin1','ignore'),Infrast_name,down_time['hostname'],down_time['sitename'],''))
                            self.__last_query = None # clear if no exception
                            # pl. refer to http://mysql-python.sourceforge.net/MySQLdb-1.2.2/public/MySQLdb.cursors.BaseCursor-class.html#callproc
                            self.__cursor.execute('SELECT @sucess_flag')
                            if self.__cursor.fetchone()[0]!=1:
                                self.__logger.debug("Possible problem in executing OSG 'DOWNTIME_UPDATE' procedure for entry (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)" % (datetime.utcfromtimestamp(float(down_time['downtimestart'])), datetime.utcfromtimestamp(float(down_time['downtimeend'])), down_time['downtimeclassification'].strip(), int(0), int(down_time['downtimeid']), down_time['downtimeseverity'], down_time['downtimedescription'][:1000].encode('latin1','ignore'), Infrast_name, down_time['hostname'], down_time['sitename'], ''))
                    else:
                        self.__cursor.callproc('DOWNTIME_UPDATE', downtime_entry)
                        self.__last_query = None # clear if no exception
                        if procedure_result.getvalue()!=1.0:
                            self.__logger.debug("Possible problem in executing OSG 'DOWNTIME_UPDATE' procedure for entry %s" % oracle_procedure_downtime_entry)
                except Exception, info:
                    self.__logger.error("DB error while executing the last query: %s" % info + ":" + str(down_time))
            
            elif down_time['action'].lower().strip()=='modify':
                #prepare a downtime-entry list to be passed to oracle procedure
                if self.__config.database_type != 'mysql':
                    import cx_Oracle
                    procedure_result = self.__cursor.var(cx_Oracle.NUMBER)
                    downtime_entry = []
                    downtime_entry.append(datetime.utcfromtimestamp(float(down_time['downtimestart'])))
                    downtime_entry.append(datetime.utcfromtimestamp(float(down_time['downtimeend'])))
                    downtime_entry.append(down_time['downtimeclassification'].strip())
                    downtime_entry.append(int(down_time['downtimeid']))
                    downtime_entry.append(down_time['downtimeseverity'])
                    downtime_entry.append(down_time['downtimedescription'][:1000].encode('latin1','ignore'))
                    downtime_entry.append(Infrast_name)
                    downtime_entry.append(down_time['hostname'])# downtime for a host
                    downtime_entry.append(down_time['sitename']) # downtime for a site
                    downtime_entry.append(down_time['action'].strip()) # action- modify/cancel
                    downtime_entry.append(procedure_result)# place holder for output result parameter

                try:
                    if self.__config.database_type == 'mysql':
                            self.__cursor.execute("""CALL UPDATE_OSG_DOWNTIMES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,@sucess_flag)""",(datetime.utcfromtimestamp(float(down_time['downtimestart'])),datetime.utcfromtimestamp(float(down_time['downtimeend'])), \
                            down_time['downtimeclassification'].strip(),int(down_time['downtimeid']),down_time['downtimeseverity'],down_time['downtimedescription'][:1000].encode('latin1','ignore'),Infrast_name,down_time['hostname'],down_time['sitename'],down_time['action'].strip()))
                            self.__last_query = None # clear if no exception
                            # pl. refer to http://mysql-python.sourceforge.net/MySQLdb-1.2.2/public/MySQLdb.cursors.BaseCursor-class.html#callproc
                            self.__cursor.execute('SELECT @sucess_flag')
                            if self.__cursor.fetchone()[0]!=1:
                                self.__logger.debug("Possible problem in executing OSG 'UPDATE_OSG_DOWNTIMES' procedure for entry (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)" % (datetime.utcfromtimestamp(float(down_time['downtimestart'])),datetime.utcfromtimestamp(float(down_time['downtimeend'])), \
                            down_time['downtimeclassification'].strip(),int(down_time['downtimeid']),down_time['downtimeseverity'],down_time['downtimedescription'][:1000].encode('latin1','ignore'),Infrast_name,down_time['hostname'],down_time['sitename'],down_time['action'].strip()))
                    else:
                        self.__cursor.callproc('UPDATE_OSG_DOWNTIMES', downtime_entry)
                        self.__last_query = None # clear if no exception
                        if procedure_result.getvalue()!=1.0:
                            self.__logger.debug("Possible problem in executing OSG 'DOWNTIME_UPDATE' procedure for entry %s" % oracle_procedure_downtime_entry)
                except Exception, info:
                    self.__logger.error("DB error while executing the last query: %s" % info + ":" + str(down_time))
            
            elif down_time['action'].lower().strip()=='cancel':
                #prepare a downtime-entry list to be passed to oracle procedure
                if self.__config.database_type != 'mysql':
                    import cx_Oracle
                    procedure_result = self.__cursor.var(cx_Oracle.NUMBER)
                    downtime_entry = []
                    for i in range(2):
                        downtime_entry.append(None)
                    downtime_entry.append('') #classification
                    downtime_entry.append(int(down_time['downtimeid']))
                    downtime_entry.append('') #downtimeseverity
                    downtime_entry.append('') #downtimedescription
                    downtime_entry.append(Infrast_name)
                    downtime_entry.append('')#hostname
                    downtime_entry.append('')#sitename
                    downtime_entry.append(down_time['action'].strip()) # action- modify/cancel
                    downtime_entry.append(procedure_result)# place holder for output result parameter

                try:
                    if self.__config.database_type == 'mysql':
                            self.__cursor.execute("""CALL UPDATE_OSG_DOWNTIMES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,@sucess_flag)""",(None,None,'',int(down_time['downtimeid']),'','',Infrast_name,'','',down_time['action'].strip()))
                            self.__last_query = None # clear if no exception
                            # pl. refer to http://mysql-python.sourceforge.net/MySQLdb-1.2.2/public/MySQLdb.cursors.BaseCursor-class.html#callproc
                            self.__cursor.execute('SELECT @sucess_flag')
                            if self.__cursor.fetchone()[0]!=1:
                                self.__logger.debug("Possible problem in executing OSG 'DOWNTIME_UPDATE' procedure for entry (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)" % ('','','',int(down_time['downtimeid']),'','',Infrast_name,'','',down_time['action'].strip()))
                    else:
                        self.__cursor.callproc('UPDATE_OSG_DOWNTIMES', downtime_entry)
                        self.__last_query = None # clear if no exception
                        if procedure_result.getvalue()!=1.0:
                            self.__logger.debug("Possible problem in executing OSG 'DOWNTIME_UPDATE' procedure for entry %s" % oracle_procedure_downtime_entry)
                except Exception, info:
                    self.__logger.error("DB error while executing the last query: %s" % info + ":" + str(down_time))
            
                #set OSG downtime synchronizer state
        self.osg_downtime_synchro_status = 'Y'

    def updateMPIServices(self, MPI_services, data_provider):
        """updates MPI info. in database"""
        # BDII synchronizer status
        self.bdii_synchro_status = 'N'
        for lst_item in MPI_services:
            try:
                if self.__config.database_type == 'mysql':
                    # parameters passed are CE hostname, MPI hostname and MPI flavour
                    self.__cursor.execute("""CALL MPI_SERVICES_UPDATE(%s,%s,%s,@sucess_flag)""",(data_provider,lst_item[0],lst_item[2]))
                    self.__last_query = None # clear if no exception
                    # pl. refer to http://mysql-python.sourceforge.net/MySQLdb-1.2.2/public/MySQLdb.cursors.BaseCursor-class.html#callproc
                    self.__cursor.execute('SELECT @sucess_flag')
                    if self.__cursor.fetchone()[0]!=1:
                        self.__logger.debug("Possible problem in executing 'MPI_SERVICES_UPDATE' procedure for entry: (%s)" %lst_item)
                else:
                    import cx_Oracle
                    procedure_result = self.__cursor.var(cx_Oracle.NUMBER)
                    tmp_list = []
                    tmp_list.append(data_provider)
                    tmp_list.append(lst_item[0])
                    tmp_list.append(lst_item[2])
                    tmp_list.append(procedure_result)
                    self.__cursor.callproc('MPI_SERVICES_UPDATE', tmp_list)
                    self.__last_query = None # clear if no exception
                    if procedure_result.getvalue()!=1.0:
                        self.__logger.debug("Possible problem in executing 'MPI_SERVICES_UPDATE' procedure for entry %s" % lst_item)
            except Exception, info:
                self.__logger.error("DB error while executing the last query: %s" % info + ":" + str(lst_item))
        #set BDII synchronizer state
        self.bdii_synchro_status = 'Y'
               
    def updateServiceVOs(self, services, vofeeds, dbInput):
        """ updates service-vo information in the database"""

        self.bdii_synchro_status = 'N'
        lfc_ops_service = ''
        vofeedsname = [ x[0] for x in vofeeds ]
        
        for item in services:
            if 'ops' in item['vos'] and item['type']=='LFC_C':
                #print item['serviceuri']
                lfc_ops_service=item['serviceuri']
                break

        # gets database status
        self.__logger.debug("BDII - Execution - Getting the service/vo mapping from the database")
        svcvo = dbInput.getServiceVOs()
        self.__logger.debug("BDII - Execution - Getting service hostname, flavours, and ids from the database")
        self.__service2id = dbInput.getServiceIDs()
        self.__logger.debug("DBII - Execution - Getting VOs from the database")
        self.__vo2id = dbInput.getVOs()

        # creates sql code
        create_sql = ''
        if self.__config.database_type == 'mysql':
            create_sql = self.__mysql_create_servicevo_sql
        else:
            create_sql = self.__ora_create_servicevo_sql

        # gets dbii mappings
        db_map_bdii_gocdb_serv_types={}
        for k,v in self.__config.db_mapping_gocdb_bdii_serv_type.iteritems():
            db_map_bdii_gocdb_serv_types[string.lower(v)]=string.lower(k)

        # processes service list
        for i in services:
            n_voname=''
            n_endpoint    = i["node"].lower()
            n_flavourtype = i["type"].lower()
            # map the bdii service type flavour into our DB service type flavour
            if n_flavourtype in db_map_bdii_gocdb_serv_types:
                n_flavourtype = db_map_bdii_gocdb_serv_types[n_flavourtype]
            else:
                self.__logger.error("BDII - Execution - Service type flavour %s was not found in db/bdii mapping" % n_flavourtype)
            if i["vos"]:
                for vo_element in i["vos"]:
                    n_voname = vo_element.lower()
                    if n_voname in vofeedsname:
                        self.__logger.debug("BDII - Execution - Service not registered for %s vo since the vo provides a vo feed" % n_voname)
                        continue
                    quit = 0
                    n_serviceid = 0;n_void = 0;
                    if (n_endpoint, n_flavourtype, n_voname) not in svcvo:
                    # This VO mapping does not exist in the DB
                    # Check if the service is defined in the DB
                        try:
                            n_serviceid = self.__service2id[(n_endpoint, n_flavourtype)]
                        except KeyError:
                            quit = 1
                        if not quit:
                            try:
                                # Check if the VO is defined in the DB
                                n_void = self.__vo2id[n_voname]
                            except KeyError:
                                self.__logger.debug("BDII - Execution - Service not registered for %s vo since the vo is not defined in the database" % n_voname)
                                quit = 1
                        if not quit:
                            #print n_serviceid,n_void
                            # Create the new VO mapping in the DB
                            if self.__config.database_type == 'mysql':
                                data_list=[]
                                data_list.append(n_serviceid)
                                data_list.append(n_void)
                                self.__runQuery(create_sql, data_list) # {"service_id": n_serviceid, "vo_id": n_void})
                            else:
                                self.__runQuery(create_sql, {"service_id": n_serviceid, "vo_id": n_void})
                            # I add the new service-vo mapping to the list of DB existing mappings.
                            svcvo[(n_endpoint, n_flavourtype, n_voname)] = (n_serviceid, n_void)
        if lfc_ops_service:
            try:
                if self.__config.database_type == 'mysql':
                    self.__cursor.execute("""CALL MARK_LFC_CEN_SERV_AS_DELETED(%s,@sucess_flag)""",lfc_ops_service)
                    self.__last_query = None # clear if no exception
                    # pl. refer to http://mysql-python.sourceforge.net/MySQLdb-1.2.2/public/MySQLdb.cursors.BaseCursor-class.html#callproc
                    self.__cursor.execute('SELECT @sucess_flag')
                    if self.__cursor.fetchone()[0]!=1:
                        self.__logger.debug("Possible problem in executing MARK_LFC_CEN_SERV_AS_DELETED' procedure for entry (%s)" % lfc_ops_service)
                else:
                    import cx_Oracle
                    proc_entry=[]
                    procedure_result=self.__cursor.var(cx_Oracle.NUMBER)
                    proc_entry.append(lfc_ops_service)
                    proc_entry.append(procedure_result)
                    self.__cursor.callproc('MARK_LFC_CEN_SERV_AS_DELETED', proc_entry)
                    self.__last_query = None # clear if no exception
                    if procedure_result.getvalue()!=1.0:
                        self.__logger.debug("Possible problem in executing MARK_LFC_CEN_SERV_AS_DELETED procedure for entry %s" % lfc_ops_service)
            except Exception, info:
                self.__logger.error("DB error while executing the last query: %s" % info + ":" + "for entry " + lfc_ops_service)

        self.bdii_synchro_status = 'Y'

    def updateOSGKSI2K(self, OSG_KSI2K_list, Infrast_name):
        "updates OSG KSI2K values in ATP DB"
        
        self.gstat_synchro_status = 'N'
        
        for site_entry in OSG_KSI2K_list:
            # OSG sites KSI2K update procedure
            if self.__config.database_type != 'mysql':
                import cx_Oracle
                procedure_result = self.__cursor.var(cx_Oracle.NUMBER)
                osgsite_entry = []
                osgsite_entry.append(Infrast_name)
                osgsite_entry.append(site_entry['groupname'])
                #osgsite_entry.append(site_entry['ksi2kmin'])
                osgsite_entry.append(site_entry['ksi2kmax'])
                osgsite_entry.append(site_entry['hepspec'])
                osgsite_entry.append(procedure_result)# place holder for output result parameter
            try:
                # execute site_update procedure
                if self.__config.database_type == 'mysql':
                    self.__cursor.execute("""CALL SITE_KSI2K_UPDATE(%s,%s,%s,%s,@sucess_flag)""",(Infrast_name, site_entry['groupname'],site_entry['ksi2kmax'],site_entry['hepspec']))
                    self.__last_query = None # clear if no exception
                    # pl. refer to http://mysql-python.sourceforge.net/MySQLdb-1.2.2/public/MySQLdb.cursors.BaseCursor-class.html#callproc
                    self.__cursor.execute('SELECT @sucess_flag')
                    if self.__cursor.fetchone()[0]!=1:
                        self.__logger.debug("Possible problem in executing OSG 'SITE_KSI2K_UPDATE' procedure for entry (%s,%s,%s,%s)" % (Infrast_name, site_entry['groupname'],site_entry['ksi2kmax'],site_entry['hepspec']))
                else:
                    self.__cursor.callproc('SITE_KSI2K_UPDATE', osgsite_entry)
                    self.__last_query = None # clear if no exception
                    if procedure_result.getvalue()!=1.0:
                        self.__logger.debug("Possible problem in executing OSG 'SITE_KSI2K_UPDATE' procedure for entry %s" % osgsite_entry)
            except Exception, info:
                self.__logger.error("DB error while executing the last query: %s" % info + ":" + str(site_entry))
        #set gstat synchronizer state
        self.gstat_synchro_status = 'Y'


    def updateServiceVOFeeds(self,VO_Feed_list,voname):
        """Updates service vo mappings from the VO feed"""
        
        self.vofeeds_synchro_status = 'N'
                
        for feed_list_item in VO_Feed_list[0]:
            for item in feed_list_item['service']:

                if self.__config.database_type != 'mysql':
                    import cx_Oracle
                    procedure_result = self.__cursor.var(cx_Oracle.NUMBER)
                    list_para_procedure=[]
                    list_para_procedure.append(item['hostname'].strip())
                    list_para_procedure.append(item['flavour'].strip())
                    list_para_procedure.append(voname)
                    list_para_procedure.append(procedure_result)# place holder for output result parameter
                try:
                     # execute service-vo procedure in vo feeds
                     if self.__config.database_type == 'mysql':
                         self.__cursor.execute("""CALL SERVICE_VO_INSERT(%s,%s,%s,@sucess_flag)""",(item['hostname'].strip(),item['flavour'].strip(),voname))
                         self.__last_query = None # clear if no exception
                         # pl. refer to http://mysql-python.sourceforge.net/MySQLdb-1.2.2/public/MySQLdb.cursors.BaseCursor-class.html#callproc
                         self.__cursor.execute('SELECT @sucess_flag')
                         if self.__cursor.fetchone()[0]!=1:
                             self.__logger.debug("Possible problem in executing VO feeds 'SERVICE_VO_INSERT' procedure for entry (%s,%s,%s)" % (item['hostname'], item['flavour'], voname))
                     else:
                        self.__cursor.callproc('SERVICE_VO_INSERT', list_para_procedure)
                        self.__last_query = None # clear if no exception
                        if procedure_result.getvalue()!=1.0:
                            self.__logger.debug("Possible problem in executing VO feeds 'SERVICE_VO_INSERT' procedure for entry %s" % list_para_procedure)
                except Exception, info:
                    #print list_para_procedure
                    self.__logger.error("DB error while executing the last query: %s" % info + ":" + str(item))
        self.vofeeds_synchro_status = 'Y'
                            
    def updateVOGroupings(self,VO_sitegroups_list, voname, dbInput):
        """updates VO-service-groups in the database"""
        
        self.vofeeds_synchro_status = 'N'
        # get existing list of groupnames from ATP DB for the VO
        self.__vofeeds_groupname2id = dbInput.getGroupnames_VOFeed(voname)
        # get existing list of group-types from ATP DB for the VO
        self.__vofeeds_grouptypes = dbInput.getGrouptypes_VOFeed(voname)
        # get exitsing list of service-groups from ATP DB for the VO
        self.__vofeeds_servicegroups = dbInput.getServiceGroups_VOFeed(voname)
      
        for vofeed_element in VO_sitegroups_list[0]:
            group_list = vofeed_element['groups']
            for group_entry in group_list:
                group_element_list=[]
                group_element_list.append(vofeed_element['infrast'])
                group_element_list.append(vofeed_element['vo'])
                group_element_list.append(vofeed_element['atp_site'])
                group_element_list.append(group_entry['groupname'])
                group_element_list.append(group_entry['grouptype'])
                # compare groupnames and group_types entries in VO feed with entries in ATP DB
                # remove groupname entry if it exists in the feed
                if group_entry['groupname'] in self.__vofeeds_groupname2id.keys():
                    del self.__vofeeds_groupname2id[group_entry['groupname']]                                    
                # remove group_type entry if it exists in the feed
                if group_entry['grouptype'] in self.__vofeeds_grouptypes.keys():
                    del self.__vofeeds_grouptypes[group_entry['grouptype']]
                 
                service_list=vofeed_element['service']
                for service_entry in service_list:
                    
                    tmp = service_entry['hostname'], service_entry['flavour'], group_entry['groupname'], group_entry['grouptype']
                    for vfsg in self.__vofeeds_servicegroups.keys():
                         if tmp == vfsg:
                             del self.__vofeeds_servicegroups[tmp]
                    
                    service_element_list=[]
                    service_element_list=[item for item in group_element_list]
                    service_element_list.append(service_entry['hostname'].strip())
                    service_element_list.append(service_entry['flavour'].strip())
                    spacetoken_list=vofeed_element['spacetokens']
                    if spacetoken_list:
                        for spacetoken_entry in spacetoken_list:
                            spacetoken_element_list=[]
                            spacetoken_element_list=[item for item in service_element_list]
                            spacetoken_element_list.append(spacetoken_entry['spacetoken_name'])
                            spacetoken_element_list.append(spacetoken_entry['spacetoken_path'])
                    else:
                            spacetoken_element_list=[item for item in service_element_list]
                            spacetoken_element_list.append('')
                            spacetoken_element_list.append('')
        
                    if self.__config.database_type != 'mysql':
                        import cx_Oracle
                        procedure_result = self.__cursor.var(cx_Oracle.NUMBER)
                        VO_services_group=[]
                        VO_services_group=[item for item in spacetoken_element_list]
                        VO_services_group.append(procedure_result)# place holder for output result parameter

                    try:
                        # execute VO service grouping update procedure
                        if self.__config.database_type == 'mysql':
                            VO_services_group = tuple(spacetoken_element_list)
                            self.__cursor.execute("""CALL VO_TOPOLOGY_UPDATE(%s,%s,%s,%s,%s,%s,%s,%s,%s,@sucess_flag)""",VO_services_group)
                            self.__last_query = None # clear if no exception
                            # pl. refer to http://mysql-python.sourceforge.net/MySQLdb-1.2.2/public/MySQLdb.cursors.BaseCursor-class.html#callproc
                            self.__cursor.execute('SELECT @sucess_flag')
                            proc_output = self.__cursor.fetchone()[0]
                            if proc_output!=1:
                                if proc_output==2:
                                    self.__logger.debug("Service flavour not found in the DB while executing 'VO_TOPOLOGY_UPDATE' procedure for entry (%s,%s,%s,%s,%s,%s,%s,%s,%s)" % (VO_services_group))
                                elif proc_output==3:
                                    self.__logger.debug("Service not found in the DB while executing 'VO_TOPOLOGY_UPDATE' procedure for entry (%s,%s,%s,%s,%s,%s,%s,%s,%s)" % (VO_services_group))
                                elif proc_output==4:
                                    self.__logger.debug("Site not found in the DB while executing 'VO_TOPOLOGY_UPDATE' procedure for entry (%s,%s,%s,%s,%s,%s,%s,%s,%s)" % (VO_services_group))
                                else:
                                    self.__logger.debug("Possible problem in executing VO feeds 'VO_TOPOLOGY_UPDATE' procedure for entry (%s,%s,%s,%s,%s,%s,%s,%s,%s)" % (VO_services_group))
                        else:
                            self.__cursor.callproc('VO_TOPOLOGY_UPDATE', VO_services_group)
                            self.__last_query = None # clear if no exception
                            proc_output = procedure_result.getvalue()
                            if proc_output!=1.0:
                                if proc_output==2.0:
                                    self.__logger.debug("Service flavour not found in the DB while executing 'VO_TOPOLOGY_UPDATE' procedure for entry %s" % VO_services_group)
                                elif proc_output==3.0:
                                    self.__logger.debug("Service not found in the DB while executing 'VO_TOPOLOGY_UPDATE' procedure for entry %s" % VO_services_group)
                                elif proc_output==4.0:
                                    self.__logger.debug("Site not found in the DB while executing 'VO_TOPOLOGY_UPDATE' procedure for entry %s" % VO_services_group)
                                else:
                                    self.__logger.debug("Possible problem in executing VO feeds 'VO_TOPOLOGY_UPDATE' procedure for entry %s" % VO_services_group)
                    except Exception, info:
                        self.__logger.error("DB error while executing the last query: %s" % info + ":" + str(VO_services_group))

        # mark as deleted vo_service_groups in the DB no longer declared in the vo feed
        if self.__vofeeds_servicegroups:
            self.__logger.info('VO Feeds - Execution - The following vo-service-groups are no longer present and will be marked as deleted')
            for item in self.__vofeeds_servicegroups:
                self.__logger.info('VO Feeds - Execution - %s'%(self.__vofeeds_servicegroups[item]))
                try:
                    if self.__config.database_type == 'mysql':
                        self.__cursor.execute("""CALL MARK_VO_SERVICE_GROUPS_AS_DELETED (%s)""", self.__vofeeds_servicegroups[item])
                        self.__last_query = None # clear if no exception
                    else:
                         self.__cursor.callproc('MARK_VO_SER_GROUPS_AS_DELETED', [self.__vofeeds_servicegroups[item]])
                         self.__last_query = None # clear if no exception
                except Exception, info:
                    self.__logger.error("VO Feeds - Execution - DB error while marking services as deleted in the ATP database: %s" % info + ":" + str(item))
        
        # mark as deleted groups in the DB no longer declared in the vo feed
        if self.__vofeeds_groupname2id:
            self.__logger.info('VO Feeds - Execution - The following groups are no longer valid and will be marked as deleted')
            for key,value in self.__vofeeds_groupname2id.items():
                self.__logger.info('VO Feeds - Execution - %s' % key)
                #key-groupname, value-id
                if self.__config.database_type != 'mysql':
                    import cx_Oracle
                    delete_entry=[]
                    delete_entry.append(value)
                    delete_entry.append('group')
                    try:
                        self.__cursor.callproc('MARK_GROUPS_AS_DELETED', delete_entry)
                        self.__last_query = None # clear if no exception
                        #if procedure_result.getvalue()!=1.0:
                        #    self.__logger.debug("Possible problem in executing 'MARK_GROUPS_AS_DELETED' procedure for entry %s" % delete_entry)
                    except Exception, info:
                        self.__logger.error("DB error while executing MARK_GROUPS_AS_DELETED procedure with group-id- %s. Error message is: %s" % (delete_entry, info))
                else:
                    try:
                        self.__cursor.execute("""CALL MARK_GROUPS_AS_DELETED(%s,%s)""",(value,'group'))
                        self.__last_query = None # clear if no exception
                        #self.__cursor.execute('SELECT @sucess_flag')
                        #if self.__cursor.fetchone()[0]!=1:
                        #    self.__logger.debug("Possible problem in executing 'MARK_GROUPS_AS_DELETED' procedure for entry (%s)" % (value))
                    except Exception, info:
                        self.__logger.error("DB error while executing MARK_GROUPS_AS_DELETED procedure with group-id- (%s). Error message is: %s" % (value, info))

        # mark as deleted group types in the DB no longer declared in the vo feed
        if self.__vofeeds_grouptypes:
            self.__logger.info('VO Feeds - Execution - The following groups types are no longer valid and will be marked as deleted')            
            for key,value in self.__vofeeds_grouptypes.items():
                self.__logger.info('VO Feeds - Execution - %s' % key)
                #key-group-type,value-group-type
                if self.__config.database_type != 'mysql':
                    import cx_Oracle
                    delete_entry=[]
                    delete_entry.append(key)
                    try:
                        self.__cursor.callproc('MARK_GROUP_TYPES_AS_DELETED', delete_entry)
                        self.__last_query = None # clear if no exception
                    except Exception, info:
                        self.__logger.error("DB error while executing MARK_GROUP_TYPES_AS_DELETED procedure with grouptype- %s. Error message is: %s" % (delete_entry, info))
                else:
                    try:
                        self.__cursor.execute("""CALL MARK_GROUP_TYPES_AS_DELETED(%s)""",(key))
                        self.__last_query = None # clear if no exception
                    except Exception, info:
                        self.__logger.error("DB error while executing MARK_GROUP_TYPES_AS_DELETED procedure with grouptype- (%s). Error message is: %s" % (key, info))
        self.vofeeds_synchro_status = 'Y'


    def updateVOGroupLinks(self,VO_sitegroups_link,voname):
        """Updates service vo mappings from the VO feed"""

        self.vofeeds_synchro_status = 'N'

        for item in VO_sitegroups_link:

            if self.__config.database_type != 'mysql':
                import cx_Oracle
                procedure_result = self.__cursor.var(cx_Oracle.NUMBER)
                list_para_procedure=[]
                list_para_procedure.append(item['atp_site'].strip())
                list_para_procedure.append(item['grouptier'].strip())
                list_para_procedure.append(item['groupsite'].strip())                
                list_para_procedure.append(voname)
                list_para_procedure.append(procedure_result)# place holder for output result parameter
            try:
                 # execute service-vo procedure in vo feeds
                 if self.__config.database_type == 'mysql':
                     self.__cursor.execute("""CALL VO_GROUP_LINKS(%s,%s,%s,%s,@sucess_flag)""",(item['atp_site'].strip(),item['grouptier'].strip(),item['groupsite'].strip(),voname))
                     self.__last_query = None # clear if no exception
                     self.__cursor.execute('SELECT @sucess_flag')
                     if self.__cursor.fetchone()[0] != 0:
                         self.__logger.debug("Possible problem executing 'VO_GROUP_LINKS' procedure for (%s,%s,%s,%s)" % (item['atp_site'], item['grouptier'], item['groupsite'],voname))
                 else:
                    self.__cursor.callproc('VO_GROUP_LINKS', list_para_procedure)
                    self.__last_query = None # clear if no exception
                    if procedure_result.getvalue() != 0.0:
                        self.__logger.debug("Possible problem executing 'VO_GROUP_LINKS' procedure for %s" % list_para_procedure)
            except Exception, info:
                self.__logger.error("DB error while executing the last query: %s" % info + ":" + str(item))

        self.vofeeds_synchro_status = 'Y'


    def deleteVOGroupings(self,vofeeds,dbInput):
        """"Delete VO groupings in the database"""

        self.vofeeds_synchro_status = 'N'
        # get list of existing VOs
        self.__vosInDB = dbInput.getVOs()
        vofeeds.append('ops')
        # remove entries for VOs having their feed.'OPS' VO will be an exception for this.
        for v in vofeeds:
            if v in self.__vosInDB.keys():
                del self.__vosInDB[v]
        for vo_name in self.__vosInDB:
            delete_vo=[]
            delete_vo.append(vo_name)
            try:
                # execute VO service grouping update procedure
                if self.__config.database_type == 'mysql':
                    self.__cursor.execute("""CALL DELETE_VO_GROUPS(%s)""",(vo_name))
                else:
                    self.__cursor.callproc('DELETE_VO_GROUPS', delete_vo)
            except Exception, info:
                self.__logger.error("DB error while marking groups defined by vo:%s as isdeleted='Y':%s" % (info ,vo_name))
        self.vofeeds_synchro_status = 'Y'
