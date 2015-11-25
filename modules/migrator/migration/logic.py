import os

from . import schema
from .constants import LEGACY_BIBLIO_MAPPING, RW, MAPS_LEGACY_FIELDS

def truncate_tables(db):

    for table in db.tables:
        db[table].truncate('RESTART IDENTITY CASCADE')
        db.commit()
    db.commit()

def new_bibliographies(db):
    table = db.bibliography
    query = table.id > 0
    rows = db(query).select()

    result = {}

    new_biblios = db(db.bibliography.id>0).select()

    for old_key, new_value in LEGACY_BIBLIO_MAPPING.iteritems():
        bibliography_id = new_biblios.find(lambda row: row.title == new_value).first()
        result[old_key] = bibliography_id

    return result

def create_bibliographies(db):

    def get_collections():
        first_item = LEGACY_BIBLIO_MAPPING['all']

        _collections = sorted(list(set(LEGACY_BIBLIO_MAPPING.values())))
        _collections.remove(first_item)
        _collections.insert(0,first_item)

        return _collections

    collections = get_collections()

    for item in collections:
        db.bibliography.insert(title=item)

    db.commit()

def migrate_citations(db,old_citations):

    latin_fields = ['c_title','c_name','c_abstract',
                    'c_subjects','c_auth','c_keywords','c_af']

    _collections = new_bibliographies(db)

    bad_citations = 0
    good_citations = 0
    total_citations = len(old_citations)
    print '--- MIGRATING CITATIONS (%s) --- ' % total_citations
    processed = 1
    for row in old_citations:
        print 'processing %s/%s' %(processed,total_citations)
        
        for field_name in latin_fields:
            value = row[field_name]
            if value != None:
                row[field_name] = value.decode('latin-1').encode('utf-8')

        _old_bibliography_id = row.c_bibname

        _new_bibliography_id = _collections.get(_old_bibliography_id,False)

        row_collections = []

        if _new_bibliography_id not in [False,None]:
            row_collections = [_new_bibliography_id]

        row = row.as_dict()

        for k,v in row.iteritems():
            if v == 'NULL':
                row[k] = None

        row['author'] = row['c_auth']
        row['title'] = row['c_title']
        row['journal'] = row['c_name']
        row['issue'] = row['c_issue']
        row['page_span'] = row['c_pages']
        row['abstract'] = row['c_abstract']
        row['isbn_issn'] = row['c_catnum']
        row['publication_date'] = row['c_date']
        row['collections'] = row_collections
        row['downloadable_resources'] = []
        row['literature_reviews'] = []
        row['tags'] = []

        result = db.citation.validate_and_insert(**row)

        if result.errors:
            bad_citations +=1
        else:
            good_citations +=1
        
        db.commit()
        processed+=1

    print good_citations, ' Citations Migrated'
    print bad_citations, ' Citations With Errors'
    print '---  --- '

    db.commit()



def migrate_documents(db,old_documents):
    print '---- MIGRATING DOCUMENTS ---- '

    good_documents = 0
    bad_documents = 0
    
    total_documents = len(old_documents)
    processed = 1
    
    for document in old_documents:
        print 'processing document %s/%s' % (processed,total_documents)
        document = document.as_dict()
        document.pop('d_mode')

        result = db.user_document.validate_and_insert(**document)

        if result.errors:
            bad_documents += 1
        else:
            good_documents += 1
        processed +=1

    print good_documents, ' Documents Migrated'
    print bad_documents, ' Documents With Errors'
    print '---  --- '

    db.commit()



def fix_document_citations(db):
    print '---- FIXING DOCUMENT CITATIONS ---- '

    new_documents = db(db.user_document.id>0).select(orderby=db.user_document.d_ckey)

    bad_citations = 0
    good_citations = 0

    documents_without_citations = []
    
    db.commit()


    total = len(new_documents)
    processing = 1
    for document in new_documents:
        print 'fixing document citation %s/%s' % (processing,total) 
        old_citation_id = document.d_ckey
        print old_citation_id, document.id, document.d_ckey

        if old_citation_id not in [None,'']:

            citation_query = db.citation.c_pkey == old_citation_id
            
            no_existing_citation = db(citation_query).isempty()
            
            citation_exists = not no_existing_citation
                        
            if citation_exists == False:
                documents_without_citations.append(old_citation_id)
                bad_citations += 1
                
                _citation = {'primary_document':document.id,
                             'c_pkey':old_citation_id}
                try:
                    result = db.citation.validate_and_insert(**_citation)
                    print result

                except:
                    print db._lastsql
                db.commit()
                good_citations += 1
            
            citation_record = db(citation_query).select().first()

            
            if not isinstance(citation_record.downloadable_resources,list):
                if citation_record.downloadable_resources in [None,'']:
                    citation_record.downloadable_resources = []
                else:
                    citation_record.downloadable_resources = [citation_record.downloadable_resources]
            resources = []
            resources.extend(citation_record.downloadable_resources)
            resources.append(citation_record.id)
            resources = list(set(resources))
            
            citation_record.update_record(primary_document = document.id,
                                          downloadable_resources = resources)
            
                
            document.update_record(citation_id = citation_record.id)
            db.commit()
        processing+=1
    print good_citations, 'Document Primary Citations Updated'
    print bad_citations, 'Documents without a Primary Citation'
    print documents_without_citations

    print '-----------'

    db.commit()




def fix_review_citations(db):

    reviews = db(db.review.id>0).select()

    bad_reviews = 0
    bad_review_citations = []

    for review in reviews:

        old_citation_id = False

        if review.s_ckey not in [None,'']:
            old_citation_id = review.s_ckey
        elif review.r_ckey not in [None,'']:
            old_citation_id = review.r_ckey

        if old_citation_id != False:
            new_citation_record = db(db.citation.c_pkey == old_citation_id).select().first()
            if new_citation_record is None:
                bad_reviews +=1
                bad_review_citations.append(old_citation_id)
            else:
                document_id = new_citation_record.primary_document
                review.update_record(user_documents=[document_id])
    print '----fixing review citations --- '
    print bad_reviews, 'Reviews with bad citation'
    print bad_review_citations
    print '---------'
    db.commit()



def migrate_reviews_and_summaries(from_db,to_db):

    print '---- Migrating Reviews and Summaries -----'

    review_query = from_db.reviews.r_id != None
    old_reviews = from_db(review_query).select()

    summary_query = from_db.summary.s_id != None
    old_summaries = from_db(summary_query).select()

    migrate_reviews(to_db,old_reviews)

    migrate_summaries(to_db,old_summaries)

    print '---------   ---------------'





def migrate_reviews(db,old_reviews):
    print 'migrating reviews'

    table = db.review
    table.review_type.default = 'review'
    bad = 0
    good = 0

    for review in old_reviews:
        table.r_id.default = review.r_id
        table.r_ckey.default = review.r_ckey
        table.body.default = review.r_review
        result = table.validate_and_insert()

        if result.errors:
            bad +=1
        else:
            good +=1

    print bad, good, 'Bad, good Reviews'

    db.commit()

def migrate_summaries(db,old_summaries):
    print 'migrating summaries'
    bad = 0
    good = 0

    table = db.review
    table.review_type.default = 'summary'

    for summary in old_summaries:

        table.r_id.default = None
        table.r_ckey.default = None
        table.body.default = None

        table.s_ckey.default = summary.s_ckey
        table.s_id.default = summary.s_id
        table.s_keywords.default = summary.s_keywords

        table.study_purpose.default = summary.s_purpose
        table.study_subjects.default = summary.s_subjects
        table.study_design.default = summary.s_design
        table.study_measures.default = summary.s_measures
        table.study_analyses.default = summary.s_analyses
        table.study_results.default = summary.s_results
        table.study_effects_observed.default = summary.s_oeffects
        table.study_effects_a.default = summary.s_aeffects
        table.study_comments.default = summary.s_comments
        result = table.validate_and_insert()

        if result.errors:
            print result.errors
            bad +=1
        else:
            good +=1

    print bad, good, 'Bad, good Summaries'

    db.commit()


def migrate_tags(db):

    print '---- Migrating Tags  ---- '

    reviews = db(db.review.id>0).select()

    for review in reviews:
        tags = []

        old_keywords = review.s_keywords

        if isinstance(old_keywords,str):
            old_keywords = old_keywords.split(',')

            for keyword in old_keywords:

                keyword = keyword.lstrip().rstrip()

                if keyword not in [None,'']:

                    tag = db(db.tag.title == keyword).select(db.tag.id).first()

                    if tag != None:
                        tags.append(tag.id)
                    else:
                        tag = db.tag.insert(title=keyword,description=keyword)
                        tags.append(tag.id)
        review.update_record(tags=tags)

    db.commit()

    citations = db(db.citation.id>0).select()


    for citation in citations:
        tags = []

        old_keywords = citation.c_keywords

        if isinstance(old_keywords,str):
            old_keywords = old_keywords.split(',')

            for keyword in old_keywords:
                keyword = keyword.lstrip().rstrip()

                if keyword not in [None,'']:

                    tag = db(db.tag.title == keyword).select(db.tag.id).first()

                    if tag != None:
                        tags.append(tag.id)
                    else:
                        tag = db.tag.insert(title=keyword,description=keyword)
                        tags.append(tag.id)
        citation.update_record(tags=tags)
    print '---- Tags Migrated'
    db.commit()


def fix_document_file_names(db):

    table = db.user_document

    documents = db(table.d_url != None).select(table.id,table.file_name,table.d_url)

    for document in documents:
        file_name = document.d_url.split('/')[-1]
        document.update_record(file_name=file_name)

    return 'ok'


def fix_review_titles(db):

    table = db.review

    reviews = db(table.id>0).select()

    for review in reviews:
        review_type = review.review_type.capitalize()
        article_title = ''

        if not isinstance(review.user_documents,list):
            review.update_record(user_documents=[])

        if review.user_documents and len(review.user_documents) > 0:

            document_id = review.user_documents[0]

            citation = db(db.citation.primary_document == document_id).select().first()

            if citation:
                article_title = citation.title

        title = '%s of %s' % (review_type, article_title)

        review.update_record(title=title)

    db.commit()


def legacy_citations(db):
    table = db.citations
    query = table.c_pkey != None
    rows = db(query).select()
    return rows

def legacy_documents(db):
    query = db.documents.d_pkey != None
    rows = db(query).select()
    return rows

def check_citation_categories(db):
    records = db(db.citations.c_pkey >0).select(db.citations.c_bibname,groupby=db.citations.c_bibname)

    found_bib_names = sorted(list([record.c_bibname for record in records]))

    bib_names = get_bib_names()

    expect_bib_names = sorted(list([x for x in bib_names.keys()]))

    assert(found_bib_names == expect_bib_names)

    citation_categories = db().select(db.citations.c_category,
                                      groupby=db.citations.c_category)


    found_citation_categories = sorted(list([record.c_category for record in citation_categories]))

    cit_categories = get_categories()

    expected_citation_categories = sorted(list([x for x in cit_categories.keys()]))

    assert(found_citation_categories == expected_citation_categories)


def migrate_database(LEGACY_DB,NEW_DB):

    schema.define_legacy_tables(LEGACY_DB)
    schema.define_new_tables(NEW_DB)

    truncate_tables(NEW_DB)

    create_bibliographies(NEW_DB)

    old_citations = legacy_citations(LEGACY_DB)

    migrate_citations(NEW_DB,old_citations)



    
def migrate_everything_else(LEGACY_DB,NEW_DB):
    schema.define_legacy_tables(LEGACY_DB)
    schema.define_new_tables(NEW_DB)
    old_documents = legacy_documents(LEGACY_DB)

    migrate_documents(NEW_DB,old_documents)
    
    fix_document_citations(NEW_DB)

    migrate_reviews_and_summaries(LEGACY_DB,NEW_DB)

    fix_review_citations(NEW_DB)
    fix_review_titles(NEW_DB)

    migrate_tags(NEW_DB)
    fix_document_file_names(NEW_DB)

def migrate_document_uploads(LEGACY_DB,NEW_DB,DOCUMENT_BASE):
    schema.define_legacy_tables(LEGACY_DB)
    schema.define_new_tables(NEW_DB)


    db = NEW_DB

    table = db.user_document

    documents = db(table.d_url != None).select(table.id,table.file_name,table.d_url)
    print len(documents), 'Documents Found'

    good_documents = 0
    bad_documents = 0

    bad_ids = []

    for document in documents:
        path = os.path.join(DOCUMENT_BASE,'private','new')
        old_base = 'http://eywa.maps.org/w3pb/new/'

        try:
            print document.id, 'uploading from ', document.d_url

            url = document.d_url
            assert(old_base in url)

            url = url.replace(old_base,'')

            parts = url.split('/')
            path = os.path.join(path,os.path.join(*parts))

            assert(os.path.isfile(path))
            print path

            file = db.user_document.file_upload.store(open(path,'rb'), parts[-1])
            document.update_record(file_upload=file)
            db.commit()
            good_documents +=1
        except Exception as e:
            print 'bad document', document.id
            print e

            bad_documents+=1
            bad_ids.append(document.id)

    print 'bad ids:', bad_ids
    print good_documents, 'Good Docs'
    print bad_documents, 'bad docs'
