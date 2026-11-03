# Configuración de gunicorn. gunicorn lee este archivo automáticamente
# cuando se inicia desde la raíz del repositorio, así que el Start Command
# de Render puede seguir siendo "gunicorn servidor:app".
#
# Un proceso con 4 hilos: una traducción lenta (hasta 30 s) ya no bloquea
# el polling del display ni el webhook de Tally. Se mantiene un solo
# proceso porque init_db() corre al importar servidor.py.
#
# No se define "bind": gunicorn usa la variable PORT que entrega Render.

workers = 1
worker_class = 'gthread'
threads = 4
timeout = 60
