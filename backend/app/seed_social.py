from app.database import SessionLocal
from app.models.poi import POI
from app.models.social import Checkin, Friendship
from app.models.user import User
from app.services.auth_service import hash_password


DEMO_USERS = [
    {
        "name": "Aditi Sharma",
        "email": "aditi@routewise.com",
        "interests": "history,food,nature",
        "budget_style": "mid",
        "preferred_transport": "Metro",
        "home_area": "Shivajinagar",
    },
    {
        "name": "Rohan Patil",
        "email": "rohan@routewise.com",
        "interests": "nature,nightlife,food",
        "budget_style": "budget",
        "preferred_transport": "Bus",
        "home_area": "Kothrud",
    },
    {
        "name": "Meera Kulkarni",
        "email": "meera@routewise.com",
        "interests": "spiritual,history,nature",
        "budget_style": "mid",
        "preferred_transport": "Metro",
        "home_area": "Deccan",
    },
    {
        "name": "Kabir Joshi",
        "email": "kabir@routewise.com",
        "interests": "food,shopping,nightlife",
        "budget_style": "comfort",
        "preferred_transport": "Auto",
        "home_area": "Koregaon Park",
    },
    {
        "name": "Sana Khan",
        "email": "sana@routewise.com",
        "interests": "history,shopping,food",
        "budget_style": "mid",
        "preferred_transport": "Metro",
        "home_area": "Viman Nagar",
    },
]


def get_or_create_user(db, data):
    user = db.query(User).filter(User.email == data["email"]).first()

    if user:
        return user

    user = User(
        name=data["name"],
        email=data["email"],
        password_hash=hash_password("RouteWise@123"),
        interests=data["interests"],
        budget_style=data["budget_style"],
        preferred_transport=data["preferred_transport"],
        home_area=data["home_area"],
        share_checkins=True,
    )

    db.add(user)
    db.flush()

    return user


def get_poi_by_name(db, name):
    return db.query(POI).filter(POI.name == name).first()


def create_checkin(db, user, poi_name):
    poi = get_poi_by_name(db, poi_name)

    if not poi:
        print(f"WARNING: POI not found: {poi_name}")
        return

    existing = (
        db.query(Checkin)
        .filter(
            Checkin.user_id == user.id,
            Checkin.poi_id == poi.id,
        )
        .first()
    )

    if not existing:
        db.add(
            Checkin(
                user_id=user.id,
                poi_id=poi.id,
            )
        )


def create_friendship(db, user_a, user_b):
    existing = (
        db.query(Friendship)
        .filter(
            (
                (Friendship.requester_id == user_a.id)
                & (Friendship.addressee_id == user_b.id)
            )
            |
            (
                (Friendship.requester_id == user_b.id)
                & (Friendship.addressee_id == user_a.id)
            )
        )
        .first()
    )

    if not existing:
        db.add(
            Friendship(
                requester_id=user_a.id,
                addressee_id=user_b.id,
                status="accepted",
            )
        )


def main():
    db = SessionLocal()

    try:
        users = {}

        for data in DEMO_USERS:
         users[data["email"]] = get_or_create_user(db, data)

        demo_user = (
            db.query(User)
            .filter(User.email == "demo@routewise.com")
            .first()
        )

        if not demo_user:
            raise RuntimeError("Main demo user not found.")

        db.commit()
        create_checkin(
            db,
            users["aditi@routewise.com"],
            "Shaniwar Wada",
        )
        create_checkin(
            db,
            users["aditi@routewise.com"],
            "Raja Dinkar Kelkar Museum",
        )
        create_checkin(
            db,
            users["aditi@routewise.com"],
            "FC Road",
        )
        create_checkin(
            db,
            users["rohan@routewise.com"],
            "Sinhagad Fort",
        )
        create_checkin(
            db,
            users["rohan@routewise.com"],
            "Vetal Tekdi",
        )
        create_checkin(
            db,
            users["rohan@routewise.com"],
            "Koregaon Park",
        )
        create_checkin(
            db,
            users["meera@routewise.com"],
            "Dagdusheth Halwai Ganpati Temple",
        )
        create_checkin(
            db,
            users["meera@routewise.com"],
            "Parvati Hill",
        )
        create_checkin(
            db,
            users["meera@routewise.com"],
            "Pataleshwar Cave Temple",
        )
        create_checkin(
            db,
            users["kabir@routewise.com"],
            "Koregaon Park",
        )
        create_checkin(
            db,
            users["kabir@routewise.com"],
            "Phoenix Marketcity Pune",
        )
        create_checkin(
            db,
            users["kabir@routewise.com"],
            "FC Road",
        )
        create_checkin(
            db,
            users["sana@routewise.com"],
            "Aga Khan Palace",
        )
        create_checkin(
            db,
            users["sana@routewise.com"],
            "Lal Mahal",
        )
        create_checkin(
            db,
            users["sana@routewise.com"],
            "Shaniwar Wada",
        )
        create_friendship(
            db,
            users["aditi@routewise.com"],
            users["rohan@routewise.com"],
        )

        create_friendship(
            db,
            users["aditi@routewise.com"],
            users["meera@routewise.com"],
        )

        create_friendship(
            db,
            users["rohan@routewise.com"],
            users["kabir@routewise.com"],
        )

        create_friendship(
            db,
            users["meera@routewise.com"],
            users["sana@routewise.com"],
        )
        create_friendship(
            db,
            demo_user,
            users["aditi@routewise.com"],
        )

        create_friendship(
            db,
            demo_user,
            users["meera@routewise.com"],
        )

        db.commit()

        print("Social seed complete.")
        print("Created/verified 5 demo users.")
        print("Created/verified demo check-ins.")
        print("Created/verified demo friendships.")

    finally:
        db.close()


if __name__ == "__main__":
    main()