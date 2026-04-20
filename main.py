import os
import uuid
import random
import psycopg2
import bcrypt
from psycopg2.extras import RealDictCursor
from datetime import datetime
from fastapi import FastAPI, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# ─── CONEXIÓN A BASE DE DATOS ───────────────────────────────────────────────

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        user=os.getenv("DB_USER", "admin"),
        password=os.getenv("DB_PASSWORD", "password123"),
        dbname=os.getenv("DB_NAME", "mercabot")
    )

def to_dict(row):
    """Convierte un RealDictRow a dict Python estándar (compatible con Jinja2)."""
    return dict(row) if row else None

def to_list(rows):
    """Convierte una lista de RealDictRow a lista de dicts estándar."""
    return [dict(r) for r in rows] if rows else []

# ─── HELPER: USUARIO ACTUAL ──────────────────────────────────────────────────

def get_current_user(request: Request):
    user_id = request.cookies.get("user_session")
    if not user_id:
        return None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT id, email, es_admin, fecha_registro FROM usuarios WHERE id = %s",
            (int(user_id),)
        )
        user = to_dict(cur.fetchone())
        cur.close()
        conn.close()
        return user
    except Exception:
        return None

# ─── AUTENTICACIÓN ───────────────────────────────────────────────────────────

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = None):
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": error, "user": None})


@app.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
    user = to_dict(cur.fetchone())
    cur.close()
    conn.close()

    if user and bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
        response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="user_session", value=str(user["id"]), httponly=True)
        return response

    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": "Email o contraseña incorrectos", "user": None}
    )


@app.get("/registro", response_class=HTMLResponse)
async def registro_page(request: Request):
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("registro.html", {"request": request, "user": None})


@app.post("/registro")
async def registrar_usuario(request: Request, email: str = Form(...), password: str = Form(...)):
    if len(password) < 6:
        return templates.TemplateResponse(
            "registro.html",
            {"request": request, "error": "La contraseña debe tener al menos 6 caracteres", "user": None}
        )
    hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO usuarios (email, password_hash) VALUES (%s, %s)",
            (email, hashed_pw)
        )
        conn.commit()
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    except psycopg2.IntegrityError:
        return templates.TemplateResponse(
            "registro.html",
            {"request": request, "error": "El correo ya está registrado", "user": None}
        )
    finally:
        cur.close()
        conn.close()


@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("user_session")
    return response

# ─── VISTA PRINCIPAL ─────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, q: str = None, selected_id: str = None):
    user = get_current_user(request)
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    if q:
        cursor.execute(
            "SELECT * FROM productos WHERE nombre_producto ILIKE %s ORDER BY nombre_producto",
            (f"%{q}%",)
        )
    else:
        cursor.execute("SELECT * FROM productos ORDER BY nombre_producto")
    productos = to_list(cursor.fetchall())

    labels, data, producto_grafica, stats = [], [], None, {}

    if selected_id:
        # Buscar el producto (puede no estar en la lista si se filtró)
        cursor.execute("SELECT * FROM productos WHERE id = %s", (selected_id,))
        producto_grafica = to_dict(cursor.fetchone())

        if producto_grafica:
            cursor.execute(
                "SELECT precio_visto, fecha_muestreo FROM historial_precios "
                "WHERE producto_id = %s ORDER BY fecha_muestreo ASC",
                (producto_grafica["id"],)
            )
            history = to_list(cursor.fetchall())
            labels = [h["fecha_muestreo"].strftime("%d/%m %H:%M") for h in history]
            data = [float(h["precio_visto"]) for h in history]

            if data:
                stats = {
                    "max":     max(data),
                    "min":     min(data),
                    "avg":     round(sum(data) / len(data), 2),
                    "current": data[-1],
                }

    cursor.close()
    conn.close()
    return templates.TemplateResponse("index.html", {
        "request":        request,
        "productos":      productos,
        "chart_labels":   labels,
        "chart_data":     data,
        "producto_grafica": producto_grafica,
        "stats":          stats,
        "user":           user,
        "query":          q,
    })


@app.post("/buscar-precio")
async def buscar_precio(producto_id: str = Form(...)):
    """Simula una consulta de precio (demo). En producción aquí iría el scraper."""
    conn = get_db_connection()
    cur = conn.cursor()

    # Precio aleatorio para demo
    nuevo_precio = round(random.uniform(3000.0, 15000.0), 2)

    # Marcar descuento si está por debajo del precio objetivo
    cur.execute("SELECT precio_objetivo FROM productos WHERE id = %s", (producto_id,))
    row = cur.fetchone()
    descuento = row and nuevo_precio < float(row[0])

    cur.execute(
        "INSERT INTO historial_precios (producto_id, precio_visto, descuento_detectado) VALUES (%s, %s, %s)",
        (producto_id, nuevo_precio, descuento)
    )
    conn.commit()
    cur.close()
    conn.close()
    return RedirectResponse(url=f"/?selected_id={producto_id}", status_code=303)

# ─── FAVORITOS ───────────────────────────────────────────────────────────────

@app.post("/agregar-favorito")
async def agregar_favorito(request: Request, producto_id: str = Form(...)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO favoritos (usuario_id, producto_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (user["id"], producto_id)
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()
    return RedirectResponse(url=f"/?selected_id={producto_id}", status_code=303)


@app.post("/quitar-favorito")
async def quitar_favorito(request: Request, producto_id: str = Form(...)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "DELETE FROM favoritos WHERE usuario_id = %s AND producto_id = %s",
            (user["id"], producto_id)
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()
    return RedirectResponse(url="/mis-favoritos", status_code=303)


@app.get("/mis-favoritos", response_class=HTMLResponse)
async def mis_favoritos(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT p.*,
               (SELECT hp.precio_visto FROM historial_precios hp
                WHERE hp.producto_id = p.id ORDER BY hp.fecha_muestreo DESC LIMIT 1) AS precio_actual,
               (SELECT MIN(hp.precio_visto) FROM historial_precios hp WHERE hp.producto_id = p.id) AS precio_min,
               (SELECT MAX(hp.precio_visto) FROM historial_precios hp WHERE hp.producto_id = p.id) AS precio_max
        FROM productos p
        INNER JOIN favoritos f ON f.producto_id = p.id
        WHERE f.usuario_id = %s
        ORDER BY f.fecha_agregado DESC
    """, (user["id"],))
    favoritos = to_list(cur.fetchall())
    cur.close()
    conn.close()

    return templates.TemplateResponse("favoritos.html", {
        "request":   request,
        "user":      user,
        "favoritos": favoritos,
    })

# ─── PANEL ADMINISTRADOR ─────────────────────────────────────────────────────

def _admin_guard(request: Request):
    """Retorna el usuario admin o None."""
    user = get_current_user(request)
    return user if (user and user["es_admin"]) else None


@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request, prod_error: str = None, prod_success: str = None):
    user = _admin_guard(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT id, email, es_admin, fecha_registro FROM usuarios ORDER BY id DESC")
    usuarios = to_list(cur.fetchall())

    cur.execute("""
        SELECT p.*,
               (SELECT COUNT(*) FROM favoritos f WHERE f.producto_id = p.id) AS total_seguidores
        FROM productos p
        ORDER BY p.nombre_producto
    """)
    productos = to_list(cur.fetchall())

    cur.execute("SELECT COUNT(*) AS total FROM favoritos")
    total_favoritos = to_dict(cur.fetchone())["total"]

    cur.execute("SELECT COUNT(*) AS total FROM historial_precios")
    total_registros = to_dict(cur.fetchone())["total"]

    cur.close()
    conn.close()

    return templates.TemplateResponse("admin.html", {
        "request":        request,
        "user":           user,
        "usuarios":       usuarios,
        "productos":      productos,
        "total_favoritos": total_favoritos,
        "total_registros": total_registros,
        "prod_error":     prod_error,
        "prod_success":   prod_success,
    })


@app.post("/admin/agregar-producto")
async def admin_agregar_producto(
    request: Request,
    nombre_producto: str   = Form(...),
    tienda_origen: str     = Form(...),
    precio_objetivo: float = Form(...),
    url_original: str      = Form(...),
    imagen_thumbnail: str  = Form(""),
):
    if not _admin_guard(request):
        return RedirectResponse(url="/", status_code=303)

    producto_id = str(uuid.uuid4())
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """INSERT INTO productos (id, nombre_producto, url_original, precio_objetivo, tienda_origen, imagen_thumbnail)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (producto_id, nombre_producto, url_original, precio_objetivo,
             tienda_origen, imagen_thumbnail or None)
        )
        conn.commit()
        return RedirectResponse(url="/admin?prod_success=Producto+agregado+correctamente", status_code=303)
    except Exception as e:
        return RedirectResponse(url=f"/admin?prod_error=Error+al+agregar+producto", status_code=303)
    finally:
        cur.close()
        conn.close()


@app.post("/admin/eliminar-producto")
async def admin_eliminar_producto(request: Request, producto_id: str = Form(...)):
    if not _admin_guard(request):
        return RedirectResponse(url="/", status_code=303)

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM productos WHERE id = %s", (producto_id,))
        conn.commit()
    finally:
        cur.close()
        conn.close()
    return RedirectResponse(url="/admin", status_code=303)


@app.post("/admin/eliminar-usuario")
async def admin_eliminar_usuario(request: Request, usuario_id: int = Form(...)):
    user = _admin_guard(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    if usuario_id == user["id"]:
        return RedirectResponse(url="/admin", status_code=303)  # No eliminarse a sí mismo

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM usuarios WHERE id = %s AND es_admin = FALSE", (usuario_id,))
        conn.commit()
    finally:
        cur.close()
        conn.close()
    return RedirectResponse(url="/admin", status_code=303)


@app.post("/admin/toggle-admin")
async def admin_toggle_admin(request: Request, usuario_id: int = Form(...)):
    user = _admin_guard(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE usuarios SET es_admin = NOT es_admin WHERE id = %s AND id != %s",
            (usuario_id, user["id"])  # No puede quitarse a sí mismo el admin
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()
    return RedirectResponse(url="/admin", status_code=303)