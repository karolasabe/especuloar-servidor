from flask import Flask, request, jsonify
import json
import os
import sqlite3
import numpy as np
from datetime import datetime

app = Flask(__name__)
from flask_cors import CORS
CORS(app)

DB_PATH = 'corpus.db'
UMBRAL = 10  # genera nueva imagen cada 10 respuestas nuevas

# --- Base de datos ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS respuestas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        edad TEXT,
        sistema_salud TEXT,
        imagen_mental TEXT,
        deseo TEXT,
        embedding TEXT,
        cluster TEXT,
        sintetico INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS imagenes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        n_respuestas INTEGER,
        prompt TEXT,
        cluster_dominante TEXT,
        url_imagen TEXT
    )''')
    conn.commit()
    conn.close()

def guardar_respuesta(datos, embedding, cluster):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT INTO respuestas 
        (timestamp, edad, sistema_salud, imagen_mental, deseo, embedding, cluster, sintetico)
        VALUES (?,?,?,?,?,?,?,?)''',
        (datetime.now().isoformat(),
         datos.get('edad', ''),
         datos.get('sistema_salud', ''),
         datos.get('imagen_mental', ''),
         datos.get('deseo', ''),
         json.dumps(embedding),
         cluster,
         datos.get('sintetico', 0)))
    conn.commit()
    n = c.execute('SELECT COUNT(*) FROM respuestas').fetchone()[0]
    conn.close()
    return n

def contar_respuestas():
    conn = sqlite3.connect(DB_PATH)
    n = conn.execute('SELECT COUNT(*) FROM respuestas').fetchone()[0]
    conn.close()
    return n

# --- Embeddings simplificados ---
DIMENSIONES = {
    'frio_metal': ['frío','helado','metal','acero','gris','plateado','oscuro'],
    'calor_deseo': ['tibio','cálido','suave','blando','silicona','rosa','morado','flor'],
    'cuerpo_dolor': ['dolor','cuerpo','músculo','contracción','sangre','herida','presión'],
    'invasion': ['invasión','abrir','forzar','entrar','romper','vulnerar','exponer'],
    'morgue_muerte': ['morgue','muerte','fría','blanca','silencio','quietud','instrumental'],
    'intimidad': ['íntimo','privado','segura','confianza','cuidado','gentil','suave'],
    'mecanico': ['metal','tornillo','herramienta','máquina','clic','chirrido','abrelatas'],
    'organico': ['carne','piel','tejido','músculo','fluido','vivo','orgánico']
}

def calcular_embedding(texto):
    texto_lower = texto.lower()
    vector = []
    for dim, palabras in DIMENSIONES.items():
        score = sum(1 for p in palabras if p in texto_lower)
        vector.append(score)
    total = sum(vector) or 1
    return [v/total for v in vector]

def calcular_cluster(embedding):
    dims = list(DIMENSIONES.keys())
    return dims[np.argmax(embedding)]

def generar_prompt_sintetico():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute('SELECT imagen_mental, deseo, cluster FROM respuestas').fetchall()
    conn.close()
    
    clusters = {}
    for imagen, deseo, cluster in rows:
        if cluster not in clusters:
            clusters[cluster] = {'imagenes': [], 'deseos': []}
        if imagen:
            clusters[cluster]['imagenes'].append(imagen[:100])
        if deseo:
            clusters[cluster]['deseos'].append(deseo[:100])
    
    dominante = max(clusters, key=lambda k: len(clusters[k]['imagenes'])) if clusters else 'frio_metal'
    
    imagenes_sample = clusters.get(dominante, {}).get('imagenes', [])[:5]
    deseos_sample = []
    for c in clusters.values():
        deseos_sample.extend(c.get('deseos', [])[:2])
    
    prompt = f"""A gynecological speculum reimagined through {contar_respuestas()} women's mental images. 
Dominant vision: {dominante.replace('_',' ')}. 
Collective imagination: {', '.join(imagenes_sample[:3])}. 
Collective desire: {', '.join(deseos_sample[:3])}. 
Hyperrealistic surreal sculpture, studio photography, cinematic light, 8k, no text."""
    
    return prompt, dominante

# --- Rutas ---
@app.route('/webhook', methods=['POST'])
def webhook():
    datos = request.json or {}
    
    texto = datos.get('imagen_mental', '') + ' ' + datos.get('deseo', '')
    embedding = calcular_embedding(texto)
    cluster = calcular_cluster(embedding)
    
    n_total = guardar_respuesta(datos, embedding, cluster)
    
    respuesta = {
        'status': 'ok',
        'id': n_total,
        'cluster': cluster,
        'total_respuestas': n_total
    }
    
    if n_total % UMBRAL == 0:
        prompt, cluster_dom = generar_prompt_sintetico()
        respuesta['nueva_imagen'] = True
        respuesta['prompt'] = prompt
        respuesta['cluster_dominante'] = cluster_dom
        print(f"UMBRAL ALCANZADO — {n_total} respuestas — prompt generado")
    
    return jsonify(respuesta)

@app.route('/estado', methods=['GET'])
def estado():
    conn = sqlite3.connect(DB_PATH)
    n = conn.execute('SELECT COUNT(*) FROM respuestas').fetchone()[0]
    clusters = conn.execute(
        'SELECT cluster, COUNT(*) as c FROM respuestas GROUP BY cluster ORDER BY c DESC'
    ).fetchall()
    conn.close()
    
    prompt, dominante = generar_prompt_sintetico() if n > 0 else ('', '')
    
    return jsonify({
        'total_respuestas': n,
        'clusters': [{'nombre': r[0], 'cantidad': r[1]} for r in clusters],
        'cluster_dominante': dominante,
        'prompt_actual': prompt
    })

@app.route('/cargar_corpus', methods=['POST'])
def cargar_corpus():
    datos = request.json or []
    for r in datos:
        texto = r.get('relato', '')
        embedding = calcular_embedding(texto)
        cluster = calcular_cluster(embedding)
        guardar_respuesta({
            'edad': r.get('edad', ''),
            'sistema_salud': r.get('sistema_salud', ''),
            'imagen_mental': texto[:500],
            'deseo': '',
            'sintetico': r.get('sintetico', 0)
        }, embedding, cluster)
    return jsonify({'status': 'ok', 'cargados': len(datos)})

# Inicializar DB al arrancar
with app.app_context():
    init_db()

if __name__ == '__main__':
    print("Servidor iniciado en http://localhost:5000")
    app.run(debug=True, port=5000)
