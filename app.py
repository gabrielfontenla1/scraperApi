from flask import Flask, request, jsonify, Response, send_file
from flask_cors import CORS
import json
import time
import threading
import uuid
import pandas as pd
import io
from datetime import datetime
from serpapi import Client
from config import ProductionConfig, DevelopmentConfig
import os

app = Flask(__name__)

# Load configuration based on environment
if os.environ.get('FLASK_ENV') == 'production':
    app.config.from_object(ProductionConfig())
else:
    app.config.from_object(DevelopmentConfig())

# Configure CORS with more specific settings
CORS(app, resources={
    r"/*": {
        "origins": [
            "http://localhost:3000",
            "http://localhost:3001",
            "https://*.vercel.app",  # Allow all Vercel preview deployments
            os.environ.get('CORS_ORIGINS', '*')  # Allow custom origins from environment
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Type", "Content-Disposition"],
        "supports_credentials": True
    }
})

tareas_activas = {}

COUNTRIES_DATA = [
    {
        "code": "AR",
        "name": "Argentina",
        "flag": "🇦🇷",
        "divisionType": "Provincias",
        "provinces": [
            "Buenos Aires", "Catamarca", "Chaco", "Chubut", "Córdoba", "Corrientes",
            "Entre Ríos", "Formosa", "Jujuy", "La Pampa", "La Rioja", "Mendoza",
            "Misiones", "Neuquén", "Río Negro", "Salta", "San Juan", "San Luis",
            "Santa Cruz", "Santa Fe", "Santiago del Estero", "Tierra del Fuego",
            "Tucumán", "Ciudad Autónoma de Buenos Aires"
        ]
    },
    {
        "code": "BO",
        "name": "Bolivia",
        "flag": "🇧🇴",
        "divisionType": "Departamentos",
        "provinces": ["La Paz", "Cochabamba", "Santa Cruz", "Potosí", "Chuquisaca", "Tarija", "Oruro", "Beni", "Pando"]
    },
    {
        "code": "BR",
        "name": "Brasil",
        "flag": "🇧🇷",
        "divisionType": "Estados",
        "provinces": [
            "Acre", "Alagoas", "Amapá", "Amazonas", "Bahía", "Ceará", "Distrito Federal",
            "Espírito Santo", "Goiás", "Maranhão", "Mato Grosso", "Mato Grosso do Sul",
            "Minas Gerais", "Pará", "Paraíba", "Paraná", "Pernambuco", "Piauí",
            "Río de Janeiro", "Rio Grande do Norte", "Rio Grande do Sul", "Rondônia",
            "Roraima", "Santa Catarina", "São Paulo", "Sergipe", "Tocantins"
        ]
    },
    {
        "code": "CL",
        "name": "Chile",
        "flag": "🇨🇱",
        "divisionType": "Regiones",
        "provinces": [
            "Arica y Parinacota", "Tarapacá", "Antofagasta", "Atacama", "Coquimbo",
            "Valparaíso", "Metropolitana de Santiago", "O'Higgins", "Maule", "Ñuble",
            "Biobío", "La Araucanía", "Los Ríos", "Los Lagos", "Aysén", "Magallanes y Antártica Chilena"
        ]
    },
    {
        "code": "CO",
        "name": "Colombia",
        "flag": "🇨🇴",
        "divisionType": "Departamentos",
        "provinces": [
            "Amazonas", "Antioquia", "Arauca", "Atlántico", "Bolívar", "Boyacá", "Caldas",
            "Caquetá", "Casanare", "Cauca", "Cesar", "Chocó", "Córdoba", "Cundinamarca",
            "Guainía", "Guaviare", "Huila", "La Guajira", "Magdalena", "Meta", "Nariño",
            "Norte de Santander", "Putumayo", "Quindío", "Risaralda", "San Andrés y Providencia",
            "Santander", "Sucre", "Tolima", "Valle del Cauca", "Vaupés", "Vichada", "Bogotá D.C."
        ]
    },
    {
        "code": "CR",
        "name": "Costa Rica",
        "flag": "🇨🇷",
        "divisionType": "Provincias",
        "provinces": ["San José", "Alajuela", "Cartago", "Heredia", "Guanacaste", "Puntarenas", "Limón"]
    },
    {
        "code": "CU",
        "name": "Cuba",
        "flag": "🇨🇺",
        "divisionType": "Provincias",
        "provinces": [
            "Pinar del Río", "Artemisa", "La Habana", "Mayabeque", "Matanzas", "Villa Clara",
            "Cienfuegos", "Sancti Spíritus", "Ciego de Ávila", "Camagüey", "Las Tunas",
            "Holguín", "Granma", "Santiago de Cuba", "Guantánamo", "Isla de la Juventud"
        ]
    },
    {
        "code": "EC",
        "name": "Ecuador",
        "flag": "🇪🇨",
        "divisionType": "Provincias",
        "provinces": [
            "Azuay", "Bolívar", "Cañar", "Carchi", "Chimborazo", "Cotopaxi", "El Oro",
            "Esmeraldas", "Galápagos", "Guayas", "Imbabura", "Loja", "Los Ríos", "Manabí",
            "Morona Santiago", "Napo", "Orellana", "Pastaza", "Pichincha", "Santa Elena",
            "Santo Domingo de los Tsáchilas", "Sucumbíos", "Tungurahua", "Zamora Chinchipe"
        ]
    },
    {
        "code": "SV",
        "name": "El Salvador",
        "flag": "🇸🇻",
        "divisionType": "Departamentos",
        "provinces": [
            "Ahuachapán", "Cabañas", "Chalatenango", "Cuscatlán", "La Libertad", "La Paz",
            "La Unión", "Morazán", "San Miguel", "San Salvador", "San Vicente", "Santa Ana",
            "Sonsonate", "Usulután"
        ]
    },
    {
        "code": "ES",
        "name": "España",
        "flag": "🇪🇸",
        "divisionType": "Comunidades Autónomas",
        "provinces": [
            "Andalucía", "Aragón", "Asturias", "Baleares", "Canarias", "Cantabria",
            "Castilla-La Mancha", "Castilla y León", "Cataluña", "Comunidad Valenciana",
            "Extremadura", "Galicia", "La Rioja", "Madrid", "Murcia", "Navarra",
            "País Vasco", "Ceuta", "Melilla"
        ]
    },
    {
        "code": "GT",
        "name": "Guatemala",
        "flag": "🇬🇹",
        "divisionType": "Departamentos",
        "provinces": [
            "Alta Verapaz", "Baja Verapaz", "Chimaltenango", "Chiquimula", "El Progreso",
            "Escuintla", "Guatemala", "Huehuetenango", "Izabal", "Jalapa", "Jutiapa",
            "Petén", "Quetzaltenango", "Quiché", "Retalhuleu", "Sacatepéquez", "San Marcos",
            "Santa Rosa", "Sololá", "Suchitepéquez", "Totonicapán", "Zacapa"
        ]
    },
    {
        "code": "HN",
        "name": "Honduras",
        "flag": "🇭🇳",
        "divisionType": "Departamentos",
        "provinces": [
            "Atlántida", "Choluteca", "Colón", "Comayagua", "Copán", "Cortés", "El Paraíso",
            "Francisco Morazán", "Gracias a Dios", "Intibucá", "Islas de la Bahía", "La Paz",
            "Lempira", "Ocotepeque", "Olancho", "Santa Bárbara", "Valle", "Yoro"
        ]
    },
    {
        "code": "MX",
        "name": "México",
        "flag": "🇲🇽",
        "divisionType": "Estados",
        "provinces": [
            "Aguascalientes", "Baja California", "Baja California Sur", "Campeche", "Chiapas",
            "Chihuahua", "Ciudad de México", "Coahuila", "Colima", "Durango", "Estado de México",
            "Guanajuato", "Guerrero", "Hidalgo", "Jalisco", "Michoacán", "Morelos", "Nayarit",
            "Nuevo León", "Oaxaca", "Puebla", "Querétaro", "Quintana Roo", "San Luis Potosí",
            "Sinaloa", "Sonora", "Tabasco", "Tamaulipas", "Tlaxcala", "Veracruz", "Yucatán", "Zacatecas"
        ]
    },
    {
        "code": "NI",
        "name": "Nicaragua",
        "flag": "🇳🇮",
        "divisionType": "Departamentos",
        "provinces": [
            "Boaco", "Carazo", "Chinandega", "Chontales", "Estelí", "Granada", "Jinotega",
            "León", "Madriz", "Managua", "Masaya", "Matagalpa", "Nueva Segovia", "Río San Juan",
            "Rivas", "Costa Caribe Norte", "Costa Caribe Sur"
        ]
    },
    {
        "code": "PA",
        "name": "Panamá",
        "flag": "🇵🇦",
        "divisionType": "Provincias",
        "provinces": [
            "Panamá", "Colón", "Chiriquí", "Coclé", "Herrera", "Los Santos", "Veraguas",
            "Bocas del Toro", "Darién", "Panamá Oeste", "Comarca Guna Yala", "Comarca Emberá-Wounaan",
            "Comarca Ngäbe-Buglé"
        ]
    },
    {
        "code": "PY",
        "name": "Paraguay",
        "flag": "🇵🇾",
        "divisionType": "Departamentos",
        "provinces": [
            "Alto Paraguay", "Alto Paraná", "Amambay", "Boquerón", "Caaguazú", "Caazapá",
            "Canindeyú", "Central", "Concepción", "Cordillera", "Guairá", "Itapúa",
            "Misiones", "Ñeembucú", "Paraguarí", "Presidente Hayes", "San Pedro", "Asunción"
        ]
    },
    {
        "code": "PE",
        "name": "Perú",
        "flag": "🇵🇪",
        "divisionType": "Departamentos",
        "provinces": [
            "Amazonas", "Áncash", "Apurímac", "Arequipa", "Ayacucho", "Cajamarca", "Callao",
            "Cusco", "Huancavelica", "Huánuco", "Ica", "Junín", "La Libertad", "Lambayeque",
            "Lima", "Loreto", "Madre de Dios", "Moquegua", "Pasco", "Piura", "Puno",
            "San Martín", "Tacna", "Tumbes", "Ucayali"
        ]
    },
    {
        "code": "DO",
        "name": "República Dominicana",
        "flag": "🇩🇴",
        "divisionType": "Provincias",
        "provinces": [
            "Azua", "Bahoruco", "Barahona", "Dajabón", "Distrito Nacional", "Duarte",
            "Elías Piña", "El Seibo", "Espaillat", "Hato Mayor", "Hermanas Mirabal",
            "Independencia", "La Altagracia", "La Romana", "La Vega", "María Trinidad Sánchez",
            "Monseñor Nouel", "Monte Cristi", "Monte Plata", "Pedernales", "Peravia",
            "Puerto Plata", "Samaná", "San Cristóbal", "San José de Ocoa", "San Juan",
            "San Pedro de Macorís", "Sánchez Ramírez", "Santiago", "Santiago Rodríguez",
            "Santo Domingo", "Valverde"
        ]
    },
    {
        "code": "UY",
        "name": "Uruguay",
        "flag": "🇺🇾",
        "divisionType": "Departamentos",
        "provinces": [
            "Artigas", "Canelones", "Cerro Largo", "Colonia", "Durazno", "Flores",
            "Florida", "Lavalleja", "Maldonado", "Montevideo", "Paysandú", "Río Negro",
            "Rivera", "Rocha", "Salto", "San José", "Soriano", "Tacuarembó", "Treinta y Tres"
        ]
    },
    {
        "code": "VE",
        "name": "Venezuela",
        "flag": "🇻🇪",
        "divisionType": "Estados",
        "provinces": [
            "Amazonas", "Anzoátegui", "Apure", "Aragua", "Barinas", "Bolívar", "Carabobo",
            "Cojedes", "Delta Amacuro", "Distrito Capital", "Falcón", "Guárico", "Lara",
            "Mérida", "Miranda", "Monagas", "Nueva Esparta", "Portuguesa", "Sucre",
            "Táchira", "Trujillo", "Vargas", "Yaracuy", "Zulia"
        ]
    }
]

COUNTRY_CODES = {c["name"]: c["code"].lower() for c in COUNTRIES_DATA}

def get_country_data(identifier: str):
    identifier = identifier.lower()
    for c in COUNTRIES_DATA:
        if c["name"].lower() == identifier or c["code"].lower() == identifier:
            return c
    return None

def validar_config(cfg: dict):
    obligatorios = ["apiKey", "query", "country", "provinces"]
    faltan = [k for k in obligatorios if not cfg.get(k)]
    if faltan:
        raise ValueError(f"Faltan campos obligatorios: {', '.join(faltan)}")

    if not isinstance(cfg["provinces"], list) or not cfg["provinces"]:
        raise ValueError("«provinces» debe ser una lista con al menos un valor")

    if not get_country_data(cfg["country"]):
        raise ValueError(f"País «{cfg['country']}» no soportado")

def scrape_odontologos(cfg: dict, task_id: str):
    try:
        tareas_activas[task_id].update(
            status="processing",
            started_at=datetime.now().isoformat()
        )

        api_key   = cfg["apiKey"]
        query     = cfg["query"]
        country   = cfg["country"]
        provinces = cfg["provinces"]
        delay     = float(cfg.get("delay", 1.5))

        client = Client(api_key=api_key)
        country_data = get_country_data(country)
        country_cc   = country_data["code"].lower()

        datos_por_prov = {p: [] for p in provinces}
        vistos         = set()
        total          = 0

        for idx, prov in enumerate(provinces, 1):
            tareas_activas[task_id]["current_province"] = prov
            tareas_activas[task_id]["progress"] = f"{idx}/{len(provinces)}"

            start = 0
            agregados = 0
            while True:
                params = {
                    "engine": "google_local",
                    "type": "search",
                    "q": query,
                    "location": prov,  # Remove the country to avoid mixing results
                    "hl": "es",
                    "gl": country_cc,
                    "start": start,
                    "api_key": api_key,
                    "location_requested": True,  # Force location-based results
                    "location_used": True       # Ensure location is respected
                }

                try:
                    rsp = client.search(params)
                    resultados = rsp.get("local_results", [])
                    
                    if not resultados:
                        if start == 0:  # Only add warning if no results on first page
                            tareas_activas[task_id]["warnings"].append(
                                f"{prov}: No se encontraron resultados para esta búsqueda.")
                        break

                    for r in resultados:
                        # Verify the result is from the correct province
                        address = r.get("address", "").lower()
                        if not address or prov.lower() not in address.lower():
                            continue  # Skip results from other provinces
                            
                        pid = r.get("place_id")
                        if pid and pid not in vistos:
                            vistos.add(pid)
                            datos_por_prov[prov].append({
                                "place_id": pid,
                                "title": r.get("title", ""),
                                "address": r.get("address", ""),
                                "phone": r.get("phone", ""),
                                "website": r.get("website", ""),
                                "rating": r.get("rating"),
                                "reviews": r.get("reviews"),
                                "type": r.get("type", ""),
                                "hours": r.get("hours", {}),
                                "gps_coordinates": r.get("gps_coordinates", {}),
                                "province": prov
                            })
                            agregados += 1
                            total += 1

                    if not rsp.get("serpapi_pagination", {}).get("next"):
                        break

                    start += 20
                    time.sleep(delay)

                except Exception as e:
                    tareas_activas[task_id]["warnings"].append(
                        f"{prov}: Error al procesar resultados - {str(e)}")
                    break

            tareas_activas[task_id]["provinces_completed"].append(
                {"name": prov, "count": agregados}
            )

        tareas_activas[task_id].update(
            status="completed",
            completed_at=datetime.now().isoformat(),
            results=datos_por_prov,
            total_records=total
        )

    except Exception as e:
        tareas_activas[task_id].update(
            status="error",
            error=str(e),
            completed_at=datetime.now().isoformat()
        )

@app.route('/scrape', methods=['POST'])
def iniciar_scraping():
    if not request.is_json:
        return jsonify(error="Content-Type debe ser application/json"), 400
    cfg = request.get_json()

    try:
        validar_config(cfg)
    except ValueError as e:
        return jsonify(error=str(e)), 400

    task_id = str(uuid.uuid4())
    tareas_activas[task_id] = {
        "task_id": task_id,
        "status": "initiated",
        "created_at": datetime.now().isoformat(),
        "config": cfg,
        "current_province": None,
        "progress": "0/0",
        "provinces_completed": [],
        "warnings": [],
        "results": {},
        "total_records": 0
    }

    threading.Thread(
        target=scrape_odontologos, args=(cfg, task_id), daemon=True
    ).start()

    return jsonify(
        message="Scraping iniciado",
        task_id=task_id,
        status_url=f"/status/{task_id}",
        results_url=f"/results/{task_id}"
    ), 202

@app.route('/status/<task_id>')
def obtener_status(task_id):
    t = tareas_activas.get(task_id)
    if not t:
        return jsonify(error="Tarea no encontrada"), 404
    t = t.copy()
    t.pop("results", None)
    return jsonify(t)

@app.route('/results/<task_id>')
def obtener_resultados(task_id):
    t = tareas_activas.get(task_id)
    if not t:
        return jsonify(error="Tarea no encontrada"), 404
    if t["status"] != "completed":
        return jsonify(error="Tarea no completada aún", status=t["status"]), 400
    return jsonify(
        task_id=task_id,
        status=t["status"],
        total_records=t["total_records"],
        provinces_completed=t["provinces_completed"],
        warnings=t["warnings"],
        results=t["results"]
    )

@app.route('/results/<task_id>/download')
def download_json(task_id):
    t = tareas_activas.get(task_id)
    if not t:
        return jsonify(error="Tarea no encontrada"), 404
    if t["status"] != "completed":
        return jsonify(error="Tarea no completada aún", status=t["status"]), 400

    # Get the requested format from query parameters, default to json
    format_type = request.args.get('format', 'json')

    if format_type == 'json':
        return Response(
            json.dumps(t["results"], ensure_ascii=False, indent=2),
            mimetype="application/json",
            headers={"Content-Disposition":
                     f"attachment; filename=odontologos_{task_id}.json"}
        )
    elif format_type == 'excel':
        # Convert the nested dictionary to a flat list of records
        records = []
        for province, items in t["results"].items():
            for item in items:
                item['province'] = province  # Add province to each record
                records.append(item)
        
        # Convert to DataFrame
        df = pd.DataFrame(records)
        
        # Reorder columns to put important info first
        columns_order = ['province', 'title', 'address', 'phone', 'website', 'rating', 
                        'reviews', 'type', 'place_id']
        other_columns = [col for col in df.columns if col not in columns_order]
        final_columns = columns_order + other_columns
        
        # Reorder and rename columns for better readability
        df = df[final_columns]
        column_names = {
            'province': 'Provincia',
            'title': 'Nombre',
            'address': 'Dirección',
            'phone': 'Teléfono',
            'website': 'Sitio Web',
            'rating': 'Calificación',
            'reviews': 'Reseñas',
            'type': 'Tipo',
            'place_id': 'ID de Google'
        }
        df = df.rename(columns=column_names)
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Resultados')
            
            # Auto-adjust columns width
            worksheet = writer.sheets['Resultados']
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).apply(len).max(),
                    len(str(col))
                ) + 2
                worksheet.column_dimensions[chr(65 + idx)].width = max_length
        
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'odontologos_{task_id}.xlsx'
        )
    else:
        return jsonify(error="Formato no soportado"), 400

@app.route('/tasks')
def listar_tareas():
    return jsonify(tasks=[
        {
            "task_id": tid,
            "status": t["status"],
            "created_at": t["created_at"],
            "progress": t["progress"],
            "total_records": t.get("total_records", 0)
        }
        for tid, t in tareas_activas.items()
    ])

@app.route('/countries')
def listar_paises():
    return jsonify(countries=COUNTRIES_DATA)

@app.route('/provinces/<country>')
def listar_provincias(country):
    cd = get_country_data(country)
    if not cd:
        return jsonify(
            error=f"País «{country}» no encontrado",
            available=[c["name"] for c in COUNTRIES_DATA]
        ), 404
    return jsonify(country=cd["name"], provinces=cd["provinces"])

@app.route('/health')
def health():
    return jsonify(
        status="healthy",
        active_tasks=len(tareas_activas),
        supported_countries=len(COUNTRIES_DATA)
    )

@app.route('/')
def doc():
    return jsonify(
        name="API Scraper ",
        version="1.0.0",
        endpoints={
            "POST /scrape": "Inicia scraping",
            "GET /status/<id>": "Estado de la tarea",
            "GET /results/<id>": "Resultados completos",
            "GET /results/<id>/download": "Descargar JSON",
            "GET /tasks": "Lista tareas",
            "GET /countries": "Lista países",
            "GET /provinces/<country>": "Lista provincias por país",
            "GET /health": "Health check"
        },
        example_request={
            "apiKey": "tu_serpapi_key",
            "query": "odontologos OR dentistas",
            "country": "Argentina",
            "provinces": ["Buenos Aires", "Córdoba"],
            "delay": 1.5
        }
    )

if __name__ == '__main__':
    print(f"🚀 API Scraper corriendo en http://localhost:{app.config['PORT']}/")
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )
