from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.social import Friendship, Checkin
from app.models.user import User
from app.models.poi import POI
from app.routers.auth import get_current_user
from app.services.friends_service import (
    get_friend_ids,
    get_friend_suggestions,
)


router = APIRouter(prefix="/friends", tags=["Friends"])


class FriendRequest(BaseModel):
    user_id: int


class CheckinRequest(BaseModel):
    poi_id: int


@router.get("/suggestions")
def friend_suggestions(
    limit: int = 10,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    limit = max(1, min(limit, 20))

    return get_friend_suggestions(
        db=db,
        user=user,
        limit=limit,
    )


@router.post("/request")
def send_friend_request(
    data: FriendRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if data.user_id == user.id:
        raise HTTPException(
            status_code=400,
            detail="You cannot send a friend request to yourself.",
        )

    target = db.get(User, data.user_id)

    if not target or not target.is_active:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    existing = db.scalar(
        select(Friendship).where(
            or_(
                (
                    (Friendship.requester_id == user.id)
                    & (Friendship.addressee_id == target.id)
                ),
                (
                    (Friendship.requester_id == target.id)
                    & (Friendship.addressee_id == user.id)
                ),
            )
        )
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Friendship already exists with status: {existing.status}",
        )

    friendship = Friendship(
        requester_id=user.id,
        addressee_id=target.id,
        status="pending",
    )

    db.add(friendship)
    db.commit()
    db.refresh(friendship)

    return {
        "message": "Friend request sent.",
        "friendship_id": friendship.id,
        "status": friendship.status,
    }


@router.get("/requests")
def get_friend_requests(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    requests = db.scalars(
        select(Friendship).where(
            Friendship.addressee_id == user.id,
            Friendship.status == "pending",
        )
    ).all()

    result = []

    for request in requests:
        requester = db.get(User, request.requester_id)

        if requester:
            result.append(
                {
                    "friendship_id": request.id,
                    "user_id": requester.id,
                    "name": requester.name,
                    "email": requester.email,
                    "status": request.status,
                }
            )

    return result


@router.post("/accept/{friendship_id}")
def accept_friend_request(
    friendship_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    friendship = db.get(Friendship, friendship_id)

    if not friendship:
        raise HTTPException(
            status_code=404,
            detail="Friend request not found.",
        )

    if friendship.addressee_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only accept requests sent to you.",
        )

    if friendship.status != "pending":
        raise HTTPException(
            status_code=400,
            detail="This friend request is not pending.",
        )

    friendship.status = "accepted"

    db.commit()
    db.refresh(friendship)

    return {
        "message": "Friend request accepted.",
        "friendship_id": friendship.id,
        "status": friendship.status,
    }


@router.get("")
def list_friends(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    friend_ids = get_friend_ids(db, user.id)

    friends = []

    if friend_ids:
        users = db.scalars(
            select(User).where(
                User.id.in_(friend_ids),
                User.is_active.is_(True),
            )
        ).all()

        for friend in users:
            friends.append(
                {
                    "user_id": friend.id,
                    "name": friend.name,
                    "email": friend.email,
                    "interests": [
                        item
                        for item in friend.interests.split(",")
                        if item
                    ],
                }
            )

    return friends


@router.post("/checkins")
def create_checkin(
    data: CheckinRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    poi = db.get(POI, data.poi_id)

    if not poi or not poi.is_active:
        raise HTTPException(
            status_code=404,
            detail="Place not found.",
        )

    checkin = Checkin(
        user_id=user.id,
        poi_id=poi.id,
    )

    db.add(checkin)
    db.commit()
    db.refresh(checkin)

    return {
        "message": "Check-in recorded.",
        "checkin_id": checkin.id,
        "poi_id": poi.id,
        "poi_name": poi.name,
    }


@router.get("/checkins/me")
def get_my_checkins(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    checkins = db.scalars(
        select(Checkin)
        .where(Checkin.user_id == user.id)
        .order_by(Checkin.created_at.desc())
    ).all()

    result = []

    for checkin in checkins:
        poi = db.get(POI, checkin.poi_id)

        if poi:
            result.append(
                {
                    "checkin_id": checkin.id,
                    "poi_id": poi.id,
                    "poi_name": poi.name,
                    "area": poi.area,
                    "created_at": checkin.created_at,
                }
            )

    return result