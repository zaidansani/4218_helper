"""
Core t-way covering array algorithm.
All functions are pure (no I/O) and return data structures.
"""

from itertools import combinations, product


def build_uncovered_tuples(levels_per_factor, strength):
    uncovered = set()
    for factors in combinations(range(len(levels_per_factor)), strength):
        for values in product(*[range(levels_per_factor[f]) for f in factors]):
            key = tuple(x for pair in zip(factors, values) for x in pair)
            uncovered.add(key)
    return uncovered


def test_covers(test_case, levels_per_factor, strength):
    covered = set()
    for factors in combinations(range(len(levels_per_factor)), strength):
        values = tuple(test_case[f] for f in factors)
        key = tuple(x for pair in zip(factors, values) for x in pair)
        covered.add(key)
    return covered


def score_candidate(candidate, uncovered, levels_per_factor, strength):
    count = 0
    for factors in combinations(range(len(levels_per_factor)), strength):
        values = tuple(candidate[f] for f in factors)
        key = tuple(x for pair in zip(factors, values) for x in pair)
        if key in uncovered:
            count += 1
    return count


def generate_tway(levels_per_factor, strength=2):
    """
    Greedy t-way covering-array construction.

    Returns a list of test cases (tuples of level indices).
    """
    uncovered = build_uncovered_tuples(levels_per_factor, strength)
    test_cases = []
    all_candidates = list(product(*[range(k) for k in levels_per_factor]))

    while uncovered:
        best = max(
            all_candidates,
            key=lambda c: score_candidate(c, uncovered, levels_per_factor, strength),
        )
        test_cases.append(best)
        uncovered -= test_covers(best, levels_per_factor, strength)

    return test_cases
