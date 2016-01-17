import sqlite3

# db navn Intervar.db
#tabeller:
#patient_info

#panels
#QC
#runs
#raw_variants
#interpretations
#alamut_annotations


def connect_to_db(db_name):
	conn = sqlite3.connect(db_name)
	c = conn.cursor()
    



def fill_db_with_mock_data():
	purchases = [('2006-03-28', 'BUY', 'IBM', 1000, 45.00),
             ('2006-04-05', 'BUY', 'MSFT', 1000, 72.00),
             ('2006-04-06', 'SELL', 'IBM', 500, 53.00),
            ]
    c.executemany('INSERT INTO stocks VALUES (?,?,?,?,?)', purchases)











