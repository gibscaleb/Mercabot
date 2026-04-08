-- 1. Tabla de Usuarios (Debe ir primero para que favoritos la pueda referenciar)
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    es_admin BOOLEAN DEFAULT FALSE,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tabla de Productos
CREATE TABLE IF NOT EXISTS productos (
    id CHAR(36) PRIMARY KEY,
    nombre_producto VARCHAR(255) NOT NULL,
    url_original TEXT NOT NULL,
    precio_objetivo DECIMAL(12, 2) NOT NULL,
    tienda_origen VARCHAR(50),
    imagen_thumbnail TEXT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Tabla de Historial
CREATE TABLE IF NOT EXISTS historial_precios (
    id SERIAL PRIMARY KEY,
    producto_id CHAR(36) REFERENCES productos(id) ON DELETE CASCADE,
    precio_visto DECIMAL(12, 2) NOT NULL,
    fecha_muestreo TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    descuento_detectado BOOLEAN DEFAULT FALSE
);

-- 4. Tabla de Favoritos (Relaciona usuarios con productos)
CREATE TABLE IF NOT EXISTS favoritos (
    usuario_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
    producto_id CHAR(36) REFERENCES productos(id) ON DELETE CASCADE,
    fecha_agregado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (usuario_id, producto_id)
);

-- 5. Inserción de Productos
INSERT INTO productos (id, nombre_producto, url_original, precio_objetivo, tienda_origen, imagen_thumbnail) VALUES 
('xb01-xb01-xb01-xb01-xb01xb01xb01', 'Microsoft Xbox Series X 1TB - Negro', 'https://amazon.mx/xbox-x', 11000.00, 'Amazon MX', 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f6/Xbox_Series_X_Console.png/320px-Xbox_Series_X_Console.png'),
('xb02-xb02-xb02-xb02-xb02xb02xb02', 'Microsoft Xbox Series S 512GB - Blanco', 'https://amazon.mx/xbox-s', 5500.00, 'Amazon MX', 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/15/Xbox_Series_S.png/320px-Xbox_Series_S.png'),
('xb03-xb03-xb03-xb03-xb03xb03xb03', 'Microsoft Xbox Series S 1TB - Carbón (Black)', 'https://amazon.mx/xbox-s-black', 7200.00, 'MercadoLibre', 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/15/Xbox_Series_S.png/320px-Xbox_Series_S.png'),
('ps01-ps01-ps01-ps01-ps01ps01ps01', 'Sony PlayStation 5 Slim (Edición Estándar)', 'https://amazon.mx/ps5-slim', 9200.00, 'Amazon MX', 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/PlayStation_5_Digital_Edition_with_DualSense.jpg/320px-PlayStation_5_Digital_Edition_with_DualSense.jpg'),
('ps02-ps02-ps02-ps02-ps02ps02ps02', 'Sony PlayStation 5 Slim (Edición Digital)', 'https://amazon.mx/ps5-digital', 8000.00, 'Amazon MX', 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/PlayStation_5_Digital_Edition_with_DualSense.jpg/320px-PlayStation_5_Digital_Edition_with_DualSense.jpg'),
('ps03-ps03-ps03-ps03-ps03ps03ps03', 'Sony PlayStation 5 Pro (Preventa)', 'https://amazon.mx/ps5-pro', 14500.00, 'MercadoLibre', 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/PlayStation_5_Digital_Edition_with_DualSense.jpg/320px-PlayStation_5_Digital_Edition_with_DualSense.jpg'),
('sw01-sw01-sw01-sw01-sw01sw01sw01', 'Nintendo Switch Modelo OLED - Blanco', 'https://amazon.mx/switch-oled', 6500.00, 'Amazon MX', 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Nintendo_Switch_OLED_model.png/320px-Nintendo_Switch_OLED_model.png'),
('sw02-sw02-sw02-sw02-sw02sw02sw02', 'Nintendo Switch V2 Neon - Rojo/Azul', 'https://amazon.mx/switch-neon', 5200.00, 'MercadoLibre', 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/88/Nintendo-Switch-wJoyCons-BlRd-Standing-Frt.png/320px-Nintendo-Switch-wJoyCons-BlRd-Standing-Frt.png'),
('sw03-sw03-sw03-sw03-sw03sw03sw03', 'Nintendo Switch Lite - Turquesa', 'https://amazon.mx/switch-lite', 3500.00, 'Amazon MX', 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/Nintendo_Switch_Lite_representation.png/320px-Nintendo_Switch_Lite_representation.png');

-- 6. Inserción del Administrador Inicial (Password: admin123)
INSERT INTO usuarios (email, password_hash, es_admin) 
VALUES ('admin@mercabot.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjIQqiRQYm', TRUE)
ON CONFLICT (email) DO NOTHING;