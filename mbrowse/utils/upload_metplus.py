from __future__ import print_function
import sqlite3
from mbrowse.utils.sql_utils import sql_column_names, check_table_exists_sqlite
from mbrowse.models import Compound

def upload_metplus(db_pth):
    # This is a quick way to get alot of important compounds.
    # The sqlite database is from https://github.com/ICBI/MetPlus-DB
    # It is 5 years old at the time of writing so it is potentially missing compounds so can't be completely relied
    # on. Also it does not contain all of PubChem so obviously we still have to add many compounds when we upload
    # the annotations that have used pubchem as the database

    conn = sqlite3.connect(db_pth)
    conn.text_factory = bytes
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM  MetPlus')

    names = sql_column_names(cursor)
    comps = []
    cursor.next() # first row is header (strange for an sqlite database!)
    c=0
    for i, row in enumerate(cursor):

        if Compound.objects.filter(inchikey_id=row[names['INCHIKEY']]):
            continue

        if c > 1000:
            Compound.objects.bulk_create(comps)
            print(i)
            comps = []
            c = 0
        comp = Compound(
                      inchikey_id=row[names['INCHIKEY']],
                      exact_mass=row[names['FORMULA']],  # I think this formula is actually molecular weight!!
                      molecular_formula=row[names['MONOISOTOPIC_WEIGHTS']],  # I think this formula is actually molecular weight!!
                      iupac_name=row[names['IUPAC_NAME']].decode('utf-8', 'ignore').encode('utf-8'),
                      systematic_name=row[names['SYSTEMATIC_NAME']].decode('utf-8', 'ignore').encode('utf-8'),
                      name=row[names['COMMON_NAME']].decode('utf-8', 'ignore').encode('utf-8'),
                      trade_name=row[names['TRADE_NAME']].decode('utf-8', 'ignore').encode('utf-8'),
                      hmdb_id=row[names['HMDB_ID']],
                      lmdb_id=row[names['LMDB_ID']],
                      humancyc_id=row[names['HUMANCYC_ID']],
                      pubchem_id=row[names['PUBCHEM_CID']],
                      chemspider_id=row[names['CHEMSPIDER_ID']],
                      chebi_id=row[names['CHEBI_ID']],
                      metlin_id=row[names['METLIN_ID']],
                      kegg_id=row[names['KEGG_ID']],
                      foodb_id=row[names['FooDB_ID']],
                      )
        comps.append(comp)
        c+=1
    Compound.objects.bulk_create(comps)
