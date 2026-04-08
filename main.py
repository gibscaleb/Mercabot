import os
import random
import psycopg2
import bcrypt
from psycopg2.extras import RealDictCursor
from datetime import datetime
from fastapi import FastAPI, Request, Form, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --- CONEXIÓN A BASE DE DATOS ---
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        user=os.getenv("DB_USER", "admin"),
        password=os.getenv("DB_PASSWORD", "password123"),
        dbname=os.getenv("DB_NAME", "mercabot")
    )

# --- MIDDLEWARE DE USUARIO ---
def get_current_user(request: Request):
    user_id = request.cookies.get("user_session")
    if not user_id:
        return None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id, email, es_admin, fecha_registro FROM usuarios WHERE id = %s", (int(user_id),))
        user = cur.fetchone()
        cur.close()
        conn.close()
        return user
    except Exception:
        return None

# --- RUTAS DE AUTENTICACIÓN ---

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = None):
    return templates.TemplateResponse("login.html", {"request": request, "error": error})

@app.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
        response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="user_session", value=str(user['id']), httponly=True)
        return response
    
    return templates.TemplateResponse("login.html", {"request": request, "error": "Email o contraseña incorrectos"})

@app.post("/registro")
async def registrar_usuario(request: Request, email: str = Form(...), password: str = Form(...)):
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO usuarios (email, password_hash) VALUES (%s, %s)", (email, hashed_pw))
        conn.commit()
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    except psycopg2.IntegrityError:
        return templates.TemplateResponse("registro.html", {"request": request, "error": "El correo ya está registrado"})
    finally:
        cur.close()
        conn.close()

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("user_session")
    return response

# --- GESTIÓN DE FAVORITOS ---

@app.post("/agregar-favorito")
async def agregar_favorito(request: Request, producto_id: str = Form(...)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO favoritos (usuario_id, producto_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (user['id'], producto_id))
        conn.commit()
    finally:
        cur.close()
        conn.close()
    return RedirectResponse(url=f"/?selected_id={producto_id}", status_code=303)

# --- PANEL ADMINISTRADOR ---

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request):
    user = get_current_user(request)
    if not user or not user['es_admin']:
        return RedirectResponse(url="/", status_code=303)
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT id, email, es_admin, fecha_registro FROM usuarios ORDER BY id DESC")
    usuarios = cur.fetchall()
    cur.execute("SELECT p.*, (SELECT COUNT(*) FROM favoritos f WHERE f.producto_id = p.id) as total_seguidores FROM productos p")
    productos = cur.fetchall()
    cur.close()
    conn.close()
    return templates.TemplateResponse("admin.html", {"request": request, "usuarios": usuarios, "productos": productos, "user": user})

# --- VISTA PRINCIPAL (EL TRACKER) ---

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, q: str = None, selected_id: str = None):
    user = get_current_user(request)
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor) 
    
    if q:
        cursor.execute("SELECT * FROM productos WHERE nombre_producto ILIKE %s", (f"%{q}%",))
    else:
        cursor.execute("SELECT * FROM productos")
    productos = cursor.fetchall()

    labels, data, producto_grafica, stats = [], [], None, {}

    if selected_id:
        producto_grafica = next((p for p in productos if str(p['id']) == selected_id), None)
        if producto_grafica:
            cursor.execute("SELECT precio_visto, fecha_muestreo FROM historial_precios WHERE producto_id = %s ORDER BY fecha_muestreo ASC", (producto_grafica['id'],))
            history = cursor.fetchall()
            labels = [h['fecha_muestreo'].strftime("%Y-%m-%d %H:%M") for h in history]
            data = [float(h['precio_visto']) for h in history]
            
            if data:
                stats = {
                    "max": max(data),
                    "min": min(data),
                    "avg": round(sum(data) / len(data), 2),
                    "current": data[-1]
                }

    cursor.close()
    conn.close()
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "productos": productos, 
        "chart_labels": labels, 
        "chart_data": data, 
        "producto_grafica": producto_grafica, 
        "stats": stats,
        "user": user,
        "query": q
    })

@app.post("/buscar-precio")
async def buscar_precio(producto_id: str = Form(...)):
    conn = get_db_connection()
    cur = conn.cursor()
    nuevo_precio = round(random.uniform(4000.0, 14000.0), 2)
    cur.execute("INSERT INTO historial_precios (producto_id, precio_visto) VALUES (%s, %s)", (producto_id, nuevo_precio))
    conn.commit()
    cur.close()
    conn.close()
    return RedirectResponse(url=f"/?selected_id={producto_id}", status_code=303)