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
    # pagina: "Pagina" = Relationship(back_populates="cuentas_de_usuario") # Ejemplo