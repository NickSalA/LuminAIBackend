from sqlmodel import SQLModel, Field, Column, DateTime, Relationship, UniqueConstraint
from typing import Optional, List
from datetime import datetime, timezone

class UsuarioBase(SQLModel):
    id_usuario: int
    email: str = Field(unique=True, index=True)
    username: str = Field(unique=True)
    fecha_nacimiento: Optional[datetime] = None

# Modelo de Tabla
class Usuario(UsuarioBase, table=True):
    id_usuario: Optional[int] = Field(default=None, primary_key=True)
    
    fecha_creacion: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), #se usa lambda disque para que se ejecute en el momento y no una sola vez
        nullable=False
    )
    
    fecha_actualizacion: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            default=lambda: datetime.now(timezone.utc), # <--- CORRECCIÓN: lambda
            onupdate=lambda: datetime.now(timezone.utc), # <--- CORRECCIÓN: lambda
            nullable=False
        )
    )
    
    # Se usan comillas porque 'External' se define más abajo
    logins_externos: List["External"] = Relationship(back_populates="usuario")
    
    cuenta_usuario : "CuentaDeUsuario" = Relationship(back_populates="usuario", sa_relationship_kwargs={"uselist": False})

    suscripciones : List["Suscripcion"] = Relationship(back_populates="usuario")

# Modelo de la tabla externa, en el mismo archivo
class External(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("id_proveedor", "proveedor", name="uq_provider_id"),) # en el remotisimo caso en que 2 proveedores tengan la misma id_proveedor

    id_external: Optional[int] = Field(default=None, primary_key=True)
    proveedor: str
    id_proveedor: str = Field(index=True)
    
    id_usuario: int = Field(foreign_key="usuario.id_usuario") # <--- CORRECCIÓN: 'usuario' en minúscula
    
    fecha_creacion: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    usuario: "Usuario" = Relationship(back_populates="logins_externos")
    
    
class CuentaDeUsuarioBase(SQLModel):
    # El default se define aquí, en el "plano" de los datos.
    vidas: int = Field(default=5)
    id_pagina: int

class CuentaDeUsuario(CuentaDeUsuarioBase, table=True):
    __tablename__ = "cuenta_de_usuario"

    # 1. Clave primaria de esta tabla
    id_cuenta: Optional[int] = Field(default=None, primary_key=True)

    # 2. AQUÍ van las Foreign Keys y sus reglas
    id_usuario: int = Field(unique=True, foreign_key="usuario.id_usuario")
    # Sobrescribimos id_pagina para añadir la FK
    id_pagina: int = Field(foreign_key="pagina.id_pagina") 
    
    # 3. AQUÍ van las Relationships
    usuario: "Usuario" = Relationship(back_populates="cuenta_usuario")
    pagina: "Pagina" = Relationship(back_populates="cuentas_de_usuario") 
    
class PaginaBase(SQLModel):
    nombre: str
    id_pagina: int
    id_modulo_teoria: int
    
class Pagina(PaginaBase, table=True):

    id_pagina: int = Field(primary_key=True)
    id_modulo_teoria: int = Field(foreign_key="modulo_teoria.id_modulo_teoria") # <--- CORRECCIÓN: 'modulo_teoria' en minúscula ponlo asi en la bd ALONSO

    cuentas_de_usuario : List["CuentaDeUsuario"] = Relationship(back_populates="pagina")

class SuscripcionBase(SQLModel):
    fecha_fin : datetime
    
class Suscripcion(SuscripcionBase, table=True):
    id_suscripcion: Optional[int] = Field(default=None, primary_key=True)
    id_usuario: int = Field(foreign_key="usuario.id_usuario")
    id_plan: int = Field(foreign_key="plan_de_suscripcion.id_plan")
    
    usuario: "Usuario" = Relationship(back_populates="suscripciones")
    plan: "PlanDeSuscripcion" = Relationship(back_populates="suscripciones")

class PlanDeSuscripcionBase(SQLModel):
    # Datos que se exponen en la API sobre un plan
    id_plan: int
    nombre: str
    duracion: str # Ej: "Mensual", "Anual"

class PlanDeSuscripcion(PlanDeSuscripcionBase, table=True):
    __tablename__ = "plan_de_suscripcion"

    id_plan: Optional[int] = Field(default=None, primary_key=True)
    
    # Un plan puede tener muchas suscripciones activas
    suscripciones: List["Suscripcion"] = Relationship(back_populates="plan")


# --- MODELOS DE LA ESTRUCTURA DEL CURSO (NIVEL -> SECCION -> MODULO) ---

class NivelBase(SQLModel):
    id_nivel: int
    nombre: str

class Nivel(NivelBase, table=True):
    __tablename__ = "nivel"
    # No se crean con el ORM, por lo que no necesita ser Optional
    id_nivel: int = Field(primary_key=True)
    
    # Un nivel tiene muchas secciones
    secciones: List["Seccion"] = Relationship(back_populates="nivel")


class SeccionBase(SQLModel):
    id_seccion: int
    nombre: str
    descripcion: str
    id_nivel: int

class Seccion(SeccionBase, table=True):
    __tablename__ = "seccion"
    id_seccion: int = Field(primary_key=True)
    id_nivel: int = Field(foreign_key="nivel.id_nivel")
    
    # Una sección pertenece a un solo nivel
    nivel: "Nivel" = Relationship(back_populates="secciones")
    # Una sección tiene muchos módulos de teoría
    modulos_teoria: List["ModuloTeoria"] = Relationship(back_populates="seccion")


class ModuloTeoriaBase(SQLModel):
    id_modulo_teoria: int
    titulo: str # Asumo que tendrá un título o nombre
    id_seccion: int

class ModuloTeoria(ModuloTeoriaBase, table=True):
    __tablename__ = "modulo_teoria"
    id_modulo_teoria: int = Field(primary_key=True)
    id_seccion: int = Field(foreign_key="seccion.id_seccion")

    # Un módulo de teoría pertenece a una sola sección
    seccion: "Seccion" = Relationship(back_populates="modulos_teoria")
    # Un módulo de teoría tiene muchas páginas
    paginas: List["Pagina"] = Relationship(back_populates="modulo_teoria")
    # Un módulo de teoría tiene un solo módulo de práctica (relación 1-a-1)
    modulo_practica: "ModuloPractica" = Relationship(
        back_populates="modulo_teoria",
        sa_relationship_kwargs={"uselist": False}
    )


class ModuloPracticaBase(SQLModel):
    id_modulo_practica: int
    completado: bool = Field(default=False)
    id_modulo_teoria: int

class ModuloPractica(ModuloPracticaBase, table=True):
    __tablename__ = "modulo_practica"
    id_modulo_practica: int = Field(primary_key=True)
    # Es FK y ÚNICO para forzar la relación 1-a-1 a nivel de BD
    id_modulo_teoria: int = Field(unique=True, foreign_key="modulo_teoria.id_modulo_teoria")
    
    # Un módulo de práctica pertenece a un solo módulo de teoría
    modulo_teoria: "ModuloTeoria" = Relationship(back_populates="modulo_practica")
