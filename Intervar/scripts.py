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



class VariantForm(Form):
    chrom = TextField("Chromosome name")
    start = TextField("Start position") #Finnes det numberfield??
    stop = TextField("Stop position")
    ref = TextField("Reference Allele")
    alt = TextField("Alternate Allele")
    submit = SubmitField("Submit to DB")
	
class SearchForm(Form):
    search = TextField("Search for Sample")

# Declare your table
class PatientTable(Table):
    PID = Col('Patient ID')
    clinInfo = Col('Clinical info')
    familyID = Col('Family ID')
    sex = Col('sex')
    classes = ['table table-striped']

class VariantTable(Table):
    chrom = Col('chrom')
    start = Col('start')
    stop = Col('stop')
    ref = Col('ref')
    alt = Col('alt')
    classes = ['table table-striped" id="test'] # make sortable like in the exac-page?

def dictFromCur(dbcursor, type):
    patient_dict = {}
    for i in dbcursor:
        if type == 'pID_patient':
            patient_dict = {"PID" : i[0], "clinInfo": i[1], "familyID" : i[2], "sex" : i[3], "panel_name" : i[4], "mean_target_cov" : i[5], "pct_target_20" : i[6], "pct_target_30": i[7], "median_is" : i[8], "mean_is" : i[9]}
    return patient_dict
            

def listOfdictsFromCur(dbcursor, type):
    """legge inn en IF saa man bruke denne til aa lage tabeller fra flere forskjellige sporringer
    I use a list of dicts for the tables, and for the single lines I simply export a single dict.

    """
    list_items = []
    for i in dbcursor:
        if type == 'patient_info':
            list_items.append(dict(PID=i[0], clinInfo=i[1], familyID=i[2], sex=i[3] ))
        elif type == 'int_variants':
            list_items.append(dict(chrom=i[0], start=i[1], stop=i[2], ref=i[3], alt=i[4]))
    return list_items
        
    

##DEV!
#metode for aa hente ut mean og median insert size:
#insertSizeMetrics.txt
#line 7, median == 0 (INT), mean 4 (REAL)
def insertsize_to_tuple(is_file, sample_name):
    istuple = (sample_name, )
    reader = csv.reader(open(is_file, 'r'), delimiter='\t')
    for count, line in enumerate(reader):
        if count == 7:
            istuple = istuple + (line[0],)
            istuple = istuple + (line[4],)
    return istuple

def get_values_from_form(type='first_input'):
    if type == 'first_input':
        form_tuple = (request.form['patient_ID'], request.form['familyID'], request.form['clinInfo'], request.form['sex'] )
    elif type == 'update':
        form_tuple = (request.form['familyID'], request.form['clinInfo'], request.form['sex'] )
    return form_tuple


def get_variants_from_form():
    variant_tuple = (request.form['chrom'], request.form['start'], request.form['stop'], request.form['ref'], request.form['alt'])
    return variant_tuple
	
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
    
def insert_data_is(cursor, table, tuple_with_data):
    c = cursor
    t = tuple_with_data
    try:
        c.execute("INSERT INTO " + table + " VALUES (?, ?, ?)", t)
    except Exception as e:
        raise e
    
    
def print_file(filename):
    reader = csv.reader(open(filename, 'r'))
    for i in reader:
        print(i)

