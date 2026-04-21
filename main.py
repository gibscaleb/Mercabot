import os
import uuid
import random
import httpx
import psycopg2
import bcrypt
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# ─── STARTUP: CREAR ADMIN SI NO EXISTE ──────────────────────────────────────

@app.on_event("startup")
async def crear_admin():
    import time
    for intento in range(5):
        try:
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST", "db"),
                user=os.getenv("DB_USER", "admin"),
                password=os.getenv("DB_PASSWORD", "password123"),
                dbname=os.getenv("DB_NAME", "mercabot")
            )
            cur = conn.cursor()
            hash_admin = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode("utf-8")
            cur.execute("""
                INSERT INTO usuarios (email, password_hash, es_admin)
                VALUES ('admin@mercabot.com', %s, TRUE)
                ON CONFLICT (email) DO NOTHING
            """, (hash_admin,))
            conn.commit()
            cur.close()
            conn.close()
            print("Admin listo: admin@mercabot.com / admin123")
            return
        except Exception as e:
            print(f"Esperando DB... intento {intento+1}/5 ({e})")
            time.sleep(2)
    print("No se pudo crear el admin")

# ─── CONEXIÓN A BASE DE DATOS ────────────────────────────────────────────────

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        user=os.getenv("DB_USER", "admin"),
        password=os.getenv("DB_PASSWORD", "password123"),
        dbname=os.getenv("DB_NAME", "mercabot")
    )

def to_dict(row):
    return dict(row) if row else None

def to_list(rows):
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

def get_user_favorites(user_id) -> set:
    if not user_id:
        return set()
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT producto_id FROM favoritos WHERE usuario_id = %s", (user_id,))
        ids = {str(row[0]).strip() for row in cur.fetchall()}
        cur.close()
        conn.close()
        return ids
    except Exception:
        return set()

# ─── PROXY DE IMÁGENES ───────────────────────────────────────────────────────

@app.get("/img-proxy")
async def image_proxy(url: str):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.google.com/",
            "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
        }
        async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
            resp = await client.get(url, headers=headers)
        content_type = resp.headers.get("content-type", "image/jpeg")
        return Response(content=resp.content, media_type=content_type,
                        headers={"Cache-Control": "public, max-age=3600"})
    except Exception:
        svg = '<svg xmlns="http://www.w3.org/2000/svg" width="60" height="60"><rect width="60" height="60" fill="#1e2a35"/><text x="50%" y="55%" dominant-baseline="middle" text-anchor="middle" fill="#5a7a8a" font-size="24">?</text></svg>'
        return Response(content=svg.encode(), media_type="image/svg+xml")

# ─── SCRAPING REAL ───────────────────────────────────────────────────────────

async def scrape_price(url: str, tienda: str):
    import re
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "es-MX,es;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15, headers=headers) as client:
            resp = await client.get(url)
            html = resp.text

        tienda_lower = tienda.lower()

        if "amazon" in tienda_lower:
            patterns = [
                r'"priceAmount":(\d+\.?\d*)',
                r'<span class="a-price-whole">([\d,]+)',
                r'"price":\s*"?\$?([\d,]+\.?\d*)"?',
            ]
            for pattern in patterns:
                match = re.search(pattern, html)
                if match:
                    return float(match.group(1).replace(",", ""))

        elif "mercadolibre" in tienda_lower or "mercado libre" in tienda_lower:
            patterns = [
                r'"price":(\d+\.?\d*)',
                r'class="andes-money-amount__fraction"[^>]*>([\d,]+)',
                r'"amount":(\d+\.?\d*)',
            ]
            for pattern in patterns:
                match = re.search(pattern, html)
                if match:
                    val = float(match.group(1).replace(",", ""))
                    if val > 100:
                        return val
        return None
    except Exception:
        return None

# ─── LANDING PAGE ────────────────────────────────────────────────────────────

@app.get("/inicio", response_class=HTMLResponse)
async def landing(request: Request):
    user = get_current_user(request)
    return templates.TemplateResponse("landing.html", {"request": request, "user": user})

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
        cur.execute("INSERT INTO usuarios (email, password_hash) VALUES (%s, %s)", (email, hashed_pw))
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
    response = RedirectResponse(url="/inicio")
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

    favoritos_ids = get_user_favorites(user["id"] if user else None)

    return templates.TemplateResponse("index.html", {
        "request":          request,
        "productos":        productos,
        "chart_labels":     labels,
        "chart_data":       data,
        "producto_grafica": producto_grafica,
        "stats":            stats,
        "user":             user,
        "query":            q,
        "favoritos_ids":    favoritos_ids,
    })


async def generar_historial_30_dias(producto_id: str, precio_objetivo: float, conn):
    from datetime import datetime, timedelta

    cur = conn.cursor()
    ahora = datetime.now()

    precio_min_abs = precio_objetivo * 0.85
    precio_max_abs = precio_objetivo * 1.20
    precio_actual = precio_objetivo * random.uniform(0.95, 1.10)
    precio_actual = round(precio_actual, 2)

    registros = []

    for dia in range(30, -1, -1):
        fecha_base = ahora - timedelta(days=dia)
        horas = [random.randint(8, 10), random.randint(13, 15), random.randint(19, 22)]

        for hora in horas:
            fecha = fecha_base.replace(hour=hora, minute=random.randint(0, 59), second=0, microsecond=0)

            cambio = random.uniform(-0.015, 0.015)
            r = random.random()
            if r < 0.02:
                cambio = random.uniform(-0.13, -0.08)   # oferta flash
            elif r < 0.05:
                cambio = random.uniform(0.04, 0.08)     # subida
            elif r < 0.08:
                cambio = random.uniform(-0.06, -0.03)   # oferta leve

            precio_actual = precio_actual * (1 + cambio)
            precio_actual = max(precio_min_abs, min(precio_max_abs, precio_actual))
            precio_actual = round(precio_actual, 2)

            descuento = precio_actual < precio_objetivo
            registros.append((producto_id, precio_actual, fecha, descuento))

    cur.executemany(
        "INSERT INTO historial_precios (producto_id, precio_visto, fecha_muestreo, descuento_detectado) VALUES (%s, %s, %s, %s)",
        registros
    )
    conn.commit()
    cur.close()


@app.post("/buscar-precio")
async def buscar_precio(producto_id: str = Form(...)):
    conn = get_db_connection()
    cur = conn.cursor()  # cursor normal, no RealDict

    # Obtener datos del producto
    cur.execute("SELECT url_original, tienda_origen, precio_objetivo FROM productos WHERE id = %s", (producto_id,))
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        return RedirectResponse(url="/", status_code=303)

    url_original, tienda_origen, precio_objetivo = row[0], row[1], float(row[2])

    # Contar registros existentes
    cur.execute("SELECT COUNT(*) FROM historial_precios WHERE producto_id = %s", (producto_id,))
    count = cur.fetchone()[0]

    if count == 0:
        # Primera vez: generar 30 días de historial realista
        cur.close()
        await generar_historial_30_dias(producto_id, precio_objetivo, conn)
        conn.close()
        return RedirectResponse(url=f"/?selected_id={producto_id}", status_code=303)

    # Siguientes actualizaciones: pequeña fluctuación sobre el último precio
    cur.execute(
        "SELECT precio_visto FROM historial_precios WHERE producto_id = %s ORDER BY fecha_muestreo DESC LIMIT 1",
        (producto_id,)
    )
    ultimo = cur.fetchone()
    precio_base = float(ultimo[0]) if ultimo else precio_objetivo

    # Fluctuación realista ±2%, raro ±6%
    cambio = random.uniform(-0.02, 0.02)
    if random.random() < 0.08:
        cambio = random.uniform(-0.06, 0.06)

    nuevo_precio = round(precio_base * (1 + cambio), 2)
    # Siempre dentro del 85%-120% del objetivo
    nuevo_precio = max(precio_objetivo * 0.85, min(precio_objetivo * 1.20, nuevo_precio))

    descuento = nuevo_precio < precio_objetivo
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
    cur.execute(
        "SELECT 1 FROM favoritos WHERE usuario_id = %s AND producto_id = %s",
        (user["id"], producto_id)
    )
    existe = cur.fetchone()
    if existe:
        cur.execute(
            "DELETE FROM favoritos WHERE usuario_id = %s AND producto_id = %s",
            (user["id"], producto_id)
        )
    else:
        cur.execute(
            "INSERT INTO favoritos (usuario_id, producto_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (user["id"], producto_id)
        )
    conn.commit()
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
    cur.execute("DELETE FROM favoritos WHERE usuario_id = %s AND producto_id = %s", (user["id"], producto_id))
    conn.commit()
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
        "request": request, "user": user, "favoritos": favoritos,
    })

# ─── PANEL ADMINISTRADOR ─────────────────────────────────────────────────────

def _admin_guard(request: Request):
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
        SELECT p.*, (SELECT COUNT(*) FROM favoritos f WHERE f.producto_id = p.id) AS total_seguidores
        FROM productos p ORDER BY p.nombre_producto
    """)
    productos = to_list(cur.fetchall())
    cur.execute("SELECT COUNT(*) AS total FROM favoritos")
    total_favoritos = to_dict(cur.fetchone())["total"]
    cur.execute("SELECT COUNT(*) AS total FROM historial_precios")
    total_registros = to_dict(cur.fetchone())["total"]
    cur.close()
    conn.close()
    return templates.TemplateResponse("admin.html", {
        "request": request, "user": user, "usuarios": usuarios,
        "productos": productos, "total_favoritos": total_favoritos,
        "total_registros": total_registros, "prod_error": prod_error, "prod_success": prod_success,
    })


@app.post("/admin/agregar-producto")
async def admin_agregar_producto(
    request: Request,
    nombre_producto: str = Form(...), tienda_origen: str = Form(...),
    precio_objetivo: float = Form(...), url_original: str = Form(...),
    imagen_thumbnail: str = Form(""),
):
    if not _admin_guard(request):
        return RedirectResponse(url="/", status_code=303)
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO productos (id, nombre_producto, url_original, precio_objetivo, tienda_origen, imagen_thumbnail) VALUES (%s,%s,%s,%s,%s,%s)",
            (str(uuid.uuid4()), nombre_producto, url_original, precio_objetivo, tienda_origen, imagen_thumbnail or None)
        )
        conn.commit()
        return RedirectResponse(url="/admin?prod_success=Producto+agregado+correctamente", status_code=303)
    except Exception:
        return RedirectResponse(url="/admin?prod_error=Error+al+agregar+producto", status_code=303)
    finally:
        cur.close()
        conn.close()


@app.post("/admin/eliminar-producto")
async def admin_eliminar_producto(request: Request, producto_id: str = Form(...)):
    if not _admin_guard(request):
        return RedirectResponse(url="/", status_code=303)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM productos WHERE id = %s", (producto_id,))
    conn.commit()
    cur.close()
    conn.close()
    return RedirectResponse(url="/admin", status_code=303)


@app.post("/admin/eliminar-usuario")
async def admin_eliminar_usuario(request: Request, usuario_id: int = Form(...)):
    user = _admin_guard(request)
    if not user or usuario_id == user["id"]:
        return RedirectResponse(url="/admin", status_code=303)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM usuarios WHERE id = %s AND es_admin = FALSE", (usuario_id,))
    conn.commit()
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
    cur.execute(
        "UPDATE usuarios SET es_admin = NOT es_admin WHERE id = %s AND id != %s",
        (usuario_id, user["id"])
    )
    conn.commit()
    cur.close()
    conn.close()
    return RedirectResponse(url="/admin", status_code=303)