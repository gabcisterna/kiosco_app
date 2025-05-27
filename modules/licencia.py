import hashlib
from datetime import datetime
import os

ARCHIVO_ACTIVACION = "activacion.txt"
CLAVE_MAESTRA = "clave-super-secreta"  # Solo vos la sabés

def hash_string(texto):
    return hashlib.sha256(texto.encode()).hexdigest()

def generar_clave_mensual():
    fecha = datetime.now()
    clave_base = f"clave-secreta-{fecha.year}-{fecha.month}"
    hash_resultado = hashlib.sha256(clave_base.encode()).hexdigest()
    return hash_resultado[:8]

def esta_activado():
    if not os.path.exists(ARCHIVO_ACTIVACION):
        return False
    
    with open(ARCHIVO_ACTIVACION, "r") as f:
        contenido = f.read().strip()
    
    # Verifica activación permanente
    if contenido == hash_string("PERMANENTE"):
        return True

    # Verifica activación mensual
    ahora = datetime.now()
    valor_mes_actual = f"{ahora.year}-{ahora.month}"
    return contenido == hash_string(valor_mes_actual)

def activar(metodo="mensual"):
    with open(ARCHIVO_ACTIVACION, "w") as f:
        if metodo == "permanente":
            f.write(hash_string("PERMANENTE"))
        elif metodo == "mensual":
            fecha = datetime.now()
            valor = f"{fecha.year}-{fecha.month}"
            f.write(hash_string(valor))



print("Clave de este mes:", generar_clave_mensual())