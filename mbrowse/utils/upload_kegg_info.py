from __future__ import print_function
import requests
import re
import pubchempy as pcp
from mbrowse.models import Compound
import uuid
from bioservices import *
import sys
if sys.version_info[0] < 3:
    from urllib2 import URLError
else:
    from urllib.error import URLError

def get_pubchem_compound(in_str, type='inchikey'):
    # pubchem stores the SID not the CID!!!! means we can't use it like this
    if not in_str:
        return 0

    try:
        pccs = pcp.get_compounds(in_str, type)
    except pcp.BadRequestError as e:
        print(e)
        return 0
    except pcp.TimeoutError as e:
        print(e)
        return 0
    except URLError as e:
        print(e)
        return 0
    except pcp.PubChemHTTPError as e:
        print(e)
        return 0

    return pccs



def get_inchi_from_chebi(chebi_id):

    if not chebi_id:
        return 0

    chebi_con = ChEBI()

    chebi_entry = chebi_con.getCompleteEntity(chebi_id)

    if 'inchikey' in chebi_entry:
        print('FOUND INCHI KEY', chebi_entry.inchikey)
        return chebi_entry.inchikey
    else:
        return ''





def get_kegg_compound(cid):

    kegg_compound = {'chebi_id':None, 'lbdb_id':None, 'lmdb_id':None, 'pubchem_id':None, 'brite':None}
    url_get = 'http://rest.kegg.jp/get/{}'.format(cid)
    resp = requests.get(url_get)
    all_cont = resp.content

    if type(all_cont) == bytes:
        all_cont = all_cont.decode("utf-8")
    all_cont_rows = all_cont.split('\n')

    chebi_count = 0

    kegg_compound['kegg_cid'] = cid
    for detail in all_cont_rows:

        mtch = re.search('^FORMULA(?::|\s)(.*)', detail)
        if mtch:
            mf = mtch.group(1).strip()
            kegg_compound['mf'] = mf

        mtch = re.search('^EXACT_MASS(?::|\s)(.*)', detail)
        if mtch:
            exact_mass = mtch.group(1).strip()
            kegg_compound['exact_mass'] = exact_mass

        mtch = re.search('^NAME(?::|\s)(.*)', detail)
        if mtch:
            name = mtch.group(1).strip()
            kegg_compound['name'] = name

        # this is getting the SID (substance ID not the compound ID i.e. CID)
        # mtch = re.search('.*PubChem(?::|\s)(.*)', detail)
        # if mtch:
        #     pubchem_id = mtch.group(1).strip()
        #     full_str = re.sub("\s+", ",", pubchem_id)
        #     kegg_compound['pubchem_id'] = full_str

        mtch = re.search('.*ChEBI(?::|\s)(.*)', detail)
        if mtch:

            chebi = mtch.group(1).strip()
            full_str = re.sub("\s+", ",", chebi)
            kegg_compound['chebi_id'] = full_str
            kegg_compound['chebi_id_single'] = full_str.split(',')[0].strip()
            chebi_count += 1


        mtch = re.search('.*LipidBank(?::|\s)(.*)', detail)
        if mtch:
            lb = mtch.group(1).strip()
            kegg_compound['lbdb_id'] = re.sub("\s+", ",", lb)


        mtch = re.search('.*LIPIDMAPS(?::|\s)(.*)', detail)
        if mtch:
            lm = mtch.group(1).strip()
            kegg_compound['lmdb_id'] = re.sub("\s+", ",", lm)

        mtch = re.search('^BRITE(?::|\s)(.*)', detail)
        if mtch:
            br = mtch.group(1).strip()
            kegg_compound['brite'] = br



    if chebi_count > 1:
        print('more than 1 pubchem!')

    return kegg_compound

def get_kegg_info():
    comps_all = Compound.objects.all()
    url_list = 'http://rest.kegg.jp/list/compound'

    resp = requests.get(url_list)

    cont = resp.content
    rows = cont.split('\n')

    kegg_compounds = []

    for i, row in enumerate(rows):
        # print row


        entry = row.split('\t')

        cid = entry[0].split(':')[1]

        names = entry[1]
        name = entry[1].split(';')[0]
        kegg_compound = get_kegg_compound(cid)
        kegg_compound['name'] = name
        kegg_compound['names'] = names


        if comps_all.filter(kegg_id__regex='(^|.*,|")({})("|,.*|$)'.format(cid)):
            continue

        if 'chebi_id_single' in kegg_compound and kegg_compound['chebi_id_single']:
            inchikey = get_inchi_from_chebi(kegg_compound['chebi_id_single'])

        # try:
        #     if 'chebi_id_single' in kegg_compound and kegg_compound['chebi_id_single']:
        #         comp = pcp.get_compounds(kegg_compound['chebi_id_single'])
        #     else:
        #         comp = pcp.get_compounds(kegg_compound['name'], 'name')
        # except pcp.BadRequestError as e:
        #     print 'no pubchem entry due to request error'
        #     continue
        # except pcp.TimeoutError as e:
        #     print 'no pubchem entry due to timeout'
        #     continue
        # if len(comp) > 1:
        #     print 'MORE THAN 1 ENTRY!!!!!', kegg_compound

        if inchikey:

            mtchs = Compound.objects.filter(inchikey_id=comp[0].inchikey)
            if mtchs:

                # if mtchs[0].kegg_id==kegg_c['kegg_cid']:
                #     continue
                mtch_compound = mtchs[0]

                mtch_compound.kegg_id = kegg_compound['kegg_cid']

                mtch_compound.inchikey_id = inchikey

                mtch_compound.chebi_id = '{},{}'.format(mtch_compound.chebi_id,
                                                        kegg_compound['chebi_id']) if mtch_compound.chebi_id else kegg_compound['chebi_id']

                if 'lbdb_id' in kegg_compound:
                    mtch_compound.lbdb_id = '{},{}'.format(mtch_compound.lbdb_id,
                                                        kegg_compound['lbdb_id']) if mtch_compound.chebi_id else kegg_compound['lbdb_id']

                if 'lmdb_id' in kegg_compound:
                    mtch_compound.lmdb_id = '{},{}'.format(mtch_compound.lmdb_id,
                                                       kegg_compound['lmdb_id']) if mtch_compound.chebi_id else  kegg_compound['lmdb_id']

                if 'brite' in kegg_compound:
                    mtch_compound.brite = '{},{}'.format(mtch_compound.brite,
                                                       kegg_compound['brite']) if mtch_compound.brite else kegg_compound['brite']

                mtch_compound.other_names = kegg_compound['names']
                mtch_compound.name = kegg_compound['name']


                mtch_compound.molecular_formula = kegg_compound['mf'] if 'mf' in kegg_compound else None,


                mtch_compound.exact_mass = kegg_compound['exact_mass'] if 'exact_mass' in kegg_compound else None,

                print('UPDATE')

                # if mtch_compound.other_names:
                #     mtch_compound.other_names = '{}; {}'.format(mtch_compound.other_names, kegg_c['names'])
                # else:
                #     mtch_compound.other_names = kegg_c['names']

                mtch_compound.save()


            else:
                print('CREATE')
                new_comp = Compound(inchikey_id=inchikey,
                                    kegg_id=kegg_compound['kegg_cid'],
                                    other_names=kegg_compound['names'],
                                    name=kegg_compound['name'],
                                    molecular_formula=kegg_compound['mf'] if 'mf' in kegg_compound else None,
                                    exact_mass=kegg_compound['exact_mass'] if 'exact_mass' in kegg_compound else None,
                                    chebi_id=kegg_compound['chebi_id'] if 'chebi_id' in kegg_compound else None,
                                    lbdb_id=kegg_compound['lbdb_id'] if 'lbdb_id' in kegg_compound else None,
                                    lmdb_id=kegg_compound['lmdb_id'] if 'lmdb_id' in kegg_compound else None,
                                    brite=kegg_compound['brite'] if 'brite' in kegg_compound else None,
                                    )
                new_comp.save()

        else:
            print('CREATE')
            new_comp = Compound(inchikey_id='UNKNOWN_' + str(uuid.uuid4()),
                                kegg_id=kegg_compound['kegg_cid'],
                                other_names=kegg_compound['names'],
                                name=kegg_compound['name'],
                                molecular_formula=kegg_compound['mf'] if 'mf' in kegg_compound else None,
                                exact_mass=kegg_compound['exact_mass'] if 'exact_mass' in kegg_compound else None,
                                chebi_id=kegg_compound['chebi_id']  if 'chebi_id' in kegg_compound else None,
                                lbdb_id=kegg_compound['lbdb_id']  if 'lbdb_id' in kegg_compound else None,
                                lmdb_id=kegg_compound['lmdb_id']  if 'lmdb_id' in kegg_compound else None,
                                brite = kegg_compound['brite']  if 'brite' in kegg_compound else None,
                                )
            new_comp.save()

            print('NO corresponding pubchem entry for KEGG compound')

        # kegg_compounds.append(kegg_compound)

    # pubchem_componds = []
    # for kegg_c in kegg_compounds:
    #     try:
    #         comp = pcp.get_compounds(kegg_c['pubchem_id'])
    #     except pcp.BadRequestError as e:
    #         comp = ''
    #     except pcp.TimeoutError as e:
    #         comp = ''
    #     if len(comp)>1:
    #         print 'MORE THAN 1 ENTRY!!!!!', kegg_c
    #
    #     if comp:
    #         print kegg_c
    #         mtchs = Compound.objects.filter(inchikey_id=comp[0].inchikey)
    #         if mtchs:
    #             # if mtchs[0].kegg_id==kegg_c['kegg_cid']:
    #             #     continue
    #             mtch_compound = mtchs[0]
    #             mtch_compound.kegg_id = kegg_c['kegg_cid']
    #
    #             mtch_compound.inchikey_id = comp[0].inchikey
    #             mtch_compound.systematic_name = comp[0].iupac_name
    #             mtch_compound.pubchem_id = comp[0].cid
    #             mtch_compound.other_names = kegg_c['names']
    #             mtch_compound.name = kegg_c['name']
    #             mtch_compound.molecular_formula = comp[0].molecular_formula
    #             mtch_compound.monoisotopic_mass = comp[0].monoisotopic_mass
    #             mtch_compound.molecular_weight = comp[0].molecular_weight
    #             mtch_compound.exact_mass = comp[0].exact_mass
    #
    #             # if mtch_compound.other_names:
    #             #     mtch_compound.other_names = '{}; {}'.format(mtch_compound.other_names, kegg_c['names'])
    #             # else:
    #             #     mtch_compound.other_names = kegg_c['names']
    #
    #             mtch_compound.save()
    #
    #
    #         else:
    #             new_comp = Compound(inchikey_id=comp[0].inchikey,
    #                                 systematic_name=comp[0].iupac_name,
    #                                 pubchem_id=comp[0].cid,
    #                                 other_names=kegg_c['names'],
    #                                 name=kegg_c['name'],
    #                                 molecular_formula=comp[0].molecular_formula,
    #                                 monoisotopic_mass=comp[0].monoisotopic_mass,
    #                                 molecular_weight=comp[0].molecular_weight,
    #                                 exact_mass=comp[0].exact_mass,
    #
    #
    #                                 )
    #             new_comp.save()
    #
    #     else:
    #         print 'NO corresponding pubchem entry for KEGG compound'
    #
    # print pubchem_componds

    # try:
    #     pccs = pcp.get_compounds(in_str, pcp_type)
    # except pcp.BadRequestError as e:
    #     print e
    #     return 0
    # except pcp.TimeoutError as e:
    #     print e
    #     return 0
    #
    # if pccs:
    #     pcc = pccs[elem]
    #     self.compound_info['inchikey_id'] = pcc.inchikey
    #
    #     if len(pccs) > 1:
    #         print 'WARNING, multiple compounds for ', self.compound_info



