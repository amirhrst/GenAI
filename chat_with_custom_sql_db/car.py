import sqlite3
import random
import string
from datetime import datetime, timedelta

# Function to generate a random car brand
def random_brand():
    brands = ['Toyota', 'Honda', 'Ford', 'Chevrolet', 'BMW', 'Mercedes', 'Hyundai', 'Nissan', 'Volkswagen', 'Audi']
    return random.choice(brands)

# Function to generate a random car model name
def random_model():
    return ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase, k=3))

# Function to generate a random price
def random_price():
    return random.randint(5000, 50000)

# Function to generate a random sale date within the last 3 years
def random_date():
    start_date = datetime.now() - timedelta(days=3*365)
    random_date = start_date + timedelta(days=random.randint(0, 3*365))
    return random_date.strftime('%Y-%m-%d')

# Create a connection to a new SQLite database
conn = sqlite3.connect('random_car_sales_data.db')  # This will create a file named 'random_car_sales_data.db' in your working directory
cursor = conn.cursor()

# Create a table for car sales data
cursor.execute('''
    CREATE TABLE IF NOT EXISTS CarSales (
        SaleID INTEGER PRIMARY KEY AUTOINCREMENT,
        Brand TEXT,
        Model TEXT,
        Price INTEGER,
        SaleDate TEXT
    )
''')

# Generate random data
data = [(random_brand(), random_model(), random_price(), random_date()) for _ in range(50)]

# Insert the random data into the CarSales table
cursor.executemany('''
    INSERT INTO CarSales (Brand, Model, Price, SaleDate)
    VALUES (?, ?, ?, ?)
''', data)

# Commit changes and close the connection
conn.commit()

# Fetch and display the data to verify
cursor.execute("SELECT * FROM CarSales")
rows = cursor.fetchall()
for row in rows:
    print(row)

# Close the connection
conn.close()
