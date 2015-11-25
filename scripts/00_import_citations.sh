#! /bin/bash

# imports old database to mysql
# Assumes script is in web2py/applications/APPLICATION/scripts folder

mysql -uroot -p < legacy_database.sql
