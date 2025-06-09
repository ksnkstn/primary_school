from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import pandas as pd
import math
from sqlalchemy.orm import relationship  # Импорт оставлен, но не используется

school = Flask(__name__)

# Настройка подключения к базе
school.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:183428@localhost:5432/school_db'
school.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(school)

# Пользовательский фильтр для Jinja2
def string_to_date_filter(date_str):
    return datetime.strptime(date_str, '%d.%m.%Y').date()

def get_weekday_filter(date):
    return date.weekday()

school.jinja_env.filters['string_to_date'] = string_to_date_filter
school.jinja_env.filters['get_weekday'] = get_weekday_filter

# Модель для учеников
class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    class_name = db.Column(db.String(10), nullable=False)

class StudentProfile(db.Model):
    __tablename__ = 'student_profile'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, nullable=False)  # Убрано ForeignKey
    address = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date)
    parent_name = db.Column(db.String(100))
    parent_phone = db.Column(db.String(20))
    enrollment_date = db.Column(db.Date)
    photo_url = db.Column(db.String(255))
    notes = db.Column(db.Text)

# Модель для учителей
class Teacher(db.Model):
    __tablename__ = 'teachers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class TeacherProfile(db.Model):
    __tablename__ = 'teacher_profile'
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, nullable=False)  # Убрано ForeignKey
    address = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    date_of_employment = db.Column(db.Date)
    email = db.Column(db.String(100))
    photo_url = db.Column(db.String(255))
    notes = db.Column(db.Text)
    department = db.Column(db.String(100))  # Например, отдел или предметная область

# Модель для родителей
class ParentProfile(db.Model):
    __tablename__ = 'parent_profile'
    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, nullable=False)  # Уникальный идентификатор родителя
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    photo_url = db.Column(db.String(255))
    workplace = db.Column(db.String(100))
    children = db.Column(db.String(200))  # Список детей (например, "Игорь Баранов, Анна Иванова")
    notes = db.Column(db.Text)

# Модель для оценок
class Grade(db.Model):
    __tablename__ = 'grades'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    grade = db.Column(db.Integer)
    date = db.Column(db.Date, nullable=False)
    comment = db.Column(db.String(200))

# Модель для домашнего задания
class Homework(db.Model):
    __tablename__ = 'homework'
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(100), nullable=False)
    content = db.Column(db.String(200))
    date = db.Column(db.Date, nullable=False)
    class_name = db.Column(db.String(10), nullable=False)

# Модель для расписания учителей
class Schedule(db.Model):
    __tablename__ = 'schedules'
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.String(20), nullable=False)
    subject = db.Column(db.String(100))
    class_name = db.Column(db.String(20))
    room = db.Column(db.String(10))

# Модель для уроков (расписания классов)
class Lesson(db.Model):
    __tablename__ = 'lessons'
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.String(20), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    class_name = db.Column(db.String(20), nullable=False)
    room = db.Column(db.String(10), nullable=False)
    __table_args__ = (
        db.UniqueConstraint('teacher_id', 'date', 'time', 'class_name', name='unique_lesson'),
    )

# Модель для успеваемости по четвертям
class Progress(db.Model):
    __tablename__ = 'progress'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    quarter = db.Column(db.Integer, nullable=False)
    grades = db.Column(db.String(100))
    average_grade = db.Column(db.Float)
    final_grade = db.Column(db.Integer, nullable=True)

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
             ['12.06.2025', '14.06.2025', '18.06.2025', '20.06.2025']]

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
    comment = data.get('comment', '')
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
            grade.comment = comment
        else:
            new_grade = Grade(student_id=student_id, subject=subject, grade=grade_value, date=date, comment=comment)
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
    student_id = 1  # Баранов Игорь Витальевич
    student = db.session.get(Student, student_id)
    if not student:
        return "Ученик не найден", 404

    now = datetime.now()
    current_week_start = now.date() - timedelta(days=now.weekday())
    current_week_end = current_week_start + timedelta(days=4)

    days = [{'day_name': d.strftime('%A'), 'date': d.strftime('%d.%m.%Y')}
            for d in pd.date_range(current_week_start, current_week_end).tolist() if d.weekday() < 5]

    grades = Grade.query.filter(
        Grade.student_id == student_id,
        Grade.date.between(current_week_start, current_week_end)
    ).all()

    lessons = db.session.query(Lesson, Teacher.name).outerjoin(Teacher, Lesson.teacher_id == Teacher.id).filter(
        Lesson.class_name == student.class_name,
        Lesson.date.between(current_week_start, current_week_end)
    ).order_by(Lesson.time).all()

    homework = Homework.query.filter(
        Homework.class_name == student.class_name,
        Homework.date.between(current_week_start, current_week_end)
    ).all()

    daily_data = {}
    for day in days:
        date_str = day['date']
        date = datetime.strptime(date_str, '%d.%m.%Y').date()
        daily_data[date_str] = {
            'date': date,
            'grades': [{'id': g.id, 'grade': g.grade, 'comment': g.comment, 'date': g.date.strftime('%d.%m.%Y'), 'subject': g.subject} for g in grades if g.date == date],
            'lessons': [{'time': l.time, 'subject': l.subject, 'teacher_name': t or 'Не указан', 'room': l.room} for l, t in lessons if l.date == date],
            'homework': [{'subject': h.subject, 'content': h.content, 'date': h.date.strftime('%d.%m.%Y')} for h in homework if h.date == date]
        }

    return render_template('student_diary.html', show_header=True, student=student, current_week_start=current_week_start.strftime('%d.%m.%Y'), current_week_end=current_week_end.strftime('%d.%m.%Y'), daily_data=daily_data, days=days)

@school.route('/student_diary_data')
def student_diary_data():
    student_id = 1
    student = db.session.get(Student, student_id)
    if not student:
        return jsonify({'error': 'Ученик не найден'}), 404

    start_date = datetime.strptime(request.args.get('start_date'), '%d.%m.%Y').date()
    end_date = datetime.strptime(request.args.get('end_date'), '%d.%m.%Y').date()

    days = [{'day_name': d.strftime('%A'), 'date': d.strftime('%d.%m.%Y')}
            for d in pd.date_range(start_date, end_date).tolist() if d.weekday() < 5]

    grades = Grade.query.filter(
        Grade.student_id == student_id,
        Grade.date.between(start_date, end_date)
    ).all()

    lessons = db.session.query(Lesson, Teacher.name).outerjoin(Teacher, Lesson.teacher_id == Teacher.id).filter(
        Lesson.class_name == student.class_name,
        Lesson.date.between(start_date, end_date)
    ).order_by(Lesson.time).all()

    homework = Homework.query.filter(
        Homework.class_name == student.class_name,
        Homework.date.between(start_date, end_date)
    ).all()

    daily_data = {}
    for day in days:
        date_str = day['date']
        date = datetime.strptime(date_str, '%d.%m.%Y').date()
        daily_data[date_str] = {
            'date': date,
            'grades': [{'id': g.id, 'grade': g.grade, 'comment': g.comment, 'date': g.date.strftime('%d.%m.%Y'), 'subject': g.subject} for g in grades if g.date == date],
            'lessons': [{'time': l.time, 'subject': l.subject, 'teacher_name': t or 'Не указан', 'room': l.room} for l, t in lessons if l.date == date],
            'homework': [{'subject': h.subject, 'content': h.content, 'date': h.date.strftime('%d.%m.%Y')} for h in homework if h.date == date]
        }

    return jsonify({
        'days': days,
        'daily_data': daily_data,
        'start_date': start_date.strftime('%d.%m.%Y'),
        'end_date': end_date.strftime('%d.%m.%Y')
    })

@school.route('/authorization')
def authorization():
    return render_template('authorization.html', show_header=False)

@school.route('/teacher_schedule')
def teacher_schedule():
    start_date = datetime.now().date() - timedelta(days=datetime.now().weekday())
    end_date = start_date + timedelta(days=4)
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
    start_date = datetime.now().date() - timedelta(days=datetime.now().weekday())
    end_date = start_date + timedelta(days=4)
    class_id = request.args.get('class_id', '1A').upper()
    days = [{'day_name': d.strftime('%A'), 'date': d.strftime('%d.%m.%Y')}
            for d in pd.date_range(start_date, end_date).tolist() if d.weekday() < 5]
    lessons = db.session.query(Lesson, Teacher.name).outerjoin(Teacher, Lesson.teacher_id == Teacher.id).filter(
        Lesson.class_name == class_id,
        Lesson.date.between(start_date, end_date)
    ).all()
    schedule = {}
    time_slots = ['08:00-08:45', '08:50-09:35', '09:40-10:25', '10:45-11:30', '11:35-12:20', '12:25-13:10']
    for t in time_slots:
        schedule[t] = {'time': t, 'lessons': []}
    for lesson, teacher_name in lessons:
        schedule[lesson.time]['lessons'].append({
            'date': lesson.date.strftime('%d.%m.%Y'),
            'subject': lesson.subject,
            'teacher_name': teacher_name or 'Не указан',
            'room': lesson.room
        })
    return render_template('class_schedule.html',
                           start_date=start_date.strftime('%d.%m.%Y'),
                           end_date=end_date.strftime('%d.%m.%Y'),
                           class_id=class_id,
                           days=days,
                           schedule=list(schedule.values()))

@school.route('/class_schedule_data')
def class_schedule_data():
    start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d').date()
    end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d').date()
    class_id = request.args.get('class_id', '1A').upper()
    days = [{'day_name': d.strftime('%A'), 'date': d.strftime('%d.%m.%Y')}
            for d in pd.date_range(start_date, end_date).tolist() if d.weekday() < 5]
    lessons = db.session.query(Lesson, Teacher.name).outerjoin(Teacher, Lesson.teacher_id == Teacher.id).filter(
        Lesson.class_name == class_id,
        Lesson.date.between(start_date, end_date)
    ).all()
    schedule = {}
    time_slots = ['08:00-08:45', '08:50-09:35', '09:40-10:25', '10:45-11:30', '11:35-12:20', '12:25-13:10']
    for t in time_slots:
        schedule[t] = {'time': t, 'lessons': []}
    for lesson, teacher_name in lessons:
        schedule[lesson.time]['lessons'].append({
            'date': lesson.date.strftime('%d.%m.%Y'),
            'subject': lesson.subject,
            'teacher_name': teacher_name or 'Не указан',
            'room': lesson.room
        })
    return jsonify({'days': days, 'schedule': list(schedule.values())})

@school.route('/progress')
def progress():
    student_id = 1
    student = db.session.get(Student, student_id)
    if not student:
        return "Ученик не найден", 404

    progress_data = Progress.query.filter_by(student_id=student_id).all()

    return render_template('progress.html', show_header=True, student=student, progress_data=progress_data)

@school.route('/summary')
def summary():
    student_id = 1
    student = db.session.get(Student, student_id)
    if not student:
        return "Ученик не найден", 404

    progress_data = Progress.query.filter_by(student_id=student_id).all()

    subjects = ['Английский язык', 'История', 'Литература', 'Логика', 'Математика', 'Окружающий мир', 'Русский язык', 'Физкультура']
    progress_by_subject = {subject: {q: None for q in range(1, 5)} for subject in subjects}
    for progress in progress_data:
        progress_by_subject[progress.subject][progress.quarter] = progress

    return render_template('summary.html', show_header=True, student=student, progress_by_subject=progress_by_subject)

def get_parent_children(parent_id):
    children = Student.query.filter(
        Student.id.in_([1, 7])
    ).all()
    return children

@school.route('/parent_diary')
def parent_diary():
    child_id = request.args.get('child_id', type=int, default=1)
    student = db.session.get(Student, child_id)
    if not student:
        return "Ученик не найден", 404

    now = datetime.now()
    current_week_start = now.date() - timedelta(days=now.weekday())
    current_week_end = current_week_start + timedelta(days=4)

    days = [{'day_name': d.strftime('%A'), 'date': d.strftime('%d.%m.%Y')}
            for d in pd.date_range(current_week_start, current_week_end).tolist() if d.weekday() < 5]

    grades = Grade.query.filter(
        Grade.student_id == child_id,
        Grade.date.between(current_week_start, current_week_end)
    ).all()

    lessons = db.session.query(Lesson, Teacher.name).outerjoin(Teacher, Lesson.teacher_id == Teacher.id).filter(
        Lesson.class_name == student.class_name,
        Lesson.date.between(current_week_start, current_week_end)
    ).order_by(Lesson.time).all()

    homework = Homework.query.filter(
        Homework.class_name == student.class_name,
        Homework.date.between(current_week_start, current_week_end)
    ).all()

    daily_data = {}
    for day in days:
        date_str = day['date']
        date = datetime.strptime(date_str, '%d.%m.%Y').date()
        daily_data[date_str] = {
            'date': date,
            'grades': [{'id': g.id, 'grade': g.grade, 'comment': g.comment, 'date': g.date.strftime('%d.%m.%Y'), 'subject': g.subject} for g in grades if g.date == date],
            'lessons': [{'time': l.time, 'subject': l.subject, 'teacher_name': t or 'Не указан', 'room': l.room} for l, t in lessons if l.date == date],
            'homework': [{'subject': h.subject, 'content': h.content, 'date': h.date.strftime('%d.%m.%Y')} for h in homework if h.date == date]
        }

    children = get_parent_children(1)
    return render_template('parent_diary.html', show_header=True, student=student, current_week_start=current_week_start.strftime('%d.%m.%Y'), current_week_end=current_week_end.strftime('%d.%m.%Y'), daily_data=daily_data, days=days, children=children, selected_child_id=child_id)

@school.route('/parent_diary_data')
def parent_diary_data():
    child_id = request.args.get('child_id', type=int, default=1)
    student = db.session.get(Student, child_id)
    if not student:
        return jsonify({'error': 'Ученик не найден'}), 404

    start_date = datetime.strptime(request.args.get('start_date'), '%d.%m.%Y').date()
    end_date = datetime.strptime(request.args.get('end_date'), '%d.%m.%Y').date()

    days = [{'day_name': d.strftime('%A'), 'date': d.strftime('%d.%m.%Y')}
            for d in pd.date_range(start_date, end_date).tolist() if d.weekday() < 5]

    grades = Grade.query.filter(
        Grade.student_id == child_id,
        Grade.date.between(start_date, end_date)
    ).all()

    lessons = db.session.query(Lesson, Teacher.name).outerjoin(Teacher, Lesson.teacher_id == Teacher.id).filter(
        Lesson.class_name == student.class_name,
        Lesson.date.between(start_date, end_date)
    ).order_by(Lesson.time).all()

    homework = Homework.query.filter(
        Homework.class_name == student.class_name,
        Homework.date.between(start_date, end_date)
    ).all()

    daily_data = {}
    for day in days:
        date_str = day['date']
        date = datetime.strptime(date_str, '%d.%m.%Y').date()
        daily_data[date_str] = {
            'date': date,
            'grades': [{'id': g.id, 'grade': g.grade, 'comment': g.comment, 'date': g.date.strftime('%d.%m.%Y'), 'subject': g.subject} for g in grades if g.date == date],
            'lessons': [{'time': l.time, 'subject': l.subject, 'teacher_name': t or 'Не указан', 'room': l.room} for l, t in lessons if l.date == date],
            'homework': [{'subject': h.subject, 'content': h.content, 'date': h.date.strftime('%d.%m.%Y')} for h in homework if h.date == date]
        }

    return jsonify({
        'days': days,
        'daily_data': daily_data,
        'start_date': start_date.strftime('%d.%m.%Y'),
        'end_date': end_date.strftime('%d.%m.%Y')
    })

@school.route('/parent_progress')
def parent_progress():
    child_id = request.args.get('child_id', type=int, default=1)
    student = db.session.get(Student, child_id)
    if not student:
        return "Ученик не найден", 404

    progress_data = Progress.query.filter_by(student_id=child_id).all()

    subjects = ['Английский язык', 'История', 'Литература', 'Логика', 'Математика', 'Окружающий мир', 'Русский язык', 'Физкультура']
    progress_by_subject = {subject: {q: None for q in range(1, 5)} for subject in subjects}
    for progress in progress_data:
        progress_by_subject[progress.subject][progress.quarter] = progress

    children = get_parent_children(1)
    return render_template('parent_progress.html', show_header=True, student=student, progress_by_subject=progress_by_subject, children=children, selected_child_id=child_id, quarter=request.args.get('quarter', type=int, default=1), class_name=student.class_name)

@school.route('/parent_summary')
def parent_summary():
    child_id = request.args.get('child_id', type=int, default=1)
    student = db.session.get(Student, child_id)
    if not student:
        return "Ученик не найден", 404

    progress_data = Progress.query.filter_by(student_id=child_id).all()

    subjects = ['Английский язык', 'История', 'Литература', 'Логика', 'Математика', 'Окружающий мир', 'Русский язык', 'Физкультура']
    progress_by_subject = {subject: {q: None for q in range(1, 5)} for subject in subjects}
    for progress in progress_data:
        progress_by_subject[progress.subject][progress.quarter] = progress

    children = get_parent_children(1)
    return render_template('parent_summary.html', show_header=True, student=student, progress_by_subject=progress_by_subject, children=children, selected_child_id=child_id, quarter=request.args.get('quarter', type=int, default=1), class_name=student.class_name)

@school.route('/student_profile')
def student_profile_route():
    student_id = 1
    student = db.session.get(Student, student_id)
    if not student:
        return "Ученик не найден", 404

    profile = db.session.execute(db.select(StudentProfile).where(StudentProfile.student_id == student_id)).scalar()
    profile_data = {
        "name": student.name,
        "class_name": student.class_name,
        "address": profile.address if profile and profile.address else "Не указано",
        "phone": profile.phone if profile and profile.phone else "Не указано",
        "date_of_birth": profile.date_of_birth.strftime('%d.%m.%Y') if profile and profile.date_of_birth else "Не указано",
        "parent_name": profile.parent_name if profile and profile.parent_name else "Не указано",
        "parent_phone": profile.parent_phone if profile and profile.parent_phone else "Не указано",
        "enrollment_date": profile.enrollment_date.strftime('%d.%m.%Y') if profile and profile.enrollment_date else "Не указано",
        "photo_url": profile.photo_url if profile and profile.photo_url else "/static/images/default.jpg",
        "notes": profile.notes if profile and profile.notes else "Нет примечаний"
    }
    return render_template('student_profile.html', student_profile=profile_data)

@school.route('/teacher_profile')
def teacher_profile_route():
    teacher_id = 1
    teacher = db.session.get(Teacher, teacher_id)
    if not teacher:
        return "Учитель не найден", 404

    profile = db.session.execute(db.select(TeacherProfile).where(TeacherProfile.teacher_id == teacher_id)).scalar()
    profile_data = {
        "name": teacher.name,
        "address": profile.address if profile and profile.address else "Не указано",
        "phone": profile.phone if profile and profile.phone else "Не указано",
        "date_of_employment": profile.date_of_employment.strftime('%d.%m.%Y') if profile and profile.date_of_employment else "Не указано",
        "email": profile.email if profile and profile.email else "Не указано",
        "photo_url": profile.photo_url if profile and profile.photo_url else "/static/images/default.jpg",
        "notes": profile.notes if profile and profile.notes else "Нет примечаний",
        "department": profile.department if profile and profile.department else "Не указано"
    }
    return render_template('teacher_profile.html', teacher_profile=profile_data)

@school.route('/parent_profile')
def parent_profile_route():
    parent_id = 1  # Пример ID для родителя (замените на реальный или динамический)
    profile = db.session.execute(db.select(ParentProfile).where(ParentProfile.parent_id == parent_id)).scalar()
    if not profile:
        return "Родитель не найден", 404

    children = get_parent_children(parent_id)
    children_names = ", ".join([child.name for child in children]) if children else "Нет детей"

    profile_data = {
        "name": profile.name,
        "address": profile.address if profile.address else "Не указано",
        "phone": profile.phone if profile.phone else "Не указано",
        "email": profile.email if profile.email else "Не указано",
        "workplace": profile.workplace if profile.workplace else "Не указано",
        "photo_url": profile.photo_url if profile.photo_url else "/static/images/default.jpg",
        "children": children_names,
        "notes": profile.notes if profile.notes else "Нет примечаний"
    }

    selected_child_id = request.args.get('child_id', type=int, default=1)
    return render_template('parent_profile.html', parent_profile=profile_data, selected_child_id=selected_child_id)

# Обновление маршрута /profile для родительской роли
@school.route('/profile')
def profile():
    role = request.args.get('role', 'student')  # По умолчанию 'student', если параметр не указан
    child_id = request.args.get('child_id', type=int, default=1)
    if role == 'teacher':
        return redirect(url_for('teacher_profile_route'))
    elif role == 'parent':
        return redirect(url_for('parent_profile_route', child_id=child_id))
    else:  # 'student' или любой другой
        return redirect(url_for('student_profile_route'))

# Инициализация базы данных
with school.app_context():
    db.create_all()

if __name__ == "__main__":
    school.run(debug=True)