from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import random
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --- CONEXIÓN A POSTGRESQL (DOCKER) ---
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "db"), # "db" es el nombre del contenedor en tu docker-compose
        user=os.getenv("DB_USER", "admin"),
        password=os.getenv("DB_PASSWORD", "password123"),
        dbname=os.getenv("DB_NAME", "mercabot")
    )

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, q: str = None, selected_id: str = None):
    conn = get_db_connection()
    # Usamos RealDictCursor para que Postgres devuelva diccionarios como lo hacía MySQL
    cursor = conn.cursor(cursor_factory=RealDictCursor) 
    
    # Búsqueda de Productos
    if q:
        # En Postgres, ILIKE se usa para buscar ignorando mayúsculas/minúsculas
        query = "SELECT * FROM productos WHERE nombre_producto ILIKE %s"
        cursor.execute(query, (f"%{q}%",))
    else:
        cursor.execute("SELECT * FROM productos")
    
    productos = cursor.fetchall()
    
    # Obtener historial para la gráfica
    labels = []
    data = []
    producto_grafica = None

    if productos and selected_id:
        producto_grafica = next((p for p in productos if str(p['id']) == selected_id), None)
        
        if producto_grafica:
            pid = producto_grafica['id']
            # Historial ordenado por fecha
            cursor.execute("SELECT precio_visto, fecha_muestreo FROM historial_precios WHERE producto_id = %s ORDER BY fecha_muestreo ASC", (pid,))
            history = cursor.fetchall()
            
            labels = [h['fecha_muestreo'].strftime("%Y-%m-%d %H:%M") for h in history]
            data = [float(h['precio_visto']) for h in history]

    cursor.close()
    conn.close()
    
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request, 
            "productos": productos,
            "chart_labels": labels,
            "chart_data": data,
            "query": q, 
            "producto_grafica": producto_grafica
        }
    )

# Simulador del bot (scraper)
@app.post("/buscar-precio")
async def buscar_precio(producto_id: str = Form(...)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    precio_simulado = round(random.uniform(3000.00, 15000.00), 2)
    
    # En Postgres los booleanos se manejan con True/False
    es_descuento = True if precio_simulado < 8000 else False 
    
    cursor.execute(
        "INSERT INTO historial_precios (producto_id, precio_visto, fecha_muestreo, descuento_detectado) VALUES (%s, %s, NOW(), %s)",
        (producto_id, precio_simulado, es_descuento)
    )
    conn.commit()
    cursor.close()
    conn.close()
    
    return RedirectResponse(url=f"/?selected_id={producto_id}", status_code=303)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)