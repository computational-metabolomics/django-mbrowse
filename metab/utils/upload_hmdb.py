import re
import pubchempy as pcp
from metab.models import Compound
import uuid
from rdkit import Chem
from django.utils.encoding import force_text

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



def get_hmdb_info(sdf_pth):


    suppl = Chem.SDMolSupplier(sdf_pth)

    new_comps = []
    c= 0
    for i, mol in enumerate(suppl):
        if i<41000:
            continue
        # print row
        if not mol:
            continue
        pd = mol.GetPropsAsDict()
        pd = string_compat(pd)

        if not 'INCHI_KEY' in pd:
            new_comp = create_hmdb_compound(pd)
            new_comps.append(new_comp)
            continue

        mtchs = Compound.objects.filter(inchikey_id=pd['INCHI_KEY'])

        if i % 1000 == 0:
            print i, pd


        if c <= 1:
            # can only do 1 at a time due to inchi key collisions
            Compound.objects.bulk_create(new_comps)
            c = 0
            new_comps = []

        if mtchs:

            # if mtchs[0].kegg_id==kegg_c['kegg_cid']:
            #     continue
            mtch_compound = mtchs[0]
            if 'HMDB_ID' in pd:
                if not mtch_compound.hmdb_id:
                    mtch_compound.hmdb_id = pd['HMDB_ID']
                elif not re.match('(^|,){}(,|$)'.format(pd['HMDB_ID']), mtch_compound.hmdb_id):
                    mtch_compound.hmdb_id = '{},{}'.format(mtch_compound.hmdb_id, pd['HMDB_ID'])

            mtch_compound.save()


        else:

            new_comp = create_hmdb_compound(pd)
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

def create_hmdb_compound(pd):

    if 'GENERIC_NAME' in pd:
        name = pd['GENERIC_NAME']
    elif 'JCHEM_TRADITIONAL_IUPAC' in pd:
        name = pd['JCHEM_TRADITIONAL_IUPAC']
    else:
        name = ''


    return Compound(inchikey_id=pd['INCHI_KEY'] if 'INCHI_KEY' in pd else 'UNKNOWN_' + str(uuid.uuid4()),
                        hmdb_id=pd['HMDB_ID'] if 'HMDB_ID' in pd else None,


                        other_names=pd['SYNONYMS'].encode('ascii', 'ignore').decode('ascii') if 'SYNONYMS' in pd else None,
                        name=name,
                        exact_mass=pd['EXACT_MASS'] if 'EXACT_MASS' in pd else None,
                        molecular_weight=pd['MOLECULAR_WEIGHT'] if 'MOLECULAR_WEIGHT' in pd else None,

                        smiles=pd['SMILES'] if 'SMILES' in pd else None,

                        molecular_formula=pd['FORMULA'] if 'FORMULA' in pd else None

                        )

