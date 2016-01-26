import csv
import os
import sqlite3

	
def insert_data(cursor, table, tuple_with_data):
    #conn = sqlite3.connect(sqlite_file)
    c = cursor
    t = tuple_with_data
    try:
        c.execute("INSERT INTO " + table + " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? )", t)
    except Exception as e:
        raise e
    finally:
        conn.commit()
        conn.close()




sqlite_file = 'test.sqlite'	
insert_data(sqlite_file, 'QC',hsmetrics_to_tuple('523_15_hsmetrix_out.txt'))
insert_data(sqlite_file, 'QC',hsmetrics_to_tuple('123_15_hsmetrix_out.txt'))
insert_data(sqlite_file, 'QC',hsmetrics_to_tuple('1123_15_hsmetrix_out.txt'))
insert_data(sqlite_file, 'QC',hsmetrics_to_tuple('1233_15_hsmetrix_out.txt'))
insert_data(sqlite_file, 'QC',hsmetrics_to_tuple('1023_15_hsmetrix_out.txt'))
insert_data(sqlite_file, 'QC',hsmetrics_to_tuple('1223_15_hsmetrix_out.txt'))