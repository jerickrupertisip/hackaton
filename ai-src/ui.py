import tkinter as tk
from tkinter import ttk, messagebox
import csv
import os

COURSES_DIR = os.path.join(os.path.dirname(__file__), 'data', 'courses')
ENROLLMENT_DIR = os.path.join(os.path.dirname(__file__), 'data', 'enrollment')
TEACHERS_CSV = os.path.join(os.path.dirname(__file__), 'data', 'teachers.csv')
ROOMS_CSV = os.path.join(os.path.dirname(__file__), 'data', 'rooms.csv')

categories = ["Teachers", "Rooms", "Courses", "Enrollment"]

# --- Schema Helpers ---
def get_course_codes():
    return [f.replace('.csv', '').upper() for f in os.listdir(COURSES_DIR) if f.endswith('.csv')]

def get_teachers_schema():
    return ['Teacher', 'Expertise', 'Availability']

def get_rooms_schema():
    return ['Room ID', 'Category', 'Capacity', 'Floor']

def get_course_schema(course_code=None):
    if course_code:
        path = os.path.join(COURSES_DIR, f'{course_code.lower()}.csv')
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                try:
                    return [h.replace('_', ' ').title() for h in next(reader)]
                except StopIteration:
                    pass
    return ['Subject', 'Year', 'Semester', 'Units', 'Preferred Room', 'Modality']

def get_enrollment_schema():
    return ['Student Name', 'Year', 'Semester', 'Course', 'Section']

def get_schema(category, course_code=None):
    if category == 'Teachers':
        return get_teachers_schema()
    elif category == 'Rooms':
        return get_rooms_schema()
    elif category == 'Courses':
        return get_course_schema(course_code)
    elif category == 'Enrollment':
        return get_enrollment_schema()
    else:
        return []

def get_options(field, category, course_code=None):
    if category == 'Rooms' and field == 'category':
        return ['Lecture', 'Lab', 'Computer']
    if category == 'Courses' and field == 'modality':
        return ['Face-to-Face', 'Online']
    if category == 'Teachers' and field == 'expertise':
        return ['Math', 'Science', 'English', 'IT']
    return []

def get_field_options(field):
    if field == 'subject':
        # Collect all subjects from all course CSVs
        subjects = set()
        for course_code in get_course_codes():
            path = os.path.join(COURSES_DIR, f'{course_code.lower()}.csv')
            if os.path.exists(path):
                with open(path, newline='', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        subj = row.get('subject')
                        if subj:
                            subjects.add(subj.strip())
        return sorted(subjects)
    return []

# --- Data Storage ---
raw_data_storage = {"Teachers": [], "Rooms": [], "Courses": {}, "Enrollment": {}}
course_codes = get_course_codes()
default_course = course_codes[0] if course_codes else "BSIT"

root = tk.Tk()
root.title("Academic Scheduler v2.0")

main_notebook = ttk.Notebook(root)
main_notebook.pack(expand=1, fill="both")

# --- Dynamic Tab Generation ---
tab_tables = {}
tab_forms = {}
tab_fields = {}
tab_buttons = {}
management_tabs = {}

def select_subjects(fields):
    # Use subjects from course CSVs
    all_subjects = get_field_options("subject")
    current_expertise = fields[1]["entry"].get().strip()
    pre_selected = [s.strip() for s in current_expertise.split(",")] if current_expertise else []
    subject_window = tk.Toplevel(root)
    subject_window.title("Select Subjects")
    listbox = tk.Listbox(subject_window, selectmode=tk.MULTIPLE, height=15, width=50)
    for subject in all_subjects:
        listbox.insert(tk.END, subject)
        if subject in pre_selected:
            listbox.selection_set(listbox.size() - 1)
    listbox.pack(pady=10)
    def ok():
        selected = [listbox.get(i) for i in listbox.curselection()]
        if selected:
            expertise_str = ", ".join(selected)
            fields[1]["entry"].delete(0, tk.END)
            fields[1]["entry"].insert(0, expertise_str)
        subject_window.destroy()
    def cancel():
        subject_window.destroy()
    btn_frame = tk.Frame(subject_window)
    btn_frame.pack()
    tk.Button(btn_frame, text="OK", command=ok).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="Cancel", command=cancel).pack(side=tk.LEFT, padx=5)

for cat in categories:
    frame = ttk.Frame(main_notebook)
    main_notebook.add(frame, text=f"Manage {cat}")
    schema = get_schema(cat, default_course if cat == "Courses" else None)
    table = ttk.Treeview(frame, columns=schema, show="headings", height=10)
    for col in schema:
        table.heading(col, text=col)
        table.column(col, width=120)
    table.pack(fill=tk.BOTH, expand=True, pady=10)
    tab_tables[cat] = table
    # Load CSV data
    if cat == "Teachers":
        data = []
        if os.path.exists(TEACHERS_CSV):
            with open(TEACHERS_CSV, newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # skip header
                for row in reader:
                    if any(cell.strip() for cell in row):
                        data.append(row)
        for row in data:
            table.insert("", tk.END, values=row)
    elif cat == "Rooms":
        data = []
        if os.path.exists(ROOMS_CSV):
            with open(ROOMS_CSV, newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)
                for row in reader:
                    if any(cell.strip() for cell in row):
                        data.append(row)
        for row in data:
            table.insert("", tk.END, values=row)
    elif cat == "Courses":
        for course_code in course_codes:
            path = os.path.join(COURSES_DIR, f"{course_code.lower()}.csv")
            if os.path.exists(path):
                with open(path, newline='', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    next(reader)
                    for row in reader:
                        if any(cell.strip() for cell in row):
                            table.insert("", tk.END, values=row)
    elif cat == "Enrollment":
        for course_code in course_codes:
            path = os.path.join(ENROLLMENT_DIR, f"{course_code.lower()}.csv")
            if os.path.exists(path):
                with open(path, newline='', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    next(reader)
                    for row in reader:
                        if any(cell.strip() for cell in row):
                            table.insert("", tk.END, values=row)
    # Form
    form_frame = tk.LabelFrame(frame, text="Entry Form", padx=10, pady=10)
    form_frame.pack(fill=tk.BOTH, expand=True, pady=10)
    fields = []
    for i, field_name in enumerate(schema):
        f = tk.Frame(form_frame)
        lbl = tk.Label(f, text=field_name, font=("Arial", 10, "bold"))
        lbl.pack(side=tk.LEFT, padx=(0,10))
        opts = get_options(field_name.lower().replace(' ', '_'), cat, default_course if cat == "Courses" else None)
        if opts:
            entry = ttk.Combobox(f, values=opts, state="readonly", width=43)
        elif cat == "Teachers" and i == 2:
            entry = tk.Checkbutton(f, text="Available")
        elif cat == "Teachers" and i == 1:
            entry = tk.Entry(f, width=44, state="readonly")
        else:
            entry = tk.Entry(f, width=44)
        entry.pack(side=tk.LEFT)
        # Only show Select Subjects for Teachers/Expertise
        if cat == "Teachers" and i == 1:
            btn = tk.Button(f, text="Select Subjects", command=lambda flds=fields: select_subjects(flds))
            btn.pack(side=tk.LEFT, padx=5)
        fields.append({"frame": f, "label": lbl, "entry": entry})
        f.pack(pady=(8,2), anchor='w')
    tab_fields[cat] = fields
    # Buttons
    btn_frame = tk.Frame(frame)
    btn_frame.pack(pady=10)
    add_btn = tk.Button(btn_frame, text="Add Record", bg="#28a745", width=15)
    edit_btn = tk.Button(btn_frame, text="Edit Selected", bg="#ffc107", width=15)
    remove_btn = tk.Button(btn_frame, text="Remove Selected", bg="#dc3545", width=15)
    save_csv_btn = tk.Button(btn_frame, text="SAVE TO CSV", bg="#007bff", width=15)
    add_btn.pack(side=tk.LEFT, padx=5)
    edit_btn.pack(side=tk.LEFT, padx=5)
    remove_btn.pack(side=tk.LEFT, padx=5)
    save_csv_btn.pack(side=tk.LEFT, padx=5)
    tab_buttons[cat] = {
        "add": add_btn,
        "edit": edit_btn,
        "remove": remove_btn,
        "save": save_csv_btn
    }
    # Add Load All CSVs button after Save to CSV
    load_all_btn = tk.Button(btn_frame, text="Load All CSVs", bg="#28a745", width=20)
    load_all_btn.pack(side=tk.LEFT, padx=5)
    management_tabs[cat] = {
        "frame": frame,
        "table": table,
        "csv_path": TEACHERS_CSV if cat == "Teachers" else ROOMS_CSV if cat == "Rooms" else os.path.join(COURSES_DIR, f"{default_course.lower()}.csv") if cat == "Courses" else os.path.join(ENROLLMENT_DIR, f"{default_course.lower()}.csv"),
        "load_btn": load_all_btn
    }

# Add a button to load all CSVs manually after the "Save to CSV" button in each management tab
def load_all_csvs():
    for tab_name, tab_info in management_tabs.items():
        table = tab_info['table']
        csv_path = tab_info['csv_path']
        table.delete(*table.get_children())
        if os.path.exists(csv_path):
            with open(csv_path, newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None)  # skip header
                for row in reader:
                    if any(cell.strip() for cell in row):
                        table.insert("", tk.END, values=row)
    # Also reload Outputs tab
    if 'output_table' in globals():
        load_outputs()

management_tabs = {}
for cat in management_tabs:
    management_tabs[cat]['load_btn'].config(command=load_all_csvs)

# Outputs Tab
output_tab = ttk.Frame(main_notebook)
main_notebook.add(output_tab, text="Outputs")
output_label = tk.Label(output_tab, text="Output Visualization", font=("Arial", 16, "bold"))
output_label.pack(pady=10)
output_course_select = ttk.Combobox(output_tab, values=course_codes, state="readonly")
output_course_select.set(default_course)
output_course_select.pack(pady=5)
output_table = ttk.Treeview(output_tab, columns=["Section", "Subject", "Teacher"], show="headings", height=10)
for col in ["Section", "Subject", "Teacher"]:
    output_table.heading(col, text=col)
    output_table.column(col, width=120)
output_table.pack(fill=tk.BOTH, expand=True, pady=10)

# Remove Load Output CSVs button

def load_outputs():
    output_table.delete(*output_table.get_children())
    selected_course = output_course_select.get()
    output_dir = os.path.join(os.path.dirname(__file__), 'output', selected_course.upper())
    if not os.path.exists(output_dir):
        return
    files = [f for f in os.listdir(output_dir) if f.endswith('.csv')]
    for file in files:
        path = os.path.join(output_dir, file)
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # skip header
            for row in reader:
                if any(cell.strip() for cell in row):
                    output_table.insert("", tk.END, values=row)

output_course_select.bind("<<ComboboxSelected>>", lambda e: load_outputs())

# Automatically load all CSVs (including Outputs) on startup
load_all_csvs()

root.mainloop()