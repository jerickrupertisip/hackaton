# Academic Scheduling System CSP Solver
import csv
import os
import math
from collections import defaultdict
from typing import List, Dict, Any, Optional

# --- Data Classes ---
class Room:
	def __init__(self, room_id, category, capacity, floor):
		self.room_id = room_id
		self.category = category
		self.capacity = int(capacity)
		self.floor = int(floor)

class Teacher:
	def __init__(self, name, expertise, availability=None):
		self.name = name
		self.expertise = [e.strip() for e in expertise.split(',')]
		self.availability = availability or []  # List of (Day, StartTime, EndTime)

class Subject:
	def __init__(self, subject, year, semester, units, preferred_room, modality):
		self.subject = subject
		self.year = int(year)
		self.semester = int(semester)
		self.units = float(units)
		self.preferred_room = preferred_room
		self.modality = modality

class Section:
	def __init__(self, course, year, semester, section_num, total_students):
		self.course = course
		self.year = int(year)
		self.semester = int(semester)
		self.section_num = section_num
		self.total_students = int(total_students)
		self.subjects: List[Subject] = []

# --- CSV Parsing and Validation ---
def parse_rooms_csv(path: str) -> Dict[str, Room]:
	rooms = {}
	with open(path, newline='', encoding='utf-8') as f:
		reader = csv.DictReader(f)
		for row in reader:
			room = Room(row['room_id'], row['category'], row['capacity'], row['floor'])
			rooms[room.room_id] = room
	return rooms

def parse_teachers_csv(path: str) -> Dict[str, Teacher]:
	teachers = {}
	with open(path, newline='', encoding='utf-8') as f:
		reader = csv.DictReader(f)
		for row in reader:
			teacher = Teacher(row['teacher'], row['expertise'], row.get('availability', ''))
			teachers[teacher.name] = teacher
	return teachers

def parse_course_csv(path: str) -> List[Subject]:
	subjects = []
	with open(path, newline='', encoding='utf-8') as f:
		reader = csv.DictReader(f)
		for row in reader:
			subjects.append(Subject(
				row['subject'], row['year'], row['semester'], row['units'], row['preferred_room'], row['modality']
			))
	return subjects

def parse_enrollment_csv(path: str) -> List[Dict[str, Any]]:
	enrollments = []
	with open(path, newline='', encoding='utf-8') as f:
		reader = csv.DictReader(f)
		for row in reader:
			enrollments.append({
				'year': int(row['year']),
				'semester': int(row['semester']),
				'total_students': int(row['total_students'])
			})
	return enrollments

# --- Validation ---
def validate_csvs(rooms, teachers, courses, enrollments):
	# Room capacity check
	for room in rooms.values():
		if room.category != 'Online' and room.capacity > 30:
			raise ValueError(f"Room {room.room_id} exceeds max capacity of 30.")
	# Teacher expertise check
	for t in teachers.values():
		if not t.expertise:
			raise ValueError(f"Teacher {t.name} has no expertise listed.")
	# Course/Subject check
	for course, subjects in courses.items():
		for subj in subjects:
			if subj.units not in [1.5, 2, 3]:
				raise ValueError(f"Subject {subj.subject} in {course} has invalid units: {subj.units}")
	# Enrollment check
	for course, enr in enrollments.items():
		for e in enr:
			if e['total_students'] < 1:
				raise ValueError(f"Enrollment for {course} year {e['year']} sem {e['semester']} is invalid.")

# --- Main Scheduling Entrypoint ---
def main():
	data_dir = os.path.join(os.path.dirname(__file__), 'data')
	rooms = parse_rooms_csv(os.path.join(data_dir, 'rooms.csv'))
	teachers = parse_teachers_csv(os.path.join(data_dir, 'teachers.csv'))


	# Parse all courses and enrollments
	courses_dir = os.path.join(data_dir, 'courses')
	enroll_dir = os.path.join(data_dir, 'enrollment')
	course_files = [f for f in os.listdir(courses_dir) if f.endswith('.csv')]
	courses = {}
	enrollments = {}
	for cf in course_files:
		cname = cf.replace('.csv', '')
		courses[cname] = parse_course_csv(os.path.join(courses_dir, cf))
		enrollments[cname] = parse_enrollment_csv(os.path.join(enroll_dir, cf))

	# Validate all loaded data
	validate_csvs(rooms, teachers, courses, enrollments)

	# --- Section Generation ---
	R_roomMaxCapacity = 30
	sections = defaultdict(list)  # course -> List[Section]
	for course, enr_list in enrollments.items():
		for enr in enr_list:
			# Only generate sections if there are subjects for this year/semester
			subjects_for_section = [s for s in courses[course] if s.year == enr['year'] and s.semester == enr['semester']]
			if not subjects_for_section:
				continue  # Skip section if no subjects defined
			n_sections = math.ceil(enr['total_students'] / R_roomMaxCapacity)
			for i in range(1, n_sections + 1):
				section_id = f"{course.upper()}-{enr['year']}{str(i).zfill(2)}"
				section = Section(course, enr['year'], enr['semester'], i, enr['total_students'])
				section.subjects = subjects_for_section
				sections[course].append(section)

	# --- Scheduling Algorithm ---
	# Configuration
	DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
	START_HOUR = 7.5  # 7:30am
	END_HOUR = 21.0   # 9:00pm
	SLOT_LENGTH = 1.5 # hours per subject (90 min)
	TEACHER_LUNCH_BREAK = 1.0 # hours
	EMPTY_DAYS = 1    # days with no class per section

	# Helper: Find available teacher for subject
	def find_teacher(subject, teachers, used_teachers, day, start_time):
		for t in teachers.values():
			if subject.subject in t.expertise and (t.name, day, start_time) not in used_teachers:
				return t.name
		return None

	# Helper: Find available room for subject
	def find_room(subject, rooms, used_rooms, day, start_time):
		for r in rooms.values():
			if r.category == subject.preferred_room or (subject.modality.startswith('online') and r.category == 'Online'):
				if (r.room_id, day, start_time) not in used_rooms:
					return r.room_id
		return None

	# Helper: Get next available time slot for a section
	def get_next_slot(section_schedule):
		for day in DAYS:
			slots = [s['start_time'] for s in section_schedule if s['day'] == day]
			t = START_HOUR
			while t + SLOT_LENGTH <= END_HOUR:
				if t not in slots:
					return day, t
				t += SLOT_LENGTH
		return None, None

	# Main scheduling loop
	output_dir = os.path.join(os.path.dirname(__file__), 'output')
	os.makedirs(output_dir, exist_ok=True)
	for course, sec_list in sections.items():
		for sec in sec_list:
			section_schedule = []
			used_teachers = set()
			used_rooms = set()
			for subj in sec.subjects:
				# Assign day and time
				day, start_time = get_next_slot(section_schedule)
				if day is None:
					raise Exception(f"No available slot for section {course}-{sec.year}{str(sec.section_num).zfill(2)}")
				# Assign teacher
				teacher = find_teacher(subj, teachers, used_teachers, day, start_time)
				if not teacher:
					teacher = "TBA"
				used_teachers.add((teacher, day, start_time))
				# Assign room
				room = find_room(subj, rooms, used_rooms, day, start_time)
				if not room:
					room = "Online" if subj.modality.startswith('online') else "TBA"
				used_rooms.add((room, day, start_time))
				# Format time
				st_hr = int(start_time)
				st_min = int((start_time - st_hr) * 60)
				etime = start_time + SLOT_LENGTH
				et_hr = int(etime)
				et_min = int((etime - et_hr) * 60)
				start_str = f"{st_hr:02d}:{st_min:02d}"
				end_str = f"{et_hr:02d}:{et_min:02d}"
				# Save schedule
				section_schedule.append({
					'subject': subj.subject,
					'unit': subj.units,
					'day': day,
					'start_time': start_str,
					'end_time': end_str,
					'room': room,
					'modality': subj.modality,
					'teacher': teacher
				})
			# Write to CSV
			out_file = os.path.join(output_dir, f"{course.upper()}-{sec.year}{str(sec.section_num).zfill(2)}.csv")
			with open(out_file, 'w', newline='', encoding='utf-8') as f:
				writer = csv.DictWriter(f, fieldnames=['subject','unit','day','start_time','end_time','room','modality','teacher'])
				writer.writeheader()
				for row in section_schedule:
					writer.writerow(row)
	print("Schedules generated and written to output directory.")

if __name__ == '__main__':
	main()
