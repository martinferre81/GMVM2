# run.py
from flask import Flask
from core.apps import core_blueprint
from reclamos.apps import reclamos_blueprint

app = Flask(__name__)

# Registramos los blueprints
app.register_blueprint(core_blueprint, url_prefix='/core')
app.register_blueprint(reclamos_blueprint, url_prefix='/reclamos')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)