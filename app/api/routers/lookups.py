"""Protected IP lookup router."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Query

from app.api.deps import get_current_user, get_lookup_service
from app.models.history import GeolocationResultModel, LookupHistoryRecordModel
from app.models.user import UserModel
from app.schemas.geo import CoordinatesResponse, GeolocationResponse, IPLookupRequest
from app.schemas.history import LookupHistoryRecordResponse
from app.services.lookup_service import LookupService

router = APIRouter(prefix="/lookups")


@router.post("", response_model=GeolocationResponse, summary="Lookup an IP address")
async def lookup_ip_address(
    payload: IPLookupRequest,
    background_tasks: BackgroundTasks,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    lookup_service: Annotated[LookupService, Depends(get_lookup_service)],
) -> GeolocationResponse:
    """Return geolocation data for a validated IP address."""

    geolocation = await lookup_service.lookup_ip(str(payload.ip))
    background_tasks.add_task(lookup_service.record_lookup, current_user, geolocation)
    return _to_geolocation_response(geolocation)


@router.get(
    "/history",
    response_model=list[LookupHistoryRecordResponse],
    summary="List recent lookup history for the current user",
)
async def get_lookup_history(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    lookup_service: Annotated[LookupService, Depends(get_lookup_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[LookupHistoryRecordResponse]:
    """Return recent lookup history for the authenticated user."""

    records = await lookup_service.list_history(current_user, limit=limit)
    return [_to_history_response(record) for record in records]


def _to_geolocation_response(geolocation: GeolocationResultModel) -> GeolocationResponse:
    """Convert an internal geolocation model into an API response schema."""

    return GeolocationResponse(
        ip_address=geolocation.ip_address,
        country=geolocation.country,
        region=geolocation.region,
        city=geolocation.city,
        coordinates=CoordinatesResponse(
            latitude=geolocation.latitude,
            longitude=geolocation.longitude,
        ),
        timezone=geolocation.timezone,
        isp=geolocation.isp,
    )


def _to_history_response(record: LookupHistoryRecordModel) -> LookupHistoryRecordResponse:
    """Convert an internal history model into an API response schema."""

    return LookupHistoryRecordResponse(
        id=record.id,
        user_id=record.user_id,
        username=record.username,
        ip_address=record.ip_address,
        requested_at=record.requested_at,
        geolocation=_to_geolocation_response(record.geolocation),
    )

