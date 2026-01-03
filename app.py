"""
NameWrite - A web application for naming things using LLMs
Flask backend with Vue.js + Vuetify frontend
Uses OpenRouter API for LLM-powered name generation
"""

import os
import json
import random
import requests
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# OpenRouter configuration
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

# Fallback names when API is unavailable
FALLBACK_NAMES = {
    "project": ["Aurora", "Nexus", "Spark", "Horizon", "Pulse", "Echo", "Nova", "Zenith", "Apex", "Ember"],
    "variable": ["dataProcessor", "resultHandler", "configManager", "eventDispatcher", "stateController", "cacheStore"],
    "company": ["TechFlow", "InnoVerse", "CloudPeak", "DataSphere", "ByteWave", "CodeCraft", "PixelForge", "NetPulse"],
    "pet": ["Luna", "Max", "Bella", "Charlie", "Milo", "Daisy", "Rocky", "Coco", "Buddy", "Sadie"]
}

CATEGORY_PROMPTS = {
    "project": "creative software project names that are memorable and modern",
    "variable": "clean, descriptive variable names following camelCase convention",
    "company": "catchy tech startup company names that are brandable",
    "pet": "cute and friendly pet names"
}


def generate_names_with_llm(category: str, context: str, count: int) -> list[str]:
    """Generate names using OpenRouter API."""
    if not OPENROUTER_API_KEY:
        return None

    category_desc = CATEGORY_PROMPTS.get(category, CATEGORY_PROMPTS["project"])

    prompt = f"""Generate exactly {count} {category_desc}.
{f'Context/theme: {context}' if context else ''}

Return ONLY a JSON array of strings, nothing else. Example: ["Name1", "Name2", "Name3"]"""

    try:
        response = requests.post(
            OPENROUTER_BASE_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://namewrite.app",
                "X-Title": "NameWrite"
            },
            json={
                "model": "openai/gpt-5-nano",
                "messages": [
                    {"role": "system", "content": "You are a creative naming assistant. Always respond with only a valid JSON array of strings."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.8,
                "max_tokens": 200
            },
            timeout=30
        )

        # Log response details for debugging
        app.logger.info(f"OpenRouter response status: {response.status_code}")
        if response.status_code != 200:
            app.logger.warning(f"OpenRouter error response: {response.text}")
            return None

        result = response.json()

        # Check for API error in response
        if "error" in result:
            app.logger.warning(f"OpenRouter API error: {result['error']}")
            return None

        content = result["choices"][0]["message"]["content"]
        app.logger.info(f"LLM raw response: '{content}'")
        content = content.strip()

        # Handle empty response
        if not content:
            app.logger.warning("LLM returned empty content")
            return None

        # Parse the JSON array from response
        names = json.loads(content)
        if isinstance(names, list) and all(isinstance(n, str) for n in names):
            return names[:count]
    except requests.exceptions.RequestException as e:
        app.logger.warning(f"OpenRouter request failed: {e}")
    except json.JSONDecodeError as e:
        app.logger.warning(f"Failed to parse response JSON: {e}")
    except KeyError as e:
        app.logger.warning(f"Unexpected response format, missing key: {e}")
    except Exception as e:
        app.logger.warning(f"OpenRouter API error: {e}")

    return None


@app.route("/")
def index():
    """Serve the main Vue.js application."""
    return render_template("index.html")


@app.route("/api/categories")
def get_categories():
    """Return available naming categories."""
    return jsonify(list(CATEGORY_PROMPTS.keys()))


@app.route("/api/generate", methods=["POST"])
def generate_names():
    """Generate name suggestions based on category and context."""
    data = request.get_json()
    category = data.get("category", "project")
    context = data.get("context", "")
    count = min(data.get("count", 5), 10)

    # Try LLM generation first
    suggestions = generate_names_with_llm(category, context, count)
    used_llm = suggestions is not None

    # Fallback to random names if LLM unavailable
    if not suggestions:
        base_names = FALLBACK_NAMES.get(category, FALLBACK_NAMES["project"])
        suggestions = random.sample(base_names, min(count, len(base_names)))

    return jsonify({
        "category": category,
        "context": context,
        "suggestions": suggestions,
        "source": "llm" if used_llm else "fallback"
    })


@app.route("/api/status")
def status():
    """Return API status including whether LLM is configured."""
    return jsonify({
        "app": "NameWrite",
        "llm_configured": bool(OPENROUTER_API_KEY),
        "llm_provider": "OpenRouter" if OPENROUTER_API_KEY else None
    })


@app.route("/api/health")
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "app": "NameWrite"})


def print_startup_info():
    """Print OpenRouter configuration status on startup."""
    print("\n" + "=" * 50)
    print("NameWrite - AI-Powered Name Generator")
    print("=" * 50)
    if OPENROUTER_API_KEY:
        print("OpenRouter: ENABLED")
        print("Model: openai/gpt-5-nano")
        print("Names will be generated using AI")
    else:
        print("OpenRouter: DISABLED")
        print("Reason: OPENROUTER_API_KEY environment variable not set")
        print("Names will use fallback random selection")
        print("\nTo enable OpenRouter, run:")
        print("  export OPENROUTER_API_KEY='your-api-key-here'")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    print_startup_info()
    app.run(debug=True, host="0.0.0.0", port=8080)
