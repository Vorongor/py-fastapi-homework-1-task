import math
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, MovieModel
from schemas import (
    MovieListResponseSchema,
    MovieDetailResponseSchema
)

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
        request: Request,
        db: Annotated[AsyncSession, Depends(get_db)],
        page: Annotated[int, Query(ge=1)] = 1,
        per_page: Annotated[int, Query(ge=1, le=20)] = 10,
) -> MovieListResponseSchema:
    total_items_result = await db.execute(select(func.count(MovieModel.id)))
    total_items = total_items_result.scalar() or 0

    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = math.ceil(total_items / per_page)

    skip = (page - 1) * per_page
    if skip >= total_items and total_items > 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    result = await db.execute(
        select(MovieModel).offset(skip).limit(per_page)
    )
    movies = result.scalars().all()

    base_url = "/theater/movies/"

    prev_page = None
    if page > 1:
        prev_page = f"{base_url}?page={page - 1}&per_page={per_page}"

    next_page = None
    if page < total_pages:
        next_page = f"{base_url}?page={page + 1}&per_page={per_page}"

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items
    }


@router.get("/movies/{movie_id}/", response_model=MovieDetailResponseSchema)
async def get_movie(
        movie_id: int,
        db: Annotated[AsyncSession, Depends(get_db)],
) -> MovieModel:
    movie = await db.get(MovieModel, movie_id)

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    return movie
