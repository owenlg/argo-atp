##############################################################################
#
# NAME:        models.py
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
#         Django DB model
#
# AUTHORS:     Joshi Pradyumna, BARC
#              David Collados, CERN
#
# CREATED:     23-Nov-2009
#
# NOTES:
#
# MODIFIED:
#
##############################################################################
#
# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#     * Rearrange models' order
#     * Make sure each model has one field with primary_key=True
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin.py sqlcustom [appname]'
# into your database.

from django.db import models

YESNO_CHOICE= ((u'Y',u'Yes'), (u'N', u'No'),)

class QuerySetManager(models.Manager):
    def get_query_set(self):
        return self.model.QuerySet(self.model)

    def __getattr__(self, attr, *args):
        return getattr(self.get_query_set(), attr, *args)

class DataProvider(models.Model):
    id = models.AutoField(primary_key=True)
    updateminutes = models.IntegerField()
    lastruntime = models.DateTimeField(auto_now_add=True)
    name = models.CharField("Name", max_length=128,unique=True)
    class Meta:
        db_table = u'data_provider'
        ordering = ['name','lastruntime']
        verbose_name = u'DataProvider'
        verbose_name_plural = u'DataProviders'
    def __unicode__(self):
        return self.name


class Vo(models.Model):
    id = models.AutoField(primary_key=True)
    voname = models.CharField("Name", max_length=100, unique = True)
    isdeleted = models.CharField(max_length=1)
    #colour = models.CharField(max_length=10, null=True, blank = True)
    class Meta:
        db_table = u'vo'
        verbose_name = u'VO'
        verbose_name_plural = u'VOs'
        ordering = ('voname',)
    def __unicode__(self):
        return self.voname

class Country(models.Model):
    id = models.AutoField(primary_key=True)
    countryname = models.CharField("Name", max_length=50, unique = True)
    countryabbr = models.CharField("Abbreviation", max_length=50, null=True, blank=True)
    class Meta:
        db_table = u'country'
        verbose_name = u'Country'
        verbose_name_plural = u"Countries"
        ordering = ('countryname',)
    def __unicode__(self):
        return self.countryname

class Infrastructure(models.Model):
    id = models.AutoField(primary_key=True)
    infrastname = models.CharField("Name", max_length=255, unique=True)
    isdeleted = models.CharField(max_length=1,choices= YESNO_CHOICE, default='N')
    description = models.CharField(max_length=512, null=True, blank=True)
    class Meta:
        db_table = u'infrastructure'
        ordering = ['infrastname']
        verbose_name = u'Infrastructure'
        verbose_name_plural = u'Infrastructures'
    def __unicode__(self):
        return self.infrastname

class Project(models.Model):
    id = models.AutoField(primary_key = True)
    projectname = models.CharField("Name", max_length=255, unique = True)
    isdeleted = models.CharField(max_length=1)
    description = models.CharField(max_length=512, null=True, blank = True)
    infrastructure = models.ManyToManyField(Infrastructure, db_table=u'infr_is_in_proj')
    class Meta:
        db_table = u'project'
        ordering = ['projectname', 'infrastructure__infrastname']
        verbose_name = u'Project'
        verbose_name_plural = u'Projects'
    def __unicode__(self):
        return self.projectname


class Site(models.Model):
    infrasttype_choice = ((u'Production', u'Production'), (u'PPS', u'PPS'), (u'Test', u'Test'), (u'SC', u'SC'))

    id = models.AutoField(primary_key=True)
    infrast = models.ForeignKey(Infrastructure)
    ismonitored = models.CharField("Is Monitored?", max_length=1,choices=YESNO_CHOICE, default='Y')
    isdeleted = models.CharField(max_length=1,choices= YESNO_CHOICE, default='N')
    sitename = models.CharField("Name", max_length=100)
    certifstatus = models.CharField("Certified?", max_length=1, choices= YESNO_CHOICE, default='N')
    infrasttype = models.CharField("Infrastructure Type", max_length=128, choices=infrasttype_choice, default='Production')
    gocsiteid = models.CharField("GOCDB Site ID", max_length=38, null=True, blank=True)
    country = models.ForeignKey(Country, null=True, blank=True)
    latitude = models.CharField("Latitude", max_length=10, null=True, blank=True)
    longitude = models.FloatField(" Longitude", max_length=10, null=True, blank=True)
    contactemail = models.CharField("Contact Email", max_length=128, null=True, blank=True)
    timezone = models.CharField(max_length=128, null=True, blank=True)
    giisurl = models.CharField("GIIS URL", max_length=250, null=True, blank=True)
    contacttel = models.CharField("Contact Telephone", max_length=255, null=True, blank=True)
    sitedesc = models.CharField("Site Description", max_length=512, null=True, blank=True)
    siteoffname = models.CharField("Site Official Name", max_length=512, null=True, blank=True)
    class Meta:
        db_table = u'site'
        ordering = ['sitename', 'country__countryname', 'infrast__infrastname']
        verbose_name = u'Site'
        verbose_name_plural = u'Sites'
    def __unicode__(self):
        return self.sitename

class SiteLastSeen(models.Model):
    id = models.AutoField(primary_key=True)
    site = models.ForeignKey(Site)
    data_provider = models.ForeignKey(DataProvider)
    lastseen = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = u'site_last_seen'
        unique_together = ("site", "data_provider", "lastseen")
        ordering = ['site__sitename', 'data_provider__name']
        verbose_name = u'SiteLastSeen'
        verbose_name_plural = u'SiteLastSeens'

class SiteStoreCap(models.Model):
    site = models.ForeignKey(Site,primary_key=True)
    phycpucount = models.IntegerField(null=True, blank=True)
    logcpucount = models.IntegerField(null=True, blank=True)
    ksi2k = models.IntegerField(null=True, blank=True)
    hspec06 = models.IntegerField(null=True, blank=True)
    class Meta:
        db_table = u'site_store_cap'
        ordering = ['site__sitename']
        verbose_name = u'SiteStoreCap'
        verbose_name_plural = u'SiteStoreCaps'

class VoSitename(models.Model):
    id = models.AutoField(primary_key=True)
    vo = models.ForeignKey(Vo)
    site = models.ForeignKey(Site)
    sitename = models.CharField(max_length=128)
    isdeleted = models.CharField(max_length=1,choices= YESNO_CHOICE, default='N')
    class Meta:
        db_table = u'vo_sitename'
        unique_together = ("vo", "site")
        verbose_name = u'VoSitename'
        verbose_name_plural = u'VoSitenames'
        ordering = ['vo__voname', 'site__sitename','sitename']

class GroupType(models.Model):
    id = models.AutoField(primary_key=True)
    typename = models.CharField("Name", max_length=100, unique = True)
    isdeleted = models.CharField(max_length=1,choices= YESNO_CHOICE, default='N')
    description = models.CharField(max_length=255, null=True, blank=True)
    class Meta:
        db_table = u'group_type'
        verbose_name = u'GroupType'
        verbose_name_plural = u'GroupTypes'
        ordering = ('typename',)
    def __unicode__(self):
        return self.typename

class Groups(models.Model):
    id = models.AutoField(primary_key=True)
    group_type = models.ForeignKey(GroupType)
    groupname = models.CharField(max_length=100)
    isdeleted = models.CharField(max_length=1,choices= YESNO_CHOICE, default='N')
    description = models.CharField(max_length=255, null=True, blank=True)
    class Meta:
        db_table = u'groups'
        verbose_name = u'Groups'
        verbose_name_plural = u'Groups'
        #ordering = ['groupname', 'group_type__typename']
    def __unicode__(self):
        return self.groupname

class ServiceTypeFlavour(models.Model):
    id = models.AutoField(primary_key=True)
    flavourname = models.CharField("Name", max_length=128, unique=True)
    isdeleted = models.CharField(max_length=1,choices= YESNO_CHOICE, default='N')
    class Meta:
        db_table = u'service_type_flavour'
        verbose_name = u'ServiceTypeFlavour'
        verbose_name_plural = u'ServiceTypeFlavours'
        ordering = ['flavourname']
    def __unicode__(self):
        return self.flavourname

class Service(models.Model):
    id = models.AutoField(primary_key=True)
    flavour = models.ForeignKey(ServiceTypeFlavour)
    ismonitored = models.CharField("Is Monitored?", max_length=1,choices= YESNO_CHOICE, default='Y')
    iscore = models.CharField("Is Core?", max_length=1,choices= YESNO_CHOICE, default='N')
    isinproduction = models.CharField("Is in production?", max_length=1, choices= YESNO_CHOICE, default='N')
    isdeleted = models.CharField(max_length=1,choices= YESNO_CHOICE, default='N')
    serviceendpoint = models.CharField("Service Endpoint", max_length=256)
    hostname = models.CharField(max_length=512)
    ipv4 = models.IPAddressField(null=True, blank=True)
    site = models.ManyToManyField(Site, db_table=u'service_site') # manytomanyfield
    vo = models.ManyToManyField(Vo, db_table = u'service_vo')
    class Meta:
        db_table = u'service'
        ordering = ['hostname']
        verbose_name = u'Service'
        verbose_name_plural = u'Services'
    def __unicode__(self):
        return self.hostname

class ServiceLastSeen(models.Model):
    id =  models.AutoField(primary_key=True)
    service = models.ForeignKey(Service)
    data_provider = models.ForeignKey(DataProvider)
    lastseen = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = u'service_last_seen'
        verbose_name = u'ServiceLastSeen'
        verbose_name_plural = u'ServiceLastSeens'
        unique_together = ("service", "data_provider", "lastseen")
        ordering = ['service__hostname', 'data_provider__name']
#
# Grid Resources
#

class SpaceToken(models.Model):
    id = models.AutoField(primary_key=True)
    service = models.ForeignKey(Service)
    tokenname = models.CharField("Name", max_length=128)
    isdeleted = models.CharField(max_length=1,choices= YESNO_CHOICE, default='N')
    tokenpath = models.CharField("Path", max_length=256)
    class Meta:
        db_table = u'space_token'
        verbose_name = u'SpaceToken'
        verbose_name_plural = u'SpaceTokens'
        ordering = ['service__hostname', 'tokenname']
        unique_together = ("service", "tokenname")
    def __unicode__(self):
        return "%s : %s"%(self.service, self.tokenname)

class StokenLastSeen(models.Model):
    id = models.AutoField(primary_key=True)
    data_provider = models.ForeignKey(DataProvider)
    space_token = models.ForeignKey(SpaceToken)
    lastseen = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = u'stoken_last_seen'
        verbose_name = u'StokenLastSeen'
        verbose_name_plural = u'StoeknLastSeens'
        unique_together = ("data_provider", "space_token", "lastseen")
        ordering = ['space_token__tokenname','data_provider__name']
#
# WLCG MoU tables
#
class AccountingUnit(models.Model):
    id = models.AutoField(primary_key=True)
    accountingname = models.CharField(max_length=128)
    group = models.ForeignKey(Groups)
    site = models.ManyToManyField(Site, db_table='SITE_ACCOUNTING_UNIT')
    class Meta:
        db_table = u'accounting_unit'
        verbose_name = u'AccountingUnit'
        verbose_name_plural = u'AccountingUnits'
        ordering = ['accountingname','group__groupname']
    def __unicode__(self):
        return self.accountingname

class SupportLevel(models.Model):
    id = models.AutoField(primary_key=True)
    vo = models.ForeignKey(Vo)
    accounting_unit = models.ForeignKey(AccountingUnit)
    isdeleted = models.CharField(max_length=1,choices= YESNO_CHOICE, default='N')
    commitment = models.CharField("Commitment", max_length=128)
    class Meta:
        db_table = u'support_level'
        verbose_name = u'SupportLevel'
        verbose_name_plural = u'SupportLevels'
        unique_together = ("vo", "accounting_unit")
        ordering = ['accounting_unit__accountingname','vo__voname']

class Federation(models.Model):
    group = models.ForeignKey(Groups)
    accounting_unit = models.ForeignKey(AccountingUnit)
    fedabbr = models.CharField(max_length=80, blank=True)
    class Meta:
        db_table = u'federation'
        verbose_name = u'Federation'
        verbose_name_plural = u'Federations'
        ordering = ['accounting_unit__accountingname','vo__voname']

#
# GOCDB Stuff
#

class Downtime(models.Model):
    id = models.AutoField(primary_key=True)
    starttimestamp = models.DateTimeField()
    endtimestamp = models.DateTimeField()
    inserttimestamp = models.DateTimeField()
    isdeleted = models.CharField(max_length=1,choices= YESNO_CHOICE, default='N')
    classification = models.CharField(max_length=128, default='SCHEDULED')
    gocdowntimeid = models.DecimalField(max_digits=38, decimal_places=0, null=True, blank=True)
    osgdowntimeid = models.DecimalField(max_digits=38, decimal_places=0, null=True, blank=True)    
    severity = models.CharField("Severity", max_length=128, null=True, blank=True)
    description = models.CharField("Description", max_length=1000, null=True, blank=True)
    service = models.ManyToManyField(Service, db_table = 'service_downtime', null = True, blank = True)
    site = models.ManyToManyField(Site, db_table = 'site_downtime', null = True, blank = True)
    class Meta:
        db_table = u'downtime'
        ordering = ['starttimestamp']#,site__sitename,service__hostname']
        verbose_name = u'Downtime'
        verbose_name_plural = u'Downtimes'
    def __unicode__(self):
        return "%s : %s"%(self.id, self.description)

class Person(models.Model):
    id = models.AutoField(primary_key=True)
    dn = models.CharField("DN", max_length=256, null=True, blank=True)
    firstname = models.CharField("First Name", max_length=255)
    lastname = models.CharField("Last Name", max_length=255, null=True, blank=True)
    email = models.CharField("EMail", max_length=512, null=True, blank=True)
    telephone1 = models.CharField("Telephone No", max_length=50, null=True, blank=True)
    workhours = models.CharField("Working Hours", max_length=128, null=True, blank=True)
    class Meta:
        db_table = u'person'
        verbose_name = u'Person'
        verbose_name_plural = u'Persons'
        ordering = ['lastname','firstname','dn']
    def __unicode__(self):
        return self.dn

class Role(models.Model):
    id = models.AutoField(primary_key=True)
    rolename = models.CharField(max_length=256)
    class Meta:
        db_table = u'role'
        verbose_name = u'Role'
        verbose_name_plural = u'Roles'

#
# Groupings after here
#
class ProjServiceGroup(models.Model):
    id = models.AutoField(primary_key=True)
    project = models.ForeignKey(Project)
    service = models.ForeignKey(Service)
    groups = models.ForeignKey(Groups)
    isdeleted = models.CharField(max_length=1,choices= YESNO_CHOICE, default='N')
    class Meta:
        db_table = u'proj_service_group'
        unique_together = ("groups", "project","service")
        verbose_name = u'ProjServiceGroup'
        verbose_name_plural = u'ProjServiceGroups'
        ordering = ['project__projectname','service__hostname', 'groups__groupname']

class ProjSiteGroup(models.Model):
    id = models.AutoField(primary_key=True)
    project = models.ForeignKey(Project)
    site = models.ForeignKey(Site)
    groups = models.ForeignKey(Groups)
    isdeleted = models.CharField(max_length=1,choices= YESNO_CHOICE, default='N')
    class Meta:
        db_table = u'proj_site_group'
        unique_together = ("project", "site", "groups")
        verbose_name = u'ProjSiteGroup'
        verbose_name_plural = u'ProjSiteGroups'
        ordering = ['project__projectname','site__sitename','groups__groupname']

class VoSiteGroup(models.Model):
    id = models.AutoField(primary_key=True)
    site = models.ForeignKey(Site)
    vo = models.ForeignKey(Vo)
    groups = models.ForeignKey(Groups)
    isdeleted = models.CharField(max_length=1,choices= YESNO_CHOICE, default='N')
    class Meta:
        db_table = u'vo_site_group'
        unique_together = ("vo", "site", "groups")
        verbose_name = u'VoSiteGroup'
        verbose_name_plural = u'VoSiteGroups'
        ordering = ['vo__voname', 'site__sitename', 'groups__groupname']

class VoServiceGroup(models.Model):
    id = models.AutoField(primary_key=True)
    vo = models.ForeignKey(Vo)
    service = models.ForeignKey(Service)
    groups = models.ForeignKey(Groups)
    isdeleted = models.CharField(max_length=1,choices= YESNO_CHOICE, default='N')
    class Meta:
        db_table = u'vo_service_group'
        unique_together = ("vo", "service", "groups")
        verbose_name = u'VoServiceGroup'
        verbose_name_plural = u'VoServiceGroups'
        ordering = ['vo__voname', 'service__hostname', 'groups__groupname']

class ProjVoGroup(models.Model):
    id = models.AutoField(primary_key=True)
    project = models.ForeignKey(Project)
    vo = models.ForeignKey(Vo)
    groups = models.ForeignKey(Groups)
    isdeleted =  models.CharField(max_length=1,choices= YESNO_CHOICE, default='N')
    class Meta:
        db_table = u'proj_vo_group'
        unique_together = ("project", "vo", "groups")
        verbose_name = u'ProjVoGroup'
        verbose_name_plural = u'ProjVoGroups'
        ordering = ['project__projectname', 'vo__voname', 'groups__groupname']

class PersonGroupRole(models.Model):
    id = models.AutoField(primary_key=True)
    person = models.ForeignKey(Person)
    groups = models.ForeignKey(Groups)
    role = models.ForeignKey(Role)
    class Meta:
        db_table = u'person_group_role'
        unique_together = ("person", "groups", "role")
        verbose_name = u'PersonGroupRole'
        verbose_name_plural = u'PersonGroupRoles'
        ordering = ['person__lastname', 'groups__groupname' , 'role__rolename']

class ProjStokenGroup(models.Model):
    id = models.AutoField(primary_key=True)
    project = models.ForeignKey(Project)
    space_token = models.ForeignKey(SpaceToken)
    groups = models.ForeignKey(Groups)
    isdeleted =  models.CharField(max_length=1,choices= YESNO_CHOICE, default='N')
    class Meta:
        db_table = u'proj_stoken_group'
        unique_together = ("project", "space_token", "groups")
        verbose_name = u'ProjStokenGroup'
        verbose_name_plural = u'ProjStokenGroups'
        ordering = ['project__projectname', 'space_token__tokenname', 'groups__groupname']

class VoStokenGroup(models.Model):
    id = models.AutoField(primary_key=True)
    vo = models.ForeignKey(Vo)
    space_token = models.ForeignKey(SpaceToken)
    groups = models.ForeignKey(Groups)
    isdeleted = models.CharField(max_length=1,choices= YESNO_CHOICE, default='N')
    class Meta:
        db_table = u'vo_stoken_group'
        unique_together = ("vo", "space_token", "groups")
        verbose_name = u'VoStokenGroup'
        verbose_name_plural = u'VoStokenGroups'
        ordering = ['vo__voname', 'space_token__tokenname', 'groups__groupname']

class InfrServiceGroup(models.Model):
    id = models.AutoField(primary_key=True)
    infrast = models.ForeignKey(Infrastructure)
    service = models.ForeignKey(Service)
    groups = models.ForeignKey(Groups)
    isdeleted = models.CharField(max_length=1,choices= YESNO_CHOICE, default='N')
    class Meta:
        db_table = u'infr_service_group'
        unique_together = ("infrast", "service", "groups")
        verbose_name = u'InfrServiceGroup'
        verbose_name_plural = u'InfrServiceGroups'
        ordering = ['infrast__infrastname', 'service__hostname', 'groups__groupname']

class InfrStokenGroup(models.Model):
    id = models.AutoField(primary_key=True)
    infrast = models.ForeignKey(Infrastructure)
    groups = models.ForeignKey(Groups)
    space_token = models.ForeignKey(SpaceToken)
    isdeleted = models.CharField(max_length=1,choices= YESNO_CHOICE, default='N')
    class Meta:
        db_table = u'infr_stoken_group'
        unique_together = ("infrast", "space_token", "groups")
        verbose_name = u'InfrStokenGroup'
        verbose_name_plural = u'InfrStokenGroups'
        ordering = ['infrast__infrastname', 'space_token__tokenname', 'groups__groupname']

class ProjInfrGroup(models.Model):
    id = models.AutoField(primary_key=True)
    project = models.ForeignKey(Project)
    infrast = models.ForeignKey(Infrastructure)
    groups = models.ForeignKey(Groups)
    isdeleted = models.CharField(max_length=1,choices= YESNO_CHOICE, default='N')
    class Meta:
        db_table = u'proj_infr_group'
        unique_together = ("project", "infrast", "groups")
        verbose_name = u'ProjInfrGroup'
        verbose_name_plural = u'ProjInfrGroups'
        ordering = ['project__projectname', 'infrast__infrastname', 'groups__groupname']

class InfrVoGroup(models.Model):
    id = models.AutoField(primary_key=True)
    infrast = models.ForeignKey(Infrastructure)
    vo = models.ForeignKey(Vo)
    groups = models.ForeignKey(Groups)
    isdeleted = models.CharField(max_length=1,choices= YESNO_CHOICE, default='N')
    class Meta:
        db_table = u'infr_vo_group'
        unique_together = ("infrast", "vo", "groups")
        verbose_name = u'InfrVoGroup'
        verbose_name_plural = u'InfrVoGroups'
        ordering = ['infrast__infrastname', 'vo__voname', 'groups__groupname']

class SiteGroup(models.Model):
    id = models.AutoField(primary_key=True)
    site = models.ForeignKey(Site)
    groups = models.ForeignKey(Groups)
    isdeleted = models.CharField(max_length=1,choices= YESNO_CHOICE, default='N')
    class Meta:
        db_table = u'site_group'
        unique_together = ("site", "groups")
        verbose_name = u'SiteGroup'
        verbose_name_plural = u'SiteGroups'
        ordering = ['site__sitename', 'groups__groupname']

class ServiceGroup(models.Model):
    id = models.AutoField(primary_key=True)
    service = models.ForeignKey(Service)
    groups = models.ForeignKey(Groups)
    isdeleted = models.CharField(max_length=1,choices= YESNO_CHOICE, default='N')
    class Meta:
        db_table = u'service_group'
        unique_together = ("service", "groups")
        verbose_name = u'ServiceGroup'
        verbose_name_plural = u'ServiceGroups'
        ordering = ['service__hostname', 'groups__groupname']

class VoGroup(models.Model):
    id = models.AutoField(primary_key=True)
    vo = models.ForeignKey(Vo)
    groups = models.ForeignKey(Groups)
    isdeleted = models.CharField(max_length=1,choices= YESNO_CHOICE, default='N')
    class Meta:
        db_table = u'vo_group'
        unique_together = ("vo", "groups")
        verbose_name = u'VoGroup'
        verbose_name_plural = u'VoGroups'
        ordering = ['vo__voname', 'groups__groupname']

class Contact(models.Model):
    id = models.AutoField(primary_key=True)
    dn = models.CharField("DN", max_length=255, blank=True)
    name = models.CharField("Name", max_length=255,null=True, blank=True)
    email = models.CharField("E-mail", max_length=255, null=True, blank=True)
    telephone = models.CharField("Telephone", max_length=255, null=True, blank=True)
    #isdeleted = models.CharField(max_length=1,choices= YESNO_CHOICE, default='N')
    class Meta:
        db_table = u'contact'
        unique_together = ("dn",)
        verbose_name = u'Contact'
        verbose_name_plural = u'Contacts'
        ordering = ['id', 'dn']
    def __unicode__(self):
        return self.dn

class ContactSite(models.Model):
    id = models.AutoField(primary_key=True)
    contact = models.ForeignKey(Contact)
    site = models.ForeignKey(Site)
    role = models.CharField("Role", max_length=255, null=True, blank=True)
    #isdeleted = models.CharField(max_length=1,choices= YESNO_CHOICE, default='N')
    class Meta:
        db_table = u'contact_site'
        unique_together = ("contact", "site", "role")
        verbose_name = u'ContactSite'
        verbose_name_plural = u'ContactSites'
        ordering = ['contact', 'site']
    def __unicode__(self):
        return ("%s:%s")%(self.contact,self.site)

class ContactGroup(models.Model):
    id = models.AutoField(primary_key=True)
    contact = models.ForeignKey(Contact)
    groups = models.ForeignKey(Groups)
    role = models.CharField("Role", max_length=255, null=True, blank=True)
    #isdeleted = models.CharField(max_length=1,choices= YESNO_CHOICE, default='N')
    class Meta:
        db_table = u'contact_group'
        unique_together = ("contact", "groups", "role")
        verbose_name = u'ContactGroup'
        verbose_name_plural = u'ContactGroups'
        ordering = ['contact', 'groups']
    def __unicode__(self):
        return ("%s:%s")%(self.contact,self.group)

class ContactVo(models.Model):
    id = models.AutoField(primary_key=True)
    contact = models.ForeignKey(Contact)
    vo = models.ForeignKey(Vo)
    #role = models.CharField("Role", max_length=255, null=True, blank=True)
    #isdeleted = models.CharField(max_length=1,choices= YESNO_CHOICE, default='N')
    class Meta:
        db_table = u'contact_vo'
        unique_together = ("contact", "vo")
        verbose_name = u'ContactVo'
        verbose_name_plural = u'ContactVos'
        ordering = ['contact', 'vo']
    def __unicode__(self):
        return ("%s:%s")%(self.contact,self.vo)

class ServiceMap(Service):
    class Meta:
        proxy = True
        app_label = 'atp'
        verbose_name = 'Servicemap'
        verbose_name_plural = 'Servicemap'
        ordering = ['serviceendpoint']
    def __unicode__(self):
        return self.serviceendpoint

class ServiceSite(Service):
    class Meta:
        proxy = True
        app_label = 'atp'
        verbose_name = 'Service-Site'
        verbose_name_plural = 'Service-Site'
        ordering = ['serviceendpoint']
    def __unicode__(self):
        return self.serviceendpoint
    


