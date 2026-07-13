"""Smart Matching REST endpoints."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.preference import PreferenceCreate, PreferenceRead, Recommendation
from app.services import matching_service as matching

router = APIRouter(prefix="/api/v1/preferences", tags=["preferences"])


def _require(db: Session, name: str):
    pref = matching.get_preference(db, name)
    if pref is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Preference {name!r} not found"
        )
    return pref


@router.post("", response_model=PreferenceRead, status_code=status.HTTP_201_CREATED)
def create_preference(payload: PreferenceCreate, db: Session = Depends(get_db)):
    try:
        return matching.create_preference(db, **payload.model_dump())
    except matching.DuplicatePreference as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except matching.InvalidPreference as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )


@router.get("/{name}", response_model=PreferenceRead)
def get_preference(name: str, db: Session = Depends(get_db)):
    return _require(db, name)


@router.get("/{name}/recommendations", response_model=List[Recommendation])
def recommendations(
    name: str, include_disqualified: bool = True, db: Session = Depends(get_db)
):
    pref = _require(db, name)
    return matching.recommend(db, pref, include_disqualified=include_disqualified)
