import sqlite3
from flask.ext.wtf import Form
from wtforms import TextField, TextAreaField, SubmitField, FileField, SelectField, validators

from flask_table import Table, Col
from flask import g, request
import csv
# db navn Intervar.sqlite


class PatientForm(Form):
    patient_ID = TextField("Patient ID")
    sex = SelectField('Sex', choices=[('M', 'Male'),('F', 'Female')])
    panel = SelectField('Panel', choices=[('PV2-1', 'PV2-1'),('F', 'Filtex'), ('E', 'Exome')])
    clinInfo = TextAreaField("Clinical info")
    familyID = TextField('Family ID')
    hsmFileUpload = FileField("Hsmetrics file")
    fragmentSizeUpload = FileField("Fragment size file")
    submit = SubmitField("Submit")

# Declare your table
class PatientTable(Table):
    PID = Col('Patient ID')
    clinInfo = Col('Clinical info')
    familyID = Col('Family ID')
    sex = Col('sex')
    classes = ['table table-striped']

class VariantTable(Table):
    chrom = Col('Chrom')
    start = Col('start')
    stop = Col('stop')
    ref = Col('ref')
    alt = Col('alt')
    inhouse_class = Col('Class')
    classes = ['table table-striped'] # make sortable like in the exac-page?


def dictFromCur(dbcursor, type):
	#legge inn en IF saa man bruke denne til aa lage tabeller fra flere forskjellige sporringer
	items = []
	for i in dbcursor:
		if type == 'patient_info':
			items.append(dict(PID=i[0], clinInfo=i[1], familyID=i[2], sex=i[3]))
		elif type == 'int_variants':
			items.append(dict(chrom=i[0], start=i[1], stop=i[2], ref=i[3], alt=i[4], inhouse_class=i[5]))
	return items

##DEV!
#metode for aa hente ut mean og median insert size:
#insertSizeMetrics.txt
#line 7, median == 0 (INT), mean 4 (REAL)
def insertsize_to_db(is_file):
    median_is = 0
    mean_is = 0
    reader = csv.reader(open(is_file, 'r'), delimiter='\t')
    for count, line in enumerate(reader):
        if count == 7:
            median_is = line[0]
            mean_is = line[4]
    return median_is, mean_is

def get_values_from_form():
    form_tuple = (request.form['patient_ID'], request.form['familyID'], request.form['clinInfo'], request.form['sex'] )
    return form_tuple
	
#get info from hsmetrics-file into tuple (exluding sample name)
def hsmetrics_to_tuple(hsmfilepath, sample_name):
    hsmetrics_csv_reader = csv.reader(open(hsmfilepath,'r'),delimiter='\t')
    hsm_list = []
    hsm_tuple = ()
    for count,line in enumerate(hsmetrics_csv_reader):
        if count == 0:
            hsm_tuple = (sample_name,)
        elif count < 43:
            hsm_list.append(float(line[1]))
    hsm_tuple = hsm_tuple + tuple(hsm_list)
    return hsm_tuple

def insert_data(cursor, table, tuple_with_data):
    c = cursor
    t = tuple_with_data
    try:
        c.execute("INSERT INTO " + table + " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? )", t)
    except Exception as e:
        raise e
    

	
def print_file(filename):
	reader = csv.reader(open(filename, 'r'))
	for i in reader:
		print(i)

