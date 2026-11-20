-- WARNING:
-- This script permanently deletes the MyHotel database
-- and all data stored in it.
-- Use only when intentionally rebuilding the project.

DROP DATABASE IF EXISTS myHotel;

CREATE DATABASE myHotel
    CHARACTER SET utf8mb4;

USE myHotel;