from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import pandas as pd

school = Flask(__name__)

# Настройка подключения к базе
school.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:183428@localhost:5432/school_db'
school.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(school)

# Модель для учеников
class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    class_name = db.Column(db.String(10), nullable=False)

# Модель для оценок
class Grade(db.Model):
    __tablename__ = 'grades'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    grade = db.Column(db.Integer)
    date = db.Column(db.Date, nullable=False)

# Модель для домашнего задания
class Homework(db.Model):
    __tablename__ = 'homework'
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(100), nullable=False)
    content = db.Column(db.String(200))
    date = db.Column(db.Date, nullable=False)
    class_name = db.Column(db.String(10), nullable=False)

# Модель для преподавателей
class Teacher(db.Model):
    __tablename__ = 'teachers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

# Модель для расписания
class Schedule(db.Model):
    __tablename__ = 'schedules'
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.String(20), nullable=False)
    subject = db.Column(db.String(100))
    class_name = db.Column(db.String(20))
    room = db.Column(db.String(10))

# Маршруты
@school.route('/teacher_journal')
@school.route('/')
def teacher_journal():
    class_id = request.args.get('class_id', '1A')
    subject_id = request.args.get('subject_id', 'math')
    student_id = request.args.get('student_id', type=int)
    date_str = request.args.get('date')

    subject_map = {'math': 'Математика', 'rus': 'Русский язык', 'history': 'История'}
    subject = subject_map.get(subject_id, 'Математика')

    students = Student.query.filter_by(class_name=class_id).all()
    dates = [datetime.strptime(date, '%d.%m.%Y').date() for date in
             ['12.05.2025', '14.05.2025', '18.05.2025', '20.05.2025']]

    grades = Grade.query.filter(
        Grade.student_id.in_([s.id for s in students]),
        Grade.subject == subject,
        Grade.date.in_(dates)
    ).all()

    homework = Homework.query.filter(
        Homework.class_name == class_id,
        Homework.subject == subject,
        Homework.date.in_(dates)
    ).all()

    if student_id and date_str:
        date = datetime.strptime(date_str, '%d.%m.%Y').date()
        students = Student.query.filter_by(id=student_id, class_name=class_id).all()
        dates = [date]
        grades = Grade.query.filter(
            Grade.student_id == student_id,
            Grade.date == date,
            Grade.subject == subject
        ).all()
        homework = Homework.query.filter(
            Homework.date == date,
            Homework.subject == subject,
            Homework.class_name == class_id
        ).all()

    return render_template(
        'teacher_journal.html',
        show_header=True,
        students=students,
        subjects=['Математика', 'Русский язык', 'История'],
        dates=dates,
        grades=grades,
        homework=homework,
        class_id=class_id,
        subject_id=subject_id
    )

@school.route('/save_grade', methods=['POST'])
def save_grade():
    data = request.get_json()
    student_id = int(data['student_id'])
    grade_value = int(data['grade'])
    date_str = data['date']
    subject_id = data.get('subject_id', 'math')
    subject_map = {'math': 'Математика', 'rus': 'Русский язык', 'history': 'История'}
    subject = subject_map.get(subject_id, 'Математика')
    grade_id = data.get('grade_id')

    if grade_value < 1 or grade_value > 5:
        return jsonify({'status': 'error', 'message': 'Grade must be between 1 and 5'})

    try:
        date = datetime.strptime(date_str, '%d.%m.%Y').date()
    except ValueError:
        return jsonify({'status': 'error', 'message': 'Invalid date format'})

    try:
        if grade_id:
            grade = Grade.query.get(int(grade_id))
            if not grade or grade.student_id != student_id or grade.subject != subject or grade.date != date:
                return jsonify({'status': 'error', 'message': 'Grade not found or mismatch'})
            grade.grade = grade_value
        else:
            new_grade = Grade(student_id=student_id, subject=subject, grade=grade_value, date=date)
            db.session.add(new_grade)

        db.session.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)})

@school.route('/save_homework', methods=['POST'])
def save_homework():
    data = request.get_json()
    date_str = data['date']
    content = data['content']
    subject_id = data.get('subject_id', 'math')
    class_id = data.get('class_id', '1A')
    subject_map = {'math': 'Математика', 'rus': 'Русский язык', 'history': 'История'}
    subject = subject_map.get(subject_id, 'Математика')

    date = datetime.strptime(date_str, '%d.%m.%Y').date()

    existing_homework = Homework.query.filter_by(date=date, subject=subject, class_name=class_id).first()

    if existing_homework:
        existing_homework.content = content
    else:
        new_homework = Homework(subject=subject, content=content, date=date, class_name=class_id)
        db.session.add(new_homework)

    db.session.commit()
    return jsonify({'status': 'success'})

@school.route('/student_diary')
def student_diary():
    grades = Grade.query.all()
    return render_template('student_diary.html', show_header=True, grades=grades)

@school.route('/authorization')
def authorization():
    return render_template('authorization.html', show_header=False)

@school.route('/teacher_schedule')
def teacher_schedule():
    start_date = datetime.now().date() - timedelta(days=datetime.now().weekday())
    end_date = start_date + timedelta(days=4)  # 5 дней (понедельник-пятница)
    days = [{'day_name': d.strftime('%A'), 'date': d.strftime('%d.%m.%Y')}
            for d in pd.date_range(start_date, end_date).tolist() if d.weekday() < 5]
    schedules = Schedule.query.filter(
        Schedule.teacher_id == 1,
        Schedule.date.between(start_date, end_date)
    ).all()
    schedule = {}
    times = ['08:00-08:45', '08:50-09:35', '09:40-10:25', '10:45-11:30', '11:35-12:20', '12:25-13:10']
    for t in times:
        schedule[t] = {'time': t, 'lessons': []}
    for s in schedules:
        schedule[s.time]['lessons'].append({
            'date': s.date.strftime('%d.%m.%Y'),
            'subject': s.subject,
            'class_name': s.class_name,
            'room': s.room
        })
    return render_template('teacher_schedule.html',
                           start_date=start_date.strftime('%d.%m.%Y'),
                           end_date=end_date.strftime('%d.%m.%Y'),
                           days=days,
                           schedule=list(schedule.values()))

@school.route('/teacher_schedule_data')
def teacher_schedule_data():
    start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d').date()
    end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d').date()
    schedules = Schedule.query.filter(
        Schedule.teacher_id == 1,
        Schedule.date.between(start_date, end_date)
    ).all()

    days = [{'day_name': d.strftime('%A'), 'date': d.strftime('%d.%m.%Y')}
            for d in pd.date_range(start_date, end_date).tolist() if d.weekday() < 5]
    schedule = {}
    times = ['08:00-08:45', '08:50-09:35', '09:40-10:25', '10:45-11:30', '11:35-12:20', '12:25-13:10']
    for t in times:
        schedule[t] = {'time': t, 'lessons': []}
    for s in schedules:
        schedule[s.time]['lessons'].append({
            'date': s.date.strftime('%d.%m.%Y'),
            'subject': s.subject,
            'class_name': s.class_name,
            'room': s.room
        })

    return jsonify({'days': days, 'schedule': list(schedule.values())})

@school.route('/class_schedule')
def class_schedule():
    return render_template('class_schedule.html')

# Инициализация базы данных
with school.app_context():
    db.create_all()

if __name__ == "__main__":
    school.run(debug=True)