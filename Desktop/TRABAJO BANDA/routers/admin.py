from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from core.database import get_db
from models.models import Solicitud

router = APIRouter()

@router.get("/resumen")
async def resumen(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            Solicitud.estado,
            func.count(Solicitud.id).label("total")
        ).group_by(Solicitud.estado)
    )
    return {"resumen_por_estado": [{"estado": r.estado, "total": r.total} for r in result.all()]}