# src/api/contenido_api.py
import oracledb
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Optional

# Importa tus utilidades
from src.db.session import get_connection
from src.core.security import get_current_user

routerContenido = APIRouter()

# --- 1. Definimos los Modelos de Respuesta (Pydantic) ---
#    (Los modelos que definimos arriba)

class LevelJson(BaseModel):
    id_level: int
    name: str
    description: str
    sections: List[int] 

class SectionJson(BaseModel):
    id_section: int
    name: str
    description: str
    pages: List[int]
    id_level : int
    
class PageJson(BaseModel):
    id_page: int
    page_order: int
    content_md: str
    id_section : int

class FullCourseResponse(BaseModel):
    levels: List[LevelJson]
    sections: List[SectionJson]
    pages: List[PageJson]


@routerContenido.get("/content/complete_structure", response_model=FullCourseResponse)
async def get_estructura_completa_del_curso_json(
    db : oracledb.Connection = Depends(get_connection),
    current_user : dict = Depends(get_current_user)
) : 
    try : 
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
            
            level_jsons : List[LevelJson] = []
            sections_json : List[SectionJson] = []
            pages_json : List[PageJson] = []
            
            page_map: Dict[int, List[int]] = {} # Clave: id_section, Valor: [id_page_1, id_page_2]
            section_map: Dict[int, List[int]] = {} # Clave: id_level, Valor: [id_section_1, ...]
            
            for row in page_refcursor :
                page = PageJson(
                        id_page= row[0],
                        page_order=row[3],
                        content_md=row[4] if row[4] else "",
                        id_section=row[2]
                    )
                
                pages_json.append(page)
                
                if row[2] not in page_map :
                    page_map[row[2]] = []
                    
                page_map[row[2]].append(page.id_page)
            
            for row in section_refcursor :
                
                    
                section = SectionJson(
                    id_section= row[0],
                    name= row[2],
                    description=row[3] if row[3] else "",
                    id_level=row[1],
                    pages= page_map.get(row[0],[])
                    
                    )
                
                sections_json.append(section)
                
                if row[1] not in section_map:
                    section_map[row[1]] = []
                
                section_map[row[1]].append(section.id_section)
                
            for row in level_refcursor : 
                
                    level_jsons.append(
                        LevelJson(
                        id_level = row[0],
                        name = row[1],
                        description = row[2] if row[2] else "",
                        sections = section_map.get(row[0],[])
                        )
                    )
                
            level_refcursor.close()
            section_refcursor.close()
            page_refcursor.close()
                
            
                
            return FullCourseResponse(
                levels= level_jsons,
                sections= sections_json,
                pages = pages_json
            )
            
    except oracledb.DatabaseError as e:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {e}")
    except Exception as e:
        print(f"Error interno inesperado: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno: {e}")