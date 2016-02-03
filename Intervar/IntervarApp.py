from flask import Flask, render_template, request, abort, redirect, url_for, flash, g, send_from_directory, jsonify
from flask.ext.login import LoginManager, UserMixin, login_user, logout_user, login_required
from flask.ext.sqlalchemy import SQLAlchemy
import os
import sqlite3
from werkzeug import secure_filename
#importere egne scripts
from scripts import PatientForm, VariantForm, SearchForm, PatientTable, VariantTable, listOfdictsFromCur, dictFromCur, print_file, hsmetrics_to_tuple, insert_data, get_values_from_form, insertsize_to_tuple, insert_data_is, get_variants_from_form
from scripts import alamut_dict_to_DB, str_to_int_float
import json

DEBUG = True
SECRET_KEY = 'yekterces'
SQLALCHEMY_DATABASE_URI = 'sqlite:///db/users.db'

app = Flask(__name__)
app.config.from_object(__name__)
UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = set(['txt', 'csv'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

login_manager = LoginManager(app)
login_manager.init_app(app)
login_manager.login_view = 'login'


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

DATABASE = 'Intervar.sqlite'
def connect_to_database():
    return sqlite3.connect(DATABASE)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connect_to_database()
    return db
    
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

db = SQLAlchemy(app)
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String)
    password = db.Column(db.String)

@login_manager.user_loader
def user_loader(user_id):
    user = User.query.filter_by(id=user_id)
    if user.count() == 1:
        return user.one()
    return None

@app.before_first_request
def init_request():
    db.create_all()
    

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    elif request.method == 'POST':
        username = request.form['txtUsername']
        password = request.form['txtPassword']

        user = User.query.filter_by(username=username)
        if user.count() == 0:
            user = User(username=username, password=password)
            db.session.add(user)
            db.session.commit()

            flash('You have registered the username {0}. Please login'.format(username))
            return redirect(url_for('login'))
        else:
            flash('The username {0} is already in use.  Please try a new username.'.format(username))
            return redirect(url_for('register'))
    else:
        abort(405)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html', next=request.args.get('next'))
    elif request.method == 'POST':
        username = request.form['txtUsername']
        password = request.form['txtPassword']

        user = User.query.filter_by(username=username).filter_by(password=password)
        if user.count() == 1:
            login_user(user.one())
            flash('Welcome back {0}'.format(username))
            try:
                next = request.form['next']
                return redirect(next)
            except:
                return redirect(url_for('index'))
        else:
            flash('Invalid login')
            return redirect(url_for('login'))
    else:
        return abort(405)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/testinput', methods=['GET', 'POST'])
@login_required
def testinput():
    form = PatientForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            db = get_db()
            cur = get_db().cursor()
            patient_form_tuple = get_values_from_form()
            cur.execute("INSERT INTO patient_info (patient_ID, family_ID, clinical_info,  sex) VALUES (?, ?, ?, ?)", patient_form_tuple )
            hsm_file = request.files['hsmFileUpload']
            if hsm_file and allowed_file(hsm_file.filename):
                filename = secure_filename(hsm_file.filename)
                hsm_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                insert_data(cur, 'QC', hsmetrics_to_tuple(os.path.join(app.config['UPLOAD_FOLDER'], filename), patient_form_tuple[0]))
            #upload insertsizemetrics-file:
            is_file = request.files['fragmentSizeUpload']
            if is_file and allowed_file(is_file.filename):
                is_filename = secure_filename(is_file.filename)
                is_file.save(os.path.join(app.config['UPLOAD_FOLDER'], patient_form_tuple[0] + "_" + is_filename))
                insert_data_is(cur, 'insert_size', insertsize_to_tuple(os.path.join(app.config['UPLOAD_FOLDER'], is_filename), patient_form_tuple[0]))
                #insert_data_is(cur, )
                # maa oppdatere databasen first
            db.commit()
            db.close()
            return "Suksess"
            #flash('Suksess!!')
        else:
            return abort(404)
    elif request.method == "GET":
        return render_template('testinput.html', form=form)

		
@app.route('/overview')
@login_required
def overview():
    return render_template('overview.html')


################################################################################################################################################
@app.route('/interpret', methods=['GET', 'POST'])
@login_required
def interpret(pID="123_15"):
    form = SearchForm()
    if request.method == "POST":
        db = get_db()
        cur = get_db().cursor()
		#return redirect(url_for('showdb', pID=request.form['search']))
        alamut_dict = request.get_json(force=True)
        #alamut_dict = {u'substType': u'transversion', u'nearestSSType': u"3'", u'varCodonFreq': u'0.082', u'clinVarMethods': u'research', u'varGSScore': u'1.53641', u'varLocation': u'exon', u'espAltEACount': u'', u'espRefAACount': u'', u'hgmdId': u'CM053325', u'espRefAllCount': u'', u'espAAAAF': u'', u'exacAllFreq': u'', u'intron': u'', u'SIFTprediction': u'Deleterious', u'exacNFEFreq': u'', u'cDNAend': u'464', u'conservedOrthos': u'14', u'rsMAF': u'0.000', u'exacAlleleCount': u'', u'PPH2prediction': u'', u'phyloP': u'6.932', u'exacQuality': u'', u'MAPPprediction': u'bad', u'cNomen': u'c.464T>G', u'PPH2class': u'', u'exon': u'6', u'alt_pNomen': u'p.Leu155Arg', u'chrom': u'3', u'hgmdPhenotype': u'Colorectal cancer, non-polyposis', u'strand': u'1', u'exacAMRFreq': u'', u'espRefEACount': u'', u'rsValidations': u'', u'pNomen': u'p.Leu155Arg', u'clinVarOrigins': u'germline', u'AGVGDclass': u'C65', u'BLOSUM45': u'-2', u'hgmdSubCategory': u'DM', u'exacOTHFreq': u'', u'wtNNSScore': u'0.798934', u'nearestSSChange': u'0.013785', u'varHSFScore': u'93.59', u'PPH2score': u'', u'posAA': u'155', u'nucChange': u'T>G', u'espAltAllCount': u'', u'rsMAFAllele': u'', u'gDNAend': u'37008824', u'varType': u'substitution', u'MAPPpValueMedian': u'8', u'wtAA_1': u'L', u'rsMAFCount': u'0', u'wtAA_3': u'Leu', u'distNearestSS': u'11', u'varCodon': u'CGT', u'clinVarReviewStatus': u'3', u'assembly': u'GRCh38', u'varSSFScore': u'87.3907', u'rsValidationNumber': u'0', u'Uniprot': u'P40692', u'cDNAstart': u'464', u'wtSSFScore': u'87.3907', u'gNomen': u'g.37008824T>G', u'espEAAAF': u'', u'varNuc': u'G', u'wtMaxEntScore': u'6.39207', u'TASTERprediction': u'', u'gene': u'MLH1', u'proteinDomain4': u'', u'proteinDomain1': u'DNA mismatch repair protein family', u'proteinDomain3': u'', u'proteinDomain2': u'Histidine kinase-like ATPase, C-terminal domain', u'varAApolarity': u'10.5', u'AGVGDgd': u'101.88', u'espAAMAF': u'', u'cosmicTissues': u'', u'AGVGDgv': u'0.00', u'wtNuc': u'T', u'omimId': u'120436', u'SIFTmedian': u'3.43', u'wtAAcomposition': u'0', u'exacDP': u'', u'rsHeterozygosity': u'0.000', u'wtHSFScore': u'93.59', u'hgmdWebLink': u'https://portal.biobase-international.com/hgmd/pro/mut.php?accession=CM053325', u'exacSASFreq': u'', u'espAltAACount': u'', u'varMaxEntScore': u'6.39207', u'exacFilter': u'', u'BLOSUM80': u'-4', u'clinVarPhenotypes': u'Lynch syndrome', u'pathogenicityClass': u'Class 3-Unknown pathogenicity', u'exacAFRFreq': u'', u'cosmicIds': u'', u'granthamDist': u'102', u'localSpliceEffect': u'', u'MAPPpValue': u'1,243E-5', u'codingEffect': u'missense', u'rsClinicalSignificance': u'pathogenic', u'nOrthos': u'14', u'varAAcomposition': u'0.65', u'espAllMAF': u'', u'gDNAstart': u'37008824', u'espAvgReadDepth': u'', u'protein': u'NP_000240.1', u'exacEASFreq': u'', u'wtCodon': u'CTT', u'wtCodonFreq': u'0.129', u'wtAApolarity': u'4.9', u'varAAvolume': u'124', u'wtGSScore': u'', u'rsSuspect': u'no', u'geneId': u'7127', u'varNNSScore': u'0.831974', u'clinVarClinSignifs': u'Pathogenic', u'SIFTweight': u'0', u'espEAMAF': u'', u'TASTERpValue': u'', u'hgmdPubMedId': u'16083711', u'rsId': u'rs63750891', u'phastCons': u'1.000', u'wtAAvolume': u'111', u'transcript': u'NM_000249.2', u'rsValidated': u'no', u'rsAncestralAllele': u'T', u'exacFINFreq': u'', u'clinVarIds': u'RCV000075730.2', u'conservedDistSpecies': u'Trichoplax adhaerens', u'varAA_3': u'Arg', u'varAA_1': u'R', u'espAllAAF': u'', u'BLOSUM62': u'-2'}
        print(alamut_dict)
        
		#sette inn metode som henter fra dict og sette inn i DB.
        new_tuple = ('transversion', 'research', 'exon', 'CM053325', 'Deleterious', 464, 14, '', '', 'bad', 'c.464T>G', '', 6, 'p.Leu155Arg', '3', 'Colorectal cancer, non-polyposis', '1', '', 'p.Leu155Arg', 'germline', 'C65', -2, 'DM', 155, 'T>G', '', 37008824, 'substitution', 'L', 0, 'Leu', 11, 'CGT', 3, 'GRCh38', 0, 'P40692', 464, 'g.37008824T>G', 'G', '', 'MLH1', '', 'DNA mismatch repair protein family', '', 'Histidine kinase-like ATPase, C-terminal domain', '', 'T', 120436, 0, '', 'https://portal.biobase-international.com/hgmd/pro/mut.php?accession=CM053325', '', -4, 'Lynch syndrome', 'Class 3-Unknown pathogenicity', '', 102, '', 'missense', 'pathogenic', 14, 37008824, '', 'NP_000240.1', 'CTT', 124, 'no', 7127, 'Pathogenic', 0, 16083711, 'rs63750891', 111, 'NM_000249.2', 'no', 'T', 'RCV000075730.2', 'Trichoplax adhaerens', 'Arg', 'R', -2)
        test_tuple = ('transversion', 'research', 'exon', '', 3, 37008824, 37008824, 'T', 'G')
        # removed nearestsstype since it contained the prime symbol"'", which fucked up things.

        cur.execute("INSERT INTO alamut_annotation (geneId, strand, gDNAstart, gDNAend, cDNAstart, cDNAend, exon, intron, omimId, distNearestSS, rsValidationNumber, rsMAFCount, exacAlleleCount, espRefEACount, espRefAACount, espRefAllCount, espAltEACount, espAltAACount, espAltAllCount, hgmdPubMedId, clinVarReviewStatus, posAA, nOrthos, conservedOrthos, BLOSUM45, BLOSUM62, BLOSUM80, wtAAcomposition, wtAAvolume, varAAvolume, granthamDist, SIFTweight, wtSSFScore, wtMaxEntScore, wtNNSScore, wtGSScore, wtHSFScore, varSSFScore, varMaxEntScore, varNNSScore, varGSScore, varHSFScore, nearestSSChange, rsHeterozygosity, rsMAF, exacAllFreq, exacAFRFreq, exacAMRFreq, exacEASFreq, exacSASFreq, exacNFEFreq, exacFINFreq, exacOTHFreq, espEAMAF, espAAMAF, espAllMAF, espEAAAF, espAAAAF, espAllAAF, phastCons, phyloP, wtCodonFreq, varCodonFreq, varAAcomposition, wtAApolarity, varAApolarity, AGVGDgv, AGVGDgd, SIFTmedian, PPH2score, MAPPpValue, MAPPpValueMedian, TASTERpValue, rsAncestralAllele, hgmdSubCategory, gene, varLocation, rsId, varAA_1, transcript, protein, Uniprot, varType, codingEffect, gNomen, cNomen, pNomen, alt_pNomen, pathogenicityClass, rsValidations, rsClinicalSignificance, rsMAFAllele, exacQuality, exacFilter, exacDP, espAvgReadDepth, hgmdId, clinVarIds, clinVarOrigins, clinVarMethods, clinVarClinSignifs, cosmicIds, substType, nucChange, AGVGDclass, chrom, rsValidated, rsSuspect, localSpliceEffect, wtNuc, varNuc, wtAA_1, wtAA_3, wtCodon, varAA_3, varCodon, proteinDomain1, proteinDomain2, proteinDomain3, proteinDomain4, conservedDistSpecies, SIFTprediction, PPH2prediction,PPH2class,MAPPprediction, TASTERprediction, assembly, hgmdPhenotype, hgmdWebLink, clinVarPhenotypes, cosmicTissues) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [str_to_int_float(alamut_dict['geneId'], 'int'), str_to_int_float(alamut_dict['strand'], 'int'), str_to_int_float(alamut_dict['gDNAstart'], 'int'), str_to_int_float(alamut_dict['gDNAend'], 'int'), str_to_int_float(alamut_dict['cDNAstart'], 'int'), str_to_int_float(alamut_dict['cDNAend'], 'int'), str_to_int_float(alamut_dict['exon'], 'int'), str_to_int_float(alamut_dict['intron'], 'int'), str_to_int_float(alamut_dict['omimId'], 'int'), str_to_int_float(alamut_dict['distNearestSS'], 'int'), str_to_int_float(alamut_dict['rsValidationNumber'], 'int'), str_to_int_float(alamut_dict['rsMAFCount'], 'int'), str_to_int_float(alamut_dict['exacAlleleCount'], 'int'), str_to_int_float(alamut_dict['espRefEACount'], 'int'), str_to_int_float(alamut_dict['espRefAACount'], 'int'), str_to_int_float(alamut_dict['espRefAllCount'], 'int'), str_to_int_float(alamut_dict['espAltEACount'], 'int'), str_to_int_float(alamut_dict['espAltAACount'], 'int'), str_to_int_float(alamut_dict['espAltAllCount'], 'int'), str_to_int_float(alamut_dict['hgmdPubMedId'], 'int'), str_to_int_float(alamut_dict['clinVarReviewStatus'], 'int'), str_to_int_float(alamut_dict['posAA'], 'int'), str_to_int_float(alamut_dict['nOrthos'], 'int'), str_to_int_float(alamut_dict['conservedOrthos'], 'int'), str_to_int_float(alamut_dict['BLOSUM45'], 'int'), str_to_int_float(alamut_dict['BLOSUM62'], 'int'), str_to_int_float(alamut_dict['BLOSUM80'], 'int'), str_to_int_float(alamut_dict['wtAAcomposition'], 'int'), str_to_int_float(alamut_dict['wtAAvolume'], 'int'), str_to_int_float(alamut_dict['varAAvolume'], 'int'), str_to_int_float(alamut_dict['granthamDist'], 'int'), str_to_int_float(alamut_dict['SIFTweight'], 'int'), str_to_int_float(alamut_dict['wtSSFScore'], 'float'), str_to_int_float(alamut_dict['wtMaxEntScore'], 'float'), str_to_int_float(alamut_dict['wtNNSScore'], 'float'), str_to_int_float(alamut_dict['wtGSScore'], 'float'), str_to_int_float(alamut_dict['wtHSFScore'], 'float'), str_to_int_float(alamut_dict['varSSFScore'], 'float'), str_to_int_float(alamut_dict['varMaxEntScore'], 'float'), str_to_int_float(alamut_dict['varNNSScore'], 'float'), str_to_int_float(alamut_dict['varGSScore'], 'float'), str_to_int_float(alamut_dict['varHSFScore'], 'float'), str_to_int_float(alamut_dict['nearestSSChange'], 'float'), str_to_int_float(alamut_dict['rsHeterozygosity'], 'float'), str_to_int_float(alamut_dict['rsMAF'], 'float'), str_to_int_float(alamut_dict['exacAllFreq'], 'float'), str_to_int_float(alamut_dict['exacAFRFreq'], 'float'), str_to_int_float(alamut_dict['exacAMRFreq'], 'float'), str_to_int_float(alamut_dict['exacEASFreq'], 'float'), str_to_int_float(alamut_dict['exacSASFreq'], 'float'), str_to_int_float(alamut_dict['exacNFEFreq'], 'float'), str_to_int_float(alamut_dict['exacFINFreq'], 'float'), str_to_int_float(alamut_dict['exacOTHFreq'], 'float'), str_to_int_float(alamut_dict['espEAMAF'], 'float'), str_to_int_float(alamut_dict['espAAMAF'], 'float'), str_to_int_float(alamut_dict['espAllMAF'], 'float'), str_to_int_float(alamut_dict['espEAAAF'], 'float'), str_to_int_float(alamut_dict['espAAAAF'], 'float'), str_to_int_float(alamut_dict['espAllAAF'], 'float'), str_to_int_float(alamut_dict['phastCons'], 'float'), str_to_int_float(alamut_dict['phyloP'], 'float'), str_to_int_float(alamut_dict['wtCodonFreq'], 'float'), str_to_int_float(alamut_dict['varCodonFreq'], 'float'), str_to_int_float(alamut_dict['varAAcomposition'], 'float'), str_to_int_float(alamut_dict['wtAApolarity'], 'float'), str_to_int_float(alamut_dict['varAApolarity'], 'float'), str_to_int_float(alamut_dict['AGVGDgv'], 'float'), str_to_int_float(alamut_dict['AGVGDgd'], 'float'), str_to_int_float(alamut_dict['SIFTmedian'], 'float'), str_to_int_float(alamut_dict['PPH2score'], 'float'), str_to_int_float(alamut_dict['MAPPpValue'], 'float'), str_to_int_float(alamut_dict['MAPPpValueMedian'], 'float'), str_to_int_float(alamut_dict['TASTERpValue'], 'float'), str(alamut_dict['rsAncestralAllele']), str(alamut_dict['hgmdSubCategory']), str(alamut_dict['gene']), str(alamut_dict['varLocation']), str(alamut_dict['rsId']), str(alamut_dict['varAA_1']), str(alamut_dict['transcript']), str(alamut_dict['protein']), str(alamut_dict['Uniprot']), str(alamut_dict['varType']), str(alamut_dict['codingEffect']), str(alamut_dict['gNomen']), str(alamut_dict['cNomen']), str(alamut_dict['pNomen']), str(alamut_dict['alt_pNomen']), str(alamut_dict['pathogenicityClass']), str(alamut_dict['rsValidations']), str(alamut_dict['rsClinicalSignificance']), str(alamut_dict['rsMAFAllele']), str(alamut_dict['exacQuality']), str(alamut_dict['exacFilter']), str(alamut_dict['exacDP']), str(alamut_dict['espAvgReadDepth']), str(alamut_dict['hgmdId']), str(alamut_dict['clinVarIds']), str(alamut_dict['clinVarOrigins']), str(alamut_dict['clinVarMethods']), str(alamut_dict['clinVarClinSignifs']), str(alamut_dict['cosmicIds']), str(alamut_dict['substType']), str(alamut_dict['nucChange']), str(alamut_dict['AGVGDclass']), str(alamut_dict['chrom']), str(alamut_dict['rsValidated']), str(alamut_dict['rsSuspect']), str(alamut_dict['localSpliceEffect']), str(alamut_dict['wtNuc']), str(alamut_dict['varNuc']), str(alamut_dict['wtAA_1']), str(alamut_dict['wtAA_3']), str(alamut_dict['wtCodon']), str(alamut_dict['varAA_3']), str(alamut_dict['varCodon']), str(alamut_dict['proteinDomain1']), str(alamut_dict['proteinDomain2']), str(alamut_dict['proteinDomain3']), str(alamut_dict['proteinDomain4']), str(alamut_dict['conservedDistSpecies']), str(alamut_dict['SIFTprediction']), str(alamut_dict['PPH2prediction']), str(alamut_dict['PPH2class']), str(alamut_dict['MAPPprediction']), str(alamut_dict['TASTERprediction']), str(alamut_dict['assembly']), str(alamut_dict['hgmdPhenotype']), str(alamut_dict['hgmdWebLink']), str(alamut_dict['clinVarPhenotypes']), str(alamut_dict['cosmicTissues']) ])
        db.commit()
        db.close()
		
    #result = request.get_json('a')
    return render_template('interpret.html', form=form)
		#should contain a search bar like:  http://exac.broadinstitute.org which will lead to a specific sample interpetation.
################################################################################################################################################	


	
@app.route('/showdb', methods=['GET', 'POST'])
@app.route('/showdb/<pID>', methods=['GET', 'POST'])
@login_required
def showdb(pID="123_15"):
    #INSERT OR REPLACE
    form = VariantForm()
    pform = PatientForm()
    db = get_db()
    cur = get_db().cursor()
    if request.method == 'POST':
        print(request.is_xhr)
        if pform.validate_on_submit() and not request.is_xhr:
            patient_form_tuple = get_values_from_form('update')
            patient_form_tuple = (pID,) + patient_form_tuple
            print(patient_form_tuple)
            cur.execute("INSERT OR REPLACE INTO patient_info (patient_ID, family_ID, clinical_info, sex) VALUES (?, ?, ?, ?)", patient_form_tuple )
            cur.execute("UPDATE patient_info2panels SET panel_name = ? WHERE patient_ID = ?", (request.form['panel'], pID)) 
            db.commit()
        elif form.validate_on_submit() and not request.is_xhr:
            variant_form_tuple = get_variants_from_form()
            cur.execute("INSERT INTO raw_variants (chr, start, stop, ref, alt, hg) VALUES (?, ?, ?, ?, ?, 'hg19')", variant_form_tuple)
            variant_form_tuple = (pID,) + variant_form_tuple
            cur.execute("INSERT INTO patient_info2raw_variants (patient_ID, chr, start, stop, ref, alt) VALUES (?, ?, ?, ?, ?, ?)", variant_form_tuple) 
            db.commit()
        #OBS: Could I check the presence of this with an if? > Oh yes!
        elif request.is_xhr:
            alamut_dict = request.get_json(force=True)
            print(alamut_dict)
            cur.execute("INSERT INTO alamut_annotation (geneId, strand, gDNAstart, gDNAend, cDNAstart, cDNAend, exon, intron, omimId, distNearestSS, rsValidationNumber, rsMAFCount, exacAlleleCount, espRefEACount, espRefAACount, espRefAllCount, espAltEACount, espAltAACount, espAltAllCount, hgmdPubMedId, clinVarReviewStatus, posAA, nOrthos, conservedOrthos, BLOSUM45, BLOSUM62, BLOSUM80, wtAAcomposition, wtAAvolume, varAAvolume, granthamDist, SIFTweight, wtSSFScore, wtMaxEntScore, wtNNSScore, wtGSScore, wtHSFScore, varSSFScore, varMaxEntScore, varNNSScore, varGSScore, varHSFScore, nearestSSChange, rsHeterozygosity, rsMAF, exacAllFreq, exacAFRFreq, exacAMRFreq, exacEASFreq, exacSASFreq, exacNFEFreq, exacFINFreq, exacOTHFreq, espEAMAF, espAAMAF, espAllMAF, espEAAAF, espAAAAF, espAllAAF, phastCons, phyloP, wtCodonFreq, varCodonFreq, varAAcomposition, wtAApolarity, varAApolarity, AGVGDgv, AGVGDgd, SIFTmedian, PPH2score, MAPPpValue, MAPPpValueMedian, TASTERpValue, rsAncestralAllele, hgmdSubCategory, gene, varLocation, rsId, varAA_1, transcript, protein, Uniprot, varType, codingEffect, gNomen, cNomen, pNomen, alt_pNomen, pathogenicityClass, rsValidations, rsClinicalSignificance, rsMAFAllele, exacQuality, exacFilter, exacDP, espAvgReadDepth, hgmdId, clinVarIds, clinVarOrigins, clinVarMethods, clinVarClinSignifs, cosmicIds, substType, nucChange, AGVGDclass, chrom, rsValidated, rsSuspect, localSpliceEffect, wtNuc, varNuc, wtAA_1, wtAA_3, wtCodon, varAA_3, varCodon, proteinDomain1, proteinDomain2, proteinDomain3, proteinDomain4, conservedDistSpecies, SIFTprediction, PPH2prediction,PPH2class,MAPPprediction, TASTERprediction, assembly, hgmdPhenotype, hgmdWebLink, clinVarPhenotypes, cosmicTissues) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [str_to_int_float(alamut_dict['geneId'], 'int'), str_to_int_float(alamut_dict['strand'], 'int'), str_to_int_float(alamut_dict['gDNAstart'], 'int'), str_to_int_float(alamut_dict['gDNAend'], 'int'), str_to_int_float(alamut_dict['cDNAstart'], 'int'), str_to_int_float(alamut_dict['cDNAend'], 'int'), str_to_int_float(alamut_dict['exon'], 'int'), str_to_int_float(alamut_dict['intron'], 'int'), str_to_int_float(alamut_dict['omimId'], 'int'), str_to_int_float(alamut_dict['distNearestSS'], 'int'), str_to_int_float(alamut_dict['rsValidationNumber'], 'int'), str_to_int_float(alamut_dict['rsMAFCount'], 'int'), str_to_int_float(alamut_dict['exacAlleleCount'], 'int'), str_to_int_float(alamut_dict['espRefEACount'], 'int'), str_to_int_float(alamut_dict['espRefAACount'], 'int'), str_to_int_float(alamut_dict['espRefAllCount'], 'int'), str_to_int_float(alamut_dict['espAltEACount'], 'int'), str_to_int_float(alamut_dict['espAltAACount'], 'int'), str_to_int_float(alamut_dict['espAltAllCount'], 'int'), str_to_int_float(alamut_dict['hgmdPubMedId'], 'int'), str_to_int_float(alamut_dict['clinVarReviewStatus'], 'int'), str_to_int_float(alamut_dict['posAA'], 'int'), str_to_int_float(alamut_dict['nOrthos'], 'int'), str_to_int_float(alamut_dict['conservedOrthos'], 'int'), str_to_int_float(alamut_dict['BLOSUM45'], 'int'), str_to_int_float(alamut_dict['BLOSUM62'], 'int'), str_to_int_float(alamut_dict['BLOSUM80'], 'int'), str_to_int_float(alamut_dict['wtAAcomposition'], 'int'), str_to_int_float(alamut_dict['wtAAvolume'], 'int'), str_to_int_float(alamut_dict['varAAvolume'], 'int'), str_to_int_float(alamut_dict['granthamDist'], 'int'), str_to_int_float(alamut_dict['SIFTweight'], 'int'), str_to_int_float(alamut_dict['wtSSFScore'], 'float'), str_to_int_float(alamut_dict['wtMaxEntScore'], 'float'), str_to_int_float(alamut_dict['wtNNSScore'], 'float'), str_to_int_float(alamut_dict['wtGSScore'], 'float'), str_to_int_float(alamut_dict['wtHSFScore'], 'float'), str_to_int_float(alamut_dict['varSSFScore'], 'float'), str_to_int_float(alamut_dict['varMaxEntScore'], 'float'), str_to_int_float(alamut_dict['varNNSScore'], 'float'), str_to_int_float(alamut_dict['varGSScore'], 'float'), str_to_int_float(alamut_dict['varHSFScore'], 'float'), str_to_int_float(alamut_dict['nearestSSChange'], 'float'), str_to_int_float(alamut_dict['rsHeterozygosity'], 'float'), str_to_int_float(alamut_dict['rsMAF'], 'float'), str_to_int_float(alamut_dict['exacAllFreq'], 'float'), str_to_int_float(alamut_dict['exacAFRFreq'], 'float'), str_to_int_float(alamut_dict['exacAMRFreq'], 'float'), str_to_int_float(alamut_dict['exacEASFreq'], 'float'), str_to_int_float(alamut_dict['exacSASFreq'], 'float'), str_to_int_float(alamut_dict['exacNFEFreq'], 'float'), str_to_int_float(alamut_dict['exacFINFreq'], 'float'), str_to_int_float(alamut_dict['exacOTHFreq'], 'float'), str_to_int_float(alamut_dict['espEAMAF'], 'float'), str_to_int_float(alamut_dict['espAAMAF'], 'float'), str_to_int_float(alamut_dict['espAllMAF'], 'float'), str_to_int_float(alamut_dict['espEAAAF'], 'float'), str_to_int_float(alamut_dict['espAAAAF'], 'float'), str_to_int_float(alamut_dict['espAllAAF'], 'float'), str_to_int_float(alamut_dict['phastCons'], 'float'), str_to_int_float(alamut_dict['phyloP'], 'float'), str_to_int_float(alamut_dict['wtCodonFreq'], 'float'), str_to_int_float(alamut_dict['varCodonFreq'], 'float'), str_to_int_float(alamut_dict['varAAcomposition'], 'float'), str_to_int_float(alamut_dict['wtAApolarity'], 'float'), str_to_int_float(alamut_dict['varAApolarity'], 'float'), str_to_int_float(alamut_dict['AGVGDgv'], 'float'), str_to_int_float(alamut_dict['AGVGDgd'], 'float'), str_to_int_float(alamut_dict['SIFTmedian'], 'float'), str_to_int_float(alamut_dict['PPH2score'], 'float'), str_to_int_float(alamut_dict['MAPPpValue'], 'float'), str_to_int_float(alamut_dict['MAPPpValueMedian'], 'float'), str_to_int_float(alamut_dict['TASTERpValue'], 'float'), str(alamut_dict['rsAncestralAllele']), str(alamut_dict['hgmdSubCategory']), str(alamut_dict['gene']), str(alamut_dict['varLocation']), str(alamut_dict['rsId']), str(alamut_dict['varAA_1']), str(alamut_dict['transcript']), str(alamut_dict['protein']), str(alamut_dict['Uniprot']), str(alamut_dict['varType']), str(alamut_dict['codingEffect']), str(alamut_dict['gNomen']), str(alamut_dict['cNomen']), str(alamut_dict['pNomen']), str(alamut_dict['alt_pNomen']), str(alamut_dict['pathogenicityClass']), str(alamut_dict['rsValidations']), str(alamut_dict['rsClinicalSignificance']), str(alamut_dict['rsMAFAllele']), str(alamut_dict['exacQuality']), str(alamut_dict['exacFilter']), str(alamut_dict['exacDP']), str(alamut_dict['espAvgReadDepth']), str(alamut_dict['hgmdId']), str(alamut_dict['clinVarIds']), str(alamut_dict['clinVarOrigins']), str(alamut_dict['clinVarMethods']), str(alamut_dict['clinVarClinSignifs']), str(alamut_dict['cosmicIds']), str(alamut_dict['substType']), str(alamut_dict['nucChange']), str(alamut_dict['AGVGDclass']), str(alamut_dict['chrom']), str(alamut_dict['rsValidated']), str(alamut_dict['rsSuspect']), str(alamut_dict['localSpliceEffect']), str(alamut_dict['wtNuc']), str(alamut_dict['varNuc']), str(alamut_dict['wtAA_1']), str(alamut_dict['wtAA_3']), str(alamut_dict['wtCodon']), str(alamut_dict['varAA_3']), str(alamut_dict['varCodon']), str(alamut_dict['proteinDomain1']), str(alamut_dict['proteinDomain2']), str(alamut_dict['proteinDomain3']), str(alamut_dict['proteinDomain4']), str(alamut_dict['conservedDistSpecies']), str(alamut_dict['SIFTprediction']), str(alamut_dict['PPH2prediction']), str(alamut_dict['PPH2class']), str(alamut_dict['MAPPprediction']), str(alamut_dict['TASTERprediction']), str(alamut_dict['assembly']), str(alamut_dict['hgmdPhenotype']), str(alamut_dict['hgmdWebLink']), str(alamut_dict['clinVarPhenotypes']), str(alamut_dict['cosmicTissues']) ])
            db.commit()
            return json.dumps({'success': True}), 200, {'ContentType':'application/json'}
    #hente ut pasientinfo for alle som er kjort
    cur.execute('SELECT * FROM patient_info')
    patient_items = listOfdictsFromCur(cur.fetchall(), 'patient_info')
    patient_table = PatientTable(patient_items)
    #hente ut tolkede varianter for en pasient
    cur.execute('SELECT p2r.chr, p2r.start, p2r.stop, p2r.ref, p2r.alt, am.gene FROM patient_info2raw_variants AS p2r LEFT JOIN alamut_annotation AS am ON p2r.chr = am.chrom AND p2r.start = am.gDNAstart WHERE patient_ID = ?', (pID, ))
    var_items = listOfdictsFromCur(cur.fetchall(), 'int_variants')
    var_table = VariantTable(var_items,)
    #get patientinfo for a single patient assigned by pID
    cur.execute('SELECT pat.patient_ID, pat.clinical_info, pat.family_ID, pat.sex, pan.panel_name,QC.MEAN_TARGET_COVERAGE,\
    QC.PCT_TARGET_BASES_20X, QC.PCT_TARGET_BASES_30X, ins.median_insert_size, ins.mean_insert_size\
    FROM patient_info AS pat JOIN patient_info2panels AS pan ON pat.patient_ID=pan.patient_ID\
    JOIN QC ON pat.patient_ID=QC.SAMPLE_NAME LEFT JOIN insert_size AS ins ON pat.patient_ID=ins.SAMPLE_NAME\
    WHERE pat.patient_ID = ?', (pID, ))
    pID_patient = dictFromCur(cur.fetchall(), 'pID_patient')
    db.close()
    return render_template('showdb.html', patient_table=patient_table, var_table=var_table, form=form, pform=pform, pID=pID, pID_patient=pID_patient)




#########

if __name__ == '__main__':
    app.run('172.16.0.56')
    #app.run('0.0.0.0', port=8080)

    
    
    
    
    
