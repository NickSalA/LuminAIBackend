import os
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any
import shutil

# Azure Document Intelligence
from azure.ai.formrecognizer import DocumentAnalysisClient

# LangChain splitter (mejor que CharacterTextSplitter para RAG)
from langchain.text_splitter import RecursiveCharacterTextSplitter

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
    Devuelve:
        - full_text (str): texto completo en orden lógico
        - parrafos (List[Dict]): [{'text': str, 'page': int|None}, ...]
    """
    servicio: DocumentAnalysisClient = conectarDocumentIntelligence()
    with open(rutaArchivo, "rb") as archivo:
        poller = servicio.begin_analyze_document("prebuilt-read", archivo)
        resultado = poller.result()

    full_text = resultado.content or ""

    parrafos: List[Dict[str, Any]] = []
    for p in getattr(resultado, "paragraphs", []) or []:
        if not getattr(p, "spans", None):
            continue
        span = p.spans[0]
        texto = full_text[span.offset : span.offset + span.length].strip()
        if not texto:
            continue
        page = None
        if getattr(p, "bounding_regions", None):
            page = getattr(p.bounding_regions[0], "page_number", None)
        parrafos.append({"text": texto, "page": page})

    # Fallback si no hay paragraphs (usamos pages->lines)
    if not parrafos:
        contenido: List[str] = []
        for pagina in resultado.pages:
            for linea in pagina.lines:
                contenido.append(linea.content)
        full_text = "\n".join(contenido).strip()
        parrafos = [{"text": full_text, "page": None}]

    return full_text, parrafos

# -------------------------------
# 2) Chunking con metadatos
# -------------------------------
def obtenerChunksDesdeParrafos(
    parrafos: List[Dict[str, Any]],
    rutaArchivo: str,
    title: str | None = None,
    tags: List[str] | None = None,
) -> List[Dict[str, Any]]:
    """
    Devuelve lista de dicts listos para indexar en AI Search con:
    id, parent_id, chunk_index, page, title, updated_at, tags, content
    """
    parent_id = _file_sha256(rutaArchivo)[:16]  # id estable por documento
    updated_at = datetime.fromtimestamp(
        os.path.getmtime(rutaArchivo), tz=timezone.utc
    ).isoformat()
    title = title or os.path.basename(rutaArchivo)
    tags = tags or []

    chunks: List[Dict[str, Any]] = []
    chunk_index = 0

    for p in parrafos:
        p_text = (p.get("text") or "").strip()
        if not p_text:
            continue
        page = p.get("page")
        for parte in _split_text(p_text):
            chunks.append(
                {
                    "id": f"{parent_id}-{chunk_index}",
                    "parent_id": parent_id,
                    "chunk_index": chunk_index,
                    "page": page, 
                    "title": title,
                    "updated_at": updated_at, 
                    "tags": tags,
                    "content": parte,
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