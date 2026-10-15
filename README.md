# RouteWise

RouteWise is a Pune trip planner with a React interface, a FastAPI backend, and a persistent local PostgreSQL/PostGIS database. The local setup runs in Docker Compose.

## Start the app

Install Docker Desktop and make sure its engine is running. From this folder, start all services:

```powershell
docker compose up --build
```

Open [http://localhost:5173](http://localhost:5173) for the app or [http://localhost:8000/docs](http://localhost:8000/docs) for the API. Compose creates the PostGIS database and keeps its data in the `pgdata` volume. The API seeds the Pune places when it starts; repeat starts do not duplicate them.

To stop the app while keeping your local data, press `Ctrl+C` and run:

```powershell
docker compose down
```

To remove the local database and all saved accounts and trips, run `docker compose down -v`.

## First visit

Create an account with an email address and a password of at least eight characters. After registration, choose a few interests, a starting neighbourhood, a preferred way to travel, and a spending style. RouteWise saves those preferences to your profile and uses the interest list for recommendations.

From the home page, explore places or open **My trip**. Start from Swargate, choose a budget, and add places such as Shaniwar Wada, Dagdusheth Ganpati, or FC Road. Once there are two or more itinerary stops, choose a leg to compare bus, metro, walking, and auto estimates. The budget panel reflects selected transport and place entry fees. Save the trip, copy a share link, or download the PDF itinerary.

## Local services

The web app runs on port 5173, the FastAPI service on port 8000, and PostGIS on port 5432. The API reads its database URL and JWT signing key from environment variables. The compose default is intended only for a local development machine; set a private `SECRET_KEY` in a root `.env` file before exposing any service beyond localhost.

Trip corridor routing, detour calculations, PMPML live data, and ride-hailing quotes are not part of the current backend. The app displays the transport figures returned by the existing estimator as estimates.
