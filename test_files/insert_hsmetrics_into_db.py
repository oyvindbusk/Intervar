import csv
import os
import sqlite3

	
def insert_data(sqlite_file, table, tuple_with_data):
    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()
    t = tuple_with_data
    try:
        c.execute("INSERT INTO " + table + " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? )", t)
    except Exception as e:
        raise e
    finally:
        conn.commit()
        conn.close()


def hsmetrics_to_tuple(hsmfilepath):
    hsmetrics_csv_reader = csv.reader(open(hsmfilepath,'r'),delimiter='\t')
    sample_name = '{}_{}'.format(os.path.basename(hsmfilepath).split('_')[0],os.path.basename(hsmfilepath).split('_')[1])
    hsm_list = []
    for count,line in enumerate(hsmetrics_csv_reader):
        if count == 0:
            hsm_tuple = (sample_name,)
        elif count < 43:
            hsm_list.append(float(line[1]))
    hsm_tuple = hsm_tuple + tuple(hsm_list)
    return hsm_tuple

sqlite_file = 'test.sqlite'	
insert_data(sqlite_file, 'QC',hsmetrics_to_tuple('523_15_hsmetrix_out.txt'))
insert_data(sqlite_file, 'QC',hsmetrics_to_tuple('123_15_hsmetrix_out.txt'))
insert_data(sqlite_file, 'QC',hsmetrics_to_tuple('1123_15_hsmetrix_out.txt'))
insert_data(sqlite_file, 'QC',hsmetrics_to_tuple('1233_15_hsmetrix_out.txt'))
insert_data(sqlite_file, 'QC',hsmetrics_to_tuple('1023_15_hsmetrix_out.txt'))
insert_data(sqlite_file, 'QC',hsmetrics_to_tuple('1223_15_hsmetrix_out.txt'))