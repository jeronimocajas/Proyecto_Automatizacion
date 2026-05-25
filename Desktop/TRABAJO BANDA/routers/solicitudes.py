from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.database import get_db
from models.models import TipoAuxilio, DocumentoRequerido

router = APIRouter()

@router.get("/tipos-auxilio")
async def tipos_auxilio(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TipoAuxilio).where(TipoAuxilio.activo == True))
    tipos = result.scalars().all()
    return [
        {
            "id": t.id,
            "codigo": t.codigo,
            "nombre": t.nombre,
            "descripcion": t.descripcion
        }
        for t in tipos
    ]

@router.get("/documentos-requeridos/{tipo_auxilio_codigo}")
async def documentos_requeridos(tipo_auxilio_codigo: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DocumentoRequerido, TipoAuxilio)
        .join(TipoAuxilio)
        .where(TipoAuxilio.codigo == tipo_auxilio_codigo.upper())
        .order_by(DocumentoRequerido.orden)
    )
    docs = result.all()
    return [
        {
            "id": d.DocumentoRequerido.id,
            "nombre": d.DocumentoRequerido.nombre,
            "descripcion": d.DocumentoRequerido.descripcion,
            "obligatorio": d.DocumentoRequerido.obligatorio,
            "orden": d.DocumentoRequerido.orden
        }
        for d in docs
    ]