-- ----------------------------------------------------------------------------
--
-- NAME:        create_procedures.sql
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
--         MySQL ATP DB procedures
--
-- AUTHORS:     David Collados, CERN
--              Joshi Pradyumna, BARC
--
-- CREATED:     23-Nov-2009
--
-- NOTES:
--
-- MODIFIED:    18-July-2011
--
-- ----------------------------------------------------------------------------


-- -------------------------
-- Procedure: SERVICE_UPDATE
-- ---------------------------
DELIMITER $$

DROP PROCEDURE IF EXISTS `SERVICE_UPDATE`$$
CREATE PROCEDURE `SERVICE_UPDATE`(IN a_infrast_name VARCHAR(256),
  IN a_site_name VARCHAR(100), IN a_service_endpoint VARCHAR(256),
  IN a_service_flavour VARCHAR(128), IN a_ipv4 VARCHAR(15),
  IN a_hostname VARCHAR(512), IN a_is_in_prod VARCHAR(1),
  IN a_is_core VARCHAR(1), IN a_is_monitored VARCHAR(1),
  IN a_synchronizer_name VARCHAR(128),IN a_gocdbpk VARCHAR(128),
  INOUT sucess_flag TINYINT)
BEGIN

  DECLARE v_synchronizerId   INTEGER;
  DECLARE v_infrastId        INTEGER;
  DECLARE v_ipv4             VARCHAR(15);
  DECLARE v_isCore           VARCHAR(1);
  DECLARE v_isDeleted        VARCHAR(1);
  DECLARE v_isInProduction   VARCHAR(1);
  DECLARE v_isMonitored      VARCHAR(1);
  DECLARE v_servFlavourId    INTEGER;
  DECLARE v_hostname         VARCHAR(512);
  DECLARE v_serviceEndpoint  VARCHAR(512);
  DECLARE v_serviceId        INTEGER;
  DECLARE v_siteId           INTEGER;
  DECLARE v_updateTime       TIMESTAMP;
  DECLARE v_gocdbpk          VARCHAR(128);
  DECLARE v_insert           INTEGER DEFAULT 0;
  DECLARE v_servicegroupId INTEGER DEFAULT -1;
  DECLARE v_groupId          INTEGER DEFAULT -1;
  DECLARE v_voId             INTEGER DEFAULT -1;
  DECLARE v_serviceSiteId    INTEGER DEFAULT -1;
  DECLARE v_servicelastseenId INTEGER DEFAULT -1;
  DECLARE v_regionId         INTEGER DEFAULT -1;
  DECLARE v_sitegroupId      INTEGER;
  DECLARE v_ConstRegion      VARCHAR(15);
  DECLARE v_ConstSite        VARCHAR(15);
  DECLARE v_voservicegroupId INTEGER DEFAULT -1;

  SET v_ConstRegion := 'Region';
  SET v_ConstSite := 'Site';

  SET sucess_flag=0;
 
  SET v_synchronizerId = get_synchronizer_id(a_synchronizer_name);

 
  SET v_infrastId = get_infrastructure_id(a_infrast_name);

 
  SET v_siteId = get_site_id(a_site_name, v_infrastId);

 
  SET v_servFlavourId = get_service_flavour_id(a_service_flavour);
 
  SET v_voId = get_vo_id('ops');
 
  SET v_updateTime = CURRENT_TIMESTAMP;

 
  IF ((v_synchronizerId != -1) AND (v_siteId != -1) AND (v_servFlavourId != -1) AND (v_voId != -1)) THEN
    BEGIN
        DECLARE EXIT HANDLER FOR NOT FOUND
            BEGIN
                INSERT INTO service(flavour_id, ismonitored, iscore, isinproduction,
                serviceendpoint, hostname, ipv4, gocdbpk)
                VALUES (v_servFlavourId, a_is_monitored, a_is_core, a_is_in_prod,
                a_service_endpoint, lower(a_hostname), a_ipv4, a_gocdbpk);

                SET v_serviceId=LAST_INSERT_ID();

                INSERT INTO service_site(service_id, site_id)
                VALUES (v_serviceId, v_siteId);
               
                INSERT INTO service_last_seen(service_id, synchronizer_id, lastseen)
                VALUES (v_serviceId, v_synchronizerId, v_updateTime);

                SET v_groupId = get_group_id(a_site_name, v_ConstSite);
         
                IF (v_groupId > -1) THEN
                    INSERT INTO service_group(service_id,groups_id)
                    VALUES(v_serviceId,v_groupId);

                    INSERT INTO vo_service_group(vo_id,service_id,groups_id)
                    VALUES(v_voId,v_serviceId,v_groupId);
                   
                END IF;

                SELECT site_id INTO v_serviceSiteId FROM service_site
                WHERE service_id=v_serviceId;
               
                SET v_groupId = get_site_group_id(v_serviceSiteId);
               
                SET v_regionId = get_site_region_group_id(v_serviceSiteId,v_groupId);
               
                IF (v_regionId > -1) THEN

                    INSERT INTO service_group(service_id,groups_id)
                    VALUES(v_serviceId,v_regionId);
		    
		    INSERT INTO vo_service_group(vo_id,service_id,groups_id)
                    VALUES(v_voId,v_serviceId,v_regionId);

                END IF;
                SET v_insert=1;
             END;

        IF ASCII(a_gocdbpk)>0 THEN

         
          SELECT id,gocdbpk INTO v_serviceId, v_gocdbpk FROM service
            WHERE  (lower(hostname)=lower(a_hostname)
            AND flavour_id=v_servFlavourId);

          IF v_gocdbpk IS NULL OR v_gocdbpk='' OR v_gocdbpk!=a_gocdbpk THEN
             UPDATE service SET gocdbpk=a_gocdbpk WHERE id=v_serviceId;
          END IF;

          SELECT ismonitored, iscore, isinproduction, serviceendpoint, ipv4,
            isdeleted, gocdbpk, hostname
            INTO v_isMonitored, v_isCore, v_isInProduction,
            v_serviceEndpoint, v_ipv4, v_isDeleted, v_gocdbpk, v_hostname
          FROM service
            WHERE gocdbpk = a_gocdbpk AND id=v_serviceId;
        ELSE
          SELECT id, ismonitored, iscore, isinproduction, serviceendpoint, ipv4,
            isdeleted, gocdbpk, hostname
            INTO v_serviceId, v_isMonitored, v_isCore, v_isInProduction,
            v_serviceEndpoint, v_ipv4, v_isDeleted, v_gocdbpk, v_hostname
          FROM service
            WHERE lower(hostname)=lower(a_hostname)
            AND flavour_id=v_servFlavourId;
        END IF;

        IF v_insert=0 THEN
            IF ((a_is_core != v_isCore) OR (a_is_monitored != v_isMonitored) OR
                (a_is_in_prod != v_isInProduction) OR (a_service_endpoint != IFNULL(v_serviceEndpoint,'')) OR
                (a_ipv4 != IFNULL(v_ipv4,''))) OR (v_isDeleted = 'Y') OR (a_gocdbpk != IFNULL(v_gocdbpk,'') OR
                (a_hostname != v_hostname)) THEN
                UPDATE service
                    SET ismonitored=IFNULL(a_is_monitored, 'Y'), iscore=IFNULL(a_is_core, 'N'),
                    isinproduction=IFNULL(a_is_in_prod, 'N'),
                    serviceendpoint=a_service_endpoint, ipv4=a_ipv4, isdeleted='N',
                    gocdbpk=a_gocdbpk, hostname=a_hostname
                WHERE id=v_serviceId;
            END IF;

            SELECT isdeleted INTO v_isDeleted
            FROM service_site
            WHERE service_id=v_serviceId;
       
            IF v_isDeleted='Y' THEN
                UPDATE service_site
                SET isdeleted='N'
                WHERE service_id=v_serviceId;
            END IF;

       
            SET v_groupId = get_group_id(a_site_name, v_ConstSite);
     
            SET v_servicegroupId = get_service_group_id(v_serviceId,v_groupId);
            IF (v_servicegroupId > -1) THEN
               UPDATE service_group
               SET isdeleted = 'N' WHERE id = v_servicegroupId;
            ELSE
                IF (v_groupId > -1) THEN
                    INSERT INTO service_group(service_id,groups_id)
                    VALUES(v_serviceId,v_groupId);
                END IF;
            END IF;
           
            SET v_voservicegroupId = get_vo_service_group_id('OPS',v_serviceId,v_groupId);
            IF (v_voservicegroupId > -1) THEN
               UPDATE vo_service_group
               SET isdeleted = 'N' WHERE id = v_voservicegroupId;
            ELSE
                IF (v_groupId > -1) THEN
                    INSERT INTO vo_service_group(vo_id,service_id,groups_id)
                    VALUES(v_voId,v_serviceId,v_groupId);
                END IF;
            END IF;
       
            SELECT site_id INTO v_serviceSiteId FROM service_site
            WHERE service_id=v_serviceId;

            SET v_sitegroupId = get_site_group_id(v_serviceSiteId);
       
            SET v_regionId = get_site_region_group_id(v_serviceSiteId,v_sitegroupId);
		-- a service should belong to a given region only. remove duplicate service-region entries
	    CALL DELETE_DUP_REGION_SERVICES(v_serviceId,v_regionId);

            SET v_servicegroupId = get_service_group_id(v_serviceId,v_regionId);
           
            IF (v_servicegroupId != -1) THEN
                UPDATE service_group
                    SET isdeleted = 'N' WHERE id = v_servicegroupId;
            ELSE
             
              IF (v_regionId > -1) THEN
                INSERT INTO service_group(service_id,groups_id)
                VALUES(v_serviceId,v_regionId);
              END IF;
            END IF;

	    SET v_voservicegroupId = get_vo_service_group_id('OPS',v_serviceId,v_regionId);
	    IF (v_voservicegroupId > -1) THEN
               UPDATE vo_service_group
               SET isdeleted = 'N' WHERE id = v_voservicegroupId;
            ELSE
                IF (v_regionId > -1) THEN
                    INSERT INTO vo_service_group(vo_id,service_id,groups_id)
                    VALUES(v_voId,v_serviceId,v_regionId);
                END IF;
            END IF;
            SET v_servicelastseenId = get_service_lastseen_id (v_serviceId,v_synchronizerId);
            IF (v_servicelastseenId  > -1) THEN
                UPDATE service_last_seen
                SET lastseen=v_updateTime
                WHERE service_id=v_serviceId
                AND synchronizer_id=v_synchronizerId;
            ELSE
         
                INSERT INTO service_last_seen(service_id, synchronizer_id, lastseen)
                VALUES (v_serviceId, v_synchronizerId, v_updateTime);
            END IF;
       
        SET sucess_flag=1;

      END IF;

    END;
  END IF;
END$$

DELIMITER ;

-- ---------------------------
-- Procedure: SITE_UPDATE
-- ----------------------------
DELIMITER $$

DROP PROCEDURE IF EXISTS `SITE_UPDATE`$$
CREATE PROCEDURE `SITE_UPDATE`(
  IN a_infrast_name VARCHAR(256),
  IN a_site_name VARCHAR(100),
  IN a_site_off_name VARCHAR(512),
  IN a_site_desc VARCHAR(512),
  IN a_synchronizer_name VARCHAR(128),
  IN a_country_name VARCHAR(50),
  IN a_certif_status VARCHAR(128),
  IN a_infrast_type VARCHAR(128),
  IN a_latitude VARCHAR(20),
  IN a_longitude VARCHAR(20),
  IN a_contact_email VARCHAR(128),
  IN a_contact_tel VARCHAR(255),
  IN a_timezone VARCHAR(128),
  IN a_giis_url VARCHAR(250),
  IN a_goc_site_id VARCHAR(50),
  IN a_roc VARCHAR(100),
  IN a_gocdbpk VARCHAR(128),
  IN a_gocdbsiteabbr VARCHAR(50),
  INOUT sucess_flag TINYINT)

BEGIN

  DECLARE v_certifStatus   VARCHAR(128);
  DECLARE v_contactEmail   VARCHAR(128);
  DECLARE v_contactTel     VARCHAR(255);
  DECLARE v_countryId      INTEGER;
  DECLARE v_countryIdParam INTEGER;
  DECLARE v_giisUrl        VARCHAR(250);
  DECLARE v_gocdbpk        VARCHAR(128);
  DECLARE v_gocdbsiteabbr  VARCHAR(50);
  DECLARE v_gocSiteId      VARCHAR(64);
  DECLARE v_groupId        INTEGER DEFAULT -1;
  DECLARE v_infrastId      INTEGER;
  DECLARE v_infrastType    VARCHAR(128);
  DECLARE v_isDeleted      VARCHAR(1);
  DECLARE v_latitude       VARCHAR(20);
  DECLARE v_longitude      VARCHAR(20);
  DECLARE v_siteDesc       VARCHAR(512);
  DECLARE v_sitegroupId    INTEGER;
  DECLARE v_sitename       VARCHAR(128);
  DECLARE v_siteId         INTEGER;
  DECLARE v_siteOffName    VARCHAR(512);
  DECLARE v_sitelastseenId INTEGER DEFAULT -1;
  DECLARE v_synchronizerId INTEGER;
  DECLARE v_timezone       VARCHAR(128);
  DECLARE v_updateTime     TIMESTAMP;
  DECLARE v_voId           INTEGER DEFAULT -1;
  DECLARE v_vogroupId      INTEGER DEFAULT -1;
  DECLARE v_ConstVO        VARCHAR(15);
  DECLARE v_ConstRegion    VARCHAR(15);
  DECLARE v_ConstSite      VARCHAR(15);
  DECLARE v_ConstOSG       VARCHAR(20); 
  DECLARE v_duplicates     INTEGER DEFAULT -1;
  DECLARE v_result         INTEGER DEFAULT -1;

  SET v_ConstRegion := 'Region';
  SET v_ConstSite := 'Site';
  SET v_ConstVO := 'ops';
  SET v_ConstOSG := 'osg';
 
  SET sucess_flag=0;

 
  SET v_synchronizerId = get_synchronizer_id(a_synchronizer_name);

 
  SET v_infrastId := get_infrastructure_id(a_infrast_name);

 
  SET v_updateTime = CURRENT_TIMESTAMP;

 
  SET v_countryIdParam = get_country_id(a_country_name);
 
  SET v_voId = get_vo_id(v_ConstVO);  

  IF ((v_synchronizerId != -1) AND (v_infrastId != -1)) THEN
    BEGIN
     
        DECLARE EXIT HANDLER FOR NOT FOUND
          proc:BEGIN
                 INSERT INTO site(infrast_id, sitename, sitedesc, siteoffname,
                   country_id, certifstatus, infrasttype, latitude, longitude,
                   contactemail, contacttel, timezone, giisurl, gocsiteid,
                   gocdbpk, gocdbsiteabbr)
                 VALUES(v_infrastId, a_site_name, a_site_desc, a_site_off_name,
                   v_countryIdParam, IFNULL(a_certif_status, 'N'),
                   IFNULL(a_infrast_type, 'Production'), a_latitude, a_longitude,
                   a_contact_email, a_contact_tel, a_timezone, a_giis_url,
                   IFNULL(a_goc_site_id,0),IFNULL(a_gocdbpk,'0'),IFNULL(a_gocdbsiteabbr,''));
                 SET v_siteId = LAST_INSERT_ID();
               
                 
                 SET v_groupId = get_group_id(a_site_name, v_ConstSite);
                 IF v_groupId=-1 THEN
                        CALL GROUPS_INSERT(v_ConstSite,a_site_name ,CONCAT('OPS site:', a_site_name));
                        SET v_groupId = get_group_id(a_site_name, v_ConstSite);
                 END IF;
                 
                 SET v_vogroupId = get_vo_group_id(v_voId, v_groupId);
                 IF (v_vogroupId>-1) THEN
                        UPDATE vo_group
                        SET isdeleted='N' WHERE groups_id=v_groupId AND vo_id=v_voId;
                 ELSE
                        IF v_voId !=-1 AND v_groupId >-1 THEN
                                INSERT INTO vo_group(vo_id,groups_id,isdeleted)
                                VALUES(v_voId,v_groupId,'N');
                        END IF;
                 END IF;

                 SET v_groupId=-1;
                 IF ASCII(a_roc) > 0 THEN
                        SET v_groupId = get_group_id(a_roc, v_ConstRegion);
                 ELSEIF a_roc='' AND lower(a_infrast_name) = v_ConstOSG THEN
			SET v_groupId = get_group_id(v_ConstOSG, v_ConstRegion);
		 END IF;

                 IF ASCII(a_roc) > 0 AND v_groupId=-1 THEN
                        call GROUPS_INSERT(v_ConstRegion, a_roc,a_roc);
                        SET v_groupId = get_group_id(a_roc, v_ConstRegion);
		 ELSEIF a_roc='' AND lower(a_infrast_name) = v_ConstOSG AND v_groupId=-1 THEN
			call GROUPS_INSERT(v_ConstRegion, v_ConstOSG,'Sites under OSG');
			SET v_groupId = get_group_id(v_ConstOSG, v_ConstRegion);
                 END IF;
               
                SET v_sitegroupId = get_site_region_group_id(v_siteId,v_groupId);

                IF (v_sitegroupId = -1) THEN
                        IF v_groupId!=-1 THEN
                               
                                INSERT INTO site_group(site_id, groups_id, isdeleted)
                                VALUES(v_siteId, v_groupId, 'N');
                               
                                -- insert or update vo-group ( virtual site)
                                SET v_vogroupId = get_vo_group_id(v_voId, v_groupId);
                                IF (v_vogroupId>-1) THEN
                                        UPDATE vo_group
                                        SET isdeleted='N' WHERE groups_id=v_groupId AND vo_id=v_voId;
                                ELSE
                                        IF v_voId !=-1 AND v_groupId !=-1 THEN
                                                INSERT INTO vo_group(vo_id,groups_id,isdeleted)
                                                VALUES(v_voId,v_groupId,'N');
                                        END IF;
                                END IF;
                        END IF;
                END IF;
               
                INSERT INTO site_last_seen(site_id, synchronizer_id, lastseen)
                VALUES (v_siteId, v_synchronizerId, v_updateTime);
               
                SET sucess_flag=1;
                LEAVE proc;
          END;

 -- update ATP DB with the latest sitename in GOCDB 
      -- check if existing sitename in ATP matches with latest GOCDB name 
      -- for the given gocdb primarykey.
      IF lower(a_infrast_name)='egi' AND a_gocdbpk !='' THEN
          -- check if there are multiple sites for given gocdbpk
SELECT a.total INTO v_duplicates FROM 
(SELECT count(id) total, gocdbpk FROM site where gocdbpk=a_gocdbpk group by gocdbpk) a;
         IF v_duplicates=1 THEN

  SELECT id,sitename INTO v_siteId,v_sitename 
  FROM site WHERE gocdbpk = a_gocdbpk;
           IF v_sitename != a_site_name THEN
UPDATE site SET sitename=a_site_name 
WHERE id=v_siteId;
  -- update groupname in groups table
  SET v_groupId = get_group_id(v_sitename, v_ConstSite);
  UPDATE groups SET groupname=a_site_name,isdeleted='N'
  WHERE id = v_groupId;
  END IF;
ELSE
SET v_result=-1;
CALL CHANGE_GOCDB_SITENAME(a_site_name,a_gocdbpk,v_result);
END IF;

      END IF;
     
      SELECT id, sitename, sitedesc, siteoffname, country_id, certifstatus,
        infrasttype, latitude, longitude, contactemail, contacttel,
        timezone, giisurl, gocsiteid, isdeleted, gocdbpk, gocdbsiteabbr
      INTO v_siteId, v_sitename, v_siteDesc, v_siteOffName, v_countryId, v_certifStatus,
        v_infrastType, v_latitude, v_longitude, v_contactEmail, v_contactTel,
        v_timezone, v_giisUrl, v_gocSiteId, v_isDeleted, v_gocdbpk, v_gocdbsiteabbr
      FROM site
      WHERE lower(sitename)=lower(a_site_name)
        AND infrast_id=v_infrastId;


      IF (a_site_desc != IFNULL(v_siteDesc,'')) OR
        (a_site_off_name != IFNULL(v_siteOffName,'')) OR
        (v_countryIdParam != v_countryId) OR
        (a_certif_status != v_certifStatus) OR
        (a_infrast_type != v_infrastType) OR
        (a_latitude != IFNULL(v_latitude,'0.0')) OR
        (a_longitude != IFNULL(v_longitude,'0.0')) OR
        (a_contact_email != IFNULL(v_contactEmail,'')) OR
        (a_contact_tel != IFNULL(v_contactTel,'')) OR
        (a_timezone != IFNULL(v_timezone,'')) OR
        (a_giis_url != IFNULL(v_giisUrl,'')) OR
        (a_goc_site_id != v_gocSiteId) OR
        (v_isDeleted = 'Y') OR
        (a_gocdbsiteabbr != IFNULL(v_gocdbsiteabbr,'')) OR
        (a_gocdbpk != IFNULL(v_gocdbpk,'0')) OR
        (a_site_name != v_sitename) THEN

        UPDATE site
        SET sitename=a_site_name, sitedesc=a_site_desc, siteoffname=a_site_off_name,
          country_id=v_countryIdParam, certifstatus=IFNULL(a_certif_status, 'N'),
          infrasttype=IFNULL(a_infrast_type, 'Production'), latitude=a_latitude,
          longitude=a_longitude, contactemail=a_contact_email,
          contacttel=a_contact_tel, timezone=a_timezone, giisurl=a_giis_url,
          gocsiteid=a_goc_site_id, isdeleted='N',gocdbsiteabbr=a_gocdbsiteabbr,
          gocdbpk=a_gocdbpk
        WHERE id=v_siteId;
      END IF;
     
      SET v_groupId = get_group_id(a_site_name, v_ConstSite);
      IF (v_groupId > -1) THEN
        UPDATE groups
        SET isdeleted='N' WHERE id = v_groupId;
      ELSE
       
        CALL GROUPS_INSERT(v_ConstSite,a_site_name ,CONCAT('OPS site:', a_site_name));
        SET v_groupId = get_group_id(a_site_name, v_ConstSite);
       
      END IF;
      -- insert or update vo-group ( virtual site)
        SET v_vogroupId = get_vo_group_id(v_voId, v_groupId);
        IF (v_vogroupId>-1) THEN
                UPDATE vo_group
                SET isdeleted='N' WHERE groups_id=v_groupId AND vo_id=v_voId;
        ELSE
                IF v_voId !=-1 AND v_groupId !=-1 THEN
                        INSERT INTO vo_group(vo_id,groups_id,isdeleted)
                        VALUES(v_voId,v_groupId,'N');
                END IF;
        END IF;

      SET v_groupId=-1;

      IF ASCII(a_roc) > 0 THEN
        SET v_groupId = get_group_id(a_roc, v_ConstRegion);
      ELSEIF a_roc='' AND lower(a_infrast_name) = v_ConstOSG THEN
	SET v_groupId = get_group_id(v_ConstOSG, v_ConstRegion);	
      END IF;

      IF ASCII(a_roc) > 0 AND v_groupId=-1 THEN
     
        call GROUPS_INSERT(v_ConstRegion, a_roc,a_roc);
        SET v_groupId = get_group_id(a_roc, v_ConstRegion);
      ELSEIF a_roc='' AND lower(a_infrast_name) = v_ConstOSG AND v_groupId=-1 THEN
	call GROUPS_INSERT(v_ConstRegion, v_ConstOSG,'Sites under OSG');
	SET v_groupId = get_group_id(v_ConstOSG, v_ConstRegion);
 
      END IF;
      IF (v_groupId > -1) THEN
	        UPDATE groups
       	        SET isdeleted='N' WHERE id = v_groupId;
      END IF;
      SET v_sitegroupId = get_site_region_group_id(v_siteId,v_groupId);
      IF ASCII(a_roc) > 0 AND v_groupId!=-1 THEN
        IF (v_sitegroupId > -1) THEN
          IF (v_sitegroupId != v_groupId) THEN
            -- region is changed for the site
            UPDATE site_group
            SET isdeleted='N', groups_id=v_groupId
            WHERE site_id=v_siteId AND groups_id=v_sitegroupId;
	  ELSE
            
            UPDATE site_group
            SET isdeleted='N'
            WHERE site_id=v_siteId AND groups_id=v_sitegroupId;

          END IF;
        ELSE
          INSERT INTO site_group(site_id, groups_id, isdeleted)
          VALUES(v_siteId, v_groupId, 'N');
        END IF;
      ELSEIF a_roc='' AND v_groupId!=-1 AND lower(a_infrast_name) = v_ConstOSG THEN 
	IF (v_sitegroupId > -1) THEN
            UPDATE site_group
            SET isdeleted='N', groups_id=v_groupId
            WHERE site_id=v_siteId AND groups_id=v_sitegroupId;
	ELSE
		INSERT INTO site_group(site_id, groups_id, isdeleted)
        	VALUES(v_siteId, v_groupId, 'N');
	END IF;
      END IF;
        -- insert or update vo-group ( region)
        SET v_vogroupId = get_vo_group_id(v_voId, v_groupId);
        IF (v_vogroupId>-1) THEN
                UPDATE vo_group
                SET isdeleted='N' WHERE groups_id=v_groupId AND vo_id=v_voId;
        ELSE
                IF v_voId !=-1 AND v_groupId !=-1 THEN
                        INSERT INTO vo_group(vo_id,groups_id,isdeleted)
                        VALUES(v_voId,v_groupId,'N');
                END IF;
        END IF;
        
   
    SET v_sitelastseenId = get_site_lastseen_id (v_siteId,v_synchronizerId);

     IF (v_sitelastseenId  > -1) THEN
      UPDATE site_last_seen
      SET lastseen=v_updateTime
      WHERE site_id=v_siteId
        AND synchronizer_id=v_synchronizerId;
    ELSE
     
      INSERT INTO site_last_seen(site_id, synchronizer_id, lastseen)
      VALUES (v_siteId, v_synchronizerId, v_updateTime);
    END IF;

      SET sucess_flag=1;
    END;
  END IF;
END$$

DELIMITER ;
-- ---------------------------
-- Procedure:DOWNTIME_UPDATE
-- ---------------------------

DELIMITER $$

DROP PROCEDURE IF EXISTS `DOWNTIME_UPDATE`$$
CREATE PROCEDURE `DOWNTIME_UPDATE`(IN a_start_time TIMESTAMP,
  IN a_end_time TIMESTAMP, IN a_classification VARCHAR(128), 
  IN a_goc_downtimeid INTEGER, IN a_osg_downtimeid INTEGER,
  IN a_severity VARCHAR(128), IN a_description VARCHAR(1000), 
  IN a_infrast_name VARCHAR(256), IN a_hostname VARCHAR(512), 
  IN a_site_name VARCHAR(100), IN a_gocdbpk VARCHAR(128), IN a_servicetype VARCHAR(128), INOUT sucess_flag INTEGER)
BEGIN

  DECLARE  exit_proc         INTEGER DEFAULT 0;
  DECLARE  v_classif         VARCHAR(128);
  DECLARE  v_description     VARCHAR(1000);
  DECLARE  v_downtimeId      INTEGER DEFAULT -1;
  DECLARE  v_downtimeId2     INTEGER;
  DECLARE  v_endTime         TIMESTAMP;
  DECLARE  v_infrastId       INTEGER;
  DECLARE  v_inserted        INTEGER DEFAULT 0;
  DECLARE  v_serviceId       INTEGER;
  DECLARE  v_serviceId2      INTEGER;
  DECLARE  v_severity        VARCHAR(128);
  DECLARE  v_siteId          INTEGER;
  DECLARE  v_siteId2         INTEGER;
  DECLARE  v_startTime       TIMESTAMP;
  DECLARE  v_updateTime      TIMESTAMP;
  DECLARE  v_gocdowntimeId   INTEGER;
  DECLARE v_gocdbpk          VARCHAR(128);

  SET sucess_flag=0;

  IF ASCII(TRIM(a_gocdbpk) > 0) OR (a_osg_downtimeid > 0) THEN
     
     
    SET v_updateTime = CURRENT_TIMESTAMP;

    IF ASCII(TRIM(a_gocdbpk) > 0) THEN

	SET v_downtimeId = get_gocdb_downtime_id(a_gocdbpk);
        IF v_downtimeId = -1 THEN
            
            INSERT INTO downtime (starttimestamp, endtimestamp,
              inserttimestamp, classification, gocdowntimeid, severity,
              description,gocdbpk)
            VALUES (a_start_time, a_end_time, v_updateTime,
              a_classification, a_goc_downtimeid, a_severity,
              a_description,TRIM(a_gocdbpk));
            COMMIT;
            SELECT LAST_INSERT_ID() INTO v_downtimeId;
 	    
            SET v_inserted = 1;

	ELSE
		SELECT starttimestamp, endtimestamp, classification, severity,
          	description, gocdowntimeid
        	INTO v_startTime, v_endTime,v_classif,v_severity,
        	v_description, v_gocdowntimeid
        	FROM downtime
        	WHERE id=v_downtimeId;
	
	END IF;

    END IF;
    

    IF (a_osg_downtimeid > 0) THEN
      
      BEGIN
        DECLARE EXIT HANDLER FOR NOT FOUND
          BEGIN
            
            INSERT INTO downtime (starttimestamp, endtimestamp, 
              inserttimestamp, classification, osgdowntimeid, severity, 
              description)
            VALUES (a_start_time, a_end_time, v_updateTime,
              a_classification, a_osg_downtimeid, a_severity, 
              a_description);
            COMMIT;
            SELECT LAST_INSERT_ID() INTO v_downtimeId;
            SET v_inserted = 1;
          END;

        SELECT id, starttimestamp, endtimestamp, classification, severity,
          description INTO v_downtimeId, v_startTime, v_endTime, v_classif,
          v_severity, v_description
        FROM downtime
        WHERE osgdowntimeid=a_osg_downtimeid;
	
      END;
    END IF;

    IF (v_inserted = 0) THEN
       IF ((v_startTime != a_start_time) OR (v_endTime != a_end_time) OR
        (v_classif <> a_classification) OR (v_severity <> a_severity) OR
        (v_description <> a_description)OR (v_gocdowntimeId != a_goc_downtimeid)) THEN
        UPDATE downtime
        SET starttimestamp=a_start_time, endtimestamp=a_end_time,
          inserttimestamp=v_updateTime, classification= a_classification,
          severity=a_severity, description=a_description, gocdowntimeid=a_goc_downtimeid
        WHERE id=v_downtimeId;
      
      END IF;
      
    END IF;
  END IF;

  SET exit_proc=0;
  
  IF  ASCII(TRIM(a_site_name))>0 THEN
    
    BEGIN
      DECLARE EXIT HANDLER FOR NOT FOUND
        BEGIN
          SET exit_proc=1;
        END;

      SELECT a.id, b.id INTO v_infrastId, v_siteId
      FROM infrastructure a, site b
      WHERE lower(a.infrastname)=lower(a_infrast_name)
        AND b.infrast_id=a.id
        AND lower(b.sitename)=lower(a_site_name);
    END;

    IF exit_proc=0 THEN
      
      BEGIN
        DECLARE EXIT HANDLER FOR NOT FOUND
          BEGIN
            
            INSERT INTO site_downtime(site_id, downtime_id)
            VALUES (v_siteId, v_downtimeId);
          END;
        SELECT site_id, downtime_id INTO v_siteId2, v_downtimeId2
        FROM site_downtime
        WHERE site_id=v_siteId
          AND downtime_id=v_downtimeId;
      END;
    END IF;
  END IF;
  
  
  IF ASCII(TRIM(a_hostname))>0 THEN
    BEGIN
      DECLARE no_more_rows BOOLEAN DEFAULT FALSE;
        
      DECLARE service_cur CURSOR FOR
        SELECT a.id
        FROM service a, site b, infrastructure c, service_site d, service_type_flavour e
        WHERE lower(c.infrastname)=lower(a_infrast_name)
          AND b.infrast_id=c.id
          AND lower(a.hostname)=lower(a_hostname)
          AND a.id=d.service_id
          AND b.id=d.site_id
          AND a.flavour_id = e.id
          AND lower(e.flavourname)=lower(a_servicetype);

      DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows = TRUE;

      
      OPEN service_cur;

      service_loop:LOOP
        
        FETCH service_cur INTO v_serviceId2;

        IF no_more_rows THEN
          CLOSE service_cur;
          LEAVE service_loop;
        END IF;
       
        SELECT service_id, downtime_id INTO v_serviceId, v_downtimeId2
        FROM service_downtime
        WHERE service_id=v_serviceId2
          AND downtime_id=v_downtimeId;

        IF no_more_rows THEN
          
          INSERT INTO service_downtime(service_id, downtime_id)
          VALUES (v_serviceId2, v_downtimeId);

	END IF;
        
        SET no_more_rows = FALSE;
      END LOOP service_loop;
      SET sucess_flag=1;
    END;
  END IF;

END$$

DELIMITER ;

-- -------------------------------
-- Procedure: SITE_CAPACITY_UPDATE
-- -------------------------------

DELIMITER $$

DROP PROCEDURE IF EXISTS `SITE_CAPACITY_UPDATE`$$
CREATE PROCEDURE `SITE_CAPACITY_UPDATE`(IN a_site_name VARCHAR(100),
  IN a_log_cpu_count INTEGER, IN a_phy_cpu_count INTEGER, IN a_ksi2k INTEGER,
  IN a_hep_spec_06 INTEGER, INOUT sucess_flag TINYINT)
BEGIN

  DECLARE v_infrastId   INTEGER;
  DECLARE v_ksi2k       INTEGER;
  DECLARE v_logCpuCount INTEGER;
  DECLARE v_phyCpuCount INTEGER;
  DECLARE v_siteId      INTEGER;
  DECLARE v_hspec06     INTEGER;
  DECLARE v_siteentry   INTEGER;

  DECLARE no_more_rows BOOLEAN DEFAULT FALSE;
  DECLARE sitecur CURSOR FOR SELECT id FROM site WHERE lower(sitename)=lower(a_site_name);
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows = TRUE;

  SET sucess_flag=0;
  OPEN sitecur;

  sites_loop: LOOP
    FETCH sitecur INTO v_siteentry;

    IF no_more_rows THEN
      CLOSE sitecur;
      LEAVE sites_loop;
    END IF;

    -- insert/update SITE_STORE_CAP table
    SELECT phycpucount, logcpucount, ksi2k, hspec06
    INTO v_phyCpuCount, v_logCpuCount, v_ksi2k, v_hspec06
    FROM site_store_cap
    WHERE site_id=v_siteentry;

    IF no_more_rows THEN
      -- We must insert a new entry
      INSERT INTO site_store_cap(site_id, phycpucount, logcpucount, ksi2k, hspec06)
      VALUES(v_siteentry, a_phy_cpu_count, a_log_cpu_count, a_ksi2k, a_hep_spec_06);
    ELSE
      -- Update table if there is mismatch
      IF (a_phy_cpu_count != v_phyCpuCount) OR 
         (a_log_cpu_count != v_logCpuCount) OR (a_hep_spec_06 != v_hspec06) OR 
         (a_ksi2k != v_ksi2k) THEN
        UPDATE site_store_cap
        SET phycpucount=a_phy_cpu_count, logcpucount=a_log_cpu_count, 
            ksi2k=a_ksi2k, hspec06=a_hep_spec_06
        WHERE site_id=v_siteentry;
      END IF;
    END IF;

    -- We reset the no_more_rows variable to now exit sites_loop prematurely.
    SET no_more_rows = FALSE;
    SET sucess_flag=1;
  END LOOP sites_loop;

END$$

DELIMITER ;


-- ------------------------------
-- Procedure:TIER_FEDERATION_INSERT
-- -----------------------------
DELIMITER $$

DROP PROCEDURE IF EXISTS `TIER_FEDERATION_INSERT`$$
CREATE PROCEDURE `TIER_FEDERATION_INSERT`(IN a_tier VARCHAR(20), IN a_federation VARCHAR(100),
 IN a_federation_account_name VARCHAR(100), IN a_site_name VARCHAR(100), IN a_infrast_name VARCHAR(256),a_country_name VARCHAR(256),
  INOUT sucess_flag TINYINT)
BEGIN

  DECLARE v_groupId          INTEGER;
  DECLARE v_infrastId        INTEGER;
  DECLARE v_isDeleted        VARCHAR(1);
  DECLARE v_siteId           INTEGER;
  DECLARE v_voId             INTEGER;
  DECLARE v_serviceentry     INTEGER DEFAULT -1;
  DECLARE v_voservicegroupId INTEGER DEFAULT -1;
  DECLARE v_vogroupId        INTEGER DEFAULT -1;
  DECLARE v_sitegroupId        INTEGER DEFAULT -1;
  DECLARE v_tiergroupId      INTEGER DEFAULT -1;
  DECLARE v_fedgroupId       INTEGER DEFAULT -1;
  DECLARE v_countryId        INTEGER DEFAULT -1;
   
  DECLARE v_flag             BOOLEAN DEFAULT FALSE;
  DECLARE no_more_rows       BOOLEAN DEFAULT FALSE;

  DECLARE v_voops            VARCHAR(15);
  DECLARE v_tier_grouptype   VARCHAR(15);
  DECLARE v_fed_grouptype    VARCHAR(15);
 
  DECLARE site_cur CURSOR FOR SELECT id FROM site  WHERE sitename=a_site_name;  
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows = TRUE;
 
  SET v_voops := 'ops';
  SET v_tier_grouptype := 'Tier';
  SET v_fed_grouptype := 'Federation';
 
  SET sucess_flag=0;
 
  SET v_voId = get_vo_id(v_voops);

  SET v_countryId = get_country_id(a_country_name);

  -- tier info
  SET v_groupId = get_group_id(a_tier, v_tier_grouptype);
  IF v_groupId = -1 THEN
   -- insert Tier
        CALL GROUPS_INSERT(v_tier_grouptype, a_tier ,CONCAT("Tier:",a_tier));
        SET v_groupId = get_group_id(a_tier, v_tier_grouptype);
  END IF;
  SET v_tiergroupId = v_groupId;

  -- federation info
  SET v_groupId = get_group_id(a_federation, v_fed_grouptype);
  IF v_groupId = -1 THEN
   -- insert Federation
        CALL GROUPS_INSERT(v_fed_grouptype, a_federation ,CONCAT("Federation accounting name:",a_federation_account_name));
        SET v_groupId = get_group_id(a_federation, v_fed_grouptype);
  ELSE
        UPDATE groups SET description=CONCAT("Federation accounting name:",a_federation_account_name), isdeleted='N'
        WHERE id = v_groupId;
  END IF;
  SET v_fedgroupId = v_groupId;
 
  SET v_infrastId = get_infrastructure_id(a_infrast_name);
 
  -- SET v_siteId = get_site_id(a_site_name, v_infrastId);
  open site_cur;
  site_loop: LOOP
        FETCH site_cur INTO v_siteId;
        IF no_more_rows THEN
                CLOSE site_cur;
                LEAVE site_loop;
        END IF;
        IF ((v_voId != -1) AND (v_siteId != -1) AND (v_groupId != -1)) THEN

		-- update site table with country name
		UPDATE site SET country_id=v_countryId WHERE id=v_siteId;

                INNER_BLOCK: BEGIN
                
                        -- insert or update vo_service_group
                        DECLARE no_more_rows_inner BOOLEAN DEFAULT FALSE;
                        DECLARE service_cur CURSOR FOR SELECT service_id FROM service_site  WHERE site_id=v_siteId AND isdeleted = 'N';
                        DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows_inner = TRUE;
                        OPEN service_cur;
 
                        services_loop: LOOP
                                FETCH service_cur INTO v_serviceentry;
                                IF no_more_rows_inner THEN
                                        CLOSE service_cur;
                                        LEAVE services_loop;
                                END IF;
                                -- tier info
                                SET v_voservicegroupId = get_vo_service_group_id(v_voops,v_serviceentry,v_tiergroupId);
                                IF v_voservicegroupId = -1 THEN
                                        INSERT INTO vo_service_group(vo_id, service_id, groups_id)
                                        VALUES (v_voId, v_serviceentry, v_tiergroupId);
                                ELSE
                                        UPDATE vo_service_group SET isdeleted ='N'
                                        WHERE vo_id = v_voId AND service_id = v_serviceentry
                                        AND groups_id = v_tiergroupId;
                                END IF;
                                -- federation info
                                SET v_voservicegroupId = get_vo_service_group_id(v_voops,v_serviceentry,v_fedgroupId);
                                IF v_voservicegroupId = -1 THEN
                                        INSERT INTO vo_service_group(vo_id, service_id, groups_id)
                                        VALUES (v_voId, v_serviceentry, v_fedgroupId);
                                ELSE
                                        UPDATE vo_service_group SET isdeleted ='N'
                                        WHERE vo_id = v_voId AND service_id = v_serviceentry
                                        AND groups_id = v_fedgroupId;
                                END IF;
                                SET no_more_rows_inner = FALSE;
                        END LOOP services_loop;

                        -- insert or update vo_group
                        -- tier info
                        SET v_vogroupId = get_vo_group_id(v_voId,v_tiergroupId);
                        IF v_vogroupId =-1 THEN
                                INSERT INTO vo_group(vo_id,groups_id,isdeleted)
                                VALUES(v_voId,v_tiergroupId,'N');
                        ELSE
                                UPDATE vo_group
                                SET isdeleted='N' WHERE groups_id=v_tiergroupId AND vo_id=v_voId;
                        END IF;
                        -- federation info
                        SET v_vogroupId = get_vo_group_id(v_voId,v_fedgroupId);
                        IF v_vogroupId =-1 THEN
                                INSERT INTO vo_group(vo_id,groups_id,isdeleted)
                                VALUES(v_voId,v_fedgroupId,'N');
                        ELSE
                                UPDATE vo_group
                                SET isdeleted='N' WHERE groups_id=v_fedgroupId AND vo_id=v_voId;
                        END IF;

                        -- insert or update site_group
                        -- tier info
                        SET v_sitegroupId = get_site_group_id2(v_siteId,v_tiergroupId);
                        IF v_sitegroupId =-1 THEN
                                INSERT INTO site_group(site_id,groups_id,isdeleted)
                                VALUES(v_siteId,v_tiergroupId,'N');
                        ELSE
                                UPDATE site_group
                                SET isdeleted='N' WHERE groups_id=v_tiergroupId AND site_id=v_siteId;
                        END IF;
                        -- federation info
                        SET v_sitegroupId = get_site_group_id2(v_siteId,v_fedgroupId);
                        IF v_sitegroupId =-1 THEN
                                INSERT INTO site_group(site_id,groups_id,isdeleted)
                                VALUES(v_siteId,v_fedgroupId,'N');
                        ELSE
                                UPDATE site_group
                                SET isdeleted='N' WHERE groups_id=v_fedgroupId AND site_id=v_siteId;
                        END IF;

                        SET sucess_flag=1;

                END INNER_BLOCK;

        END IF;
        SET no_more_rows = FALSE;
  END LOOP site_loop;
END$$

DELIMITER ;
-- ------------------------------
-- Procedure: SERVICE_VO_INSERT
-- --------------------------------

DELIMITER $$

DROP PROCEDURE IF EXISTS `SERVICE_VO_INSERT` $$
CREATE PROCEDURE `SERVICE_VO_INSERT`(IN a_hostname VARCHAR(512),
  IN a_service_flavour VARCHAR(128), IN a_vo_name VARCHAR(100),
  INOUT sucess_flag TINYINT)
BEGIN

  DECLARE v_isDeleted      VARCHAR(1);
  DECLARE v_servFlavourId  INTEGER;
  DECLARE v_serviceId      INTEGER;
  DECLARE v_voId           INTEGER;

  SET sucess_flag=0;
  -- Check if the VO is defined in the DB
  SET v_voId = get_vo_id(a_vo_name);

  -- Check if the service flavour is defined in the DB
  SET v_servFlavourId = get_service_flavour_id(a_service_flavour);

  -- Check if the service is already defined in the DB
  SET v_serviceId = get_service_id(a_hostname, v_servFlavourId);

  IF ((v_voId != -1) AND (v_serviceId != -1)) THEN
    BEGIN
      DECLARE EXIT HANDLER FOR NOT FOUND
        BEGIN
           -- Insert service endpoint-vo entry
           INSERT INTO service_vo(service_id, vo_id)
           VALUES(v_serviceId, v_voId);
        END;

      SELECT vo_id, isdeleted INTO v_voId, v_isDeleted
      FROM service_vo
      WHERE service_id=v_serviceId
        AND vo_id=v_voId;

      IF (v_isDeleted = 'Y') THEN
        UPDATE service_vo
        SET isdeleted='N'
        WHERE service_id=v_serviceId
          AND vo_id=v_voId;
      END IF;
      SET sucess_flag=1;
    END;
  END IF;
END $$

DELIMITER ;

-- -------------------------------------
-- Procedure:SERVICE_TYPE_FLAVOUR_INSERT
-- ---------------------------------------

DELIMITER $$

DROP PROCEDURE IF EXISTS `SERVICE_TYPE_FLAVOUR_INSERT` $$
CREATE PROCEDURE `SERVICE_TYPE_FLAVOUR_INSERT`(IN a_service_flavour_name VARCHAR(128))
BEGIN

  DECLARE v_servTypeFlavourId INTEGER;

  -- Check if the service_type exists
  SET v_servTypeFlavourId = get_service_flavour_id(a_service_flavour_name);

  IF (v_servTypeFlavourId = -1) THEN
    BEGIN
      INSERT INTO service_type_flavour(flavourname)
      VALUES (a_service_flavour_name);
    END;
  END IF;
END $$

DELIMITER ;

-- ----------------------------
-- Procedure: GROUPS_INSERT
-- ------------------------------

DELIMITER $$

DROP PROCEDURE IF EXISTS `GROUPS_INSERT`$$
CREATE PROCEDURE `GROUPS_INSERT`(IN a_group_type_name VARCHAR(100), 
  IN a_group_groupname VARCHAR(100), IN a_group_description VARCHAR(255))
BEGIN

  DECLARE v_groupId  INTEGER;
  DECLARE v_groupTypeId INTEGER;

  
  BEGIN
    DECLARE EXIT HANDLER FOR NOT FOUND
      BEGIN
        
        SET v_groupTypeId = get_group_type_id(a_group_type_name);

        IF v_groupTypeId > 0 THEN
          
          INSERT INTO groups(group_type_id, groupname, description)
          VALUES (v_groupTypeId, a_group_groupname, a_group_description);
        END IF;
      END;

    SELECT a.id INTO v_groupId
    FROM groups a, group_type b
    WHERE lower(a.groupname)= lower(a_group_groupname)
      AND lower(b.typename)= lower(a_group_type_name)
      AND a.group_type_id=b.id;
  END;

END$$

DELIMITER ;

-- ----------------------------
-- Procedure: TIER_INSERT
-- -----------------------------
DELIMITER $$

DROP PROCEDURE IF EXISTS `TIER_INSERT`$$
CREATE PROCEDURE `TIER_INSERT`(IN a_site_name VARCHAR(100),
  IN a_tier INTEGER, IN a_infrast_name VARCHAR(256), IN a_vo_name VARCHAR(100),
  INOUT sucess_flag TINYINT)
BEGIN

  DECLARE v_groupId          INTEGER;
  DECLARE v_infrastId        INTEGER;
  DECLARE v_isDeleted        VARCHAR(1);
  DECLARE v_siteId           INTEGER;
  DECLARE v_voId             INTEGER;
  DECLARE v_ServiceEntry     INTEGER DEFAULT -1;
  DECLARE v_VoServiceGroupId INTEGER DEFAULT -1;
  DECLARE v_vogroupId        INTEGER DEFAULT -1;
  DECLARE v_flag             BOOLEAN DEFAULT FALSE;
  DECLARE no_more_rows       BOOLEAN DEFAULT FALSE;
  
  DECLARE service_cur CURSOR FOR SELECT service_id from service_site  where site_id=v_siteId; 
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows = TRUE;
  
  SET sucess_flag=0;
  

  SET v_voId = get_vo_id(a_vo_name);

  
  SET v_groupId = get_group_id(concat('Tier-', a_tier), 'Tier');

  
  SET v_infrastId = get_infrastructure_id(a_infrast_name);

  
  SET v_siteId = get_site_id(a_site_name, v_infrastId);

  IF ((v_voId != -1) AND (v_siteId != -1) AND (v_groupId != -1)) THEN
    
      OPEN service_cur;
 
  	services_loop: LOOP
    		FETCH service_cur INTO v_ServiceEntry;
 
    		IF no_more_rows THEN
     			 CLOSE service_cur;
      			LEAVE services_loop;
    		END IF;
   		 
      		SET v_VoServiceGroupId = get_vo_service_group_id(a_vo_name,v_ServiceEntry,v_groupId);
      		IF v_voServiceGroupId != -1 THEN
      			UPDATE vo_service_group SET isdeleted ='N'
       			WHERE vo_id = v_voId AND service_id = v_ServiceEntry
        		AND groups_id = v_groupId;
      		ELSE
        		INSERT INTO vo_service_group(vo_id, service_id, groups_id)
        		VALUES (v_voId, v_ServiceEntry, v_groupId);
			
      		END IF;
    	
    		SET no_more_rows = FALSE;
  	END LOOP services_loop;
	-- insert or update vo-group
	SET v_vogroupId = get_vo_group_id(v_voId,v_groupId);

	IF v_vogroupId !=-1 THEN

		UPDATE vo_group
		SET isdeleted='N' WHERE groups_id=v_groupId and vo_id=v_voId;
	ELSE
		INSERT INTO vo_group(vo_id,groups_id,isdeleted)
		VALUES(v_voId,v_groupId,'N');
	END IF;
  	SET sucess_flag=1;
  END IF;
END$$

DELIMITER ;

-- ------------------------------
-- Procedure:SYNCHRONIZER_LASTRUN_UPDATE
-- ------------------------------

DELIMITER $$

DROP PROCEDURE IF EXISTS `SYNCHRONIZER_LASTRUN_UPDATE`$$
CREATE PROCEDURE `SYNCHRONIZER_LASTRUN_UPDATE`( IN a_sync_name VARCHAR(128), IN a_sync_status VARCHAR(1),
IN a_sync_updatetime TIMESTAMP)
BEGIN

-- DECLARE v_updateTime TIMESTAMP;
DECLARE v_syncId INTEGER;
DECLARE v_synclastrunId INTEGER;
DECLARE v_synclastupdate_status INTEGER;
  -- Compute the update time
  -- SET v_updateTime = CURRENT_TIMESTAMP;
  -- get synchronizer Id
  SET v_syncId = get_synchronizer_id(a_sync_name);
 -- get synchronizer last update status
  SET v_synclastupdate_status = get_synchronizer_lastupdate_status(a_sync_name);
  IF v_synclastupdate_status = -1 THEN
  	-- Insert row in SYNCHRONIZER_LASTRUN table
	INSERT INTO synchronizer_lastrun (synchronizer_id,succeed,lastexecution)
        VALUES (v_syncId,a_sync_status,a_sync_updatetime);   
  ELSE
  	-- UPDATE synchronizer_lastrun SET succeed=a_sync_status, lastexecution=v_updatetime WHERE synchronizer_id=v_syncid;
  	UPDATE synchronizer_lastrun SET succeed=a_sync_status, lastexecution=a_sync_updatetime WHERE synchronizer_id=v_syncid;
 END IF;
END$$

DELIMITER ;

-- -----------------------------------
-- Procedure: REMOVE_SERVICES_AND_SITES
-- -------------------------------------
DELIMITER $$

DROP PROCEDURE IF EXISTS `REMOVE_SERVICES_AND_SITES`$$
CREATE PROCEDURE `REMOVE_SERVICES_AND_SITES`()
BEGIN

  DECLARE v_synchronizerId   INTEGER;
  DECLARE v_synchronizerLSId INTEGER;
  DECLARE v_lastExecution    TIMESTAMP;
  DECLARE v_lastSeen         TIMESTAMP;
  DECLARE v_removeService    BOOLEAN DEFAULT TRUE;
  DECLARE v_serviceId        INTEGER;
  DECLARE v_serviceLSId      INTEGER;
  DECLARE v_siteId           INTEGER;

  DECLARE no_more_rows BOOLEAN DEFAULT FALSE;

  -- Cursor to extract all services not found by the last 
  -- synchronizer execution
  DECLARE serviceCur CURSOR FOR 
    SELECT c.id, a.synchronizer_id
    FROM service_last_seen a, synchronizer_lastrun b, service c
    WHERE a.synchronizer_id=b.synchronizer_id
      AND a.lastseen<b.lastexecution
      AND a.service_id= c.id
      AND c.isdeleted='N';

  -- Cursor to extract sites with no services associated.
  DECLARE emptySitesCur CURSOR FOR 
    SELECT a.site_id
    FROM (SELECT site_id, COUNT(id) total
          FROM service_site
          WHERE isdeleted='N'
          GROUP BY site_id
        ) a
    WHERE a.total=0;

  -- Cursor to extract the same service but detected by another synchronizer
  DECLARE serviceLastSeenCur CURSOR FOR 
    SELECT service_id, synchronizer_id, lastseen
    FROM service_last_seen
    WHERE service_id=v_serviceId
      AND synchronizer_id != v_synchronizerId;

  DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows=TRUE;

  OPEN serviceCur;

  services_loop: LOOP
    -- For all active services not found during the last synchronizer run
    FETCH serviceCur INTO v_serviceId, v_synchronizerId;

    IF no_more_rows THEN
      CLOSE serviceCur;
      LEAVE services_loop;
    END IF;

    SET v_removeService = TRUE;

    -- If the service has not been detected by any other synchronizer,
    -- we remove it marking it as deleted.
    OPEN serviceLastSeenCur;

    serviceLastSeen_loop: LOOP
      FETCH serviceLastSeenCur INTO v_serviceLSId, v_synchronizerLSId, v_lastSeen;

      IF no_more_rows THEN
        SET no_more_rows = FALSE;
        CLOSE serviceLastSeenCur;
        LEAVE serviceLastSeen_loop;
      END IF;

      BEGIN
        SELECT lastexecution INTO v_lastExecution
        FROM synchronizer_lastrun
        WHERE id=v_synchronizerLSId;
          
        -- Check if by this other synchronizer the service has been 
        -- updated recently, so we don't remove it
        IF (v_lastExecution < v_lastSeen) THEN
          SET v_removeService = FALSE;
        END IF;
      END;
    END LOOP serviceLastSeen_loop;

    IF v_removeService THEN
      UPDATE service
      SET isdeleted='Y'
      WHERE id=v_serviceId;
        
      UPDATE service_site
      SET isdeleted='Y'
      WHERE service_id=v_serviceId;

	BLOCK1: begin
		DECLARE v_servicevoId INTEGER;
		DECLARE no_more_rows1 BOOLEAN DEFAULT FALSE;
		DECLARE servicevoCur CURSOR FOR
			SELECT id
			FROM service_vo
			WHERE service_id=v_serviceId;
		DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows1=TRUE;
		-- service-vo table
		OPEN servicevoCur;
	
		servicevo_loop: LOOP
		        FETCH servicevoCur INTO v_servicevoId;
		        IF no_more_rows1 THEN
		              CLOSE servicevoCur;
		              LEAVE servicevo_loop;
		        END IF;

			UPDATE service_vo SET isdeleted='Y' WHERE id=v_servicevoId;	
			SET no_more_rows1=False;

		END LOOP servicevo_loop;
        end BLOCK1;	

	BLOCK2: begin
		DECLARE v_servicegroupId INTEGER;
		DECLARE no_more_rows1 BOOLEAN DEFAULT FALSE;
		DECLARE servicegroupCur CURSOR FOR
			SELECT id
			FROM service_group
			WHERE service_id=v_serviceId;
		DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows1=TRUE;
		-- service-group table
		OPEN servicegroupCur;
	
		servicegroup_loop: LOOP
		        FETCH servicegroupCur INTO v_servicegroupId;
		        IF no_more_rows1 THEN
		              CLOSE servicegroupCur;
		              LEAVE servicegroup_loop;
		        END IF;

			UPDATE service_group SET isdeleted='Y' WHERE id=v_servicegroupId;	
			SET no_more_rows1=False;

		END LOOP servicegroup_loop;
        end BLOCK2;	


	BLOCK3: begin
		DECLARE v_voservicegroupId INTEGER;
		DECLARE no_more_rows1 BOOLEAN DEFAULT FALSE;
		DECLARE voservicegroupCur CURSOR FOR
			SELECT id
			FROM vo_service_group
			WHERE service_id=v_serviceId;
		DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows1=TRUE;
		-- vo-service-group table
		OPEN voservicegroupCur;
	
		voservicegroup_loop: LOOP
		        FETCH voservicegroupCur INTO v_voservicegroupId;
		        IF no_more_rows1 THEN
		              CLOSE voservicegroupCur;
		              LEAVE voservicegroup_loop;
		        END IF;

			UPDATE vo_service_group SET isdeleted='Y' WHERE id=v_voservicegroupId;	
			SET no_more_rows1=False;

		END LOOP voservicegroup_loop;
        end BLOCK3;	


    END IF;
  END LOOP services_loop;

  -- Reset no_more_rows variable
  SET no_more_rows = FALSE;

  -- If there are sites without any service mapped to them, mark them as deleted
  OPEN emptySitesCur;

  emptySites_loop: LOOP
    FETCH emptySitesCur INTO v_siteId;

    IF no_more_rows THEN
      CLOSE emptySitesCur;
      LEAVE emptySites_loop;
    END IF;

    UPDATE site
    SET isdeleted='Y'
    WHERE id=v_siteId;
  
    UPDATE vo_sitename
    SET isdeleted='Y'
    WHERE site_id=v_siteId;

    UPDATE site_group
    SET isdeleted='Y'
    WHERE site_id=v_siteId;

  END LOOP emptySites_loop;

 -- If the service is deleted, it's entry from other tables like service_vo,vo_service_group should be marked as deleted.
	BLOCK4: begin
		DECLARE v_voservicegroupId INTEGER;
		DECLARE no_more_rows1 BOOLEAN DEFAULT FALSE;
		DECLARE voservicegroupCur CURSOR FOR
			SELECT id
			FROM vo_service_group
			WHERE service_id IN (SELECT id FROM service WHERE isdeleted='Y')
			AND isdeleted = 'N';
		DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows1=TRUE;
		-- vo-service-group table
		OPEN voservicegroupCur;
	
		voservicegroup_loop: LOOP
		        FETCH voservicegroupCur INTO v_voservicegroupId;
		        IF no_more_rows1 THEN
		              CLOSE voservicegroupCur;
		              LEAVE voservicegroup_loop;
		        END IF;

			UPDATE vo_service_group SET isdeleted='Y' WHERE id=v_voservicegroupId;	
			SET no_more_rows1=False;

		END LOOP voservicegroup_loop;
        end BLOCK4;	

	BLOCK5: begin
		DECLARE v_servicevoId INTEGER;
		DECLARE no_more_rows1 BOOLEAN DEFAULT FALSE;
		DECLARE servicevoCur CURSOR FOR
			SELECT id
			FROM service_vo
			WHERE service_id IN (SELECT id FROM service WHERE isdeleted='Y')
			AND isdeleted = 'N';
		DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows1=TRUE;
		-- service-vo table
		OPEN servicevoCur;
	
		servicevo_loop: LOOP
		        FETCH servicevoCur INTO v_servicevoId;
		        IF no_more_rows1 THEN
		              CLOSE servicevoCur;
		              LEAVE servicevo_loop;
		        END IF;

			UPDATE vo_service_group SET isdeleted='Y' WHERE id=v_servicevoId;	
			SET no_more_rows1=False;

		END LOOP servicevo_loop;
        end BLOCK5;	

  COMMIT;
END$$

DELIMITER ;

-- -----------------------------
-- Procedure: SITE_KSI2K_UPDATE
-- -----------------------------
DELIMITER $$

DROP PROCEDURE IF EXISTS `SITE_KSI2K_UPDATE`$$
CREATE PROCEDURE `SITE_KSI2K_UPDATE`(IN a_infrast_name VARCHAR(256),IN a_site_name VARCHAR(256),IN a_ksi2k INTEGER,
  IN a_hepspec INTEGER, INOUT sucess_flag TINYINT)
BEGIN

  DECLARE v_ksi2k   INTEGER;
  DECLARE v_hepspec   INTEGER;
  DECLARE v_siteentry  INTEGER;
  DECLARE no_more_rows BOOLEAN DEFAULT FALSE;
  DECLARE sitecur CURSOR FOR SELECT id FROM site WHERE lower(sitename)=lower(a_site_name) AND infrast_id IN (SELECT id FROM infrastructure WHERE lower(infrastname)=lower(a_infrast_name));
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows = TRUE;
 
  SET sucess_flag=0;
  OPEN sitecur;
 
  sites_loop: LOOP
    FETCH sitecur INTO v_siteentry;
 
    IF no_more_rows THEN
      CLOSE sitecur;
      LEAVE sites_loop;
    END IF;
 
    -- insert/update SITE_STORE_CAP table
    SELECT ksi2k,hspec06 INTO v_ksi2k, v_hepspec
    FROM site_store_cap
    WHERE site_id=v_siteentry;
 
    IF no_more_rows THEN
      -- We must insert a new entry
      INSERT INTO site_store_cap(site_id, phycpucount, logcpucount, ksi2k, hspec06)
      VALUES(v_siteentry, -1, -1, a_ksi2k, a_hepspec);
    ELSE
      -- Update table if there is mismatch
      IF (a_ksi2k != v_ksi2k) OR (a_hepspec != v_hepspec)THEN
        UPDATE site_store_cap
        SET ksi2k=a_ksi2k, hspec06=a_hepspec
        WHERE site_id=v_siteentry;
      END IF;
    END IF;
 
    -- We reset the no_more_rows variable to now exit sites_loop prematurely.
    SET no_more_rows = FALSE;
    SET sucess_flag=1;
  END LOOP sites_loop;

END$$

DELIMITER ;

-- -------------------------------------
-- Procedure: SERVICEENDPOINTS_PER_REGION
-- --------------------------------------

DELIMITER $$

DROP PROCEDURE IF EXISTS `SERVICEENDPOINTS_PER_REGION` $$
CREATE PROCEDURE `SERVICEENDPOINTS_PER_REGION`(a_region_name VARCHAR(50))

MAIN_BLOCK: BEGIN

  DECLARE v_group_type_Id INT(11);
  DECLARE v_group_Id INT(11);
  DECLARE v_group_type_Name VARCHAR(50);
  DECLARE no_more_rows BOOLEAN DEFAULT FALSE;
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows = TRUE;


-- Drop the temporary table used for creating service id and site id entries
   DROP TEMPORARY TABLE IF EXISTS `TMP_SERVICEENDPOINTS_REGION`;
-- check if region name is not null
 -- If not null, extract service_id and site_id for the specified region
 -- If null, extract the entries for all regions

   IF ISNULL(a_region_name)=0 THEN
      -- check if the region entered exists in groups table
     SELECT id, group_type_id INTO v_group_Id, v_group_type_Id
     FROM groups
     WHERE lower(groupname)=lower(a_region_name);
    -- No data is found
     IF no_more_rows THEN
        LEAVE MAIN_BLOCK;
     END IF;
    -- if the entry exists, get typename from group_type table
     SELECT typename INTO v_group_type_Name
     FROM group_type
     WHERE id=v_group_type_Id;
    -- No data is found
     IF no_more_rows THEN
       LEAVE MAIN_BLOCK;
     END IF;
    -- The group type returned MUST corresponds to 'Region'
     IF lower(v_group_type_Name)!= lower('region') THEN
       LEAVE MAIN_BLOCK;
     END IF;
    -- select services from service-site table that corresponds to the region
     CREATE TEMPORARY TABLE IF NOT EXISTS `TMP_SERVICEENDPOINTS_REGION`
     SELECT service_id,site_id FROM
     service_site
     WHERE site_id IN (SELECT site_id FROM site_group WHERE group_id=v_group_Id);
  ELSE
    -- select services from service-site table for all regions
     CREATE TEMPORARY TABLE IF NOT EXISTS `TMP_SERVICEENDPOINTS_REGION`
     SELECT service_id,site_id FROM
     service_site
     WHERE site_id IN
           (SELECT site_id FROM site_group WHERE groups_id IN
                 (SELECT id FROM groups WHERE group_type_id IN
                    (SELECT id from group_type WHERE lower(typename)='region')
                 )
           )
     ORDER BY site_id,service_id;

  END IF;
END $$

DELIMITER ;

-- -----------------------------
-- Procedure:MPI_SERVICES_VO_UPDATE
-- -----------------------------
DELIMITER $$

DROP PROCEDURE IF EXISTS MPI_SERVICES_VO_UPDATE$$
CREATE PROCEDURE MPI_SERVICES_VO_UPDATE(IN a_serviceCEId INTEGER, IN a_serviceMPIId INTEGER)
BEGIN

DECLARE v_servvoId INTEGER DEFAULT -1;
DECLARE v_mpivoId INTEGER DEFAULT -1;
DECLARE no_more_rows BOOLEAN DEFAULT FALSE;
DECLARE servicevo_cursor CURSOR FOR
	SELECT vo_id
        FROM service_vo
        WHERE service_id  = a_serviceCEId;
DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows = TRUE;
	-- map MPI services to VO           
	-- find existing VOs for CE service and map them to MPI service
         OPEN servicevo_cursor;
         servvo_loop: LOOP

                FETCH servicevo_cursor INTO v_servvoId;
		IF no_more_rows THEN
                              CLOSE servicevo_cursor;
                              LEAVE servvo_loop;
                END IF;

                BEGIN
                    DECLARE EXIT HANDLER FOR NOT FOUND
                        BEGIN
                            INSERT INTO service_vo(service_id,vo_id)
                            VALUES (a_serviceMPIId,v_servvoId);
                        END;           

		   -- check if given VO exists for MPI service	
                    SELECT vo_id INTO v_mpivoId FROM service_vo
                    WHERE service_id=a_serviceMPIId and vo_id=v_servvoId;

		    -- SET isdeleted='N'	
                        UPDATE service_vo SET isdeleted='N'
                        WHERE service_id=a_serviceMPIId and vo_id=v_mpivoId;

                END;
                SET no_more_rows = FALSE;
            END LOOP servvo_loop;

END$$

DELIMITER ;

-- -----------------------------
-- Procedure:MPI_SERVICES_UPDATE
-- -----------------------------
DELIMITER $$

DROP PROCEDURE IF EXISTS `MPI_SERVICES_UPDATE`$$
CREATE PROCEDURE `MPI_SERVICES_UPDATE`(IN a_synchronizer_name VARCHAR(100),
IN a_CEservice_name VARCHAR(100), IN a_service_flavour VARCHAR(128),
INOUT sucess_flag TINYINT)
BEGIN

  DECLARE v_servTypeFlavourId   INTEGER;
  DECLARE v_servTypeId          INTEGER;
  DECLARE v_servConstMPI        VARCHAR(20);
  DECLARE v_serviceId           INTEGER;
  DECLARE v_serviceName         VARCHAR(30);
  DECLARE v_ismonitored         VARCHAR(1);
  DECLARE v_isinproduction      VARCHAR(1);
  DECLARE v_serviceFlavourId    INTEGER;
  DECLARE v_serviceCEId         INTEGER;
  DECLARE v_ismonitored_CEflavour         VARCHAR(1);
  DECLARE v_isinproduction_CEflavour      VARCHAR(1);
  DECLARE v_isdeleted_CEflavour           VARCHAR(1);
  DECLARE v_siteId              INTEGER;
  DECLARE v_groupId             INTEGER DEFAULT -1;
  DECLARE v_regionId            INTEGER DEFAULT -1;
  DECLARE v_serviceSiteId       INTEGER DEFAULT -1;
  DECLARE v_servicegroupId      INTEGER DEFAULT -1;
  DECLARE v_voservicegroupId    INTEGER DEFAULT -1;
  DECLARE v_servicegroupId2     INTEGER DEFAULT -1;
  DECLARE v_voservicegroupId2   INTEGER DEFAULT -1;
  DECLARE v_sitegroupId         INTEGER DEFAULT -1;
  DECLARE v_servicelastseenId   INTEGER DEFAULT -1;
  DECLARE v_updateTime          TIMESTAMP;
  DECLARE v_sitename            VARCHAR(255);
  DECLARE v_voId                INTEGER DEFAULT -1;
  DECLARE v_synchronizerId      INTEGER DEFAULT -1;
  DECLARE v_insertId            INTEGER DEFAULT -1;
  DECLARE v_isDeleted           VARCHAR(1);
  DECLARE v_ConstRegion         VARCHAR(15);
  DECLARE v_ConstSite           VARCHAR(15);
  DECLARE v_ConstCE             VARCHAR(20);
  DECLARE v_site_isDeleted      VARCHAR(1);

  SET v_ConstRegion := 'Region';
  SET v_ConstSite := 'Site';
  SET v_ConstCE  := 'CE';

 
  SET v_servTypeFlavourId = get_service_flavour_id(a_service_flavour);

  SET sucess_flag=0;

  SET v_updateTime = CURRENT_TIMESTAMP;

  SET v_voId = get_vo_id('ops');

  SET v_synchronizerId = get_synchronizer_id(a_synchronizer_name);

 -- check if CE service for the 'a_CEservice_name' exists.
        BEGIN
                DECLARE EXIT HANDLER FOR NOT FOUND
                BEGIN   
                        SET sucess_flag=-1;
                END;

                -- find out - id, ismonitored and isinproduction flags status for 'CE' service
                SELECT id, ismonitored, isinproduction, isdeleted  INTO v_serviceCEId, v_ismonitored_CEflavour,v_isinproduction_CEflavour, v_isdeleted_CEflavour FROM service
                WHERE LOWER(hostname) = LOWER(a_CEservice_name)
                    AND flavour_id IN (SELECT id FROM service_type_flavour WHERE flavourname IN ('ARC-CE','CE','CREAM-CE','OSG-CE','gLite-CE')) LIMIT 1;
                -- site-id from CE service              
                SELECT site_id INTO v_siteId FROM service_site WHERE service_id=v_serviceCEId;
        END;

  IF (v_servTypeFlavourId != -1) AND (v_synchronizerId != -1) AND (sucess_flag !=-1) THEN
  
            BEGIN

                    DECLARE EXIT HANDLER FOR NOT FOUND
                        BEGIN
                              
                                INSERT INTO service(flavour_id,hostname,serviceendpoint,ismonitored,isinproduction)
                                VALUES(v_servTypeFlavourId,a_CEservice_name,a_CEservice_name,'N','N');
                      
                                SET v_serviceId=LAST_INSERT_ID();

                                INSERT INTO service_site(service_id, site_id)
                                VALUES (v_serviceId, v_siteId);
                                
                                 -- map MPI services to VO. Use existing 'CE' service vo mappings
                                CALL MPI_SERVICES_VO_UPDATE (v_serviceCEId, v_serviceId);
                                
                                INSERT INTO service_last_seen(service_id, synchronizer_id, lastseen)
                                VALUES (v_serviceId, v_synchronizerId, v_updateTime);

                                SET v_groupId = get_group_id(v_sitename, v_ConstSite);
                
                                IF (v_groupId > -1) THEN
                                        INSERT INTO service_group(service_id,groups_id)
                                        VALUES(v_serviceId,v_groupId);

                                        INSERT INTO vo_service_group(vo_id,service_id,groups_id)
                                        VALUES(v_voId,v_serviceId,v_groupId);
                          
                                END IF;

                                SELECT site_id INTO v_serviceSiteId FROM service_site
                                WHERE service_id=v_serviceId;
              
                                SET v_groupId = get_site_group_id(v_serviceSiteId);
              
                                SET v_regionId = get_site_region_group_id(v_serviceSiteId,v_groupId);
                      
                                IF (v_regionId > -1) THEN
                                        INSERT INTO service_group(service_id,groups_id)
                                        VALUES(v_serviceId,v_regionId);
                                        INSERT INTO vo_service_group(vo_id,service_id,groups_id)
                                        VALUES(v_voId,v_serviceId,v_regionId);
                                END IF;
                                SET sucess_flag = 1;
                                SET v_insertId = 1;
                      
                        END;

                
                -- find id, ismonitored and isinproduction flags status for existing MPI service entry
                SELECT id,ismonitored,isinproduction,isdeleted  INTO v_serviceId, v_ismonitored, v_isinproduction,v_isDeleted FROM service
                WHERE LOWER(hostname) = LOWER(a_CEservice_name)
                    AND flavour_id = v_servTypeFlavourId;

                -- update if 'CE' service and 'MPI' service - ismonitored and isinproduction flags do not match
                IF (v_ismonitored !=v_ismonitored_CEflavour) OR (v_isinproduction !=v_isinproduction_CEflavour) OR (v_isDeleted != v_isdeleted_CEflavour) THEN
                        UPDATE service SET ismonitored=v_ismonitored_CEflavour, isinproduction=v_isinproduction_CEflavour,isdeleted=v_isdeleted_CEflavour
                    WHERE LOWER(hostname) = LOWER(a_CEservice_name)
                        AND flavour_id = v_servTypeFlavourId;
                END IF;

                -- find out site for MPI service                
                SELECT a.id,a.sitename INTO v_siteId,v_sitename FROM site a,service_site b
                WHERE a.id=b.site_id AND b.service_id=v_serviceId;

                IF v_insertId != 1 THEN

                -- set isdeleted='N' for MPI service entry
                UPDATE service SET isdeleted='N'
                WHERE LOWER(hostname) = LOWER(a_CEservice_name)
                    AND flavour_id = v_servTypeFlavourId;

                UPDATE service_site SET isdeleted='N',site_id=v_siteId WHERE service_id=v_serviceId;

                -- map MPI services to VO. Use existing 'CE' service vo mappings
                CALL MPI_SERVICES_VO_UPDATE (v_serviceCEId, v_serviceId);
        
                SET v_groupId = get_group_id(v_sitename, v_ConstSite);
    
                SET v_servicegroupId = get_service_group_id(v_serviceId,v_groupId);
                IF (v_servicegroupId > -1) THEN
                        UPDATE service_group
                        SET isdeleted = 'N' WHERE id = v_servicegroupId;
                ELSE
                        IF (v_groupId > -1) THEN
                                INSERT INTO service_group(service_id,groups_id)
                                VALUES(v_serviceId,v_groupId);
                        END IF;
                END IF;
          
                SET v_voservicegroupId = get_vo_service_group_id('OPS',v_serviceId,v_groupId);
                IF (v_voservicegroupId > -1) THEN
                        UPDATE vo_service_group
                        SET isdeleted = 'N' WHERE id = v_voservicegroupId;
                ELSE
                        IF (v_groupId > -1) THEN
                                INSERT INTO vo_service_group(vo_id,service_id,groups_id)
                                VALUES(v_voId,v_serviceId,v_groupId);
                        END IF;
                END IF;
      
      
                SELECT site_id INTO v_serviceSiteId FROM service_site
                WHERE service_id=v_serviceId;
                
                SET v_sitegroupId = get_site_group_id(v_serviceSiteId);
      
                SET v_regionId = get_site_region_group_id(v_serviceSiteId,v_sitegroupId);
                SET v_servicegroupId2 = get_service_group_id(v_serviceId,v_regionId);
          
                IF (v_servicegroupId2 != -1) THEN
                        UPDATE service_group
                        SET isdeleted = 'N' WHERE id = v_servicegroupId2;
                ELSE
            
                        IF (v_regionId > -1) THEN
                                INSERT INTO service_group(service_id,groups_id)
                                VALUES(v_serviceId,v_regionId);
                        END IF;
                END IF;
                SET v_voservicegroupId2 = get_vo_service_group_id('OPS',v_serviceId,v_regionId);
                IF (v_voservicegroupId2 > -1) THEN
                        UPDATE vo_service_group
                       SET isdeleted = 'N' WHERE id = v_voservicegroupId2;
                    ELSE
                        IF (v_regionId > -1) THEN
                            INSERT INTO vo_service_group(vo_id,service_id,groups_id)
                            VALUES(v_voId,v_serviceId,v_regionId);
                        END IF;
                END IF;
                
                SET v_servicelastseenId = get_service_lastseen_id (v_serviceId,v_synchronizerId);
                IF (v_servicelastseenId  > -1) THEN
                        UPDATE service_last_seen
                        SET lastseen=v_updateTime
                        WHERE service_id=v_serviceId
                        AND synchronizer_id=v_synchronizerId;
                ELSE
        
                        INSERT INTO service_last_seen(service_id, synchronizer_id, lastseen)
                        VALUES (v_serviceId, v_synchronizerId, v_updateTime);
                END IF;
                
                -- update service if site is deleted
                SELECT si.isdeleted INTO v_site_isDeleted 
                FROM service_site ss, service se, site si
                WHERE ss.service_id = se.id
                AND ss.site_id = si.id
                AND LOWER(se.hostname) = LOWER(a_CEservice_name)
                AND se.flavour_id = v_servTypeFlavourId;

                IF (v_site_isDeleted != 'N') THEN
                    UPDATE service SET isdeleted = 'Y' WHERE id = v_serviceId;
                    UPDATE service_site SET isdeleted = 'Y' WHERE service_id = v_serviceId;
                    UPDATE service_group SET isdeleted = 'Y' WHERE id = v_servicegroupId;
                    UPDATE vo_service_group SET isdeleted = 'Y' WHERE id = v_voservicegroupId;
                    UPDATE service_group SET isdeleted = 'Y' WHERE id = v_servicegroupId2;    
                    UPDATE vo_service_group SET isdeleted = 'Y' WHERE id = v_voservicegroupId2;                                   
                END IF;

            END IF;     

            END;
         
         SET sucess_flag = 1;

  END IF;

END$$

DELIMITER ;

-- -------------------------------------
-- Procedure: GET_REGION_SITES
-- --------------------------------------

DELIMITER $$

DROP PROCEDURE IF EXISTS `GET_REGION_SITES`$$
CREATE PROCEDURE `GET_REGION_SITES`(a_voname VARCHAR(128), a_region VARCHAR(128))
BEGIN

  DECLARE v_groupsId INT DEFAULT -1;
  DECLARE v_voId INT DEFAULT -1;
  DECLARE v_siteId INT DEFAULT -1;
  DECLARE v_serviceId INT DEFAULT -1; 

-- FALSE
  DECLARE no_more_rows BOOLEAN DEFAULT FALSE;   
  DECLARE servicecur_vos CURSOR FOR
	 SELECT service_id FROM vo_service_group WHERE vo_id=v_voId AND groups_id=v_groupsId AND isdeleted='N';
 
  DECLARE servicecur_ops CURSOR FOR
	 SELECT service_id FROM service_group WHERE groups_id=v_groupsId AND isdeleted='N';
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows = TRUE;
  
-- Drop the temporary table used for creating site entries for the region
  DROP TEMPORARY TABLE IF EXISTS tmp_region_sites;
  CREATE TEMPORARY TABLE IF NOT EXISTS tmp_region_sites (sites_in_region INTEGER);
  -- VO Id
  SET v_voId = get_vo_id(a_voname);
  -- groups Id
  SELECT id INTO v_groupsId 
  FROM groups
  WHERE lower(groupname) = lower(a_region)
  AND group_type_id IN
  (SELECT id from group_type WHERE lower(typename)='region');
  -- Service Id
  -- check if vo is 'OPS'
  IF v_voId !=-1 AND v_groupsId !=-1 THEN
  	IF lower(a_voname)!= lower('ops') THEN
  		-- VOs other than 'OPS'
		OPEN servicecur_vos;
		services_loop: LOOP
    		FETCH servicecur_vos INTO v_serviceId;
	 
    		IF no_more_rows THEN
      			CLOSE servicecur_vos;
      			LEAVE services_loop;
    		END IF;
        	-- find site corresponding to the service
        	SELECT site_id INTO v_siteId
        	FROM service_site 
		WHERE service_id=v_serviceId;
        	
		INSERT INTO tmp_region_sites (sites_in_region) VALUES(v_siteId);
		SET no_more_rows = FALSE;

		END LOOP services_loop; 
  	ELSE
		-- 'OPS' vo
		OPEN servicecur_ops;
		services_loop: LOOP
    		FETCH servicecur_ops INTO v_serviceId;
	 
    		IF no_more_rows THEN
      			CLOSE servicecur_ops;
      			LEAVE services_loop;
    		END IF;
		-- find site corresponding to the service
        	SELECT site_id INTO v_siteId
        	FROM service_site 
		WHERE service_id=v_serviceId;
 		-- insert into temporary table- sites in the region
        	INSERT INTO tmp_region_sites (sites_in_region) VALUES(v_siteId);
		SET no_more_rows = FALSE;

		END LOOP services_loop; 

  	END IF;
 END IF;
END$$

DELIMITER ;

-- -------------------------------------
-- Procedure: GET_TIER_SITES
-- --------------------------------------
DELIMITER $$

DROP PROCEDURE IF EXISTS `GET_TIER_SITES`$$
CREATE PROCEDURE `GET_TIER_SITES`(a_voname VARCHAR(128), a_tier VARCHAR(1))
BEGIN

  DECLARE v_groupsId INT DEFAULT -1;
  DECLARE v_voId INT DEFAULT -1;
  DECLARE v_siteId INT DEFAULT -1;
  DECLARE v_serviceId INT DEFAULT -1; 
  DECLARE v_sitename VARCHAR(512) DEFAULT NULL;

-- FALSE
  DECLARE no_more_rows BOOLEAN DEFAULT FALSE;   
  DECLARE servicecur_vos CURSOR FOR
	 SELECT service_id FROM vo_service_group WHERE vo_id=v_voId AND groups_id=v_groupsId AND isdeleted='N';

  DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows = TRUE;
  
-- Drop the temporary table used for creating site entries for the given tier
  DROP TEMPORARY TABLE IF EXISTS tmp_tier_sites;
  CREATE TEMPORARY TABLE IF NOT EXISTS tmp_tier_sites (id INTEGER,sitename VARCHAR(512));
  -- VO Id
  SET v_voId = get_vo_id(a_voname);
  -- groups Id
  SELECT id INTO v_groupsId 
  FROM groups
  WHERE lower(groupname) = lower(CONCAT('Tier-',a_tier))
  AND group_type_id IN
  (SELECT id from group_type WHERE lower(typename)=lower('Tier'));
  -- Service Id
  -- check if vo is 'OPS'
  IF v_voId !=-1 AND v_groupsId !=-1 THEN
	OPEN servicecur_vos;
	services_loop: LOOP
    	FETCH servicecur_vos INTO v_serviceId;
	 
    	IF no_more_rows THEN
      		CLOSE servicecur_vos;
      		LEAVE services_loop;
    	END IF;
        -- find site corresponding to the service
         -- find site corresponding to the service
        SELECT a.id,a.sitename INTO v_siteId,v_sitename
        FROM site a, service_site b 
        WHERE a.id=b.site_id and b.service_id=v_serviceId;
        	
	INSERT INTO tmp_tier_sites (id,sitename) VALUES(v_siteId,v_sitename);
	SET no_more_rows = FALSE;

	END LOOP services_loop; 
 END IF;
END$$

DELIMITER ;

-- --------------------------------------
-- PROCEDURE: VO_TOPOLOGY_UPDATE
-- --------------------------------------
DELIMITER $$

DROP PROCEDURE IF EXISTS `VO_TOPOLOGY_UPDATE`$$
CREATE PROCEDURE `VO_TOPOLOGY_UPDATE`(IN a_infrast_name VARCHAR(256),
  IN a_voname VARCHAR(100), IN a_atp_site_name VARCHAR(100), IN a_groupname VARCHAR(100), IN
  a_typename VARCHAR(100), IN a_hostname VARCHAR(256), IN
  a_service_flavour VARCHAR(50), IN a_spacetoken_name VARCHAR(512), IN
a_spacetoken_path VARCHAR(512),INOUT sucess_flag TINYINT)
BEGIN

  DECLARE v_groupsId         INTEGER;
  DECLARE v_grouptypeId      INTEGER;
  DECLARE v_groupsname       VARCHAR(128);
  DECLARE v_groupname_result BOOLEAN; 
  DECLARE v_siteId           INTEGER DEFAULT -1;  
  DECLARE v_infrastId        INTEGER;
  DECLARE v_isDeleted        VARCHAR(1);
  DECLARE v_voId             INTEGER DEFAULT -1;
  DECLARE v_serviceId        INTEGER DEFAULT -1;
  DECLARE v_serviceflavourId INTEGER;
  DECLARE v_spacetokenId     INTEGER DEFAULT -1; 
  DECLARE v_updateTime       TIMESTAMP;
  DECLARE v_synchronizerId   INTEGER DEFAULT -1;

  DECLARE no_more_rows BOOLEAN DEFAULT FALSE;
  DECLARE sitecur CURSOR FOR SELECT id, infrast_id FROM site WHERE LOWER(sitename)=LOWER(a_atp_site_name) AND isdeleted='N';
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows = TRUE;

  SET sucess_flag=0;
  
  OPEN sitecur;

  sites_loop: LOOP
    SET v_siteId=-1;    
    FETCH sitecur INTO v_siteId,v_infrastId;

    IF no_more_rows THEN
      CLOSE sitecur;
      LEAVE sites_loop;
    END IF;

    -- check if groupname and group type name is null string
    IF a_typename='' OR a_groupname='' THEN
      CLOSE sitecur;
      LEAVE sites_loop;
    END IF;
        IF v_siteId =-1 THEN
              SET sucess_flag=4;
              CLOSE sitecur;
              LEAVE sites_loop;
        END IF;
    SET v_voId = get_vo_id(a_voname);

    
    SET v_serviceflavourId = get_service_flavour_id(a_service_flavour);
    
    IF v_serviceflavourId =-1 THEN
      SET sucess_flag=2;
      CLOSE sitecur;
      LEAVE sites_loop;
    END IF; 
   
    SET v_serviceId = get_service_id(a_hostname,v_serviceflavourId);

    IF v_serviceId =-1 THEN
      SET sucess_flag=3;
      CLOSE sitecur;
      LEAVE sites_loop;
    END IF; 


    SET v_updateTime = CURRENT_TIMESTAMP;
    
    SET v_synchronizerId = get_synchronizer_id('vo-feeds');
    
    SET v_grouptypeId = get_group_type_id(a_typename);
    -- add group type
    IF v_grouptypeId =-1 THEN
     
          INSERT INTO group_type(typename,description)
          VALUES(a_typename, concat(a_voname,':',a_typename));
          SET v_grouptypeId=LAST_INSERT_ID();
    ELSE
        UPDATE group_type SET isdeleted='N' WHERE id=v_grouptypeId;     
    END IF;

   
    SET v_groupsId = get_group_id(a_groupname, a_typename);
    -- add group
    IF v_groupsId =-1 THEN
     
          INSERT INTO groups(group_type_id,groupname,description)
          VALUES(v_grouptypeId,a_groupname, concat(a_voname,':',a_groupname));
		 SET v_groupsId=LAST_INSERT_ID();
    ELSE
		SELECT groupname INTO v_groupsname FROM groups WHERE id = v_groupsId;
		SELECT BINARY v_groupsname = a_groupname INTO v_groupname_result;
		IF v_groupname_result = FALSE THEN
			UPDATE groups SET groupname = a_groupname, isdeleted='N' WHERE id = v_groupsId;
		ELSE
			UPDATE groups SET isdeleted='N' WHERE id=v_groupsId;    
		END IF;
    END IF;

  
    IF ((v_voId != -1) AND (v_siteId != -1) AND (v_groupsId > -1) AND (v_serviceId !=-1) AND (v_synchronizerId !=-1)) THEN
      BEGIN
        DECLARE EXIT HANDLER FOR NOT FOUND
        BEGIN
          INSERT INTO vo_service_group(vo_id, service_id, groups_id)
          VALUES(v_voId, v_serviceId, v_groupsId);
        END;

        SELECT isdeleted INTO v_isDeleted
        FROM vo_service_group
        WHERE service_id=v_serviceId
          AND vo_id=v_voId
          AND groups_id=v_groupsId;

        IF (v_isDeleted = 'Y') THEN
          UPDATE vo_service_group
          SET isdeleted='N'
          WHERE service_id=v_serviceId
            AND groups_id=v_groupsId
            AND vo_id=v_voId;
        END IF;
      END;
      IF ASCII(a_spacetoken_name)>0 THEN
      -- insert or update spacetoken and spacetoken last seen
        BEGIN
                DECLARE EXIT HANDLER FOR NOT FOUND
                BEGIN
                -- spacetoken
                INSERT INTO space_token(service_id,tokenname,tokenpath)
                VALUES(v_serviceId,a_spacetoken_name,a_spacetoken_path);
          
                SET v_spacetokenId=LAST_INSERT_ID();   
          
                -- spacetoken lastseen
                INSERT INTO stoken_last_seen(space_token_id,synchronizer_id,lastseen)
                VALUES (v_spacetokenId,v_synchronizerId,v_updateTime);
                
                END;
                
                SELECT id,isdeleted INTO v_spacetokenId,v_isDeleted
                FROM space_token
                WHERE service_id=v_serviceId
                AND tokenname=a_spacetoken_name;
                IF (v_isDeleted = 'Y') THEN
                        UPDATE space_token 
                        SET isdeleted='N'
                        WHERE service_id=v_serviceId
                        AND tokenname=a_spacetoken_name;
                END IF;
                -- update last seen time stamp
                UPDATE stoken_last_seen
                SET lastseen=v_updateTime 
                WHERE space_token_id=v_spacetokenId
                AND synchronizer_id=v_synchronizerId;  
        END;
      -- insert or update vo spacetoken group
        BEGIN
                DECLARE EXIT HANDLER FOR NOT FOUND
                BEGIN
                -- vo spacetoken group
                        INSERT INTO vo_stoken_group(vo_id,space_token_id,groups_id)
                        VALUES(v_voId,v_spacetokenId,v_groupsId);
                END;

                SELECT isdeleted INTO v_isDeleted
                FROM vo_stoken_group
                WHERE space_token_id=v_spacetokenId
                        AND vo_id=v_voId
                        AND groups_id=v_groupsId;

                IF (v_isDeleted = 'Y') THEN
                        UPDATE vo_stoken_group
                        SET isdeleted='N'
                        WHERE space_token_id=v_spacetokenId
                        AND groups_id=v_groupsId
                        AND vo_id=v_voId;
                END IF;
        END; 
       END IF;  
      -- insert or update vo-group
      BEGIN
        DECLARE EXIT HANDLER FOR NOT FOUND
        BEGIN
          INSERT INTO vo_group(vo_id,groups_id)
          VALUES(v_voId,v_groupsId);
        END;
        
        SELECT isdeleted INTO v_isDeleted
        FROM vo_group
        WHERE vo_id=v_voId AND groups_id=v_groupsId;
        
        IF (v_isDeleted = 'Y') THEN
            UPDATE vo_group
              SET isdeleted='N'
            WHERE groups_id=v_groupsId
              AND vo_id=v_voId;
        END IF;
      END;      
      SET sucess_flag=1;
    END IF;
 
   SET no_more_rows = FALSE;
  END LOOP sites_loop;
END$$

DELIMITER ;

-- --------------------------------------
-- PROCEDURE: MARK_DOWNTIMES_AS_DELETED
-- --------------------------------------
DELIMITER $$

DROP PROCEDURE IF EXISTS `MARK_DOWNTIMES_AS_DELETED`$$
CREATE PROCEDURE `MARK_DOWNTIMES_AS_DELETED`(IN a_gocdbdowntimeId INTEGER,
INOUT sucess_flag TINYINT)
BEGIN
  
  DECLARE no_more_rows BOOLEAN DEFAULT FALSE;
  DECLARE v_downtimeId INTEGER DEFAULT -1;
  DECLARE sitedowntimescur CURSOR FOR SELECT id FROM site_downtime WHERE downtime_id=a_gocdbdowntimeId;
  DECLARE servicedowntimescur CURSOR FOR SELECT id FROM service_downtime WHERE downtime_id=a_gocdbdowntimeId;  
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows = TRUE;
 
  SET sucess_flag=0;

  -- mark isdeleted='Y' in downtimes
   UPDATE downtime SET isdeleted='Y' 
   WHERE id=a_gocdbdowntimeId;

  -- mark isdeleted='Y' in site-downtimes
  OPEN sitedowntimescur;
 
  downtimes_loop: LOOP
    FETCH sitedowntimescur INTO v_downtimeId;
 
    IF no_more_rows THEN
      CLOSE sitedowntimescur;
      LEAVE downtimes_loop;
    END IF;

    IF no_more_rows = FALSE THEN
	UPDATE site_downtime SET isdeleted='Y' 
    	WHERE id=v_downtimeId;
    END IF;
    
    SET no_more_rows = FALSE;

  END LOOP downtimes_loop;

 SET no_more_rows = FALSE;

 -- mark isdeleted='Y' in service_downtimes
  OPEN servicedowntimescur;
 
  downtimes_loop: LOOP
    FETCH servicedowntimescur INTO v_downtimeId;

    IF no_more_rows THEN
      CLOSE servicedowntimescur;
      LEAVE downtimes_loop;
    END IF;

    IF no_more_rows = FALSE THEN
    	UPDATE service_downtime SET isdeleted='Y' 
    	WHERE id=v_downtimeId;
    END IF;
    SET no_more_rows = FALSE;

  END LOOP downtimes_loop;
 
 SET sucess_flag=1; 

END$$

DELIMITER ;

-- --------------------------------
-- Procedure: UPDATE_OSG_DOWNTIMES
-- --------------------------------
DELIMITER $$

DROP PROCEDURE IF EXISTS UPDATE_OSG_DOWNTIMES $$
CREATE PROCEDURE UPDATE_OSG_DOWNTIMES(IN a_starttime DATETIME,
IN a_endtime DATETIME, IN a_classification VARCHAR(128),
IN a_osgdowntimeId INTEGER,IN a_severity VARCHAR(128), IN a_description VARCHAR(1024),
IN a_infrast_name VARCHAR(256), IN a_hostname VARCHAR(512),
IN a_site_name VARCHAR(100), IN a_action VARCHAR(100),
INOUT sucess_flag INTEGER)

BEGIN
 
  DECLARE no_more_rows BOOLEAN DEFAULT FALSE;
  DECLARE v_downtimeId INTEGER DEFAULT -1;
  DECLARE v_Id INTEGER DEFAULT -1;
  DECLARE v_starttime TIMESTAMP;
  DECLARE v_endtime TIMESTAMP;
  DECLARE v_classification VARCHAR(128);
  DECLARE v_osgdowntimeId INTEGER;
  DECLARE v_severity VARCHAR(128);
  DECLARE v_description VARCHAR(1024);
  DECLARE v_updateTime TIMESTAMP;
  DECLARE v_isdeleted VARCHAR(1); 

  DECLARE sitedowntimescur CURSOR FOR SELECT id FROM site_downtime WHERE downtime_id=v_downtimeId;
  DECLARE servicedowntimescur CURSOR FOR SELECT id FROM service_downtime WHERE downtime_id=v_downtimeId;  
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows = TRUE;
 
  SET sucess_flag=0;
 
 SET v_updateTime = CURRENT_TIMESTAMP;

  IF lower(a_action)='cancel' THEN
       
        SELECT id INTO v_downtimeId FROM downtime
        WHERE osgdowntimeid=a_osgdowntimeId;
       
        UPDATE downtime SET isdeleted='Y'
        WHERE id=v_downtimeId;
       
        OPEN sitedowntimescur;
 
        downtimes_loop: LOOP
                FETCH sitedowntimescur INTO v_Id;
 
                IF no_more_rows THEN
                        CLOSE sitedowntimescur;
                        LEAVE downtimes_loop;
                END IF;

                IF no_more_rows = FALSE THEN
                        UPDATE site_downtime SET isdeleted='Y'
                        WHERE id=v_Id;
                END IF;
   
                SET no_more_rows = FALSE;
       
        END LOOP downtimes_loop;

        SET no_more_rows = FALSE;

 
        OPEN servicedowntimescur;
 
        downtimes_loop: LOOP
                FETCH servicedowntimescur INTO v_Id;

                IF no_more_rows THEN
                        CLOSE servicedowntimescur;
                        LEAVE downtimes_loop;
                END IF;

                IF no_more_rows = FALSE THEN
                        UPDATE service_downtime SET isdeleted='Y'
                        WHERE id=v_Id;
                END IF;
                SET no_more_rows = FALSE;

        END LOOP downtimes_loop;

  ELSEIF lower(a_action)='modify' THEN
       
         BEGIN
        	-- DECLARE EXIT HANDLER FOR NOT FOUND
		--	BEGIN
		--		INSERT INTO downtime (starttimestamp, endtimestamp, inserttimestamp, classification, osgdowntimeid, severity, description)
            	--		VALUES (a_starttime, a_endtime, v_updateTime, a_classification, a_osgdowntimeid, a_severity, a_description);
		--	END;

		SELECT id, starttimestamp, endtimestamp, description, severity, classification, isdeleted
        	INTO v_downtimeId, v_starttime, v_endtime, v_description, v_severity, v_classification, v_isdeleted FROM downtime
        	WHERE osgdowntimeid=a_osgdowntimeid;  
       
        	IF (a_starttime !=v_starttime) OR (a_endtime !=v_endtime) OR (a_description !=IFNULL(v_description,'')) OR
        	(a_severity !=IFNULL(v_severity,'')) OR (a_classification !=IFNULL(v_classification,'')) OR (v_isdeleted='Y') THEN  
                	UPDATE downtime SET isdeleted='N',starttimestamp=a_starttime,endtimestamp=a_endtime,description=a_description,
			severity=a_severity,classification=a_classification,inserttimestamp=v_updateTime
                	WHERE id=v_downtimeId;
        	END IF;
	END;
  END IF;
 
 
 
 SET sucess_flag=1;

END$$

DELIMITER ;
-- ----------------------------------------
-- Procedure: CHK_DUPLICATE_GOCDB_DOWNTIMES
-- -----------------------------------------
DELIMITER $$

DROP PROCEDURE IF EXISTS `CHK_DUPLICATE_GOCDB_DOWNTIMES`$$
CREATE PROCEDURE `CHK_DUPLICATE_GOCDB_DOWNTIMES`()
BEGIN

  DECLARE v_downtimeId INT;
  DECLARE v_total INT;
  DECLARE v_gocdbpk VARCHAR(20);
  DECLARE v_downtime_entries INT DEFAULT 0; 
  DECLARE no_more_rows BOOLEAN DEFAULT FALSE;
  DECLARE downtime_cur CURSOR FOR   
   SELECT a.total,a.id,a.gocdbpk FROM 
	(SELECT count(id) total, id,gocdbpk FROM downtime GROUP BY gocdbpk) a 
	WHERE a.total>1 order by a.gocdbpk;
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows = TRUE;  
 
	SELECT a.total INTO v_downtime_entries FROM
		(SELECT count(id) total, gocdbpk FROM
		downtime GROUP BY gocdbpk
		) a 
		WHERE a.total>1 order BY a.gocdbpk LIMIT 1;
	IF v_downtime_entries>1 THEN
		OPEN downtime_cur;
 
       		downtime_loop: LOOP
			BEGIN
             		FETCH downtime_cur INTO v_total, v_downtimeId, v_gocdbpk;
			IF v_total=1 THEN
				CLOSE downtime_cur;
				LEAVE downtime_loop;
			ELSE
                                DELETE FROM service_downtime where downtime_id=v_downtimeId;
                                DELETE FROM site_downtime where downtime_id=v_downtimeId;
				DELETE FROM downtime where id=v_downtimeId;
			END IF;
			IF no_more_rows THEN
               			CLOSE downtime_cur;
               			LEAVE downtime_loop;
         		END IF;
 
         		SET no_more_rows = FALSE;
			END;
	       END LOOP downtime_loop;
	END IF;
END$$

DELIMITER ;

-- ---------------------------------
-- Procedure:MARK_GROUPS_AS_DELETED
-- ---------------------------------
DELIMITER $$

DROP PROCEDURE IF EXISTS `MARK_GROUPS_AS_DELETED`$$
CREATE PROCEDURE `MARK_GROUPS_AS_DELETED`(
  IN a_groupsId INTEGER,
  IN a_type VARCHAR(100))
BEGIN

        UPDATE groups SET isdeleted='Y' WHERE id=a_groupsId;

	BLOCK1: begin
		DECLARE v_vogroupId INTEGER;
		DECLARE no_more_rows1 BOOLEAN DEFAULT FALSE;
		DECLARE vogroupCur CURSOR FOR
			SELECT id
			FROM vo_group
			WHERE groups_id=a_groupsId;
		DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows1=TRUE;
		-- vo-group table
		OPEN vogroupCur;
	
		vogroup_loop: LOOP
		        FETCH vogroupCur INTO v_vogroupId;
		        IF no_more_rows1 THEN
		              CLOSE vogroupCur;
		              LEAVE vogroup_loop;
		        END IF;

			UPDATE vo_group SET isdeleted='Y' WHERE id=v_vogroupId;	
			SET no_more_rows1=False;

		END LOOP vogroup_loop;
        end BLOCK1;	
	BLOCK2: begin
		DECLARE v_voservicegroupId INTEGER;
		DECLARE no_more_rows2 BOOLEAN DEFAULT FALSE;
		DECLARE voservicegroupCur CURSOR FOR
			SELECT id
			FROM vo_service_group
			WHERE groups_id=a_groupsId;
		DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows2=TRUE;

		-- vo-service-group table
		OPEN voservicegroupCur;

		voservicegroup_loop: LOOP
		        FETCH voservicegroupCur INTO v_voservicegroupId;
		        IF no_more_rows2 THEN
		              CLOSE voservicegroupCur;
		              LEAVE voservicegroup_loop;
		        END IF;

			UPDATE vo_service_group SET isdeleted='Y' WHERE id=v_voservicegroupId;
			SET no_more_rows2=False;
		END LOOP voservicegroup_loop;
	end BLOCK2;

	IF lower(a_type)='region' THEN

	BLOCK3: begin
		DECLARE v_sitegroupId INTEGER;
		DECLARE no_more_rows3 BOOLEAN DEFAULT FALSE;
		DECLARE sitegroupCur CURSOR FOR
			SELECT id
			FROM site_group
			WHERE groups_id=a_groupsId;
		DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows3=TRUE;

		-- site-group table
		OPEN sitegroupCur;

		sitegroup_loop: LOOP
		        FETCH sitegroupCur INTO v_sitegroupId;
		        IF no_more_rows3 THEN
		              CLOSE sitegroupCur;
		              LEAVE sitegroup_loop;
		        END IF;

			UPDATE site_group SET isdeleted='Y' WHERE id=v_sitegroupId;
			SET no_more_rows3=False;
		END LOOP sitegroup_loop;
	end BLOCK3;
	END IF;

END$$

DELIMITER ;

-- ---------------------------------
-- Procedure:DELETE_VO_GROUPS
-- ---------------------------------
DELIMITER $$

DROP PROCEDURE IF EXISTS `DELETE_VO_GROUPS`$$
CREATE PROCEDURE `DELETE_VO_GROUPS`(
  IN a_voname VARCHAR(100))
BEGIN
DECLARE v_voId INT(11);

	SET v_voId = get_vo_id(a_voname);

	IF v_voId !=-1 THEN

	BLOCK1: begin
		DECLARE v_vogroupId INTEGER;
		DECLARE no_more_rows1 BOOLEAN DEFAULT FALSE;
		DECLARE vogroupCur CURSOR FOR
			SELECT id
			FROM vo_group
			WHERE vo_id=v_voId AND isdeleted='N';
		DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows1=TRUE;
		-- vo-group table
		OPEN vogroupCur;
	
		vogroup_loop: LOOP
		        FETCH vogroupCur INTO v_vogroupId;
		        IF no_more_rows1 THEN
		              CLOSE vogroupCur;
		              LEAVE vogroup_loop;
		        END IF;

			UPDATE vo_group SET isdeleted='Y' WHERE id=v_vogroupId;	
			SET no_more_rows1=False;

		END LOOP vogroup_loop;
        end BLOCK1;	
	BLOCK2: begin
		DECLARE v_voservicegroupId INTEGER;
		DECLARE no_more_rows2 BOOLEAN DEFAULT FALSE;
		DECLARE voservicegroupCur CURSOR FOR
			SELECT id
			FROM vo_service_group
			WHERE vo_id=v_voId AND isdeleted='N';
		DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows2=TRUE;

		-- vo-service-group table
		OPEN voservicegroupCur;

		voservicegroup_loop: LOOP
		        FETCH voservicegroupCur INTO v_voservicegroupId;
		        IF no_more_rows2 THEN
		              CLOSE voservicegroupCur;
		              LEAVE voservicegroup_loop;
		        END IF;

			UPDATE vo_service_group SET isdeleted='Y' WHERE id=v_voservicegroupId;
			SET no_more_rows2=False;
		END LOOP voservicegroup_loop;
	end BLOCK2;

    	END IF;	
END$$

DELIMITER ;


-- -----------------------------------
-- Procedure:MARK_VOGROUPS_AS_DELETED
-- ------------------------------------
DELIMITER $$

DROP PROCEDURE IF EXISTS `MARK_VOGROUPS_AS_DELETED`$$
CREATE PROCEDURE `MARK_VOGROUPS_AS_DELETED`(IN a_voId INTEGER)
BEGIN
	
	UPDATE vo SET isdeleted='Y' WHERE id=a_voId;
	BLOCK1: begin
		DECLARE v_vogroupId INTEGER;
		DECLARE no_more_rows1 BOOLEAN DEFAULT FALSE;
		DECLARE vogroupCur CURSOR FOR
			SELECT id
			FROM vo_group
			WHERE vo_id=a_voId;
		DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows1=TRUE;
		-- vo-group table
		OPEN vogroupCur;
		vogroup_loop: LOOP
	        	FETCH vogroupCur INTO v_vogroupId;
	        	IF no_more_rows1 THEN
	              		CLOSE vogroupCur;
	           		LEAVE vogroup_loop;
		        END IF;
			UPDATE vo_group SET isdeleted='Y' WHERE id=v_vogroupId;	
			SET no_more_rows1=False;
			END LOOP vogroup_loop;
        end BLOCK1;	
	BLOCK2: begin
		DECLARE v_voservicegroupId INTEGER;
		DECLARE no_more_rows2 BOOLEAN DEFAULT FALSE;
		DECLARE voservicegroupCur CURSOR FOR
			SELECT id
			FROM vo_service_group
			WHERE vo_id=a_voId;
		DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows2=TRUE;
		-- vo-service-group table
		OPEN voservicegroupCur;

		voservicegroup_loop: LOOP
		       	FETCH voservicegroupCur INTO v_voservicegroupId;
		       	IF no_more_rows2 THEN
		             	CLOSE voservicegroupCur;
		              	LEAVE voservicegroup_loop;
		        END IF;

			UPDATE vo_service_group SET isdeleted='Y' WHERE id=v_voservicegroupId;
			SET no_more_rows2=False;
		END LOOP voservicegroup_loop;
	end BLOCK2;

END$$

DELIMITER ;

-- ---------------------------------------
-- Procedure:MARK_GROUP_TYPES_AS_DELETED
-- ------------------------------------------
DELIMITER $$

DROP PROCEDURE IF EXISTS `MARK_GROUP_TYPES_AS_DELETED`$$
CREATE PROCEDURE `MARK_GROUP_TYPES_AS_DELETED`(
  IN a_grouptype_name VARCHAR(100))
BEGIN

DECLARE v_groupsId INTEGER DEFAULT -1;

MAIN: begin
		DECLARE v_groupId INTEGER;
		DECLARE no_more_rows_main BOOLEAN DEFAULT FALSE;
		DECLARE groupCur CURSOR FOR
			SELECT id
			FROM groups
			WHERE group_type_id 
			IN
			(
			SELECT id from group_type WHERE LOWER(typename)=LOWER(a_grouptype_name)
			);
		DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows_main=TRUE;
		-- groups table
		OPEN groupCur;
	
		group_loop: LOOP
		        FETCH groupCur INTO v_groupsId;
		        IF no_more_rows_main THEN
		              CLOSE groupCur;
		              LEAVE group_loop;
		        END IF;


        	UPDATE groups SET isdeleted='Y' WHERE id=v_groupsId;

		BLOCK1: begin
			DECLARE v_vogroupId INTEGER;
			DECLARE no_more_rows1 BOOLEAN DEFAULT FALSE;
			DECLARE vogroupCur CURSOR FOR
				SELECT id
				FROM vo_group
				WHERE groups_id=v_groupsId;
			DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows1=TRUE;
			-- vo-group table
			OPEN vogroupCur;
	
			vogroup_loop: LOOP
		        	FETCH vogroupCur INTO v_vogroupId;
		        	IF no_more_rows1 THEN
		              		CLOSE vogroupCur;
		              		LEAVE vogroup_loop;
		        	END IF;

				UPDATE vo_group SET isdeleted='Y' WHERE id=v_vogroupId;	
				SET no_more_rows1=False;

			END LOOP vogroup_loop;
        	end BLOCK1;	
		BLOCK2: begin
			DECLARE v_voservicegroupId INTEGER;
			DECLARE no_more_rows2 BOOLEAN DEFAULT FALSE;
			DECLARE voservicegroupCur CURSOR FOR
				SELECT id
				FROM vo_service_group
				WHERE groups_id=v_groupsId;
			DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows2=TRUE;

			-- vo-service-group table
			OPEN voservicegroupCur;

			voservicegroup_loop: LOOP
		        	FETCH voservicegroupCur INTO v_voservicegroupId;
		        	IF no_more_rows2 THEN
		              		CLOSE voservicegroupCur;
		              		LEAVE voservicegroup_loop;
		        	END IF;

				UPDATE vo_service_group SET isdeleted='Y' WHERE id=v_voservicegroupId;
				SET no_more_rows2=False;
			END LOOP voservicegroup_loop;
		end BLOCK2;

		SET no_more_rows_main=False;

		END LOOP group_loop;
end MAIN;	
	
END$$

DELIMITER ;


-- --------------------------------
-- Procedure:MARK_SITES_AS_DELETED
-- ---------------------------------
DELIMITER $$

DROP PROCEDURE IF EXISTS `MARK_SITES_AS_DELETED`$$
CREATE PROCEDURE `MARK_SITES_AS_DELETED`(IN a_siteId INTEGER)

BEGIN

DECLARE v_servicesiteId INTEGER DEFAULT -1;
DECLARE no_more_rows BOOLEAN DEFAULT FALSE;
DECLARE service_siteCur CURSOR FOR
 SELECT id from service_site WHERE site_id=a_siteId;

DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows=TRUE;

-- update site, site_store_cap and site_last_seen tables
UPDATE site SET isdeleted='Y' WHERE id=a_siteId;

-- update service_site
OPEN service_siteCur;

      site_loop: LOOP
   
        	FETCH service_siteCur INTO v_servicesiteId;
        	IF no_more_rows THEN
              		CLOSE service_siteCur;
              		LEAVE site_loop;
        	END IF;
		
		UPDATE service_site SET isdeleted='Y' WHERE id=v_servicesiteId;	
		SET no_more_rows=False;

	END LOOP site_loop;

END$$

DELIMITER ;

-- --------------------------------
-- Procedure:CHANGE_GOCDB_SITENAME
-- --------------------------------

DELIMITER $$

DROP PROCEDURE IF EXISTS `CHANGE_GOCDB_SITENAME`$$
CREATE PROCEDURE `CHANGE_GOCDB_SITENAME`(IN a_sitename VARCHAR(100),
IN a_gocdbpk VARCHAR(100),INOUT sucess_flag INT)
BEGIN

  DECLARE v_siteId   INTEGER;
  DECLARE v_sitename VARCHAR(100);
  DECLARE v_isdeleted   VARCHAR(1);
  DECLARE v_groupId   INTEGER;
  DECLARE v_duplicates INTEGER DEFAULT -1;
  DECLARE v_siteokId  INTEGER;
  DECLARE v_siteokname VARCHAR(100);

  DECLARE no_more_rows BOOLEAN DEFAULT FALSE;
  DECLARE sitecur CURSOR FOR SELECT id,sitename,isdeleted FROM site WHERE gocdbpk=a_gocdbpk;
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows = TRUE;
  DROP TEMPORARY TABLE IF EXISTS tmp_sites;
  CREATE TEMPORARY TABLE IF NOT EXISTS tmp_sites (id INTEGER,sitename VARCHAR(512),isdeleted VARCHAR(1));
  
SET sucess_flag=0;
     -- check if there are multiple sites for given gocdbpk
SELECT a.total INTO v_duplicates FROM (SELECT count(id) total, gocdbpk FROM site where gocdbpk !='' AND gocdbpk=a_gocdbpk group by gocdbpk) a WHERE a.total>1;
        IF v_duplicates>1 THEN

-- fill the temporary table with site entries for given gocdb
OPEN sitecur;
 
      sites_loop: LOOP
            FETCH sitecur INTO v_siteId, v_sitename, v_isdeleted;
IF no_more_rows THEN
       CLOSE sitecur;
       LEAVE sites_loop;
     END IF;
     INSERT INTO tmp_sites(id,sitename,isdeleted) VALUES(v_siteId,v_sitename,v_isdeleted);
SET no_more_rows = FALSE;
END LOOP sites_loop;

 -- after execution of the above loop, we have all the sites with their ids and sitenames for given gocdbpk
BLOCK: begin
  DECLARE no_more_rows_tmp BOOLEAN DEFAULT FALSE;
  DECLARE tmp_sitecur CURSOR FOR
SELECT id,sitename,isdeleted FROM tmp_sites;
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows_tmp = TRUE;

    -- find out site with isdeleted='Y' and lowest id
   SELECT id, sitename INTO v_siteokId, v_siteokname FROM tmp_sites WHERE isdeleted='Y' ORDER BY id ASC LIMIT 1;
 

-- mark all the remaining sites in temporary table as deleted and set gocdbpk to NULL

OPEN tmp_sitecur;
 
      tmp_sites_loop: LOOP
            FETCH tmp_sitecur INTO v_siteId, v_sitename, v_isdeleted;
IF no_more_rows_tmp THEN
       CLOSE tmp_sitecur;
       LEAVE tmp_sites_loop;
     END IF;
     IF v_siteId != v_siteokId and v_siteokId !=-1 THEN
UPDATE site SET sitename=concat('old_',v_sitename),gocdbpk=concat('old_',a_gocdbpk),isdeleted='Y' WHERE id=v_siteId;
-- update groupname in groups table
  SET v_groupId = get_group_id(v_sitename, 'Site');
  UPDATE groups SET groupname=concat('old_',v_sitename),isdeleted='Y' WHERE id = v_groupId;
END IF;
SET no_more_rows_tmp = FALSE;
END LOOP tmp_sites_loop;
END BLOCK;
-- update site 
IF v_siteokId !=-1 THEN
UPDATE site SET sitename=a_sitename,gocdbpk=a_gocdbpk, isdeleted ='N' WHERE id=v_siteokId;
-- update groupname in groups table
  SET v_groupId = get_group_id(v_siteokname, 'Site');
  UPDATE groups SET groupname=a_sitename,isdeleted='N' WHERE id = v_groupId;
END IF;
SET sucess_flag=1;
  END IF;

END$$

DELIMITER ;

-- ------------------------------------------------
-- Procedure:MARK_LFC_CEN_SERV_AS_DELETED
-- ------------------------------------------------
DELIMITER $$

DROP PROCEDURE IF EXISTS `MARK_LFC_CEN_SERV_AS_DELETED`$$
CREATE PROCEDURE `MARK_LFC_CEN_SERV_AS_DELETED`(IN a_hostname VARCHAR(100),INOUT sucess_flag INT)
BEGIN

DECLARE v_serviceflavourId INTEGER DEFAULT -1;
DECLARE v_voId INTEGER DEFAULT -1;
DECLARE v_cnt INTEGER DEFAULT -1;
DECLARE v_servicevoId INTEGER DEFAULT -1;
DECLARE v_curcnt INTEGER DEFAULT -1;

DECLARE no_more_rows BOOLEAN DEFAULT FALSE;
DECLARE servicecur CURSOR FOR 
	SELECT b.id FROM service a, service_vo b
	WHERE a.id=b.service_id AND a.hostname!=a_hostname AND a.flavour_id=v_serviceflavourId 
	AND b.vo_id=v_voId AND a.isdeleted='N' AND b.isdeleted='N' ORDER BY a.id;

DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows = TRUE;

SET sucess_flag=0;
-- find id for 'OPS' vo
SET v_voId=get_vo_id('ops');
-- find service-type-flavour for 'LFC-Central(LFC_C)' flavour
SET v_serviceflavourId=get_service_flavour_id('Central-LFC');

IF v_voId!=-1 AND v_serviceflavourId !=-1 THEN
	-- find how many LFC-central services exists for 'OPS' vo
	SELECT count(*) INTO v_cnt FROM service a, service_vo b WHERE a.id=b.service_id AND a.flavour_id=v_serviceflavourId
	AND b.vo_id=v_voId AND a.isdeleted='N' AND b.isdeleted='N'group by b.vo_id;
	SET v_curcnt=v_cnt;
	IF v_cnt>1 THEN
		OPEN servicecur;
			services_loop: LOOP
				FETCH servicecur INTO v_servicevoId;

				IF no_more_rows OR v_curcnt=1 THEN
					CLOSE servicecur;
					LEAVE services_loop;
				END IF;

				UPDATE service_vo SET isdeleted='Y' WHERE id=v_servicevoId;
				-- reduce count by  1				
				SET v_curcnt = v_curcnt -1;
				SET no_more_rows = FALSE;
			END LOOP services_loop;
	END IF;
SET sucess_flag=1;
END IF;
END$$

DELIMITER ;

-- -------------------------------------
-- Procedure:DELETE_SITES_IN_FEDERATION
-- --------------------------------------
DELIMITER $$

DROP PROCEDURE IF EXISTS `DELETE_SITES_IN_FEDERATION`$$
CREATE PROCEDURE `DELETE_SITES_IN_FEDERATION`(
  IN a_siteId INTEGER)
BEGIN

MAIN_BLOCK:begin

          	DECLARE v_serviceId INTEGER;
          	DECLARE v_groupsId INTEGER;
			DECLARE no_more_rows BOOLEAN DEFAULT FALSE;
			DECLARE FederationCur CURSOR FOR
			-- find groups-id
			SELECT DISTINCT service_id, groups_id FROM vo_service_group 
			WHERE service_id IN
			(SELECT id FROM service_site WHERE isdeleted='N' AND site_id=a_siteId) 
			AND groups_id IN (SELECT id FROM groups 
			WHERE group_type_id IN
			(SELECT id FROM group_type WHERE LOWER(typename)=LOWER('Federation')));
			DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows=TRUE;
			
			-- find federation groups
			OPEN FederationCur;
	
			federation_loop: LOOP
				FETCH FederationCur INTO v_serviceId, v_groupsId;
				IF no_more_rows THEN
					CLOSE FederationCur;
					LEAVE federation_loop;
				END IF;

			IF v_groupsId !=-1 THEN
				
				BLOCK1: begin
					DECLARE v_voservicegroupId INTEGER;
					DECLARE no_more_rows2 BOOLEAN DEFAULT FALSE;
					DECLARE voservicegroupCur CURSOR FOR
						SELECT id
						FROM vo_service_group
						WHERE groups_id=v_groupsId and service_id=v_serviceId;
					DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows2=TRUE;

					-- vo-service-group table
					OPEN voservicegroupCur;

					voservicegroup_loop: LOOP
						FETCH voservicegroupCur INTO v_voservicegroupId;
						IF no_more_rows2 THEN
							CLOSE voservicegroupCur;
							LEAVE voservicegroup_loop;
						END IF;
	
						UPDATE vo_service_group SET isdeleted='Y' WHERE id=v_voservicegroupId;
						SET no_more_rows2=False;
					END LOOP voservicegroup_loop;
				end BLOCK1;
			END IF;

			SET no_more_rows=False;
			END LOOP federation_loop;

end MAIN_BLOCK;
END$$

DELIMITER ;

-- -------------------------------------
-- Procedure:DELETE_DUP_REGION_SERVICES
-- -------------------------------------
DELIMITER $$

DROP PROCEDURE IF EXISTS `DELETE_DUP_REGION_SERVICES`$$
CREATE PROCEDURE `DELETE_DUP_REGION_SERVICES`(IN a_serviceId INTEGER, IN a_groupId INTEGER)
BEGIN

  DECLARE v_groupId   INTEGER;
  DECLARE v_cnt       INTEGER;
  DECLARE no_more_rows BOOLEAN DEFAULT FALSE;
  DECLARE groupcur CURSOR FOR SELECT DISTINCT groups_id FROM vo_service_group WHERE service_id=a_serviceId AND groups_id IN (SELECT id FROM groups WHERE group_type_id IN (SELECT id FROM group_type WHERE LOWER(typename)=LOWER('Region'))) and isdeleted='N';
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows = TRUE;

SELECT DISTINCT COUNT(*) INTO v_cnt FROM vo_service_group WHERE service_id=a_serviceId AND groups_id IN (SELECT id FROM groups WHERE group_type_id IN (SELECT id FROM group_type WHERE LOWER(typename)=LOWER('Region'))) and isdeleted='N';

IF v_cnt>1 THEN
OPEN groupcur;
 
  groups_loop: LOOP
    FETCH groupcur INTO v_groupId;
 
    IF no_more_rows THEN
      CLOSE groupcur;
      LEAVE groups_loop;
    END IF;
    IF v_groupid != a_groupId THEN
    UPDATE service_group SET isdeleted='Y' WHERE service_id=a_serviceId and groups_id=v_groupId;
        UPDATE vo_service_group SET isdeleted='Y' WHERE service_id=a_serviceId and groups_id=v_groupId;
    END IF;
        
    END LOOP;

END IF;

END$$

DELIMITER ;


-- ---------------------
-- Procedure: VO_UPDATE
-- --------------------
DELIMITER $$

DROP PROCEDURE IF EXISTS `VO_UPDATE`$$
CREATE PROCEDURE `VO_UPDATE`(IN a_voname VARCHAR(100))
BEGIN

  DECLARE v_voId  INTEGER DEFAULT -1;
  
  SET v_voId = get_vo_id(a_voname);
  IF v_voId = -1 THEN
    INSERT INTO vo(voname) VALUES (a_voname);
  ELSE
    UPDATE vo SET isdeleted='N' WHERE id=v_voId;
  END IF; 

END$$

DELIMITER ;


-- ---------------------------------
-- Procedure: SERVICE_FLAVOUR_UPDATE
-- ---------------------------------
DELIMITER $$

DROP PROCEDURE IF EXISTS `SERVICE_FLAVOUR_UPDATE`$$
CREATE PROCEDURE `SERVICE_FLAVOUR_UPDATE`(IN a_serviceflavourname VARCHAR(100))
BEGIN

  DECLARE v_servFlavourId INTEGER;
  
  SET v_servFlavourId = get_service_flavour_id(a_serviceflavourname);

  IF v_servFlavourId = -1 THEN  
    INSERT INTO service_type_flavour(flavourname) VALUES (a_serviceflavourname);      
  ELSE
    UPDATE service_type_flavour SET isdeleted='N' WHERE id=v_servFlavourId;
  END IF;
      
END$$

DELIMITER ;


-- -----------------------------------------
-- PROCEDURE: ROC_CONTACTS_UPDATE
-- -----------------------------------------

DELIMITER $$

DROP PROCEDURE IF EXISTS `ROC_CONTACTS_UPDATE`$$
CREATE PROCEDURE `ROC_CONTACTS_UPDATE` (IN a_rocname VARCHAR(256), IN a_certdn VARCHAR(256), IN a_name VARCHAR(256), IN a_email VARCHAR(256), IN a_tel VARCHAR(256), IN a_role VARCHAR(256))

BEGIN
    DECLARE v_rocId INTEGER DEFAULT -1;
    DECLARE v_contactId INTEGER DEFAULT -1;
    DECLARE v_contactGroupId INTEGER DEFAULT -1;

    DECLARE no_more_rows BOOLEAN DEFAULT FALSE;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows=TRUE;

    SELECT id INTO v_rocId FROM groups where lower(groupname) = lower(a_rocname) and group_type_id = 2;
    IF NOT no_more_rows THEN
        SET v_contactId = get_contact_id(a_certdn);
        IF ( v_contactId = -1 ) THEN
    	    INSERT INTO contact(dn, name, email, telephone) VALUES (a_certdn, a_name, a_email, a_tel);
    	    SET v_contactId=LAST_INSERT_ID();
    	ELSE
    		UPDATE contact SET name=a_name, email=a_email, telephone=a_tel WHERE id=v_contactId;
    	END IF;

        SET v_contactGroupId = get_contact_group_id(v_rocId, v_contactId, a_role);
        IF ( v_contactGroupId = -1 ) THEN
    	    INSERT INTO contact_group(groups_id, contact_id, role) VALUES (v_rocId, v_contactId, a_role);
    	END IF;
	END IF;    
    SET no_more_rows = FALSE;
    
END$$

DELIMITER ;

-- -----------------------------------------
-- PROCEDURE: SITE_CONTACTS_UPDATE
-- -----------------------------------------

DELIMITER $$

DROP PROCEDURE IF EXISTS `SITE_CONTACTS_UPDATE`$$
CREATE PROCEDURE `SITE_CONTACTS_UPDATE` (IN a_infrastructure VARCHAR(256), IN a_sitename VARCHAR(256), IN a_certdn VARCHAR(256), IN a_name VARCHAR(256), IN a_email VARCHAR(256), IN a_tel VARCHAR(256), IN a_role VARCHAR(256))

BEGIN

    DECLARE v_siteId INTEGER DEFAULT -1;
    DECLARE v_contactId INTEGER DEFAULT -1;
    DECLARE v_contactSiteId INTEGER DEFAULT -1;

    DECLARE no_more_rows BOOLEAN DEFAULT FALSE;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows=TRUE;

    SELECT id INTO v_siteId FROM site where lower(sitename) = lower(a_sitename) and infrast_id in (SELECT id FROM infrastructure where lower(infrastname) = lower(a_infrastructure));
    IF NOT no_more_rows THEN
        SET v_contactId = get_contact_id(a_certdn);
        IF ( v_contactId = -1 ) THEN
    	    INSERT INTO contact(dn, name, email, telephone) VALUES (a_certdn, a_name, a_email, a_tel);
    	    SET v_contactId=LAST_INSERT_ID();    	    
    	ELSE
    		UPDATE contact SET name=a_name, email=a_email, telephone=a_tel WHERE id=v_contactId;
    	END IF;

        SET v_contactSiteId = get_contact_site_id(v_siteId, v_contactId, a_role);
        IF ( v_contactSiteId = -1 ) THEN
    	    INSERT INTO contact_site(contact_id, site_id, role) VALUES (v_contactId, v_siteId, a_role);
    	END IF;
    END IF;
    SET no_more_rows = FALSE;

END$$

DELIMITER ;

-- -----------------------------------------
-- PROCEDURE: VOMS_CONTACTS_UPDATE
-- -----------------------------------------

DELIMITER $$

DROP PROCEDURE IF EXISTS `VOMS_CONTACTS_UPDATE`$$
CREATE PROCEDURE `VOMS_CONTACTS_UPDATE` (IN a_voname VARCHAR(256), IN a_certdn VARCHAR(256), IN a_email VARCHAR(256))

BEGIN

    DECLARE v_voId INTEGER DEFAULT -1;
    DECLARE v_contactId INTEGER DEFAULT -1;
    DECLARE v_contactVoId INTEGER DEFAULT -1;

    DECLARE no_more_rows BOOLEAN DEFAULT FALSE;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows=TRUE;

    SELECT id INTO v_voId FROM vo where lower(voname) = lower(a_voname);
    IF NOT no_more_rows THEN
        SET v_contactId = get_contact_id(a_certdn);
        IF ( v_contactId = -1 ) THEN
    	    INSERT INTO contact(dn, email) VALUES (a_certdn, a_email);
    	    SET v_contactId=LAST_INSERT_ID();
    	ELSE
    		UPDATE contact SET email=a_email WHERE id=v_contactId;
    	END IF;

        SET v_contactVoId = get_contact_vo_id(v_voId, v_contactId);
        IF ( v_contactVoId = -1 ) THEN
    	    INSERT INTO contact_vo(contact_id, vo_id) VALUES (v_contactId, v_voId);
    	END IF;
    END IF;
    SET no_more_rows = FALSE;
            
END$$

DELIMITER ;


-- -------------------------------------------
-- Procedure:MARK_VO_SERVICE_GROUPS_AS_DELETED
-- --------------------------------------------
DELIMITER $$

DROP PROCEDURE IF EXISTS `MARK_VO_SERVICE_GROUPS_AS_DELETED`$$
CREATE PROCEDURE `MARK_VO_SERVICE_GROUPS_AS_DELETED`(
  IN a_voservicegroupsId INTEGER)

BEGIN

        UPDATE vo_service_group SET isdeleted='Y' WHERE id=a_voservicegroupsId;
END$$

DELIMITER ;


-- -------------------------------------------
-- Procedure: VO_GROUP_LINKS
-- -------------------------------------------
DELIMITER $$

DROP PROCEDURE IF EXISTS `VO_GROUP_LINKS`$$

CREATE PROCEDURE VO_GROUP_LINKS (IN a_atp_site VARCHAR(256), IN a_grouptier VARCHAR(256), IN a_groupsite VARCHAR(256), IN a_voname VARCHAR(256), INOUT sucess_flag TINYINT)

BEGIN

    DECLARE v_grouptierId INTEGER DEFAULT -1;
    DECLARE v_groupsiteId INTEGER DEFAULT -1;
    DECLARE v_id INTEGER DEFAULT -1;

    DECLARE no_more_rows BOOLEAN DEFAULT FALSE;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows=TRUE;
    
    SET sucess_flag=0;

    SELECT gr.id INTO v_grouptierId
    FROM groups gr, group_type gt, vo vo, vo_group vg
    WHERE gr.groupname = a_grouptier
    AND gt.typename LIKE '%_Tier'
    AND vo.voname = a_voname
    AND gr.group_type_id = gt.id
    AND vg.groups_id = gr.id
    AND vg.vo_id = vo.id;

    SELECT gr.id INTO v_groupsiteId
    FROM groups gr, group_type gt, vo vo, vo_group vg
    WHERE gr.groupname = a_groupsite
    AND gt.typename LIKE '%_Site'
    AND vo.voname = a_voname
    AND gr.group_type_id = gt.id
    AND vg.groups_id = gr.id
    AND vg.vo_id = vo.id;

    IF NOT no_more_rows THEN
        SET v_id = get_group_link(v_groupsiteId);
        IF v_id = -1 THEN
            INSERT INTO group_link(groups_id_site, groups_id_tier) VALUES (v_groupsiteId, v_grouptierId);
        ELSE
            UPDATE group_link SET groups_id_tier = v_grouptierId WHERE groups_id_site = v_groupsiteId;
        END IF;
    END IF;  
    SET no_more_rows = FALSE;  
END$$

DELIMITER ;
