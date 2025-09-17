from dfa import DFA

def minimize_dfa_table_filling(dfa):
    """
    Minimize a DFA using the Table-Filling Algorithm (Myhill-Nerode Algorithm).
    Returns a tuple: (minimized_dfa, table_filling_data)
    """
    # First, remove unreachable states
    dfa = dfa.remove_unreachable_states()

    # If there's only one state, the DFA is already minimal
    if len(dfa.states) <= 1:
        return dfa, generate_table_filling_data(dfa, {})

    # Initialize the distinguishability table
    # distinguishable[(p, q)] = True if states p and q are distinguishable
    distinguishable = {}

    # Initialize all pairs as indistinguishable
    states_list = list(dfa.states)
    for i in range(len(states_list)):
        for j in range(i + 1, len(states_list)):
            p, q = states_list[i], states_list[j]
            distinguishable[(p, q)] = False
            distinguishable[(q, p)] = False

    # Mark pairs where one state is accepting and the other is not
    for p in dfa.states:
        for q in dfa.states:
            if p != q:
                if (p in dfa.accept_states) != (q in dfa.accept_states):
                    distinguishable[(p, q)] = True

    # Iteratively mark more pairs as distinguishable
    changed = True
    while changed:
        changed = False
        for p in dfa.states:
            for q in dfa.states:
                if p != q and not distinguishable.get((p, q), False):
                    for symbol in dfa.alphabet:
                        p_next = dfa.transitions[(p, symbol)]
                        q_next = dfa.transitions[(q, symbol)]
                        if p_next != q_next and distinguishable.get((p_next, q_next), False):
                            distinguishable[(p, q)] = True
                            distinguishable[(q, p)] = True
                            changed = True
                            break

    # Create equivalence classes based on indistinguishable states
    equivalence_classes = {}
    for state in dfa.states:
        found = False
        for representative in equivalence_classes:
            if not distinguishable.get((state, representative), False):
                equivalence_classes[representative].add(state)
                found = True
                break
        if not found:
            equivalence_classes[state] = {state}

    # Create the minimized DFA
    new_states = set(equivalence_classes.keys())
    new_accept_states = {state for state in new_states if state in dfa.accept_states}

    # Find the new start state
    new_start_state = None
    for representative, eq_class in equivalence_classes.items():
        if dfa.start_state in eq_class:
            new_start_state = representative
            break

    # Create new transitions
    new_transitions = {}
    for representative in new_states:
        for symbol in dfa.alphabet:
            original_next = dfa.transitions[(representative, symbol)]
            for new_state, eq_class in equivalence_classes.items():
                if original_next in eq_class:
                    new_transitions[(representative, symbol)] = new_state
                    break

    # Generate the table filling visualization data
    table_data = generate_table_filling_data(dfa, distinguishable)

    minimized = DFA(new_states, dfa.alphabet, new_transitions, new_start_state, new_accept_states)
    return minimized, table_data

def generate_table_filling_data(dfa, distinguishable):
    """
    Generate data for visualizing the table-filling algorithm.
    """
    states_list = sorted(list(dfa.states))
    n = len(states_list)
    
    table = []
    for i in range(n - 1):
        row = []
        for j in range(i + 1, n):
            p, q = states_list[i], states_list[j]
            is_distinguishable = distinguishable.get((p, q), False)
            row.append(is_distinguishable)
        table.append(row)
    
    return {
        "states": states_list,
        "table": table
    }
