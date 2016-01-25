import sqlite3
from flask.ext.wtf import Form
from wtforms import TextField, TextAreaField, SubmitField, FileField, SelectField, validators

from flask_table import Table, Col
from flask import g
import csv
# db navn Intervar.sqlite
#tabeller:
#patient_info

#panels
#QC
#runs
#raw_variants
#interpretations
#alamut_annotations


#patient form

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

def print_file(filename):
	reader = csv.reader(open(filename, 'r'))
	for i in reader:
		print(i)

