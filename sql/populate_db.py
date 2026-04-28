import csv
import sqlite3

def populate_db(db_path, csv_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()


    conn.commit()
    conn.close()


def room_categories_from_csv() -> set[str]:
    categories = set()
    with open("ai-src/data/rooms.csv", 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            categories.add(row["category"].strip())
    return categories


def room_from_csv() -> list[dict]:
    categories = room_categories_from_csv()
    rooms = []
    with open("ai-src/data/rooms.csv", 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            category = row["category"].strip()
            if category not in categories:
                raise ValueError(f"Category '{category}' not found in categories list")
            room = {
                "name": row["room_id"].strip(),
                "capacity": int(row["capacity"].strip()),
                "category": category,
                "floor": int(row["floor"].strip())
            }
            rooms.append(room)
    return rooms


def teacher_from_csv() -> list[dict]:
    teachers = []
    with open("ai-src/data/teachers.csv", 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            teacher = {
                "name": row["teacher"].strip(),
                "availability": row["availability"].strip() == "1",
            }
            teachers.append(teacher)
    return teachers


def subjects_from_csv() -> list[dict]:
    room_categories = room_categories_from_csv()
    subjects = []
    with open("ai-src/data/courses/bsit.csv", 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            preferred_room_category = row["preferred_room"].strip().removesuffix(" Room")
            if preferred_room_category not in room_categories:
                raise ValueError(f"Preferred room category '{row['preferred_room'].strip()}' not found in room categories list")
            subject = {
                "name": row["subject"].strip(),
                "year": int(row["year"].strip()),
                "semester": int(row["semester"].strip()),
                "units": float(row["units"].strip()),
                "preferred_room": preferred_room_category,
                "modality": row["modality"].strip()
            }
            subjects.append(subject)
    return subjects


def teacher_expertise_from_csv() -> list[dict]:
    teachers = teacher_from_csv()
    subjects = subjects_from_csv()
    expertise_list = []
    with open("ai-src/data/teachers.csv", 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            teacher_name = row["teacher"].strip()
            expertise_str = row["expertise"].strip()

            expertise = expertise_str.split(",")
            expertise = [e.strip() for e in expertise]
            
            if teacher_name not in [t["name"] for t in teachers]:
                raise ValueError(f"Teacher '{teacher_name}' not found in teachers list")

            for subject_name in expertise:
                if subject_name not in [s["name"] for s in subjects]:
                    raise ValueError(f"Subject '{subject_name}' not found in subjects list")
            print([s["name"] for s in subjects])
            expertise_list.append({
                "teacher": teacher_name,
                "subject": subject_name
            })

    return expertise_list

print(teacher_expertise_from_csv())