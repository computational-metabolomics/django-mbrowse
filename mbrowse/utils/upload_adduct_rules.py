import csv
from mbrowse.models import AdductRule

def upload_adduct_rules(addduct_rule_file):

    addr = list(AdductRule.objects.filter().values('adduct_type', 'id'))
    if len(addr) > 0:
        addrd = {a['adduct_type']: a['id'] for a in addr}
    else:
        addrd = {}

    ruleset_d = {}

    reader = csv.DictReader(addduct_rule_file)
    for row in reader:
        if row['name'] not in addrd:
            arulei = AdductRule(adduct_type=row['name'],
                                nmol=row['nmol'],
                                charge=row['charge'],
                                massdiff=row['massdiff'],
                                oidscore=row['oidscore'],
                                quasi=row['quasi'],
                                ips=row['ips'],
                                frag_score=row['frag_score'] if 'frag_score' in row.keys() else None
                                )
            arulei.save()
            ruleset_d[row['rule_id']] = arulei.id
        else:
            ruleset_d[row['rule_id']] = addrd[row['name']]

    return ruleset_d
