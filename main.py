from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import mysql.connector
from datetime import datetime
import random

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# conexion a base de datos
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="mercabot"
    )

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, q: str = None, selected_id: str = None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True) 
    
    # Búsqueda de Productos
    if q:
        # busqueda por palabras clave
        query = "SELECT * FROM productos WHERE nombre_producto LIKE %s"
        cursor.execute(query, (f"%{q}%",))
    else:
        cursor.execute("SELECT * FROM productos")
    
    productos = cursor.fetchall()
    
    #obtener historial para la gráfica
    labels = []
    data = []
    producto_grafica = None

    if productos:
        producto_grafica = productos[0]
        pid = producto_grafica['id']
        
        # historial ordenado por fecha
        cursor.execute("SELECT precio_visto, fecha_muestreo FROM historial_precios WHERE producto_id = %s ORDER BY fecha_muestreo ASC", (pid,))
        history = cursor.fetchall()
        
        labels = [h['fecha_muestreo'].strftime("%Y-%m-%d %H:%M") for h in history]
        data = [float(h['precio_visto']) for h in history]

    cursor.close()
    conn.close()
    
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "productos": productos,
        "chart_labels": labels,
        "chart_data": data,
        "query": q, 
        "producto_grafica": producto_grafica
    })

# simulador del bot(scrapper)
@app.post("/buscar-precio")
async def buscar_precio(producto_id: str = Form(...)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    precio_simulado = round(random.uniform(3000.00, 15000.00), 2)
    
    es_descuento = 1 if precio_simulado < 8000 else 0 
    
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
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)