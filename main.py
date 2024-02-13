from flask import Flask, render_template, request, redirect, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from forms import LoginForm, RegistrationForm
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
import pymysql
from random import randrange, randint

pymysql.install_as_MySQLdb()
import json


pymysql.install_as_MySQLdb()
app = Flask(__name__)
app.app_context().push()
app.config['SECRET_KEY'] = 'a really really really really long secret key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/meets.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
engine = create_engine("sqlite:///instance/meets.db")
db = SQLAlchemy(app)
mail = Mail(app)

login_manager = LoginManager(app)
login_manager.login_view = 'index'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)
    login = db.Column(db.String(30), nullable=False, unique=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class usee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quote = db.Column(db.String(300), nullable=False)
    topic = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    possible_days = db.Column(db.String(50), nullable=False)
    clas = db.Column(db.Integer, nullable=False)
    confirmed = db.Column(db.Integer, nullable=False)
    link = db.Column(db.String(300))
    email = db.Column(db.String(300))
    sender = db.Column(db.String(300))

    def __repr__(self):
        return '<usee %r>' % self.id


class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), nullable=False, unique=True)
    subjects = db.relationship('Subject', backref='class', lazy=True)


class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    courses = db.relationship('Course', backref='subject', lazy=True)


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)

    def __repr__(self):
        return f"Image('{self.filename}')"

@app.route("/index", methods=['GET', 'POST'])
def index():
    form = LoginForm(request.form)
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect('/meets-subj1')
        else:
            flash('Invalid email or password', 'error')
    return render_template('index.html', form=form)


@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm(request.form)
    if form.validate_on_submit():
        try:
            user = User(email=form.email.data, login=form.login.data)
            user.set_password(form.password.data)
            user.id = randint(1, 100000000)

            db.session.add(user)
            db.session.commit()

            login_user(user)
            flash('Регистрация успешна!', 'success')
            return redirect('/meets-subj1')
        except Exception as e:
            print(f"Error adding user to the database: {str(e)}")
            db.session.rollback()
            flash('Ошибка регистрации. Возможно, такой пользователь уже существует.', 'error')
    return render_template('register.html', form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('Вы успешно вышли из аккаунта.', 'success')
    return redirect('index')


@app.route('/subjects')
def subjects():
    classes = Class.query.all()
    return render_template('subjects.html', classes=classes)


@app.route('/notifications')
@login_required
def notifications():
    use = usee.query.order_by(usee.date.desc()).all()
    return render_template('notifications.html', use=use)


@app.route('/class/<int:class_id>/subjects')
def class_subjects(class_id):
    class_info = Class.query.get_or_404(class_id)
    subjects = class_info.subjects
    return render_template('class_subjects.html', class_info=class_info, subjects=subjects)


@app.route('/subject/<int:subject_id>/1')
def list_courses(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    courses = subject.courses
    return render_template('article.html', subject=subject, courses=courses)


@app.route('/get_course_content/<int:course_id>', methods=['GET'])
def get_course_content(course_id):
    course = Course.query.get_or_404(course_id)
    description = course.description.split("/n")
    images = Image.query.filter_by(course_id=course_id).all()
    image_ids = [image.id for image in images]
    print(image_ids)
    for i, line in enumerate(description):
        while "<" in line and ">" in line:
            start_index = line.find("<")
            end_index = line.find(">")
            if start_index != -1 and end_index != -1:
                image_id_str = line[start_index + 1:end_index]

                if image_id_str.isdigit():
                    image_id = int(image_id_str)
                    if image_id in image_ids:
                        image_filename = Image.query.get(image_id).filename
                        line = line.replace(f"<{image_id_str}>", f"<img src='../../static/{image_filename}' alt='Image'>")
                        print(line)
                        description[i] = line
                    else:
                        line = line.replace(f"<{image_id_str}>", "")
                        print(1)
                else:
                    print(type(image_id_str))
                    line = line.replace(f"<{image_id_str}>", "")
    content = {
        'title': course.title,
        'description': description
    }
    print(description)
    return jsonify(content)


@app.route("/submit_link", methods=['POST'])
@login_required
def submit_link():
    if request.method == 'POST':
        link = request.form.get('form-link')

        meet_id = request.form.get('meet_id')

        meet_record = usee.query.get(meet_id)

        if meet_record:
            meet_record.link = link
            meet_record.confirmed = 1
            meet_record.sender = current_user.email
            try:
                db.session.commit()

                return jsonify({'success': True})

            except Exception as e:
                db.session.rollback()
                return jsonify({'success': False, 'error': str(e)})

        return jsonify({'success': False, 'error': 'Meeting record not found'})
    else:
        return jsonify({'success': False, 'error': 'Invalid request method'})


@app.route("/faq")
def faq():
    return render_template('faq.html')


@app.route("/new")
@login_required
def new():
    return render_template('new.html')


@app.route("/Teachers")
@login_required
def teachers():
    return render_template('Teachers.html')


@app.route("/meets-subj1")
@login_required
def meets1():
    if request.method == "POST":
        link = request.form['linkk']
        try:
            db.session.add(link)
            db.session.commit()
            return redirect("/meets-subj1")
        except:
            return "При добавлении ссылки произошла ошибка"
    else:
        questions = usee.query.order_by(usee.date.desc()).all()
        return render_template('meets.html', questions=questions)


@app.route("/footer")
@login_required
def footer():
    return render_template('footer.html')


@app.route("/header")
@login_required
def header():
    return render_template('header.html')


@app.route("/")
@app.route("/main")
def about():
    return render_template('main.html')


@app.route("/meet-create", methods=['POST', 'GET'])
@login_required
def meet_create():
    if request.method == "POST":
        quote = request.form['quote']
        topic = request.form['topic']
        possible_days = request.form['possible_days']
        possible_day = list(possible_days)
        possible_days = ""
        possible_day[10] = " "
        constant_user = User.query.filter_by(id=current_user.id).first()
        email = constant_user.email
        for i in possible_day:
            possible_days = possible_days + i
        clas = request.form['class']

        use = usee(quote=quote, topic=topic, possible_days=possible_days, clas=clas, confirmed=0, email=email)
        try:
            db.session.add(use)
            db.session.commit()
            return redirect('/meets-subj1')
        except:
            return "При добавлении запроса произошла ошибка"

    else:
        return render_template('create-meet.html')


'''class_5 = Class.query.filter_by(name="5").first()
class_6 = Class.query.filter_by(name="6").first()
class_7 = Class.query.filter_by(name="7").first()
class_8 = Class.query.filter_by(name="8").first()
class_9 = Class.query.filter_by(name="9").first()

if not class_5:
    class_5 = Class(name="5")
    db.session.add(class_5)
if not class_6:
    class_6 = Class(name="6")
    db.session.add(class_6)
if not class_7:
    class_7 = Class(name="7")
    db.session.add(class_7)
if not class_8:
    class_8 = Class(name="8")
    db.session.add(class_8)
if not class_9:
    class_9 = Class(name="9")
    db.session.add(class_9)

db.session.commit()'''
if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5000, debug=True)
