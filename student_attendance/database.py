import hashlib
import os
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    return f"pbkdf2_sha256$200000${salt.hex()}${derived.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations, salt, hash_value = stored_hash.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        derived = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt),
            int(iterations),
        )
        return hashlib.compare_digest(derived.hex(), hash_value)
    except (ValueError, TypeError):
        return False


class DatabaseManager:
    def __init__(self, db_path: str | None = None):
        self.base_dir = Path(__file__).resolve().parent.parent
        self.db_path = Path(db_path) if db_path else self.base_dir / "data" / "attendance_system.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize_database()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize_database(self):
        with self.get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('Admin', 'Teacher')),
                    force_password_change INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS classes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    class_name TEXT NOT NULL,
                    section TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(class_name, section)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT UNIQUE NOT NULL,
                    roll_number TEXT UNIQUE NOT NULL,
                    full_name TEXT NOT NULL,
                    class_name TEXT NOT NULL,
                    section TEXT NOT NULL,
                    contact_number TEXT,
                    enrollment_date TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(class_name, roll_number)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL,
                    class_name TEXT NOT NULL,
                    section TEXT NOT NULL,
                    attendance_date TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('Present', 'Absent', 'Late', 'Excused')),
                    note TEXT,
                    UNIQUE(student_id, class_name, section, attendance_date)
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_students_class ON students(class_name, section)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(attendance_date)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance(student_id, attendance_date)"
            )
            conn.commit()

        if not self.get_user_by_username("admin"):
            self.create_user(
                username="admin",
                password="Admin@123",
                full_name="System Administrator",
                role="Admin",
                force_password_change=True,
            )

        self.seed_classes_and_students_if_empty()

    def create_user(
        self,
        username: str,
        password: str,
        full_name: str,
        role: str,
        force_password_change: bool = True,
    ) -> dict:
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO users (username, password_hash, full_name, role, force_password_change, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    username.strip(),
                    hash_password(password),
                    full_name.strip(),
                    role,
                    1 if force_password_change else 0,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
            conn.commit()
            user_id = cursor.lastrowid
        return self.get_user_by_id(user_id)

    def get_user_by_id(self, user_id: int):
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
        return dict(row) if row else None

    def get_user_by_username(self, username: str):
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE username = ?",
                (username.strip(),),
            ).fetchone()
        return dict(row) if row else None

    def authenticate_user(self, username: str, password: str):
        user = self.get_user_by_username(username)
        if not user:
            return None
        if verify_password(password, user["password_hash"]):
            return user
        return None

    def update_password(self, username: str, new_password: str):
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE users SET password_hash = ?, force_password_change = 0 WHERE username = ?",
                (hash_password(new_password), username.strip()),
            )
            conn.commit()

    def seed_classes_and_students_if_empty(self):
        with self.get_connection() as conn:
            existing_classes = conn.execute("SELECT COUNT(*) AS count FROM classes").fetchone()["count"]
            if existing_classes == 0:
                defaults = [
                    ("Class 10", "A"),
                    ("Class 10", "B"),
                    ("Class 9", "A"),
                    ("Class 8", "A"),
                ]
                for class_name, section in defaults:
                    conn.execute(
                        "INSERT INTO classes (class_name, section, created_at) VALUES (?, ?, ?)",
                        (class_name, section, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                    )
            students_count = conn.execute("SELECT COUNT(*) AS count FROM students").fetchone()["count"]
            if students_count == 0:
                sample_students = [
                    ("STU1001", "101", "Aarav Sharma", "Class 10", "A", "9876543210", "2024-01-15"),
                    ("STU1002", "102", "Diya Patel", "Class 10", "A", "9876543211", "2024-01-15"),
                    ("STU1003", "103", "Rohan Verma", "Class 10", "B", "9876543212", "2024-01-15"),
                    ("STU1004", "104", "Meera Singh", "Class 9", "A", "9876543213", "2024-01-15"),
                    ("STU1005", "105", "Kabir Joshi", "Class 8", "A", "9876543214", "2024-01-15"),
                    ("STU1006", "106", "Ishita Nair", "Class 10", "A", "9876543215", "2024-01-15"),
                ]
                for student in sample_students:
                    conn.execute(
                        """
                        INSERT INTO students (
                            student_id, roll_number, full_name, class_name, section, contact_number, enrollment_date, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (*student, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                    )
            conn.commit()

    def get_all_classes(self):
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT DISTINCT class_name, section FROM classes ORDER BY class_name, section"
            ).fetchall()
        return [dict(row) for row in rows]

    def get_class_names(self):
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT DISTINCT class_name FROM students ORDER BY class_name"
            ).fetchall()
        return [row["class_name"] for row in rows]

    def get_sections_for_class(self, class_name: str):
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT DISTINCT section FROM students WHERE class_name = ? ORDER BY section",
                (class_name,),
            ).fetchall()
        return [row["section"] for row in rows]

    def add_student(self, record: dict):
        if not record.get("student_id"):
            record["student_id"] = f"STU{uuid.uuid4().hex[:8].upper()}"
        if not record.get("roll_number"):
            raise ValueError("Roll number is required.")
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO students (
                    student_id, roll_number, full_name, class_name, section, contact_number, enrollment_date, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["student_id"],
                    record["roll_number"],
                    record["full_name"],
                    record["class_name"],
                    record["section"],
                    record.get("contact_number") or "",
                    record.get("enrollment_date") or datetime.now().strftime("%Y-%m-%d"),
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
            conn.commit()
        return record

    def update_student(self, student_id: str, record: dict):
        with self.get_connection() as conn:
            conn.execute(
                """
                UPDATE students
                SET roll_number = ?, full_name = ?, class_name = ?, section = ?, contact_number = ?, enrollment_date = ?
                WHERE student_id = ?
                """,
                (
                    record["roll_number"],
                    record["full_name"],
                    record["class_name"],
                    record["section"],
                    record.get("contact_number") or "",
                    record.get("enrollment_date") or datetime.now().strftime("%Y-%m-%d"),
                    student_id,
                ),
            )
            conn.commit()

    def delete_student(self, student_id: str):
        with self.get_connection() as conn:
            conn.execute("DELETE FROM attendance WHERE student_id = ?", (student_id,))
            conn.execute("DELETE FROM students WHERE student_id = ?", (student_id,))
            conn.commit()

    def search_students(self, query: str = ""):
        with self.get_connection() as conn:
            if query.strip():
                pattern = f"%{query.strip()}%"
                rows = conn.execute(
                    """
                    SELECT * FROM students
                    WHERE full_name LIKE ? OR roll_number LIKE ? OR class_name LIKE ? OR student_id LIKE ?
                    ORDER BY class_name, roll_number
                    """,
                    (pattern, pattern, pattern, pattern),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM students ORDER BY class_name, roll_number"
                ).fetchall()
        return [dict(row) for row in rows]

    def get_student_by_id(self, student_id: str):
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM students WHERE student_id = ?", (student_id,)).fetchone()
        return dict(row) if row else None

    def get_students_by_class(self, class_name: str, section: str | None = None):
        with self.get_connection() as conn:
            if section:
                rows = conn.execute(
                    "SELECT * FROM students WHERE class_name = ? AND section = ? ORDER BY roll_number",
                    (class_name, section),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM students WHERE class_name = ? ORDER BY roll_number",
                    (class_name,),
                ).fetchall()
        return [dict(row) for row in rows]

    def save_attendance_records(self, records: list[dict]):
        with self.get_connection() as conn:
            for record in records:
                conn.execute(
                    """
                    INSERT INTO attendance (student_id, class_name, section, attendance_date, status, note)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(student_id, class_name, section, attendance_date)
                    DO UPDATE SET status = excluded.status, note = excluded.note
                    """,
                    (
                        record["student_id"],
                        record["class_name"],
                        record["section"],
                        record["attendance_date"],
                        record["status"],
                        record.get("note") or "",
                    ),
                )
            conn.commit()

    def get_attendance_for_date(self, class_name: str, section: str, attendance_date: str):
        with self.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT s.student_id, s.roll_number, s.full_name, s.class_name, s.section,
                       COALESCE(a.status, 'Absent') AS status, COALESCE(a.note, '') AS note
                FROM students s
                LEFT JOIN attendance a
                    ON s.student_id = a.student_id
                   AND s.class_name = a.class_name
                   AND s.section = a.section
                   AND a.attendance_date = ?
                WHERE s.class_name = ? AND s.section = ?
                ORDER BY s.roll_number
                """,
                (attendance_date, class_name, section),
            ).fetchall()
        return [dict(row) for row in rows]

    def update_attendance_item(self, student_id: str, class_name: str, section: str, attendance_date: str, status: str, note: str = ""):
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO attendance (student_id, class_name, section, attendance_date, status, note)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(student_id, class_name, section, attendance_date)
                DO UPDATE SET status = excluded.status, note = excluded.note
                """,
                (student_id, class_name, section, attendance_date, status, note),
            )
            conn.commit()

    def get_student_attendance_history(self, student_id: str):
        with self.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT attendance_date, status, note
                FROM attendance
                WHERE student_id = ?
                ORDER BY attendance_date DESC
                """,
                (student_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_dashboard_stats(self):
        today = datetime.now().strftime("%Y-%m-%d")
        with self.get_connection() as conn:
            total_students = conn.execute("SELECT COUNT(*) AS count FROM students").fetchone()["count"]
            total_classes = conn.execute("SELECT COUNT(DISTINCT class_name) AS count FROM students").fetchone()["count"]
            present_today = conn.execute(
                "SELECT COUNT(*) AS count FROM attendance WHERE attendance_date = ? AND status IN ('Present', 'Late')",
                (today,),
            ).fetchone()["count"]
            absent_today = conn.execute(
                "SELECT COUNT(*) AS count FROM attendance WHERE attendance_date = ? AND status = 'Absent'",
                (today,),
            ).fetchone()["count"]
            attended_students = conn.execute(
                "SELECT COUNT(DISTINCT student_id) AS count FROM attendance WHERE attendance_date = ?",
                (today,),
            ).fetchone()["count"]
            attendance_percentage = round((present_today / total_students * 100), 2) if total_students else 0.0
        return {
            "total_students": total_students,
            "total_classes": total_classes,
            "present_today": present_today,
            "absent_today": absent_today,
            "attendance_percentage": attendance_percentage,
            "records_taken_today": attended_students,
        }

    def get_attendance_records(self, report_type: str = "daily", start_date: str | None = None, end_date: str | None = None, class_name: str | None = None, section: str | None = None, student_id: str | None = None):
        query = "SELECT * FROM attendance WHERE 1=1"
        params = []
        if start_date:
            query += " AND attendance_date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND attendance_date <= ?"
            params.append(end_date)
        if class_name:
            query += " AND class_name = ?"
            params.append(class_name)
        if section:
            query += " AND section = ?"
            params.append(section)
        if student_id:
            query += " AND student_id = ?"
            params.append(student_id)
        query += " ORDER BY attendance_date DESC, class_name, section"
        with self.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_student_name_by_id(self, student_id: str):
        with self.get_connection() as conn:
            row = conn.execute("SELECT full_name, roll_number FROM students WHERE student_id = ?", (student_id,)).fetchone()
        if not row:
            return "Unknown"
        return f"{row['full_name']} ({row['roll_number']})"

    def get_class_summary(self):
        with self.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT s.class_name, s.section, COUNT(s.id) AS total_students,
                       SUM(CASE WHEN a.status IN ('Present', 'Late') THEN 1 ELSE 0 END) AS present_count,
                       SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) AS absent_count
                FROM students s
                LEFT JOIN attendance a ON s.student_id = a.student_id AND a.attendance_date = ?
                GROUP BY s.class_name, s.section
                ORDER BY s.class_name, s.section
                """,
                (datetime.now().strftime("%Y-%m-%d"),),
            ).fetchall()
        return [dict(row) for row in rows]

    def export_report_rows(self, rows: list[dict], output_path: str):
        import pandas as pd
        df = pd.DataFrame(rows)
        df.to_csv(output_path, index=False)
        return output_path

    def export_report_excel(self, rows: list[dict], output_path: str):
        import pandas as pd
        df = pd.DataFrame(rows)
        df.to_excel(output_path, index=False)
        return output_path

    def get_low_attendance_students(self, threshold: float = 75.0):
        with self.get_connection() as conn:
            students = conn.execute("SELECT student_id, full_name, roll_number, class_name, section FROM students").fetchall()
        flagged = []
        for student in students:
            history = self.get_student_attendance_history(student["student_id"])
            if not history:
                continue
            present = sum(1 for item in history if item["status"] in ("Present", "Late"))
            counted = sum(1 for item in history if item["status"] != "Excused")
            if counted == 0:
                continue
            pct = round((present / counted) * 100, 2)
            if pct < threshold:
                flagged.append({
                    "student_id": student["student_id"],
                    "full_name": student["full_name"],
                    "roll_number": student["roll_number"],
                    "class_name": student["class_name"],
                    "section": student["section"],
                    "attendance_percent": pct,
                    "counted_days": counted,
                })
        return flagged
