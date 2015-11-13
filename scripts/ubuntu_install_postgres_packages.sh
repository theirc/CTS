#!/bin/sh
sudo apt-add-repository -y ppa:ubuntugis
sudo apt-get update
sudo apt-get install postgresql-9.3-postgis-2.1 postgresql-contrib-9.3
