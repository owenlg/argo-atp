create database mrs;

use mrs;
	
CREATE TABLE  IF NOT EXISTS schema_details (
	id INT AUTO_INCREMENT NOT NULL,
	ver VARCHAR(20) NOT NULL,
	db_name VARCHAR(200),
	creation_date DATETIME NOT NULL,
	remarks VARCHAR(1000) BINARY NULL,
	PRIMARY KEY (id) )
	ENGINE=INNODB;