from __future__ import print_function
from django.db import connection
from sqlite3 import OperationalError


def insert_query_m(data, table, columns=None):

    if len(data)>10000:
        chunk_query(data, 10000, columns, table)
    else:
        type = "%s, " * (len(data[0]) - 1)
        type = type + "%s"

        if columns:
            stmt = "INSERT INTO " + table + "( " + columns + ") VALUES (" + type + ")"
        else:
            stmt = "INSERT INTO " + table + " VALUES (" + type + ")"

        print(stmt)

        cursor = connection.cursor()
        cursor.executemany(stmt, data)
        connection.commit()


def chunk_query(l, n, cn, name):
    # For item i in a range that is a length of l,
    [insert_query_m(l[i:i+n], name, cn) for i in range(0, len(l), n)]


def sql_query(query):
    with connection.cursor() as cursor:
        cursor.execute(query)
        columns = [i[0] for i in cursor.description]
        rows = cursor.fetchall()

    return rows, columns


def get_current_row(model):
    # get last id of LipidSearchSampleGroup
    m = model.objects.filter().order_by('-id')
    if m:
        id = m[0].id + 1
    else:
        id = 1

    return id



def select_query(stmt):

    cursor = connection.cursor()
    cursor.execute(stmt)
    connection.commit()
    return [i for i in cursor]


def sql_column_names(cursor):
    names = {}
    c = 0
    for description in cursor.description:
        names[description[0]] = c
        c += 1

    return names

def check_table_exists_sqlite(cursor, tablename):
    #https://stackoverflow.com/questions/17044259/python-how-to-check-if-table-exists
    try:
        qry =cursor.execute("SELECT NULL FROM {} LIMIT 1".format(tablename))
    except OperationalError as e:
        return False

    return True

