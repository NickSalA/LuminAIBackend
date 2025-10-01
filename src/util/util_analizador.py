# Cliente para Azure Document Intelligence
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

# Helpers propios
from src.util.util_credenciales import obtenerAPI

nombre_servicio = "sopport-di" # CAMBIAR NOMBRE

def conectarDocumentIntelligence():
    return DocumentAnalysisClient(
        endpoint=f"https://{nombre_servicio}.cognitiveservices.azure.com/",
        credential=AzureKeyCredential(obtenerAPI("CONF-AZURE-FORM-RECOGNIZER-KEY")),
    )