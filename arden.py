from typing import Dict, Tuple, List

from dfa import DFA
from regex_utils import re_union, re_concat, re_star, EMPTY, EPS


def dfa_to_regex_arden(dfa: DFA) -> Dict:
    # Work on a trimmed DFA to avoid unreachable states affecting equations
    trimmed = dfa.remove_unreachable_states()

    # Order states deterministically
    states = sorted(list(trimmed.states))

    # Build coefficients R_{i,j} and constants C_i
    R: Dict[Tuple[str, str], str] = {}
    C: Dict[str, str] = {}

    # Initialize C_i (epsilon if accepting, else empty)
    for s in states:
        C[s] = EPS if s in trimmed.accept_states else EMPTY

    # For each pair, collect union of symbols causing transition i -a-> j
    symbols_to_targets: Dict[Tuple[str, str], List[str]] = {}
    for (s, a), t in trimmed.transitions.items():
        key = (s, t)
        symbols_to_targets.setdefault(key, []).append(a)

    for (i_state, j_state), syms in symbols_to_targets.items():
        syms_sorted = sorted(set(str(x) for x in syms))
        coeff = '|'.join(syms_sorted) if len(syms_sorted) > 1 else syms_sorted[0]
        R[(i_state, j_state)] = coeff

    # Elimination order: eliminate all except start_state, from the end
    order = [s for s in states if s != trimmed.start_state]

    steps: List[Dict] = []

    for k in order[::-1]:
        Rkk = R.get((k, k), EMPTY)
        star = re_star(Rkk)
        Ck = C.get(k, EMPTY)
        step = {
            'eliminate': k,
            'Rkk': Rkk,
            'Rkk_star': star,
            'updates': {
                'constants': [],
                'coefficients': []
            }
        }
        new_R: Dict[Tuple[str, str], str] = {}
        new_C: Dict[str, str] = {}
        for i in states:
            if i == k:
                continue
            Rik = R.get((i, k), EMPTY)
            # constants: C[i] := C[i] | Rik Rkk* Ck
            const_before = C.get(i, EMPTY)
            const_term = re_concat(re_concat(Rik, star), Ck)
            const_after = re_union([const_before, const_term])
            new_C[i] = const_after
            step['updates']['constants'].append({
                'i': i,
                'before': const_before,
                'term': (f"R[{i},{k}] {star} {Ck}" if Rik != EMPTY and Ck != EMPTY else EMPTY),
                'after': const_after
            })
            for j in states:
                if j == k:
                    continue
                Rij = R.get((i, j), EMPTY)
                Rkj = R.get((k, j), EMPTY)
                through_k = re_concat(re_concat(Rik, star), Rkj)
                after = re_union([Rij, through_k])
                new_R[(i, j)] = after
                step['updates']['coefficients'].append({
                    'i': i,
                    'j': j,
                    'before': Rij,
                    'term': (f"R[{i},{k}] {star} R[{k},{j}]" if Rik != EMPTY and Rkj != EMPTY else EMPTY),
                    'after': after
                })
        # Remove any coefficients involving k
        for (i, j) in list(R.keys()):
            if i == k or j == k:
                del R[(i, j)]
        # Add updated coefficients, skipping empties
        for (i, j), v in new_R.items():
            if v != EMPTY:
                R[(i, j)] = v
        # Remove C[k] and update others
        if k in C:
            del C[k]
        C.update(new_C)
        steps.append(step)

    s0 = trimmed.start_state
    R00 = R.get((s0, s0), EMPTY)
    regex = re_concat(re_star(R00), C.get(s0, EMPTY))

    return {
        'regex': regex,
        'steps': steps,
        'start_state': s0,
    }
