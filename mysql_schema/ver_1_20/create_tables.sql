-- ----------------------------------------------------------------------------
--
-- NAME:        create_tables.sql
--
-- FACILITY:    SAM (Service Availability Monitoring)
--
-- COPYRIGHT:
--         Copyright (c) 2009, Members of the EGEE Collaboration.
--         http://www.eu-egee.org/partners/
--         Licensed under the Apache License, Version 2.0.
--         http://www.apache.org/licenses/LICENSE-2.0
--         This software is provided "as is", without warranties
--         or conditions of any kind, either express or implied.
--
-- DESCRIPTION:
--         MySQL ATP DB tables
--
-- AUTHORS:     David Collados, CERN
--              Joshi Pradyumna, BARC
--
-- CREATED:     23-Nov-2009
-- 
-- MODIFIED: 25-Nov-2010 By Joshi
--
-- NOTES:
--
-- MODIFIED:
--
-- ----------------------------------------------------------------------------

SET FOREIGN_KEY_CHECKS = 0;

-- -------------------------------------
-- Tables

DROP TABLE IF EXISTS `country`;
CREATE TABLE `country` (
  `id` INTEGER AUTO_INCREMENT NOT NULL,
  `countryname` VARCHAR(50) NOT NULL,
  `code` VARCHAR(2) NOT NULL,
  `countryabbr` VARCHAR(50) NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `country_code_un` (`code`(2)),
  UNIQUE INDEX `country_countryname_un` (`countryname`(50))
)
ENGINE = INNODB;


DROP TABLE IF EXISTS `contact`;
CREATE TABLE `contact` (
  `id` INTEGER AUTO_INCREMENT NOT NULL,
  `dn` VARCHAR(256) NOT NULL,
  `name` VARCHAR(256) ,
  `email` VARCHAR(256) ,
  `telephone` VARCHAR(256) ,  
  PRIMARY KEY (`id`),
  UNIQUE INDEX `countact_dn` (`dn`(256))
)
ENGINE = INNODB;


DROP TABLE IF EXISTS `contact_group`;
CREATE TABLE `contact_group` (
  `id` INTEGER AUTO_INCREMENT NOT NULL,
  `groups_id` INTEGER NOT NULL,
  `contact_id` INTEGER NOT NULL,  
  `role` VARCHAR(256) ,  
  PRIMARY KEY (`id`) ,
  UNIQUE INDEX `contact_group_groups_id_contact_id_role` (`groups_id`,`contact_id`, `role`(256)) ,
  CONSTRAINT `contact_group_groups_id_fk` FOREIGN KEY `contact_group_groups_id_fk` (`groups_id`)
    REFERENCES `groups` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `contact_group_contact_id_fk` FOREIGN KEY `contact_group_contact_id_fk` (`contact_id`)
    REFERENCES `contact` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
)
ENGINE = INNODB;


DROP TABLE IF EXISTS `contact_site`;
CREATE TABLE `contact_site` (
  `id` INTEGER AUTO_INCREMENT NOT NULL,
  `contact_id` INTEGER NOT NULL,  
  `site_id` INTEGER NOT NULL,
  `role` VARCHAR(256) ,  
  PRIMARY KEY (`id`) ,
  UNIQUE INDEX `contact_site_contact_id_site_id_role` (`contact_id`,`site_id`, `role`(256)) ,
  CONSTRAINT `contact_site_contact_id_fk` FOREIGN KEY `contact_site_contact_id_fk` (`contact_id`)
    REFERENCES `contact` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `contact_site_site_id_fk` FOREIGN KEY `contact_site_site_id_fk` (`site_id`)
    REFERENCES `site` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
)
ENGINE = INNODB;


DROP TABLE IF EXISTS `contact_vo`;
CREATE TABLE `contact_vo` (
  `id` INTEGER AUTO_INCREMENT NOT NULL,
  `contact_id` INTEGER NOT NULL,  
  `vo_id` INTEGER NOT NULL,
  PRIMARY KEY (`id`) ,
  UNIQUE INDEX `contact_vo_contact_id_vo_id_role` (`contact_id`,`vo_id`) ,
  CONSTRAINT `contact_vo_contact_id_fk` FOREIGN KEY `contact_vo_contact_id_fk` (`contact_id`)
    REFERENCES `contact` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `contact_vo_vo_id_fk` FOREIGN KEY `contact_vo_vo_id_fk` (`vo_id`)
    REFERENCES `vo` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
)
ENGINE = INNODB;


DROP TABLE IF EXISTS `downtime`;
CREATE TABLE `downtime` (
  `id` INTEGER AUTO_INCREMENT NOT NULL,
  `starttimestamp` DATETIME NOT NULL,
  `endtimestamp` DATETIME NOT NULL,
  `inserttimestamp` DATETIME NOT NULL,
  `isdeleted` VARCHAR(1) NOT NULL DEFAULT 'N',
  `classification` VARCHAR(128) NOT NULL DEFAULT 'SCHEDULED',
  `gocdowntimeid` INTEGER NULL,
  `osgdowntimeid` INTEGER NULL,
  `severity` VARCHAR(128) NULL,
  `description` VARCHAR(1000) NULL,
  `gocdbpk` VARCHAR(128) NULL,
  PRIMARY KEY (`id`),
  INDEX `downtime_start_end_downtid_idx` (`starttimestamp`, `endtimestamp`, `id`)
)
ENGINE = INNODB;


DROP TABLE IF EXISTS `groups`;
CREATE TABLE `groups` (
  `id` INTEGER AUTO_INCREMENT NOT NULL,
  `group_type_id` INTEGER NOT NULL,
  `groupname` VARCHAR(100) NOT NULL,
  `isdeleted` VARCHAR(1) NOT NULL DEFAULT 'N',
  `description` VARCHAR(255) NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `groups_groupname_un` (`groupname`(100), `group_type_id`),
  CONSTRAINT `groups_group_type_fk` FOREIGN KEY `groups_group_type_fk` (`group_type_id`)
    REFERENCES `group_type` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
)
ENGINE = INNODB;


DROP TABLE IF EXISTS `group_type`;
CREATE TABLE `group_type` (
  `id` INTEGER AUTO_INCREMENT NOT NULL,
  `typename` VARCHAR(100) NOT NULL,
  `isdeleted` VARCHAR(1) NOT NULL DEFAULT 'N',
  `description` VARCHAR(255) NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `group_type_typename_un` (`typename`(100))
)
ENGINE = INNODB;


DROP TABLE IF EXISTS `group_link`;
CREATE TABLE `group_link` (
  `id` INTEGER AUTO_INCREMENT NOT NULL,
  `groups_id_tier` INTEGER NOT NULL,
  `groups_id_site` INTEGER NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `group_link_un` (`groups_id_tier`,`groups_id_site`) ,
CONSTRAINT `group_link_groups_id_tier_fk` FOREIGN KEY `group_link_groups_id_tier_fk` (`groups_id_tier`)
  REFERENCES `groups` (`id`)
  ON DELETE NO ACTION
  ON UPDATE NO ACTION,
CONSTRAINT `group_link_groups_id_site_fk` FOREIGN KEY `group_link_groups_id_site_fk` (`groups_id_site`)
  REFERENCES `groups` (`id`)
  ON DELETE NO ACTION
  ON UPDATE NO ACTION
)
ENGINE = INNODB;


DROP TABLE IF EXISTS `infrastructure`;
CREATE TABLE `infrastructure` (
  `id` INTEGER AUTO_INCREMENT NOT NULL,
  `infrastname` VARCHAR(256) NOT NULL,
  `isdeleted` VARCHAR(1) NOT NULL DEFAULT 'N',
  `description` VARCHAR(512) NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `infrastructure_infrastname_un` (`infrastname`(256))
)
ENGINE = INNODB;


DROP TABLE IF EXISTS `project`;
CREATE TABLE `project` (
  `id` INTEGER AUTO_INCREMENT NOT NULL,
  `projectname` VARCHAR(256) NOT NULL,
  `isdeleted` VARCHAR(1) NOT NULL DEFAULT 'N',
  `description` VARCHAR(512) NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `project_projectname_un` (`projectname`(256))
)
ENGINE = INNODB;


DROP TABLE IF EXISTS `service`;
CREATE TABLE `service` (
  `id` INTEGER AUTO_INCREMENT NOT NULL,
  `flavour_id` INTEGER NOT NULL,
  `ismonitored` VARCHAR(1) NOT NULL DEFAULT 'Y',
  `iscore` VARCHAR(1) NOT NULL DEFAULT 'N',
  `isinproduction` VARCHAR(1) NOT NULL DEFAULT 'N',
  `isdeleted` VARCHAR(1) NOT NULL DEFAULT 'N',
  `serviceendpoint` VARCHAR(256) NOT NULL,
  `hostname` VARCHAR(512) NOT NULL,
  `ipv4` VARCHAR(15) NULL,
  `gocdbpk` VARCHAR(128) NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `service_hostname_flavor_un` (`hostname`(500), `flavour_id`),
  CONSTRAINT `service_stype_flavour_fk` FOREIGN KEY `service_stype_flavour_fk` (`flavour_id`)
    REFERENCES `service_type_flavour` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
)
ENGINE = INNODB;


DROP TABLE IF EXISTS `service_downtime`;
CREATE TABLE `service_downtime` (
  `id` INTEGER AUTO_INCREMENT NOT NULL,
  `service_id` INTEGER NOT NULL,
  `downtime_id` INTEGER NOT NULL,
  `isdeleted` VARCHAR(1) NOT NULL DEFAULT 'N',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `service_downtime_un` (`service_id`, `downtime_id`),
  CONSTRAINT `service_downtime_downtime_fk` FOREIGN KEY `service_downtime_downtime_fk` (`downtime_id`)
    REFERENCES `downtime` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `service_downtime_service_fk` FOREIGN KEY `service_downtime_service_fk` (`service_id`)
    REFERENCES `service` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
)
ENGINE = INNODB;


DROP TABLE IF EXISTS `service_last_seen`;
CREATE TABLE `service_last_seen` (
  `id` INTEGER AUTO_INCREMENT NOT NULL,
  `service_id` INTEGER NOT NULL,
  `synchronizer_id` INTEGER NOT NULL,
  `lastseen` DATETIME NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `service_last_seen_un` (`service_id`, `synchronizer_id`),
  CONSTRAINT `service_last_seen_service_fk` FOREIGN KEY `service_last_seen_service_fk` (`service_id`)
    REFERENCES `service` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `service_lseen_synchro_fk` FOREIGN KEY `service_lseen_synchro_fk` (`synchronizer_id`)
    REFERENCES `synchronizer` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
)
ENGINE = INNODB;


DROP TABLE IF EXISTS `service_site`;
CREATE TABLE `service_site` (
  `id` INTEGER AUTO_INCREMENT NOT NULL,
  `service_id` INTEGER NOT NULL,
  `site_id` INTEGER NOT NULL,
  `isdeleted` VARCHAR(1) NOT NULL DEFAULT 'N',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `service_site_un` (`service_id`, `site_id`),
  CONSTRAINT `service_site_service_fk` FOREIGN KEY `service_site_service_fk` (`service_id`)
    REFERENCES `service` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `service_site_site_fk` FOREIGN KEY `service_site_site_fk` (`site_id`)
    REFERENCES `site` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
)
ENGINE = INNODB;


DROP TABLE IF EXISTS `service_type_flavour`;
CREATE TABLE `service_type_flavour` (
  `id` INTEGER AUTO_INCREMENT NOT NULL,
  `flavourname` VARCHAR(128) NOT NULL,
  `isdeleted` VARCHAR(1) NOT NULL DEFAULT 'N',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `serv_type_id_flavour_un` (`flavourname`(128))
)
ENGINE = INNODB;


DROP TABLE IF EXISTS `service_vo`;
CREATE TABLE `service_vo` (
  `id` INTEGER AUTO_INCREMENT NOT NULL,
  `vo_id` INTEGER NOT NULL,
  `service_id` INTEGER NOT NULL,
  `isdeleted` VARCHAR(1) NOT NULL DEFAULT 'N',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `service_vo_un` (`vo_id`, `service_id`),
  CONSTRAINT `service_vo_service_fk` FOREIGN KEY `service_vo_service_fk` (`service_id`)
    REFERENCES `service` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `service_vo_vo_fk` FOREIGN KEY `service_vo_vo_fk` (`vo_id`)
    REFERENCES `vo` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
)
ENGINE = INNODB;


DROP TABLE IF EXISTS `site`;
CREATE TABLE `site` (
  `id` INTEGER AUTO_INCREMENT NOT NULL,
  `infrast_id` INTEGER NOT NULL,
  `ismonitored` CHAR(1) NOT NULL DEFAULT 'Y',
  `isdeleted` VARCHAR(1) NOT NULL DEFAULT 'N',
  `sitename` VARCHAR(100) NOT NULL,
  `certifstatus` VARCHAR(128) NOT NULL DEFAULT 'N',
  `infrasttype` VARCHAR(128) NOT NULL DEFAULT 'Production',
  `gocsiteid` VARCHAR(50) NULL,
  `country_id` INTEGER NULL,
  `latitude` VARCHAR(20) NULL,
  `longitude` VARCHAR(20) NULL,
  `contactemail` VARCHAR(128) NULL,
  `timezone` VARCHAR(128) NULL,
  `giisurl` VARCHAR(250) NULL,
  `contacttel` VARCHAR(255) NULL,
  `sitedesc` VARCHAR(512) NULL,
  `siteoffname` VARCHAR(512) NULL,
  `gocdbpk` VARCHAR(128) NULL,
  `gocdbsiteabbr` VARCHAR(50) NULL,
  PRIMARY KEY (`id`, `certifstatus`, `infrasttype`),
  INDEX `site_countryid_idx` (`country_id`),
  INDEX `site_sid_certstat_inftype_idx` (`id`, `certifstatus`(128), `infrasttype`(128)),
  UNIQUE INDEX `site_sitename_infrast_idx` (`sitename`(100), `infrast_id`),
  INDEX `site_timezone_idx` (`timezone`(128)),
  CONSTRAINT `site_country_fk` FOREIGN KEY `site_country_fk` (`country_id`)
    REFERENCES `country` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `site_infrastructure_fk` FOREIGN KEY `site_infrastructure_fk` (`infrast_id`)
    REFERENCES `infrastructure` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
)
ENGINE = INNODB;


DROP TABLE IF EXISTS `site_downtime`;
CREATE TABLE `site_downtime` (
  `id` INTEGER AUTO_INCREMENT NOT NULL,
  `site_id` INTEGER NOT NULL,
  `downtime_id` INTEGER NOT NULL,
  `isdeleted` VARCHAR(1) NOT NULL DEFAULT 'N',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `site_downtime_un` (`site_id`, `downtime_id`),
  CONSTRAINT `site_downtime_downtime_fk` FOREIGN KEY `site_downtime_downtime_fk` (`downtime_id`)
    REFERENCES `downtime` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `site_downtime_site_fk` FOREIGN KEY `site_downtime_site_fk` (`site_id`)
    REFERENCES `site` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
)
ENGINE = INNODB;


DROP TABLE IF EXISTS `site_group`;
CREATE TABLE `site_group` (
  `id` INTEGER AUTO_INCREMENT NOT NULL,
  `site_id` INTEGER NOT NULL,
  `groups_id` INTEGER NOT NULL,
  `isdeleted` VARCHAR(1) NOT NULL DEFAULT 'N',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `site_group_un` (`site_id`, `groups_id`),
  CONSTRAINT `site_group_groups_fk` FOREIGN KEY `site_group_groups_fk` (`groups_id`)
    REFERENCES `groups` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `site_group_site_fk` FOREIGN KEY `site_group_site_fk` (`site_id`)
    REFERENCES `site` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
)
ENGINE = INNODB;


DROP TABLE IF EXISTS `site_last_seen`;
CREATE TABLE `site_last_seen` (
  `id` INTEGER AUTO_INCREMENT NOT NULL,
  `site_id` INTEGER NOT NULL,
  `synchronizer_id` INTEGER NOT NULL,
  `lastseen` DATETIME NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `site_last_seen_un` (`site_id`, `synchronizer_id`),
  CONSTRAINT `site_last_seen_site_fk` FOREIGN KEY `site_last_seen_site_fk` (`site_id`)
    REFERENCES `site` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `site_lseen_synchro_fk` FOREIGN KEY `site_lseen_synchro_fk` (`synchronizer_id`)
    REFERENCES `synchronizer` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
)
ENGINE = INNODB;


DROP TABLE IF EXISTS `site_store_cap`;
CREATE TABLE `site_store_cap` (
  `site_id` INTEGER NOT NULL,
  `phycpucount` INTEGER NOT NULL,
  `logcpucount` INTEGER NOT NULL,
  `hspec06` INTEGER NOT NULL,
  `ksi2k` INTEGER NOT NULL,
  PRIMARY KEY (`site_id`),
  CONSTRAINT `site_store_cap_site_fk` FOREIGN KEY `site_store_cap_site_fk` (`site_id`)
    REFERENCES `site` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
)
ENGINE = INNODB;


DROP TABLE IF EXISTS `space_token`;
CREATE TABLE `space_token` (
  `id` INTEGER AUTO_INCREMENT NOT NULL,
  `service_id` INTEGER NOT NULL,
  `tokenname` VARCHAR(128) NOT NULL DEFAULT 'N.A.',
  `isdeleted` VARCHAR(1) NOT NULL DEFAULT 'N',
  `tokenpath` VARCHAR(256) NOT NULL DEFAULT 'N.A.',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `space_token_un` (`service_id`, `tokenname`(128)),
  CONSTRAINT `space_token_service_fk` FOREIGN KEY `space_token_service_fk` (`service_id`)
    REFERENCES `service` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
)
ENGINE = INNODB;


DROP TABLE IF EXISTS `stoken_last_seen`;
CREATE TABLE `stoken_last_seen` (
  `id` INTEGER AUTO_INCREMENT NOT NULL,
  `space_token_id` INTEGER NOT NULL,
  `synchronizer_id` INTEGER NOT NULL,
  `lastseen` DATETIME NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `stoken_last_seen_un` (`space_token_id`, `synchronizer_id`),
  CONSTRAINT `stoken_last_seen_stoken_fk` FOREIGN KEY `stoken_last_seen_stoken_fk` (`space_token_id`)
    REFERENCES `space_token` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `stoken_l_seen_synchro_fk` FOREIGN KEY `stoken_l_seen_synchro_fk` (`synchronizer_id`)
    REFERENCES `synchronizer` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
)
ENGINE = INNODB;


DROP TABLE IF EXISTS `synchronizer`;
CREATE TABLE `synchronizer` (
  `id` INTEGER AUTO_INCREMENT NOT NULL,
  `name` VARCHAR(512) NOT NULL,
  `updateminutes` INTEGER NOT NULL DEFAULT 30,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `synchronizer_name_un` (`name`)
)
ENGINE = INNODB;


DROP TABLE IF EXISTS `synchronizer_lastrun`;
CREATE TABLE `synchronizer_lastrun` (
  `id` INTEGER AUTO_INCREMENT NOT NULL,
  `synchronizer_id` INTEGER NOT NULL,
  `succeed` VARCHAR(1) NOT NULL DEFAULT 'N',
  `lastexecution` DATETIME NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `synchronizer_lastrun_synchronizer_un` (`synchronizer_id`, `lastexecution`),
  CONSTRAINT `synchro_l_seen_synchro_fk` FOREIGN KEY `synchro_l_seen_synchro_fk` (`synchronizer_id`)
    REFERENCES `synchronizer` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
)
ENGINE = INNODB;


DROP TABLE IF EXISTS `vo`;
CREATE TABLE `vo` (
  `id` INTEGER AUTO_INCREMENT NOT NULL,
  `voname` VARCHAR(100) NOT NULL,
  `isdeleted` VARCHAR(1) NOT NULL DEFAULT 'N',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `vo_voname_idx` (`voname`(100))
)
ENGINE = INNODB;

DROP TABLE IF EXISTS `vo_site_group`;
CREATE TABLE `vo_site_group` (
  `id` INTEGER AUTO_INCREMENT NOT NULL,
  `vo_id` INTEGER NOT NULL,
  `site_id` INTEGER NOT NULL,
  `groups_id` INTEGER NOT NULL,
  `isdeleted` VARCHAR(1) NOT NULL DEFAULT 'N',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `vo_site_group_un` (`vo_id`, `site_id`, `groups_id`),
  CONSTRAINT `vo_site_group_group_fk` FOREIGN KEY `vo_site_group_group_fk` (`groups_id`)
    REFERENCES `groups` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `vo_site_group_site_fk` FOREIGN KEY `vo_site_group_site_fk` (`site_id`)
    REFERENCES `site` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `vo_site_group_vo_fk` FOREIGN KEY `vo_site_group_vo_fk` (`vo_id`)
    REFERENCES `vo` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
)
ENGINE = INNODB;

DROP TABLE IF EXISTS `vo_service_group`;
CREATE TABLE `vo_service_group` (
  `id` INTEGER AUTO_INCREMENT NOT NULL,
  `vo_id` INTEGER NOT NULL,
  `service_id` INTEGER NOT NULL,
  `groups_id` INTEGER NOT NULL,
  `isdeleted` VARCHAR(1) NOT NULL DEFAULT 'N',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `vo_service_group_un` (`vo_id`, `service_id`, `groups_id`),
  CONSTRAINT `vo_service_group_groups_fk` FOREIGN KEY `vo_service_group_groups_fk` (`groups_id`)
    REFERENCES `groups` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `vo_service_group_service_fk` FOREIGN KEY `vo_service_group_service_fk` (`service_id`)
    REFERENCES `service` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `vo_service_group_vo_fk` FOREIGN KEY `vo_service_group_vo_fk` (`vo_id`)
    REFERENCES `vo` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
)
ENGINE = INNODB;


DROP TABLE IF EXISTS `vo_sitename`;
CREATE TABLE `vo_sitename` (
  `id` INTEGER AUTO_INCREMENT NOT NULL,
  `vo_id` INTEGER NOT NULL,
  `site_id` INTEGER NOT NULL,
  `sitename` VARCHAR(128) NOT NULL,
  `isdeleted` VARCHAR(1) NOT NULL DEFAULT 'N',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `vo_sitename_void_siteid_un` (`vo_id`, `site_id`),
  UNIQUE INDEX `vo_sitename_void_sitename_un` (`vo_id`, `sitename`(128)),
  CONSTRAINT `vo_sitename_site_fk` FOREIGN KEY `vo_sitename_site_fk` (`site_id`)
    REFERENCES `site` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `vo_sitename_vo_fk` FOREIGN KEY `vo_sitename_vo_fk` (`vo_id`)
    REFERENCES `vo` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
)
ENGINE = INNODB;


DROP TABLE IF EXISTS `vo_group`;
CREATE TABLE `vo_group` (
  `id` INTEGER AUTO_INCREMENT NOT NULL,
  `vo_id` INTEGER NOT NULL,
  `groups_id` INTEGER NOT NULL,
  `isdeleted` VARCHAR(1)  NOT NULL DEFAULT 'N',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `vo_group_un` (`vo_id`, `groups_id`),
  CONSTRAINT `vo_group_groups_fk` FOREIGN KEY `vo_group_groups_fk` (`groups_id`)
    REFERENCES `groups` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `vo_group_vo_fk` FOREIGN KEY `vo_group_vo_fk` (`vo_id`)
    REFERENCES `vo` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
)
ENGINE = INNODB;

DROP TABLE IF EXISTS `service_group`;
CREATE TABLE `service_group` (
  `id` INTEGER AUTO_INCREMENT NOT NULL,
  `service_id` INTEGER NOT NULL,
  `groups_id` INTEGER NOT NULL,
  `isdeleted` VARCHAR(1) NOT NULL DEFAULT 'N',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `service_group_un` (`service_id`, `groups_id`),
  CONSTRAINT `service_group_groups_fk` FOREIGN KEY `service_group_groups_fk` (`groups_id`)
    REFERENCES `groups` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `service_group_service_fk` FOREIGN KEY `service_group_service_fk` (`service_id`)
    REFERENCES `service` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
)
ENGINE = INNODB;

DROP TABLE IF EXISTS `vo_stoken_group`;
CREATE TABLE `vo_stoken_group` (
  `id` INTEGER AUTO_INCREMENT NOT NULL,
  `vo_id` INTEGER NOT NULL,
  `space_token_id` INTEGER NOT NULL,
  `groups_id` INTEGER NOT NULL,
  `isdeleted` VARCHAR(1) NOT NULL DEFAULT 'N',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `vo_stoken_group_un` (`vo_id`, `space_token_id`, `groups_id`),
  CONSTRAINT `vo_stoken_group_groups_fk` FOREIGN KEY `vo_stoken_group_groups_fk` (`groups_id`)
    REFERENCES `groups` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `vo_stoken_group_space_token_fk` FOREIGN KEY `vo_stoken_group_space_token_fk` (`space_token_id`)
    REFERENCES `space_token` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `vo_stoken_group_vo_fk` FOREIGN KEY `vo_stoken_group_vo_fk` (`vo_id`)
    REFERENCES `vo` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
)
ENGINE = INNODB;

SET FOREIGN_KEY_CHECKS = 1;

-- Alter character set and collations to latin1 and latin1_general_ci for all the tables
-- use information_schema;
-- SELECT CONCAT('ALTER TABLE ', table_name, ' convert to CHARACTER SET latin1 COLLATE latin1_general_ci', ';') FROM information_schema.tables WHERE table_schema ='atp';
-- ----------------------------------------------------------------------
-- EOF
