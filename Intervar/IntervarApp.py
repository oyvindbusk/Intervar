from flask import Flask, render_template, request, abort, redirect, url_for, flash, g, send_from_directory
from flask.ext.login import LoginManager, UserMixin, login_user, logout_user, login_required
from flask.ext.sqlalchemy import SQLAlchemy
import os
import sqlite3
from werkzeug import secure_filename
#importere egne scripts
from scripts import PatientForm, PatientTable, VariantTable, dictFromCur, print_file




DEBUG = True
SECRET_KEY = 'yekterces'
SQLALCHEMY_DATABASE_URI = 'sqlite:///db/users.db'

app = Flask(__name__)
app.config.from_object(__name__)
UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
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

@app.route('/secret')
@login_required
def secret():
    return render_template('secret.html')

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
        cur.execute("INSERT INTO patient_info (patient_ID, family_ID, clinical_info,  sex) VALUES (?, ?, ?, ?)", [request.form['patient_ID'], request.form['familyID'], request.form['clinInfo'], request.form['sex'], ])
        db.commit()
        file = request.files['hsmFileUpload']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return "Suksess"
        #flash('Suksess!!')
    elif request.method == "GET":
        return render_template('testinput.html', form=form)

@app.route('/showdb')
@login_required
def showdb():
    cur = get_db().cursor()
    #hente ut pasientinfo for alle som er kjort
    cur.execute('SELECT * FROM patient_info')
    patient_items = dictFromCur(cur.fetchall(), 'patient_info')
    patient_table = PatientTable(patient_items)
    #hente ut tolkede varianter for en pasient
    cur.execute('SELECT chr, start, stop, ref, alt, inhouse_class FROM interpretations WHERE SAMPLE_NAME = "123_15"')
    var_items = dictFromCur(cur.fetchall(), 'int_variants')
    var_table = VariantTable(var_items,)
    return render_template('showdb.html', patient_table=patient_table, var_table=var_table)
    
    
if __name__ == '__main__':
        #app.run('172.16.0.56')
    app.run('0.0.0.0')

    

    
    #@app.route('/uploads/<filename>')
#def uploaded_file(filename):
 #   return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    
    
    
    
    
    
