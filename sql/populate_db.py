import csv
import sqlite3

def populate_db(db_path, csv_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()


    conn.commit()
    conn.close()


def room_categories_from_csv() -> set[str]:
    with open("ai-src/data/rooms.csv", 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        categories = set()
        for row in reader:
            categories.add(row["category"].strip())
        print("Unique room categories:", categories)


def room_from_csv() -> list[dict]:
    categories = room_categories_from_csv()
    rooms = []
    with open("ai-src/data/rooms.csv", 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            category = row["category"].strip()
            assert category in categories, f"Category '{category}' not found in unique categories set"
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

def teacher_expertise_from_csv() -> list[dict]:
    teachers = teacher_from_csv()
    expertise_list = []
    with open("ai-src/data/teachers.csv", 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            teacher_name = row["teacher"].strip()
            expertise_str = row["expertise"].strip()

            expertise = expertise_str.split(",")
            expertise = [e.strip() for e in expertise]
            
            assert teacher_name in [t["name"] for t in teachers], f"Teacher '{teacher_name}' not found in teachers list"
    return expertise_list

print(teacher_from_csv())