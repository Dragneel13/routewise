import random

from app.models.poi import POI
from app.models.user import User
from app.services.friends_service import get_friend_checkin_scores

def calculate_interest_match(user, poi):
    user_interests = {
        interest.strip().lower()
        for interest in user.interests.split(",")
        if interest.strip()
    }

    poi_tags = {
        tag.strip().lower()
        for tag in poi.tags.split(",")
        if tag.strip()
    }

    if not user_interests or not poi_tags:
        return 0.0

    matches = user_interests.intersection(poi_tags)

    return len(matches) / len(user_interests)


def calculate_popularity_score(poi):
    return max(
        0.0,
        min(poi.popularity / 100.0, 1.0),
    )


def calculate_context_score(user, poi):
    score = 0.5

    if user.budget_style == "budget":
        if poi.entry_fee <= 50:
            score += 0.3
        elif poi.entry_fee <= 150:
            score += 0.1
        else:
            score -= 0.2

    elif user.budget_style == "mid":
        if poi.entry_fee <= 300:
            score += 0.2
        else:
            score -= 0.1

    elif user.budget_style == "comfort":
        if poi.entry_fee <= 500:
            score += 0.2

    if user.preferred_transport == "Metro":
        if poi.near_metro:
            score += 0.2
        else:
            score -= 0.1

    return max(
        0.0,
        min(score, 1.0),
    )


def calculate_recommendation_score(
    friend_score,
    interest_match,
    popularity_score,
    context_score,
):
    return (
        0.35 * friend_score
        + 0.25 * interest_match
        + 0.20 * popularity_score
        + 0.20 * context_score
    )


def recommend_pois(db, user, pois):
    recommendations = []

    friend_scores = get_friend_checkin_scores(
        db=db,
        user=user,
        pois=pois,
    )

    for poi in pois:
        friend_score = friend_scores.get(
            poi.id,
            0.5,
        )

        interest_match = calculate_interest_match(
            user,
            poi,
        )

        popularity_score = calculate_popularity_score(
            poi,
        )

        context_score = calculate_context_score(
            user,
            poi,
        )

        recommendation_score = calculate_recommendation_score(
            friend_score,
            interest_match,
            popularity_score,
            context_score,
        )

        recommendations.append(
            {
                "poi_id": poi.id,
                "name": poi.name,
                "category": poi.category,
                "area": poi.area,
                "description": poi.description,
                "rating": poi.rating,
                "popularity": poi.popularity,
                "entry_fee": poi.entry_fee,
                "recommended_duration": poi.recommended_duration,
                "tags": poi.tags,
                "near_metro": poi.near_metro,
                "friend_score": round(friend_score, 3),
                "interest_match": round(interest_match, 3),
                "popularity_score": round(popularity_score, 3),
                "context_score": round(context_score, 3),
                "recommendation_score": round(
                    recommendation_score,
                    3,
                ),
            }
        )
    ranked = sorted(
        recommendations,
        key=lambda item: item["recommendation_score"],
        reverse=True,
    )

    discovery_count = max(
        1,
        round(len(ranked) * 0.20),
    )

    discovery_candidates = [
        item
        for item in ranked
        if item["rating"] >= 4.3
        and item["friend_score"] <= 0.5
    ]

    random.shuffle(discovery_candidates)

    discovery_items = discovery_candidates[:discovery_count]

    discovery_ids = {
        item["poi_id"]
        for item in discovery_items
    }
    normal_items = [
        item
        for item in ranked
        if item["poi_id"] not in discovery_ids
    ]

    final_recommendations = []

    insert_after = min(3, len(normal_items))

    final_recommendations.extend(
        normal_items[:insert_after]
    )

    for item in discovery_items:
        item["recommendation_score"] = round(
            item["recommendation_score"] * 0.90,
            3,
        )
        final_recommendations.append(item)

    final_recommendations.extend(
        normal_items[insert_after:]
    )

    return final_recommendations