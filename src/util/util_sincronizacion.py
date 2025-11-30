# Utilitarios para sincronización de documentos con Azure Cognitive Search
import os
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any
import shutil
import re
# Azure Document Intelligence
from azure.ai.formrecognizer import DocumentAnalysisClient

# LangChain splitter (mejor que CharacterTextSplitter para RAG)
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Helpers propios
from src.util.util_analizador import conectarDocumentIntelligence
from src.util.util_retriever import conectarBaseDeConocimientos

# -------------------------------
# Utilitarios
# -------------------------------
def obtenerArchivos(ruta: str = "") -> List[str]:
    if not ruta or not os.path.isdir(ruta):
        return []
    archivos = []
    for elemento in os.listdir(ruta):
        ruta_completa = os.path.join(ruta, elemento)
        if os.path.isfile(ruta_completa):
            archivos.append(ruta_completa)
    return archivos

def _file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(8192), b""):
            h.update(b)
    return h.hexdigest()

def limpiar_texto(texto: str) -> str:
    """
    Limpia 'basura' común de PDFs extraídos, como saltos de línea CSV (\r\n)
    o comillas excesivas generadas por tablas mal interpretadas.
    """
    if not texto:
        return ""
    # Reemplazar retornos de carro
    texto = texto.replace("\r", " ")
    # Eliminar comillas dobles excesivas que a veces aparecen en celdas
    texto = texto.replace('""', '"')
    # Colapsar espacios múltiples y saltos de línea excesivos
    texto = re.sub(r'\n{3,}', '\n\n', texto)
    texto = re.sub(r' {2,}', ' ', texto)
    return texto.strip()

def _split_text(texto: str, max_chars: int = 1000, overlap: int = 100) -> List[str]:
    splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", ". ", " ", ""],
        chunk_size=max_chars,
        chunk_overlap=overlap,
    )
    return splitter.split_text(texto)

def _extraer_iterable_resultados(resultados: Any):
    """
    Devuelve un iterable de resultados individuales (IndexingResult)
    soportando:
        - IndexDocumentsResult.results (SDK Azure)
        - Lista de dicts con claves como 'succeeded', 'key', 'errorMessage'
    """
    if hasattr(resultados, "results"):
        return resultados.results
    if isinstance(resultados, list):
        return resultados
    return None  # estructura desconocida

def _resumen_subida(resultados: Any) -> Dict[str, Any] | None:
    """
    Calcula totales OK/FAIL. Si la estructura es desconocida, devuelve None.
    """
    it = _extraer_iterable_resultados(resultados)
    if it is None:
        return None

    total = 0
    ok = 0
    fail = 0
    detalles = []
    for r in it:
        # soporta objeto o dict
        succeeded = (
            getattr(r, "succeeded", None)
            if not isinstance(r, dict)
            else r.get("succeeded")
        )
        key = getattr(r, "key", None) if not isinstance(r, dict) else r.get("key")
        err = (
            getattr(r, "error_message", None)
            if not isinstance(r, dict)
            else r.get("errorMessage") or r.get("error_message")
        )

        total += 1
        if succeeded is True:
            ok += 1
        else:
            fail += 1
            detalles.append({"key": key, "error": err})

    return {"total": total, "ok": ok, "fail": fail, "detalles": detalles}

# -------------------------------
# 1) Lectura del documento (orden lógico + páginas)
# -------------------------------
def leerContenidoDeDocumento(rutaArchivo: str):
    """
    Versión compatible con azure-ai-formrecognizer 3.3.3
    Usa 'prebuilt-layout' para mejor detección de estructura visual,
    pero sin el parámetro de markdown que causa el error.
    """
    servicio: DocumentAnalysisClient = conectarDocumentIntelligence()
    
    with open(rutaArchivo, "rb") as archivo:
        # 1. ERROR SOLUCIONADO: Quitamos 'output_content_format'
        # Usamos prebuilt-layout, que es más inteligente que 'read' para tablas
        poller = servicio.begin_analyze_document("prebuilt-layout", archivo)
        resultado = poller.result()

    full_text = resultado.content or ""
    parrafos: List[Dict[str, Any]] = []

    # 2. Extracción Robusta:
    # Iteramos por páginas y luego por líneas. El modelo 'layout' agrupa
    # las líneas visualmente mucho mejor que el modelo 'read'.
    for page in resultado.pages:
        lines_content = []
        
        # Recolectamos el texto línea por línea
        if hasattr(page, 'lines'):
            for line in page.lines:
                lines_content.append(line.content)
        
        # Unimos con salto de línea. 
        # Esto suele preservar la estructura de listas y párrafos mejor.
        page_text = "\n".join(lines_content)
        
        # Solo guardamos si la página tiene texto
        if page_text.strip():
            parrafos.append({
                "text": page_text, 
                "page": page.page_number
            })

    # Fallback: Si por alguna razón extraña no hay páginas detectadas pero sí texto global
    if not parrafos and full_text:
         parrafos.append({"text": full_text, "page": 1})

    return full_text, parrafos

# -------------------------------
# 2) Chunking con metadatos
# -------------------------------
def obtenerChunksDesdeParrafos(
    parrafos: List[Dict[str, Any]],
    rutaArchivo: str,
    title: str | None = None,
    level: str = "",
    tags: List[str] | None = None,
) -> List[Dict[str, Any]]:
    
    # Generar metadatos base
    parent_id = _file_sha256(rutaArchivo)[:16]
    updated_at = datetime.fromtimestamp(
        os.path.getmtime(rutaArchivo), tz=timezone.utc
    ).isoformat()
    title = title or os.path.basename(rutaArchivo)
    # Si 'level' viene vacío, usa el nombre de la carpeta padre
    level = level or os.path.basename(os.path.dirname(rutaArchivo))
    tags = tags or []

    chunks: List[Dict[str, Any]] = []
    chunk_index = 0

    # Agrupación por página (Crucial para diapositivas)
    contenido_por_pagina: Dict[Any, str] = {}
    
    for p in parrafos:
        raw_text = p.get("text") or ""
        # APLICAMOS LIMPIEZA AQUÍ
        p_text = limpiar_texto(raw_text)
        
        if not p_text:
            continue
            
        # Manejo seguro del número de página
        page_num = p.get("page")
        page_key = page_num if page_num is not None else 0 
        
        if page_key not in contenido_por_pagina:
            contenido_por_pagina[page_key] = ""
        
        contenido_por_pagina[page_key] += p_text + "\n\n"

    # Generar chunks finales
    for page_num, page_text in contenido_por_pagina.items():
        partes = _split_text(page_text)
        
        # Azure espera Int32 para 'page'. Si es 0 (indefinido), lo mandamos tal cual.
        real_page = page_num 
        
        for parte in partes:
            if len(parte) < 10: continue # Saltar fragmentos vacíos

            # Estructura EXACTA para tu índice 'lumin_index'
            chunks.append(
                {
                    "id": f"{parent_id}-{chunk_index}",
                    "parent_id": parent_id,
                    "chunk_index": chunk_index,
                    "page": int(real_page),      # Int32
                    "title": title,              # String
                    "updated_at": updated_at,    # DateTimeOffset
                    "tags": tags,                # StringCollection
                    "level": level,              # String
                    "content": parte,            # String (Searchable)
                }
            )
            chunk_index += 1

    return chunks

# -------------------------------
# 3) Carga en la base de conocimiento
# -------------------------------
def cargarArchivo(rutaDeArchivo: str = "", tags: List[str] | None = None):
    """
    Lee el PDF, genera chunks con metadatos y los sube.
    Args:
        rutaDeArchivo (str): Ruta del archivo a procesar.
        tags (List[str], optional): Lista de tags a asociar al documento. Defaults to None.
    Returns: Resultados de la operación de subida.
    """
    # 1) Leer (orden lógico + páginas)
    try:
        _, parrafos = leerContenidoDeDocumento(rutaDeArchivo)
    except Exception as e:
        raise Exception(f"Error en Document Intelligence: {e}")
    # 2) Chunkear con metadatos
    chunks = obtenerChunksDesdeParrafos(parrafos, rutaDeArchivo, tags=tags)

    # 3) Conectar a AI Search
    try: 
        baseDeConocimiento = conectarBaseDeConocimientos()
    except Exception as e:
        raise Exception(f"Error conectando a Azure Cognitive Search: {e}")
    # 4) Subir
    try:
        resultados = baseDeConocimiento.upload_documents(chunks)
    except Exception as e:
        raise Exception(f"Error subiendo a Azure Cognitive Search: {e}")
    return resultados

# -------------------------------
# 4) Procesar carpeta (borra o mueve según resultado)
# -------------------------------
def cargarArchivoDeCarpeta(
    rutaDeCarpeta: str = "",
    tags: List[str] | None = None,
    carpetaErrores: str | None = None,
) -> Dict[str, Any]:
    """
    Carga todos los archivos de una carpeta en la base de conocimientos.
    - Si la subida es 100% exitosa => borra el archivo.
    - Si hay errores (parciales o totales) => mueve a carpeta de errores.
    """
    resultados_totales: Dict[str, Any] = {}

    if not rutaDeCarpeta or not os.path.isdir(rutaDeCarpeta):
        return {"status": "ERROR", "message": f"Carpeta inválida: {rutaDeCarpeta}"}

    errores_dir = (
        carpetaErrores if carpetaErrores else os.path.join(rutaDeCarpeta, "_errores")
    )
    os.makedirs(errores_dir, exist_ok=True)

    archivos = obtenerArchivos(rutaDeCarpeta)
    if not archivos:
        return {"status": "OK", "message": "No hay archivos para procesar."}
    for archivo in archivos:
        try:
            resultados = cargarArchivo(archivo, tags=tags)

            resumen = _resumen_subida(resultados)
            # Si no pudimos interpretar, asumimos éxito (no hubo excepción)
            subida_exitosa = True if resumen is None else (resumen["fail"] == 0)

            if subida_exitosa:
                try:
                    os.remove(archivo)
                    accion = "BORRADO"
                except Exception as e_rm:
                    accion = f"NO_BORRADO: {e_rm}"
            else:
                destino = os.path.join(errores_dir, os.path.basename(archivo))
                try:
                    shutil.move(archivo, destino)
                    accion = f"MOVIDO_A_ERRORES: {destino}"
                except Exception as e_mv:
                    accion = f"NO_MOVIDO: {e_mv}"

            resultados_totales[archivo] = {
                "status": "OK" if subida_exitosa else "PARTIAL_OR_FAIL",
                "accion": accion,
                "resumen": (
                    resumen
                    if resumen is not None
                    else "estructura_resultado_desconocida"
                ),
            }
            print(f"[{resultados_totales[archivo]['status']}] {archivo} → {accion}")

        except Exception as e:
            # Error en procesamiento/carga: mover a errores
            destino = os.path.join(errores_dir, os.path.basename(archivo))
            try:
                shutil.move(archivo, destino)
                accion = f"MOVIDO_A_ERRORES: {destino}"
            except Exception as e_mv:
                accion = f"NO_MOVIDO: {e_mv}"

            resultados_totales[archivo] = {
                "status": "ERROR",
                "accion": accion,
                "message": str(e),
            }
            print(f"[ERROR] {archivo} → {accion} ({e})")

    return resultados_totales