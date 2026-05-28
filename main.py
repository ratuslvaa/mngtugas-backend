from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Manajemen Tugas Kuliah API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 3306)),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )

class TugasBase(BaseModel):
    user_id: int
    mk_id: int
    judul: str
    deskripsi: Optional[str] = None
    deadline: datetime
    prioritas: str  # rendah / sedang / tinggi
    status: str     # belum / dikerjakan / selesai

class TugasUpdate(BaseModel):
    user_id: Optional[int] = None
    mk_id: Optional[int] = None
    judul: Optional[str] = None
    deskripsi: Optional[str] = None
    deadline: Optional[datetime] = None
    prioritas: Optional[str] = None
    status: Optional[str] = None

@app.get("/")
def root():
    return {"message": "API Manajemen Tugas Kuliah berjalan"}

@app.get("/tugas")
def get_all():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT 
            tugas.id,
            users.nama AS mahasiswa,
            mata_kuliah.nama_mk,
            tugas.judul,
            tugas.deskripsi,
            tugas.deadline,
            tugas.prioritas,
            tugas.status,
            tugas.created_at
        FROM tugas
        JOIN users ON tugas.user_id = users.id
        JOIN mata_kuliah ON tugas.mk_id = mata_kuliah.id
        ORDER BY tugas.deadline ASC
    """)
    rows = cursor.fetchall()
    db.close()
    return rows

@app.get("/tugas/{id}")
def get_one(id: int):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tugas WHERE id = %s", (id,))
    row = cursor.fetchone()
    db.close()
    if not row:
        raise HTTPException(status_code=404, detail="Tugas tidak ditemukan")
    return row

@app.post("/tugas", status_code=201)
def create(data: TugasBase):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO tugas
        (user_id, mk_id, judul, deskripsi, deadline, prioritas, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        data.user_id,
        data.mk_id,
        data.judul,
        data.deskripsi,
        data.deadline,
        data.prioritas,
        data.status
    ))
    db.commit()
    new_id = cursor.lastrowid
    db.close()
    return {
        "id": new_id,
        "message": "Tugas berhasil ditambahkan"
    }

@app.put("/tugas/{id}")
def update(id: int, data: TugasUpdate):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tugas WHERE id = %s", (id,))
    row = cursor.fetchone()
    if not row:
        db.close()
        raise HTTPException(status_code=404, detail="Tugas tidak ditemukan")
    updated = {
        **row,
        **{k: v for k, v in data.dict().items() if v is not None}
    }
    cursor.execute("""
        UPDATE tugas
        SET
            user_id=%s,
            mk_id=%s,
            judul=%s,
            deskripsi=%s,
            deadline=%s,
            prioritas=%s,
            status=%s
        WHERE id=%s
    """, (
        updated["user_id"],
        updated["mk_id"],
        updated["judul"],
        updated["deskripsi"],
        updated["deadline"],
        updated["prioritas"],
        updated["status"],
        id
    ))
    db.commit()
    db.close()
    return {"message": "Tugas berhasil diperbarui"}

@app.delete("/tugas/{id}")
def delete(id: int):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("DELETE FROM tugas WHERE id = %s", (id,))
    db.commit()
    affected = cursor.rowcount
    db.close()
    if affected == 0:
        raise HTTPException(status_code=404, detail="Tugas tidak ditemukan")
    return {"message": "Tugas berhasil dihapus"}
