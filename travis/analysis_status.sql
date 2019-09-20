-- MySQL dump 10.13  Distrib 5.6.33, for debian-linux-gnu (x86_64)
--
-- Host: mysql-vm-022.ebi.ac.uk    Database: emg
-- ------------------------------------------------------
--
-- Dumping data for table `ANALYSIS_STATUS`
--

LOCK TABLES `ANALYSIS_STATUS` WRITE;
/*!40000 ALTER TABLE `ANALYSIS_STATUS` DISABLE KEYS */;
INSERT INTO `ANALYSIS_STATUS` VALUES (1,'scheduled'),(2,'running'),(3,'completed'),(4,'failed'),(5,'suppressed'),(6,'QC not passed'),(7,'Unable to process'),(8,'unknown');
/*!40000 ALTER TABLE `ANALYSIS_STATUS` ENABLE KEYS */;
UNLOCK TABLES;

-- Dump completed on 2019-09-18 15:24:22
