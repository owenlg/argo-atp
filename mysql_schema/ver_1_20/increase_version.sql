-- ----------------------------------------------------------------------------
--
-- NAME:        db_schema_version.sql
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
-- CREATED:     07-Dec-2010
--
-- NOTES:
--
-- MODIFIED: 12-Apr-2011   
--
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS schema_details (
     id INT AUTO_INCREMENT NOT NULL,
     ver VARCHAR(20) NOT NULL,
     db_name VARCHAR(200),
     creation_date DATETIME NOT NULL,
     remarks VARCHAR(1000) BINARY NULL,
     PRIMARY KEY (id),
     CONSTRAINT `uk_schema_details`
          UNIQUE KEY (`ver`, `db_name`)
) ENGINE=INNODB;

-- Schema Version
INSERT INTO schema_details(ver,creation_date,remarks,db_name) VALUES('1.20',NOW(),"Version 1.20 of the schema","atp");
