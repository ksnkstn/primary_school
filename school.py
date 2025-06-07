from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

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

# Модель для домашнего задания с добавленной колонкой class_name
class Homework(db.Model):
    __tablename__ = 'homework'
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(100), nullable=False)
    content = db.Column(db.String(200))
    date = db.Column(db.Date, nullable=False)
    class_name = db.Column(db.String(10), nullable=False)  # Новая колонка для класса

# Маршруты
@school.route('/teacher_journal')
@school.route('/')
def teacher_journal():
    class_id = request.args.get('class_id', '1A')
    subject_id = request.args.get('subject_id', 'math')
    student_id = request.args.get('student_id', type=int)
    date_str = request.args.get('date')

    # Маппинг subject_id к полному названию предмета
    subject_map = {'math': 'Математика', 'rus': 'Русский язык', 'history': 'История'}
    subject = subject_map.get(subject_id, 'Математика')

    # Фильтрация учеников по классу
    students = Student.query.filter_by(class_name=class_id).all()

    # Фиксированные даты (можно заменить на динамические из базы)
    dates = [datetime.strptime(date, '%d.%m.%Y').date() for date in ['12.05.2025', '14.05.2025', '18.05.2025', '20.05.2025']]

    # Фильтрация оценок по классу, предмету и датам
    grades = Grade.query.filter(
        Grade.student_id.in_([s.id for s in students]),
        Grade.subject == subject,
        Grade.date.in_(dates)
    ).all()

    # Фильтрация домашних заданий по классу, предмету и датам
    homework = Homework.query.filter(
        Homework.class_name == class_id,
        Homework.subject == subject,
        Homework.date.in_(dates)
    ).all()

    # Если переданы student_id и date, фильтруем данные для одной ячейки
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

    print(f"Class: {class_id}, Subject: {subject}")
    print(f"Students: {len(students)}")
    for s in students:
        print(f"Student: id={s.id}, name={s.name}")
    print(f"Grades: {len(grades)}")
    for g in grades:
        print(f"Grade: student_id={g.student_id}, grade={g.grade}, date={g.date}")
    print(f"Homework: {len(homework)}")
    for h in homework:
        print(f"Homework: date={h.date}, content={h.content}, class={h.class_name}")

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

    print(f"Received save_grade request: student_id={student_id}, grade={grade_value}, date={date_str}, subject_id={subject_id}, grade_id={grade_id}")

    if grade_value < 1 or grade_value > 5:
        print(f"Invalid grade value: {grade_value}. Must be between 1 and 5.")
        return jsonify({'status': 'error', 'message': 'Grade must be between 1 and 5'})

    try:
        date = datetime.strptime(date_str, '%d.%m.%Y').date()
    except ValueError as e:
        print(f"Error parsing date: {e}")
        return jsonify({'status': 'error', 'message': 'Invalid date format'})

    try:
        if grade_id:
            grade = Grade.query.get(int(grade_id))
            if not grade or grade.student_id != student_id or grade.subject != subject or grade.date != date:
                return jsonify({'status': 'error', 'message': 'Grade not found or mismatch'})
            print(f"Updating grade id={grade_id} for student_id={student_id}, date={date}")
            grade.grade = grade_value
        else:
            print(f"Creating new grade for student_id={student_id}, date={date}, subject={subject}")
            new_grade = Grade(student_id=student_id, subject=subject, grade=grade_value, date=date)
            db.session.add(new_grade)

        db.session.commit()
        print(f"Grade saved successfully for student_id={student_id}, date={date}")
        return jsonify({'status': 'success'})
    except Exception as e:
        db.session.rollback()
        print(f"Error saving grade: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@school.route('/save_homework', methods=['POST'])
def save_homework():
    data = request.get_json()
    date_str = data['date']
    content = data['content']
    subject_id = data.get('subject_id', 'math')
    class_id = data.get('class_id', '1A')  # Получаем class_id из запроса
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

# Инициализация базы данных
with school.app_context():
    db.create_all()

if __name__ == "__main__":
    school.run(debug=True)