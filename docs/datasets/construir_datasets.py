"""Construye los 3 datasets del proyecto a partir de fuentes públicas reales.

Responsable: Fernando.
Ejecución (desde la raíz del proyecto):  python docs/datasets/construir_datasets.py

Los archivos de origen se leen por streaming EN MEMORIA y no se guardan en
disco (los de Amazon pesan cientos de MB). Solo se escriben los 3 Excel:

  1. dataset_1_intenciones_atencion_cliente.xlsx
     Bitext Customer Support (traducción al español, CDLA-Sharing-1.0),
     intenciones mapeadas a las del proyecto: envios, devoluciones, metodos_pago.
  2. dataset_2_consultas_fuera_de_dominio.xlsx
     MASSIVE es-ES de Amazon (CC BY 4.0) + intenciones de Bitext que no son de
     una tienda de ropa (cuentas, facturas...). Para el detector de rechazo (OOD).
  3. dataset_3_inventario_ventas_amazon.xlsx
     Amazon Reviews'23, categoría Amazon_Fashion (McAuley Lab, UCSD): productos
     reales con precio, y ventas tomadas de las reseñas de compra verificada.

Cada Excel trae una hoja "fuentes" con origen, licencia, fecha de obtención y
transformaciones aplicadas.
"""

import gzip
import hashlib
import io
import json
import re
import ssl
import time
import urllib.request
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

SALIDA = Path(__file__).resolve().parent
FECHA_OBTENCION = date.today().isoformat()
SEMILLA = 42
TASA_BOB_USD = 6.96  # tipo de cambio oficial del Banco Central de Bolivia (Bs por USD)

# Patrones de marcadores sin rellenar que trae Bitext ("{{Order Number}}", "__cnPLACEHOLDER_0__")
MARCADOR = re.compile(r"\{\{|\}\}|PLACEHOLDER", re.IGNORECASE)


# ------------------------------------------------------------------------------
# Utilidades de descarga en memoria
# ------------------------------------------------------------------------------

def _abrir(url, timeout=300, verificar_ssl=True):
    """Abre una URL con reintentos (devuelve la respuesta sin leerla)."""
    contexto = None if verificar_ssl else ssl._create_unverified_context()
    peticion = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (proyecto academico)"})
    for intento in range(4):
        try:
            return urllib.request.urlopen(peticion, timeout=timeout, context=contexto)
        except Exception as exc:
            if intento == 3:
                raise
            print(f"   reintento {intento + 1} ({exc})")
            time.sleep(5 * (intento + 1))


def parquet_hf(dataset, split):
    """Lee un split de Hugging Face en memoria mediante su exportación a parquet."""
    urls = json.load(_abrir(f"https://huggingface.co/api/datasets/{dataset}/parquet/default/{split}", 60))
    partes = [pd.read_parquet(io.BytesIO(_abrir(u).read())) for u in urls]
    return pd.concat(partes, ignore_index=True)


def jsonl_gz_streaming(url):
    """Recorre un .jsonl.gz remoto línea por línea sin guardarlo en disco."""
    # El certificado del servidor de UCSD está vencido: solo lectura de datos públicos
    respuesta = _abrir(url, timeout=600, verificar_ssl=False)
    with gzip.GzipFile(fileobj=respuesta) as archivo:
        for linea in archivo:
            yield json.loads(linea)


def hoja_fuentes(filas):
    """Hoja de documentación: una fila por campo descriptivo."""
    return pd.DataFrame(filas, columns=["campo", "valor"])


def guardar_excel(nombre, hojas):
    """Escribe un Excel con varias hojas y ajusta el ancho de las columnas."""
    ruta = SALIDA / nombre
    with pd.ExcelWriter(ruta, engine="openpyxl") as escritor:
        for hoja, tabla in hojas.items():
            tabla.to_excel(escritor, sheet_name=hoja, index=False)
            ws = escritor.sheets[hoja]
            for columna in ws.columns:
                ancho = max(len(str(c.value or "")) for c in list(columna)[:200])
                ws.column_dimensions[columna[0].column_letter].width = min(max(ancho + 2, 10), 80)
            ws.freeze_panes = "A2"  # encabezado fijo al desplazarse
    print(f"   guardado {ruta.name} ({ruta.stat().st_size / 1e6:.1f} MB)")


# ------------------------------------------------------------------------------
# Dataset 1: intenciones de atención al cliente (Bitext en español)
# ------------------------------------------------------------------------------

BITEXT = "Faramir/Bitext-customer-support-llm-chatbot-training-dataset-spanish"
BITEXT_URL = f"https://huggingface.co/datasets/{BITEXT}"
BITEXT_ORIGINAL = "https://huggingface.co/datasets/bitext/Bitext-customer-support-llm-chatbot-training-dataset"

# Intención de Bitext -> intención del proyecto (plan, sección 3.1)
MAPEO_BITEXT = {
    "delivery_options": "envios",
    "delivery_period": "envios",
    "track_order": "envios",
    "change_shipping_address": "envios",
    "set_up_shipping_address": "envios",
    "check_refund_policy": "devoluciones",
    "get_refund": "devoluciones",
    "track_refund": "devoluciones",
    "check_payment_methods": "metodos_pago",
    "payment_issue": "metodos_pago",
}


def cargar_bitext():
    print("1) Bitext Customer Support (español) desde Hugging Face...")
    datos = parquet_hf(BITEXT, "train")
    datos["texto"] = datos["instruction"].astype(str).str.strip()
    total = len(datos)
    datos = datos[~datos["texto"].str.contains(MARCADOR)]  # quita frases con marcadores sin rellenar
    datos = datos.drop_duplicates(subset=["texto"])
    print(f"   {total} frases -> {len(datos)} sin marcadores ni duplicados")
    return datos


def construir_dataset_1(bitext):
    tabla = bitext[bitext["intent"].isin(MAPEO_BITEXT)].copy()
    tabla["intencion"] = tabla["intent"].map(MAPEO_BITEXT)
    tabla = pd.DataFrame({
        "texto": tabla["texto"],
        "intencion": tabla["intencion"],
        "rol": "cliente",
        "fuente": "externo_bitext",
        "intencion_original": tabla["intent"],
        "categoria_original": tabla["category"],
    }).sample(frac=1, random_state=SEMILLA).reset_index(drop=True)  # mezcla con semilla fija

    conteo = tabla.groupby(["intencion", "intencion_original"]).size().reset_index(name="frases")
    fuentes = hoja_fuentes([
        ("dataset", "Frases de clientes etiquetadas por intención (atención al cliente)"),
        ("uso en el proyecto", "Entrenamiento del clasificador de intenciones: aporta frases reales de 3 de las 13 intenciones"),
        ("fuente", "Bitext - Customer Service Tagged Training Dataset for LLM-based Virtual Assistants, traducción al español"),
        ("url (traducción usada)", BITEXT_URL),
        ("url (original en inglés)", BITEXT_ORIGINAL),
        ("autor original", "Bitext Innovations International, Inc. (https://www.bitext.com)"),
        ("licencia", "CDLA-Sharing-1.0 (Community Data License Agreement - Sharing): permite usar, modificar y compartir citando la fuente"),
        ("fecha de obtención", FECHA_OBTENCION),
        ("filas", len(tabla)),
        ("transformaciones", "1) se eliminaron frases con marcadores sin rellenar ({{Order Number}}, PLACEHOLDER); "
                             "2) se eliminaron duplicados; 3) se mapearon 10 intenciones de Bitext a envios, devoluciones y metodos_pago "
                             "(ver hoja 'mapeo'); 4) se mezclaron las filas con semilla 42"),
        ("limitaciones", "La traducción al español es automática (algunas frases suenan poco naturales) y el dominio es "
                         "atención al cliente general, no exclusivo de ropa. No cubre consultar_stock, consultar_precio, "
                         "consultar_tallas, saludo, despedida, horarios_ubicacion ni las intenciones de administración: "
                         "esas deben recolectarlas el grupo (columna fuente = manual o real)."),
        ("columnas", "texto, intencion, rol, fuente (formato de data/raw/intenciones.csv del plan) + intencion_original y "
                     "categoria_original de Bitext para trazabilidad"),
    ])
    guardar_excel("dataset_1_intenciones_atencion_cliente.xlsx",
                  {"frases": tabla, "mapeo": conteo, "fuentes": fuentes})
    print("   por intención:", tabla["intencion"].value_counts().to_dict())


# ------------------------------------------------------------------------------
# Dataset 2: consultas fuera de dominio (MASSIVE es-ES + resto de Bitext)
# ------------------------------------------------------------------------------

MASSIVE = "SetFit/amazon_massive_intent_es-ES"
MASSIVE_URL = f"https://huggingface.co/datasets/{MASSIVE}"
MASSIVE_ORIGINAL = "https://huggingface.co/datasets/AmazonScience/massive"

# Intenciones de MASSIVE que sí podrían ser de una tienda (se excluyen del OOD)
MASSIVE_EXCLUIDAS = {"general_greet"}


def construir_dataset_2(bitext):
    print("2) MASSIVE es-ES desde Hugging Face...")
    massive = pd.concat([parquet_hf(MASSIVE, s) for s in ["train", "validation", "test"]], ignore_index=True)
    massive = massive[~massive["label_text"].isin(MASSIVE_EXCLUIDAS)]
    massive = massive.drop_duplicates(subset=["text"])
    parte_massive = pd.DataFrame({
        "texto": massive["text"].astype(str).str.strip(),
        "categoria": massive["label_text"].str.split("_").str[0],  # escenario: alarm, weather, music...
        "dificultad": "facil",
        "fuente": "externo_massive",
        "intencion_original": massive["label_text"],
    })

    resto = bitext[~bitext["intent"].isin(MAPEO_BITEXT)]
    parte_bitext = pd.DataFrame({
        "texto": resto["texto"],
        "categoria": resto["category"].str.lower(),  # account, invoice, order, newsletter...
        "dificultad": "dificil",  # atención al cliente pero fuera de lo que responde una tienda de ropa
        "fuente": "externo_bitext",
        "intencion_original": resto["intent"],
    })

    tabla = pd.concat([parte_massive, parte_bitext], ignore_index=True)
    tabla = tabla.drop_duplicates(subset=["texto"]).sample(frac=1, random_state=SEMILLA).reset_index(drop=True)

    fuentes = hoja_fuentes([
        ("dataset", "Consultas que NO pertenecen a una tienda de ropa (fuera de dominio, OOD)"),
        ("uso en el proyecto", "Calibrar y evaluar el detector de rechazo de src/models/ood.py (formato de data/ood_val.csv: "
                               "texto, categoria, dificultad, fuente). No se usan para entrenar intenciones."),
        ("fuente 1", "MASSIVE (Multilingual Amazon SLU resource package), subconjunto es-ES"),
        ("url fuente 1", f"{MASSIVE_URL} (copia de {MASSIVE_ORIGINAL})"),
        ("autor fuente 1", "Amazon Science. FitzGerald et al. (2022), MASSIVE: A 1M-Example Multilingual Natural Language "
                           "Understanding Dataset with 51 Typologically-Diverse Languages, arXiv:2204.08582"),
        ("licencia fuente 1", "CC BY 4.0"),
        ("fuente 2", "Bitext Customer Support en español: intenciones que no responde una tienda de ropa (cuentas, facturas, "
                     "contraseñas, boletín, quejas, pedidos)"),
        ("url fuente 2", BITEXT_URL),
        ("licencia fuente 2", "CDLA-Sharing-1.0"),
        ("fecha de obtención", FECHA_OBTENCION),
        ("filas", len(tabla)),
        ("dificultad", "facil = MASSIVE (alarmas, clima, música...: sin relación con la tienda); dificil = Bitext (atención al "
                       "cliente parecida pero fuera del alcance del chatbot, por ejemplo 'recuperar mi contraseña')"),
        ("transformaciones", f"se excluyeron de MASSIVE las intenciones {sorted(MASSIVE_EXCLUIDAS)} (saludos, que sí son del "
                             "dominio); se quitaron frases de Bitext con marcadores sin rellenar; se eliminaron duplicados; "
                             "se mezclaron las filas con semilla 42"),
    ])
    por_categoria = tabla.groupby(["fuente", "dificultad", "categoria"]).size().reset_index(name="frases")
    guardar_excel("dataset_2_consultas_fuera_de_dominio.xlsx",
                  {"consultas": tabla, "resumen": por_categoria, "fuentes": fuentes})
    print("   por dificultad:", tabla["dificultad"].value_counts().to_dict())


# ------------------------------------------------------------------------------
# Dataset 3: inventario y ventas (Amazon Reviews'23, Amazon_Fashion)
# ------------------------------------------------------------------------------

AMAZON_META = "https://mcauleylab.ucsd.edu/public_datasets/data/amazon_2023/raw/meta_categories/meta_Amazon_Fashion.jsonl.gz"
AMAZON_RESENAS = "https://mcauleylab.ucsd.edu/public_datasets/data/amazon_2023/raw/review_categories/Amazon_Fashion.jsonl.gz"
AMAZON_WEB = "https://amazon-reviews-2023.github.io/"

# Palabra clave en el título (inglés) -> categoría en español. El orden importa:
# las frases más específicas van primero ("dress shirt" antes que "dress").
CATEGORIAS = [
    (r"\bdress (shirt|pants|socks|shoes?)\b", None),  # se resuelve por la otra palabra
    (r"\b(earrings?|necklaces?|bracelets?|pendants?|anklets?|rings?|brooch|charms?)\b", "joyeria"),
    (r"\b(sneakers?|shoes?|boots?|sandals?|slippers?|loafers?|heels|pumps|flip flops?|clogs?|mules)\b", "calzado"),
    (r"\bsocks?\b", "calcetines"),
    (r"\b(bras?|bralettes?|panties|underwear|boxers?|briefs|lingerie|thongs?)\b", "ropa interior"),
    (r"\b(swimsuits?|bikinis?|swimwear|swim trunks|board shorts|rash guard)\b", "trajes de bano"),
    (r"\b(hoodies?|sweatshirts?)\b", "buzos"),
    (r"\b(sweaters?|cardigans?|pullovers?)\b", "chompas"),
    (r"\b(jackets?|coats?|parkas?|windbreakers?|blazers?|vests?)\b", "abrigos"),
    (r"\b(t-shirts?|tees?|tank tops?|camisoles?|crop tops?)\b", "poleras"),
    (r"\b(shirts?|blouses?|button[- ]down|polos?)\b", "camisas"),
    (r"\b(jeans|denim)\b", "jeans"),
    (r"\bshorts\b", "shorts"),
    (r"\b(pants|trousers|leggings|joggers|sweatpants|overalls)\b", "pantalones"),
    (r"\bskirts?\b", "faldas"),
    (r"\b(dress|dresses|gowns?|jumpsuits?|rompers?)\b", "vestidos"),
    (r"\b(hats?|caps?|beanies?|scarf|scarves|gloves?|belts?|wallets?|handbags?|bags?|backpacks?|sunglasses|ties?)\b", "accesorios"),
]
CATEGORIAS = [(re.compile(p, re.IGNORECASE), c) for p, c in CATEGORIAS]

TALLAS = {"xs": "XS", "x-small": "XS", "small": "S", "s": "S", "medium": "M", "m": "M", "large": "L", "l": "L",
          "x-large": "XL", "xl": "XL", "xx-large": "XXL", "xxl": "XXL", "2xl": "XXL", "3xl": "XXXL", "xxx-large": "XXXL",
          "one size": "UNICA"}
# Último paréntesis del título con forma "(Color, Talla)": "(Flower Mix Blue, XL)"
PARENTESIS = re.compile(r"\(([^()]+),\s*([^()]+)\)\s*$")

# Colores en inglés que aparecen en los títulos -> español (mismo vocabulario que src/nlp/entidades.py)
COLORES = {
    "black": "negro", "white": "blanco", "ivory": "blanco", "navy": "azul", "blue": "azul", "red": "rojo",
    "burgundy": "rojo", "wine": "rojo", "green": "verde", "olive": "verde", "yellow": "amarillo", "gray": "gris",
    "grey": "gris", "charcoal": "gris", "pink": "rosado", "brown": "café", "coffee": "café", "beige": "beige",
    "khaki": "beige", "tan": "beige", "purple": "morado", "lavender": "morado",
}
COLOR_TITULO = re.compile(r"\b(" + "|".join(COLORES) + r")\b", re.IGNORECASE)

# Nombre de prenda en español por categoría, para armar el nombre del producto
PRENDA_ES = {
    "poleras": "Polera", "vestidos": "Vestido", "calzado": "Calzado", "camisas": "Camisa", "abrigos": "Chaqueta",
    "buzos": "Buzo", "pantalones": "Pantalón", "ropa interior": "Ropa interior", "calcetines": "Calcetines",
    "accesorios": "Accesorio", "joyeria": "Joya", "chompas": "Chompa", "shorts": "Short", "jeans": "Jeans",
    "faldas": "Falda", "trajes de bano": "Traje de baño",
}
# Para quién es la prenda, según el título en inglés (el orden importa: "women" contiene "men")
PUBLICO = [
    (re.compile(r"\b(women'?s?|womens|ladies|woman)\b", re.I), "de mujer"),
    (re.compile(r"\b(men'?s?|mens|man)\b", re.I), "de hombre"),
    (re.compile(r"\b(girls?'?s?|boys?'?s?|kids?|toddlers?|baby|little kid|big kid)\b", re.I), "infantil"),
    (re.compile(r"\bunisex\b", re.I), "unisex"),
]


def _nombre_es(categoria, titulo, marca, color):
    """'Chaqueta de mujer Carhartt rojo': nombre en español armado con datos reales del producto."""
    publico = next((texto for patron, texto in PUBLICO if patron.search(titulo)), "")
    partes = [PRENDA_ES[categoria], publico, marca, color or ""]
    return re.sub(r"\s+", " ", " ".join(p for p in partes if p)).strip()[:100]


# Máximo de productos por categoría: Amazon Fashion vende sobre todo joyería y
# accesorios; se limitan para que el catálogo se parezca a una tienda de ropa
TOPE_CATEGORIA = {"joyeria": 400, "accesorios": 400, "calcetines": 400}


def _categoria(titulo):
    """Categoría en español según palabras del título, o None si no es ropa reconocible."""
    t = titulo.lower()
    t = re.sub(r"\bdress (shirt|pants|socks|shoes?)\b", r"\1", t)  # "dress shirt" -> "shirt"
    for patron, categoria in CATEGORIAS[1:]:
        if patron.search(t):
            return categoria
    return None


def _talla_color(titulo):
    """Extrae (talla, color) del paréntesis final del título si lo tiene."""
    coincidencia = PARENTESIS.search(titulo)
    if not coincidencia:
        return None, None
    color, talla = coincidencia.group(1).strip(), coincidencia.group(2).strip()
    talla_norm = TALLAS.get(talla.lower())
    if talla_norm is None and re.fullmatch(r"\d{1,2}(\.\d)?", talla):
        talla_norm = talla  # talla numérica (pantalones, calzado)
    if talla_norm is None:
        return None, None  # el paréntesis no era (color, talla)
    return talla_norm, color.lower()[:40]


def _precio(valor):
    """'19.99' o '$19.99' -> 19.99; None si no hay precio."""
    try:
        numero = float(str(valor).replace("$", "").replace(",", "").strip())
        return numero if numero > 0 else None
    except ValueError:
        return None


def _stock_simulado(sku):
    """Stock SIMULADO y reproducible (Amazon no publica inventario): 0 a 40 unidades."""
    return int(hashlib.md5(sku.encode()).hexdigest(), 16) % 41


def construir_dataset_3(max_productos=8000, max_ventas=15000):
    print("3) Amazon Reviews'23 - metadatos de Amazon_Fashion (streaming, ~0.22 GB, no se guarda)...")
    productos = {}
    leidos = 0
    for item in jsonl_gz_streaming(AMAZON_META):
        leidos += 1
        precio = _precio(item.get("price"))
        titulo = str(item.get("title") or "").strip()
        if not precio or not titulo:
            continue
        categoria = _categoria(titulo)
        if not categoria:
            continue
        talla, _ = _talla_color(titulo)
        # Color: el primer color reconocible del título (incluido el paréntesis "(Black, XL)"),
        # traducido al español. Nombres comerciales sin traducción ("Ocean", "Havana") se descartan.
        hallado = COLOR_TITULO.search(titulo)
        color = COLORES[hallado.group(1).lower()] if hallado else None
        marca = str(item.get("store") or "").strip()[:60]
        productos[item["parent_asin"]] = {
            "sku": item["parent_asin"],
            "nombre": _nombre_es(categoria, titulo, marca, color),  # en español, derivado de datos reales
            "categoria": categoria,
            "talla": talla,
            "color": color,
            "precio": round(precio * TASA_BOB_USD, 2),
            "precio_usd": precio,
            "nombre_original": re.sub(r"\s+", " ", titulo).strip()[:200],  # título tal como lo publica Amazon
            "marca": marca,
            "valoracion_promedio": item.get("average_rating"),
            "num_valoraciones": item.get("rating_number"),
        }
    print(f"   {leidos} productos leídos -> {len(productos)} con precio y categoría de ropa reconocible")

    print("   reseñas de Amazon_Fashion (streaming, ~0.29 GB, no se guarda)...")
    ventas = defaultdict(list)
    leidas = 0
    for resena in jsonl_gz_streaming(AMAZON_RESENAS):
        leidas += 1
        if resena.get("verified_purchase") and resena.get("parent_asin") in productos:
            fecha = datetime.fromtimestamp(resena["timestamp"] / 1000, tz=timezone.utc).date().isoformat()
            ventas[resena["parent_asin"]].append((fecha, resena.get("rating")))
    print(f"   {leidas} reseñas leídas -> {sum(map(len, ventas.values()))} compras verificadas de esos productos")

    # Productos: primero los que tienen ventas (más vendidos primero), luego el resto,
    # respetando el tope por categoría
    con_ventas = sorted(ventas, key=lambda s: len(ventas[s]), reverse=True)
    sin_ventas = [s for s in productos if s not in ventas]
    por_categoria = Counter()
    elegidos = []
    for sku in con_ventas + sin_ventas:
        categoria = productos[sku]["categoria"]
        if por_categoria[categoria] >= TOPE_CATEGORIA.get(categoria, max_productos):
            continue
        por_categoria[categoria] += 1
        elegidos.append(sku)
        if len(elegidos) >= max_productos:
            break
    tabla_productos = pd.DataFrame([productos[s] for s in elegidos])
    tabla_productos.insert(6, "stock", tabla_productos["sku"].map(_stock_simulado))  # después de precio
    tabla_productos["stock_origen"] = "simulado"
    tabla_productos["fuente"] = "Amazon Reviews'23 (Amazon_Fashion)"

    # Ventas: una fila por compra verificada; se conservan las más recientes
    filas = [
        {"fecha": f, "sku": s, "cantidad": 1, "precio_unitario": productos[s]["precio"], "calificacion": r}
        for s in elegidos if s in ventas for f, r in ventas[s]
    ]
    tabla_ventas = pd.DataFrame(filas).sort_values("fecha", ascending=False).head(max_ventas)
    tabla_ventas = tabla_ventas.sort_values("fecha").reset_index(drop=True)
    tabla_ventas["fuente"] = "compra verificada (verified_purchase) en Amazon Reviews'23"

    fuentes = hoja_fuentes([
        ("dataset", "Inventario y ventas de una tienda de ropa, con productos reales de Amazon"),
        ("uso en el proyecto", "Importar en el apartado 'Inventarios y métricas' (hojas productos y ventas en el formato del "
                               "plan, sección 3.2). Alimenta las respuestas del chatbot y las analíticas. No entrena el clasificador."),
        ("fuente", "Amazon Reviews'23, categoría Amazon_Fashion (metadatos de productos y reseñas)"),
        ("url", f"{AMAZON_WEB} | {AMAZON_META} | {AMAZON_RESENAS}"),
        ("autor", "McAuley Lab, University of California San Diego"),
        ("cita", "Hou, Y., Li, J., He, Z., Yan, A., Chen, X., & McAuley, J. (2024). Bridging Language and Items for "
                 "Retrieval and Recommendation. arXiv:2403.03952"),
        ("licencia", "La página no declara una licencia explícita (© 2024 McAuley Lab); se publica para investigación. "
                     "Uso académico citando el artículo."),
        ("fecha de obtención", FECHA_OBTENCION),
        ("filas productos", len(tabla_productos)),
        ("filas ventas", len(tabla_ventas)),
        ("columnas REALES (de Amazon)", "sku (parent_asin), nombre (título del producto), marca (store), precio_usd, "
                                        "valoracion_promedio, num_valoraciones; color (primer color mencionado en el título, "
                                        "traducido al español) y talla cuando el título la trae entre paréntesis; fecha y "
                                        "calificacion de cada compra verificada"),
        ("limitación talla", "Amazon publica un producto por modelo (parent_asin) con todas sus tallas juntas, así que casi "
                             "ningún producto trae una talla concreta: la columna talla queda vacía en la mayoría."),
        ("selección", f"tope por categoría {TOPE_CATEGORIA} (Amazon Fashion vende sobre todo joyería y accesorios); "
                      "dentro de cada categoría se priorizan los productos con más compras verificadas"),
        ("idioma", "Amazon publica los títulos en inglés. La columna nombre está en español y se arma con datos reales "
                   "del producto: tipo de prenda + público (mujer/hombre/infantil, según el título) + marca + color. "
                   "El título original queda en la columna nombre_original para verificar contra la fuente."),
        ("columnas DERIVADAS", f"nombre (ver 'idioma'); categoria: traducida al español a partir de palabras del título (dress -> vestidos...); "
                               f"precio y precio_unitario: precio_usd x {TASA_BOB_USD} Bs (tipo de cambio oficial del BCB)"),
        ("columna SIMULADA", "stock: Amazon no publica inventario. Valor reproducible de 0 a 40 calculado con un hash del sku "
                             "(columna stock_origen = simulado). Reemplazar por el stock real de la tienda si se tiene."),
        ("supuestos de ventas", "cada reseña con compra verificada se toma como una venta de 1 unidad; es un mínimo (no todos "
                                "los compradores escriben reseña). El precio_unitario es el precio de catálogo actual, no el "
                                "pagado en esa fecha (Amazon no lo publica). Se conservan las ventas más recientes."),
        ("transformaciones", "solo productos con precio y con una categoría de ropa reconocible en el título; nombre sin el "
                             "paréntesis final y recortado a 120 caracteres"),
    ])
    resumen = tabla_productos.groupby("categoria").agg(productos=("sku", "count"), precio_promedio_bs=("precio", "mean")).round(2).reset_index()
    guardar_excel("dataset_3_inventario_ventas_amazon.xlsx",
                  {"productos": tabla_productos, "ventas": tabla_ventas, "resumen_categorias": resumen, "fuentes": fuentes})


if __name__ == "__main__":
    inicio = time.time()
    bitext = cargar_bitext()
    construir_dataset_1(bitext)
    construir_dataset_2(bitext)
    construir_dataset_3()
    print(f"Listo en {time.time() - inicio:.0f} s")
