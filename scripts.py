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
    dis_category = SelectField('Disease category', choices=[('Atax', 'Ataxia'),('CMT', 'CMT'), ('EDS', 'EDS'), ('APN', 'APN'), ('HSP', 'HSP'), ('Noonan_Marfan', 'Noonan Marfan'), ('Skeletal', 'Skeletal'), ('ALS', 'ALS'), ('NF', 'NF')])
    familyID = TextField('Family ID')
    hsmFileUpload = FileField("Hsmetrics file")
    fragmentSizeUpload = FileField("Fragment size file")
    sbs_run = TextField("SBS")
    submit = SubmitField("Submit")

class VariantForm(Form):
    chrom = TextField("Chromosome name")
    start = TextField("Start position") #Finnes det numberfield??
    stop = TextField("Stop position")
    ref = TextField("Reference Allele")
    alt = TextField("Alternate Allele")
    zyg = SelectField('Zygosity', default='HET', choices=[('HOM', 'Homozygous'), ('HET', 'Heterozygous'), ('HEM', 'Hemizygous')])
    denovo = SelectField('Denovo', default='null', choices=[('0','No'),('1','Yes'), ('null', 'Undetermined')])
    combo = TextField('Combofield')
    submit = SubmitField("Submit to DB")

class polyphenForm(Form):
    polyphen = SelectField('Polyphen prediction', default='null', choices=[('probd', 'Probably damaging'), ('possd', 'Possibly damaging'), ('B', 'Bening'), ('null', 'Undetermined')])
    variant_id = TextField('variant_id')
    submit = SubmitField("Submit Polyphen")

class deleteVariantForm(Form):
    hidden_variant_ID = HiddenField("Hidden variant field")
    submit = SubmitField("Delete variant")

class SearchForm(Form):
    search = TextField("Search for Sample")

class Interpret_overallForm(Form):
    comment = TextAreaField("Comment")
    filtus_settings = TextAreaField("Filtus settings")
    submit = SubmitField("Update")

class InterpretVariantForm(Form):
    comments = TextAreaField("Comments")
    varid = HiddenField("varid", default="testing")
    inhouse_class = SelectField('Inhouse Class', choices=[('1', '1'),('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('0', '0'), ('6', 'Not considered')], default='3')
    acmg_class = SelectField('ACMG Class', choices=[('1', '1'),('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')], default='3')
    submit = SubmitField("Submit comment/class")

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
    concat = Col('Sample;dis;class')
    denovo = Col('denovo')
    classes = ['table table-striped" id="variant_table'] # make sortable like in the exac-page?

class SampleOverviewTable(Table):
    sbs = Col('SBS')
    panel = Col('panel')
    sample_count = Col('Sample count')
    mean_cov = Col('Mean Coverage')
    classes = ['table table-striped" id="overview_table']

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
            list_items.append(dict(chrom=i[0], start=i[1], stop=i[2], ref=i[3], alt=i[4], zygosity=i[5], denovo=i[6], ID=i[7], gene=i[8], cDNA=i[9], protein=i[10], exacAll=i[11], inclass=i[12], comments=i[13], signed=i[14], concat=i[15] ))
        elif type == 'int_variants_report':
            list_items.append(dict(chrom=i[0], start=i[1], stop=i[2], ref=i[3], alt=i[4], zygosity=i[5], denovo=i[6], ID=i[7], gene=i[8], gDNA=i[9], cDNA=i[10], protein=i[11], exacAll=i[12], clinVarPhenotypes=i[13], clinVarClinSignifs=i[14], transcript=i[15], codingEffect=i[16], hgmdId=i[17], hgmdPhenotype=i[18], varLocation=i[19], localSpliceEffect=i[20], rsClinicalSignificance=i[21], exacNFEFreq=i[22], espEAMAF=i[23], espAltEACount=i[24] , espRefEACount=i[25], conservedOrthos=i[26], AGVGDclass=i[27], SIFTprediction=i[28],TASTERprediction=i[29], exons=i[30], rsId=i[31], wtMaxEntScore=i[32], varMaxEntScore=i[33], wtNNSScore=i[34], varNNSScore=i[35], wtHSFScore=i[36], varHSFScore=i[37], interp_ID=i[38], inclass=i[39], acmg_class=i[40], interpretor=i[41], comments=i[42], signed=i[43], publications=i[44], concat=i[45] ))

        elif type == 'overview_table':
            list_items.append(dict(sbs=i[0], panel=i[1], sample_count=i[2], mean_cov=i[3] ))

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
        form_tuple = (request.form['patient_ID'], request.form['familyID'], request.form['clinInfo'], request.form['sex'], request.form['panel'], request.form['dis_category'], request.form['sbs_run'] )
    return form_tuple

def get_variants_from_form(type):
    if type == 'regular':
        variant_tuple = (request.form['chrom'], request.form['start'], request.form['stop'], request.form['ref'], request.form['alt'], request.form['zyg'], request.form['denovo'])
    elif type == 'combo':
        variant_tuple = (request.form['combo'].split()[0], request.form['combo'].split()[1], request.form['combo'].split()[2], request.form['combo'].split()[3], request.form['combo'].split()[4], request.form['zyg'], request.form['denovo'])
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
