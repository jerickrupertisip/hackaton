import sqlite3
import csv
import os
from datetime import datetime

def get_db_connection(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA foreign_keys = ON;')
    return conn

def create_schema(conn, schema_path):
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    conn.executescript(schema_sql)
    conn.commit()

def insert_room_categories(conn, categories):
    for cat in categories:
        conn.execute('INSERT OR IGNORE INTO room_category (name) VALUES (?)', (cat,))
    conn.commit()

def insert_modalities(conn, modalities):
    for mod in modalities:
        conn.execute('INSERT OR IGNORE INTO modality (name) VALUES (?)', (mod,))
    conn.commit()

def insert_courses(conn, courses_dir):
    course_codes = []
    for fname in os.listdir(courses_dir):
        if fname.endswith('.csv'):
            code = fname.replace('.csv', '').upper()
            conn.execute('INSERT OR IGNORE INTO course (code) VALUES (?)', (code,))
            course_codes.append(code)
    conn.commit()
    return course_codes

def get_id(conn, table, col, value):
    cur = conn.execute(f'SELECT id FROM {table} WHERE {col} = ?', (value,))
    row = cur.fetchone()
    return row[0] if row else None

def insert_rooms(conn, rooms_csv):
    with open(rooms_csv, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cat_id = get_id(conn, 'room_category', 'name', row['category'])
            conn.execute('INSERT OR IGNORE INTO room (room_code, category_id, capacity, floor) VALUES (?, ?, ?, ?)',
                         (row['room_id'], cat_id, int(row['capacity']), int(row['floor'])))
    conn.commit()

def insert_course_subjects(conn, courses_dir):
    for fname in os.listdir(courses_dir):
        if fname.endswith('.csv'):
            code = fname.replace('.csv', '').upper()
            course_id = get_id(conn, 'course', 'code', code)
            with open(os.path.join(courses_dir, fname), newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    room_cat_id = get_id(conn, 'room_category', 'name', row['preferred_room'])
                    modality_id = get_id(conn, 'modality', 'name', row['modality'])
                    conn.execute('''INSERT OR IGNORE INTO course_subject
                        (course_id, subject_code, year, semester, units, preferred_room_category_id, modality_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?)''',
                        (course_id, row['subject'], int(row['year']), int(row['semester']), float(row['units']), room_cat_id, modality_id))
    conn.commit()

def insert_teachers(conn, teachers_csv):
    teacher_ids = {}
    with open(teachers_csv, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            conn.execute('INSERT OR IGNORE INTO teacher (name, availability) VALUES (?, ?)',
                         (row['teacher'], int(row.get('availability', '1'))))
            teacher_ids[row['teacher']] = get_id(conn, 'teacher', 'name', row['teacher'])
    conn.commit()
    return teacher_ids

def insert_teacher_expertise(conn, teachers_csv, courses_dir):
    # Map subject to course_subject.id
    subj_map = {}
    for fname in os.listdir(courses_dir):
        if fname.endswith('.csv'):
            code = fname.replace('.csv', '').upper()
            course_id = get_id(conn, 'course', 'code', code)
            with open(os.path.join(courses_dir, fname), newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cur = conn.execute('''SELECT id FROM course_subject WHERE course_id=? AND subject_code=? AND year=? AND semester=?''',
                        (course_id, row['subject'], int(row['year']), int(row['semester'])))
                    r = cur.fetchone()
                    if r:
                        subj_map[(row['subject'], course_id, int(row['year']), int(row['semester']))] = r[0]
    with open(teachers_csv, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            teacher_id = get_id(conn, 'teacher', 'name', row['teacher'])
            for subj in row['expertise'].split(','):
                subj = subj.strip()
                # Insert for all years/semesters for this subject
                for k, cs_id in subj_map.items():
                    if k[0] == subj:
                        conn.execute('INSERT OR IGNORE INTO teacher_expertise (teacher_id, course_subject_id) VALUES (?, ?)',
                                     (teacher_id, cs_id))
    conn.commit()

def insert_enrollments(conn, enroll_dir):
    for fname in os.listdir(enroll_dir):
        if fname.endswith('.csv'):
            code = fname.replace('.csv', '').upper()
            course_id = get_id(conn, 'course', 'code', code)
            with open(os.path.join(enroll_dir, fname), newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Fill missing columns
                    status = row.get('status', 'confirmed')
                    source = row.get('source', None)
                    timestamp = row.get('timestamp', datetime.now().isoformat())
                    conn.execute('''INSERT OR IGNORE INTO enrollment
                        (course_id, year, semester, total_students, status, source, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?)''',
                        (course_id, int(row['year']), int(row['semester']), int(row['total_students']), status, source, timestamp))
    conn.commit()

def main():
    base = os.path.dirname(__file__)
    db_path = os.path.join(base, 'data', 'local.db')
    data_dir = os.path.join(base, 'data')
    schema_path = os.path.join(base, 'sql', 'schema.sql')
    courses_dir = os.path.join(data_dir, 'courses')
    enroll_dir = os.path.join(data_dir, 'enrollment')
    rooms_csv = os.path.join(data_dir, 'rooms.csv')
    teachers_csv = os.path.join(data_dir, 'teachers.csv')

    # Remove existing db to start fresh
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = get_db_connection(db_path)

    # Create schema
    create_schema(conn, schema_path)

    # Canonical values
    insert_room_categories(conn, ['Regular', 'Science Lab', 'Computer Lab', 'Online'])
    insert_modalities(conn, ['f2f', 'online', 'hyflex_a', 'hyflex_b'])
    # Courses
    course_codes = insert_courses(conn, courses_dir)
    # Rooms
    insert_rooms(conn, rooms_csv)
    # Course subjects
    insert_course_subjects(conn, courses_dir)
    # Teachers
    insert_teachers(conn, teachers_csv)
    # Teacher expertise
    insert_teacher_expertise(conn, teachers_csv, courses_dir)
    # Enrollments
    insert_enrollments(conn, enroll_dir)
    conn.close()
    print('Database population complete.')

if __name__ == '__main__':
    main()
