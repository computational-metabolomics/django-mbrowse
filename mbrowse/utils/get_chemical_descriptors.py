import requests
import pubchempy as pcp
from rdkit.Chem import Descriptors
from rdkit.Chem import Descriptors3D
from rdkit import Chem
import six
import re
import csv
import os

def run_all_functions_in_module(module, mol, skip_funcs=None, skip_starts_with='_'):
    descriptors = {}
    if skip_funcs is None:
        skip_funcs = []

    for name, val in six.iteritems(module.__dict__):
        if callable(val) and not name.startswith(skip_starts_with) and not name in skip_funcs:
            try:
                descriptors[name] = val(mol)
            except AttributeError as e:
                print(e)
                descriptors[name] = ''
            except ValueError as e:
                print(e)
                descriptors[name] = ''
            except:
                descriptors[name] = ''


    return descriptors


def get_kegg_chemical_descriptors():

    url_list = 'http://rest.kegg.jp/list/compound'

    resp = requests.get(url_list)

    cont = resp.content
    rows = cont.decode("utf-8").split('\n')

    kegg_compounds = []

    d = get_descriptors('C00001')
    fieldnames = ['name', 'names', 'pathway', 'kegg_cid', 'brite', 'brite_first_level', 'brite_second_level', 'brite_third_level']
    fieldnames.extend(list(d))
    go =False
    with open('kegg_descriptors.csv', 'a') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for i, row in enumerate(rows):
            entry = row.split('\t')

            cid = entry[0].split(':')[1]
            print(i, cid)
            names = entry[1]
            name = entry[1].split(';')[0]

            kegg_compound = get_kegg_row(cid, name, names)
            # kegg_compounds.append(kegg_compound)
            writer.writerow(kegg_compound)


def get_kegg_row(cid, name='', names=''):


    kegg_compound = {}

    url_get = 'http://rest.kegg.jp/get/{}'.format(cid)
    resp_get = requests.get(url_get)
    all_cont = resp_get.content

    kegg_compound['kegg_cid'] = cid
    kegg_compound['brite'] = ''
    kegg_compound['brite_first_level'] = ''
    kegg_compound['brite_second_level'] = ''
    kegg_compound['brite_third_level'] = ''
    kegg_compound['pathway'] = False
    kegg_compound['name'] = name
    kegg_compound['names'] = names

    for detail in all_cont.decode("utf-8").split('\n'):
        mtch = re.search('^NAME(?::|\s)(.*)', detail)
        if mtch:
            kegg_compound['name'] = mtch.group(1).strip() if not kegg_compound['name'] else ''


        mtch = re.search('^PATHWAY(?::|\s)(.*)', detail)
        if mtch:
            kegg_compound['pathway'] = True

        mtch = re.search('^BRITE(?::|\s)(.*)', detail)
        if mtch:
            kegg_compound['brite'] = mtch.group(1).strip()
            continue

        if kegg_compound['brite'] and not kegg_compound['brite_first_level']:
            kegg_compound['brite_first_level'] = detail.strip()
        elif kegg_compound['brite'] and kegg_compound['brite_first_level'] and not kegg_compound['brite_second_level']:
            kegg_compound['brite_second_level'] = detail.strip()
        elif kegg_compound['brite'] and kegg_compound['brite_first_level'] and \
                kegg_compound['brite_second_level'] and not kegg_compound['brite_third_level']:
            kegg_compound['brite_third_level'] = detail.strip()

    kegg_compound.update(get_descriptors(cid))

    return kegg_compound


def get_descriptors(cid):

    url_get = 'http://rest.kegg.jp/get/{}/mol/'.format(cid)
    resp = requests.get(url_get)
    all_cont = resp.content

    mol = Chem.MolFromMolBlock(all_cont)

    d = run_all_functions_in_module(Descriptors, mol, ['PropertyFunctor'],'_')
    d.update(run_all_functions_in_module(Descriptors3D, mol, None, '_'))

    return d



def get_descriptors_pubchem(cid):
    c = pcp.get_compounds(cid)

    if not c:
        return 0

    sdf_pth = 'data/{}.sdf'.format(cid)

    if not os.path.exists(sdf_pth):
        pcp.download('SDF', sdf_pth, cid, 'cid')

    suppl = Chem.SDMolSupplier(sdf_pth)

    mol = next(suppl)

    d = run_all_functions_in_module(Descriptors, mol, ['PropertyFunctor'],'_')
    d.update(run_all_functions_in_module(Descriptors3D, mol, None, '_'))

    return d



def get_annotation_result_descriptors(filepth):
    print(filepth)

    ############################
    # Need to update kegg id to
    #############################

    # loop through the annotation output file path
    compounds = {}

    d_blank = {'name': '', 'names': '', 'pathway': '', 'kegg_cid': '', 'pubchem_id':'',
     'brite': '', 'brite_first_level': '', 'brite_second_level': '',
     'brite_third_level': '', 'rank': ''}

    d_blank.update(get_descriptors('C00001'))
    d_blank = d_blank.fromkeys(d_blank, '')







    with open(filepth, 'r') as csvfile:
        reader = csv.DictReader(csvfile)

        for i, row in enumerate(reader):
            print(i)
            cmp_nme = row['Compound name']
            # check if compound in the compound dict already
            if cmp_nme in compounds:
                if int(row['Rank']) > compounds[cmp_nme]['rank']:
                    compounds[cmp_nme]['rank'] = int(row['Rank'])
                continue

            if row['KEGG cid(s)'] and not row['KEGG cid(s)'] == 'NA':

                cid = row['KEGG cid(s)'].replace('"', '').replace("'","").split(',')[0]
                compounds[cmp_nme] = get_kegg_row(cid)

            elif row['PubChem cid(s)'] and not row['PubChem cid(s)'] == 'NA':

                cid = row['PubChem cid(s)'].replace('"', '').replace("'", "").split(',')[0]

                compounds[cmp_nme] = get_descriptors_pubchem(cid)
                compounds[cmp_nme]['pubchem_id'] = cid

            else:
                compounds[cmp_nme] = d_blank

            compounds[cmp_nme]['rank'] = int(row['Rank'])


    with open('exp_descriptors.csv', 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=list(d_blank))
        writer.writeheader()
        for cmp_nme, row in six.iteritems(compounds):
            row['name'] = cmp_nme
            writer.writerow(row)

    # get unique annotations

    # get either KEGG id, or a PubChem ID

    # get a mol file

    # get descriptors

    # output to