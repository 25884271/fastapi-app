from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "employees.db")

@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            salary INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    print(f"Database ready at {DB_PATH}")
    yield

app = FastAPI(lifespan=lifespan)

class EmployeeIn(BaseModel):
    name: str
    department: str
    salary: int

@app.get("/employees")
def get_all_employees():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, department, salary FROM employees ORDER BY id")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": row[0], "name": row[1], "department": row[2], "salary": row[3]} for row in rows]

@app.get("/employees/{employee_id}")
def get_employee_by_id(employee_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, department, salary FROM employees WHERE id = ?", (employee_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"id": row[0], "name": row[1], "department": row[2], "salary": row[3]}

@app.get("/salary/{department}")
def get_avg_salary(department: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT AVG(salary) FROM employees WHERE department = ?", (department,))
    result = cursor.fetchone()
    conn.close()
    if result[0] is None:
        raise HTTPException(status_code=404, detail="Department not found")
    return {"department": department, "average_salary": result[0]}

@app.post("/employees")
def create_employee(emp: EmployeeIn):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO employees (name, department, salary) VALUES (?, ?, ?)",
        (emp.name, emp.department, emp.salary)
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return {"id": new_id, "name": emp.name, "department": emp.department, "salary": emp.salary}

@app.delete("/employees/{employee_id}")
def delete_employee(employee_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
    conn.commit()
    deleted = cursor.rowcount
    conn.close()
    if not deleted:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"message": f"Employee {employee_id} deleted"}