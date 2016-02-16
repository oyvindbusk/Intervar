import sqlite3
from flask.ext.wtf import Form
from wtforms import TextField, TextAreaField, SubmitField, FileField, SelectField, HiddenField, validators

from flask_table import Table, Col
from flask import g, request
import csv

################################################################################################################################################
class PatientForm(Form):
    patient_ID = TextField("Patient ID")
    sex = SelectField('Sex', choices=[('M', 'Male'),('F', 'Female')])
    panel = SelectField('Panel', choices=[('PV2-1', 'PV2-1'),('F', 'Filtex'), ('E', 'Exome')])
    clinInfo = TextAreaField("Clinical info")
    dis_category = SelectField('Disease category', choices=[('Atax', 'Ataxia'),('CMT', 'CMT'), ('EDS', 'EDS')])
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
    zyg = SelectField('Zygosity', choices=[('HOM', 'Homozygous'),('HET', 'Heterozygous'), ('HEM', 'Hemizygous')])
    denovo = SelectField('Denovo', choices=[('0','No'),('1','Yes')], default='0')
    submit = SubmitField("Submit to DB")
	
class SearchForm(Form):
    search = TextField("Search for Sample")

class Interpret_overallForm(Form):
    comment = TextAreaField("Comment")
    submit = SubmitField("Update")

class InterpretVariantForm(Form):
    comments = TextAreaField("Comments")
    varid = HiddenField("varid", default="testing")
    inhouse_class = SelectField('Inhouse Class', choices=[('1', '1'),('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')], default='3')
    acmg_class = SelectField('ACMG Class', choices=[('1', '1'),('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')], default='3')
    submit = SubmitField("Submit comment")

class PublicationsForm(Form):
    PMID = TextField("PMID")
    reference = TextField("Reference")
    year = TextField("Year")
    pcomment = TextAreaField("Comment")
    pub2varID = HiddenField("pub2varID") # to get the variant ID from the table to insert into the publications2variants-table
    submit = SubmitField("Submit publication")


# Declare your table
class PatientTable(Table):
    PID = Col('Patient ID')
    clinInfo = Col('Clinical info')
    familyID = Col('Family ID')
    sex = Col('sex')
    classes = ['table table-striped']

class VariantTable(Table): # add signed as a column
    ID = Col('ID')
    chrom = Col('chrom')
    start = Col('start')
    stop = Col('stop')
    ref = Col('ref')
    alt = Col('alt')
    zygosity = Col('Zygosity')
    gene = Col('gene')
    cDNA = Col('cDNA')
    protein = Col('protein')
    exacAll = Col('exacAllFreq')
    inclass = Col('inhouse_class')
    comments = Col('comments')
    signed = Col('Signed')
    classes = ['table table-striped"  id="variant_table'] # make sortable like in the exac-page?

################################################################################################################################################
def dictFromCur(dbcursor, type):
    patient_dict = {}
    for i in dbcursor:
        if type == 'pID_patient':
            patient_dict = {"PID" : i[0], "clinInfo": i[1], "familyID" : i[2], "sex" : i[3], "disease_category" : i[4],"panel_name" : i[5],   "mean_target_cov" : i[6], "pct_target_20" : i[7], "pct_target_30": i[8], "median_is" : i[9], "mean_is" : i[10]}
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
            list_items.append(dict(chrom=i[0], start=i[1], stop=i[2], ref=i[3], alt=i[4], zygosity=i[5], ID=i[6], gene=i[7], cDNA=i[8], protein=i[9], exacAll=i[10], inclass=i[11], comments=i[12], signed=i[13] ))
        elif type == 'int_variants_report':
            list_items.append(dict(chrom=i[0], start=i[1], stop=i[2], ref=i[3], alt=i[4], zygosity=i[5], ID=i[6], gene=i[7], cDNA=i[8], protein=i[9], exacAll=i[10], clinVarPhenotypes=i[11], inclass=i[12], comments=i[13], signed=i[14] ))

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
        form_tuple = (request.form['patient_ID'], request.form['familyID'], request.form['clinInfo'], request.form['sex'], request.form['panel'], request.form['dis_category'] )
    return form_tuple

def get_variants_from_form():
    variant_tuple = (request.form['chrom'], request.form['start'], request.form['stop'], request.form['ref'], request.form['alt'], request.form['zyg'], request.form['denovo'])
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
        
def alamut_dict_to_DB(ala_dict, pID):
    '''
    A dictionary requested from Alamut via Ajax JSON is inserted into the SQLITE db.
    fields:
    	
    '''
    #establish connection to db
    #make a tuple from dict including pID
    new_tuple = ()
    new_dict = {}
    for k, v in ala_dict.iteritems():
        if k in ["gene", "geneId"]:
            if k in ["geneId", "gDNAstart", "gDNAend", "cDNAstart", "cDNAend", "exon", "intron", "omimId", "distNearestSS", "rsValidationNumber", "rsMAFCount", "exacAlleleCount", "espRefEACount", "espRefAACount", "espRefAllCount", "espAltEACount", "espAltAACount", "espAltAllCount", "hgmdPubMedId", "clinVarReviewStatus", "posAA", "nOrthos", "conservedOrthos", "BLOSUM45", "BLOSUM62", "BLOSUM80", "wtAAcomposition", "wtAAvolume", "varAAvolume", "granthamDist", "SIFTweight"]:
                try:
                    new_dict[k] = int(v)
                    new_tuple = new_tuple + (int(v),)
                except:
                    new_dict[k] = v
                    new_tuple + (v,)
            elif k in ["wtSSFScore", "wtMaxEntScore", "wtNNSScore", "wtGSScore", "wtHSFScore", "varSSFScore", "varMaxEntScore", "varNNSScore", "varGSScore", "varHSFScore", "nearestSSChange", "rsHeterozygosity", "rsMAF", "exacAllFreq", "exacAFRFreq", "exacAMRFreq", "exacEASFreq", "exacSASFreq", "exacNFEFreq", "exacFINFreq", "exacOTHFreq", "espEAMAF", "espAAMAF", "espAllMAF", "espEAAAF", "espAAAAF", "espAllAAF", "phastCons", "phyloP", "wtCodonFreq", "varCodonFreq", "varAAcomposition", "wtAApolarity", "varAApolarity", "AGVGDgv", "AGVGDgd", "SIFTmedian", "PPH2score", "MAPPpValue", "MAPPpValueMedian", "TASTERpValue"]:
                try:
                    new_dict[k] = float(v)
                    new_tuple + (float(v),)
                except:
                    new_dict[k] = v
                    new_tuple + (v,)
            else:
                new_dict[k] = v
                new_tuple = new_tuple + (v,)
    print(new_dict)
    print(new_tuple)
    print(ala_tup)
    ala_tup = [('gene', 'MLH1'), ('geneId', 7127)]
         #   print(i)
    cur.execute("INSERT INTO alamut_annotation \
    (gene, geneId)\
    VALUES (?,?) \
    ", new_tuple)
    db.commit()
    db.close()
    
    
	
def str_to_int_float(input, type):
    output = None
    if type == 'int':
        try:
            output = int(input)
        except:
            output = str(input)
    if type == 'float': 
        try:
            output = float(input)
        except:
            output = str(input)
    return output
