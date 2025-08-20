import os
import json
from flask import Flask, render_template, request, jsonify
from dfa import DFA
from minimization import minimize_dfa_table_filling
import tempfile

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/minimize', methods=['POST'])
def minimize():
    # Get DFA data from request
    data = request.json
    
    try:
        # Create DFA from input data
        dfa = DFA.from_dict(data)
        
        # Minimize the DFA
        minimized_dfa = minimize_dfa_table_filling(dfa)
        
        # Generate visualizations
        original_image = generate_dfa_image(dfa, "original")
        minimized_image = generate_dfa_image(minimized_dfa, "minimized")
        comparison_image = generate_comparison_image(dfa, minimized_dfa)
        
        # Return the results
        return jsonify({
            'success': True,
            'original_dfa': dfa.to_dict(),
            'minimized_dfa': minimized_dfa.to_dict(),
            'original_image': original_image,
            'minimized_image': minimized_image,
            'comparison_image': comparison_image
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def generate_dfa_image(dfa, name):
    """Generate an image of the DFA using Graphviz"""
    import graphviz
    
    # Create a new directed graph
    dot = graphviz.Digraph(comment=f"{name.capitalize()} DFA Visualization")
    dot.attr(rankdir="LR")  # Left to right layout
    
    # Add states
    for state in dfa.states:
        if state == dfa.start_state:
            dot.node(str(state), shape="circle", style="bold")
        elif state in dfa.accept_states:
            dot.node(str(state), shape="doublecircle")
        else:
            dot.node(str(state), shape="circle")
    
    # Add a hidden node for the start arrow
    dot.node("", shape="none")
    dot.edge("", str(dfa.start_state))
    
    # Add transitions
    for (state, symbol), next_state in dfa.transitions.items():
        dot.edge(str(state), str(next_state), label=str(symbol))
    
    # Generate a unique filename
    filename = f"static/images/{name}_{os.urandom(8).hex()}"
    
    # Render the graph
    dot.render(filename, format="png", cleanup=True)
    
    # Return the URL to the image
    return f"{filename}.png"

def generate_comparison_image(original_dfa, minimized_dfa):
    """Generate a comparison image of the original and minimized DFAs"""
    import graphviz
    
    # Create a new directed graph
    dot = graphviz.Digraph(comment="DFA Comparison Visualization")
    dot.attr(rankdir="TB")  # Top to bottom layout
    
    # Create subgraphs for original and minimized DFAs
    with dot.subgraph(name="cluster_original") as c:
        c.attr(label="Original DFA")
        
        # Add states for original DFA
        for state in original_dfa.states:
            if state == original_dfa.start_state:
                c.node(f"orig_{state}", label=str(state), shape="circle", style="bold")
            elif state in original_dfa.accept_states:
                c.node(f"orig_{state}", label=str(state), shape="doublecircle")
            else:
                c.node(f"orig_{state}", label=str(state), shape="circle")
        
        # Add a hidden node for the start arrow
        c.node("orig_start", shape="none", label="")
        c.edge("orig_start", f"orig_{original_dfa.start_state}")
        
        # Add transitions for original DFA
        for (state, symbol), next_state in original_dfa.transitions.items():
            c.edge(f"orig_{state}", f"orig_{next_state}", label=str(symbol))
    
    with dot.subgraph(name="cluster_minimized") as c:
        c.attr(label="Minimized DFA")
        
        # Add states for minimized DFA
        for state in minimized_dfa.states:
            if state == minimized_dfa.start_state:
                c.node(f"min_{state}", label=str(state), shape="circle", style="bold")
            elif state in minimized_dfa.accept_states:
                c.node(f"min_{state}", label=str(state), shape="doublecircle")
            else:
                c.node(f"min_{state}", label=str(state), shape="circle")
        
        # Add a hidden node for the start arrow
        c.node("min_start", shape="none", label="")
        c.edge("min_start", f"min_{minimized_dfa.start_state}")
        
        # Add transitions for minimized DFA
        for (state, symbol), next_state in minimized_dfa.transitions.items():
            c.edge(f"min_{state}", f"min_{next_state}", label=str(symbol))
    
    # Generate a unique filename
    filename = f"static/images/comparison_{os.urandom(8).hex()}"
    
    # Render the graph
    dot.render(filename, format="png", cleanup=True)
    
    # Return the URL to the image
    return f"{filename}.png"

# Add this line to the if __name__ == '__main__': block
# Create the images directory if it doesn't exist
os.makedirs('static/images', exist_ok=True)

@app.route('/test_string', methods=['POST'])
def test_string():
    """Test a string on a DFA and return the sequence of states visited"""
    data = request.json
    
    try:
        # Get the DFA and input string
        dfa_data = data.get('dfa')
        input_string = data.get('input_string')
        
        if not dfa_data or not input_string:
            return jsonify({'success': False, 'error': 'Missing DFA or input string'})
        
        # Create DFA from input data
        dfa = DFA.from_dict(dfa_data)
        
        # Process the string and get the trace
        result = dfa.process_string_with_trace(input_string)
        
        # Generate a visualization of the path
        path_image = generate_path_visualization(dfa, input_string, result['trace'])
        
        return jsonify({
            'success': True,
            'trace': result['trace'],
            'accepted': result['accepted'],
            'path_image': path_image
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def generate_path_visualization(dfa, input_string, trace):
    """Generate a visualization of the path taken through the DFA"""
    import graphviz
    
    # Create a new directed graph
    dot = graphviz.Digraph(comment="DFA Path Visualization")
    dot.attr(rankdir="LR")  # Left to right layout
    
    # Add states
    for state in dfa.states:
        if state in trace:
            # Highlight states in the path
            if state == dfa.start_state:
                dot.node(str(state), shape="circle", style="bold,filled", fillcolor="lightblue")
            elif state in dfa.accept_states:
                dot.node(str(state), shape="doublecircle", style="filled", fillcolor="lightgreen")
            else:
                dot.node(str(state), shape="circle", style="filled", fillcolor="lightblue")
        else:
            # Regular states not in the path
            if state == dfa.start_state:
                dot.node(str(state), shape="circle", style="bold")
            elif state in dfa.accept_states:
                dot.node(str(state), shape="doublecircle")
            else:
                dot.node(str(state), shape="circle")
    
    # Add a hidden node for the start arrow
    dot.node("", shape="none")
    dot.edge("", str(dfa.start_state))
    
    # Add transitions
    for (state, symbol), next_state in dfa.transitions.items():
        # Check if this transition is part of the path
        is_path_transition = False
        for i in range(len(trace) - 1):
            if trace[i] == state and trace[i+1] == next_state and i < len(input_string) and input_string[i] == symbol:
                is_path_transition = True
                break
        
        if is_path_transition:
            # Highlight transitions in the path
            dot.edge(str(state), str(next_state), label=str(symbol), color="red", penwidth="2.0")
        else:
            dot.edge(str(state), str(next_state), label=str(symbol))
    
    # Generate a unique filename
    filename = f"static/images/path_{os.urandom(8).hex()}"
    
    # Render the graph
    dot.render(filename, format="png", cleanup=True)
    
    # Return the URL to the image
    return f"{filename}.png"

if __name__ == '__main__':
    app.run(debug=True)