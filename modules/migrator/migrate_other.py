from migrator import migration


LEGACY_DB = DAL('MYCONNECTIONSTRING',migrate=True,fake_migrate_all=True,lazy_tables=False)
NEW_DB =  DAL('MYOTHERCONNECTIONSTRING', check_reserved=['all'], migrate=True,fake_migrate_all=False,lazy_tables=False)

DOCUMENT_BASE = request.folder

migration.logic.migrate_everything_else(LEGACY_DB,NEW_DB)



