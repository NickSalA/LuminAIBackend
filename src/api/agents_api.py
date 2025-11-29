import httpx
import oracledb
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import uuid

from src.flow.flow_tutor import FlowAgenteTutor
from src.flow.flow_preguntas_diarias import FlowAgentePreguntasDiarias
from src.flow.flow_preguntas_practica import FlowAgentePreguntas
from src.flow.flow_respuestas import FlowAgenteRespuestas
from src.flow.flow_retroalimentacion import FlowAgenteRetroalimentacion

from src.util.util_schemas import (AgentMessageJson, ChatIn,respuestasRequest, chatTutorRequest, chatRetroalimentacionRequest,preguntasRequest,PracticeResultsResponse, DailyPracticeResultsResponse,UserMetrics, CalificationJson)

from src.db.session import get_connection
from src.core.security import get_current_user

routerAgente = APIRouter()

@routerAgente.post("/tutor", response_model=AgentMessageJson)
async def obtener_tutor(req: chatTutorRequest, body: ChatIn):
    user = req.userData
    seccion = req.contextData

    orq = FlowAgenteTutor(user, seccion)
    thread = body.thread_id

    if not thread:
        thread = orq.reiniciarMemoria()

    try:
        respuesta = await orq.responderMensaje(body.mensaje, thread)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error al enviar el mensaje: {e}')

    return AgentMessageJson(text=respuesta, thread_id=thread)


@routerAgente.post("/practice")
async def obtener_preguntas(
        req: preguntasRequest,
        db: oracledb.Connection = Depends(get_connection),
        current_user: dict = Depends(get_current_user)
):
    user_id = current_user["user_id"]
    seccion_data = req.contextData
    id_section = seccion_data.get("id_section")

    if id_section:
        try:
            with db.cursor() as cursor:
                cursor.callfunc("PKG_PROGRESS.START_ATTEMPT", oracledb.NUMBER, [user_id, id_section])
                db.commit()
        except oracledb.DatabaseError as e:
            error_msg = str(e)
            if "ORA-20010" in error_msg:  # Error definido en tu PL/SQL "No tienes mas vidas"
                raise HTTPException(status_code=402, detail="No tienes suficientes vidas.")
            if "ORA-20020" in error_msg:  # "SECCION BLOQUEADA"
                raise HTTPException(status_code=403, detail="Sección bloqueada.")
            raise HTTPException(status_code=500, detail=f"Error de BD al iniciar práctica: {e}")

    # Generar con IA
    orq = FlowAgentePreguntas(seccion_data)
    try:
        preguntas = await orq.generarPreguntas()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error al generar preguntas: {e}')

    return preguntas


@routerAgente.post("/dailyPractice")
async def obtener_preguntas_diarias(
        db: oracledb.Connection = Depends(get_connection),
        current_user: dict = Depends(get_current_user)
):
    user_id = current_user["user_id"]

    temas_desbloqueados = []

    try:
        with db.cursor() as cursor:
            can_play = cursor.callfunc("PKG_PROGRESS.CAN_START_DAILY_CHALLENGE", oracledb.STRING, [user_id])
            if can_play == 'N':
                raise HTTPException(status_code=403, detail="Ya has completado tu práctica diaria de hoy.")

            query_temas = """
                          SELECT s.NAME
                          FROM USER_SECTION_PROGRESS usp
                                   JOIN SECTION s ON s.ID_SECTION = usp.ID_SECTION
                          WHERE usp.ID_USER = :user_id
                            AND usp.STATUS IN ('EN PROGRESO', 'SUPERADO', 'PERFECTO')
                          ORDER BY s.ID_LEVEL, s.ID_SECTION ASC \
                          """

            # Pasamos el parámetro como un diccionario explícito con la clave 'user_id'
            cursor.execute(query_temas, {"user_id": user_id})

            rows = cursor.fetchall()

            if rows:
                temas_desbloqueados = [row[0] for row in rows]
            else:
                cursor.execute("SELECT NAME FROM SECTION WHERE ID_SECTION = 1")  # O busca por min(ID)
                row_default = cursor.fetchone()
                if row_default:
                    temas_desbloqueados = [row_default[0]]
                else:
                    temas_desbloqueados = ["Conceptos Básicos de Programación"]  # Fallback final

    except oracledb.DatabaseError as e:
        raise HTTPException(status_code=500, detail=f"Error de BD verificando reto diario: {e}")

    print(f"Generando práctica diaria para usuario {user_id} con temas: {temas_desbloqueados}")

    orq = FlowAgentePreguntasDiarias(temas_desbloqueados)

    try:
        preguntas = await orq.generarPreguntas()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error al generar preguntas diarias: {e}')

    return preguntas


@routerAgente.post("/practiceResults", response_model=PracticeResultsResponse)
async def obtener_respuestas(
        req: respuestasRequest,
        db: oracledb.Connection = Depends(get_connection),
        current_user: dict = Depends(get_current_user)
):
    user_id = current_user["user_id"]
    orq = FlowAgenteRespuestas(req.questions, req.answers)
    try:
        evaluacion = await orq.evaluarRespuestas()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error IA evaluando respuestas: {e}')

    score_obtenido = evaluacion.get("score", 0)
    id_section = req.userData.get("sectionId")
    
    try:
        with db.cursor() as cursor:
            cursor.callproc("PKG_PROGRESS.FINISH_ATTEMPT", [user_id, id_section, score_obtenido])

            # Recuperar métricas
            cursor.execute("SELECT * FROM V_USER_DASHBOARD WHERE ID_USER = :1", [user_id])
            row = cursor.fetchone()

            # Calcular currentSectionId
            current_page_id = row[8] if row else None
            current_section_user_id = 0

            if current_page_id:
                current_section_user_id = cursor.callfunc(
                    "PKG_CONTENT.SECTION_OF_PAGE",
                    oracledb.NUMBER,
                    [current_page_id]
                )

            user_metrics = UserMetrics(
                currentLevelId=row[2],
                averageScore=float(row[4]) if row[4] is not None else 0.0,
                succededSectionsCount=row[5],
                totalSectionsCount=row[6],

                # Nombres y campos corregidos:
                totalPracticeRetries=row[7],  # Sin 's'
                currentPageId=current_page_id,
                currentSectionId=current_section_user_id,  # Campo nuevo agregado

                succededDailyPracticeCount=row[13]  # Índice 13
            ) if row else None

            cursor.execute("""
                           SELECT ATTEMPTS, STATUS
                           FROM USER_SECTION_PROGRESS
                           WHERE ID_USER = :1 AND ID_SECTION = :2
                           """, [user_id, id_section])
            prog_row = cursor.fetchone()

            retries = prog_row[0] if prog_row else 0
            status_sec = prog_row[1] if prog_row else 'BLOQUEADO'
            passed = status_sec in ('SUPERADO', 'PERFECTO')

            db.commit()

            calification = CalificationJson(
                sectionId=id_section,
                score=score_obtenido,
                retries=retries,
                passed=passed
            )

    except oracledb.DatabaseError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error guardando progreso: {e}")

    return PracticeResultsResponse(
        questionsResults=evaluacion["questionsResults"],
        resultType=evaluacion["resultType"],
        score=score_obtenido,
        userMetrics=user_metrics,
        calification=calification
    )

@routerAgente.post("/dailyPracticeResults", response_model=DailyPracticeResultsResponse)
async def obtener_respuestas_diarias(
        req: respuestasRequest,
        db: oracledb.Connection = Depends(get_connection),
        current_user: dict = Depends(get_current_user)
):
    user_id = current_user["user_id"]

    # 1. Evaluar con IA
    orq = FlowAgenteRespuestas(req.questions, req.answers)
    try:
        evaluacion = await orq.evaluarRespuestas()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error IA evaluando: {e}')

    score = evaluacion.get("score", 0)
    did_win = score >= 3

    # 2. Guardar en BD
    try:
        with db.cursor() as cursor:
            cursor.callproc("PKG_PROGRESS.FINISH_DAILY_CHALLENGE", [user_id, did_win])

            cursor.execute("SELECT DAILY_CHALLENGE_WINS FROM USER_ACCOUNT WHERE ID_USER = :1", [user_id])
            res = cursor.fetchone()
            wins = res[0] if res else 0

            db.commit()
    except oracledb.DatabaseError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error guardando reto diario: {e}")

    return DailyPracticeResultsResponse(
        questionsResults=evaluacion["questionsResults"],
        resultType=evaluacion["resultType"],
        score=score,
        succededDailyPracticeCount=wins
    )


@routerAgente.post("/feedback", response_model=AgentMessageJson)
async def obtener_retroalimentacion(req: chatRetroalimentacionRequest, body: Optional[ChatIn] = None):
    user = req.userData
    seccion = req.contextData

    orq = FlowAgenteRetroalimentacion(user, seccion, req.questions, req.answers)
    thread = body.thread_id if body else None

    if not thread:
        thread = orq.reiniciarMemoria()
        try:
            feedback = await orq.darRetroalimentacion(thread)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f'Error al generar retroalimentación: {e}')

    else:
        mensaje = body.mensaje if body else ""
        try:
            feedback = await orq.responderMensaje(mensaje, thread)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f'Error al enviar el mensaje: {e}')

    return AgentMessageJson(text=feedback, thread_id=thread)


@routerAgente.post("/reset", response_model=str)
def reiniciar_Memoria() -> str:
    thread = f"usuario:{'anon'}-{uuid.uuid4().hex}"
    return thread

