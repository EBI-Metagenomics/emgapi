-- MySQL dump 10.13  Distrib 5.7.18, for macos10.12 (x86_64)

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `ANALYSIS_JOB`
--

DROP TABLE IF EXISTS `ANALYSIS_JOB`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ANALYSIS_JOB` (
  `JOB_ID` bigint(20) NOT NULL AUTO_INCREMENT,
  `JOB_OPERATOR` varchar(15) COLLATE utf8_unicode_ci NOT NULL,
  `PIPELINE_ID` tinyint(4) NOT NULL,
  `SUBMIT_TIME` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `COMPLETE_TIME` datetime DEFAULT NULL,
  `ANALYSIS_STATUS_ID` tinyint(4) NOT NULL,
  `RE_RUN_COUNT` tinyint(4) DEFAULT '0',
  `INPUT_FILE_NAME` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  `RESULT_DIRECTORY` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `EXTERNAL_RUN_IDS` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
  `SAMPLE_ID` int(11) DEFAULT NULL,
  `IS_PRODUCTION_RUN` bit(1) DEFAULT NULL,
  `EXPERIMENT_TYPE_ID` tinyint(4) DEFAULT NULL,
  `RUN_STATUS_ID` tinyint(4) DEFAULT NULL,
  `INSTRUMENT_PLATFORM` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `INSTRUMENT_MODEL` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`JOB_ID`),
  UNIQUE KEY `UC_ANALYSIS_JOB` (`PIPELINE_ID`,`EXTERNAL_RUN_IDS`),
  KEY `ANALYSIS_STATUS_ID` (`ANALYSIS_STATUS_ID`),
  KEY `SAMPLE_ID` (`SAMPLE_ID`),
  KEY `ANALYSIS_JOB_E_TYPE_ID_IDX` (`EXPERIMENT_TYPE_ID`),
  CONSTRAINT `ANALYSIS_JOB_ibfk_1` FOREIGN KEY (`PIPELINE_ID`) REFERENCES `PIPELINE_RELEASE` (`PIPELINE_ID`),
  CONSTRAINT `ANALYSIS_JOB_ibfk_2` FOREIGN KEY (`ANALYSIS_STATUS_ID`) REFERENCES `ANALYSIS_STATUS` (`ANALYSIS_STATUS_ID`),
  CONSTRAINT `ANALYSIS_JOB_ibfk_3` FOREIGN KEY (`EXPERIMENT_TYPE_ID`) REFERENCES `EXPERIMENT_TYPE` (`EXPERIMENT_TYPE_ID`),
  CONSTRAINT `ANALYSIS_JOB_ibfk_4` FOREIGN KEY (`SAMPLE_ID`) REFERENCES `SAMPLE` (`SAMPLE_ID`)
) ENGINE=InnoDB AUTO_INCREMENT=135105 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci COMMENT='Table to track all analysis runs in production.';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ANALYSIS_STATUS`
--

DROP TABLE IF EXISTS `ANALYSIS_STATUS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ANALYSIS_STATUS` (
  `ANALYSIS_STATUS_ID` tinyint(4) NOT NULL AUTO_INCREMENT,
  `ANALYSIS_STATUS` varchar(25) CHARACTER SET utf8 NOT NULL,
  PRIMARY KEY (`ANALYSIS_STATUS_ID`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `BIOME_HIERARCHY_TREE`
--

DROP TABLE IF EXISTS `BIOME_HIERARCHY_TREE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `BIOME_HIERARCHY_TREE` (
  `BIOME_ID` smallint(6) NOT NULL DEFAULT '0',
  `BIOME_NAME` varchar(60) COLLATE utf8_unicode_ci NOT NULL,
  `LFT` smallint(6) NOT NULL,
  `RGT` smallint(6) NOT NULL,
  `DEPTH` tinyint(4) NOT NULL,
  `LINEAGE` varchar(500) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`BIOME_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `BLACKLISTED_STUDY`
--

DROP TABLE IF EXISTS `BLACKLISTED_STUDY`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `BLACKLISTED_STUDY` (
  `EXT_STUDY_ID` varchar(18) COLLATE utf8_unicode_ci NOT NULL COMMENT 'This is the external unique (non-EMG) ID for the study, e.g. SRPXXXXXX for SRA studies',
  `ERROR_TYPE_ID` tinyint(4) NOT NULL COMMENT 'Foreign key to the study error type table.',
  `ANALYZER` varchar(15) COLLATE utf8_unicode_ci NOT NULL COMMENT 'Person who tried to analyse this study.',
  `PIPELINE_ID` tinyint(4) DEFAULT NULL COMMENT 'Optional. The pipeline version used to run this study.',
  `DATE_BLACKLISTED` date NOT NULL COMMENT 'The date when the study has been marked as blacklisted.',
  `COMMENT` text COLLATE utf8_unicode_ci COMMENT 'Use this field to add more detailed information about the issue.',
  PRIMARY KEY (`EXT_STUDY_ID`),
  KEY `ERROR_TYPE_ID` (`ERROR_TYPE_ID`),
  CONSTRAINT `BLACKLISTED_STUDY_ibfk_1` FOREIGN KEY (`ERROR_TYPE_ID`) REFERENCES `STUDY_ERROR_TYPE` (`ERROR_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `EXPERIMENT_TYPE`
--

DROP TABLE IF EXISTS `EXPERIMENT_TYPE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `EXPERIMENT_TYPE` (
  `EXPERIMENT_TYPE_ID` tinyint(4) NOT NULL AUTO_INCREMENT,
  `EXPERIMENT_TYPE` varchar(30) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`EXPERIMENT_TYPE_ID`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `GSC_CV_CV`
--

DROP TABLE IF EXISTS `GSC_CV_CV`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `GSC_CV_CV` (
  `VAR_NAME` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `VAR_VAL_CV` varchar(60) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
  PRIMARY KEY (`VAR_VAL_CV`),
  UNIQUE KEY `GSC_CV_CV_PK` (`VAR_VAL_CV`),
  UNIQUE KEY `GSC_CV_CV_U1` (`VAR_NAME`,`VAR_VAL_CV`),
  CONSTRAINT `GSC_CV_CV_ibfk_1` FOREIGN KEY (`VAR_NAME`) REFERENCES `VARIABLE_NAMES` (`VAR_NAME`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `PIPELINE_RELEASE`
--

DROP TABLE IF EXISTS `PIPELINE_RELEASE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `PIPELINE_RELEASE` (
  `PIPELINE_ID` tinyint(4) NOT NULL AUTO_INCREMENT,
  `DESCRIPTION` text COLLATE utf8_unicode_ci,
  `CHANGES` text COLLATE utf8_unicode_ci NOT NULL,
  `RELEASE_VERSION` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `RELEASE_DATE` date NOT NULL,
  PRIMARY KEY (`PIPELINE_ID`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `PIPELINE_RELEASE_TOOL`
--

DROP TABLE IF EXISTS `PIPELINE_RELEASE_TOOL`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `PIPELINE_RELEASE_TOOL` (
  `PIPELINE_ID` tinyint(4) NOT NULL,
  `TOOL_ID` smallint(6) NOT NULL,
  `TOOL_GROUP_ID` decimal(6,3) NOT NULL,
  `HOW_TOOL_USED_DESC` text COLLATE utf8_unicode_ci NOT NULL COMMENT 'Text description on how this version of the tool is used in this version of the pipeline.',
  PRIMARY KEY (`PIPELINE_ID`,`TOOL_ID`),
  UNIQUE KEY `pipeline_tool_group_uqidx` (`PIPELINE_ID`,`TOOL_GROUP_ID`),
  KEY `TOOL_ID` (`TOOL_ID`),
  CONSTRAINT `PIPELINE_RELEASE_TOOL_ibfk_1` FOREIGN KEY (`PIPELINE_ID`) REFERENCES `PIPELINE_RELEASE` (`PIPELINE_ID`),
  CONSTRAINT `PIPELINE_RELEASE_TOOL_ibfk_2` FOREIGN KEY (`TOOL_ID`) REFERENCES `PIPELINE_TOOL` (`TOOL_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `PIPELINE_TOOL`
--

DROP TABLE IF EXISTS `PIPELINE_TOOL`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `PIPELINE_TOOL` (
  `TOOL_ID` smallint(6) NOT NULL AUTO_INCREMENT,
  `TOOL_NAME` varchar(30) COLLATE utf8_unicode_ci NOT NULL,
  `DESCRIPTION` text COLLATE utf8_unicode_ci NOT NULL,
  `WEB_LINK` varchar(500) COLLATE utf8_unicode_ci DEFAULT NULL,
  `VERSION` varchar(30) COLLATE utf8_unicode_ci NOT NULL,
  `EXE_COMMAND` varchar(500) COLLATE utf8_unicode_ci NOT NULL,
  `INSTALLATION_DIR` varchar(200) COLLATE utf8_unicode_ci DEFAULT NULL,
  `CONFIGURATION_FILE` longtext COLLATE utf8_unicode_ci,
  `NOTES` text COLLATE utf8_unicode_ci,
  PRIMARY KEY (`TOOL_ID`)
) ENGINE=InnoDB AUTO_INCREMENT=24 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `PUBLICATION`
--

DROP TABLE IF EXISTS `PUBLICATION`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `PUBLICATION` (
  `PUB_ID` int(11) NOT NULL AUTO_INCREMENT,
  `AUTHORS` varchar(4000) COLLATE utf8_unicode_ci DEFAULT NULL,
  `DOI` varchar(1500) COLLATE utf8_unicode_ci DEFAULT NULL,
  `ISBN` varchar(100) CHARACTER SET utf8 DEFAULT NULL,
  `ISO_JOURNAL` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `ISSUE` varchar(55) COLLATE utf8_unicode_ci DEFAULT NULL,
  `MEDLINE_JOURNAL` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `PUB_ABSTRACT` longtext COLLATE utf8_unicode_ci,
  `PUBMED_CENTRAL_ID` int(11) DEFAULT NULL,
  `PUBMED_ID` int(11) NOT NULL DEFAULT '0',
  `PUB_TITLE` varchar(740) COLLATE utf8_unicode_ci NOT NULL,
  `RAW_PAGES` varchar(30) COLLATE utf8_unicode_ci DEFAULT NULL,
  `URL` varchar(740) COLLATE utf8_unicode_ci DEFAULT NULL,
  `VOLUME` varchar(55) COLLATE utf8_unicode_ci DEFAULT NULL,
  `PUBLISHED_YEAR` smallint(6) DEFAULT NULL,
  `PUB_TYPE` varchar(150) COLLATE utf8_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`PUB_ID`)
) ENGINE=InnoDB AUTO_INCREMENT=526 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `SAMPLE`
--

DROP TABLE IF EXISTS `SAMPLE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `SAMPLE` (
  `SAMPLE_ID` int(11) NOT NULL AUTO_INCREMENT COMMENT 'The unique identifier assigned by a trigger on the database that assignes the next number in the series. This is effectively an EMG accession number, but we have no intention of ever discolsing this to external users.',
  `ANALYSIS_COMPLETED` date DEFAULT NULL COMMENT 'This is the date that analysis was (last) completed on. It is the trigger used in the current web-app to display the analysis results page, if this is null there will never be the button on the sample page to be able to show the analsyis results.',
  `COLLECTION_DATE` date DEFAULT NULL COMMENT 'The date the sample was collected, this value is now also present in the sample_ann table, and so can be deleted from this table AFTER the web-app has been changed to get the date from the sample_ann table instead.',
  `GEO_LOC_NAME` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL COMMENT 'The (country) name of the location the sample was collected from, this value is now also present in the sample_ann table, and so can be deleted from this table AFTER the web-app has been changed to get the data from the sample_ann table instead.',
  `IS_PUBLIC` tinyint(4) DEFAULT NULL,
  `METADATA_RECEIVED` datetime DEFAULT CURRENT_TIMESTAMP,
  `SAMPLE_DESC` longtext COLLATE utf8_unicode_ci,
  `SEQUENCEDATA_ARCHIVED` datetime DEFAULT NULL,
  `SEQUENCEDATA_RECEIVED` datetime DEFAULT NULL,
  `ENVIRONMENT_BIOME` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `ENVIRONMENT_FEATURE` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `ENVIRONMENT_MATERIAL` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `STUDY_ID` int(11) DEFAULT NULL,
  `SAMPLE_NAME` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `SAMPLE_ALIAS` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `HOST_TAX_ID` int(11) DEFAULT NULL,
  `EXT_SAMPLE_ID` varchar(15) COLLATE utf8_unicode_ci DEFAULT NULL,
  `SPECIES` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `LATITUDE` decimal(7,4) DEFAULT NULL,
  `LONGITUDE` decimal(7,4) DEFAULT NULL,
  `LAST_UPDATE` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `SUBMISSION_ACCOUNT_ID` varchar(15) COLLATE utf8_unicode_ci DEFAULT NULL COMMENT 'Defines which users do have permission to access that sample/study. It is a reference to ERAPRO''s submission_account table',
  `BIOME_ID` smallint(6) DEFAULT NULL,
  PRIMARY KEY (`SAMPLE_ID`),
  KEY `STUDY_ID` (`STUDY_ID`),
  KEY `BIOME_ID` (`BIOME_ID`),
  CONSTRAINT `SAMPLE_ibfk_1` FOREIGN KEY (`STUDY_ID`) REFERENCES `STUDY` (`STUDY_ID`),
  CONSTRAINT `SAMPLE_ibfk_2` FOREIGN KEY (`BIOME_ID`) REFERENCES `BIOME_HIERARCHY_TREE` (`BIOME_ID`)
) ENGINE=InnoDB AUTO_INCREMENT=104652 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `SAMPLE_ANN`
--

DROP TABLE IF EXISTS `SAMPLE_ANN`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `SAMPLE_ANN` (
  `SAMPLE_ID` int(11) NOT NULL COMMENT 'Internal sample ID from SAMPLE table',
  `VAR_VAL_CV` varchar(60) COLLATE utf8_unicode_ci DEFAULT NULL COMMENT 'The value of the variable defined in VAR_ID where that variable must use a controlled vocabulary, this value must be in GSC_CV_CV',
  `UNITS` varchar(25) COLLATE utf8_unicode_ci DEFAULT NULL COMMENT 'The UNITS of the value given in VAR_VAL_UCV',
  `VAR_ID` smallint(6) NOT NULL COMMENT 'The variable ID from the VARIABLE_NAMES table',
  `VAR_VAL_UCV` varchar(4000) COLLATE utf8_unicode_ci DEFAULT NULL COMMENT 'The value for the varible defined by VAR_ID',
  PRIMARY KEY (`SAMPLE_ID`,`VAR_ID`),
  UNIQUE KEY `SAMPLE_ANN_PK` (`SAMPLE_ID`,`VAR_ID`),
  KEY `VAR_ID` (`VAR_ID`),
  KEY `VAR_VAL_CV` (`VAR_VAL_CV`),
  CONSTRAINT `SAMPLE_ANN_ibfk_1` FOREIGN KEY (`VAR_ID`) REFERENCES `VARIABLE_NAMES` (`VAR_ID`),
  CONSTRAINT `SAMPLE_ANN_ibfk_2` FOREIGN KEY (`SAMPLE_ID`) REFERENCES `SAMPLE` (`SAMPLE_ID`),
  CONSTRAINT `SAMPLE_ANN_ibfk_3` FOREIGN KEY (`VAR_VAL_CV`) REFERENCES `GSC_CV_CV` (`VAR_VAL_CV`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `SAMPLE_PUBLICATION`
--

DROP TABLE IF EXISTS `SAMPLE_PUBLICATION`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `SAMPLE_PUBLICATION` (
  `SAMPLE_ID` int(11) NOT NULL COMMENT 'sample_id from the sample table, of the sample associated with this publication',
  `PUB_ID` int(11) NOT NULL COMMENT 'publication ID from publication table',
  PRIMARY KEY (`SAMPLE_ID`,`PUB_ID`),
  KEY `PUB_ID` (`PUB_ID`),
  CONSTRAINT `SAMPLE_PUBLICATION_ibfk_1` FOREIGN KEY (`SAMPLE_ID`) REFERENCES `SAMPLE` (`SAMPLE_ID`),
  CONSTRAINT `SAMPLE_PUBLICATION_ibfk_2` FOREIGN KEY (`PUB_ID`) REFERENCES `PUBLICATION` (`PUB_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `STUDY`
--

DROP TABLE IF EXISTS `STUDY`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `STUDY` (
  `STUDY_ID` int(11) NOT NULL AUTO_INCREMENT,
  `CENTRE_NAME` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL COMMENT 'The center_name used by SRA, it must be in the SRA schema, table CV_CENTER_NAME, which also should contain the description of that acronym (but doesn''t always!)',
  `EXPERIMENTAL_FACTOR` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL COMMENT 'This is metadata about the study, its to give an easy look up for time series studies or things where the study wass designed to test a particular variable, e.g. time, depth, disease etc...',
  `IS_PUBLIC` tinyint(4) DEFAULT NULL COMMENT '1 for public, 0 for private (As of Aug2012 this is set manually in both Production and Web databases)',
  `NCBI_PROJECT_ID` int(11) DEFAULT NULL COMMENT 'This is for an X-ref to the NCBI projects ID, which is now BioProjects, not used very much and should be moved to an xref table',
  `PUBLIC_RELEASE_DATE` date DEFAULT NULL COMMENT 'The date originally specified by the submitter of when their data should be released to public, can be changed by submitter in SRA and we should sync with SRA.',
  `STUDY_ABSTRACT` longtext COLLATE utf8_unicode_ci COMMENT 'The submitter provided description of the project/study.',
  `EXT_STUDY_ID` varchar(18) COLLATE utf8_unicode_ci NOT NULL COMMENT 'This is the external (non-EMG) ID for the study, i.e. its the SRA study ID which always starts ERP or SRP (or DRP)',
  `STUDY_NAME` varchar(300) COLLATE utf8_unicode_ci DEFAULT NULL,
  `STUDY_STATUS` varchar(30) COLLATE utf8_unicode_ci DEFAULT NULL COMMENT 'not used, should be deprecated',
  `DATA_ORIGINATION` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL COMMENT 'Where did the data come from, this could be HARVESTED for stuff taken from SRA, or SUBMITTED for stuff that is brokered to SRA through EMG',
  `AUTHOR_EMAIL` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL COMMENT 'Email address of contact person for study, WILL be shown publicly on Study page',
  `AUTHOR_NAME` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL COMMENT 'Name of contact person for study, WILL be shown publicly on Study page',
  `LAST_UPDATE` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'The date any update was made to the row, this is auto-updated in PROD by a trigger, but not in any others (e.g. web, test or dev)',
  `SUBMISSION_ACCOUNT_ID` varchar(15) COLLATE utf8_unicode_ci DEFAULT NULL COMMENT 'Defines which users do have permission to access that sample/study. It is a reference to ERAPRO''s submission_account table',
  `BIOME_ID` smallint(6) DEFAULT NULL COMMENT 'Links to an entry in the biome hierarchy table, which is a controlled vocabulary.',
  `RESULT_DIRECTORY` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL COMMENT 'Path to the results directory for this study',
  `FIRST_CREATED` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'The date when the study has been created in EMG for the first time. Usually happens when a new study is loaded from ENA into EMG using the webuploader tool.',
  `PROJECT_ID` varchar(18) COLLATE utf8_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`STUDY_ID`),
  KEY `STUDY_BIOME_ID_IDX` (`BIOME_ID`),
  CONSTRAINT `STUDY_ibfk_1` FOREIGN KEY (`BIOME_ID`) REFERENCES `BIOME_HIERARCHY_TREE` (`BIOME_ID`)
) ENGINE=InnoDB AUTO_INCREMENT=1940 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `STUDY_ERROR_TYPE`
--

DROP TABLE IF EXISTS `STUDY_ERROR_TYPE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `STUDY_ERROR_TYPE` (
  `ERROR_ID` tinyint(4) NOT NULL DEFAULT '0' COMMENT 'Primary key.',
  `ERROR_TYPE` varchar(50) COLLATE utf8_unicode_ci NOT NULL COMMENT 'Represents the name of the issue.',
  `DESCRIPTION` text COLLATE utf8_unicode_ci NOT NULL COMMENT 'Describes the issue.',
  PRIMARY KEY (`ERROR_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `STUDY_PUBLICATION`
--

DROP TABLE IF EXISTS `STUDY_PUBLICATION`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `STUDY_PUBLICATION` (
  `STUDY_ID` int(11) NOT NULL COMMENT 'the study id of the study with this publication',
  `PUB_ID` int(11) NOT NULL COMMENT 'publication ID from the publication table',
  PRIMARY KEY (`STUDY_ID`,`PUB_ID`),
  KEY `PUB_ID` (`PUB_ID`),
  CONSTRAINT `STUDY_PUBLICATION_ibfk_1` FOREIGN KEY (`PUB_ID`) REFERENCES `PUBLICATION` (`PUB_ID`),
  CONSTRAINT `STUDY_PUBLICATION_ibfk_2` FOREIGN KEY (`STUDY_ID`) REFERENCES `STUDY` (`STUDY_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `VARIABLE_NAMES`
--

DROP TABLE IF EXISTS `VARIABLE_NAMES`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `VARIABLE_NAMES` (
  `VAR_ID` smallint(6) NOT NULL AUTO_INCREMENT COMMENT ' variable identifier, unique sequenctial number auto generated',
  `VAR_NAME` varchar(50) COLLATE utf8_unicode_ci NOT NULL COMMENT 'Unique human readable name as given by GSC (or other authority)',
  `DEFINITION` longtext COLLATE utf8_unicode_ci COMMENT 'Definition of variable, as given by GSC (or other authority)',
  `VALUE_SYNTAX` varchar(250) COLLATE utf8_unicode_ci DEFAULT NULL COMMENT 'how the GSC (or other authority) has defined the value for the term should be given',
  `ALIAS` varchar(30) COLLATE utf8_unicode_ci DEFAULT NULL COMMENT 'Short name, or INSDC name given by GSC, should be less than 20char and contain no spaces',
  `AUTHORITY` varchar(30) COLLATE utf8_unicode_ci DEFAULT NULL COMMENT 'person or organisation that created/defined the variable (usualy GSC)',
  `SRA_XML_ATTRIBUTE` varchar(30) COLLATE utf8_unicode_ci DEFAULT NULL COMMENT 'Where the ATTRIBUTE should be in the SRA XML schema, (NB currently (Aug2012) almost everything goes in SRA.SAMPLE which is technically wrong!)',
  `REQUIRED_FOR_MIMARKS_COMPLIANC` varchar(1) COLLATE utf8_unicode_ci DEFAULT NULL COMMENT 'If a value for the variable is required for GSC MIMARKS compliance (as of Aug2012)',
  `REQUIRED_FOR_MIMS_COMPLIANCE` varchar(1) COLLATE utf8_unicode_ci DEFAULT NULL COMMENT 'Is a value required for GSC MIMS compliance (as of Aug 2012)',
  `GSC_ENV_PACKAGES` varchar(250) COLLATE utf8_unicode_ci DEFAULT NULL COMMENT 'which (if any) of the GSC environmental packages is this variable part of',
  `COMMENTS` varchar(250) COLLATE utf8_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`VAR_ID`,`VAR_NAME`),
  UNIQUE KEY `VAR_NAME` (`VAR_NAME`),
  UNIQUE KEY `VAR_ID` (`VAR_ID`),
  UNIQUE KEY `VARIABLE_NAMES_PK` (`VAR_ID`,`VAR_NAME`)
) ENGINE=InnoDB AUTO_INCREMENT=938 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2017-09-14 21:17:41
