import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.cidade import Cidade
from app.models.hotel import Hotel
from app.schemas.hotel import (
    CidadeCreateSchema,
    CidadeResponseSchema,
    CidadeUpdateSchema,
    HotelCreateSchema,
    HotelResponseSchema,
    HotelUpdateSchema,
)

router = APIRouter(tags=["Gestão"])


@router.get("/cidades", response_model=list[CidadeResponseSchema])
def listar_cidades(db: Session = Depends(get_db)):
    cidades = db.query(Cidade).order_by(Cidade.nome.asc()).all()
    return [
        CidadeResponseSchema(
            id=cidade.id,
            nome=cidade.nome,
            uf=cidade.uf,
            hoteis=len(cidade.hoteis),
            status="Ativa" if cidade.hoteis else "Inativa",
        )
        for cidade in cidades
    ]


@router.post("/cidades", response_model=CidadeResponseSchema, status_code=status.HTTP_201_CREATED)
def criar_cidade(payload: CidadeCreateSchema, db: Session = Depends(get_db)):
    cidade = Cidade(
        nome=payload.nome.strip(),
        uf=payload.uf.strip().upper(),
    )
    db.add(cidade)
    db.commit()
    db.refresh(cidade)

    return CidadeResponseSchema(
        id=cidade.id,
        nome=cidade.nome,
        uf=cidade.uf,
        hoteis=0,
        status=payload.status or "Ativa",
    )


@router.put("/cidades/{cidade_id}", response_model=CidadeResponseSchema)
def atualizar_cidade(cidade_id: uuid.UUID, payload: CidadeUpdateSchema, db: Session = Depends(get_db)):
    cidade = db.get(Cidade, cidade_id)
    if not cidade:
        raise HTTPException(status_code=404, detail="Cidade nao encontrada")

    cidade.nome = payload.nome.strip()
    cidade.uf = payload.uf.strip().upper()

    db.commit()
    db.refresh(cidade)

    return CidadeResponseSchema(
        id=cidade.id,
        nome=cidade.nome,
        uf=cidade.uf,
        hoteis=len(cidade.hoteis),
        status=payload.status or ("Ativa" if cidade.hoteis else "Inativa"),
    )


@router.delete("/cidades/{cidade_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_cidade(cidade_id: uuid.UUID, db: Session = Depends(get_db)):
    cidade = db.get(Cidade, cidade_id)
    if not cidade:
        raise HTTPException(status_code=404, detail="Cidade nao encontrada")

    db.delete(cidade)
    db.commit()
    return None


@router.get("/hoteis", response_model=list[HotelResponseSchema])
def listar_hoteis(db: Session = Depends(get_db)):
    hoteis = db.query(Hotel).options(joinedload(Hotel.cidade)).order_by(Hotel.nome.asc()).all()
    return [
        HotelResponseSchema(
            id=hotel.id,
            nome=hotel.nome,
            endereco=hotel.endereco,
            estrelas=hotel.estrelas,
            cidade_id=hotel.cidade_id,
            cidade_nome=hotel.cidade.nome if hotel.cidade else None,
            status="Ativo",
            diaria=hotel.diaria or "R$ 0",
        )
        for hotel in hoteis
    ]


@router.post("/hoteis", response_model=HotelResponseSchema, status_code=status.HTTP_201_CREATED)
def criar_hotel(payload: HotelCreateSchema, db: Session = Depends(get_db)):
    cidade = db.get(Cidade, payload.cidade_id)
    if not cidade:
        raise HTTPException(status_code=404, detail="Cidade nao encontrada")

    hotel = Hotel(
        nome=payload.nome.strip(),
        endereco=payload.endereco.strip(),
        estrelas=payload.estrelas,
        diaria=payload.diaria or "R$ 0",
        cidade_id=cidade.id,
    )
    db.add(hotel)
    db.commit()
    db.refresh(hotel)

    return HotelResponseSchema(
        id=hotel.id,
        nome=hotel.nome,
        endereco=hotel.endereco,
        estrelas=hotel.estrelas,
        cidade_id=hotel.cidade_id,
        cidade_nome=cidade.nome,
        status=payload.status or "Ativo",
        diaria=hotel.diaria or "R$ 0",
    )


@router.put("/hoteis/{hotel_id}", response_model=HotelResponseSchema)
def atualizar_hotel(hotel_id: uuid.UUID, payload: HotelUpdateSchema, db: Session = Depends(get_db)):
    hotel = db.get(Hotel, hotel_id)
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel nao encontrado")

    cidade = db.get(Cidade, payload.cidade_id)
    if not cidade:
        raise HTTPException(status_code=404, detail="Cidade nao encontrada")

    hotel.nome = payload.nome.strip()
    hotel.endereco = payload.endereco.strip()
    hotel.estrelas = payload.estrelas
    hotel.diaria = payload.diaria or "R$ 0"
    hotel.cidade_id = cidade.id

    db.commit()
    db.refresh(hotel)

    return HotelResponseSchema(
        id=hotel.id,
        nome=hotel.nome,
        endereco=hotel.endereco,
        estrelas=hotel.estrelas,
        cidade_id=hotel.cidade_id,
        cidade_nome=cidade.nome,
        status=payload.status or "Ativo",
        diaria=hotel.diaria or "R$ 0",
    )


@router.delete("/hoteis/{hotel_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_hotel(hotel_id: uuid.UUID, db: Session = Depends(get_db)):
    hotel = db.get(Hotel, hotel_id)
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel nao encontrado")

    db.delete(hotel)
    db.commit()
    return None
