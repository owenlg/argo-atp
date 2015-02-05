-- ----------------------------------------------------------------------------
--
-- NAME:        create_functions.sql
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
--         MySQL ATP DB functions
--
-- AUTHORS:     David Collados, CERN
--              Joshi Pradyumna, BARC
--
-- CREATED:     23-Nov-2009
--
-- NOTES:
--
-- MODIFIED: 10-Dec-2010
--
-- ----------------------------------------------------------------------------

-- -------------------------
-- Function: GET_COUNTRY_ID
-- ---------------------------

DELIMITER $$

DROP FUNCTION IF EXISTS `get_country_id` $$
CREATE FUNCTION `get_country_id`(a_country_name VARCHAR(50)) RETURNS int(11)
    DETERMINISTIC
BEGIN

  DECLARE v_countryId INTEGER;
  DECLARE v_nullcountryId INTEGER DEFAULT 1;
  DECLARE no_more_rows BOOLEAN DEFAULT FALSE;
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows = TRUE;

  IF a_country_name='' THEN
    SELECT id INTO v_countryId
    FROM country
    WHERE lower(countryname) = 'unknown';

    IF no_more_rows THEN
      RETURN -1;
    ELSE
      RETURN v_countryId;
    END IF;
  ELSE
    SELECT id INTO v_countryId
    FROM country
    WHERE lower(countryabbr)=lower(a_country_name);

    IF no_more_rows THEN
      SET no_more_rows = FALSE;

      SELECT id INTO v_countryId
      FROM country
      WHERE lower(countryname)=lower(a_country_name);

      IF no_more_rows THEN
        SET no_more_rows = FALSE;

        SELECT IFNULL(MIN(id),v_nullcountryId) INTO v_countryId
        FROM country
        WHERE lower(countryname) LIKE concat('%', lower(a_country_name), '%');

        IF no_more_rows THEN
          SET no_more_rows = FALSE;

          SELECT id INTO v_countryId
          FROM country
          WHERE lower(countryname) = 'unknown';

          IF no_more_rows THEN
            RETURN -1;
          ELSE
            RETURN v_countryId;
          END IF;
        ELSE
          RETURN v_countryId;
        END IF;
      ELSE
        RETURN v_countryId;
      END IF;
    ELSE
      RETURN v_countryId;
    END IF;
  END IF;
END $$

DELIMITER ;

-- ----------------------------
-- Function: GET_SYNCHRONIZER_ID
-- ---------------------------

DELIMITER $$

DROP FUNCTION IF EXISTS `get_synchronizer_id` $$
CREATE FUNCTION `get_synchronizer_id`(a_synchronizer_name VARCHAR(100)) RETURNS int(11)

BEGIN
  DECLARE v_synchronizer_id INTEGER;
  DECLARE EXIT HANDLER FOR NOT FOUND RETURN -1;
  -- Returns the ID of synchronizer specified in the parameter

  SELECT id INTO v_synchronizer_id
  FROM synchronizer
  WHERE lower(name) = lower(a_synchronizer_name);

  RETURN v_synchronizer_id;

END $$

DELIMITER ;


-- -------------------------
-- Function: GET_GROUP_TYPE_ID
-- ---------------------------

DELIMITER $$

DROP FUNCTION IF EXISTS `get_group_type_id` $$
CREATE FUNCTION `get_group_type_id`(a_typename VARCHAR(100)) RETURNS int(11)
    DETERMINISTIC
BEGIN
  DECLARE v_groupTypeId INTEGER;
  DECLARE EXIT HANDLER FOR NOT FOUND RETURN -1;

  -- Get the group type id
  SELECT id INTO v_groupTypeId
  FROM group_type
  WHERE typename=a_typename;

  RETURN v_groupTypeId;
END $$

DELIMITER ;

-- -------------------------
-- Function: GET_GROUP_ID
-- ---------------------------

DELIMITER $$

DROP FUNCTION IF EXISTS `get_group_id` $$
CREATE FUNCTION `get_group_id`(a_groupname VARCHAR(100), a_typename VARCHAR(100)) RETURNS int(11)
    DETERMINISTIC
BEGIN

  DECLARE v_group_id INT DEFAULT -1;
  DECLARE EXIT HANDLER FOR NOT FOUND RETURN -1;

  -- Get the groups id
  SELECT a.id INTO v_group_id
  FROM groups a, group_type b
  WHERE lower(a.groupname)=lower(a_groupname)
    AND lower(b.typename)=lower(a_typename)
    AND a.group_type_id=b.id;

  RETURN v_group_id;
END $$

DELIMITER ;

-- -------------------------------
-- Function: GET_INFRASTRUCTURE_ID
-- -------------------------------

DELIMITER $$

DROP FUNCTION IF EXISTS `get_infrastructure_id` $$
CREATE FUNCTION `get_infrastructure_id`(a_infrast_name VARCHAR(256)) RETURNS int(11)
    DETERMINISTIC
BEGIN

  DECLARE v_infrast_id INT;
  DECLARE EXIT HANDLER FOR NOT FOUND RETURN -1;

  -- Get infrastructure id
  SELECT id INTO v_infrast_id
  FROM infrastructure
  WHERE lower(infrastname)=lower(a_infrast_name);

  RETURN v_infrast_id;
END $$

DELIMITER ;

-- --------------------------------
-- Function: GET_SERVICE_FLAVOUR_ID
-- --------------------------------

DELIMITER $$

DROP FUNCTION IF EXISTS `get_service_flavour_id` $$
CREATE FUNCTION `get_service_flavour_id`(a_service_flavour VARCHAR(128)) RETURNS int(11)
    DETERMINISTIC
BEGIN

  DECLARE v_service_flavour_id INT;
  DECLARE EXIT HANDLER FOR NOT FOUND RETURN -1;

  -- Get the service flavour id
  SELECT id INTO v_service_flavour_id
  FROM service_type_flavour
  WHERE lower(flavourname)=lower(a_service_flavour);

  RETURN v_service_flavour_id;
END $$

DELIMITER ;


-- -------------------------
-- Function: GET_SERVICE_ID
-- ---------------------------

DELIMITER $$

DROP FUNCTION IF EXISTS `get_service_id` $$
CREATE FUNCTION `get_service_id`(a_hostname VARCHAR(512), a_service_flavour_id INTEGER) RETURNS int(11)
BEGIN

  DECLARE v_service_id INTEGER;
  DECLARE EXIT HANDLER FOR NOT FOUND RETURN -1;

  SELECT id INTO v_service_id
  FROM service
  WHERE lower(hostname)=lower(a_hostname)
    AND flavour_id=a_service_flavour_id;

  RETURN v_service_id;
END $$

DELIMITER ;


-- -------------------------
-- Function: GET_SITE_ID
-- ---------------------------

DELIMITER $$

DROP FUNCTION IF EXISTS `get_site_id` $$
CREATE FUNCTION `get_site_id`(a_site_name VARCHAR(100), a_infrast_id INTEGER) RETURNS int(11)
    DETERMINISTIC
BEGIN

  DECLARE v_site_id INT;
  DECLARE EXIT HANDLER FOR NOT FOUND RETURN -1;

  -- Get the site id
  SELECT id INTO v_site_id
  FROM site
  WHERE lower(sitename)=lower(a_site_name)
    AND infrast_id=a_infrast_id;

  RETURN v_site_id;
END $$

DELIMITER ;

-- -------------------------
-- Function: GET_VO_ID
-- ---------------------------

DELIMITER $$

DROP FUNCTION IF EXISTS `get_vo_id` $$
CREATE FUNCTION `get_vo_id`(a_voname VARCHAR(100)) RETURNS int(11)
BEGIN

  DECLARE v_voId INTEGER;
  DECLARE EXIT HANDLER FOR NOT FOUND RETURN -1;

  SELECT id INTO v_voId
  FROM vo
  WHERE lower(voname)=lower(a_voname);

  RETURN v_voId;
END $$

DELIMITER ;

-- -------------------------
-- Function: GET_ROC_NAME
-- ---------------------------

DELIMITER $$

DROP FUNCTION IF EXISTS `get_roc_name` $$
CREATE FUNCTION `get_roc_name`(a_service_id INT(11)) RETURNS varchar(200)
BEGIN

  DECLARE v_ROC_name VARCHAR(200);
  DECLARE v_site_Id INT(11);

  DECLARE EXIT HANDLER FOR NOT FOUND RETURN '';

  -- get site id
  SELECT site_id INTO v_site_Id
  FROM service_site
  WHERE service_id=a_service_id;

-- get ROC name
  SELECT b.groupname INTO v_ROC_name FROM site_group a,groups b
  WHERE a.site_id=v_site_Id AND a.groups_id=b.id
  AND a.groups_id IN
     (SELECT id FROM groups WHERE group_type_id IN
       (SELECT id FROM group_type WHERE lower(typename)=lower('region')
       )
     );

  RETURN v_ROC_name;
END $$

DELIMITER ;

-- -------------------------
-- Function: GET_SITENAME
-- ---------------------------

DELIMITER $$

DROP FUNCTION IF EXISTS `get_sitename` $$
CREATE FUNCTION `get_sitename`(serv_Id INT(11)) RETURNS VARCHAR(100)

BEGIN

  DECLARE v_siteId INT(11) DEFAULT -1;
  DECLARE v_sitename VARCHAR(100) DEFAULT NULL;
  DECLARE no_more_rows BOOLEAN DEFAULT FALSE;

  DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows = TRUE;

   -- find site id for the given service id
   SELECT site_id INTO v_siteId FROM service_site WHERE service_id=serv_Id;

   IF no_more_rows THEN
    -- if no site associated with a given service id
      RETURN v_sitename;
   ELSE
    SELECT sitename INTO v_sitename FROM site WHERE id=v_siteId;
    RETURN v_sitename;
   END IF;
END $$

DELIMITER ;


-- -------------------------------
-- Function: GET_SITE_GROUP_ID
-- -------------------------------

DELIMITER $$

DROP FUNCTION IF EXISTS `get_site_group_id`$$
CREATE FUNCTION `get_site_group_id`(a_siteId INTEGER) RETURNS int(11)
BEGIN

  DECLARE v_site_group_id INT(11) DEFAULT -1;
  DECLARE EXIT HANDLER FOR NOT FOUND RETURN -1;

  SELECT id INTO v_site_group_id
  FROM site_group
  WHERE site_id=a_siteId
    AND groups_id in (select id from groups where group_type_id in(select id from group_type where lower(typename)='region'));

  RETURN v_site_group_id;
END$$

DELIMITER ;

-- -------------------------------
-- Function: GET_SERVICE_GROUP_ID
-- -------------------------------

DELIMITER $$

DROP FUNCTION IF EXISTS `get_service_group_id`$$
CREATE FUNCTION `get_service_group_id`(a_serviceId INTEGER, a_groupId INTEGER) RETURNS int(11)
BEGIN

  DECLARE v_service_group_id INT(11) DEFAULT -1;
  DECLARE EXIT HANDLER FOR NOT FOUND RETURN -1;

  SELECT id INTO v_service_group_id
  FROM service_group
  WHERE service_id=a_serviceId
    AND groups_id=a_groupId;

  RETURN v_service_group_id;
END$$

DELIMITER ;

-- --------------------------------------
-- Function: GET_SITE_REGION_GROUP_ID
-- --------------------------------------

DELIMITER $$

DROP FUNCTION IF EXISTS `get_site_region_group_id`$$
CREATE FUNCTION `get_site_region_group_id`(a_siteId INTEGER,a_curgroupId INTEGER) RETURNS int(11)
BEGIN

  DECLARE v_total_groups            INT(11) DEFAULT 0;
  DECLARE v_site_region_group_id INT(11) DEFAULT -1;
  DECLARE v_siteId                  INTEGER;
  DECLARE v_groupId              INTEGER;

  DECLARE no_more_rows BOOLEAN DEFAULT FALSE;
  DECLARE region_cursor CURSOR FOR
    SELECT site_id, groups_id
    FROM site_group
    WHERE site_id=a_siteId
      AND groups_id IN (SELECT id
                          FROM groups
                          WHERE group_type_id IN (SELECT id
                                                  FROM group_type
                                                  WHERE lower(typename)='region'
                                                 )
                         );
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows = TRUE;


  SELECT count(*) INTO v_total_groups
  FROM site_group
  WHERE site_id=a_siteId
    AND groups_id IN (SELECT id
                        FROM groups
                        WHERE group_type_id IN (SELECT id
                                                FROM group_type
                                                WHERE lower(typename)='region'
                                                )
                       );

  IF no_more_rows THEN
    RETURN -1;
  ELSE
    IF v_total_groups > 1 THEN
      BEGIN
       
        OPEN region_cursor;
        regions_loop: LOOP
          FETCH region_cursor INTO v_siteId,v_groupId;
          IF no_more_rows THEN
            CLOSE region_cursor;
            LEAVE regions_loop;
          END IF;
          IF v_groupId != a_curgroupId THEN
              DELETE FROM site_group
              WHERE site_id = v_siteId
                AND groups_id = v_groupId;
          ELSE
        SET v_site_region_group_id = v_groupId;
          END IF;
          SET no_more_rows = FALSE;
        END LOOP regions_loop;

        RETURN v_site_region_group_id;
      END;
    ELSE
      BEGIN
        SELECT groups_id INTO v_site_region_group_id
        FROM site_group
        WHERE site_id=a_siteId
          AND groups_id IN (SELECT id
                              FROM groups
                              WHERE group_type_id IN (SELECT id
                                                      FROM group_type
                                                      WHERE lower(typename)='region'
                                                      )
                             );

        IF no_more_rows THEN
          RETURN -1;
        ELSE
          RETURN v_site_region_group_id;
        END IF;
      END;
    END IF;
  END IF;
END$$

DELIMITER ;

-- --------------------------------------
-- Function: GET_VO_SERVICE_GROUP_ID
-- --------------------------------------

DELIMITER $$

DROP FUNCTION IF EXISTS `get_vo_service_group_id`$$
CREATE FUNCTION `get_vo_service_group_id`(a_voname VARCHAR(128), a_serviceId INTEGER, a_groupId INTEGER) RETURNS int(11)
BEGIN

  DECLARE v_vo_service_group_id INT(11) DEFAULT -1;
  DECLARE v_voId INTEGER DEFAULT -1;
  DECLARE EXIT HANDLER FOR NOT FOUND RETURN -1;
 
  -- VO
  SET v_voId = get_vo_id(a_voname);
  IF (v_voId > -1) THEN
      SELECT id INTO v_vo_service_group_id
      FROM vo_service_group
      WHERE vo_id=v_voId
        AND service_id=a_serviceId
        AND groups_id=a_groupId;
  END IF;
  RETURN v_vo_service_group_id;
END$$

DELIMITER ;

-- --------------------------------------
-- Function: GET_VO_SITE_GROUP_ID
-- --------------------------------------
DELIMITER $$

DROP FUNCTION IF EXISTS `get_vo_site_group_id`$$
CREATE FUNCTION `get_vo_site_group_id`(a_voname VARCHAR(128), a_siteId INTEGER, a_groupId INTEGER) RETURNS int(11)
BEGIN

  DECLARE v_vo_site_group_id INT(11) DEFAULT -1;
  DECLARE v_voId INTEGER DEFAULT -1;
  DECLARE EXIT HANDLER FOR NOT FOUND RETURN -1;
 
  -- VO
  SET v_voId = get_vo_id(a_voname);
  IF (v_voId > -1) THEN
      SELECT id INTO v_vo_site_group_id
      FROM vo_site_group
      WHERE vo_id=v_voId
        AND site_id=a_siteId
        AND groups_id=a_groupId;
  END IF;
  RETURN v_vo_site_group_id;
END$$

DELIMITER ;

-- -----------------------------------------------
-- Function: GET_SYNCHRONIZER_LASTUPDATE_STATUS
-- ---------------------------------------------

DELIMITER $$

DROP FUNCTION IF EXISTS `get_synchronizer_lastupdate_status`$$
CREATE FUNCTION `get_synchronizer_lastupdate_status`(a_synchronizer_name VARCHAR(100)) RETURNS int(11)
BEGIN
  DECLARE v_synchronizer_id INTEGER DEFAULT -1;
  DECLARE v_syncId INTEGER;
  DECLARE EXIT HANDLER FOR NOT FOUND RETURN -1;
 -- get synchronizer Id
  SET v_syncId = get_synchronizer_id(a_synchronizer_name);  
 
  SELECT id INTO v_synchronizer_id
  FROM synchronizer_lastrun
  WHERE synchronizer_id=v_syncid;

  RETURN v_synchronizer_id;

END$$

DELIMITER ;

-- --------------------------------
-- Function: GET_SITE_LAST_SEEN_ID
-- ---------------------------------
DELIMITER $$

DROP FUNCTION IF EXISTS `get_site_lastseen_id`$$

CREATE FUNCTION get_site_lastseen_id (a_siteId INT, a_synchronizerId INT ) RETURNS int(11)

BEGIN 

DECLARE v_site_lastseen_id INT;
DECLARE EXIT HANDLER FOR NOT FOUND RETURN -1;
/**
 * Returns the ID of the site_lastseen table that correspond to the siteId and
 * synchronizerId passed in the parameters
 */
    SELECT id INTO v_site_lastseen_id
    FROM site_last_seen
    WHERE site_id=a_siteId
      AND synchronizer_id=a_synchronizerId;

    RETURN v_site_lastseen_id;

END$$

DELIMITER ;

-- --------------------------------
-- Function: GET_SERVICE_LAST_SEEN_ID
-- ---------------------------------
DELIMITER $$

DROP FUNCTION IF EXISTS `get_service_lastseen_id`$$

CREATE FUNCTION get_service_lastseen_id (a_serviceId INT, a_synchronizerId INT ) RETURNS int(11)

BEGIN 

DECLARE v_service_lastseen_id INT;
DECLARE EXIT HANDLER FOR NOT FOUND RETURN -1;
/**
 * Returns the ID of the service_lastseen table that correspond to the serviceId and
 * synchronizerId passed in the parameters
 */
    SELECT id INTO v_service_lastseen_id
    FROM service_last_seen
    WHERE service_id=a_serviceId
      AND synchronizer_id=a_synchronizerId;

    RETURN v_service_lastseen_id;

END$$

DELIMITER ;

-- ------------------------
-- FUNCTION:get_vo_group_id
-- ------------------------
DELIMITER $$

DROP FUNCTION IF EXISTS `get_vo_group_id`$$
CREATE FUNCTION `get_vo_group_id`(a_voId INTEGER,a_groupId INTEGER) RETURNS int(11)
    DETERMINISTIC
BEGIN

  DECLARE v_vogroup_id INT DEFAULT -1;
  DECLARE EXIT HANDLER FOR NOT FOUND RETURN -1;

  
  SELECT id INTO v_vogroup_id
  FROM vo_group
  WHERE vo_id=a_voId AND groups_id=a_groupId;

  RETURN v_vogroup_id;
END$$

DELIMITER ;

-- -------------------------------
-- Function:get_gocdb_downtime_id
-- ------------------------------
DELIMITER $$

DROP FUNCTION IF EXISTS `get_gocdb_downtime_id`$$
CREATE FUNCTION `get_gocdb_downtime_id`(a_gocdbpk VARCHAR(128)) RETURNS INTEGER
BEGIN

  DECLARE v_id INTEGER DEFAULT -1;
  DECLARE EXIT HANDLER FOR NOT FOUND RETURN -1;

  
  SELECT id INTO v_id
  FROM downtime
  WHERE lower(gocdbpk)=lower(TRIM(a_gocdbpk));

  RETURN v_id;
END$$

DELIMITER ;


-- -------------------------
-- Function: GET_REGION
-- ---------------------------

DELIMITER $$

DROP FUNCTION IF EXISTS `get_region`$$
CREATE FUNCTION `get_region`(a_virtual_sitename VARCHAR(100), a_voname VARCHAR(128)) RETURNS varchar(128) CHARSET latin1
   
BEGIN

  DECLARE v_groupsId INT DEFAULT -1;
  DECLARE v_voId INT DEFAULT -1;
  DECLARE v_vo_service_groupId INT DEFAULT -1;
  DECLARE v_serviceId INT DEFAULT -1; 
  DECLARE v_rocName VARCHAR(128) DEFAULT NULL;
-- FALSE
  DECLARE no_more_rows BOOLEAN DEFAULT TRUE;   
  DECLARE servicecur_vos CURSOR FOR
	 SELECT service_id FROM vo_service_group WHERE vo_id=v_voId AND groups_id=v_groupsId AND isdeleted='N';
 
  DECLARE servicecur_ops CURSOR FOR
	 SELECT service_id FROM service_group WHERE groups_id=v_groupsId AND isdeleted='N';
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET no_more_rows = TRUE;
  -- VO Id
  SET v_voId = get_vo_id(a_voname);
  -- groups Id
  SELECT id INTO v_groupsId 
  FROM groups
  WHERE lower(groupname) = lower(a_virtual_sitename);
  -- Service Id
  -- check if vo is 'OPS' or not
  IF lower(a_voname)!= lower('ops') THEN
  	-- VOs other than 'OPS'
	OPEN servicecur_vos;
	services_loop: LOOP
    	FETCH servicecur_vos INTO v_serviceId;
	 
    	IF no_more_rows THEN
      		CLOSE servicecur_vos;
      		LEAVE services_loop;
    	END IF;
	END LOOP services_loop; 

--        SELECT service_id INTO v_serviceId
--  	FROM vo_service_group
--  	WHERE vo_id=v_voId AND group_id=v_groupsId;
  ELSE
	-- 'OPS' vo
	OPEN servicecur_ops;
	services_loop: LOOP
    	FETCH servicecur_ops INTO v_serviceId;
	 
    	IF no_more_rows THEN
      		CLOSE servicecur_ops;
      		LEAVE services_loop;
    	END IF;
	END LOOP services_loop; 
--	SELECT service_id INTO v_serviceId
--  	FROM service_group
--  	WHERE group_id=v_groupsId AND isdeleted='N' limit 1;

  END IF;
  -- roc name
  SET v_rocName = get_roc_name(v_serviceId);
  RETURN v_rocName;
END$$

DELIMITER ;


-- -------------------------
-- Function: GET_TIER
-- ---------------------------

DELIMITER $$

DROP FUNCTION IF EXISTS `get_tier`$$
CREATE FUNCTION `get_tier`(a_sitename VARCHAR(100), a_voname VARCHAR(128)) RETURNS varchar(128) CHARSET latin1
    
BEGIN

  DECLARE v_groupsId INT DEFAULT -1;
  DECLARE v_Tier VARCHAR(128) DEFAULT NULL;
  
  DECLARE EXIT HANDLER FOR NOT FOUND RETURN NULL;   

  IF nls_lower(a_voname) = nls_lower('atlas')
    OR nls_lower(a_voname) = nls_lower('alice')
    OR nls_lower(a_voname) = nls_lower('cms')
    OR nls_lower(a_voname) = nls_lower('lhcb')
    OR nls_lower(a_voname) = nls_lower('superbvo.org')
  THEN 
    -- get groupid for site
    SELECT gr.id INTO v_groupsId 
    FROM groups gr, vo_group vg 
    WHERE gr.id = vg.groups_id
    AND gr.groupname = a_sitename
    AND vg.vo_id in (SELECT id FROM vo WHERE voname = a_voname)
    AND group_type_id in (SELECT id FROM group_type WHERE typename LIKE '%Site')
    AND gr.isdeleted = 'N';
    
    -- get groupname for tier
    SELECT groupname INTO v_Tier
    FROM groups 
    WHERE id in (SELECT groups_id_tier FROM group_link WHERE groups_id_site = v_groupsId); 

  ELSE
    SELECT gr.groupname INTO v_Tier
    FROM groups gr, site si, site_group sg, group_type gt
    WHERE gr.id = sg.groups_id
    AND si.id = sg.site_id
    AND gt.id = gr.group_type_id
    AND gt.typename LIKE '%Tier'
    AND si.id in (SELECT id FROM site WHERE sitename = a_sitename)
    AND gr.isdeleted = 'N'
    AND si.isdeleted = 'N';
    
  END IF;

  RETURN v_Tier;

END$$

DELIMITER ;


-- --------------------------------
-- Function: GET_SERVICE_TYPE_ID
-- --------------------------------

DELIMITER $$

DROP FUNCTION IF EXISTS `get_service_type_id` $$
CREATE FUNCTION `get_service_type_id`(a_service_type VARCHAR(128)) RETURNS int(11)
    DETERMINISTIC
BEGIN

  DECLARE v_service_type_id INT;
  DECLARE EXIT HANDLER FOR NOT FOUND RETURN -1;

  -- Get the service type id
  SELECT id INTO v_service_type_id
  FROM service_type
  WHERE lower(servicename)=lower(a_service_type);

  RETURN v_service_type_id;
END $$

DELIMITER ;


-- --------------------------------
-- Function: get_contact_id
-- --------------------------------

DELIMITER $$

DROP FUNCTION IF EXISTS `get_contact_id` $$
CREATE FUNCTION `get_contact_id`(a_certdn VARCHAR(256)) RETURNS int(11)
    DETERMINISTIC
BEGIN

  DECLARE v_contactId INT;
  DECLARE EXIT HANDLER FOR NOT FOUND RETURN -1;

  SELECT id INTO v_contactId
  FROM contact
  WHERE lower(dn)=lower(a_certdn);

  RETURN v_contactId;
END $$

DELIMITER ;


-- --------------------------------
-- Function: get_contact_group_id
-- --------------------------------

DELIMITER $$

DROP FUNCTION IF EXISTS `get_contact_group_id` $$
CREATE FUNCTION `get_contact_group_id`(a_rocId INTEGER, a_contactId INTEGER, a_role VARCHAR(256)) RETURNS int(11)
    DETERMINISTIC
BEGIN

  DECLARE v_contactGroupId INT;
  DECLARE EXIT HANDLER FOR NOT FOUND RETURN -1;

  SELECT id INTO v_contactGroupId
  FROM contact_group
  WHERE lower(groups_id)=lower(a_rocId) and lower(contact_id)=lower(a_contactId) and lower(role)=lower(a_role);

  RETURN v_contactGroupId;
END $$

DELIMITER ;


-- --------------------------------
-- Function: get_contact_site_id
-- --------------------------------

DELIMITER $$

DROP FUNCTION IF EXISTS `get_contact_site_id` $$
CREATE FUNCTION `get_contact_site_id`(a_siteId INTEGER, a_contactId INTEGER, a_role VARCHAR(256)) RETURNS int(11)
    DETERMINISTIC
BEGIN

  DECLARE v_contactSiteId INT;
  DECLARE EXIT HANDLER FOR NOT FOUND RETURN -1;

  SELECT id INTO v_contactSiteId
  FROM contact_site
  WHERE lower(site_id)=lower(a_siteId) and lower(contact_id)=lower(a_contactId) and lower(role)=lower(a_role);

  RETURN v_contactSiteId;
END $$

DELIMITER ;

-- --------------------------------
-- Function: get_contact_vo_id
-- --------------------------------

DELIMITER $$

DROP FUNCTION IF EXISTS `get_contact_vo_id` $$
CREATE FUNCTION `get_contact_vo_id`(a_voId INTEGER, a_contactId INTEGER) RETURNS int(11)
    DETERMINISTIC
BEGIN

  DECLARE v_contactVoId INT;
  DECLARE EXIT HANDLER FOR NOT FOUND RETURN -1;

  SELECT id INTO v_contactVoId
  FROM contact_vo
  WHERE lower(vo_id)=lower(a_voId) and lower(contact_id)=lower(a_contactId);

  RETURN v_contactVoId;
END $$

DELIMITER ;


-- ----------------------
-- FUNCTION: GET_GROUP_LINK
-- ----------------------

DELIMITER $$

DROP FUNCTION IF EXISTS `get_group_link` $$
CREATE FUNCTION `get_group_link`(a_groupsite VARCHAR(256)) RETURNS INT(11)
    DETERMINISTIC
BEGIN

    DECLARE v_groupLinkId INT;
    DECLARE EXIT HANDLER FOR NOT FOUND RETURN -1;
  
    SELECT id INTO v_groupLinkId
    FROM group_link
    WHERE groups_id_site = a_groupsite;
   
    RETURN v_groupLinkId;
END $$

DELIMITER ;


-- ----------------------------
-- Function: GET_SITE_GROUP_ID2
-- ----------------------------

DELIMITER $$

DROP FUNCTION IF EXISTS `get_site_group_id2`$$
CREATE FUNCTION `get_site_group_id2`(a_siteId INTEGER, a_groupId INTEGER) RETURNS int(11)
BEGIN
    DECLARE v_site_group_id INT(11) DEFAULT -1;
    DECLARE EXIT HANDLER FOR NOT FOUND RETURN -1;

    SELECT id INTO v_site_group_id
    FROM site_group
    WHERE site_id=a_siteId AND groups_id=a_groupId;

    RETURN v_site_group_id;
END$$

DELIMITER ;

