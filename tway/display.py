"""
Data-oriented display layer for t-way results.

tway_result() returns a plain dict that can be rendered by either
the CLI (print_tway_result) or the Flask app (Jinja templates).
"""

from collections import defaultdict
from itertools import combinations, product


def _factor_letter(i):
    letters = "xyzabcdefghijklmnopqrstuvw"
    if i < len(letters):
        return letters[i]
    i -= len(letters)
    return "a" + chr(ord("a") + i % 26)


def tway_result(test_cases, levels_per_factor, strength=2, factor_names=None):
    """
    Build a data structure describing the t-way result.

    Returns
    -------
    dict with keys:
      strength        int
      strength_name   str  e.g. "Pairwise"
      n_factors       int
      letters         list[str]          symbolic letter per factor
      factor_names    list[str]          human name per factor
      levels_per_factor list[int]
      test_cases      list[dict]         each: {index, values: list[int], symbolic: str}
      coverage        list[dict]         each: {
                                           tuple_str: str,
                                           factors: list[int],
                                           values: list[int],
                                           covered_by: list[dict{index, symbolic, hi_symbolic}]
                                         }
      total_tuples    int
      missing_tuples  int
    """
    n = len(levels_per_factor)
    letters = [_factor_letter(i) for i in range(n)]

    if factor_names is None:
        factor_names = [f"F{i}" for i in range(n)]

    strength_name = {2: "Pairwise", 3: "Three-way"}.get(strength, f"{strength}-way")

    def sym_level(fi, vi):
        return f"{letters[fi]}{vi + 1}"

    def sym_test(tc):
        return "(" + ", ".join(sym_level(fi, vi) for fi, vi in enumerate(tc)) + ")"

    def sym_test_hi(tc, hi_set):
        """Return list of (label, highlighted) per factor position."""
        parts = []
        for fi, vi in enumerate(tc):
            parts.append({"label": sym_level(fi, vi), "highlight": fi in hi_set})
        return parts

    tc_index = {tc: idx + 1 for idx, tc in enumerate(test_cases)}

    # Build test case dicts
    tc_dicts = []
    for idx, tc in enumerate(test_cases):
        tc_dicts.append({
            "index": idx + 1,
            "values": list(tc),
            "symbolic": sym_test(tc),
        })

    # Build coverage index: key -> list[tc]
    tuple_coverage = defaultdict(list)
    for tc in test_cases:
        for factors in combinations(range(n), strength):
            key = tuple(x for pair in zip(factors, (tc[f] for f in factors)) for x in pair)
            tuple_coverage[key].append(tc)

    # Build coverage proof entries
    coverage = []
    missing = 0
    for factors in combinations(range(n), strength):
        for values in product(*[range(levels_per_factor[f]) for f in factors]):
            key = tuple(x for pair in zip(factors, values) for x in pair)
            tuple_str = "(" + ",".join(sym_level(f, v) for f, v in zip(factors, values)) + ")"
            covering_tcs = tuple_coverage.get(key, [])
            covered_by = []
            for tc in covering_tcs:
                covered_by.append({
                    "index": tc_index[tc],
                    "symbolic": sym_test(tc),
                    "parts": sym_test_hi(tc, set(factors)),
                })
            if not covered_by:
                missing += 1
            coverage.append({
                "tuple_str": tuple_str,
                "factors": list(factors),
                "values": list(values),
                "factor_labels": [factor_names[f] for f in factors],
                "level_labels": [sym_level(f, v) for f, v in zip(factors, values)],
                "covered_by": covered_by,
            })

    total_tuples = len(coverage)

    return {
        "strength": strength,
        "strength_name": strength_name,
        "n_factors": n,
        "letters": letters,
        "factor_names": factor_names,
        "levels_per_factor": levels_per_factor,
        "test_cases": tc_dicts,
        "coverage": coverage,
        "total_tuples": total_tuples,
        "missing_tuples": missing,
    }


# ── CLI rendering ─────────────────────────────────────────────────────────────

_BOLD_YELLOW = "\033[1;33m"
_RESET = "\033[0m"


def print_tway_result(result, verbose=False):
    r = result
    strength_name = r["strength_name"]
    letters = r["letters"]
    levels_per_factor = r["levels_per_factor"]

    print(f"\n=== Symbolic View ({strength_name} / t={r['strength']}) ===")
    print("Factors:", "  ".join(f"{l} = Factor {i}" for i, l in enumerate(letters)))
    for letter, k in zip(letters, levels_per_factor):
        print(f"  {letter}: " + "  ".join(f"{letter}{v+1}=level{v+1}" for v in range(k)))

    print("\nTest cases:")
    for tc in r["test_cases"]:
        print(f"  T{tc['index']}: {tc['symbolic']}")

    print(f"\n{strength_name} coverage proof:")
    for entry in r["coverage"]:
        if entry["covered_by"]:
            parts = []
            for cb in entry["covered_by"]:
                hi_set = set(entry["factors"])
                rendered = "(" + ", ".join(
                    f"{_BOLD_YELLOW}{p['label']}{_RESET}" if p["highlight"] else p["label"]
                    for p in cb["parts"]
                ) + ")"
                parts.append(f"T{cb['index']}: {rendered}")
            print(f"  {entry['tuple_str']} -> covered by {', '.join(parts)}")
        else:
            print(f"  {entry['tuple_str']} -> ** MISSING **")

    total = r["total_tuples"]
    missing = r["missing_tuples"]
    print(f"\n  {total - missing}/{total} tuples covered", end="")
    print(" -- all tuples covered" if not missing else f" -- {missing} MISSING")

    if verbose:
        _print_coverage_table(r)


def _print_coverage_table(r):
    strength = r["strength"]
    factor_names = r["factor_names"]
    levels_per_factor = r["levels_per_factor"]
    n = r["n_factors"]

    def make_sep(widths):
        return "+-" + "-+-".join("-" * w for w in widths) + "-+"

    def make_row(cells, widths):
        return "| " + " | ".join(str(c).ljust(w) for c, w in zip(cells, widths)) + " |"

    # Test suite table
    header = ["Test"] + factor_names
    col_widths = [max(4, len(h)) for h in header]
    for tc in r["test_cases"]:
        col_widths[0] = max(col_widths[0], len(str(tc["index"])))
        for fi, vi in enumerate(tc["values"]):
            col_widths[fi + 1] = max(col_widths[fi + 1], len(str(vi)))

    sep = make_sep(col_widths)
    print("\n=== Test Suite ===")
    print(sep)
    print(make_row(header, col_widths))
    print(sep)
    for tc in r["test_cases"]:
        cells = [str(tc["index"])] + [str(v) for v in tc["values"]]
        print(make_row(cells, col_widths))
    print(sep)
    print(f"\nTotal test cases: {len(r['test_cases'])}")

    # Coverage proof table
    factor_headers = [f"Factor {chr(ord('i') + k)}" for k in range(strength)]
    level_headers  = [f"Level {chr(ord('i') + k)}"  for k in range(strength)]
    proof_header = [h for pair in zip(factor_headers, level_headers) for h in pair] + ["Covered by test(s)"]
    proof_widths = [len(h) for h in proof_header]

    rows_data = []
    for entry in r["coverage"]:
        row = []
        for fl, ll in zip(entry["factor_labels"], entry["level_labels"]):
            row += [fl, ll]
        if entry["covered_by"]:
            row.append(", ".join(str(cb["index"]) for cb in entry["covered_by"]))
        else:
            row.append("** MISSING **")
        rows_data.append(row)
        for k, cell in enumerate(row):
            proof_widths[k] = max(proof_widths[k], len(str(cell)))

    strength_label = {2: "Pair", 3: "Triple"}.get(strength, f"{strength}-tuple")
    psep = make_sep(proof_widths)
    print(f"\n=== {strength_label} Coverage Proof ===")
    print(psep)
    print(make_row(proof_header, proof_widths))
    print(psep)
    missing = 0
    for row in rows_data:
        print(make_row(row, proof_widths))
        if "MISSING" in row[-1]:
            missing += 1
    print(psep)
    total = len(rows_data)
    print(f"\nTotal tuples required : {total}")
    print(f"Tuples covered        : {total - missing}")
    if missing:
        print(f"Tuples MISSING        : {missing}  <-- COVERAGE GAP")
    else:
        print("All tuples covered    : YES")
