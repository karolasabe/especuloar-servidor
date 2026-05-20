from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import psycopg2
import psycopg2.extras
from datetime import datetime

app = Flask(__name__)
CORS(app)

DATABASE_URL = os.environ.get('DATABASE_URL')
UMBRAL = 5

# ============================================================
# DICCIONARIO DE CATEGORÍAS — 9 campos semánticos
# ============================================================
CATEGORIAS = {
    'dolor_fisico': {
        'color': '#E8453A',
        'nombre_es': 'dolor físico',
        'nombre_en': 'physical pain',
        'palabras': [
            'dolor','duele','duelen','dolió','doloroso','ardor','arde','ardía',
            'punzada','punzadas','pinchazo','pinchazos','quemar','quema','quemaba',
            'desgarrar','desgarro','desgarramiento','cortar','cortante',
            'lastimar','lastimó','lastimaba','herida','heridas',
            'rasgar','rasgado','presión','presiona','presionaba',
            'calambres','calambre','contractura','contracción',
            'insoportable','agudo','aguda','intenso','intensa',
            'lacerante','punzante','brutalmente','brutal',
            'hurt','hurts','pain','painful','ache','aching','burning','sharp','cramp'
        ]
    },
    'frio_metal': {
        'color': '#5A8FD4',
        'nombre_es': 'material metálico / frío / desagradable',
        'nombre_en': 'metallic / cold / unpleasant',
        'palabras': [
            'frío','fría','frías','fríos','helado','helada','congelado','congelante',
            'metal','metálico','metálica','acero','hierro','inoxidable',
            'duro','dura','rígido','rígida','áspero','áspera',
            'chirría','chirrido','chirriar','cruje','crujido','ruido','estridente',
            'instrumento','aparato','dispositivo','máquina','herramienta',
            'invasivo','invasiva','penetrar','penetración',
            'abrelatas','sacacorcho','pinza','tenaza','tornillo','tuerca',
            'desagradable','molesto','molesta','incómodo','incómoda',
            'cold','metal','metallic','rigid','hard','device','instrument','invasive'
        ]
    },
    'materiales_agradables': {
        'color': '#E8935A',
        'nombre_es': 'materiales agradables / cálidos',
        'nombre_en': 'pleasant / warm materials',
        'palabras': [
            'tibio','tibia','cálido','cálida','caliente','calientito',
            'suave','suavidad','blando','blanda','flexible','morbido',
            'silicona','goma','plástico blando','algodón','tela',
            'perfume','aroma','olor agradable','floral',
            'pequeño','pequeña','diminuto','liviano','ligero',
            'ergonómico','ergonómica','adaptable','amigable',
            'reconfortante','confortable','cómodo','cómoda',
            'warm','soft','gentle','comfortable','smooth','flexible'
        ]
    },
    'miedo_ansiedad': {
        'color': '#9E9E9E',
        'nombre_es': 'miedo / ansiedad / preocupación',
        'nombre_en': 'fear / anxiety / worry',
        'palabras': [
            'miedo','miedosa','aterrada','aterrador','aterradora',
            'ansiedad','ansiosa','ansioso','angustia','angustiada',
            'nervios','nerviosa','nervioso','nerviosismo',
            'temor','temores','temer','pánico','terror','terrorífica',
            'preocupación','preocupada','preocupante',
            'anticipación','anticipar','esperar lo peor',
            'taquicardia','sudor','temblor','temblaba',
            'llorar','lloraba','lloré','llanto','lágrimas',
            'dread','fear','anxiety','panic','terror','scared','nervous','worried'
        ]
    },
    'sensaciones_agradables': {
        'color': '#D4847A',
        'nombre_es': 'sensaciones agradables / seguridad / calma',
        'nombre_en': 'pleasant sensations / safety / calm',
        'palabras': [
            'tranquila','tranquilidad','tranquilizadora','calma','calmada',
            'segura','seguridad','confianza','confiable',
            'alivio','aliviada','reconfortada',
            'cómoda','comodidad','bien','bienestar',
            'profesional amable','trato amable','gentil','gentileza',
            'explicación','explicó','informó','avisó','preparó',
            'respeto','respetuosa','respetuoso','dignidad',
            'empática','empatía','comprensión','comprensiva',
            'safe','comfortable','calm','relief','trust','gentle','kind','reassured'
        ]
    },
    'normalizacion': {
        'color': '#6BBF8A',
        'nombre_es': 'normalización / resignación',
        'nombre_en': 'normalization / resignation',
        'palabras': [
            'normal','normalidad','normalizar','rutina','rutinario',
            'necesario','necesaria','hay que hacerlo','toca hacerlo',
            'resignada','resignación','resignarse','acostumbrada',
            'tolerable','toleraba','aguantar','aguantaba','soportar','soportaba',
            'trámite','obligación','obligatoria','deber',
            'siempre es así','así es','así funciona',
            'nada nuevo','lo de siempre','ya sé cómo es',
            'inevitable','inevitablemente',
            'routine','necessary','tolerate','endure','resign','accept'
        ]
    },
    'vivencia_sexual_traumatica': {
        'color': '#9B6BBF',
        'nombre_es': 'vivencia sexual traumática',
        'nombre_en': 'traumatic sexual experience',
        'palabras': [
            'violación','violar','violada',
            'abuso sexual','abusada sexualmente',
            'obscenidad','obsceno','obscena','lascivo','lascivia',
            'erección','erecto','excitado','excitación',
            'tocó más de la cuenta','tocaron más de la cuenta',
            'tocó donde no debía','manoseo','manoseada','manosearon',
            'sin consentimiento','sin mi consentimiento',
            'acoso','acosada','acosaron','conducta inapropiada',
            'assault','sexual abuse','erection','inappropriate touching',
            'without consent','harassment'
        ]
    },
    'profesional_masculino': {
        'color': '#1A3A6B',
        'nombre_es': 'profesional masculino',
        'nombre_en': 'male professional',
        'palabras': [
            'médico','doctor','ginecólogo','especialista hombre',
            'él'
        ]
    },
    'profesional_femenino': {
        'color': '#D4B800',
        'nombre_es': 'profesional femenina',
        'nombre_en': 'female professional',
        'palabras': [
            'médica','doctora','ginecóloga','matrona','obstétrica',
            'ella'
        ]
    }
}

# ============================================================
# BASE DE DATOS
# ============================================================
def get_conn():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS respuestas (
        id SERIAL PRIMARY KEY,
        timestamp TEXT,
        relato TEXT,
        correo TEXT,
        idioma TEXT,
        categorias_activadas TEXT,
        intensidades TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS pintitas (
        id SERIAL PRIMARY KEY,
        respuesta_id INTEGER,
        categoria TEXT,
        intensidad REAL,
        timestamp TEXT
    )''')
    conn.commit()
    conn.close()

with app.app_context():
    init_db()

# ============================================================
# ANÁLISIS SEMÁNTICO
# ============================================================
def analizar_relato(texto):
    texto_lower = texto.lower()
    resultado = {}
    for cat, datos in CATEGORIAS.items():
        menciones = sum(1 for p in datos['palabras'] if p in texto_lower)
        if menciones > 0:
            palabras_texto = max(1, len(texto.split()))
            intensidad = min(1.0, menciones / max(1, palabras_texto / 20))
            resultado[cat] = round(intensidad, 3)
    return resultado

def detectar_idioma(texto):
    palabras_es = ['que','con','una','por','para','como','pero','los','las','del']
    palabras_en = ['the','and','that','with','for','this','but','are','was','have']
    score_es = sum(1 for p in palabras_es if f' {p} ' in f' {texto.lower()} ')
    score_en = sum(1 for p in palabras_en if f' {p} ' in f' {texto.lower()} ')
    return 'es' if score_es >= score_en else 'en'

# ============================================================
# GUARDAR
# ============================================================
def guardar_respuesta(relato, correo, categorias_activadas):
    conn = get_conn()
    c = conn.cursor()
    idioma = detectar_idioma(relato)
    c.execute('''INSERT INTO respuestas
        (timestamp, relato, correo, idioma, categorias_activadas, intensidades)
        VALUES (%s,%s,%s,%s,%s,%s) RETURNING id''',
        (datetime.now().isoformat(),
         relato,
         correo,
         idioma,
         json.dumps(list(categorias_activadas.keys())),
         json.dumps(categorias_activadas)))
    respuesta_id = c.fetchone()[0]
    for cat, intensidad in categorias_activadas.items():
        c.execute('''INSERT INTO pintitas
            (respuesta_id, categoria, intensidad, timestamp)
            VALUES (%s,%s,%s,%s)''',
            (respuesta_id, cat, intensidad, datetime.now().isoformat()))
    conn.commit()
    n = c.execute('SELECT COUNT(*) FROM respuestas').fetchone()[0]
    conn.close()
    return respuesta_id, n

# ============================================================
# ENDPOINTS
# ============================================================
@app.route('/webhook', methods=['POST'])
def webhook():
    datos = request.json or {}
    relato = ''
    correo = ''

    if 'data' in datos:
        for field in datos.get('data', {}).get('fields', []):
            if field.get('type') == 'TEXTAREA':
                relato = field.get('value', '')
            if field.get('type') == 'INPUT_EMAIL':
                correo = field.get('value', '')

    if not relato:
        relato = datos.get('relato', datos.get('texto', datos.get('story', '')))
    if not correo:
        correo = datos.get('correo', datos.get('email', ''))

    if not relato:
        return jsonify({'status': 'error', 'mensaje': 'sin relato'}), 400

    categorias = analizar_relato(relato)
    respuesta_id, n_total = guardar_respuesta(relato, correo, categorias)

    return jsonify({
        'status': 'ok',
        'id': respuesta_id,
        'total_respuestas': n_total,
        'categorias_activadas': categorias,
        'nueva_sintesis': n_total % UMBRAL == 0
    })

@app.route('/estado', methods=['GET'])
def estado():
    conn = get_conn()
    c = conn.cursor()
    n_respuestas = c.execute('SELECT COUNT(*) FROM respuestas').fetchone()[0]
    c.execute(
        'SELECT categoria, COUNT(*) as n, AVG(intensidad) as avg_int '
        'FROM pintitas GROUP BY categoria ORDER BY n DESC'
    )
    pintitas = c.fetchall()
    conn.close()

    datos_pintitas = [{
        'categoria': p[0],
        'cantidad': p[1],
        'intensidad_promedio': round(p[2], 3),
        'color': CATEGORIAS.get(p[0], {}).get('color', '#888'),
        'nombre_es': CATEGORIAS.get(p[0], {}).get('nombre_es', p[0]),
        'nombre_en': CATEGORIAS.get(p[0], {}).get('nombre_en', p[0])
    } for p in pintitas]

    return jsonify({
        'total_respuestas': n_respuestas,
        'pintitas': datos_pintitas
    })

@app.route('/pintitas_recientes', methods=['GET'])
def pintitas_recientes():
    n = int(request.args.get('n', 20))
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        'SELECT id, respuesta_id, categoria, intensidad, timestamp '
        'FROM pintitas ORDER BY id DESC LIMIT %s', (n,)
    )
    rows = c.fetchall()
    conn.close()
    return jsonify([{
        'id': r[0],
        'respuesta_id': r[1],
        'categoria': r[2],
        'intensidad': r[3],
        'color': CATEGORIAS.get(r[2], {}).get('color', '#888'),
        'nombre_es': CATEGORIAS.get(r[2], {}).get('nombre_es', r[2]),
        'timestamp': r[4]
    } for r in rows])

@app.route('/relato/<int:respuesta_id>', methods=['GET'])
def obtener_relato(respuesta_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        'SELECT relato, idioma, categorias_activadas, intensidades, timestamp '
        'FROM respuestas WHERE id = %s', (respuesta_id,)
    )
    row = c.fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'no encontrado'}), 404
    return jsonify({
        'id': respuesta_id,
        'relato': row[0],
        'idioma': row[1],
        'categorias_activadas': json.loads(row[2]),
        'intensidades': json.loads(row[3]),
        'timestamp': row[4]
    })

@app.route('/cargar_corpus', methods=['POST'])
def cargar_corpus():
    datos = request.json or []
    cargados = 0
    for r in datos:
        relato = r.get('relato_experiencia', r.get('relato', ''))
        correo = r.get('correo', r.get('email', ''))
        if relato:
            categorias = analizar_relato(relato)
            guardar_respuesta(relato, correo, categorias)
            cargados += 1
    return jsonify({'status': 'ok', 'cargados': cargados})

@app.route('/reiniciar', methods=['POST'])
def reiniciar():
    conn = get_conn()
    c = conn.cursor()
    c.execute('DELETE FROM respuestas')
    c.execute('DELETE FROM pintitas')
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok', 'mensaje': 'corpus reiniciado'})

if __name__ == '__main__':
    print('Servidor Espéculo(ar) exp2 — Supabase')
    app.run(debug=True, port=5000)
