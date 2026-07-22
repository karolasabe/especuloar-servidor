from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import re
import unicodedata
import urllib.request
import urllib.error
import psycopg2
import psycopg2.extras
from datetime import datetime

app = Flask(__name__)
CORS(app)

DATABASE_URL = os.environ.get('DATABASE_URL')
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
UMBRAL = 5

# ============================================================
# DICCIONARIO DE CATEGORÍAS — 11 campos semánticos
# ============================================================
CATEGORIAS = {
    'dolor_fisico': {
        'color': '#FF2424',
        'nombre_es': 'dolor físico',
        'nombre_en': 'physical pain',
        'palabras': [
            'dolor','duele','duelen','dolió','doloroso',
            'ardor','arde','ardía','ardió','ardiendo',
            'quema','quemaba','quemar','quemó',
            'abrasó','abrasar','abrasa',
            'escaldó','escaldaba','escaldar',
            'calambre','calambres','cólico','cólicos',
            'contractura','espasmo','espasmos',
            'retorcijón','retorcijones',
            'retorció','retorcía',
            'torció','torcía','torcer','torcimiento',
            'insoportable','adolorida','adolorido',
            'cortar','cortó','cortante','corte',
            'rajar','rajó','rajada','rajadura',
            'pinchar','pinchó','pinchazo','pinchazos',
            'punzada','punzadas','punzante','punzó',
            'clavar','clavó','agujazo',
            'perforar','perforación',
            'atravesar','atravesó',
            'incidir','incisión',
            'lacerante','lacera','laceró',
            'sangrar','sangró','sangrando','sangré',
            'sangre','desangrar','desangrarse','me desangré',
            'hemorragia','hematoma','hematomas',
            'herida','heridas',
            'moretón','moretones',
            'llaga','llagas',
            'lesión','lesiones',
            'magullada','magulladura','amoratada',
            'desgarro','desgarrar','desgarramiento',
            'rasgar','rasgado',
            'tirón','tirones','pellizco','pellizcos',
            'apretó','apretaba','apretar','aprieta',
            'estrujó','estrujaba','estrujar',
            'oprimió','oprimía','oprimir',
            'comprimió','comprimía',
            'quebró','quebraba','quebrar',
            'rompió','rompía',
            'fracturó','fractura','fracturaba',
            'partió','partía',
            'astilló','resquebrajó',
            'pulverizó','pulverizaba','pulverizar',
            'trituró','trituraba','triturar',
            'aplastó','aplastaba','aplastar',
            'destrozó','destrozaba',
            'sufrimiento','sufrir','sufrí',
            'padecimiento','padecer','padecí',
            'agonía','agonizaba',
            'tormento','atormentada','martirio',
            'náuseas','náusea','mareo','mareada',
            'me desmayé','me desvanecí',
            'me descompuse','me descompongo',
            'machucó','machucaba','machuca','tincazo',
            'me mató','me estaba matando',
            'no aguantaba','no aguanté',
            'quedé destrozada','quedé destruida',
            'me dejó cagada','me sacaron la mugre',
            'ardía horrores','horrible dolor',
            'me partió','me rajó',
            'dolores','escozor','picazón','picazon','picor',
            'ardiente','lacerada','lacerado','laceraciones',
            'apuñalada','apuñalado','estocada','puñalada',
            'me retorcía de dolor','contorsión','contorsionaba',
            'malestar físico','malestar fisico',
            'molestia física','molestia fisica',
            'me quejé de dolor','quejido de dolor',
            'tironeo','tironeaba',
            'me sacó un grito','grité de dolor',
            'insufrible','punzadas agudas',
            'hurt','hurts','pain','painful',
            'ache','aching','bleeding','bleed',
            'burning','cramp','wound','cut','bruise',
            'stinging','throbbing','sore','soreness',
            'agony','agonizing','excruciating',
            'tender','tenderness','bruised','bruising',
            'wounded','scraped','scratch','scratching',
            'stab','stabbing','piercing','laceration',
            'discomfort','uncomfortable','unbearable'
        ]
    },
    'miedo': {
        'color': '#A01F35',
        'nombre_es': 'miedo',
        'nombre_en': 'fear',
        'palabras': [
            'miedo','miedosa',
            'aterrada','aterradora','aterró','aterraba',
            'horror','horrorizada','horrorosa',
            'espanto','espantada','espantosa',
            'fobia','aprensión','aprensiva',
            'pánico','paniqueada',
            'temor','temores','temía','temerosa',
            'ansiedad','ansiosa','ansioso',
            'angustia','angustiada','angustiante',
            'estrés','estresada','estresante',
            'tensión','tensa','tenso',
            'nervios','nerviosa','nervioso','nerviosismo',
            'agitada','agitación',
            'intranquila','intranquilidad',
            'inquieta','inquietud','zozobra',
            'susto','asustada','me asusté',
            'preocupación','preocupada',
            'anticipación','esperar lo peor',
            'taquicardia',
            'temblaba','temblé','temblor',
            'me paralicé','parálisis',
            'me bloqueé','bloqueo',
            'piel de gallina',
            'hiperventilé','respiración agitada',
            'sudor frío','sudorosa',
            'me aferré','me puse rígida',
            'el corazón a mil','me latía fuerte',
            'llorar','lloraba','lloré','llanto','lágrimas',
            'sollozar','sollocé','sollozos',
            'llorosa','quería llorar','ganas de llorar',
            'escalofrío','escalofríos',
            'me cagué de miedo','me cagué',
            'quedé helada','me quedé congelada',
            'me dio cosa','me dio susto',
            'quería salir corriendo','me quería ir',
            'quería escapar','no podía respirar bien',
            'me puse histérica','los nervios a flor de piel',
            'me latía a mil','no podía parar de temblar',
            'temeroso','temerosa','aprensivo',
            'consternada','consternado','consternación',
            'pavor','pavoroso','inseguridad','insegura','inseguro',
            'alarmada','alarmado','alarma','sobresalto',
            'sobresaltada','sobresaltado',
            'me heló la sangre','se me heló la sangre',
            'me quedé sin aire','no podía moverme',
            'quedé paralizada','quedé paralizado',
            'me tiritaba la voz','voz entrecortada','entrecortada',
            'inquietante','desasosiego','desasosegada',
            'recelo','recelosa','desconfianza','desconfiada',
            'fear','anxiety','panic','terror',
            'scared','nervous','dread','worried',
            'frightened','terrified','paralyzed',
            'trembling','shaking',
            'apprehension','apprehensive','uneasy','uneasiness',
            'startled','alarm','alarmed','trembled',
            'freeze','froze','frozen','petrified','dreaded',
            'distress','distressed','jittery'
        ]
    },
    'verguenza_exposicion': {
        'color': '#C4943D',
        'nombre_es': 'vergüenza / exposición',
        'nombre_en': 'shame / exposure',
        'palabras': [
            'vergüenza','avergonzada','pudor',
            'exposición','expuesta','expuesto',
            'desnudez','desnuda','desnudada',
            'despojada','despojo',
            'íntimo','íntima','intimidad',
            'zona íntima','partes íntimas','lo más íntimo',
            'vulnerable','vulnerabilidad',
            'humillación','humillante',
            'privacidad','privado','privada',
            'observada','observación',
            'pilucha','piluchi',
            'en pelota','encuera','encuerada',
            'mirada','miradas','bajo la lupa',
            'examinada','inspeccionada','inspección',
            'escudriñada','radiografiada','diseccionada',
            'vitrina','escaparate','aparador',
            'exhibida','exhibición',
            'muñeca','maniquí',
            'objeto de estudio','pieza de museo',
            'cosificada','cosificación',
            'deshumanizada','deshumanizante',
            'reducida a un cuerpo','solo un cuerpo',
            'pena','me dio pena','qué pena','penosa',
            'me sonrojé','me puse colorada',
            'degradante','degradada',
            'indigna','indignante',
            'juzgada','juzgar',
            'quería desaparecer',
            'quería que me tragara la tierra',
            'me quería morir de vergüenza',
            'bochorno','bochornoso','turbada','turbado','turbación',
            'sonrojo','sonrojada','sonrojado',
            'ruborizada','ruborizado','rubor',
            'desprotegida','desprotegido','desprotección',
            'indefensa','indefenso','desamparada','desamparo',
            'tratada como objeto','como pieza de carne',
            'trato deshumanizante','sin dignidad',
            'despersonalizada','despersonalizado',
            'cero privacidad','ninguna privacidad','nula privacidad',
            'me sentí un número','me sentí un numero',
            'solo un número','me sentí cosa','como mercancía',
            'shame','ashamed','embarrassed',
            'exposed','naked','vulnerable',
            'humiliation','humiliated',
            'objectified','scrutinized',
            'privacy','intimate',
            'mortified','mortification','blush','blushing',
            'undignified','dehumanizing','dehumanized',
            'stared at','on display','specimen',
            'scrutiny','self-conscious'
        ]
    },
    'sensaciones_frias': {
        'color': '#2EC4D8',
        'nombre_es': 'sensaciones frías',
        'nombre_en': 'cold sensations',
        'palabras': [
            'frío','fría','frías','fríos',
            'helado','helada','gélido','gélida',
            'congelado','congelante',
            'frialdad','glacial',
            'frío de morgue','frío como el hielo',
            'temperatura helada',
            'me congelé','congelada',
            'me heló','me dejó helada',
            'metal','metálico','metálica',
            'fierro','acero','acero inoxidable',
            'hierro','inoxidable',
            'metalizado','cromado','niquelado',
            'titanio','aluminio',
            'tornillo','corchete','grapa',
            'clavo','alambre','varilla','barra',
            'lámina','placa',
            'quirúrgico','quirúrgica',
            'pabellón','quirófano',
            'plateado','plateada',
            'brillante','liso','lisa','resbaladizo',
            'áspero','áspera','tosco','tosca',
            'duro','dura','dureza',
            'rígido','rígida','rigidez',
            'inerte','inanimado','inanimada',
            'muerto','muerta','sin vida',
            'sin pulso','sin temperatura',
            'cadavérico','cadáver',
            'morgue','frigorífico',
            'disecado','embalsamado','fosilizado',
            'clínico','séptico',
            'antiséptico','aséptico','aséptica',
            'esterilizado','esterilizada','desinfectado',
            'tumba','fosa',
            'cloaca','desagüe','sumidero',
            'humedad','húmedo','húmeda','humedal',
            'congelador','heladera','refrigerador','hielera',
            'témpano','iceberg','glaciar','escarcha',
            'antártida','polo sur','tundra','permafrost',
            'patagonia',
            'llave de tuercas','abrelatas','sacacorchos',
            'pinza','pinzas','tenaza',
            'gancho','garfio',
            'bisturí','tijera','tijeras',
            'cuchillo','cuchilla','espéculo',
            'como una trampa',
            'frío a cagarse','me cagué de frío',
            'me llegó frío hasta los huesos',
            'entumecida','entumecido','entumecimiento',
            'adormecida','adormecido',
            'anestesiada','anestesiado','anestesia local',
            'insensibilizada','distanciamiento','frialdad clínica',
            'cold','freezing','metallic','steel',
            'rigid','icy','frozen','hard',
            'sharp','clinical','sterile',
            'instrument','morgue','cadaver',
            'numb','numbness','sterilized','stainless',
            'chilly','chill','frosty','detached'
        ]
    },
    'sensaciones_calidas': {
        'color': '#E8935A',
        'nombre_es': 'sensaciones cálidas',
        'nombre_en': 'warm sensations',
        'palabras': [
            'tibio','tibia','tibiecito','tibiecita',
            'templado','templada',
            'calorcito','entibió','entibiando',
            'temperatura agradable',
            'cariño','cariños','cariñoso','cariñosa',
            'amor','amoroso','amorosa',
            'ternura','tierno','tierna',
            'afecto','afectuoso','afectuosa',
            'alegría','alegre','felicidad','feliz',
            'familiar','familiaridad',
            'cercano','cercana','cercanía',
            'vínculo','vinculada',
            'conexión','conectada',
            'cuidado','cuidados','cuidadoso','cuidadosa',
            'empatía','empático','empática',
            'comprensión','comprensivo','comprensiva',
            'considerado','considerada',
            'atento','atenta',
            'amigable','amistoso','amistosa',
            'amable','amabilidad',
            'gentil','gentileza',
            'delicado','delicada','delicadeza',
            'respetuoso','respetuosa','respeto',
            'humano','humana','humanidad',
            'sensible','sensibilidad',
            'acogedor','acogedora','acogida',
            'tranquilidad','tranquila',
            'alivio','aliviada',
            'paz','pacífica',
            'simpático','simpática','buena onda',
            'goma','algodón',
            'tela','tela suave',
            'espuma','esponja','esponjosa','esponjoso',
            'acolchado','acolchada',
            'blando','blanda',
            'suave','suavidad',
            'flexible','maleable',
            'reconfortante','confortable',
            'a gusto','agusto',
            'entrañable','protector','protectora','protección',
            'resguardada','resguardado','resguardo',
            'arropada','arropado','abrazo','abrazada','abrazado',
            'contención emocional','sostén','sostenida','sostenido',
            'acompañada','acompañado','acompañamiento',
            'seguridad emocional',
            'warm','soft','gentle',
            'rubber','cotton',
            'comfortable','soothing','smooth',
            'care','kindness','empathy',
            'warmth','tenderness','affection',
            'nurturing','protective','supportive',
            'embrace','embraced','held','wrapped',
            'cared for','looked after'
        ]
    },
    'sonido': {
        'color': '#6BBF8A',
        'nombre_es': 'sonido / acústica',
        'nombre_en': 'sound / acoustics',
        'palabras': [
            'sonido','sonidos','ruido','ruidos',
            'chirrido','chirría','chirriar',
            'clic','click',
            'cruje','crujido','crujir',
            'rechinido','rechinar',
            'zumbido','zumba','zumbar',
            'tintineo','tintinear',
            'traqueteo','traquetear',
            'golpeteo','golpe','golpear',
            'martilleo','martillar',
            'repiqueteo','redoble',
            'burbujeo','burbujea',
            'estrépito','estruendo',
            'resonancia','reverberación',
            'vibración','vibra','eco','tictac',
            'murmullo','susurro','rumor','rumores',
            'cuchicheo','parloteo',
            'latido','latidos','palpitación',
            'pulso','pulsación','bombeo',
            'respiración','jadeo',
            'quejido','gemido','gemidos',
            'lamento','lamentos','lamentar','quejumbroso',
            'grito','gritos','gritería','griterío',
            'alarido','alaridos',
            'chillido','chillar',
            'hipido','hipo',
            'sollozos','sollozo',
            'risas','risa','carcajada',
            'bostezo','bostezar',
            'vozarrón','voz grave','voz ronca',
            'ronco','ronca','ronquido','ronquera',
            'carraspeo',
            'silbido','silbar','silba',
            'pitido','pitar','pita',
            'sinfonía','sinfónico',
            'melodía','melódico','melodioso',
            'polifonía','polifónico',
            'armonía','armónico',
            'disonancia','disonante',
            'ritmo','rítmico','compás',
            'nota','notas','tono','tonos',
            'tambor','tamborilleo','percusión',
            'música','musicales','midi',
            'sonido metálico','sonido industrial',
            'sonido de máquina','maquinaria',
            'engranaje','motor','mecanismo',
            'silencio','mutismo',
            'callado','callada','en silencio',
            'nadie habló','no dijo nada',
            'escuché','escuchaba','escuchar',
            'oí','oía','oír',
            'percibí','percibía',
            'retumbaba','resonaba',
            'sonaba feo','sonaba horrible',
            'hacía un ruido','estridente',
            'traqueteando','vibrando','pitido agudo',
            'sonido chirriante','estruendoso','ensordecedor',
            'apagado','amortiguado','sonido sordo','ruido sordo',
            'sound','noise','click','clang','scrape',
            'creak','squeak','rattle',
            'buzz','hum','vibration',
            'silence','heard','listening',
            'muffled','deafening','screeching','beeping',
            'thud','thump','tapping','rustling'
        ]
    },
    'aromas': {
        'color': '#E8E0D4',
        'nombre_es': 'aromas / olores',
        'nombre_en': 'aromas / smells',
        'palabras': [
            'olor','olía','huele','huelen','oler',
            'aroma','fragancia',
            'olfato','olfativo',
            'hedor','hediondez','hediondo',
            'pestilencia','fetidez','fétido','fétida',
            'pudredumbre','pudrición','putrefacción',
            'podrido','podredumbre',
            'descompuesto','descomposición',
            'rancio','rancia',
            'corrompido','enmohecido',
            'nauseabundo','nauseabunda',
            'repugnante','repugnancia',
            'asqueroso','asquerosa','asco',
            'maloliente','pestoso',
            'olor característico','olor peculiar',
            'olor raro','olor extraño',
            'mal olor','qué olor','qué peste',
            'huele feo','hedía','apestaba','apeste',
            'olía a','huele a',
            'antiséptico','alcohol','alcohol gel',
            'yodo','cloro','lejía',
            'desinfectante','limpiador',
            'detergente','amoniaco',
            'éter','formol','acetona',
            'químico','química',
            'sintético','sintética',
            'reactivo','laboratorio',
            'sangre','orgánico','sudor',
            'secreción','fluido corporal',
            'fluidos corporales',
            'orina','excremento',
            'vagina','genitales','poto',
            'cochino','cochina','sucio','sucia',
            'alcantarilla','alcantarillado',
            'aguas servidas','desagüe','cañería',
            'perfume','jabón','floral',
            'inodoro','penetrante','acre','rancidez',
            'vaho','tufo','hedores',
            'olor a hospital','olor hospitalario',
            'smell','scent','odor',
            'antiseptic','alcohol','chemical','organic',
            'stench','fragrance','rotten','putrid','sewage',
            'pungent','acrid','musty','reek','reeking',
            'whiff','odorless'
        ]
    },
    'violencia_sexual': {
        'color': '#B814E8',
        'nombre_es': 'violencia sexual',
        'nombre_en': 'sexual violence',
        'palabras': [
            'violación','violar','violada',
            'agresión sexual','agresión física',
            'vejación','vejada','vejar',
            'ultraje','ultrajada','ultrajar',
            'atropello','atropellada','violentada',
            'profanación','transgredió','transgresión',
            'sometimiento sexual','sumisión química',
            'coerción sexual','coercitivo',
            'intimidación sexual','intimidación',
            'explotación sexual','estupro',
            'violencia de género',
            'abuso de poder','abuso de confianza',
            'depravado','depravación',
            'lascivo','lascivia','libertinaje',
            'se propasó','se excedió',
            'se aprovechó','abusó de mí',
            'se erectó','erección',
            'se masturbó','masturbación',
            'me penetró','penetración no consentida',
            'abuso sexual','abusada sexualmente',
            'manoseo','manoseada','manosearon',
            'tocamientos no consentidos',
            'tocó donde no debía',
            'tocó más de la cuenta',
            'tocó partes que no debía',
            'entró sin avisar','metió mano',
            'me agarró','me tocó','me manoseó',
            'me palpó sin permiso',
            'hizo algo que no correspondía',
            'me desnudaron innecesariamente',
            'me exhibieron sin necesidad',
            'sin consentimiento','sin mi consentimiento',
            'consentimiento vulnerado',
            'acoso','acosada','acoso sexual',
            'ciberacoso sexual',
            'conducta inapropiada',
            'obsceno','obscena',
            'trauma sexual','traumatizada',
            'victimización','víctima',
            'me pasó a llevar','me faltó el respeto',
            'se mandó un abuso','me vulneró','me hizo algo',
            'violentación','vejatorio','vejatoria',
            'denigrante','denigrada','denigrado',
            'cosificación sexual','violencia obstétrica',
            'maltrato obstétrico','trato denigrante',
            'sin mi permiso','en contra de mi voluntad',
            'contra mi voluntad','me obligaron','me forzaron',
            'forzada','forzado','abuso de autoridad médica',
            'assault','sexual abuse',
            'without consent','harassment',
            'groped','violated','molested',
            'inappropriate contact',
            'non-consensual','coercion',
            'sexual trauma','abuse of power',
            'exploitation','predatory',
            'obstetric violence','forced','forcibly',
            'against my will','degrading',
            'non-consensual touching','misconduct','coerced'
        ]
    },
    'placer_deseo': {
        'color': '#FF2D8A',
        'nombre_es': 'placer / deseo',
        'nombre_en': 'pleasure / desire',
        'palabras': [
            'placer','placentero','placentera',
            'placer sexual','placer corporal','placer físico',
            'goce','gozar','gozosa',
            'orgasmo','orgásmica',
            'erótico','erótica','erotismo',
            'sensual','sensualidad',
            'voluptuoso','voluptuosa',
            'lujuria','lujurioso',
            'excitación sexual','deseo sexual',
            'rico','rica','qué rico',
            'me excitó','me provocó',
            'me gustó el tacto',
            'delicioso','deliciosa',
            'pleasure','pleasurable',
            'orgasm','erotic',
            'sensual','arousal',
            'desire','enjoyment','la pasé bien','fascinada','entretenido','entretenida','me encantó','gozo','amado','amor','maravilloso',
            'complacencia','autoconocimiento','conexión con mi cuerpo',
            'empoderada','empoderado','empoderamiento',
            'disfrute','disfruté','disfrutar',
            'satisfacción','satisfactorio','satisfactoria',
            'libertad corporal','plenitud',
            'satisfaction','satisfying','empowered','empowerment',
            'enjoyed','enjoyable','fulfilling',
            'bodily autonomy','pleasurable experience'
        ]
    },
    'profesional_hombre': {
        'color': '#4A7BAF',
        'nombre_es': 'profesional hombre',
        'nombre_en': 'male professional',
        'palabras': [
            'médico',
            'ginecólogo','obstetra',
            'urólogo','anestesiólogo',
            'enfermero','radiólogo','ecografista',
            'residente','interno','becado',
            'técnico','paramédico',
            'matrón','secretario','el tens',
            'especialista hombre',
            'el médico','el doctor',
            'el ginecólogo','el anestesista',
            'facultativo','cirujano','kinesiólogo',
            'male doctor','male physician',
            'male gynecologist','male obstetrician',
            'male nurse','man doctor','he was my doctor'
        ]
    },
    'profesional_mujer': {
        'color': '#F5DD2C',
        'nombre_es': 'profesional mujer',
        'nombre_en': 'female professional',
        'palabras': [
            'médica','doctora',
            'ginecóloga','uróloga',
            'anestesióloga','enfermera',
            'radióloga','ecografista',
            'residente','interna','becada',
            'paramédica','matrona','partera',
            'doula','dula',
            'secretaria','la tens',
            'especialista mujer',
            'la médica','la medica',
            'la doctora','la ginecóloga',
            'la anestesista',
            'facultativa','cirujana','kinesióloga',
            'female doctor','female physician',
            'female gynecologist','female obstetrician',
            'female nurse','woman doctor','midwife','doula'
        ]
    }
}

# ============================================================
# NORMALIZACIÓN DE TILDES
# El corpus llega con ortografía inconsistente: mismo hablante puede
# escribir "dolió" o "dolio", "vergüenza" o "verguenza". Sin esto,
# el clasificador solo detecta la forma exacta que quedó tipeada en
# el diccionario, y pierde todas las variantes sin tilde.
# Se normaliza tanto el texto del relato como cada palabra del
# diccionario antes de comparar, así ambos quedan en el mismo
# alfabeto y coinciden sin importar si el relato llevaba tildes.
# La ñ se protege explícitamente: NFKD la descompone en "n" + tilde
# combinante, y removerla la convertiría en "n" común, lo cual es un
# error de fondo (año / ano son palabras distintas, no una acentuada
# y otra no).
# ============================================================
def quitar_tildes(texto):
    texto = texto.replace('ñ', '\x00').replace('Ñ', '\x01')
    descompuesto = unicodedata.normalize('NFKD', texto)
    sin_tildes = ''.join(c for c in descompuesto if not unicodedata.combining(c))
    return sin_tildes.replace('\x00', 'ñ').replace('\x01', 'Ñ')

# Patrones precompilados por categoría, calculados una sola vez al
# iniciar el servidor. Cada palabra del diccionario se normaliza y
# se compila con límite de palabra, para no volver a hacerlo en cada
# relato que llega por el webhook.
_PATRONES_CATEGORIA = {
    cat: [
        re.compile(r'(?<!\w)' + re.escape(quitar_tildes(palabra.lower())) + r'(?!\w)')
        for palabra in datos['palabras']
    ]
    for cat, datos in CATEGORIAS.items()
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
        relato_traducido TEXT,
        correo TEXT,
        idioma TEXT,
        categorias_activadas TEXT,
        intensidades TEXT
    )''')
    c.execute('''ALTER TABLE respuestas
        ADD COLUMN IF NOT EXISTS relato_traducido TEXT''')
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
# TRADUCCIÓN
# ============================================================
def traducir_relato(texto):
    if not ANTHROPIC_API_KEY:
        return None
    try:
        payload = json.dumps({
            'model': 'claude-haiku-4-5-20251001',
            'max_tokens': 1000,
            'messages': [{
                'role': 'user',
                'content': (
                    'Traduce al español este relato de experiencia corporal. '
                    'Mantén el tono íntimo y personal. '
                    'Solo responde con la traducción, sin comentarios adicionales:\n\n'
                    + texto
                )
            }]
        }).encode('utf-8')
        req = urllib.request.Request(
            'https://api.anthropic.com/v1/messages',
            data=payload,
            headers={
                'x-api-key': ANTHROPIC_API_KEY,
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json'
            }
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read())
            return data['content'][0]['text']
    except Exception:
        return None

# ============================================================
# ANÁLISIS SEMÁNTICO
# ============================================================
def analizar_relato(texto):
    texto_normalizado = quitar_tildes(texto.lower())
    resultado = {}
    for cat, patrones in _PATRONES_CATEGORIA.items():
        menciones = sum(1 for patron in patrones if patron.search(texto_normalizado))
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
    relato_traducido = traducir_relato(relato) if idioma == 'en' else None
    c.execute('''INSERT INTO respuestas
        (timestamp, relato, relato_traducido, correo, idioma, categorias_activadas, intensidades)
        VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id''',
        (datetime.now().isoformat(),
         relato,
         relato_traducido,
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
    c.execute('SELECT COUNT(*) FROM respuestas')
    n = c.fetchone()[0]
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
    c.execute('SELECT COUNT(*) FROM respuestas')
    n_respuestas = c.fetchone()[0]
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
        'SELECT relato, relato_traducido, idioma, categorias_activadas, intensidades, timestamp '
        'FROM respuestas WHERE id = %s', (respuesta_id,)
    )
    row = c.fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'no encontrado'}), 404
    return jsonify({
        'id': respuesta_id,
        'relato': row[0],
        'relato_traducido': row[1],
        'idioma': row[2],
        'categorias_activadas': json.loads(row[3]),
        'intensidades': json.loads(row[4]),
        'timestamp': row[5]
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
    print('Servidor Espéculo(ar) — 11 categorías')
    app.run(debug=True, port=5000)
