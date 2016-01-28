from flask import Flask, render_template, request, abort, redirect, url_for, flash, g, send_from_directory, jsonify
from flask.ext.login import LoginManager, UserMixin, login_user, logout_user, login_required
from flask.ext.sqlalchemy import SQLAlchemy
import os
import sqlite3
from werkzeug import secure_filename
#importere egne scripts
from scripts import PatientForm, VariantForm, SearchForm, PatientTable, VariantTable, dictFromCur, print_file, hsmetrics_to_tuple, insert_data, get_values_from_form, insertsize_to_tuple, insert_data_is
#from scripts import SearchForm



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
    elif request.method == "GET":
        return render_template('testinput.html', form=form)

		
@app.route('/overview')
@login_required
def overview():
    return render_template('overview.html')

@app.route('/interpret', methods=['GET', 'POST'])
@login_required
def interpret():
    form = VariantForm()
    searchform = SearchForm
    if request.method == "POST":
        return render_template('post_search.html', search_results=request.form['search'], form=form, searchform=searchform)
    return render_template('interpret.html')
		#should contain a search bar like:  http://exac.broadinstitute.org which will lead to a specific sample interpetation.
	

@app.route('/_add_numbers')
def add_numbers():
    """Add two numbers server side, ridiculous but well..."""
    a = request.args.get('a', 0, type=int)
    b = request.args.get('b', 0, type=int)
    alamut = request.args.get('alamut', 0, type=str)
    print(alamut)
    return jsonify(result=a + b)


@app.route('/showdb')
@app.route('/showdb/<pID>')
@login_required
def showdb(pID="123_15"):
    form = VariantForm()
    cur = get_db().cursor()
    #hente ut pasientinfo for alle som er kjort
    cur.execute('SELECT * FROM patient_info')
    patient_items = dictFromCur(cur.fetchall(), 'patient_info')
    patient_table = PatientTable(patient_items)
    #hente ut tolkede varianter for en pasient
    cur.execute('SELECT chr, start, stop, ref, alt, inhouse_class FROM interpretations WHERE SAMPLE_NAME = "123_15"')
    var_items = dictFromCur(cur.fetchall(), 'int_variants')
    var_table = VariantTable(var_items,)
    return render_template('showdb.html', patient_table=patient_table, var_table=var_table, form=form, pID=pID)






if __name__ == '__main__':
    #app.run('172.16.0.56')
    app.run('0.0.0.0', port=8080)

    
    
    
    
    
