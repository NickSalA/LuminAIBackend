# src/api/contenido_api.py
import oracledb
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict

# Importa tus utilidades
from src.db.session import get_connection
from src.core.security import get_current_user

routerContenido = APIRouter()


# --- 1. Definimos los Modelos de Respuesta (Ajustados a tu Frontend) ---

class LevelJson(BaseModel):
    id: int  # Antes id_level
    name: str
    description: str
    sections: List[int]


class SectionJson(BaseModel):
    id: int  # Antes id_section
    name: str
    description: str
    pages: List[int]
    # Eliminado id_level del output final (se usa solo para agrupar)


class PageJson(BaseModel):
    id: int  # Antes id_page
    content: str  # Antes content_md
    pageNumber: int  # Antes page_order


class FullCourseResponse(BaseModel):
    levels: List[LevelJson]
    sections: List[SectionJson]
    pages: List[PageJson]


@routerContenido.get("/content/complete_structure", response_model=FullCourseResponse)
async def get_estructura_completa_del_curso_json(
        db: oracledb.Connection = Depends(get_connection),
        current_user: dict = Depends(get_current_user)
):
    try:
        with db.cursor() as cursor:

            level_cursor_var = cursor.var(oracledb.DB_TYPE_CURSOR)
            section_cursor_var = cursor.var(oracledb.DB_TYPE_CURSOR)
            page_cursor_var = cursor.var(oracledb.DB_TYPE_CURSOR)

            cursor.callproc("PKG_CONTENT.GET_FULL_COURSE_DATA", [
                level_cursor_var,
                section_cursor_var,
                page_cursor_var
            ])

            level_refcursor = level_cursor_var.getvalue()
            section_refcursor = section_cursor_var.getvalue()
            page_refcursor = page_cursor_var.getvalue()

            level_jsons: List[LevelJson] = []
            sections_json: List[SectionJson] = []
            pages_json: List[PageJson] = []

            page_map: Dict[int, List[int]] = {}
            section_map: Dict[int, List[int]] = {}

            # --- PROCESAR PÁGINAS ---
            for row in page_refcursor:

                current_section_id = row[2]

                page = PageJson(
                    id=row[0],
                    pageNumber=row[3],
                    content=row[4] if row[4] else ""
                )

                pages_json.append(page)

                if current_section_id not in page_map:
                    page_map[current_section_id] = []

                page_map[current_section_id].append(page.id)

            for row in section_refcursor:

                current_level_id = row[1]

                section = SectionJson(
                    id=row[0],  # Mapea a "id"
                    name=row[2],
                    description=row[3] if row[3] else "",
                    pages=page_map.get(row[0], [])
                )
                sections_json.append(section)

                if current_level_id not in section_map:
                    section_map[current_level_id] = []

                section_map[current_level_id].append(section.id)

            # --- PROCESAR NIVELES ---
            for row in level_refcursor:

                level_jsons.append(
                    LevelJson(
                        id=row[0],  # Mapea a "id"
                        name=row[1],
                        description=row[2] if row[2] else "",
                        sections=section_map.get(row[0], [])
                    )
                )

            # Liberar recursos
            level_refcursor.close()
            section_refcursor.close()
            page_refcursor.close()

            return FullCourseResponse(
                levels=level_jsons,
                sections=sections_json,
                pages=pages_json
            )

    except oracledb.DatabaseError as e:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {e}")
    except Exception as e:
        print(f"Error interno inesperado: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno: {e}")