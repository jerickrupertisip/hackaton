PRAGMA foreign_keys = ON;

-- ###########################################################################
-- INPUT CSV: ./data/courses/<course>.csv
-- Purpose: Defines the subjects offered per course, year, and semester.
-- CSV header: subject,year,semester,units,preferred_room,modality
-- Notes: subject must be unique per course/year/semester; preferred_room ∈ (Regular,Science Lab,Computer Lab,Online)
CREATE TABLE course (
  id INTEGER PRIMARY KEY AUTOINCREMENT, -- surrogate PK
  code TEXT NOT NULL UNIQUE             -- human course code (e.g., 'BSIT')
);

-- course_subject: canonical subjects offered per course/year/semester
-- (stored under the same CSV group; importer maps course.code -> course_id)
CREATE TABLE course_subject (
  id INTEGER PRIMARY KEY AUTOINCREMENT,               -- surrogate PK for the subject row
  course_id INTEGER NOT NULL REFERENCES course(id) ON DELETE CASCADE, -- FK to course
  subject_code TEXT NOT NULL,                         -- short subject identifier (matches CSV 'subject')
  year INTEGER NOT NULL CHECK(year BETWEEN 1 AND 4),  -- CSV 'year'
  semester INTEGER NOT NULL CHECK(semester IN (1,2)), -- CSV 'semester'
  units REAL NOT NULL CHECK(units IN (1.5,2,3)),      -- CSV 'units'
  preferred_room_category_id INTEGER NOT NULL REFERENCES room_category(id), -- maps CSV 'preferred_room'
  modality_id INTEGER NOT NULL REFERENCES modality(id), -- maps CSV 'modality'
  UNIQUE(course_id, subject_code, year, semester)
);

-- ###########################################################################
-- INPUT CSV: ./data/teachers.csv
-- Purpose: Defines teacher expertise and availability.
-- CSV header: teacher,expertise,availability
-- Notes:
--   - 'teacher' is the teacher’s name (Firstname Lastname)
--   - 'expertise' is a list of subjects the teacher can teach
--   - 'availability' is a boolean (0 = False, 1 = True)
CREATE TABLE teacher (
  id INTEGER PRIMARY KEY AUTOINCREMENT, -- surrogate PK for teacher
  name TEXT NOT NULL UNIQUE,            -- CSV 'teacher'
  availability INTEGER NOT NULL CHECK(availability IN (0,1)) -- CSV 'availability' (boolean flag)
);

-- teacher_expertise: one row per (teacher, course_subject)
-- importer should map teacher_name -> teacher.id and subject tuple -> course_subject.id
CREATE TABLE teacher_expertise (
  id INTEGER PRIMARY KEY AUTOINCREMENT, -- surrogate PK for expertise row
  teacher_id INTEGER NOT NULL REFERENCES teacher(id) ON DELETE CASCADE, -- FK to teacher
  course_subject_id INTEGER NOT NULL REFERENCES course_subject(id) ON DELETE CASCADE, -- FK to subject
  UNIQUE(teacher_id, course_subject_id)
);

-- ###########################################################################
-- INPUT CSV: ./data/rooms.csv
-- Purpose: Canonical inventory of physical and Online rooms used by the scheduler.
-- CSV header: room_id,category,capacity,floor
-- Notes: category must map to room_category; capacity integer; floor 0 for Online
CREATE TABLE room_category (
  id INTEGER PRIMARY KEY AUTOINCREMENT, -- surrogate PK
  name TEXT NOT NULL UNIQUE             -- CSV 'category' values (Regular, Science Lab, Computer Lab, Online)
);

CREATE TABLE room (
  id INTEGER PRIMARY KEY AUTOINCREMENT, -- surrogate PK for room
  room_code TEXT NOT NULL UNIQUE,       -- CSV 'room_id' (e.g., 'Lab 1','2A','Online')
  category_id INTEGER NOT NULL REFERENCES room_category(id), -- FK to room_category
  capacity INTEGER NOT NULL CHECK(capacity >= 0), -- CSV 'capacity'
  floor INTEGER NOT NULL                 -- CSV 'floor' (0 for Online)
);

-- ###########################################################################
-- INPUT CSV: ./data/modalities.csv
-- Purpose: Canonical list of delivery modes used by course_subject and schedule.
-- CSV header: name
CREATE TABLE modality (
  id INTEGER PRIMARY KEY AUTOINCREMENT, -- surrogate PK
  name TEXT NOT NULL UNIQUE             -- CSV 'modality' (f2f, online, hyflex_a, hyflex_b)
);

-- ###########################################################################
-- INPUT CSV: ./data/enrollment/<course>.csv
-- Purpose: Store total student counts per course, year, and semester for section generation.
-- CSV header: year,semester,total_students,status,source,timestamp
-- Note: number of course files in ./data/courses/ should match ./data/enrollment/
CREATE TABLE enrollment (
  id INTEGER PRIMARY KEY AUTOINCREMENT, -- surrogate PK for enrollment row
  course_id INTEGER NOT NULL REFERENCES course(id) ON DELETE RESTRICT, -- FK to course (map course_code -> id)
  year INTEGER NOT NULL CHECK(year BETWEEN 1 AND 4),   -- CSV 'year'
  semester INTEGER NOT NULL CHECK(semester IN (1,2)), -- CSV 'semester'
  total_students INTEGER NOT NULL CHECK(total_students >= 0), -- CSV 'total_students'
  status TEXT NOT NULL CHECK(status IN ('confirmed','provisional')) DEFAULT 'confirmed', -- CSV 'status'
  source TEXT,                                         -- CSV 'source' (optional)
  timestamp TEXT NOT NULL,                             -- CSV 'timestamp' (ISO 8601)
  UNIQUE(course_id, year, semester)
);

-- ###########################################################################
-- OUTPUT CSV: ./output/sections.csv  (or ./output/<course>-<year-level><section>.csv)
-- Purpose: Generated sections registry (scheduler output).
-- CSV header: section_code,course_code,year,semester,suffix,student_count,created_at
CREATE TABLE section (
  id INTEGER PRIMARY KEY AUTOINCREMENT, -- surrogate PK for section
  section_code TEXT NOT NULL UNIQUE,    -- CSV 'section_code' (e.g., 'BSIT-105')
  course_id INTEGER NOT NULL REFERENCES course(id) ON DELETE RESTRICT, -- FK to course
  year INTEGER NOT NULL CHECK(year BETWEEN 1 AND 4),   -- CSV 'year'
  semester INTEGER NOT NULL CHECK(semester IN (1,2)), -- CSV 'semester'
  suffix INTEGER NOT NULL,               -- numeric suffix used to generate section_code (application-generated)
  student_count INTEGER NOT NULL DEFAULT 0, -- CSV 'student_count'
  created_at TEXT NOT NULL,               -- CSV 'created_at' (ISO 8601)
  UNIQUE(course_id, year, semester, suffix)
);

-- ###########################################################################
-- OUTPUT CSV: ./output/<course>-<year-level><section>.csv  (per-section schedule)
-- Alternative combined output: ./output/schedule.csv
-- CSV header: section_code,course_code,subject_code,unit,day,start_time,end_time,room_code,modality,teacher_name,hyflex_pattern,week_parity,created_at
-- Purpose: Generated timetable rows for each section (scheduler output).
CREATE TABLE schedule (
  id INTEGER PRIMARY KEY AUTOINCREMENT, -- surrogate PK for schedule row
  section_id INTEGER NOT NULL REFERENCES section(id) ON DELETE CASCADE, -- FK to section
  course_subject_id INTEGER NOT NULL REFERENCES course_subject(id) ON DELETE RESTRICT, -- FK to subject (maps to CSV 'subject')
  day TEXT NOT NULL CHECK(day IN ('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday')), -- CSV 'day'
  start_seconds INTEGER NOT NULL CHECK(start_seconds BETWEEN 0 AND 86399), -- CSV 'start_time' converted to seconds
  end_seconds INTEGER NOT NULL CHECK(end_seconds BETWEEN 0 AND 86399),   -- CSV 'end_time' converted to seconds
  room_id INTEGER NOT NULL REFERENCES room(id) ON DELETE SET NULL, -- FK to room (maps to CSV 'room')
  modality_id INTEGER NOT NULL REFERENCES modality(id), -- FK to modality (maps to CSV 'modality')
  teacher_id INTEGER REFERENCES teacher(id) ON DELETE SET NULL, -- FK to teacher (maps to CSV 'teacher')
  hyflex_pattern TEXT CHECK(hyflex_pattern IN ('A','B')) DEFAULT NULL, -- CSV 'hyflex_pattern' (optional)
  week_parity INTEGER CHECK(week_parity IN (0,1)) DEFAULT NULL, -- CSV 'week_parity' (optional)
  created_at TEXT NOT NULL,               -- CSV 'created_at' (ISO 8601)
  UNIQUE(section_id, course_subject_id, day, start_seconds),
  CHECK(start_seconds < end_seconds)
);

-- ###########################################################################
-- Indexes for performance (helpful for conflict checks and lookups)
CREATE INDEX idx_course_subject_course ON course_subject(course_id);
CREATE INDEX idx_enrollment_course_year_sem ON enrollment(course_id, year, semester);
CREATE INDEX idx_section_course_year_sem ON section(course_id, year, semester);
CREATE INDEX idx_schedule_room_day_time ON schedule(room_id, day, start_seconds, end_seconds);
CREATE INDEX idx_schedule_teacher_day_time ON schedule(teacher_id, day, start_seconds, end_seconds);
CREATE INDEX idx_schedule_section_day_time ON schedule(section_id, day, start_seconds, end_seconds);
-- ###########################################################################
