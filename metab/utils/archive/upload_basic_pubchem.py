import gzip
import io
import re
import sqlite3
from rdkit import Chem
from metab.utils.msp2db import insert_query_m

def create_pubchem_sqlite(compound_pth, sqlite_pth):
    conn = sqlite3.connect(sqlite_pth)
    c = conn.cursor()
    c.execute('DROP TABLE IF EXISTS pubchem_compounds')
    c.execute('''CREATE TABLE pubchem_compounds (
                                      cid integer PRIMARY KEY,
                                      inchikey text,
                                      name text,
                                      systematic_name text,
                                      mf text,
                                      exact_mass float,
                                      monoisotopic_weight float,
                                      molecular_weight float
                                      )'''
              )
    suppl = Chem.SDMolSupplier(compound_pth)

    inchi_dict = {}
    rows = []
    c = 1
    for i, mol in enumerate(suppl):
        print(i)
        if c>500:
            insert_query_m(rows, columns='cid, inchikey, name, systematic_name, mf, exact_mass, molecular_weight,monoisotopic_weight',
                           conn=conn, table='pubchem_compounds',
                           db_type='sqlite')
            rows = []
        if not mol:
            continue
        pd = mol.GetPropsAsDict()

        cid = pd['PUBCHEM_COMPOUND_CID']
        exact_mass = pd['PUBCHEM_EXACT_MASS'] if 'PUBCHEM_EXACT_MASS' in pd.keys() else None
        inchi_key = pd['PUBCHEM_IUPAC_INCHIKEY'] if 'PUBCHEM_IUPAC_INCHIKEY' in pd.keys() else None
        mf = pd['PUBCHEM_MOLECULAR_FORMULA'] if 'PUBCHEM_MOLECULAR_FORMULA' in pd.keys() else None
        systematic_name = pd['PUBCHEM_IUPAC_SYSTEMATIC_NAME'] if 'PUBCHEM_IUPAC_SYSTEMATIC_NAME' in pd.keys() else None
        name = pd['PUBCHEM_IUPAC_NAME'] if 'PUBCHEM_IUPAC_NAME' in pd.keys() else None

        mw = pd['PUBCHEM_MOLECULAR_WEIGHT'] if 'PUBCHEM_MOLECULAR_WEIGHT' in pd.keys() else None

        miw = pd['PUBCHEM_MONOISOTOPIC_WEIGHT'] if 'PUBCHEM_MONOISOTOPIC_WEIGHT' in pd.keys() else None

        rows.append((cid, inchi_key, name, systematic_name, mf, exact_mass, mw, miw))
        c+=1

    insert_query_m(rows,
                   columns='cid, inchikey, name, systematic_name, mf, exact_mass, molecular_weight,monoisotopic_weight',
                   conn=conn, table='pubchem_compounds',
                   db_type='sqlite')

# def upload_basic_pubchem(cid_inchi_pth, cid_name_pth):
#
#     with io.TextIOWrapper(io.BufferedReader(gzip.open(cid_inchi_pth))) as file:
#         new_comps = []
#         c = 1
#         for i, line in enumerate(file):
#             print i
#             if i>8000:
#                 break
#             if c>5000:
#                 Compound.objects.bulk_create(new_comps)
#                 new_comps = []
#                 c = 0
#
#             l = line.split('\t')
#             inchikey= l[2].rstrip()
#             cid = l[0].rstrip()
#             if Compound.objects.filter(inchikey_id=inchikey, pubchem_id__regex='(^|,){}(,|$)'.format(cid)):
#                 continue
#             elif Compound.objects.filter(inchikey_id=inchikey):
#                 comp = Compound.objects.filter(inchikey_id=inchikey)[0]
#                 comp.pubchem_id = '{},{}'.format(comp.pubchem_id, cid)
#                 comp.save()
#             elif not Compound.objects.filter(inchikey_id=inchikey):
#                 comp = Compound(inchikey_id=inchikey, pubchem_id=cid)
#                 comp.save()
#                 new_comps.append(comp)
#             c+=1
#
#     Compound.objects.bulk_create(new_comps)
#     named = {}
#
#     with io.TextIOWrapper(io.BufferedReader(gzip.open(cid_name_pth))) as file:
#         c = 1
#         for i, line in enumerate(file):
#             print i, line
#             if i>8000:
#                 break
#
#
#             line = line.rstrip()
#             l = line.split('\t')
#             if line[0] in named.keys():
#                 continue
#
#             comps = Compound.objects.filter(pubchem_id__regex='(^|,){}(,|$)'.format(l[0].strip()), name__isnull=False)
#
#             if comps:
#                 for comp in comps:
#                     comp.name = l[1].strip()
#                     comp.save()
#
#             if c>300:
#                 break
#
#             named[l[0].strip()] = ''
#             c += 1
