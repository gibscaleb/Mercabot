-- 1. Tabla de Usuarios 
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

-- 4. Tabla de Favoritos
CREATE TABLE IF NOT EXISTS favoritos (
    usuario_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
    producto_id CHAR(36) REFERENCES productos(id) ON DELETE CASCADE,
    fecha_agregado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (usuario_id, producto_id)
);

-- 5. Productos con URLs reales y correctas
INSERT INTO productos (id, nombre_producto, url_original, precio_objetivo, tienda_origen, imagen_thumbnail) VALUES 
(
    'xb01-xb01-xb01-xb01-xb01xb01xb01',
    'Microsoft Xbox Series X 1TB - Negro',
    'https://www.amazon.com.mx/Consola-Xbox-X-1-TB/dp/B08H75RTZ8/ref=sr_1_3?__mk_es_MX=%C3%85M%C3%85%C5%BD%C3%95%C3%91&crid=15SOJ1DFEXO7J&dib=eyJ2IjoiMSJ9.X2VGsTLMvDzydcODcT25nrH74Dnwl7565cNx3n9P_g3u_70dGgSue9Hcgj3ZeUnay3QcKBpTN0C2vOLaKyjl60U0qSHyPR2cvQFl3ioXrkc.2J37VUtN_4MXlJvra_0pweiMhrg2pGv0xIPmFV2hFJA&dib_tag=se&keywords=xbox+series+x+1t&qid=1776756668&s=videogames&sprefix=xbxo+series+x+1t%2Cvideogames%2C151&sr=1-3',
    11000.00,
    'Amazon MX',
    'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f6/Xbox_Series_X_Console.png/320px-Xbox_Series_X_Console.png'
),
(
    'xb02-xb02-xb02-xb02-xb02xb02xb02',
    'Microsoft Xbox Series S 512GB - Blanco',
    'https://www.amazon.com.mx/Microsoft-NewXbox-All-Digital-Controlador-inal%C3%A1mbrico/dp/B09N7JBPWD/ref=sr_1_6?__mk_es_MX=%C3%85M%C3%85%C5%BD%C3%95%C3%91&crid=518EAUL0FR4E&dib=eyJ2IjoiMSJ9.SV5wObg6lbyhBfjj6vVSPPyzcARGia9gjHXxPgcI6aOlc057gefltcmm1gDiFb_ZHif8D3sVGSURdZJB-1R7XoY6XqfX7HbxCoFa0NNwztei-GfPZHoYhJnXYssjgmnS9zQP2XXNsUubxroJ79X_UtwKtLteKY9WUcwTpMaOf9JzbMWJ4r7s3nvdlLA5MpriuRLKwidQ8hjySAA59HY1U0GYYGCcK9orDe7UumAc5N0.JEYH9giArPiUDR-TtNFSvnz_wnJlQlG60FbAWBcgYVI&dib_tag=se&keywords=Microsoft+Xbox+Series+S+512GB+-+Blanco&qid=1776756732&s=videogames&sprefix=microsoft+xbox+series+s+512gb+-+blanco%2Cvideogames%2C139&sr=1-6&ufe=app_do%3Aamzn1.fos.de93fa6a-174c-4df7-be7c-5bc8e9c5a71b',
    5500.00,
    'Amazon MX',
    'https://upload.wikimedia.org/wikipedia/commons/thumb/1/15/Xbox_Series_S.png/320px-Xbox_Series_S.png'
),
(
    'xb03-xb03-xb03-xb03-xb03xb03xb03',
    'Microsoft Xbox Series S 1TB - Carbón (Black)',
    'https://www.mercadolibre.com.mx/consola-xbox-series-s-carbon-black-all-digital-1tb-ssd-negro/p/MLM26036405#polycard_client=search-desktop&search_layout=grid&position=4&type=product&tracking_id=8eaad108-543c-48a5-a79d-ebc77833fc14&wid=MLM2141103875&sid=search',
    7200.00,
    'MercadoLibre',
    'https://upload.wikimedia.org/wikipedia/commons/thumb/1/15/Xbox_Series_S.png/320px-Xbox_Series_S.png'
),
(
    'ps01-ps01-ps01-ps01-ps01ps01ps01',
    'Sony PlayStation 5 Slim (Edición Estándar)',
    'https://www.amazon.com.mx/dp/B0CL5KNB9M',
    9200.00,
    'Amazon MX',
    'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/PlayStation_5_Digital_Edition_with_DualSense.jpg/320px-PlayStation_5_Digital_Edition_with_DualSense.jpg'
),
(
    'ps02-ps02-ps02-ps02-ps02ps02ps02',
    'Sony PlayStation 5 Slim (Edición Digital)',
    'https://www.amazon.com.mx/PlayStation%C2%AE5-Modelo-Slim-Juegos-Digital/dp/B0CTD14KQ6/ref=sr_1_3?__mk_es_MX=%C3%85M%C3%85%C5%BD%C3%95%C3%91&crid=2RY2MJZ4IQ99X&dib=eyJ2IjoiMSJ9.TI4SvKokQryqnkCaKU4ao0VBdLDhqdYR2W5VRPDwsmJO6cye5wwtacgdEP9SHMVZ76EJw21teLX8ZyYG515begyv9KVV4lZS2Cl5ih5Q0pB8PyyP6jIRnbS_vm0jCmUb00R_x_nEcdR3SOOIv9dwLGSJ2ETeMzz8J2bB4gMXUj3ee-wbxwIIfOLVSV3F1tC185AS5FVg06tWBeHHlIrkAkxmNt3bUt8YXlCqmhS0IYI.4nWv49eJVlN7F-5HZYTJFC2fOZ8NU49PMkjHUlrHCSs&dib_tag=se&keywords=ps+5+slim+digital&qid=1776757128&s=videogames&sprefix=ps+5+slim+digital%2Cvideogames%2C139&sr=1-3',
    8000.00,
    'Amazon MX',
    'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/PlayStation_5_Digital_Edition_with_DualSense.jpg/320px-PlayStation_5_Digital_Edition_with_DualSense.jpg'
),
(
    'ps03-ps03-ps03-ps03-ps03ps03ps03',
    'Sony PlayStation 5 Pro',
    'https://www.mercadolibre.com.mx/consola-sony-playstation-5-pro-digital-2-tb-blanco/p/MLM41975964#polycard_client=search-desktop&search_layout=grid&position=1&type=product&tracking_id=be9090f9-26d8-49e6-b2cc-c9bf7c46fd56&wid=MLM2180848723&sid=search',
    14500.00,
    'MercadoLibre',
    'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/PlayStation_5_Digital_Edition_with_DualSense.jpg/320px-PlayStation_5_Digital_Edition_with_DualSense.jpg'
),
(
    'sw01-sw01-sw01-sw01-sw01sw01sw01',
    'Nintendo Switch Modelo OLED - Blanco',
    'https://www.amazon.com.mx/Nintendo-Console-Touchscreen-Display-Bluetooth/dp/B09Q3QTN1F/ref=sr_1_3?__mk_es_MX=%C3%85M%C3%85%C5%BD%C3%95%C3%91&crid=3K526I2E8RAJX&dib=eyJ2IjoiMSJ9.4rKfjfE6_vQZZR1nIxN6O5TLuOVosejTiOsGAeqqZ1xSd3dqKeadZclIBK4i5Y3CypXtQMMOHE4RAkQnbg_L-uCOrzkjqN7EN6_10tA40e3pVcvcPT2Bt-ue2uocSddGt_UbY6w7X_svQj-3WTrDvGAQUvpZuJlGLzJdoYbOSiK-8HjNxE-UngEUY5nTurclJED51iHrCP4TO3OTEXOs6mQ2LsOOCaOWYYpHCGARCpk.55FPpjT8X19V_TUnDzrOzqhU2Vw5IBES2QyTWpXimvc&dib_tag=se&keywords=Nintendo+Switch+Modelo+OLED+-+Blanc&qid=1776757472&s=videogames&sprefix=%2Cvideogames%2C168&sr=1-3',
    6500.00,
    'Amazon MX',
    'https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Nintendo_Switch_OLED_model.png/320px-Nintendo_Switch_OLED_model.png'
),
(
    'sw02-sw02-sw02-sw02-sw02sw02sw02',
    'Nintendo Switch V2 Neon - Rojo/Azul',
    'https://www.mercadolibre.com.mx/nintendo-switch-neon-blue-and-neon-red-joycon-color-rojo/p/MLM24529032#polycard_client=search-desktop&search_layout=grid&position=1&type=product&tracking_id=3d2ccdf5-f3d9-4856-b4ba-1bb227bab6bc&wid=MLM2831746113&sid=search',
    5200.00,
    'MercadoLibre',
    'https://upload.wikimedia.org/wikipedia/commons/thumb/8/88/Nintendo-Switch-wJoyCons-BlRd-Standing-Frt.png/320px-Nintendo-Switch-wJoyCons-BlRd-Standing-Frt.png'
),
(
    'sw03-sw03-sw03-sw03-sw03sw03sw03',
    'Nintendo Switch Lite - Turquesa',
    'https://www.amazon.com.mx/Nintendo-Switch-Turquesa-Edici%C3%B3n-Est%C3%A1ndar/dp/B07V4GCFP9/ref=sr_1_3?__mk_es_MX=%C3%85M%C3%85%C5%BD%C3%95%C3%91&crid=TIIT6TIUA0UP&dib=eyJ2IjoiMSJ9.1QUzpvlXnMwexZy5fAX8uMeSFcEo5fE6arMQ8IVPso8M7-jD7LQfpHeXl8EThIW3d4zxL6gzp1HRKuiG7KLSFbp4Zmo2_Ltf-o4RvKNS2ui0-ppZVkVF53YO-1DIO10Rjkm3B6Iyo5sVQjlrEcbA5Ul946Ii-5n1BFmDyAtpad2Rs1Lqu735OQg5edIANLRFNSYfD5kDr1Ac8QOS9SHXnb6NNDkC1jzgfsUZpT1skcI.AS8viPsSUFzWKdIg7TCjnb9_cQ_qOZdd5pSd7X5yI1Q&dib_tag=se&keywords=Nintendo%2BSwitch%2BLite%2B-%2BTurquesa&qid=1776757571&s=videogames&sprefix=%2Cvideogames%2C154&sr=1-3&ufe=app_do%3Aamzn1.fos.44a97073-60b7-4563-a75a-8c47678c9132&th=1',
    3500.00,
    'Amazon MX',
    'https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/Nintendo_Switch_Lite_representation.png/320px-Nintendo_Switch_Lite_representation.png'
)
ON CONFLICT (id) DO NOTHING;