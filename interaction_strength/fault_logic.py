import itertools

def analyse_fault(array, fault_mask):
    """
    Determines if each interaction strength t is 'valid'.
    t is valid if there is at least one t-way interaction in the faulty rows
    that does not appear in any of the non-faulty rows.
    
    array: list of lists (the test cases)
    fault_mask: list of booleans (True if the row is faulty)
    """
    N = len(array)
    if N == 0:
        return []
    
    k = len(array[0])
    faulty_rows = [array[i] for i in range(N) if fault_mask[i]]
    non_faulty_rows = [array[i] for i in range(N) if not fault_mask[i]]
    
    results = []
    
    for t in range(1, k + 1):
        separator_sets = []
        
        # Check every combination of t columns
        for cols in itertools.combinations(range(k), t):
            fault_tuples = set()
            for row in faulty_rows:
                fault_tuples.add(tuple(row[c] for c in cols))
            
            non_fault_tuples = set()
            for row in non_faulty_rows:
                non_fault_tuples.add(tuple(row[c] for c in cols))
            
            # Disjoint sets mean these columns can separate faults from non-faults
            if fault_tuples.isdisjoint(non_fault_tuples):
                separator_sets.append({
                    "cols": list(cols),
                    "unique_fault_tuples": [list(tp) for tp in sorted(list(fault_tuples))[:100]]
                })
        
        results.append({
            "t": t,
            "valid": len(separator_sets) > 0,
            "separator_count": len(separator_sets),
            "separators": separator_sets[:50] # Limit for UI
        })
        
    return results
