
from gluon import Field
from gluon.tools import Auth
from fs.s3fs import S3FS


from gluon.validators import *
from .constants import LEGACY_BIBLIO_MAPPING, RW, MAPS_LEGACY_FIELDS


UPLOAD_FILESYSTEM = S3FS(bucket = 'S3BUCKET', aws_access_key='S3ACCESSKEY', aws_secret_key='S3SECRETKEY')

def define_legacy_tables(db):

    db.define_table('citations',
                    Field('c_pkey','id'),
                    Field('c_key', 'string'),
                    Field('c_id', 'string'),
                    Field('c_auth', 'string'),
                    Field('c_date', 'string'),
                    Field('c_title', 'text'),
                    Field('c_name', 'string'),
                    Field('c_issue', 'string'),
                    Field('c_pages', 'string'),
                    Field('c_abstract', 'text'),
                    Field('c_subjects', 'string'),
                    Field('c_bibname', 'string'),
                    Field('c_ishof', 'string'),
                    Field('c_lsdid', 'string'),
                    Field('c_psiid', 'string'),
                    Field('c_catnum', 'string'),
                    Field('c_keywords', 'string'),
                    Field('c_category', 'string'),
                    Field('c_af', 'text'),
                    Field('c_cdate', 'integer', default=0),
                    Field('c_mdate', 'integer', default=0),
                    Field('c_pmid', 'integer', default=0),
                    Field('c_owner', 'integer', default=0),
                    Field('c_mode','string',default='r'))


    db.define_table('documents',
                    Field('d_pkey', 'id'),
                    Field('d_id', 'string'),
                    Field('d_cid', 'integer'),
                    Field('d_lang', 'string'),
                    Field('d_type', 'string'),
                    Field('d_url', 'text'),
                    Field('d_ckey', 'integer', default=0),
                    Field('d_cdate', 'integer', default=0),
                    Field('d_mdate', 'integer', default=0),
                    Field('d_owner', 'integer', default=0),
                    Field('d_mode','string', default='r'))

    db.define_table('reviews',
                    Field('r_id','id'),
                    Field('r_ckey', 'integer'),
                    Field('r_auth', 'string'),
                    Field('r_cdate', 'integer'),
                    Field('r_mdate', 'integer', default=0),
                    Field('r_type',  'string', default='preliminary', requires = IS_IN_SET(['preliminary','final'])),
                    Field('r_review', 'text'),
                    Field('r_owner', 'integer', default=0),
                    Field('r_mode', 'string', requires = IS_IN_SET(RW)))


    db.define_table('summary',
                    Field('s_ckey','integer', default=0),
                    Field('s_auth' , 'string'),
                    Field('s_cdate', 'integer', default=0),
                    Field('s_mdate', 'integer', default=0),
                    Field('s_type','string', default='short',),
                    Field('s_keywords' , 'string'),
                    Field('s_purpose', 'text'),
                    Field('s_subjects', 'text'),
                    Field('s_design', 'text'),
                    Field('s_measures', 'text'),
                    Field('s_analyses', 'text'),
                    Field('s_results', 'text'),
                    Field('s_oeffects', 'text'),
                    Field('s_aeffects', 'text'),
                    Field('s_comments', 'text'),
                    Field('s_id', 'id'),
                    Field('s_owner', 'integer', default=0),
                    Field('s_mode', 'string', requires = IS_IN_SET(RW)))

    db.citations.c_mode.requires = IS_IN_SET(RW)
    db.documents.d_mode.requires = IS_IN_SET(RW)

    db.summary.requires=IS_IN_SET(['long','short'])

def define_new_tables(db):

    auth = Auth(db)
    auth.define_tables(username=False, signature=False,migrate=False)

    db.define_table('bibliography',
                    Field('title','string'))

    db.define_table('user_document',
                    Field('citation_id','integer'),
                    Field('file_upload','upload'),
                    Field('file_name','string'),
                    Field('last_modified','datetime'),
                    Field('date_created','datetime'),
                    Field('d_pkey', 'integer'),
                    Field('d_id', 'string'),
                    Field('d_cid', 'integer'),
                    Field('d_lang', 'string'),
                    Field('d_type', 'string'),
                    Field('d_url', 'text'),
                    Field('d_ckey', 'integer'),
                    Field('d_cdate', 'integer'),
                    Field('d_mdate', 'integer'),
                    Field('d_owner', 'integer'))


    db.define_table('review',
                     Field('user_id','integer'),
                     Field('title','string'),
                     Field('body','text'),
                     Field('user_documents','list:string'),
                     Field('tags','list:string'),
                     Field('date_created','datetime'),
                     Field('date_modified','datetime'),
                     Field('study_purpose','text'),
                     Field('study_subjects','text'),
                     Field('study_design','text'),
                     Field('study_measures','text'),
                     Field('study_analyses','text'),
                     Field('study_results','text'),
                     Field('study_effects_observed','text'),
                     Field('study_effects_a','text'),
                     Field('study_comments','text'),
                     Field('review_type','string'),
                     Field('s_id','integer'),
                     Field('s_ckey','integer'),
                     Field('s_keywords','string'),
                     Field('r_id','integer'),
                     Field('r_ckey','integer'))

    db.review.user_documents.default = []
    db.review.tags.default = []
    
    db.define_table('citation',
                    Field('user_id','integer'),
                    Field('publicly_searchable','boolean'),
                    Field('primary_document','reference user_document'),
                    Field('author','string'),
                    Field('title','text'),
                    Field('journal','text'),
                    Field('publication_date','string'),
                    Field('issue','string'),
                    Field('page_span','string'),
                    Field('abstract','text'),
                    Field('isbn_issn','string'),
                    Field('collections','list:reference bibliography'),
                    Field('downloadable_resources','list:reference user_document'),
                    Field('literature_reviews','list:reference review'),
                    Field('tags','list:string'),
                    Field('last_modified','datetime'),
                    Field('date_created','datetime'),
                    Field('c_pkey','integer'),
                    Field('c_key', 'string'),
                    Field('c_id', 'string'),
                    Field('c_auth', 'string'),
                    Field('c_date', 'string'),
                    Field('c_title', 'text'),
                    Field('c_name', 'string'),
                    Field('c_issue', 'string'),
                    Field('c_pages', 'string'),
                    Field('c_abstract', 'text'),
                    Field('c_subjects', 'string'),
                    Field('c_bibname', 'string'),
                    Field('c_ishof', 'string'),
                    Field('c_lsdid', 'string'),
                    Field('c_psiid', 'string'),
                    Field('c_catnum', 'string'),
                    Field('c_keywords', 'string'),
                    Field('c_category', 'string'),
                    Field('c_af', 'text'),
                    Field('c_cdate', 'integer'),
                    Field('c_mdate', 'integer'),
                    Field('c_pmid', 'integer'),
                    Field('c_owner', 'integer'),
                    Field('c_mode','string'))

    db.citation.collections.default = []
    db.citation.downloadable_resources.default = []
    db.citation.literature_reviews.default = []


    db.define_table('tag',
                    Field('title','string'),
                    Field('description','text'))

    db.user_document.file_upload.uploadfs = UPLOAD_FILESYSTEM
