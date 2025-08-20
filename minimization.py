from dfa import DFA

def minimize_dfa_table_filling_with_steps(dfa):
    """
    Minimize a DFA using the Table-Filling Algorithm with step-by-step tracking.
    Returns the minimized DFA and detailed steps for visualization.
    """
    # First, remove unreachable states
    dfa = dfa.remove_unreachable_states()
    
    # Initialize tracking for visualization
    steps = []
    states_list = sorted(list(dfa.states))
    n = len(states_list)
    
    # If there's only one state, the DFA is already minimal
    if len(dfa.states) <= 1:
        return dfa, steps
    
    # Initialize the distinguishability table
    distinguishable = {}
    table_state = {}
    
    # Initialize all pairs as indistinguishable
    for i in range(len(states_list)):
        for j in range(i + 1, len(states_list)):
            p, q = states_list[i], states_list[j]
            distinguishable[(p, q)] = False
            distinguishable[(q, p)] = False
            table_state[(p, q)] = {'marked': False, 'reason': None, 'iteration': -1}
    
    # Step 1: Mark pairs where one state is accepting and the other is not
    initial_marks = []
    for p in dfa.states:
        for q in dfa.states:
            if p != q and p < q:  # Only process each pair once
                if (p in dfa.accept_states) != (q in dfa.accept_states):
                    distinguishable[(p, q)] = True
                    distinguishable[(q, p)] = True
                    table_state[(p, q)] = {
                        'marked': True, 
                        'reason': f"State {p} {'is' if p in dfa.accept_states else 'is not'} accepting, state {q} {'is' if q in dfa.accept_states else 'is not'} accepting",
                        'iteration': 0
                    }
                    initial_marks.append((p, q))
    
    steps.append({
        'iteration': 0,
        'description': 'Initial marking: Mark pairs where one state is accepting and the other is not',
        'table_snapshot': create_table_snapshot(states_list, table_state),
        'newly_marked': initial_marks,
        'total_marked': len(initial_marks)
    })
    
    # Iteratively mark more pairs as distinguishable
    iteration = 1
    while True:
        changed = False
        newly_marked = []
        
        for p in dfa.states:
            for q in dfa.states:
                if p < q and not distinguishable.get((p, q), False):
                    for symbol in sorted(dfa.alphabet):
                        p_next = dfa.transitions[(p, symbol)]
                        q_next = dfa.transitions[(q, symbol)]
                        
                        if p_next != q_next and distinguishable.get((p_next, q_next), False):
                            distinguishable[(p, q)] = True
                            distinguishable[(q, p)] = True
                            table_state[(p, q)] = {
                                'marked': True,
                                'reason': f"δ({p}, {symbol}) = {p_next} and δ({q}, {symbol}) = {q_next} are distinguishable",
                                'iteration': iteration
                            }
                            newly_marked.append((p, q))
                            changed = True
                            break
        
        if newly_marked:
            total_marked = sum(1 for state in table_state.values() if state['marked'])
            steps.append({
                'iteration': iteration,
                'description': f'Iteration {iteration}: Mark pairs whose transitions lead to already distinguishable states',
                'table_snapshot': create_table_snapshot(states_list, table_state),
                'newly_marked': newly_marked,
                'total_marked': total_marked
            })
            iteration += 1
        
        if not changed:
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
    
    # Add final step showing equivalence classes
    steps.append({
        'iteration': iteration,
        'description': 'Final result: Equivalent states grouped together',
        'table_snapshot': create_table_snapshot(states_list, table_state),
        'equivalence_classes': {repr: list(eq_class) for repr, eq_class in equivalence_classes.items()},
        'total_marked': sum(1 for state in table_state.values() if state['marked'])
    })
    
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
    
    minimized_dfa = DFA(new_states, dfa.alphabet, new_transitions, new_start_state, new_accept_states)
    
    return minimized_dfa, steps

def create_table_snapshot(states_list, table_state):
    """Create a snapshot of the current table state for visualization"""
    n = len(states_list)
    table = []
    
    for i in range(n - 1):
        row = []
        for j in range(i + 1, n):
            p, q = states_list[i], states_list[j]
            state_info = table_state.get((p, q), {'marked': False, 'reason': None, 'iteration': -1})
            row.append({
                'states': (p, q),
                'marked': state_info['marked'],
                'reason': state_info['reason'],
                'iteration': state_info['iteration']
            })
        table.append(row)
    
    return {
        'states': states_list,
        'table': table
    }

def check_dfa_equivalence(dfa1, dfa2):
    """
    Check if two DFAs are equivalent (accept the same language).
    Returns equivalence status and a counterexample if not equivalent.
    """
    # Simple approach: construct product automaton and check for reachable states
    # where one DFA accepts and the other doesn't
    
    if dfa1.alphabet != dfa2.alphabet:
        return {
            'equivalent': False,
            'reason': 'Different alphabets',
            'counterexample': None
        }
    
    # BFS to explore all reachable state pairs
    visited = set()
    queue = [(dfa1.start_state, dfa2.start_state, "")]
    
    while queue:
        s1, s2, path = queue.pop(0)
        
        if (s1, s2) in visited:
            continue
        visited.add((s1, s2))
        
        # Check if current states have different acceptance
        accept1 = s1 in dfa1.accept_states
        accept2 = s2 in dfa2.accept_states
        
        if accept1 != accept2:
            return {
                'equivalent': False,
                'reason': f'String "{path}" is accepted by one DFA but not the other',
                'counterexample': path,
                'dfa1_accepts': accept1,
                'dfa2_accepts': accept2
            }
        
        # Explore transitions
        for symbol in sorted(dfa1.alphabet):
            try:
                next1 = dfa1.transitions[(s1, symbol)]
                next2 = dfa2.transitions[(s2, symbol)]
                new_path = path + symbol
                
                # Limit path length to prevent infinite exploration
                if len(new_path) <= 20:  # Reasonable limit
                    queue.append((next1, next2, new_path))
            except KeyError:
                # Handle incomplete transition functions
                return {
                    'equivalent': False,
                    'reason': 'Incomplete transition function',
                    'counterexample': path + symbol
                }
    
    return {
        'equivalent': True,
        'reason': 'DFAs accept the same language',
        'counterexample': None
    }

def get_dfa_metrics(original_dfa, minimized_dfa):
    """Calculate performance metrics comparing original and minimized DFAs"""
    return {
        'original_states': len(original_dfa.states),
        'minimized_states': len(minimized_dfa.states),
        'states_reduced': len(original_dfa.states) - len(minimized_dfa.states),
        'reduction_percentage': round((len(original_dfa.states) - len(minimized_dfa.states)) / len(original_dfa.states) * 100, 2) if len(original_dfa.states) > 0 else 0,
        'original_transitions': len(original_dfa.transitions),
        'minimized_transitions': len(minimized_dfa.transitions),
        'transitions_reduced': len(original_dfa.transitions) - len(minimized_dfa.transitions),
        'alphabet_size': len(original_dfa.alphabet),
        'space_complexity_improvement': f"O({len(original_dfa.states)}²) → O({len(minimized_dfa.states)}²)"
    }