import sqlite3
from flask.ext.wtf import Form
from wtforms import TextField, TextAreaField, SubmitField, FileField, SelectField, validators

from flask_table import Table, Col
from flask import g
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
    clinInfo = TextAreaField("Clinical info")
    familyID = TextField('Family ID')
    hsmFileUpload = FileField("Hsmetrics file")
    submit = SubmitField("Submit")
    


# Declare your table
class ItemTable(Table):
    PID = Col('Patient ID')
    clinInfo = Col('Clinical info')
    familyID = Col('Family ID')
    sex = Col('sex')
    classes = ['table table-striped']


def dictFromCur(dbcursor):
	items = []
	for i in dbcursor:
		items.append(dict(PID=i[0], clinInfo=i[1], familyID=i[2], sex=i[3]))
	return items
	
