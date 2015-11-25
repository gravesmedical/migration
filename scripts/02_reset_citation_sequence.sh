#! /bin/bash

# Resets citation_id because this is not working
# Assumes script is in web2py/applications/APPLICATION/scripts folder

psql -U admin -d maps -c "SELECT setval('citation_id_seq', (SELECT max(citation.id)+1 from public.citation),false);"

