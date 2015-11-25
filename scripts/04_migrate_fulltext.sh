#! /bin/bash

# Runs migration logic
# Assumes script is in web2py/applications/APPLICATION/scripts folder

cd ..
cd ..
cd ..

python web2py.py -S biblio_api -M -R applications/biblio_api/modules/migrator/migrate_document_uploads.py
