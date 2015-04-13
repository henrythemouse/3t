#################
# There are 3 required tables that must be present.
# Essentially these are special purpose support tables.
# As such they can be InnoDB tables, they are never searched.
# Replace XXXXXXXXXXXXX with the database name


#################
# First create a DB

CREATE DATABASE IF NOT EXISTS XXXXXXXXXXXX
DEFAULT CHARACTER SET = utf8
DEFAULT COLLATE = utf8_unicode_ci


#################
# Create the tables

# 1 stores the configuration variables.
# This table will be automatically populated by starting the script.

CREATE TABLE `_config` (
  `_id` tinyint(1) unsigned NOT NULL DEFAULT '1',
  `dbname` varchar(45) NOT NULL COMMENT '## Name of the mysql database (no default).',
  `displayname` varchar(45) DEFAULT NULL COMMENT '## Text to print on top of the logo image (default=dbname).',
  `displaynamelocation` enum('TOP','MIDDLE','BOTTOM') NOT NULL DEFAULT 'MIDDLE' COMMENT '## Location for the displayname (default=MIDDLE).',
  `displaylogo` varchar(45) DEFAULT NULL COMMENT '## Image to use as your logo, located in path2serverRoot/3t/images/dbname/ (default provided).',
  `popupbackground` varchar(45) DEFAULT NULL COMMENT '## Image to use as the popup background (default=displaylogo).',
  `emailcontact` varchar(45) DEFAULT NULL COMMENT '## Email contact address (default=root@localhost).',
  `selectedHost` varchar(45) DEFAULT NULL COMMENT '## Hostname for the mysql server (default=localhost).',
  `catColumn` varchar(45) DEFAULT NULL COMMENT '## Category table column containg the category names (no default).',
  `catSortColumn` varchar(45) DEFAULT NULL COMMENT '## Category table column to sort results by (default=the id column)',
  `itemListColumns` varchar(45) DEFAULT NULL COMMENT '## Item table column names that will uniquely identify an item (default=first 2 char columns).',
  `itemColumns` varchar(45) DEFAULT NULL COMMENT '## Item table column names that will comprise the All_Items table (default=first 4 char columns).',
  `catSearchColumns` varchar(45) DEFAULT NULL COMMENT '## Category table column names you want included in search results (default=None).',
  `lastupdate` enum('YES','NO') NOT NULL DEFAULT 'NO' COMMENT '## On startup, display the last record entered (YES will enable, NO to disable).',
  `theme` varchar(45) DEFAULT 'default' COMMENT '## Theme files are css files located in the style directory (default=default)',
  PRIMARY KEY (`_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


# 2 stores the category names and images used in the UI.
# This table will need to have data inserted, defaults are provided.

CREATE TABLE `_category` (
  `_id` tinyint(2) unsigned zerofill NOT NULL AUTO_INCREMENT,
  `category` varchar(45) NOT NULL,
  `image` mediumblob NOT NULL,
  `filename` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


# 3 stores cache data for each browser connection.
# This table will be automatically populated by starting the script.

CREATE TABLE `_kooky` (
  `_kookyID` bigint(20) unsigned NOT NULL DEFAULT '0',
  `modstamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `remoteHost` varchar(100) DEFAULT NULL,
  `kookyData` mediumtext,
  PRIMARY KEY (`_kookyID`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
