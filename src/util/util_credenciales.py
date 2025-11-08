# Credenciales Azure
from azure.identity import DefaultAzureCredential

# Manejo de secretos en Key Vault
from azure.keyvault.secrets import SecretClient

vault_name = "keylumin" # CAMBIAR NOMBRE
KVUri = f"https://{vault_name}.vault.azure.net"

credential = DefaultAzureCredential()
client = SecretClient(vault_url=KVUri, credential=credential)

def obtenerAPI(name: str) -> str:
    secret = client.get_secret(name)
    if secret.value is None:
        raise ValueError(f"Secret '{name}' does not have a value.")
    return secret.value