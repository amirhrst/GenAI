import sqlite3
import random

# Connect to SQLite
connection = sqlite3.connect("student.db")

# Create a cursor object to insert records and create table
cursor = connection.cursor()

# Create the table
table_info = """
CREATE TABLE IF NOT EXISTS STUDENT(
    NAME VARCHAR(25),
    CLASS VARCHAR(25),
    SECTION VARCHAR(25),
    MARKS INT
)
"""

cursor.execute(table_info)

# Sample data for random insertions
names = ['Alex', 'Sophia', 'Michael', 'Sarah', 'Daniel', 'Emma', 'David', 'Olivia', 'Liam', 'Isabella']
classes = ['AI', 'Cyber Security', 'Machine Learning', 'Data Science', 'DEVOPS']
sections = ['A', 'B', 'C', 'D']

# Insert initial records
initial_records = [
    ('A', 'Data Science', 'A', 90),
    ('John', 'Data Science', 'B', 100),
    ('Mukesh', 'Data Science', 'A', 86),
    ('Jacob', 'DEVOPS', 'A', 50),
    ('Dipesh', 'DEVOPS', 'A', 35)
]

cursor.executemany("INSERT INTO STUDENT VALUES (?, ?, ?, ?)", initial_records)

# Insert random records
for _ in range(20):  # Change the range to add more or fewer records
    name = random.choice(names)
    class_name = random.choice(classes)
    section = random.choice(sections)
    marks = random.randint(30, 100)
    cursor.execute("INSERT INTO STUDENT VALUES (?, ?, ?, ?)", (name, class_name, section, marks))

# Display all the records
print("The inserted records are:")
data = cursor.execute("SELECT * FROM STUDENT")
for row in data:
    print(row)

# Commit your changes in the database
connection.commit()
connection.close()
