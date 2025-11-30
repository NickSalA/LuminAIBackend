# ##########################
# ETAPA 1: BUILDER
# ##########################
FROM python:3.12-slim AS builder

WORKDIR /app

# Instalamos herramientas necesarias para construir (git, compiladores, etc.)
RUN apt-get update && apt-get install -y git

# Configuramos Pipenv para que cree el entorno virtual DENTRO de la carpeta del proyecto
# Esto es clave para poder copiarlo después fácilmente.
ENV PIPENV_VENV_IN_PROJECT=1

COPY Pipfile Pipfile.lock ./

# Instalamos pipenv y las dependencias en el .venv
RUN pip install pipenv && \
    pipenv install --deploy

# ##########################
# ETAPA 2: RUNNER (Final)
# ##########################
FROM python:3.12-slim AS runner

WORKDIR /app

# TRUCO DE MAGIA:
# Copiamos la carpeta .venv desde la etapa "builder".
# Ya contiene todas las librerías instaladas.
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

COPY .wallet/ app/wallet    

# Copiamos el código fuente de tu app
COPY . .

ENV ORACLE_WALLET_PATH=/app/wallet

EXPOSE 8000

# Ejecutamos uvicorn directamente (ya está en el PATH gracias a la línea de ENV)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]