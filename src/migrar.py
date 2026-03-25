import json

# cargar dump
with open("datos.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# modelos que querés conservar
modelos = {
    "auth.group",
    "auth.user",
    "reclamos.estadoreclamo",
    "reclamos.tiporeclamo"
}

# filtrar
filtrado = [obj for obj in data if obj["model"] in modelos]

# guardar nuevo archivo
with open("datos_filtrados.json", "w", encoding="utf-8") as f:
    json.dump(filtrado, f, indent=2, ensure_ascii=False)

print("Archivo generado: datos_filtrados.json")