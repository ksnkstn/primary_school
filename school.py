from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

school = Flask(__name__)


# Настройка подключения к базе
school.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:183428@localhost:5432/school_db'
school.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
print("hello world!")
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

# Маршруты
@school.route('/teacher_journal')
@school.route('/')
def teacher_journal():
    student_id = request.args.get('student_id', type=int)
    date_str = request.args.get('date')

    students = Student.query.filter_by(class_name='1A').all()
    subjects = ['Математика']
    dates = [datetime.strptime(date, '%d.%m.%Y').date() for date in ['12.05.2025', '14.05.2025', '18.05.2025', '20.05.2025']]
    grades = Grade.query.filter(Grade.date.in_(dates), Grade.subject == 'Математика').all()
    homework = Homework.query.filter(Homework.date.in_(dates), Homework.subject == 'Математика').all()

    # Если переданы student_id и date, фильтруем данные для одной ячейки
    if student_id and date_str:
        date = datetime.strptime(date_str, '%d.%m.%Y').date()
        students = Student.query.filter_by(id=student_id).all()
        dates = [date]
        grades = Grade.query.filter(Grade.student_id == student_id, Grade.date == date, Grade.subject == 'Математика').all()
        homework = Homework.query.filter(Homework.date == date, Homework.subject == 'Математика').all()

    print(f"Students: {len(students)}")
    for s in students:
        print(f"Student: id={s.id}, name={s.name}")
    print(f"Grades: {len(grades)}")
    for g in grades:
        print(f"Grade: student_id={g.student_id}, grade={g.grade}, date={g.date}")
    print(f"Homework: {len(homework)}")
    for h in homework:
        print(f"Homework: date={h.date}, content={h.content}")

    return render_template('teacher_journal.html', show_header=True, students=students, subjects=subjects, dates=dates, grades=grades, homework=homework)

@school.route('/save_grade', methods=['POST'])
def save_grade():
    data = request.get_json()
    student_id = int(data['student_id'])
    grade_value = int(data['grade'])
    date_str = data['date']
    subject = 'Математика'
    grade_id = data.get('grade_id')  # Если передан grade_id, это редактирование

    print(f"Received save_grade request: student_id={student_id}, grade={grade_value}, date={date_str}, grade_id={grade_id}")

    # Проверка диапазона оценки
    if grade_value < 1 or grade_value > 5:
        print(f"Invalid grade value: {grade_value}. Must be between 1 and 5.")
        return jsonify({'status': 'error', 'message': 'Grade must be between 1 and 5'})

    try:
        date = datetime.strptime(date_str, '%d.%m.%Y').date()
    except ValueError as e:
        print(f"Error parsing date: {e}")
        return jsonify({'status': 'error', 'message': 'Invalid date format'})

    try:
        if grade_id:  # Редактирование существующей оценки
            grade = Grade.query.get(int(grade_id))
            if not grade:
                return jsonify({'status': 'error', 'message': 'Grade not found'})
            print(f"Updating grade id={grade_id} for student_id={student_id}, date={date}")
            grade.grade = grade_value
        else:  # Добавление новой оценки
            print(f"Creating new grade for student_id={student_id}, date={date}")
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
    subject = 'Математика'

    date = datetime.strptime(date_str, '%d.%m.%Y').date()

    existing_homework = Homework.query.filter_by(date=date, subject=subject).first()

    if existing_homework:
        existing_homework.content = content
    else:
        new_homework = Homework(subject=subject, content=content, date=date)
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