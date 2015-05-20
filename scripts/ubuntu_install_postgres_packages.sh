#!/bin/sh
sudo apt-add-repository -y ppa:ubuntugis
sudo apt-get update
sudo apt-get install postgresql-9.1-postgis-2.0 postgresql-contrib-9.1
