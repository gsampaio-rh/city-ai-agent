# services/llm.py
import json
import re
import time
import ollama
import config

def generate_triage_summary(
    geo_info,
    lat,
    lon,
    caption=None,
    tags=None,
    severity=None,
    traffic_data=None,
    facility_flags=None,
    organized_amenities=None,
    retry_attempts=3,
):
    """
    Builds and sends a prompt to the LLM for generating a triage summary.
    The caption and tags parameters are optional.
    
    If no caption is provided, an empty string is used.
    If no tags are provided, an empty list is used.
    
    Retries a number of times if errors occur.
    """
    # Assign default values if not provided.
    caption = caption if caption is not None else ""
    tags = tags if tags is not None else []
    traffic_data = traffic_data if traffic_data is not None else {}
    facility_flags = facility_flags if facility_flags is not None else {}
    organized_amenities = organized_amenities if organized_amenities is not None else {}

    summary_payload = {
        "location": {
            "display_name": geo_info.get("display_name"),
            "coordinates": {"lat": lat, "lon": lon},
            "city": geo_info.get("address", {}).get("city"),
            "road": geo_info.get("address", {}).get("road"),
        },
        "caption": caption,
        "tags": tags,
        "severity": severity,
        "traffic": traffic_data.get("tags", {}),
        "facility_risk": {},  # Could be precomputed by a risk function if needed.
        "amenity_types": list(organized_amenities.keys()),
    }

    prompt = f"""
<|begin_of_text|>

You are a municipal AI agent that summarizes pothole triage cases for dispatchers and city planners.

Given the structured input below, generate a 3–5 sentence summary covering:
- 📍 Location and road name
- 🕳️ Severity and key visual tags
- 🚦 Road type, speed, and rules
- 🏥 Risk level based on proximity to hospitals, schools, etc.
- 🧱 Contextual environment (e.g. presence of amenities)

Use this structured data:
```json
{json.dumps(summary_payload, indent=2)}
```

Answer a 100% BR Portuguese. Respond with only the summary. No title, no comments, no JSON.
<|eot_id|>
"""

    attempt = 0
    last_exception = None
    while attempt < retry_attempts:
        try:
            response = ollama.chat(
                model=config.LLAMA_MODEL_DEFAULT,
                messages=[{"role": "user", "content": prompt}],
            )
            return response["message"]["content"].strip()
        except Exception as e:
            last_exception = e
            attempt += 1
            time.sleep(1)
    return f"(Triage Summary Error: {str(last_exception)})"


def generate_llm_insight(image_path, caption=None, top_tags=None, retry_attempts=3):
    """
    Asks the LLM (with vision support) to produce image insights.
    The caption and top_tags parameters are optional.
    
    If no caption is provided, an empty string is used.
    If no top_tags are provided, an empty list is used.
    
    The prompt instructs the model to return a JSON object in the specified format.
    """
    caption = caption if caption is not None else ""
    top_tags = top_tags if top_tags is not None else []
    
    prompt = f"""
<|begin_of_text|><|image|>

You are a visual scene tagging expert creating high-quality datasets for an AI pothole triage agent.

Your task is to return a valid JSON object in this format:

```json
{{
"caption": "<short sentence (5–15 words)>",
"tags": ["<tag1>", "<tag2>", "..."]
}}
```

All tags must be:
- ✅ lowercase
- ✅ single words
- ✅ strictly based on visible elements
- ❌ no guesses, no emotions, no inferred context

### 🔖 Example
```json
{{
"caption": "large pothole on residential road with houses nearby",
"tags": ["pothole", "patch", "asphalt", "house", "tree", "road", "sidewalk", "wall", "curb", "shadow"]
}}
```

Now, analyze the uploaded image and return your response in the exact JSON format — no narration, no extra explanation.
<|eot_id|>
"""
    attempt = 0
    last_exception = None
    while attempt < retry_attempts:
        try:
            response = ollama.chat(
                model=config.LLAMA_VISION_MODEL,
                messages=[{"role": "user", "content": prompt, "images": [image_path]}],
                stream=False,  # Service layer waits for a complete response.
            )
            raw_response = response["message"]["content"]
            json_match = re.search(r"\{.*\}", raw_response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            else:
                raise ValueError("No valid JSON found in model output")
        except Exception as e:
            last_exception = e
            attempt += 1
            time.sleep(1)
    return {
        "caption": caption,
        "tags": top_tags,
        "triage_notes": f"(LLaMA 3.2 error – {str(last_exception)})",
    }
