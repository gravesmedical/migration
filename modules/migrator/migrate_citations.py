from migrator import migration

migrate_database = migration.logic.migrate_database

LEGACY_DB = DAL('MYCONNECTIONSTRING',migrate=True,fake_migrate_all=True,lazy_tables=False)
NEW_DB =  DAL('MYOTHERCONNECTIONSTRING', check_reserved=['all'], migrate=True,fake_migrate_all=False,lazy_tables=False)

DOCUMENT_BASE = request.folder

migrate_database(LEGACY_DB,NEW_DB)



