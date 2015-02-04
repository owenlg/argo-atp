-- ----------------------------------------------------------------------------
--
-- NAME:        drop_scheduler_event.sql
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
--         MySQL ATP DB scheduler events
--
-- AUTHORS:     David Collados, CERN
--              Joshi Pradyumna, BARC
--
-- CREATED:     23-Nov-2009
--
-- NOTES:
--
-- MODIFIED:
--
-- ----------------------------------------------------------------------------

SET GLOBAL event_scheduler = 1;

DROP EVENT IF EXISTS `REMOVE_SERVICES_AND_SITES_EVENT`;

