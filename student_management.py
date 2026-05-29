"""
Student Management System
Author: Sai Surya Yeedulapally
Stack: Python · SQLite · OOP
Description: Console-based CRUD application for managing student records using SQLite and OOP principles.
"""

import sqlite3
import os


DB_NAME = "students.db"


class Database:
    """Handles SQLite connection and schema setup."""

    def __init__(self, db_name=DB_NAME):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                name     TEXT    NOT NULL,
                age      INTEGER NOT NULL,
                email    TEXT    UNIQUE NOT NULL,
                course   TEXT    NOT NULL,
                grade    TEXT
            )
        """)
        self.conn.commit()

    def close(self):
        self.conn.close()


class Student:
    """Represents a single student record."""

    def __init__(self, name, age, email, course, grade=None, student_id=None):
        self.id = student_id
        self.name = name
        self.age = age
        self.email = email
        self.course = course
        self.grade = grade

    def __repr__(self):
        return (
            f"Student(id={self.id}, name='{self.name}', age={self.age}, "
            f"email='{self.email}', course='{self.course}', grade='{self.grade}')"
        )


class StudentRepository:
    """Data access layer — wraps all CRUD operations."""

    def __init__(self, db: Database):
        self.db = db

    def add(self, student: Student) -> int:
        try:
            self.db.cursor.execute(
                "INSERT INTO students (name, age, email, course, grade) VALUES (?, ?, ?, ?, ?)",
                (student.name, student.age, student.email, student.course, student.grade),
            )
            self.db.conn.commit()
            return self.db.cursor.lastrowid
        except sqlite3.IntegrityError:
            raise ValueError(f"Email '{student.email}' already exists.")

    def get_all(self):
        self.db.cursor.execute("SELECT * FROM students ORDER BY id")
        rows = self.db.cursor.fetchall()
        return [Student(*row[1:], student_id=row[0]) for row in rows]

    def get_by_id(self, student_id: int):
        self.db.cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
        row = self.db.cursor.fetchone()
        if row:
            return Student(*row[1:], student_id=row[0])
        return None

    def search_by_name(self, name: str):
        self.db.cursor.execute(
            "SELECT * FROM students WHERE name LIKE ?", (f"%{name}%",)
        )
        rows = self.db.cursor.fetchall()
        return [Student(*row[1:], student_id=row[0]) for row in rows]

    def update(self, student_id: int, **fields):
        if not fields:
            return False
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [student_id]
        self.db.cursor.execute(
            f"UPDATE students SET {set_clause} WHERE id = ?", values
        )
        self.db.conn.commit()
        return self.db.cursor.rowcount > 0

    def delete(self, student_id: int) -> bool:
        self.db.cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
        self.db.conn.commit()
        return self.db.cursor.rowcount > 0

    def count(self) -> int:
        self.db.cursor.execute("SELECT COUNT(*) FROM students")
        return self.db.cursor.fetchone()[0]


class StudentManagementCLI:
    """Interactive console interface for the Student Management System."""

    def __init__(self):
        self.db = Database()
        self.repo = StudentRepository(self.db)

    def _print_header(self):
        print("\n" + "=" * 55)
        print("       STUDENT MANAGEMENT SYSTEM")
        print("       Sai Surya Yeedulapally · Python + SQLite")
        print("=" * 55)

    def _print_menu(self):
        print("\n  1. Add Student")
        print("  2. View All Students")
        print("  3. Search Student by Name")
        print("  4. Update Student")
        print("  5. Delete Student")
        print("  6. View Summary Stats")
        print("  0. Exit")
        print("-" * 55)

    def _print_student(self, s: Student):
        print(f"\n  ID     : {s.id}")
        print(f"  Name   : {s.name}")
        print(f"  Age    : {s.age}")
        print(f"  Email  : {s.email}")
        print(f"  Course : {s.course}")
        print(f"  Grade  : {s.grade or 'N/A'}")
        print("  " + "-" * 40)

    def add_student(self):
        print("\n--- Add New Student ---")
        name = input("  Name   : ").strip()
        age_str = input("  Age    : ").strip()
        email = input("  Email  : ").strip()
        course = input("  Course : ").strip()
        grade = input("  Grade (optional, press Enter to skip): ").strip() or None

        if not all([name, age_str, email, course]):
            print("  [!] All fields except grade are required.")
            return

        try:
            age = int(age_str)
        except ValueError:
            print("  [!] Age must be a number.")
            return

        student = Student(name, age, email, course, grade)
        try:
            new_id = self.repo.add(student)
            print(f"  [✓] Student added with ID: {new_id}")
        except ValueError as e:
            print(f"  [!] Error: {e}")

    def view_all(self):
        students = self.repo.get_all()
        if not students:
            print("\n  No students found.")
            return
        print(f"\n--- All Students ({len(students)} total) ---")
        for s in students:
            self._print_student(s)

    def search_student(self):
        name = input("\n  Enter name to search: ").strip()
        results = self.repo.search_by_name(name)
        if not results:
            print("  No matching students found.")
            return
        print(f"\n  Found {len(results)} result(s):")
        for s in results:
            self._print_student(s)

    def update_student(self):
        try:
            sid = int(input("\n  Enter Student ID to update: "))
        except ValueError:
            print("  [!] Invalid ID.")
            return

        student = self.repo.get_by_id(sid)
        if not student:
            print(f"  [!] No student with ID {sid}.")
            return

        print(f"\n  Updating: {student.name} (leave blank to keep current value)")
        updates = {}

        name = input(f"  Name [{student.name}]: ").strip()
        if name:
            updates["name"] = name

        age_str = input(f"  Age [{student.age}]: ").strip()
        if age_str:
            try:
                updates["age"] = int(age_str)
            except ValueError:
                print("  [!] Invalid age — keeping current.")

        email = input(f"  Email [{student.email}]: ").strip()
        if email:
            updates["email"] = email

        course = input(f"  Course [{student.course}]: ").strip()
        if course:
            updates["course"] = course

        grade = input(f"  Grade [{student.grade or 'N/A'}]: ").strip()
        if grade:
            updates["grade"] = grade

        if updates:
            success = self.repo.update(sid, **updates)
            print("  [✓] Student updated." if success else "  [!] Update failed.")
        else:
            print("  No changes made.")

    def delete_student(self):
        try:
            sid = int(input("\n  Enter Student ID to delete: "))
        except ValueError:
            print("  [!] Invalid ID.")
            return

        student = self.repo.get_by_id(sid)
        if not student:
            print(f"  [!] No student with ID {sid}.")
            return

        confirm = input(f"  Delete '{student.name}'? (yes/no): ").strip().lower()
        if confirm == "yes":
            self.repo.delete(sid)
            print("  [✓] Student deleted.")
        else:
            print("  Deletion cancelled.")

    def summary_stats(self):
        total = self.repo.count()
        students = self.repo.get_all()
        print(f"\n--- Summary ---")
        print(f"  Total Students : {total}")
        if students:
            courses = {}
            for s in students:
                courses[s.course] = courses.get(s.course, 0) + 1
            print("  Courses        :")
            for course, count in sorted(courses.items()):
                print(f"    - {course}: {count} student(s)")

    def run(self):
        self._print_header()
        while True:
            self._print_menu()
            choice = input("  Enter choice: ").strip()
            if choice == "1":
                self.add_student()
            elif choice == "2":
                self.view_all()
            elif choice == "3":
                self.search_student()
            elif choice == "4":
                self.update_student()
            elif choice == "5":
                self.delete_student()
            elif choice == "6":
                self.summary_stats()
            elif choice == "0":
                print("\n  Goodbye!\n")
                self.db.close()
                break
            else:
                print("  [!] Invalid choice. Try again.")


if __name__ == "__main__":
    app = StudentManagementCLI()
    app.run()
