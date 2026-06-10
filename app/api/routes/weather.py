"""Real-time weather at an incident's location, with a disaster-aware risk note.

Proxies OpenWeather's free *Current Weather* API server-side so the browser
never sees the API key and CORS is a non-issue. The headline feature isn't the
raw reading — it's the ``risk_note``: the same fire is far more dangerous under
strong wind than under torrential rain, and a flood is graver in freezing
weather than under a warm sun. We turn the forecast into that operational signal.

Endpoint::

    GET /api/v1/weather?lat=45.6&lon=24.97&disaster_type=Wildfire

``disaster_type`` is optional; without it you get the plain reading, no note.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.config import get_settings
from app.schemas.responses import WeatherResponse

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["weather"])

# OpenWeather refreshes a given point roughly every 10 min; a short TTL cache
# keyed by rounded coordinates spares the free quota when operators reopen the
# same incident or several incidents share a city.
_CACHE_TTL_SECONDS = 600.0
_cache: dict[tuple[float, float], tuple[float, dict]] = {}


def _assess_risk(
    disaster_type: str,
    *,
    wind_ms: float,
    wind_kmh: float,
    rain_mm: float,
    snow_mm: float,
    temp_c: float,
    humidity: int,
) -> tuple[str | None, str | None]:
    """Map (disaster, weather) → (risk_level, note). Returns (None, None) when
    the disaster type has no meaningful weather coupling.

    Levels: ``elevated`` (weather worsens the situation), ``reduced`` (weather
    helps), ``normal`` (no material effect)."""
    kmh = round(wind_kmh)
    wet = rain_mm > 0 or snow_mm > 0

    if disaster_type == "Wildfire":
        if rain_mm > 0:
            return "reduced", (
                "Active rainfall in the area — lower fire-spread risk; crews can "
                "focus on extinguishing the structure rather than the surroundings."
            )
        if wind_ms >= 11:
            return "elevated", (
                f"Strong wind ({kmh} km/h) — high risk of the fire spreading to "
                "adjacent buildings and trees; watch the surroundings closely."
            )
        if wind_ms >= 6:
            return "elevated", (
                f"Moderate wind ({kmh} km/h) — some risk of the fire reaching "
                "nearby vegetation; keep an eye on neighbouring structures."
            )
        if humidity >= 75:
            return "reduced", (
                f"High humidity ({humidity}%) — damp conditions slow fire spread."
            )
        return "normal", "Calm, dry conditions — fire behaviour likely stable."

    if disaster_type == "Flood":
        if rain_mm > 0:
            return "elevated", (
                "Active precipitation — water levels may keep rising; expect the "
                "situation to worsen before it improves."
            )
        if temp_c < 5:
            return "elevated", (
                f"Low temperature ({round(temp_c)}°C) — hypothermia risk for people "
                "in the water or evacuated; dispatch warming and medical support."
            )
        return "reduced", "Dry, mild conditions — water levels likely receding."

    if disaster_type == "Car Crash":
        if wet or temp_c <= 2:
            return "elevated", (
                "Wet or icy road conditions — risk of secondary collisions; secure "
                "the scene and warn approaching traffic early."
            )
        return "normal", "Dry road, good conditions — low risk of secondary collisions."

    if disaster_type == "Cyclone":
        if wind_ms >= 17:
            return "elevated", (
                f"Storm-force wind ({kmh} km/h) — expect structural damage and "
                "flying debris; keep responders and residents sheltered."
            )
        if wind_ms >= 11:
            return "elevated", (
                f"Strong wind ({kmh} km/h) — conditions still hazardous; approach "
                "with caution."
            )
        return "reduced", "Winds easing — conditions improving for response teams."

    if disaster_type == "Earthquake":
        if wet or temp_c < 5:
            return "elevated", (
                "Cold or wet weather complicates search-and-rescue and shelter for "
                "displaced residents; arrange warm, covered staging areas."
            )
        return "normal", "Mild, dry weather — favourable conditions for rescue work."

    return None, None


def _to_response(data: dict, disaster_type: str | None) -> WeatherResponse:
    """Shape a raw OpenWeather *Current Weather* payload into our schema."""
    weather = (data.get("weather") or [{}])[0]
    main = data.get("main") or {}
    wind = data.get("wind") or {}
    rain = data.get("rain") or {}
    snow = data.get("snow") or {}

    wind_ms = float(wind.get("speed") or 0.0)
    wind_kmh = round(wind_ms * 3.6, 1)
    rain_mm = float(rain.get("1h") or 0.0)
    snow_mm = float(snow.get("1h") or 0.0)
    temp_c = float(main.get("temp") or 0.0)
    humidity = int(main.get("humidity") or 0)

    risk_level = risk_note = None
    if disaster_type:
        risk_level, risk_note = _assess_risk(
            disaster_type,
            wind_ms=wind_ms, wind_kmh=wind_kmh,
            rain_mm=rain_mm, snow_mm=snow_mm,
            temp_c=temp_c, humidity=humidity,
        )

    observed = data.get("dt")
    observed_at = (
        datetime.fromtimestamp(observed, tz=timezone.utc).isoformat(timespec="seconds")
        if observed else datetime.now(timezone.utc).isoformat(timespec="seconds")
    )

    return WeatherResponse(
        description=(weather.get("description") or "unknown").capitalize(),
        icon=weather.get("icon"),
        temp_c=round(temp_c, 1),
        feels_like_c=round(float(main.get("feels_like") or temp_c), 1),
        humidity_pct=humidity,
        wind_speed_ms=round(wind_ms, 1),
        wind_speed_kmh=wind_kmh,
        wind_gust_ms=round(float(wind["gust"]), 1) if wind.get("gust") is not None else None,
        wind_deg=int(wind["deg"]) if wind.get("deg") is not None else None,
        rain_1h_mm=round(rain_mm, 1) if rain_mm else None,
        snow_1h_mm=round(snow_mm, 1) if snow_mm else None,
        clouds_pct=int(data["clouds"]["all"]) if data.get("clouds", {}).get("all") is not None else None,
        visibility_m=data.get("visibility"),
        observed_at=observed_at,
        place=data.get("name") or None,
        risk_level=risk_level,
        risk_note=risk_note,
    )


async def _fetch_openweather(lat: float, lon: float) -> dict:
    """Call OpenWeather (or serve a cached payload). Raises HTTPException on
    misconfiguration / upstream failure."""
    settings = get_settings()
    if not settings.openweather_api_key:
        raise HTTPException(
            503,
            "Weather lookups are not configured. Set APP_OPENWEATHER_API_KEY to a "
            "free OpenWeather key (https://openweathermap.org/api).",
        )

    key = (round(lat, 2), round(lon, 2))
    hit = _cache.get(key)
    if hit and (time.monotonic() - hit[0]) < _CACHE_TTL_SECONDS:
        return hit[1]

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                settings.openweather_base_url,
                params={
                    "lat": lat, "lon": lon,
                    "appid": settings.openweather_api_key,
                    "units": "metric",
                },
            )
    except httpx.RequestError as exc:
        log.warning("OpenWeather request failed: %s", exc)
        raise HTTPException(502, "Could not reach the weather service.") from exc

    if resp.status_code == 401:
        raise HTTPException(502, "Weather service rejected the API key (401).")
    if resp.status_code != 200:
        raise HTTPException(502, f"Weather service returned {resp.status_code}.")

    data = resp.json()
    _cache[key] = (time.monotonic(), data)
    return data


@router.get("/weather", response_model=WeatherResponse)
async def weather(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    disaster_type: str | None = Query(
        None, description="Incident class — enables the contextual risk note"
    ),
) -> WeatherResponse:
    """Current conditions at ``(lat, lon)`` plus, when ``disaster_type`` is
    given, a one-line operational risk note."""
    data = await _fetch_openweather(lat, lon)
    return _to_response(data, disaster_type)
