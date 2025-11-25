# src/api/usuarios_api.py
import httpx
import oracledb
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import asyncio
from datetime import datetime

# --- ¡NUEVAS IMPORTACIONES DE GOOGLE! ---
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# Importa tus utilidades
from src.db.session import get_connection
from src.core.security import (
    create_access_token, 
    get_current_user,
    GOOGLE_CLIENT_ID, 
    GOOGLE_CLIENT_SECRET, 
    GOOGLE_REDIRECT_URI
)
from src.util.util_schemas import (UserMetrics, CalificationJson)

# Constantes (igual que antes)
AGE_URL = "https://people.googleapis.com/v1/people/me?personFields=birthdays"
NAME_EMAIL_URL = "https://www.googleapis.com/userinfo/v2/me"

routerUsuarios = APIRouter()

# --- Modelos Pydantic (igual que antes) ---
class GoogleAuthCode(BaseModel):
    code: str

class TokenResponse(BaseModel):
    token: str
    token_type: str = "bearer"
    name : str
    email : str

class UserDataPost(BaseModel):
    id_plan : int
    
class SubscriptionResponse(BaseModel):
    message: str    
    
class UserDataGet(BaseModel):
    id: int
    username: str | None
    #userIcon: int
    email: str
    age: int | None
    lives: int | None
    newLife: datetime | None
    isPremium: bool

class LastPageResponse(BaseModel):
    id_page : int
    id_section : int
    id_level : int
    
class LastPageRequest(BaseModel):
    id_page: int

class DeleteResponse(BaseModel) :
    cod : int
    response : str

# --- Función auxiliar (igual que antes) ---
async def fetch_google_data(url: str, access_token: str, client: httpx.AsyncClient):
    headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
    try:
        response = await client.get(url, headers=headers)
        if response.status_code == 401:
            raise HTTPException(status_code=401, detail="Access Token de Google expirado o inválido.")
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Error al obtener datos de Google: {e.response.json()}")

# --- Endpoint de Autenticación (¡LÓGICA MODIFICADA!) ---
@routerUsuarios.post("/auth/google", response_model=TokenResponse)
async def google_auth(
    auth_data: GoogleAuthCode, 
    db: oracledb.Connection = Depends(get_connection)
):
    
    # --- 1. Configurar el Flujo de OAuth (como el 'new google.auth.OAuth2') ---
    # Usamos la configuración de tu .env
    client_config = {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=[ # Los scopes que definimos antes
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/user.birthday.read"
        ],
        redirect_uri=GOOGLE_REDIRECT_URI
    )

    # --- 2. Canjear el Código por Tokens (como 'oauth2Client.getToken') ---
    try:
        # Esta función hace la llamada POST a https://oauth2.googleapis.com/token
        # usando el 'code', 'client_id', 'client_secret' y 'redirect_uri'
        flow.fetch_token(code=auth_data.code)
        
        access_token_google = flow.credentials.token
        if not access_token_google:
            raise HTTPException(status_code=400, detail="No se pudo obtener el Access Token de Google.")

    except Exception as e:
        # Si las credenciales en tu .env (ID o Secret) son incorrectas,
        # ¡fallará aquí con un error 401 (invalid_client)!
        print(f"Error detallado al canjear el código: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Fallo al canjear el código (invalid_client?): {str(e)}")

    # --- 3. Obtener datos del usuario (¡igual que antes!) ---
    try:
        async with httpx.AsyncClient() as client:
            personal_data_task = fetch_google_data(NAME_EMAIL_URL, access_token_google, client)
            age_data_task = fetch_google_data(AGE_URL, access_token_google, client)
            personal_data, age_data = await asyncio.gather(personal_data_task, age_data_task)

            p_email = personal_data.get('email')
            p_google_name = personal_data.get('name')
            p_google_id = personal_data.get('id')
            
            # (Procesar age_data si es necesario)

            if not p_email or not p_google_id:
                raise HTTPException(status_code=400, detail="Google no devolvió email o ID del usuario.")

            birth_date = None
            try:
                birthdays = age_data.get('birthdays', [])
                if birthdays:
                    # Google suele devolver varias, tomamos la primera que tenga fecha completa
                    for b in birthdays:
                        date_info = b.get('date', {})
                        year = date_info.get('year')
                        month = date_info.get('month')
                        day = date_info.get('day')

                        if year and month and day:
                            # Crear objeto datetime
                            birth_date = datetime(year, month, day)
                            break
            except Exception as e:
                print(f"Advertencia: No se pudo procesar la fecha de nacimiento: {e}")
                # No fallamos el login, simplemente birth_date será None

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo datos de Google: {str(e)}")

    # --- 4. Llamar al Paquete de Oracle (¡igual que antes!) ---
    try:
        with db.cursor() as cursor:
            id_usuario_out = cursor.var(oracledb.NUMBER)
            
            cursor.callproc(
                "PKG_USER_REGISTRATION.HANDLE_GOOGLE_LOGIN",
                [p_email, p_google_name, p_google_id, birth_date,id_usuario_out]
            )
            
            id_usuario_interno = id_usuario_out.getvalue()
            
            if not id_usuario_interno:
                raise Exception("El procedimiento de login no devolvió un ID de usuario.")
        
        db.commit()

    except oracledb.DatabaseError as e:
        db.rollback() 
        raise HTTPException(status_code=500, detail=f"Error en base de datos al procesar login: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno (Oracle): {str(e)}")

    # --- 5. Creación de TU Token JWT (¡igual que antes!) ---
    access_token_propio = create_access_token(
        data={"sub": str(id_usuario_interno)} 
    )

    # --- 6. Respuesta al Frontend ---
    return TokenResponse(token=access_token_propio, name= p_google_name, email= p_email) #Esto va encriptado el JWT no lo esta
#TODO agregar edad en la respuesta

#TODO cambiar el uri del playground a la app cuando sea necesario 

@routerUsuarios.get("/user/metrics", response_model=UserMetrics)
async def fetch_user_metrichs(

        db: oracledb.Connection = Depends(get_connection),
        current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("user_id")

    try:
        with db.cursor() as cursor:
            # 1. Obtener datos del Dashboard
            sql = "SELECT * FROM V_USER_DASHBOARD WHERE ID_USER = :1"
            cursor.execute(sql, [user_id])
            row = cursor.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="Datos de dashboard no encontrados.")

            current_page_id = row[8]

            current_section_id = 0
            if current_page_id:
                current_section_id = cursor.callfunc(
                    "PKG_CONTENT.SECTION_OF_PAGE",
                    oracledb.NUMBER,
                    [current_page_id]
                )

            return UserMetrics(
                currentLevelId=row[2],
                succededSectionsCount=row[5],
                currentSectionId=current_section_id,
                currentPageId=current_page_id,
                averageScore=float(row[4]) if row[4] is not None else 0.0,
                totalPracticeRetries=row[7],
                succededDailyPracticeCount=row[13],
                totalSectionsCount=row[6]
            )

    except oracledb.DatabaseError as e:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {e}")


@routerUsuarios.get("/user/data", response_model=UserDataGet)
async def get_user_data(
        bd: oracledb.Connection = Depends(get_connection),
        current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("user_id")

    try:
        with bd.cursor() as cursor:
            sql = "SELECT * FROM V_USER_ACCOUNT_INFO WHERE ID_USER = :1"
            cursor.execute(sql, [user_id])

            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Usuario no encontrado.")

            vidas_out = cursor.var(oracledb.NUMBER)
            date_life = cursor.var(oracledb.DATETIME)

            cursor.callproc(
                "PKG_ACCOUNT.GET_LIVES_STATUS",
                [user_id, vidas_out, date_life]
            )

            membership = cursor.callfunc(
                "PKG_SUBSCRIPTION.IS_ACTIVE",
                oracledb.STRING,
                [user_id]
            )

            return UserDataGet(
                id=user_id,
                username=row[2],
                #userIcon=2131230810,
                email=row[1],
                age=2025 - row[5].year if row[5] else None,
                lives=int(vidas_out.getvalue()) if vidas_out.getvalue() is not None else 5,
                newLife=date_life.getvalue(),
                isPremium=(membership == 'S')
            )

    except oracledb.DatabaseError as e:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {e}")


@routerUsuarios.post("/users/subscription", response_model=SubscriptionResponse) 
async def register_user_subscription(
    data: UserDataPost,
    db: oracledb.Connection = Depends(get_connection),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("user_id")
    
    try:
        with db.cursor() as cursor:
            # Llamada al procedimiento
            cursor.callproc("PKG_SUBSCRIPTION.REGISTER_SUBSCRIPTION", [user_id, data.id_plan])
        
        # 2. ¡IMPORTANTE! Guardar los cambios
        db.commit()
        
        # 3. Devolver un mensaje JSON claro
        return {"message": "Suscripción registrada exitosamente"}
        
    except oracledb.DatabaseError as e:
        # 4. Rollback en caso de error para limpiar la transacción
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {e}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {e}")
    
#TODO post last page

@routerUsuarios.post("/user/set_last_page", response_model=LastPageResponse )
async def register_last_page (
    data : LastPageRequest,
    db : oracledb.Connection = Depends(get_connection),
    user_data : dict = Depends(get_current_user)
    
) : 
    
    id_user = user_data.get("user_id")
    try :
        with db.cursor() as cursor :
            cursor.callproc("PKG_ACCOUNT.SET_LAST_PAGE", [id_user, data.id_page])
            
            db.commit()
            
            sql = "SELECT * FROM V_USER_DASHBOARD WHERE ID_USER = :user_id"
            
            cursor.execute(sql, user_id = id_user)
            
            row = cursor.fetchone()
            
            
            
            if not row : 
                raise HTTPException(status_code=404, detail="Datos de dashboard no encontrados para el usuario.")
            #print(row)
            return LastPageResponse(
                id_level = row[2],
                id_section = cursor.callfunc("PKG_CONTENT.SECTION_OF_PAGE",oracledb.NUMBER,[row[8]] ),
                id_page =row[8],
                
            )
        
    except oracledb.DatabaseError as e :
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {e}")

@routerUsuarios.get("/user/qualifications", response_model=list[CalificationJson])
async def get_user_qualifications(
        user_id: int,
        db: oracledb.Connection = Depends(get_connection),
        #current_user: dict = Depends(get_current_user)
):
    #user_id = current_user["user_id"]
    qualifications = []

    try:
        with db.cursor() as cursor:
            sql = """
                  SELECT usp.ID_SECTION, \
                         usp.ATTEMPTS, \
                         usp.STATUS, \
                         (SELECT MAX(SCORE) \
                          FROM PRACTICE_ATTEMPT pa \
                          WHERE pa.ID_USER = usp.ID_USER \
                            AND pa.ID_SECTION = usp.ID_SECTION \
                            AND pa.STATUS = 'FINISHED') as MAX_SCORE
                  FROM USER_SECTION_PROGRESS usp
                  WHERE usp.ID_USER = :1
                  ORDER BY usp.ID_SECTION ASC \
                  """
            cursor.execute(sql, [user_id])
            rows = cursor.fetchall()

            for row in rows:

                status_sec = row[2]
                passed = status_sec in ('SUPERADO', 'PERFECTO')

                max_score = row[3] if row[3] is not None else 0

                qualifications.append(CalificationJson(
                    sectionId=row[0],
                    score=max_score,
                    retries=row[1],
                    passed=passed
                ))

    except oracledb.DatabaseError as e:
        raise HTTPException(status_code=500, detail=f"Error de base de datos al obtener calificaciones: {e}")

    return qualifications

@routerUsuarios.post("/user/delete/account", response_model=DeleteResponse)
async def post_delete_account(
    db : oracledb.Connection = Depends(get_connection),
    user_data : dict = Depends(get_current_user)
) :
    user_id = user_data.get("user_id")
    
    try :
        with db.cursor() as cursor :
            cursor.callproc("PKG_ACCOUNT.DELETE_USER_ACCOUNT", [user_id])
            
            db.commit()
            
            return DeleteResponse(
                cod=200,
                response= "Cuenta eliminada exitosamente!"
            )
    except oracledb.DatabaseError as e:
        db.rollback()
        # 4. Lanzar excepción HTTP real
        raise HTTPException(status_code=500, detail=f"Error al eliminar la cuenta: {e}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {e}")