from collections import Counter
from math import log2

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.poi import POI
from app.models.social import Checkin, Friendship
from app.models.user import User


def interest_vector(user: User) -> set[str]:
    return {
        item.strip().lower()
        for item in user.interests.split(",")
        if item.strip()
    }


def jensen_shannon_similarity(user_a: User, user_b: User) -> float:
    """
    Measures similarity between two users' interest profiles.
    Returns a value between 0 and 1.
    """

    interests_a = interest_vector(user_a)
    interests_b = interest_vector(user_b)

    if not interests_a and not interests_b:
        return 1.0

    if not interests_a or not interests_b:
        return 0.0

    vocabulary = sorted(interests_a | interests_b)

    p = []
    q = []

    for interest in vocabulary:
        p.append(1.0 if interest in interests_a else 0.0)
        q.append(1.0 if interest in interests_b else 0.0)

    m = [(a + b) / 2 for a, b in zip(p, q)]

    def kl_divergence(x, y):
        total = 0.0

        for a, b in zip(x, y):
            if a > 0 and b > 0:
                total += a * log2(a / b)

        return total
    p_sum = sum(p)
    q_sum = sum(q)

    p = [value / p_sum for value in p]
    q = [value / q_sum for value in q]
    m = [(a + b) / 2 for a, b in zip(p, q)]

    js_divergence = (
        kl_divergence(p, m) +
        kl_divergence(q, m)
    ) / 2
    return max(0.0, min(1.0, 1.0 - js_divergence))


def get_friend_ids(db: Session, user_id: int) -> set[int]:
    friendships = db.scalars(
        select(Friendship).where(
            Friendship.status == "accepted",
            or_(
                Friendship.requester_id == user_id,
                Friendship.addressee_id == user_id,
            ),
        )
    ).all()

    friend_ids = set()

    for friendship in friendships:
        if friendship.requester_id == user_id:
            friend_ids.add(friendship.addressee_id)
        else:
            friend_ids.add(friendship.requester_id)

    return friend_ids


def get_friend_suggestions(
    db: Session,
    user: User,
    limit: int = 10,
):
    friend_ids = get_friend_ids(db, user.id)

    excluded_ids = friend_ids | {user.id}

    users = db.scalars(
        select(User).where(
            User.is_active.is_(True),
            User.id.not_in(excluded_ids),
        )
    ).all()

    suggestions = []

    for candidate in users:
        similarity = jensen_shannon_similarity(user, candidate)

        candidate_score = similarity

        suggestions.append(
            {
                "user_id": candidate.id,
                "name": candidate.name,
                "email": candidate.email,
                "interest_similarity": round(similarity, 3),
                "suggestion_score": round(candidate_score, 3),
            }
        )

    suggestions.sort(
        key=lambda item: item["suggestion_score"],
        reverse=True,
    )

    return suggestions[:limit]


def get_friend_checkin_scores(
    db: Session,
    user: User,
    pois: list[POI],
) -> dict[int, float]:

    friend_ids = get_friend_ids(db, user.id)

    if not friend_ids:
        return {
            poi.id: 0.5
            for poi in pois
        }

    friend_checkins = db.scalars(
        select(Checkin).where(
            Checkin.user_id.in_(friend_ids)
        )
    ).all()

    checkin_counts = Counter(
        checkin.poi_id
        for checkin in friend_checkins
    )

    max_count = max(checkin_counts.values(), default=1)

    scores = {}

    for poi in pois:
        count = checkin_counts.get(poi.id, 0)
        score = 0.5 + 0.5 * (count / max_count)

        scores[poi.id] = min(score, 1.0)

    return scores