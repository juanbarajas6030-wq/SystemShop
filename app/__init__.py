from flask import Flask
import os

# Crear app
app = Flask(__name__)

# Secret key desde variables de entorno
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

# Importar rutas
from app import routes