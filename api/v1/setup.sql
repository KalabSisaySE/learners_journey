-- Setups the database
CREATE DATABASE IF NOT EXISTS `the_journey`;
CREATE USER IF NOT EXISTS 'lns_jny_dev'@'localhost' IDENTIFIED BY 'root';
GRANT ALL ON the_journey.* TO 'lns_jny_dev'@'localhost';