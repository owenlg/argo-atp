##############################################################################
#
# NAME:        config.py
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
# MODIFIED:     23-July-2011
#
##############################################################################

import ConfigParser
import getopt
import os
import logging,logging.config
import string
import sys

class Config:

    action                           = None # remember the last action in case it fails
    atlas_data_provider              = 'Atlas'
    bdii_data_provider               = 'BDII'
    bdii_ldap_base                   = "o=grid"
    bdii_ldap_filter                 = """(|(objectClass=GlueSite)(objectClass=GlueService)(objectClass=GlueCE)(objectClass=GlueSA))"""
    bdii_ldap_mpi_filter             = """(&(objectclass=GlueHostApplicationSoftware)(&(GlueHostApplicationSoftwareRunTimeEnvironment=MPI-START)))"""
    bdii_ldap_uri                    = "ldap://bdii.host:2170"
    cic_portal_data_provider         = 'CIC'
    cic_portal_vo_url                = ''
    #cms_topology_feed                = 'http://dashboard02.cern.ch/dashboard/request.py/cmssitemap'
    cms_data_provider                = 'CMS'
    config_file                      = ''
    database_host                    = ""
    database_name                    = ""
    database_password                = ""
    database_type                    = "mysql"
    database_user                    = ""
    db_commit                        = 1 # really commit changes to the database
    db_mapping_gocdb_bdii_serv_type  = {}
    db_mapping_gocdb_downtime_serv_type  = {'SRM': ['SRM', 'SRMv2']}
    db_mapping_gocdb_downtime        = {}
    db_mapping_gocdb_serviceendpoint = {}
    db_mapping_gocdb_site            = {}
    db_mapping_osg                   = {}
    db_mapping_osg_servicetype       = {}
    db_uri                           = "user/pass@db"
    egi_infrast                      = 'EGI'
    gocdb_data_provider              = 'GOCDB'
    gocdb_downtime_url               = ''
    gocdb_node_url                   = ''
    gocdb_roccontacts_url            = ''
    gocdb_sitecontacts_url           = ''
    gocdb_serviceendpoint_url        = ''
    gocdb_servicetype_url            = ''
    gocdb_site_url                   = ''
    voms_servers                     = {}
    gstat_data_provider              = 'GSTAT'
    gstat_tier_federation_url        = ''
    gstat_cpu_hepspec06_url          = ''
    lhcb_data_provider               = 'LHCb'
    limit                            = 1000 # IN ( ) can't have more than 1000 elements in Oracle
    log_level                        = logging.ERROR # only log errors by default
    logger                           = None
    logger_syslog                    = None
    logging_config                   = '/etc/atp/atp_logging_parameters_config.conf'
    msg_destination                  = '/queue/grid.topology.atp.osg.downtimes'
    msg_destination_virtual_prefix   = 'Consumer'
    msg_client_type                  = 'virtual'
    msg_client_name                  = 'atp.osg.downtimes'
    msg_broker                       = ''
    msg_port                         = 6163
    msg_broker_list_file             = '/var/cache/msg/broker-cache-file/broker-list'
    osg_data_provider                = 'OIM'
    osg_infrast                      = 'OSG'
    osg_topology_url                 = ''
    roc_config_file                  = ''
    run_synchro_bdii                 = "N"
    run_synchro_cic_portal           = "N"
    run_synchro_gocdb_downtime       = "N"
    run_synchro_gocdb_topo           = "N"
    run_synchro_gstat                = "N"
    run_synchro_osg                  = "N"
    run_synchro_osg_downtime         = "N"
    run_synchro_alice_topology       = "N"
    run_synchro_atlas_topology       = "N"
    run_synchro_cms_topology         = "N"
    run_synchro_lhcb_topology        = "N"
    run_synchro_vo_feeds             = 'N'
    static_filename                  = ""
    site_status                      = "Certified"  # defaults for new sites
    site_type                        = "Production"
    vofeeds_config_file              = ''
    vofeeds_data_provider            = 'VO-Feeds'
    vofeeds_xsd_schema               = '/etc/atp/atp_vo_feeds_schema.xsd'
    x509_user_cert                   = 'usercert.pem'
    x509_user_key                    = 'userkey.pem'

    def __dir_exists(self,f):
        d = os.path.dirname(f)
        if not os.path.exists(d):
            os.makedirs(d)


    def __init__(self):
        try:
            self.__parseArgs()
            self.__setupLogging()
        except Exception, exception:
            print "Errors in reading/parsing ATP configuration files in '/etc/atp' directory: %s" % str(exception).strip()
            sys.exit(1)


    def __readDBConfig(self,configfile):
        "Read  database config file"
        try:
            conf = ConfigParser.ConfigParser()
            conf.read(configfile)
            #Database parameters
            self.db_uri = self.__confGet(conf, "database", "url") or self.db_uri

            self.database_type = self.__confGet(conf, "database", "db_type") or self.database_type
            self.database_name = self.__confGet(conf, "database", "db_name") or self.database_name
            self.database_host = self.__confGet(conf, "database", "host") or self.database_host
            self.database_user = self.__confGet(conf, "database", "user") or self.database_user
            self.database_password = self.__confGet(conf, "database", "passwd") or self.database_password

            if self.__confGet(conf, "database", "commit"):
                if string.upper(self.__confGet(conf, "database", "commit"))[0] == 'Y':
                    self.db_commit = 1;
        except Exception, info:
            print "Error in retriving database configuration information from 'atp_db.conf' file."
            sys.exit(1)
            
    def __readLogConfig(self,configfile):
        "Read path info. for ATP logging configuration and OSG downtimes configuration"
        conf = ConfigParser.ConfigParser()
        conf.read(configfile)
        # logging and OSG downtime configuration
        self.logging_config = self.__confGet(conf,"log_files","logging_config_file") or self.logging_config
        if os.path.exists(self.logging_config)==False:
            print "Some of the paths defined in 'atp_logging_files.conf' file are not valid."
            sys.exit(1)

    def __readConfig(self, configfile):
        "Read ATP config file"
        conf = ConfigParser.ConfigParser()
        conf.read(configfile)

        # save config. file name for internal use
        self.config_file=configfile
        # Log level
        self.log_level = self.__confGet(conf, "logging", "log_level") or self.log_level

        #Infrastructure parameters
        self.egi_infrast       = self.__confGet(conf, "infrastructure", "egi_infrast") or self.egi_infrast
        self.osg_infrast        = self.__confGet(conf, "infrastructure", "osg_infrast") or self.osg_infrast

        #GOCDB parameters
        self.gocdb_data_provider       = self.__confGet(conf, "gocdb", "data_provider_name") or self.gocdb_data_provider
        self.gocdb_downtime_url        = self.__confGet(conf, "gocdb", "downtime_url") or self.gocdb_downtime_url
        self.gocdb_node_url            = self.__confGet(conf, "gocdb", "node_url") or self.gocdb_node_url
        self.gocdb_serviceendpoint_url = self.__confGet(conf, "gocdb", "serviceendpoint_url") or self.gocdb_serviceendpoint_url
        self.gocdb_roccontacts_url     = self.__confGet(conf, "gocdb", "roccontacts_url") or self.gocdb_roccontacts_url
        self.gocdb_sitecontacts_url    = self.__confGet(conf, "gocdb", "sitecontacts_url") or self.gocdb_sitecontacts_url
        self.gocdb_servicetype_url     = self.__confGet(conf, "gocdb", "servicetype_url") or self.gocdb_servicetype_url
        self.gocdb_site_url            = self.__confGet(conf, "gocdb", "site_url") or self.gocdb_site_url
        self.x509_user_key             = self.__confGet(conf, "gocdb", "user_key_file") or self.x509_user_key
        self.x509_user_cert            = self.__confGet(conf, "gocdb", "user_cert_file") or self.x509_user_cert
        if os.path.exists(self.x509_user_key)==False or os.path.exists(self.x509_user_cert)==False:   
            print "Certificate files specified in 'atp_synchro.conf' do not exist. Please re-check their presence."
            sys.exit(1)

        #VOMS servers parameters
        self.voms_servers  = self.__confGetSection(conf, "voms") or self.voms_servers
        
        #OSG parameters
        self.osg_data_provider = self.__confGet(conf, "osg", "data_provider_name") or self.osg_data_provider
        self.osg_topology_url  = self.__confGet(conf, "osg", "topology_url") or self.osg_topology_url

        #OSG Downtimes  parameters
        self.msg_destination                = self.__confGet(conf, "osg_downtimes","destination")or self.msg_destination
        self.msg_destination_virtual_prefix = self.__confGet(conf, "osg_downtimes","virtual_prefix")or self.msg_destination_virtual_prefix
        self.msg_client_type                = self.__confGet(conf, "osg_downtimes","type")or self.msg_client_type
        self.msg_client_name                = self.__confGet(conf, "osg_downtimes","name")or self.msg_client_name 
        self.msg_broker                     = self.__confGet(conf, "osg_downtimes","broker")or self.msg_broker
        self.msg_port                       = self.__confGet(conf, "osg_downtimes","port")or self.msg_port
        self.msg_broker_list_file           = self.__confGet(conf, "osg_downtimes","broker_list_file")or self.msg_broker_list_file

        #BDII parameters
        self.bdii_data_provider = self.__confGet(conf, "bdii", "data_provider_name") or self.bdii_data_provider
        self.bdii_ldap_base     = self.__confGet(conf, "bdii", "ldap_base")   or self.bdii_ldap_base
        self.bdii_ldap_filter   = self.__confGet(conf, "bdii", "ldap_filter") or self.bdii_ldap_filter
        self.bdii_ldap_mpi_filter   = self.__confGet(conf, "bdii", "ldap_mpi_filter") or self.bdii_ldap_mpi_filter
        self.bdii_ldap_uri      = self.__confGet(conf, "bdii", "ldap_uri")    or self.bdii_ldap_uri
        
        #Gstat parameters
        self.gstat_data_provider         = self.__confGet(conf, "gstat", "data_provider_name") or self.gstat_data_provider
        self.gstat_tier_federation_url   = self.__confGet(conf, "gstat", "tier_federation_url") or self.gstat_tier_federation_url
        self.gstat_cpu_hepspec06_url     = self.__confGet(conf, "gstat", "site_cpu_hepspec06_url") or self.gstat_cpu_hepspec06_url
        

        #CIC Portal parameters
        self.cic_portal_data_provider = self.__confGet(conf, "cic_portal", "data_provider_name") or self.cic_portal_data_provider
        self.cic_portal_vo_url        = self.__confGet(conf, "cic_portal", "vo_url") or self.cic_portal_vo_url

        #DB Mapping tables
        self.db_mapping_gocdb_bdii_serv_type  = self.__confGetSection(conf, "db_mapping_gocdb_bdii_serv_type") or self.db_mapping_gocdb_bdii_serv_type
        self.db_mapping_gocdb_downtime        = self.__confGetSection(conf, "db_mapping_gocdb_downtime") or self.db_mapping_gocdb_downtime
        self.db_mapping_gocdb_serviceendpoint = self.__confGetSection(conf, "db_mapping_gocdb_serviceendpoint") or self.db_mapping_gocdb_serviceendpoint
        self.db_mapping_gocdb_site            = self.__confGetSection(conf, "db_mapping_gocdb_site") or self.db_mapping_gocdb_site
        self.db_mapping_osg                   = self.__confGetSection(conf, "db_mapping_osg") or self.db_mapping_osg
        self.db_mapping_osg_servicetype       = self.__confGetSection(conf, "db_mapping_osg_servicetype") or self.db_mapping_osg_servicetype

        # VO feeds XSD url and config file
        self.vofeeds_xsd_schema = self.__confGet(conf, "vofeeds_settings","vofeeds_xsd_schema") or self.vofeeds_xsd_schema
        self.vofeeds_config_file =  self.__confGet(conf, "vofeeds_settings","config_file") or self.vofeeds_config_file 

        # roc config file
        self.roc_config_file =  self.__confGet(conf, "roc","config_file") or self.roc_config_file

        #Execute synchronizers
        
        if self.__confGet(conf, "run_synchronizer", "bdii"):
            self.run_synchro_bdii = string.upper(self.__confGet(conf, "run_synchronizer", "bdii"))[0]
        if self.__confGet(conf, "run_synchronizer", "cic_portal"):
            self.run_synchro_cic_portal = string.upper(self.__confGet(conf, "run_synchronizer", "cic_portal"))[0]
        if self.__confGet(conf, "run_synchronizer", "gocdb_downtime"):
            self.run_synchro_gocdb_downtime = string.upper(self.__confGet(conf, "run_synchronizer", "gocdb_downtime"))[0]
        if self.__confGet(conf, "run_synchronizer", "gocdb_topology"):
            self.run_synchro_gocdb_topo = string.upper(self.__confGet(conf, "run_synchronizer", "gocdb_topology"))[0]
        if self.__confGet(conf, "run_synchronizer", "gstat"):
            self.run_synchro_gstat = string.upper(self.__confGet(conf, "run_synchronizer", "gstat"))[0]
        if self.__confGet(conf, "run_synchronizer", "osg"):
            self.run_synchro_osg = string.upper(self.__confGet(conf, "run_synchronizer", "osg"))[0]
        if self.__confGet(conf, "run_synchronizer", "osg_downtime"):
            self.run_synchro_osg_downtime = string.upper(self.__confGet(conf, "run_synchronizer", "osg_downtime"))[0]
        if self.__confGet(conf, "run_synchronizer", "vo_feeds"):
            self.run_synchro_vo_feeds = string.upper(self.__confGet(conf, "run_synchronizer", "vo_feeds"))[0]


    def __confGetSection(self, conf, section):
        """returns the value of all the configuration options in one section or None if not set"""
        try:
            options = {}
            for i in conf.items(section):
                options [i[0]] = i[1]
            return options
        except ConfigParser.Error:
            return None # ignore missing values


    def __confGet(self, conf, section, option):
        """returns the value of the configuration option or None if not set"""
        try:
            return conf.get(section, option)
        except ConfigParser.Error:
            return None # ignore missing values


    def __setupLogging(self):
        try:
            "creates and returns file logger"
            logging.config.fileConfig(self.logging_config)
            # creation of loggers - 'ATPSyslog' logger will output info in syslog and this will analyzed by Nagios check_config plugin.
            #'ATP' logger will output info. in /var/log/atp/atp.log
            self.logger = logging.getLogger('ATP')
            self.logger_syslog = logging.getLogger('ATPSyslog')
            try:
                self.logger.setLevel(int(self.log_level))
                self.logger_syslog.setLevel(int(self.log_level))
            except:
                self.logger.warn("Bad value for option log_level: %s", self.log_level)
                self.logger_syslog.warn("Bad value for option log_level: %s", self.log_level)
        except Exception, info:
            print "An error is encounted while setting up ATP logger-%s" %info
            sys.exit(1)

    def usage(self):
        "prints the command line options of the program"
        print """
                usage:""", os.path.basename(sys.argv[0]), """[options]

                options:
                -c file     read ATP config file
                -d db_file  read database config file
                -l log_file read ATP log files
                -h          display this help
                -n          don't commit changes to the database
                -v          run in verbose mode
                --help      see -h
                --db_commit see -n
              """


    def __parseArgs(self):
        """parses the command line arguments"""
        try:
            opts, args = getopt.getopt(sys.argv[1:], "c:d:l:hn", ["help", "db_commit"])
        except getopt.GetoptError, exception:
            print "Error while parsing arguments %s -%s" % (args, str(exception).strip())
            self.usage()
            sys.exit(1)

        for opt, arg in opts:
            if opt == "-c":
                self.__readConfig(arg)
            elif opt == "-d":
                self.__readDBConfig(arg)
            elif opt == "-l":
                self.__readLogConfig(arg)
            elif opt == "-h" or opt == "--help":
                self.usage()
                sys.exit()
            elif opt == "-n" or opt == "--db_commit":
                self.db_commit = 1


    def setAction(self, act):
        "define and log what we are doing right now"
        self.logger.info(act)
        self.action = act[0].lower() + act[1:]


    def getAction(self):
        "return the last action"
        return self.action

