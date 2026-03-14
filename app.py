"""
Flask API for Heat Sink Thermal Assessment
==========================================
Endpoints:
  GET  /              – Web UI with interactive form
  POST /api/calculate – JSON API for thermal resistance calculation
"""

from flask import Flask, request, jsonify, render_template
from thermal_model import compute_thermal_resistance, DEFAULT_PARAMS

app = Flask(__name__)


@app.route("/")
def index():
    """Serve the web UI."""
    return render_template("index.html", defaults=DEFAULT_PARAMS)


@app.route("/api/calculate", methods=["POST"])
def calculate():
    """
    JSON API endpoint.

    Accepts a JSON body with any subset of the input parameters.
    Missing keys fall back to DEFAULT_PARAMS.

    Returns the full results dictionary.
    """
    try:
        data = request.get_json(silent=True) or {}

        # Merge user-supplied values over defaults
        params = {**DEFAULT_PARAMS}
        for key in DEFAULT_PARAMS:
            if key in data:
                try:
                    params[key] = float(data[key])
                except (ValueError, TypeError):
                    return jsonify({"error": f"Invalid value for '{key}': {data[key]}"}), 400

        results = compute_thermal_resistance(params)
        return jsonify({"success": True, "data": results})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
