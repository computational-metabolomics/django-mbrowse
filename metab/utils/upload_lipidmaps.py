# -*- coding: utf-8 -*-
import re
import pubchempy as pcp
from metab.models import Compound
import uuid
from rdkit import Chem
from django.utils.encoding import force_text, smart_bytes, smart_text

def get_pubchem_compound(in_str, type='inchikey'):
    if not in_str:
        return 0

    try:
        pccs = pcp.get_compounds(in_str, type)
    except pcp.BadRequestError as e:
        print e
        return 0
    except pcp.TimeoutError as e:
        print e
        return 0

    return pccs



def get_lipidmaps_info(sdf_pth):


    suppl = Chem.SDMolSupplier(sdf_pth)

    new_comps = []
    c= 0
    for i, mol in enumerate(suppl):
        # print row
        # if i<3000:
        #     continue
        if not mol:
            continue
        pd = mol.GetPropsAsDict()
        pd = string_compat(pd)

        if not 'INCHI_KEY' in pd:
            new_comp = create_lipid_compound(pd)
            new_comps.append(new_comp)
            continue

        mtchs = Compound.objects.filter(inchikey_id=pd['INCHI_KEY'])

        if i % 1000 == 0:
            print i, pd

        if c==1:
            # Can't do batch because may end up with duplicate inchikeys in the same batch!!!
            Compound.objects.bulk_create(new_comps)
            c = 0
            new_comps = []

        if mtchs:

            # if mtchs[0].kegg_id==kegg_c['kegg_cid']:
            #     continue
            mtch_compound = mtchs[0]
            if 'PUBCHEM_CID' in pd:
                pubchem_id_tmp = str(int(pd['PUBCHEM_CID']))
                if not mtch_compound.pubchem_id:
                    mtch_compound.pubchem_id = pubchem_id_tmp
                elif not re.match('(^|,){}(,|$)'.format(pubchem_id_tmp), mtch_compound.pubchem_id):
                    mtch_compound.pubchem_id = '{},{}'.format(mtch_compound.pubchem_id, pubchem_id_tmp)


            if 'LM_ID' in pd:
                if not mtch_compound.lmdb_id:
                    mtch_compound.lmdb_id = pd['LM_ID']
                elif not re.match('(^|,){}(,|$)'.format(re.escape(pd['LM_ID'])), mtch_compound.lmdb_id):
                    mtch_compound.lmdb_id = '{},{}'.format(mtch_compound.lmdb_id, pd['LM_ID'])


            if 'MAIN_CLASS' in pd:
                if not mtch_compound.compound_class:
                    mtch_compound.compound_class = pd['MAIN_CLASS']
                elif not re.match('(^|,){}(,|$)'.format(re.escape(pd['MAIN_CLASS'])), mtch_compound.compound_class):
                    mtch_compound.compound_class = '{},{}'.format(mtch_compound.compound_class, pd['MAIN_CLASS'])


            if 'SUB_CLASS' in pd:
                if not mtch_compound.sub_class:
                    mtch_compound.sub_class = pd['SUB_CLASS']
                elif not re.match('(^|,){}(,|$)'.format(re.escape(pd['SUB_CLASS'])), mtch_compound.sub_class):
                    mtch_compound.sub_class = '{},{}'.format(mtch_compound.sub_class, pd['SUB_CLASS'])


            if 'CATEGORY' in pd:
                if not mtch_compound.category:
                    mtch_compound.category = pd['CATEGORY']
                elif not re.match('(^|,){}(,|$)'.format(re.escape(pd['CATEGORY'])), mtch_compound.category):
                    mtch_compound.category = '{},{}'.format(mtch_compound.category, pd['CATEGORY'])


            if 'SYSTEMATIC_NAME' in pd:
                if not mtch_compound.systematic_name:
                    mtch_compound.systematic_name = pd['SYSTEMATIC_NAME']

            if 'COMMON_NAME' in pd:
                if not mtch_compound.name:
                    mtch_compound.name = pd['COMMON_NAME']

            if 'SYNONYMS' in pd:
                if not mtch_compound.other_names:
                    mtch_compound.other_names = pd['SYNONYMS']


            if 'EXACT_MASS' in pd:
                if not mtch_compound.exact_mass:
                    mtch_compound.exact_mass = pd['EXACT_MASS']

            if 'FORMULA' in pd:
                if not mtch_compound.molecular_formula:
                    mtch_compound.molecular_formula = pd['FORMULA']

            mtch_compound.save()


        else:

            new_comp = create_lipid_compound(pd)
            new_comps.append(new_comp)
        c+=1



    Compound.objects.bulk_create(new_comps)

def string_compat(pd):
    new_pd = {}
    for k, v in pd.iteritems():
        if isinstance(v, float):
            new_pd[k] = v
        else:
            new_pd[k] = force_text(v.decode('cp1252', 'ignore').encode('utf-8'))

    return new_pd

def create_lipid_compound(pd):

    if 'COMMON_NAME' in pd:
        name = pd['COMMON_NAME']
    elif 'SYSTEMATIC_NAME' in pd:
        name = pd['SYSTEMATIC_NAME']
    elif 'SYNONYMS' in pd:
        name = pd['SYNONYMS']
    elif 'LM_ID' in pd:
        name = pd['LM_ID']
    else:
        name = 'undefined'

    return Compound(inchikey_id=pd['INCHI_KEY'] if 'INCHI_KEY' in pd else 'UNKNOWN_' + str(uuid.uuid4()),
                        systematic_name=pd['SYSTEMATIC_NAME'] if 'SYSTEMATIC_NAME' in pd else None,
                        pubchem_id=int(pd['PUBCHEM_CID']) if 'PUBCHEM_CID' in pd else None,
                        lmdb_id=pd['LM_ID'],
                        lbdb_id=pd['LIPIDBANK_ID'] if 'LIPIDBANK_ID' in pd else None,
                        kegg_id=pd['KEGG_ID'] if 'KEGG_ID' in pd else None,
                        hmdb_id=pd['HMDBID'] if 'HMDBID' in pd else None,
                        chebi_id=int(pd['CHEBI_ID']) if 'CHEBI_ID' in pd else None,

                        other_names=pd['SYNONYMS'] if 'SYNONYMS' in pd else None,
                        name=name,

                        category=pd['CATEGORY'] if 'CATEGORY' in pd else None,
                        compound_class=pd['MAIN_CLASS'] if 'MAIN_CLASS' in pd else None,
                        sub_class=pd['SUB_CLASS'] if 'SUB_CLASS' in pd else None,
                        molecular_formula=pd['FORMULA'] if 'FORMULA' in pd else None

                        )

