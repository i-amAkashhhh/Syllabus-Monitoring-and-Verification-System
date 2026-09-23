
import sqlite3
from datetime import date

from kivy.app import App
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.uix.anchorlayout import AnchorLayout


DB_NAME = "syllabus.db"

CONFIRMATION_THRESHOLD = 70.0
QUIZ_THRESHOLD = 60.0

Window.clearcolor = (0.95, 0.96, 0.98, 1)
Window.minimum_width = 1000
Window.minimum_height = 700


# ============================================================
# COLORS
# ============================================================

PRIMARY = (0.12, 0.31, 0.68, 1)
PRIMARY_DARK = (0.08, 0.18, 0.40, 1)
SUCCESS = (0.10, 0.58, 0.32, 1)
WARNING = (0.93, 0.57, 0.10, 1)
DANGER = (0.80, 0.22, 0.25, 1)
TEXT = (0.08, 0.10, 0.15, 1)
MUTED = (0.40, 0.44, 0.52, 1)
WHITE = (1, 1, 1, 1)
LIGHT = (0.96, 0.97, 0.99, 1)


# ============================================================
# DATABASE
# ============================================================

def get_connection():
    return sqlite3.connect(DB_NAME)


def ensure_column(cur, table, column, definition):
    cur.execute(f"PRAGMA table_info({table})")
    cols = {r[1] for r in cur.fetchall()}
    if column not in cols:
        cur.execute(
            f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
        )


def create_database():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT NOT NULL,
            teacher TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            unit_no INTEGER NOT NULL,
            topic_name TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            completed_date TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student TEXT NOT NULL,
            topic_id INTEGER NOT NULL,
            confirmed INTEGER DEFAULT 0,
            confirmed_date TEXT
        )
    """)

    ensure_column(cur, "feedback", "confirmed_date", "TEXT")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS quiz_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct_option TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student TEXT NOT NULL,
            topic_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            percentage REAL NOT NULL,
            attempted_date TEXT NOT NULL,
            UNIQUE(student, topic_id)
        )
    """)

    conn.commit()
    conn.close()


def seed_demo_data():
    conn = get_connection()
    cur = conn.cursor()

    users = [
        ("Admin", "admin", "1234", "admin"),
        ("Rahul Sharma", "teacher", "1234", "teacher"),
        ("Student One", "student", "1234", "student"),
        ("Student Two", "student2", "1234", "student"),
        ("Student Three", "student3", "1234", "student"),
        ("Student Four", "student4", "1234", "student"),
        ("Student Five", "student5", "1234", "student"),
    ]

    for user in users:
        cur.execute("""
            INSERT OR IGNORE INTO users(name, username, password, role)
            VALUES (?, ?, ?, ?)
        """, user)

    cur.execute("SELECT COUNT(*) FROM subjects")
    if cur.fetchone()[0] == 0:
        cur.execute("""
            INSERT INTO subjects(name, code, teacher)
            VALUES (?, ?, ?)
        """, ("Database Management System", "CS401", "Rahul Sharma"))
        dbms_id = cur.lastrowid

        dbms_topics = [
            (1, "Introduction to DBMS"),
            (1, "DBMS Architecture"),
            (2, "ER Model"),
            (2, "Relational Model"),
            (3, "Normalization"),
            (3, "Transactions"),
        ]

        for unit, topic in dbms_topics:
            cur.execute("""
                INSERT INTO topics(subject_id, unit_no, topic_name)
                VALUES (?, ?, ?)
            """, (dbms_id, unit, topic))

        cur.execute("""
            INSERT INTO subjects(name, code, teacher)
            VALUES (?, ?, ?)
        """, ("Operating Systems", "CS402", "Rahul Sharma"))
        os_id = cur.lastrowid

        os_topics = [
            (1, "Introduction to Operating Systems"),
            (1, "Process Management"),
            (2, "CPU Scheduling"),
            (2, "Deadlocks"),
            (3, "Memory Management"),
            (3, "File Systems"),
        ]

        for unit, topic in os_topics:
            cur.execute("""
                INSERT INTO topics(subject_id, unit_no, topic_name)
                VALUES (?, ?, ?)
            """, (os_id, unit, topic))

    conn.commit()
    conn.close()


def seed_quiz_questions():
    bank = {
        "Introduction to DBMS": [
            ("What is the main purpose of a DBMS?",
             "Manage and organize data", "Design hardware",
             "Compile programs", "Create networks", "A"),
            ("Which is an example of a DBMS?",
             "MySQL", "HTML", "Python", "Linux Kernel", "A"),
        ],
        "DBMS Architecture": [
            ("Which level describes physical data storage?",
             "External", "Conceptual", "Internal", "View", "C"),
            ("Three-schema architecture mainly supports:",
             "Data independence", "CPU scheduling",
             "Packet routing", "Image compression", "A"),
        ],
        "ER Model": [
            ("A real-world object is represented as:",
             "Entity", "Process", "Thread", "Packet", "A"),
            ("A property of an entity is called:",
             "Attribute", "Relation", "Transaction", "Lock", "A"),
        ],
        "Relational Model": [
            ("A row in a relation is called:",
             "Tuple", "Attribute", "Domain", "Schema", "A"),
            ("A column in a relation is called:",
             "Attribute", "Tuple", "Process", "Page", "A"),
        ],
        "Normalization": [
            ("Normalization mainly reduces:",
             "Data redundancy", "CPU usage",
             "Network bandwidth", "Display size", "A"),
            ("Which normal form removes partial dependency?",
             "2NF", "1NF", "4NF", "5NF", "A"),
        ],
        "Transactions": [
            ("All-or-nothing execution refers to:",
             "Atomicity", "Consistency", "Isolation", "Durability", "A"),
            ("Committed data surviving failure refers to:",
             "Durability", "Atomicity", "Isolation", "Availability", "A"),
        ],
        "Introduction to Operating Systems": [
            ("An operating system acts as an interface between:",
             "Applications and hardware", "Two databases",
             "Two routers", "HTML and CSS", "A"),
            ("Which is an operating system?",
             "Linux", "SQL", "JPEG", "JSON", "A"),
        ],
        "Process Management": [
            ("A program in execution is called:",
             "Process", "File", "Relation", "Frame", "A"),
            ("PCB stands for:",
             "Process Control Block", "Program Cache Buffer",
             "Primary Code Bus", "Process Command Base", "A"),
        ],
        "CPU Scheduling": [
            ("Which algorithm uses a time quantum?",
             "Round Robin", "FCFS", "SJF", "FIFO paging", "A"),
            ("The CPU scheduler mainly selects from:",
             "Ready queue", "Disk block",
             "File directory", "Page table", "A"),
        ],
        "Deadlocks": [
            ("Which is a necessary condition for deadlock?",
             "Mutual exclusion", "Infinite memory",
             "No processes", "No resources", "A"),
            ("Deadlock prevention works by:",
             "Breaking a necessary condition", "Increasing RAM",
             "Deleting files", "Disabling cache", "A"),
        ],
        "Memory Management": [
            ("Paging divides physical memory into:",
             "Frames", "Tuples", "Sockets", "Relations", "A"),
            ("Virtual memory can allow:",
             "Programs larger than physical memory",
             "Only one process", "No disk use",
             "No address translation", "A"),
        ],
        "File Systems": [
            ("A file system organizes:",
             "Files and directories", "CPU instructions only",
             "Database locks only", "Network cables", "A"),
            ("Which stores file metadata in many Unix systems?",
             "Inode", "Semaphore", "Socket", "Register", "A"),
        ],
    }

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, topic_name FROM topics")
    for topic_id, topic_name in cur.fetchall():
        cur.execute(
            "SELECT COUNT(*) FROM quiz_questions WHERE topic_id=?",
            (topic_id,)
        )

        if cur.fetchone()[0] > 0:
            continue

        for q in bank.get(topic_name, []):
            cur.execute("""
                INSERT INTO quiz_questions(
                    topic_id, question,
                    option_a, option_b, option_c, option_d,
                    correct_option
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (topic_id, *q))

    conn.commit()
    conn.close()


def initialize_database():
    create_database()
    seed_demo_data()
    seed_quiz_questions()


def get_verification(topic_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT completed FROM topics WHERE id=?",
        (topic_id,)
    )
    row = cur.fetchone()
    completed = row[0] if row else 0

    cur.execute("""
        SELECT COUNT(DISTINCT student)
        FROM feedback
        WHERE topic_id=? AND confirmed=1
    """, (topic_id,))
    confirmations = cur.fetchone()[0] or 0

    cur.execute(
        "SELECT COUNT(*) FROM users WHERE role='student'"
    )
    students = cur.fetchone()[0] or 0

    confirmation_rate = (
        confirmations / students * 100
        if students else 0
    )

    cur.execute("""
        SELECT COUNT(*), AVG(percentage)
        FROM quiz_results
        WHERE topic_id=?
    """, (topic_id,))
    attempts, avg = cur.fetchone()

    attempts = attempts or 0
    avg = float(avg or 0)

    conn.close()

    if not completed:
        final_status = "Pending"
    elif (
        confirmation_rate >= CONFIRMATION_THRESHOLD
        and avg >= QUIZ_THRESHOLD
    ):
        final_status = "Verified"
    elif confirmation_rate >= 40 or avg >= 40:
        final_status = "Review"
    else:
        final_status = "Not Verified"

    return {
        "completed": completed,
        "confirmations": confirmations,
        "students": students,
        "confirmation_rate": confirmation_rate,
        "attempts": attempts,
        "quiz_average": avg,
        "status": final_status,
    }


# ============================================================
# BASIC UI HELPERS
# ============================================================

def make_label(
    text,
    font_size=16,
    color=TEXT,
    bold=False,
    height=40,
    halign="left"
):
    lbl = Label(
        text=text,
        font_size=font_size,
        color=color,
        bold=bold,
        size_hint_y=None,
        height=dp(height),
        halign=halign,
        valign="middle"
    )
    lbl.bind(
        size=lambda obj, size: setattr(
            obj, "text_size", (size[0], None)
        )
    )
    return lbl


def make_button(
    text,
    color=PRIMARY,
    width=None,
    height=48
):
    btn = Button(
        text=text,
        size_hint_y=None,
        height=dp(height),
        background_normal="",
        background_down="",
        background_color=color,
        color=WHITE,
        font_size=15,
        bold=True,
    )

    if width is not None:
        btn.size_hint_x = None
        btn.width = dp(width)

    return btn


def show_message(title, message):
    layout = BoxLayout(
        orientation="vertical",
        padding=dp(20),
        spacing=dp(15)
    )

    msg = Label(
        text=message,
        color=TEXT,
        font_size=15,
        halign="center",
        valign="middle"
    )
    msg.bind(
        size=lambda obj, size: setattr(
            obj, "text_size", (size[0], None)
        )
    )

    close_btn = make_button(
        "OK",
        color=PRIMARY,
        height=45
    )

    layout.add_widget(msg)
    layout.add_widget(close_btn)

    popup = Popup(
        title=title,
        content=layout,
        size_hint=(0.55, 0.38),
        auto_dismiss=False
    )

    close_btn.bind(on_release=popup.dismiss)
    popup.open()


# ============================================================
# LOGIN
# ============================================================

class LoginScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        root = AnchorLayout(
            anchor_x="center",
            anchor_y="center",
            padding=dp(40)
        )

        card = BoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            width=dp(520),
            height=dp(520),
            padding=dp(35),
            spacing=dp(14)
        )

        card.add_widget(
            make_label(
                "Syllabus Monitoring System",
                font_size=30,
                bold=True,
                height=65,
                halign="center"
            )
        )

        card.add_widget(
            make_label(
                "Login to continue",
                font_size=16,
                color=MUTED,
                height=35,
                halign="center"
            )
        )

        card.add_widget(
            Widget(size_hint_y=None, height=dp(10))
        )

        card.add_widget(
            make_label(
                "Username",
                font_size=14,
                bold=True,
                height=28
            )
        )

        self.username = TextInput(
            hint_text="Enter username",
            multiline=False,
            size_hint_y=None,
            height=dp(52),
            font_size=17,
            padding=[dp(12), dp(13)],
            background_normal="",
            background_active="",
            background_color=(0.92, 0.94, 0.97, 1),
            foreground_color=TEXT,
            hint_text_color=MUTED
        )

        card.add_widget(self.username)

        card.add_widget(
            make_label(
                "Password",
                font_size=14,
                bold=True,
                height=28
            )
        )

        self.password = TextInput(
            hint_text="Enter password",
            password=True,
            multiline=False,
            size_hint_y=None,
            height=dp(52),
            font_size=17,
            padding=[dp(12), dp(13)],
            background_normal="",
            background_active="",
            background_color=(0.92, 0.94, 0.97, 1),
            foreground_color=TEXT,
            hint_text_color=MUTED
        )

        card.add_widget(self.password)

        self.error_label = make_label(
            "",
            font_size=13,
            color=DANGER,
            height=28,
            halign="center"
        )
        card.add_widget(self.error_label)

        login_btn = make_button(
            "LOGIN",
            color=PRIMARY,
            height=52
        )
        login_btn.bind(on_release=self.login)

        card.add_widget(login_btn)

        # Press Enter in password box to login
        self.password.bind(
            on_text_validate=self.login
        )

        card.add_widget(
            make_label(
                "Demo: admin / teacher / student    Password: 1234",
                font_size=13,
                color=MUTED,
                height=36,
                halign="center"
            )
        )

        root.add_widget(card)
        self.add_widget(root)

    def login(self, *args):
        username = self.username.text.strip()
        password = self.password.text.strip()

        self.error_label.text = ""

        if not username or not password:
            self.error_label.text = (
                "Please enter username and password."
            )
            return

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT name, role
            FROM users
            WHERE username=? AND password=?
        """, (username, password))

        user = cur.fetchone()
        conn.close()

        if not user:
            self.error_label.text = (
                "Invalid username or password."
            )
            return

        app = App.get_running_app()
        app.current_user = user[0]
        app.current_role = user[1]
        app.current_username = username

        dashboard = app.root.get_screen("dashboard")
        dashboard.load_dashboard()

        app.root.current = "dashboard"


# ============================================================
# DASHBOARD
# ============================================================

class DashboardScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        root = BoxLayout(
            orientation="vertical"
        )

        # Header
        header = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(82),
            padding=[dp(25), dp(15)],
            spacing=dp(12)
        )

        self.title = Label(
            text="Dashboard",
            color=WHITE,
            font_size=24,
            bold=True,
            halign="left",
            valign="middle"
        )
        self.title.bind(
            size=lambda obj, size: setattr(
                obj, "text_size", (size[0], None)
            )
        )

        header.add_widget(self.title)

        logout = make_button(
            "Logout",
            color=DANGER,
            width=110,
            height=46
        )
        logout.bind(on_release=self.logout)

        header.add_widget(logout)
        header.background_color = PRIMARY_DARK

        with header.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(*PRIMARY_DARK)
            self.header_rect = Rectangle(
                pos=header.pos,
                size=header.size
            )

        header.bind(
            pos=lambda *_: setattr(
                self.header_rect, "pos", header.pos
            ),
            size=lambda *_: setattr(
                self.header_rect, "size", header.size
            )
        )

        root.add_widget(header)

        content = BoxLayout(
            orientation="vertical",
            padding=dp(22),
            spacing=dp(16)
        )

        self.stats = GridLayout(
            cols=4,
            spacing=dp(12),
            size_hint_y=None,
            height=dp(110)
        )

        content.add_widget(self.stats)

        content.add_widget(
            make_label(
                "Subjects",
                font_size=21,
                bold=True,
                height=40
            )
        )

        self.scroll = ScrollView(
            bar_width=dp(6)
        )

        self.subjects_box = BoxLayout(
            orientation="vertical",
            spacing=dp(14),
            size_hint_y=None
        )

        self.subjects_box.bind(
            minimum_height=self.subjects_box.setter("height")
        )

        self.scroll.add_widget(self.subjects_box)
        content.add_widget(self.scroll)

        root.add_widget(content)
        self.add_widget(root)

    def make_stat_box(self, title, value, subtitle):
        box = BoxLayout(
            orientation="vertical",
            padding=dp(12),
            spacing=dp(3)
        )

        box.add_widget(
            make_label(
                title,
                font_size=13,
                color=MUTED,
                bold=True,
                height=25,
                halign="center"
            )
        )

        box.add_widget(
            make_label(
                str(value),
                font_size=27,
                bold=True,
                height=42,
                halign="center"
            )
        )

        box.add_widget(
            make_label(
                subtitle,
                font_size=11,
                color=MUTED,
                height=22,
                halign="center"
            )
        )

        return box

    def load_dashboard(self):
        app = App.get_running_app()

        self.subjects_box.clear_widgets()
        self.stats.clear_widgets()

        self.title.text = (
            f"{app.current_role.title()} Dashboard   |   "
            f"{app.current_user}"
        )

        conn = get_connection()
        cur = conn.cursor()

        if app.current_role == "teacher":
            cur.execute("""
                SELECT id, name, code, teacher
                FROM subjects
                WHERE teacher=?
                ORDER BY code
            """, (app.current_user,))
        else:
            cur.execute("""
                SELECT id, name, code, teacher
                FROM subjects
                ORDER BY code
            """)

        subjects = cur.fetchall()

        total_topics = 0
        total_completed = 0
        total_verified = 0
        total_review = 0

        summary = []

        for sid, name, code, teacher in subjects:
            cur.execute("""
                SELECT id, completed
                FROM topics
                WHERE subject_id=?
            """, (sid,))

            topic_rows = cur.fetchall()

            total = len(topic_rows)
            completed = sum(x[1] for x in topic_rows)
            verified = 0
            review = 0

            for topic_id, _ in topic_rows:
                status = get_verification(topic_id)["status"]

                if status == "Verified":
                    verified += 1
                elif status in ("Review", "Not Verified"):
                    review += 1

            total_topics += total
            total_completed += completed
            total_verified += verified
            total_review += review

            summary.append(
                (
                    sid, name, code, teacher,
                    total, completed, verified
                )
            )

        conn.close()

        self.stats.add_widget(
            self.make_stat_box(
                "SUBJECTS",
                len(subjects),
                "Available"
            )
        )

        self.stats.add_widget(
            self.make_stat_box(
                "TOPICS",
                total_topics,
                f"{total_completed} completed"
            )
        )

        self.stats.add_widget(
            self.make_stat_box(
                "VERIFIED",
                total_verified,
                "Fully verified"
            )
        )

        self.stats.add_widget(
            self.make_stat_box(
                "REVIEW",
                total_review,
                "Needs attention"
            )
        )

        for (
            sid, name, code, teacher,
            total, completed, verified
        ) in summary:

            progress = int(
                completed / total * 100
            ) if total else 0

            card = BoxLayout(
                orientation="vertical",
                size_hint_y=None,
                height=dp(205),
                padding=dp(16),
                spacing=dp(7)
            )

            card.add_widget(
                make_label(
                    f"{code} - {name}",
                    font_size=19,
                    bold=True,
                    height=34
                )
            )

            card.add_widget(
                make_label(
                    f"Teacher: {teacher}",
                    font_size=14,
                    color=MUTED,
                    height=28
                )
            )

            card.add_widget(
                make_label(
                    f"Progress: {completed}/{total} topics ({progress}%)",
                    font_size=15,
                    height=30
                )
            )

            card.add_widget(
                ProgressBar(
                    max=100,
                    value=progress,
                    size_hint_y=None,
                    height=dp(12)
                )
            )

            card.add_widget(
                make_label(
                    f"Verified topics: {verified}/{total}",
                    font_size=14,
                    color=SUCCESS,
                    height=28
                )
            )

            open_btn = make_button(
                "Open Subject",
                color=PRIMARY,
                height=45
            )

            open_btn.subject_id = sid
            open_btn.subject_name = name
            open_btn.bind(
                on_release=self.open_subject
            )

            card.add_widget(open_btn)

            self.subjects_box.add_widget(card)

    def open_subject(self, button):
        app = App.get_running_app()

        screen = app.root.get_screen("topics")
        screen.subject_id = button.subject_id
        screen.subject_name = button.subject_name
        screen.load_topics()

        app.root.current = "topics"

    def logout(self, *args):
        app = App.get_running_app()

        app.current_user = ""
        app.current_role = ""
        app.current_username = ""

        login = app.root.get_screen("login")
        login.username.text = ""
        login.password.text = ""
        login.error_label.text = ""

        app.root.current = "login"


# ============================================================
# TOPICS
# ============================================================

class TopicScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.subject_id = None
        self.subject_name = ""

        root = BoxLayout(
            orientation="vertical",
            padding=dp(20),
            spacing=dp(12)
        )

        top = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(70),
            spacing=dp(10)
        )

        self.heading = make_label(
            "Subject",
            font_size=25,
            bold=True,
            height=60
        )

        top.add_widget(self.heading)

        back = make_button(
            "Back",
            color=PRIMARY_DARK,
            width=110,
            height=46
        )
        back.bind(on_release=self.go_back)

        top.add_widget(back)
        root.add_widget(top)

        rule = make_label(
            "Verification rule: topic is VERIFIED when student "
            f"confirmation is at least {int(CONFIRMATION_THRESHOLD)}% "
            f"and average quiz score is at least {int(QUIZ_THRESHOLD)}%.",
            font_size=14,
            color=MUTED,
            height=50
        )

        root.add_widget(rule)

        self.scroll = ScrollView(
            bar_width=dp(6)
        )

        self.topic_box = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(12)
        )

        self.topic_box.bind(
            minimum_height=self.topic_box.setter("height")
        )

        self.scroll.add_widget(self.topic_box)
        root.add_widget(self.scroll)

        self.add_widget(root)

    def load_topics(self):
        self.topic_box.clear_widgets()
        self.heading.text = self.subject_name

        app = App.get_running_app()

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, unit_no, topic_name,
                   completed, completed_date
            FROM topics
            WHERE subject_id=?
            ORDER BY unit_no, id
        """, (self.subject_id,))

        topics = cur.fetchall()
        conn.close()

        current_unit = None

        for (
            topic_id, unit, topic_name,
            completed, completed_date
        ) in topics:

            if current_unit != unit:
                current_unit = unit

                self.topic_box.add_widget(
                    make_label(
                        f"UNIT {unit}",
                        font_size=18,
                        bold=True,
                        color=PRIMARY,
                        height=42
                    )
                )

            v = get_verification(topic_id)

            card_height = (
                260 if app.current_role == "student"
                else 235
            )

            card = BoxLayout(
                orientation="vertical",
                size_hint_y=None,
                height=dp(card_height),
                padding=dp(14),
                spacing=dp(6)
            )

            card.add_widget(
                make_label(
                    topic_name,
                    font_size=18,
                    bold=True,
                    height=34
                )
            )

            teacher_status = (
                f"Completed on {completed_date}"
                if completed and completed_date
                else "Completed"
                if completed
                else "Pending"
            )

            card.add_widget(
                make_label(
                    f"Teacher status: {teacher_status}",
                    font_size=14,
                    color=SUCCESS if completed else MUTED,
                    height=28
                )
            )

            card.add_widget(
                make_label(
                    f"Student confirmations: "
                    f"{v['confirmations']}/{v['students']} "
                    f"({v['confirmation_rate']:.0f}%)",
                    font_size=14,
                    height=28
                )
            )

            card.add_widget(
                make_label(
                    f"Quiz average: {v['quiz_average']:.1f}% "
                    f"({v['attempts']} attempts)",
                    font_size=14,
                    height=28
                )
            )

            status_color = MUTED

            if v["status"] == "Verified":
                status_color = SUCCESS
            elif v["status"] == "Review":
                status_color = WARNING
            elif v["status"] == "Not Verified":
                status_color = DANGER

            card.add_widget(
                make_label(
                    f"Verification status: {v['status']}",
                    font_size=15,
                    bold=True,
                    color=status_color,
                    height=30
                )
            )

            if app.current_role == "teacher":
                btn = make_button(
                    "Mark Pending" if completed
                    else "Mark Completed",
                    color=WARNING if completed else SUCCESS,
                    height=44
                )

                btn.topic_id = topic_id
                btn.completed = completed
                btn.bind(
                    on_release=self.update_topic
                )

                card.add_widget(btn)

            elif app.current_role == "student":
                if completed:
                    confirmed = self.student_confirmed(
                        app.current_username,
                        topic_id
                    )

                    row = BoxLayout(
                        orientation="horizontal",
                        size_hint_y=None,
                        height=dp(46),
                        spacing=dp(10)
                    )

                    confirm_btn = make_button(
                        "Confirmed" if confirmed
                        else "Confirm Topic",
                        color=SUCCESS if confirmed else PRIMARY,
                        height=44
                    )

                    confirm_btn.topic_id = topic_id
                    confirm_btn.disabled = confirmed
                    confirm_btn.bind(
                        on_release=self.confirm_topic
                    )

                    result = self.student_quiz_result(
                        app.current_username,
                        topic_id
                    )

                    quiz_btn = make_button(
                        f"Quiz: {result:.0f}%"
                        if result is not None
                        else "Take Quiz",
                        color=PRIMARY_DARK,
                        height=44
                    )

                    quiz_btn.topic_id = topic_id
                    quiz_btn.topic_name = topic_name
                    quiz_btn.disabled = result is not None
                    quiz_btn.bind(
                        on_release=self.open_quiz
                    )

                    row.add_widget(confirm_btn)
                    row.add_widget(quiz_btn)

                    card.add_widget(row)

                else:
                    card.add_widget(
                        make_label(
                            "Confirmation and quiz will unlock after "
                            "teacher marks the topic completed.",
                            font_size=13,
                            color=MUTED,
                            height=40
                        )
                    )

            elif app.current_role == "admin":
                if v["status"] == "Verified":
                    msg = (
                        "Verified: student confirmation and quiz "
                        "thresholds are satisfied."
                    )
                    col = SUCCESS

                elif v["status"] == "Review":
                    msg = (
                        "Review required: some evidence is available "
                        "but threshold is not fully satisfied."
                    )
                    col = WARNING

                elif v["status"] == "Not Verified":
                    msg = (
                        "Alert: teacher marked this topic complete, "
                        "but verification evidence is insufficient."
                    )
                    col = DANGER

                else:
                    msg = (
                        "Waiting for teacher to complete this topic."
                    )
                    col = MUTED

                card.add_widget(
                    make_label(
                        msg,
                        font_size=13,
                        color=col,
                        height=42
                    )
                )

            self.topic_box.add_widget(card)

    def update_topic(self, button):
        new_status = 0 if button.completed else 1

        completed_date = (
            date.today().strftime("%d %b %Y")
            if new_status else None
        )

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            UPDATE topics
            SET completed=?, completed_date=?
            WHERE id=?
        """, (
            new_status,
            completed_date,
            button.topic_id
        ))

        if new_status == 0:
            cur.execute(
                "DELETE FROM feedback WHERE topic_id=?",
                (button.topic_id,)
            )

            cur.execute(
                "DELETE FROM quiz_results WHERE topic_id=?",
                (button.topic_id,)
            )

        conn.commit()
        conn.close()

        self.load_topics()

    def student_confirmed(
        self,
        username,
        topic_id
    ):
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT COUNT(*)
            FROM feedback
            WHERE student=? AND topic_id=? AND confirmed=1
        """, (
            username,
            topic_id
        ))

        result = cur.fetchone()[0] > 0
        conn.close()

        return result

    def student_quiz_result(
        self,
        username,
        topic_id
    ):
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT percentage
            FROM quiz_results
            WHERE student=? AND topic_id=?
        """, (
            username,
            topic_id
        ))

        row = cur.fetchone()
        conn.close()

        return float(row[0]) if row else None

    def confirm_topic(self, button):
        app = App.get_running_app()

        if self.student_confirmed(
            app.current_username,
            button.topic_id
        ):
            show_message(
                "Already Confirmed",
                "You already confirmed this topic."
            )
            return

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO feedback(
                student,
                topic_id,
                confirmed,
                confirmed_date
            )
            VALUES (?, ?, 1, ?)
        """, (
            app.current_username,
            button.topic_id,
            date.today().strftime("%d %b %Y")
        ))

        conn.commit()
        conn.close()

        show_message(
            "Saved",
            "Your confirmation has been recorded."
        )

        self.load_topics()

    def open_quiz(self, button):
        app = App.get_running_app()

        quiz = app.root.get_screen("quiz")
        quiz.topic_id = button.topic_id
        quiz.topic_name = button.topic_name
        quiz.load_quiz()

        app.root.current = "quiz"

    def go_back(self, *args):
        app = App.get_running_app()

        dashboard = app.root.get_screen("dashboard")
        dashboard.load_dashboard()

        app.root.current = "dashboard"


# ============================================================
# QUIZ
# ============================================================

class QuizScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.topic_id = None
        self.topic_name = ""

        self.questions = []
        self.index = 0
        self.score = 0
        self.selected = None
        self.option_buttons = []

        root = AnchorLayout(
            anchor_x="center",
            anchor_y="center",
            padding=dp(35)
        )

        card = BoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            width=dp(760),
            height=dp(590),
            padding=dp(25),
            spacing=dp(12)
        )

        self.heading = make_label(
            "Topic Quiz",
            font_size=25,
            bold=True,
            height=50
        )

        card.add_widget(self.heading)

        self.question_no = make_label(
            "",
            font_size=14,
            color=PRIMARY,
            bold=True,
            height=28
        )

        card.add_widget(self.question_no)

        self.question_text = make_label(
            "",
            font_size=19,
            bold=True,
            height=90
        )

        card.add_widget(self.question_text)

        for code in ["A", "B", "C", "D"]:
            btn = Button(
                text="",
                size_hint_y=None,
                height=dp(56),
                background_normal="",
                background_down="",
                background_color=(0.90, 0.92, 0.96, 1),
                color=TEXT,
                font_size=16,
                halign="left",
                valign="middle"
            )

            btn.option_code = code

            btn.bind(
                size=lambda obj, size: setattr(
                    obj, "text_size",
                    (size[0] - dp(20), None)
                )
            )

            btn.bind(
                on_release=self.select_option
            )

            self.option_buttons.append(btn)
            card.add_widget(btn)

        self.next_btn = make_button(
            "Next Question",
            color=PRIMARY,
            height=50
        )

        self.next_btn.bind(
            on_release=self.next_question
        )

        card.add_widget(self.next_btn)

        cancel = make_button(
            "Exit Quiz",
            color=MUTED,
            height=44
        )

        cancel.bind(on_release=self.cancel)
        card.add_widget(cancel)

        root.add_widget(card)
        self.add_widget(root)

    def load_quiz(self):
        app = App.get_running_app()

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT percentage
            FROM quiz_results
            WHERE student=? AND topic_id=?
        """, (
            app.current_username,
            self.topic_id
        ))

        existing = cur.fetchone()

        if existing:
            conn.close()

            show_message(
                "Quiz Completed",
                f"You already completed this quiz. "
                f"Score: {existing[0]:.0f}%"
            )

            app.root.current = "topics"
            return

        cur.execute("""
            SELECT
                id,
                question,
                option_a,
                option_b,
                option_c,
                option_d,
                correct_option
            FROM quiz_questions
            WHERE topic_id=?
            ORDER BY id
        """, (
            self.topic_id,
        ))

        self.questions = cur.fetchall()
        conn.close()

        if not self.questions:
            show_message(
                "Quiz Not Available",
                "No quiz questions are available for this topic."
            )

            app.root.current = "topics"
            return

        self.index = 0
        self.score = 0
        self.selected = None

        self.heading.text = (
            f"Topic Quiz - {self.topic_name}"
        )

        self.show_question()

    def show_question(self):
        self.selected = None

        row = self.questions[self.index]

        _, question, a, b, c, d, _ = row

        self.question_no.text = (
            f"Question {self.index + 1} of "
            f"{len(self.questions)}"
        )

        self.question_text.text = question

        options = {
            "A": a,
            "B": b,
            "C": c,
            "D": d
        }

        for btn in self.option_buttons:
            btn.text = (
                f"{btn.option_code}. "
                f"{options[btn.option_code]}"
            )

            btn.background_color = (
                0.90, 0.92, 0.96, 1
            )

            btn.color = TEXT

        if self.index == len(self.questions) - 1:
            self.next_btn.text = "Submit Quiz"
        else:
            self.next_btn.text = "Next Question"

    def select_option(self, button):
        self.selected = button.option_code

        for btn in self.option_buttons:
            if btn.option_code == self.selected:
                btn.background_color = PRIMARY
                btn.color = WHITE
            else:
                btn.background_color = (
                    0.90, 0.92, 0.96, 1
                )
                btn.color = TEXT

    def next_question(self, *args):
        if not self.selected:
            show_message(
                "Select an Answer",
                "Please select one option."
            )
            return

        correct = self.questions[self.index][6]

        if self.selected == correct:
            self.score += 1

        if self.index < len(self.questions) - 1:
            self.index += 1
            self.show_question()
        else:
            self.save_result()

    def save_result(self):
        app = App.get_running_app()

        total = len(self.questions)

        percentage = (
            self.score / total * 100
            if total else 0
        )

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT OR REPLACE INTO quiz_results(
                student,
                topic_id,
                score,
                total_questions,
                percentage,
                attempted_date
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            app.current_username,
            self.topic_id,
            self.score,
            total,
            percentage,
            date.today().strftime("%d %b %Y")
        ))

        conn.commit()
        conn.close()

        show_message(
            "Quiz Submitted",
            f"Your score is {self.score}/{total} "
            f"({percentage:.0f}%)."
        )

        topics = app.root.get_screen("topics")
        topics.load_topics()

        app.root.current = "topics"

    def cancel(self, *args):
        App.get_running_app().root.current = "topics"


# ============================================================
# APP
# ============================================================

class SyllabusApp(App):

    current_user = ""
    current_role = ""
    current_username = ""

    def build(self):
        initialize_database()

        manager = ScreenManager(
            transition=FadeTransition(duration=0.15)
        )

        manager.add_widget(
            LoginScreen(name="login")
        )

        manager.add_widget(
            DashboardScreen(name="dashboard")
        )

        manager.add_widget(
            TopicScreen(name="topics")
        )

        manager.add_widget(
            QuizScreen(name="quiz")
        )

        return manager


if __name__ == "__main__":
    SyllabusApp().run()
