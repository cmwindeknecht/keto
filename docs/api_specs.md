# API Specifications

**Fill this in as you build endpoints**

## Go API Gateway (Public Endpoints)

### GET /api/games/search
Query parameters:
- `q` (string): Search query
- `limit` (int): Max results (default: 20)
- `offset` (int): Pagination offset

Response:
```json
{
  "games": [...],
  "total": 150,
  "limit": 20,
  "offset": 0
}
```

### GET /api/games/:id
Response:
```json
{
  "id": 1,
  "steam_app_id": 570,
  "name": "Dota 2",
  "price_history": [...],
  "reviews": {...}
}
```

## FastAPI Internal Service

### POST /internal/games/fetch
Fetches game data from Steam API

Request:
```json
{
  "steam_app_id": 570
}
```

Response:
```json
{
  "success": true,
  "game_id": 1
}
```