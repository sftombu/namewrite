"""
NameWrite - A web application for naming things using LLMs
Flask backend with Vue.js + Vuetify frontend
"""

from flask import Flask, render_template, jsonify, request
import random

app = Flask(__name__)

# Sample naming suggestions (in a real app, this would use an LLM API)
NAMING_CATEGORIES = {
    "project": [
        "Aurora", "Nexus", "Spark", "Horizon", "Pulse",
        "Echo", "Nova", "Zenith", "Apex", "Ember"
    ],
    "variable": [
        "dataProcessor", "resultHandler", "configManager",
        "eventDispatcher", "stateController", "cacheStore"
    ],
    "company": [
        "TechFlow", "InnoVerse", "CloudPeak", "DataSphere",
        "ByteWave", "CodeCraft", "PixelForge", "NetPulse"
    ],
    "pet": [
        "Luna", "Max", "Bella", "Charlie", "Milo",
        "Daisy", "Rocky", "Coco", "Buddy", "Sadie"
    ]
}


@app.route("/")
def index():
    """Serve the main Vue.js application."""
    return render_template("index.html")


@app.route("/api/categories")
def get_categories():
    """Return available naming categories."""
    return jsonify(list(NAMING_CATEGORIES.keys()))


@app.route("/api/generate", methods=["POST"])
def generate_names():
    """Generate name suggestions based on category and context."""
    data = request.get_json()
    category = data.get("category", "project")
    context = data.get("context", "")
    count = min(data.get("count", 5), 10)

    # Get base suggestions from category
    base_names = NAMING_CATEGORIES.get(category, NAMING_CATEGORIES["project"])
    suggestions = random.sample(base_names, min(count, len(base_names)))

    # Add context-based variations if context provided
    if context:
        context_word = context.split()[0].capitalize() if context else ""
        suggestions = [f"{context_word}{name}" if random.random() > 0.5 else name
                      for name in suggestions]

    return jsonify({
        "category": category,
        "context": context,
        "suggestions": suggestions
    })


@app.route("/api/health")
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "app": "NameWrite"})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
