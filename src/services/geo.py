# services/geo.py
import requests
import json
import config

def forward_geocode(address):
    """
    Converts an address string into geographic coordinates using Nominatim.
    """
    try:
        params = {
            "q": address,
            "format": "json",
            "limit": config.NOMINATIM_SEARCH_LIMIT,
        }
        headers = {"User-Agent": config.NOMINATIM_USER_AGENT}
        response = requests.get(config.NOMINATIM_SEARCH_URL, params=params, headers=headers)
        results = response.json()
        if results:
            return float(results[0]["lat"]), float(results[0]["lon"]), results[0]["display_name"]
        else:
            return None, None, "Endereço não encontrado"
    except Exception as e:
        return None, None, f"Erro ao buscar endereço: {str(e)}"

def reverse_geocode(lat, lon):
    """
    Returns full reverse-geocoded JSON given latitude and longitude.
    """
    try:
        headers = {"User-Agent": config.NOMINATIM_USER_AGENT}
        url = f"{config.NOMINATIM_REVERSE_URL}?lat={lat}&lon={lon}&format=json"
        response = requests.get(url, headers=headers)
        return response.json()
    except Exception:
        return {"error": "Failed to fetch reverse geocoding data"}

def query_all_amenities(lat, lon, radius=config.AMENITY_RADIUS):
    """
    Fetches all amenities around a location within the specified radius.
    """
    query = f"""
        [out:json];
        (
        node["amenity"](around:{radius},{lat},{lon});
        way["amenity"](around:{radius},{lat},{lon});
        relation["amenity"](around:{radius},{lat},{lon});
        );
        out center;
    """
    try:
        response = requests.post(config.OVERPASS_API_URL, data={"data": query})
        data = response.json().get("elements", [])
        return data
    except Exception as e:
        return {"error": str(e)}

def organize_amenities_by_type(amenities):
    """
    Groups amenities by their type.
    """
    grouped = {}
    for item in amenities:
        tags = item.get("tags", {})
        amenity_type = tags.get("amenity", "unknown")
        entry = {
            "name": tags.get("name", "Unnamed"),
            "lat": item.get("lat") or item.get("center", {}).get("lat"),
            "lon": item.get("lon") or item.get("center", {}).get("lon"),
            "tags": tags,
        }
        if amenity_type not in grouped:
            grouped[amenity_type] = []
        grouped[amenity_type].append(entry)
    return grouped

def query_nearby_amenities(lat, lon, types, radius=config.AMENITY_RADIUS):
    """
    Queries nearby amenities of given types.
    """
    all_results = []
    for tag, emoji in types:
        query = f"""
        [out:json];
        (
        node["amenity"="{tag}"](around:{radius},{lat},{lon});
        way["amenity"="{tag}"](around:{radius},{lat},{lon});
        relation["amenity"="{tag}"](around:{radius},{lat},{lon});
        );
        out center;
        """
        try:
            response = requests.post(config.OVERPASS_API_URL, data={"data": query})
            data = response.json()
            all_results.append({
                "tag": tag,
                "emoji": emoji,
                "results": data
            })
        except Exception:
            all_results.append({
                "tag": tag,
                "emoji": emoji,
                "results": {"error": f"Failed to query {tag}"}
            })
    return all_results

def query_traffic_data(lat, lon, street_name=None):
    """
    Queries nearby road data and attempts to match a street name.
    """
    query = f"""
    [out:json];
    way(around:{config.TRAFFIC_RADIUS},{lat},{lon})["highway"];
    out body;
    """
    try:
        response = requests.post(config.OVERPASS_API_URL, data={"data": query})
        elements = response.json().get("elements", [])
        if not elements:
            return {"error": "No roads found near this location"}
        if street_name:
            street_name = street_name.lower().strip()
            for e in elements:
                tags = e.get("tags", {})
                name = tags.get("name", "").lower().strip()
                if name == street_name:
                    return {
                        "matched": True,
                        "street": name,
                        "tags": tags,
                        "raw": e
                    }
        for e in elements:
            tags = e.get("tags", {})
            if "maxspeed" in tags or "lanes" in tags or "surface" in tags:
                return {
                    "matched": False,
                    "street": tags.get("name", "unknown"),
                    "tags": tags,
                    "raw": e
                }
        return {"error": "No traffic-relevant tags found"}
    except Exception as e:
        return {"error": str(e)}