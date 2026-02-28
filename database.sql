
-- 1. REINICIO TOTAL DE LA BASE DE DATOS
SET FOREIGN_KEY_CHECKS = 0; 
DROP TABLE IF EXISTS historial_precios;
DROP TABLE IF EXISTS productos;
SET FOREIGN_KEY_CHECKS = 1;

-- 2. CREACIÓN DE TABLAS

-- Tabla de Productos 
CREATE TABLE productos (
    id CHAR(36) PRIMARY KEY,
    nombre_producto VARCHAR(255) NOT NULL,
    url_original TEXT NOT NULL,
    precio_objetivo DECIMAL(12, 2) NOT NULL,
    tienda_origen VARCHAR(50),
    imagen_thumbnail TEXT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Historial
CREATE TABLE historial_precios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    producto_id CHAR(36),
    precio_visto DECIMAL(12, 2) NOT NULL,
    fecha_muestreo TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    descuento_detectado TINYINT(1) DEFAULT 0,
    FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE
);

-- productos (MOCKUP)

INSERT INTO productos (id, nombre_producto, url_original, precio_objetivo, tienda_origen, imagen_thumbnail) VALUES 
('xb01-xb01-xb01-xb01-xb01xb01xb01', 'Microsoft Xbox Series X 1TB - Negro', 'https://amazon.mx/xbox-x', 11000.00, 'Amazon MX', 'https://m.media-amazon.com/images/I/61-jjE67uqL._AC_SX679_.jpg'),
('xb02-xb02-xb02-xb02-xb02xb02xb02', 'Microsoft Xbox Series S 512GB - Blanco', 'https://amazon.mx/xbox-s', 5500.00, 'Amazon MX', 'https://m.media-amazon.com/images/I/71NBQ2a52CL._AC_SX679_.jpg'),
('xb03-xb03-xb03-xb03-xb03xb03xb03', 'Microsoft Xbox Series S 1TB - Carbón (Black)', 'https://amazon.mx/xbox-s-black', 7200.00, 'MercadoLibre', 'https://m.media-amazon.com/images/I/61jC5z8-1HL._AC_SL1500_.jpg');

INSERT INTO productos (id, nombre_producto, url_original, precio_objetivo, tienda_origen, imagen_thumbnail) VALUES 
('ps01-ps01-ps01-ps01-ps01ps01ps01', 'Sony PlayStation 5 Slim (Edición Estándar con Disco)', 'https://amazon.mx/ps5-slim', 9200.00, 'Amazon MX', 'https://m.media-amazon.com/images/I/51051FiD9UL._SX522_.jpg'),
('ps02-ps02-ps02-ps02-ps02ps02ps02', 'Sony PlayStation 5 Slim (Edición Digital)', 'https://amazon.mx/ps5-digital', 8000.00, 'Amazon MX', 'https://m.media-amazon.com/images/I/51d1lfcMiIL._SX522_.jpg'),
('ps03-ps03-ps03-ps03-ps03ps03ps03', 'Sony PlayStation 5 Pro (Preventa)', 'https://amazon.mx/ps5-pro', 14500.00, 'MercadoLibre', 'https://m.media-amazon.com/images/I/31M35WdoUHL._SY445_SX342_QL70_FMwebp_.jpg');

INSERT INTO productos (id, nombre_producto, url_original, precio_objetivo, tienda_origen, imagen_thumbnail) VALUES 
('sw01-sw01-sw01-sw01-sw01sw01sw01', 'Nintendo Switch Modelo OLED - Blanco', 'https://amazon.mx/switch-oled', 6500.00, 'Amazon MX', 'https://m.media-amazon.com/images/I/71O15lM1TlL._AC_SX679_.jpg'),
('sw02-sw02-sw02-sw02-sw02sw02sw02', 'Nintendo Switch V2 Neon - Rojo/Azul', 'https://amazon.mx/switch-neon', 5200.00, 'MercadoLibre', 'https://m.media-amazon.com/images/I/61-PblYntsL._AC_SL1500_.jpg'),
('sw03-sw03-sw03-sw03-sw03sw03sw03', 'Nintendo Switch Lite - Turquesa', 'https://amazon.mx/switch-lite', 3500.00, 'Amazon MX', 'https://m.media-amazon.com/images/I/61I42o5aZpL._AC_SL1500_.jpg');


-- 4. historial de precios inicial

INSERT INTO historial_precios (producto_id, precio_visto, fecha_muestreo, descuento_detectado) VALUES

('xb01-xb01-xb01-xb01-xb01xb01xb01', 13999.00, NOW() - INTERVAL 5 DAY, 0),
('xb01-xb01-xb01-xb01-xb01xb01xb01', 12500.00, NOW() - INTERVAL 3 DAY, 0),
('xb01-xb01-xb01-xb01-xb01xb01xb01', 11200.00, NOW() - INTERVAL 1 DAY, 0),

('xb02-xb02-xb02-xb02-xb02xb02xb02', 6200.00, NOW() - INTERVAL 4 DAY, 0),
('xb02-xb02-xb02-xb02-xb02xb02xb02', 5900.00, NOW() - INTERVAL 2 DAY, 0),
('xb02-xb02-xb02-xb02-xb02xb02xb02', 5400.00, NOW() - INTERVAL 12 HOUR, 1), 

('ps01-ps01-ps01-ps01-ps01ps01ps01', 9000.00, NOW() - INTERVAL 6 DAY, 1),
('ps01-ps01-ps01-ps01-ps01ps01ps01', 9500.00, NOW() - INTERVAL 2 DAY, 0),
('ps01-ps01-ps01-ps01-ps01ps01ps01', 9800.00, NOW() - INTERVAL 1 HOUR, 0),

('sw01-sw01-sw01-sw01-sw01sw01sw01', 7500.00, NOW() - INTERVAL 3 DAY, 0),
('sw01-sw01-sw01-sw01-sw01sw01sw01', 6400.00, NOW() - INTERVAL 1 DAY, 1);