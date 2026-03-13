"""
Flask web app for t-way covering arrays and orthogonal array analysis.

Run:
    cd misc-scripts
    pip install flask
    python app/app.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, render_template, request, jsonify
from tway.core import generate_tway
from tway.display import tway_result
from oa.core import analyse_oa
from moa.core import analyse_moa

app = Flask(__name__, template_folder="templates")


@app.route("/")
def index():
    return render_template("index.html")


# ── T-way ─────────────────────────────────────────────────────────────────────

@app.route("/tway")
def tway_page():
    return render_template("tway.html")


@app.route("/api/tway", methods=["POST"])
def api_tway():
    data = request.get_json()
    try:
        strength = int(data.get("strength", 2))
        factors = data.get("factors", [])  # list of {name, levels}

        if len(factors) < strength:
            return jsonify({"error": f"Need at least {strength} factors for {strength}-way testing."}), 400

        levels_per_factor = []
        factor_names = []
        for f in factors:
            name = str(f.get("name", "")).strip() or None
            lvl = int(f.get("levels", 2))
            if lvl < 2:
                return jsonify({"error": f"Each factor needs at least 2 levels."}), 400
            levels_per_factor.append(lvl)
            factor_names.append(name or f"F{len(factor_names)}")

        test_cases = generate_tway(levels_per_factor, strength)
        result = tway_result(test_cases, levels_per_factor, strength, factor_names)
        return jsonify(result)

    except (ValueError, TypeError, KeyError) as e:
        return jsonify({"error": str(e)}), 400


# ── Orthogonal Array ───────────────────────────────────────────────────────────

@app.route("/oa")
def oa_page():
    return render_template("oa.html")


@app.route("/api/oa", methods=["POST"])
def api_oa():
    data = request.get_json()
    try:
        raw = data.get("array", [])
        if not raw:
            return jsonify({"error": "No array provided."}), 400

        # Parse: each cell is an int
        array = []
        for row in raw:
            parsed_row = []
            for cell in row:
                val = str(cell).strip()
                if val == "":
                    return jsonify({"error": "Array contains empty cells."}), 400
                parsed_row.append(int(val))
            array.append(parsed_row)

        result = analyse_oa(array)

        # Convert dataclass to dict for JSON
        return jsonify({
            "N": result.N,
            "k": result.k,
            "s": result.s,
            "mixed": result.mixed,
            "symbols": [list(s) for s in result.symbols],
            "strength": result.strength,
            "index": result.index,
            "oa_notation": result.oa_notation,
            "l_notation": result.l_notation,
            "is_valid_oa": result.is_valid_oa,
            "errors": result.errors,
            "strength_checks": result.strength_checks,
        })

    except (ValueError, TypeError) as e:
        return jsonify({"error": str(e)}), 400


# ── Mixed Orthogonal Array ─────────────────────────────────────────────────────

@app.route("/moa")
def moa_page():
    return render_template("moa.html")


@app.route("/api/moa", methods=["POST"])
def api_moa():
    data = request.get_json()
    try:
        raw = data.get("array", [])
        groups_raw = data.get("groups", [])   # list of {s, k}
        t_requested = int(data.get("t", 2))

        if not raw:
            return jsonify({"error": "No array provided."}), 400
        if not groups_raw:
            return jsonify({"error": "No groups provided."}), 400

        # Parse groups: [{s: int, k: int}, ...]
        groups = []
        for g in groups_raw:
            s = int(g.get("s", 2))
            k = int(g.get("k", 1))
            if s < 2:
                return jsonify({"error": "Each group needs at least 2 symbols."}), 400
            if k < 1:
                return jsonify({"error": "Each group needs at least 1 column."}), 400
            groups.append((s, k))

        # Parse array
        array = []
        for row in raw:
            parsed_row = []
            for cell in row:
                val = str(cell).strip()
                if val == "":
                    return jsonify({"error": "Array contains empty cells."}), 400
                parsed_row.append(int(val))
            array.append(parsed_row)

        result = analyse_moa(array, groups, t_requested)

        return jsonify({
            "N": result.N,
            "k": result.k,
            "groups": [{"s": s, "k": k} for s, k in result.groups],
            "t_requested": result.t_requested,
            "col_s": result.col_s,
            "col_symbols": result.col_symbols,
            "strength": result.strength,
            "index": result.index,
            "moa_notation": result.moa_notation,
            "is_valid_moa": result.is_valid_moa,
            "errors": result.errors,
            "strength_checks": result.strength_checks,
        })

    except (ValueError, TypeError, KeyError) as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    app.run(debug=True, port=5050)
