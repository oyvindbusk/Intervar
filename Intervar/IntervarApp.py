from flask import Flask, render_template, request, abort, redirect, url_for, flash, g, send_from_directory, jsonify
from flask.ext.login import LoginManager, UserMixin, login_user, logout_user, login_required
from flask.ext.sqlalchemy import SQLAlchemy
import os
import sqlite3
from werkzeug import secure_filename
#importere egne scripts
from scripts import PatientForm, VariantForm, SearchForm, PatientTable, VariantTable, listOfdictsFromCur, dictFromCur, print_file, hsmetrics_to_tuple, insert_data, get_values_from_form, insertsize_to_tuple, insert_data_is, get_variants_from_form
from scripts import alamut_dict_to_DB, str_to_int_float, Interpret_overallForm, InterpretForm
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
        else:
            return abort(404)
    elif request.method == "GET":
        return render_template('testinput.html', form=form)

################################################################################################################################################		

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
		return redirect(url_for('showdb', pID=request.form['search']))
    return render_template('interpret.html', form=form)
		#should contain a search bar like:  http://exac.broadinstitute.org which will lead to a specific sample interpetation.

################################################################################################################################################	
	
@app.route('/showdb', methods=['GET', 'POST'])
@app.route('/showdb/<pID>', methods=['GET', 'POST'])
@login_required
def showdb(pID="123_15"):
    # legge inn en count paa hvor mange tolkninger som er utfort, og velge den hvis 1, mens hvis det er flere, faa ett valg? vrient... velge en forst og fremst
    form = VariantForm()
    pform = PatientForm()
    iform = Interpret_overallForm()
    ivform = InterpretForm()
    db = get_db()
    cur = get_db().cursor()
    if request.method == 'POST':
        
        if pform.validate_on_submit() and not request.is_xhr:
            patient_form_tuple = get_values_from_form('update')
            patient_form_tuple = (pID,) + patient_form_tuple
            print(patient_form_tuple)
            cur.execute("INSERT OR REPLACE INTO patient_info (patient_ID, family_ID, clinical_info, sex) VALUES (?, ?, ?, ?)", patient_form_tuple )
            cur.execute("UPDATE patient_info2panels SET panel_name = ? WHERE patient_ID = ?", (request.form['panel'], pID)) 
            db.commit()
        elif form.validate_on_submit() and not request.is_xhr:
            variant_form_tuple = get_variants_from_form()
            cur.execute("INSERT OR IGNORE INTO raw_variants (chr, start, stop, ref, alt, hg) VALUES (?, ?, ?, ?, ?, 'hg19')", [variant_form_tuple[0], variant_form_tuple[1], variant_form_tuple[2], variant_form_tuple[3], variant_form_tuple[4]])
            variant_form_tuple = (pID,) + variant_form_tuple
            cur.execute("INSERT INTO patient_info2raw_variants (patient_ID, chr, start, stop, ref, alt, zygosity, denovo ) VALUES (?, ?, ?, ?, ?, ?, ?,?)", variant_form_tuple) 
            #insert into interpretations
            db.commit()
        elif request.is_xhr: # checking if this comes 
            alamut_dict = request.get_json(force=True)
            print(alamut_dict)
            cur.execute("INSERT INTO alamut_annotation (geneId, strand, gDNAstart, gDNAend, cDNAstart, cDNAend, exon, intron, omimId, distNearestSS, rsValidationNumber, rsMAFCount, exacAlleleCount, espRefEACount, espRefAACount, espRefAllCount, espAltEACount, espAltAACount, espAltAllCount, hgmdPubMedId, clinVarReviewStatus, posAA, nOrthos, conservedOrthos, BLOSUM45, BLOSUM62, BLOSUM80, wtAAcomposition, wtAAvolume, varAAvolume, granthamDist, SIFTweight, wtSSFScore, wtMaxEntScore, wtNNSScore, wtGSScore, wtHSFScore, varSSFScore, varMaxEntScore, varNNSScore, varGSScore, varHSFScore, nearestSSChange, rsHeterozygosity, rsMAF, exacAllFreq, exacAFRFreq, exacAMRFreq, exacEASFreq, exacSASFreq, exacNFEFreq, exacFINFreq, exacOTHFreq, espEAMAF, espAAMAF, espAllMAF, espEAAAF, espAAAAF, espAllAAF, phastCons, phyloP, wtCodonFreq, varCodonFreq, varAAcomposition, wtAApolarity, varAApolarity, AGVGDgv, AGVGDgd, SIFTmedian, PPH2score, MAPPpValue, MAPPpValueMedian, TASTERpValue, rsAncestralAllele, hgmdSubCategory, gene, varLocation, rsId, varAA_1, transcript, protein, Uniprot, varType, codingEffect, gNomen, cNomen, pNomen, alt_pNomen, pathogenicityClass, rsValidations, rsClinicalSignificance, rsMAFAllele, exacQuality, exacFilter, exacDP, espAvgReadDepth, hgmdId, clinVarIds, clinVarOrigins, clinVarMethods, clinVarClinSignifs, cosmicIds, substType, nucChange, AGVGDclass, chrom, rsValidated, rsSuspect, localSpliceEffect, wtNuc, varNuc, wtAA_1, wtAA_3, wtCodon, varAA_3, varCodon, proteinDomain1, proteinDomain2, proteinDomain3, proteinDomain4, conservedDistSpecies, SIFTprediction, PPH2prediction,PPH2class,MAPPprediction, TASTERprediction, assembly, hgmdPhenotype, hgmdWebLink, clinVarPhenotypes, cosmicTissues) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [str_to_int_float(alamut_dict['geneId'], 'int'), str_to_int_float(alamut_dict['strand'], 'int'), str_to_int_float(alamut_dict['gDNAstart'], 'int'), str_to_int_float(alamut_dict['gDNAend'], 'int'), str_to_int_float(alamut_dict['cDNAstart'], 'int'), str_to_int_float(alamut_dict['cDNAend'], 'int'), str_to_int_float(alamut_dict['exon'], 'int'), str_to_int_float(alamut_dict['intron'], 'int'), str_to_int_float(alamut_dict['omimId'], 'int'), str_to_int_float(alamut_dict['distNearestSS'], 'int'), str_to_int_float(alamut_dict['rsValidationNumber'], 'int'), str_to_int_float(alamut_dict['rsMAFCount'], 'int'), str_to_int_float(alamut_dict['exacAlleleCount'], 'int'), str_to_int_float(alamut_dict['espRefEACount'], 'int'), str_to_int_float(alamut_dict['espRefAACount'], 'int'), str_to_int_float(alamut_dict['espRefAllCount'], 'int'), str_to_int_float(alamut_dict['espAltEACount'], 'int'), str_to_int_float(alamut_dict['espAltAACount'], 'int'), str_to_int_float(alamut_dict['espAltAllCount'], 'int'), str_to_int_float(alamut_dict['hgmdPubMedId'], 'int'), str_to_int_float(alamut_dict['clinVarReviewStatus'], 'int'), str_to_int_float(alamut_dict['posAA'], 'int'), str_to_int_float(alamut_dict['nOrthos'], 'int'), str_to_int_float(alamut_dict['conservedOrthos'], 'int'), str_to_int_float(alamut_dict['BLOSUM45'], 'int'), str_to_int_float(alamut_dict['BLOSUM62'], 'int'), str_to_int_float(alamut_dict['BLOSUM80'], 'int'), str_to_int_float(alamut_dict['wtAAcomposition'], 'int'), str_to_int_float(alamut_dict['wtAAvolume'], 'int'), str_to_int_float(alamut_dict['varAAvolume'], 'int'), str_to_int_float(alamut_dict['granthamDist'], 'int'), str_to_int_float(alamut_dict['SIFTweight'], 'int'), str_to_int_float(alamut_dict['wtSSFScore'], 'float'), str_to_int_float(alamut_dict['wtMaxEntScore'], 'float'), str_to_int_float(alamut_dict['wtNNSScore'], 'float'), str_to_int_float(alamut_dict['wtGSScore'], 'float'), str_to_int_float(alamut_dict['wtHSFScore'], 'float'), str_to_int_float(alamut_dict['varSSFScore'], 'float'), str_to_int_float(alamut_dict['varMaxEntScore'], 'float'), str_to_int_float(alamut_dict['varNNSScore'], 'float'), str_to_int_float(alamut_dict['varGSScore'], 'float'), str_to_int_float(alamut_dict['varHSFScore'], 'float'), str_to_int_float(alamut_dict['nearestSSChange'], 'float'), str_to_int_float(alamut_dict['rsHeterozygosity'], 'float'), str_to_int_float(alamut_dict['rsMAF'], 'float'), str_to_int_float(alamut_dict['exacAllFreq'], 'float'), str_to_int_float(alamut_dict['exacAFRFreq'], 'float'), str_to_int_float(alamut_dict['exacAMRFreq'], 'float'), str_to_int_float(alamut_dict['exacEASFreq'], 'float'), str_to_int_float(alamut_dict['exacSASFreq'], 'float'), str_to_int_float(alamut_dict['exacNFEFreq'], 'float'), str_to_int_float(alamut_dict['exacFINFreq'], 'float'), str_to_int_float(alamut_dict['exacOTHFreq'], 'float'), str_to_int_float(alamut_dict['espEAMAF'], 'float'), str_to_int_float(alamut_dict['espAAMAF'], 'float'), str_to_int_float(alamut_dict['espAllMAF'], 'float'), str_to_int_float(alamut_dict['espEAAAF'], 'float'), str_to_int_float(alamut_dict['espAAAAF'], 'float'), str_to_int_float(alamut_dict['espAllAAF'], 'float'), str_to_int_float(alamut_dict['phastCons'], 'float'), str_to_int_float(alamut_dict['phyloP'], 'float'), str_to_int_float(alamut_dict['wtCodonFreq'], 'float'), str_to_int_float(alamut_dict['varCodonFreq'], 'float'), str_to_int_float(alamut_dict['varAAcomposition'], 'float'), str_to_int_float(alamut_dict['wtAApolarity'], 'float'), str_to_int_float(alamut_dict['varAApolarity'], 'float'), str_to_int_float(alamut_dict['AGVGDgv'], 'float'), str_to_int_float(alamut_dict['AGVGDgd'], 'float'), str_to_int_float(alamut_dict['SIFTmedian'], 'float'), str_to_int_float(alamut_dict['PPH2score'], 'float'), str_to_int_float(alamut_dict['MAPPpValue'], 'float'), str_to_int_float(alamut_dict['MAPPpValueMedian'], 'float'), str_to_int_float(alamut_dict['TASTERpValue'], 'float'), str(alamut_dict['rsAncestralAllele']), str(alamut_dict['hgmdSubCategory']), str(alamut_dict['gene']), str(alamut_dict['varLocation']), str(alamut_dict['rsId']), str(alamut_dict['varAA_1']), str(alamut_dict['transcript']), str(alamut_dict['protein']), str(alamut_dict['Uniprot']), str(alamut_dict['varType']), str(alamut_dict['codingEffect']), str(alamut_dict['gNomen']), str(alamut_dict['cNomen']), str(alamut_dict['pNomen']), str(alamut_dict['alt_pNomen']), str(alamut_dict['pathogenicityClass']), str(alamut_dict['rsValidations']), str(alamut_dict['rsClinicalSignificance']), str(alamut_dict['rsMAFAllele']), str(alamut_dict['exacQuality']), str(alamut_dict['exacFilter']), str(alamut_dict['exacDP']), str(alamut_dict['espAvgReadDepth']), str(alamut_dict['hgmdId']), str(alamut_dict['clinVarIds']), str(alamut_dict['clinVarOrigins']), str(alamut_dict['clinVarMethods']), str(alamut_dict['clinVarClinSignifs']), str(alamut_dict['cosmicIds']), str(alamut_dict['substType']), str(alamut_dict['nucChange']), str(alamut_dict['AGVGDclass']), str(alamut_dict['chrom']), str(alamut_dict['rsValidated']), str(alamut_dict['rsSuspect']), str(alamut_dict['localSpliceEffect']), str(alamut_dict['wtNuc']), str(alamut_dict['varNuc']), str(alamut_dict['wtAA_1']), str(alamut_dict['wtAA_3']), str(alamut_dict['wtCodon']), str(alamut_dict['varAA_3']), str(alamut_dict['varCodon']), str(alamut_dict['proteinDomain1']), str(alamut_dict['proteinDomain2']), str(alamut_dict['proteinDomain3']), str(alamut_dict['proteinDomain4']), str(alamut_dict['conservedDistSpecies']), str(alamut_dict['SIFTprediction']), str(alamut_dict['PPH2prediction']), str(alamut_dict['PPH2class']), str(alamut_dict['MAPPprediction']), str(alamut_dict['TASTERprediction']), str(alamut_dict['assembly']), str(alamut_dict['hgmdPhenotype']), str(alamut_dict['hgmdWebLink']), str(alamut_dict['clinVarPhenotypes']), str(alamut_dict['cosmicTissues']) ])
            db.commit()
            return json.dumps({'success': True}), 200, {'ContentType':'application/json'}
        elif iform.validate_on_submit() and not request.is_xhr:
            int_form_tuple = get_values_from_form('Interpret_overall')
            print(int_form_tuple + ": " + pID)
            cur.execute('INSERT OR REPLACE INTO interpretations_pr_patient (comments, patient_ID) VALUES (?, ?)', [int_form_tuple, pID])
            db.commit()
        elif ivform.validate_on_submit() and not request.is_xhr:
            int_form_tuple = get_values_from_form('Interpret_overall')
            print(int_form_tuple + ": " + pID)
    #hente ut pasientinfo for alle som er kjort
    cur.execute('SELECT * FROM patient_info')
    patient_items = listOfdictsFromCur(cur.fetchall(), 'patient_info')
    patient_table = PatientTable(patient_items)
    #hente ut tolkede varianter for en pasient
    cur.execute('SELECT p2r.chr, p2r.start, p2r.stop, p2r.ref, p2r.alt, p2r.zygosity,\
    am.ID, am.gene, am.cNomen AS cDNA, am.pNomen AS protein, am.exacAllFreq,\
    i.inhouse_class, i.comments\
    FROM patient_info2raw_variants AS p2r\
    LEFT JOIN alamut_annotation AS am ON p2r.chr = am.chrom AND p2r.start = am.gDNAstart\
    LEFT JOIN interpretations AS i ON p2r.patient_ID = i.SAMPLE_NAME AND p2r.chr = i.chr AND p2r.start =i.start\
    WHERE patient_ID = ?', (pID, ))
    var_items = listOfdictsFromCur(cur.fetchall(), 'int_variants')
    var_table = VariantTable(var_items,)
    #get patientinfo for a single patient assigned by pID
    cur.execute('SELECT pat.patient_ID, pat.clinical_info, pat.family_ID, pat.sex, pan.panel_name,QC.MEAN_TARGET_COVERAGE,\
    QC.PCT_TARGET_BASES_20X, QC.PCT_TARGET_BASES_30X, ins.median_insert_size, ins.mean_insert_size\
    FROM patient_info AS pat JOIN patient_info2panels AS pan ON pat.patient_ID=pan.patient_ID\
    JOIN QC ON pat.patient_ID=QC.SAMPLE_NAME LEFT JOIN insert_size AS ins ON pat.patient_ID=ins.SAMPLE_NAME\
    WHERE pat.patient_ID = ?', (pID, ))
    pID_patient = dictFromCur(cur.fetchall(), 'pID_patient')
    #get comments for the interpretations of one patient:
    cur.execute('SELECT comments FROM interpretations_pr_patient WHERE patient_ID = ?', (pID, ))
    patient_comment = cur.fetchall()[0][0]
    if len(patient_comment) == 0:
        patient_comment = ''
    else:
        pass
    db.close()
    return render_template('showdb.html', patient_table=patient_table, var_table=var_table, form=form, pform=pform, iform=iform, ivform=ivform, pID=pID, pID_patient=pID_patient, patient_comment=patient_comment)

################################################################################################################################################



################################################################################################################################################	
	
@app.route('/report', methods=['GET', 'POST'])
@app.route('/report/<pID>', methods=['GET', 'POST'])
@login_required
def report(pID="123_15"):
    # legge inn en count paa hvor mange tolkninger som er utfort, og velge den hvis 1, mens hvis det er flere, faa ett valg? vrient... velge en forst og fremst
    
    db = get_db()
    cur = get_db().cursor()
    
    #hente ut tolkede varianter for en pasient
    cur.execute('SELECT p2r.chr, p2r.start, p2r.stop, p2r.ref, p2r.alt, p2r.zygosity,\
    am.ID, am.gene, am.cNomen AS cDNA, am.pNomen AS protein, am.exacAllFreq,\
    i.inhouse_class, i.comments\
    FROM patient_info2raw_variants AS p2r\
    LEFT JOIN alamut_annotation AS am ON p2r.chr = am.chrom AND p2r.start = am.gDNAstart\
    LEFT JOIN interpretations AS i ON p2r.patient_ID = i.SAMPLE_NAME AND p2r.chr = i.chr AND p2r.start =i.start\
    WHERE patient_ID = ?', (pID, ))
    var_items = listOfdictsFromCur(cur.fetchall(), 'int_variants')
   
    #get patientinfo for a single patient assigned by pID
    cur.execute('SELECT pat.patient_ID, pat.clinical_info, pat.family_ID, pat.sex, pan.panel_name,QC.MEAN_TARGET_COVERAGE,\
    QC.PCT_TARGET_BASES_20X, QC.PCT_TARGET_BASES_30X, ins.median_insert_size, ins.mean_insert_size\
    FROM patient_info AS pat JOIN patient_info2panels AS pan ON pat.patient_ID=pan.patient_ID\
    JOIN QC ON pat.patient_ID=QC.SAMPLE_NAME LEFT JOIN insert_size AS ins ON pat.patient_ID=ins.SAMPLE_NAME\
    WHERE pat.patient_ID = ?', (pID, ))
    pID_patient = dictFromCur(cur.fetchall(), 'pID_patient')
    db.close()
    variant_dict = {}
    
    return render_template('report.html', var_items=var_items, pID=pID, pID_patient=pID_patient)

################################################################################################################################################

@app.route('/_return_alamut_for_variant')
def _return_alamut_for_variant():
    ''' Gets a ID from the alamut table and returns the contents as a JSON
    '''
    variant_id = request.args.get('id', 0, type=int)
    def dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d
    db = get_db()
    db.row_factory = dict_factory
    cur = get_db().cursor()
    cur.execute('SELECT * FROM alamut_annotation WHERE ID = ?', [variant_id])
    #obs index out of bounds nar den er tom
    result = cur.fetchall()[0]
    db.close()
    return jsonify(result)

################################################################################################################################################

if __name__ == '__main__':
    app.run('172.16.0.56')
    #app.run('0.0.0.0', port=8080)


    
    
    
    
    
