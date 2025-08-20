document.addEventListener('DOMContentLoaded', function() {
    // Theme toggle functionality
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = themeToggle.querySelector('i');
    
    // Always start with dark mode
    document.body.classList.add('dark-mode');
    
    themeToggle.addEventListener('click', function() {
        document.body.classList.toggle('dark-mode');
        
        // Update icon
        if (document.body.classList.contains('dark-mode')) {
            themeIcon.classList.remove('fa-sun');
            themeIcon.classList.add('fa-moon');
        } else {
            themeIcon.classList.remove('fa-moon');
            themeIcon.classList.add('fa-sun');
        }
    });

    // Get form elements
    const statesInput = document.getElementById('states');
    const alphabetInput = document.getElementById('alphabet');
    const startStateInput = document.getElementById('start-state');
    const acceptStatesInput = document.getElementById('accept-states');
    const transitionsTable = document.getElementById('transitions-table');
    const generateTransitionsBtn = document.getElementById('generate-transitions');
    const minimizeBtn = document.getElementById('minimize-btn');
    const resultsDiv = document.getElementById('results');
    const processDiv = document.getElementById('process');
    
    // Generate transitions table when button is clicked
    generateTransitionsBtn.addEventListener('click', function() {
        generateTransitionsTable();
    });
    
    // Handle form submission
    document.getElementById('dfa-form').addEventListener('submit', function(e) {
        e.preventDefault();
        minimizeDFA();
    });
    
    function generateTransitionsTable() {
        // Get states and alphabet
        const states = statesInput.value.split(',').map(s => s.trim()).filter(s => s);
        const alphabet = alphabetInput.value.split(',').map(s => s.trim()).filter(s => s);
        
        if (states.length === 0 || alphabet.length === 0) {
            alert('Please enter at least one state and one symbol in the alphabet.');
            return;
        }
        
        // Clear existing table
        const thead = transitionsTable.querySelector('thead tr');
        const tbody = transitionsTable.querySelector('tbody');
        
        // Clear all but the first header cell
        while (thead.children.length > 1) {
            thead.removeChild(thead.lastChild);
        }
        
        // Clear all rows
        tbody.innerHTML = '';
        
        // Add alphabet headers
        for (const symbol of alphabet) {
            const th = document.createElement('th');
            th.textContent = symbol;
            thead.appendChild(th);
        }
        
        // Add rows for each state
        for (const state of states) {
            const tr = document.createElement('tr');
            
            // Add state cell
            const stateTd = document.createElement('td');
            stateTd.textContent = state;
            tr.appendChild(stateTd);
            
            // Add input cells for each symbol
            for (const symbol of alphabet) {
                const td = document.createElement('td');
                const input = document.createElement('input');
                input.type = 'text';
                input.className = 'form-control transition-input';
                input.dataset.from = state;
                input.dataset.symbol = symbol;
                input.placeholder = 'Target state';
                td.appendChild(input);
                tr.appendChild(td);
            }
            
            tbody.appendChild(tr);
        }
    }
    
    function minimizeDFA() {
        // Get DFA data from form
        const states = statesInput.value.split(',').map(s => s.trim()).filter(s => s);
        const alphabet = alphabetInput.value.split(',').map(s => s.trim()).filter(s => s);
        const startState = startStateInput.value.trim();
        const acceptStates = acceptStatesInput.value.split(',').map(s => s.trim()).filter(s => s);
        
        // Validate inputs
        if (states.length === 0 || alphabet.length === 0 || !startState || acceptStates.length === 0) {
            alert('Please fill in all required fields.');
            return;
        }
        
        if (!states.includes(startState)) {
            alert('Start state must be one of the states.');
            return;
        }
        
        for (const acceptState of acceptStates) {
            if (!states.includes(acceptState)) {
                alert(`Accept state ${acceptState} is not in the list of states.`);
                return;
            }
        }
        
        // Get transitions from table
        const transitions = {};
        const transitionInputs = document.querySelectorAll('.transition-input');
        
        for (const input of transitionInputs) {
            const fromState = input.dataset.from;
            const symbol = input.dataset.symbol;
            const toState = input.value.trim();
            
            if (!toState) {
                alert(`Please fill in all transitions. Missing transition for state ${fromState} on symbol ${symbol}.`);
                return;
            }
            
            if (!states.includes(toState)) {
                alert(`Transition from ${fromState} on ${symbol} goes to ${toState}, which is not in the list of states.`);
                return;
            }
            
            if (!transitions[fromState]) {
                transitions[fromState] = {};
            }
            
            transitions[fromState][symbol] = toState;
        }
        
        // Create DFA object
        const dfa = {
            states: states,
            alphabet: alphabet,
            transitions: transitions,
            start_state: startState,
            accept_states: acceptStates
        };
        
        // Send DFA to server for minimization
        sendDFAForMinimization(dfa);
    }
    
    function sendDFAForMinimization(dfa) {
        // Show loading indicator
        resultsDiv.innerHTML = '<div class="text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div><p class="mt-2">Processing DFA...</p></div>';
        processDiv.innerHTML = '';
        
        // Send DFA to server for minimization
        fetch('/minimize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(dfa)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayResults(data);
            } else {
                resultsDiv.innerHTML = `<div class="alert alert-danger"><i class="fas fa-exclamation-circle"></i> Error: ${data.error}</div>`;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            resultsDiv.innerHTML = `<div class="alert alert-danger"><i class="fas fa-exclamation-circle"></i> An error occurred while minimizing the DFA.</div>`;
        });
    }
    
    // Add these functions to your existing dfa.js file
    
    // After displayResults function, add:
    function displayResults(data) {
        // Display the original and minimized DFAs
        resultsDiv.innerHTML = `
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h4 class="mb-0"><i class="fas fa-chart-bar"></i> Minimization Results</h4>
                <button class="btn btn-primary download-all-btn" onclick="downloadAllImages('${data.original_image}', '${data.minimized_image}', '${data.comparison_image}')">
                    <i class="fas fa-download"></i> Download All Images
                </button>
            </div>
            <div class="row">
                <div class="col-md-6">
                    <div class="result-box original-dfa">
                        <div class="d-flex justify-content-between align-items-center mb-3">
                            <h5><i class="fas fa-project-diagram"></i> Original DFA</h5>
                            <button class="btn btn-outline-primary btn-sm download-btn" onclick="downloadImage('${data.original_image}', 'original-dfa.png')">
                                <i class="fas fa-download"></i> Download
                            </button>
                        </div>
                        <img src="${data.original_image}" class="img-fluid" alt="Original DFA">
                        <div class="dfa-details">
                            <p><strong>States:</strong> ${data.original_dfa.states.join(', ')}</p>
                            <p><strong>Alphabet:</strong> ${data.original_dfa.alphabet.join(', ')}</p>
                            <p><strong>Start State:</strong> ${data.original_dfa.start_state}</p>
                            <p><strong>Accept States:</strong> ${data.original_dfa.accept_states.join(', ')}</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="result-box minimized-dfa">
                        <div class="d-flex justify-content-between align-items-center mb-3">
                            <h5><i class="fas fa-compress-arrows-alt"></i> Minimized DFA</h5>
                            <button class="btn btn-outline-success btn-sm download-btn" onclick="downloadImage('${data.minimized_image}', 'minimized-dfa.png')">
                                <i class="fas fa-download"></i> Download
                            </button>
                        </div>
                        <img src="${data.minimized_image}" class="img-fluid" alt="Minimized DFA">
                        <div class="dfa-details">
                            <p><strong>States:</strong> ${data.minimized_dfa.states.join(', ')}</p>
                            <p><strong>Alphabet:</strong> ${data.minimized_dfa.alphabet.join(', ')}</p>
                            <p><strong>Start State:</strong> ${data.minimized_dfa.start_state}</p>
                            <p><strong>Accept States:</strong> ${data.minimized_dfa.accept_states.join(', ')}</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Display the comparison
        processDiv.innerHTML = `
            <div class="comparison-section">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h5><i class="fas fa-exchange-alt"></i> Comparison of Original and Minimized DFAs</h5>
                    <button class="btn btn-outline-info btn-sm download-btn" onclick="downloadImage('${data.comparison_image}', 'dfa-comparison.png')">
                        <i class="fas fa-download"></i> Download Comparison
                    </button>
                </div>
                <img src="${data.comparison_image}" class="img-fluid" alt="DFA Comparison">
                <div class="mt-4">
                    <h5><i class="fas fa-code-branch"></i> Minimization Process</h5>
                    <div class="process-details">
                        <p>The Table-Filling Algorithm was used to minimize the DFA:</p>
                        <ol>
                            <li>First, we identified and removed any unreachable states.</li>
                            <li>Then, we marked pairs of states that are distinguishable (one accepting, one non-accepting).</li>
                            <li>Iteratively, we marked more pairs as distinguishable if they transition to distinguishable states on some input.</li>
                            <li>Finally, we merged indistinguishable states to create the minimized DFA.</li>
                        </ol>
                    </div>
                    <div class="stats-section">
                        <div class="row text-center">
                            <div class="col-md-4">
                                <div class="stat-card">
                                    <h3>${data.original_dfa.states.length}</h3>
                                    <p>Original States</p>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="stat-card">
                                    <h3>${data.minimized_dfa.states.length}</h3>
                                    <p>Minimized States</p>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="stat-card">
                                    <h3>${data.original_dfa.states.length - data.minimized_dfa.states.length}</h3>
                                    <p>States Reduced</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="table-filling-section mt-5">
                <h5><i class="fas fa-table"></i> Table-Filling Visualization</h5>
                <p>This table shows which pairs of states are distinguishable (marked with X) or indistinguishable (unmarked):</p>
                <div class="table-responsive">
                    ${generateTableFillingHTML(data.table_filling_data)}
                </div>
            </div>
        `;
        
        // Store the minimized DFA globally for string testing
        window.minimizedDFA = data.minimized_dfa;

        // Show the string testing section
        document.getElementById('string-test-section').style.display = 'block';

        // Scroll to results
        document.getElementById('results-section').scrollIntoView({ behavior: 'smooth' });
    }

    // Function to download images
    function downloadImage(imageUrl, filename) {
        // Create a temporary anchor element
        const link = document.createElement('a');
        link.href = imageUrl;
        link.download = filename;

        // Append to body, click, and remove
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    // Function to download all images
    function downloadAllImages(originalImage, minimizedImage, comparisonImage) {
        // Add a small delay between downloads to avoid issues
        downloadImage(originalImage, 'original-dfa.png');

        setTimeout(() => {
            downloadImage(minimizedImage, 'minimized-dfa.png');
        }, 500);

        setTimeout(() => {
            downloadImage(comparisonImage, 'dfa-comparison.png');
        }, 1000);

        // Show a notification
        const notification = document.createElement('div');
        notification.className = 'alert alert-success alert-dismissible fade show position-fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.zIndex = '9999';
        notification.innerHTML = `
            <i class="fas fa-check-circle"></i> Downloading all DFA images...
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(notification);

        // Auto-remove notification after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }
    
    // Function to generate HTML for the table-filling visualization
    function generateTableFillingHTML(tableData) {
        if (!tableData || !tableData.states || !tableData.table) {
            return '<p class="text-danger">Table filling data not available</p>';
        }
        
        const states = tableData.states;
        const table = tableData.table;
        
        let html = '<table class="table-filling">';
        
        // Header row with state labels
        html += '<tr><th></th>';
        for (let j = 1; j < states.length; j++) {
            html += `<th>${states[j]}</th>`;
        }
        html += '</tr>';
        
        // Table body
        for (let i = 0; i < states.length - 1; i++) {
            html += `<tr><th>${states[i]}</th>`;
            
            // Add empty cells for the upper triangle
            for (let k = 0; k < i; k++) {
                html += '<td></td>';
            }
            
            // Add cells with distinguishability information
            for (let j = 0; j < table[i].length; j++) {
                const isDistinguishable = table[i][j];
                const cellClass = isDistinguishable ? 'distinguishable' : 'indistinguishable';
                const cellContent = isDistinguishable ? 'X' : '';
                html += `<td class="${cellClass}">${cellContent}</td>`;
            }
            
            html += '</tr>';
        }
        
        html += '</table>';
        return html;
    }
    
    // Canvas-based DFA drawing functionality
    const canvas = document.getElementById('dfa-canvas');
    const ctx = canvas.getContext('2d');
    const addStateBtn = document.getElementById('add-state-btn');
    const addTransitionBtn = document.getElementById('add-transition-btn');
    const isStartStateCheckbox = document.getElementById('is-start-state');
    const isAcceptStateCheckbox = document.getElementById('is-accept-state');
    const transitionPropertiesDiv = document.getElementById('transition-properties');
    const transitionSymbolInput = document.getElementById('transition-symbol');
    const clearCanvasBtn = document.getElementById('clear-canvas-btn');
    const minimizeDrawingBtn = document.getElementById('minimize-drawing-btn');
    
    // Drawing state
    let drawingMode = 'state'; // 'state' or 'transition'
    let states = [];
    let transitions = [];
    let selectedState = null;
    let transitionStart = null;
    let nextStateId = 1;
    
    // Initialize canvas
    function initCanvas() {
        // Set canvas size to match container
        const container = canvas.parentElement;
        canvas.width = container.clientWidth;
        canvas.height = 500;
        
        // Clear canvas
        ctx.fillStyle = 'white';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // Draw grid
        drawGrid();
    }
    
    function drawGrid() {
        ctx.strokeStyle = '#f0f0f0';
        ctx.lineWidth = 1;
        
        // Draw vertical lines
        for (let x = 0; x < canvas.width; x += 20) {
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, canvas.height);
            ctx.stroke();
        }
        
        // Draw horizontal lines
        for (let y = 0; y < canvas.height; y += 20) {
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(canvas.width, y);
            ctx.stroke();
        }
    }
    
    function drawState(state) {
        // Draw circle
        ctx.beginPath();
        ctx.arc(state.x, state.y, state.radius, 0, Math.PI * 2);
        ctx.fillStyle = state.selected ? '#4fc3a1' : 'white';
        ctx.fill();
        ctx.strokeStyle = state.selected ? '#166088' : '#4a6fa5';
        ctx.lineWidth = 2;
        ctx.stroke();
        
        // Draw double circle for accept states
        if (state.isAcceptState) {
            ctx.beginPath();
            ctx.arc(state.x, state.y, state.radius - 5, 0, Math.PI * 2);
            ctx.stroke();
        }
        
        // Draw state label
        ctx.fillStyle = '#343a40';
        ctx.font = '14px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(state.label, state.x, state.y);
        
        // Draw start state arrow
        if (state.isStartState) {
            const angle = Math.PI;
            const arrowLength = 30;
            const arrowX = state.x - state.radius - arrowLength;
            const arrowY = state.y;
            
            ctx.beginPath();
            ctx.moveTo(arrowX, arrowY);
            ctx.lineTo(state.x - state.radius, state.y);
            ctx.strokeStyle = '#4a6fa5';
            ctx.lineWidth = 2;
            ctx.stroke();
            
            // Draw arrowhead
            const headLength = 10;
            const headAngle = Math.PI / 6;
            
            ctx.beginPath();
            ctx.moveTo(state.x - state.radius, state.y);
            ctx.lineTo(state.x - state.radius - headLength * Math.cos(angle - headAngle), 
                      state.y - headLength * Math.sin(angle - headAngle));
            ctx.lineTo(state.x - state.radius - headLength * Math.cos(angle + headAngle), 
                      state.y - headLength * Math.sin(angle + headAngle));
            ctx.closePath();
            ctx.fillStyle = '#4a6fa5';
            ctx.fill();
        }
    }
    
    function drawTransition(transition) {
        const fromState = states.find(s => s.id === transition.from);
        const toState = states.find(s => s.id === transition.to);
        
        if (!fromState || !toState) return;
        
        // Self-loop
        if (fromState.id === toState.id) {
            drawSelfLoop(fromState, transition.symbol);
            return;
        }
        
        // Calculate angle between states
        const dx = toState.x - fromState.x;
        const dy = toState.y - fromState.y;
        const angle = Math.atan2(dy, dx);
        
        // Calculate start and end points on the circles
        const startX = fromState.x + fromState.radius * Math.cos(angle);
        const startY = fromState.y + fromState.radius * Math.sin(angle);
        const endX = toState.x - toState.radius * Math.cos(angle);
        const endY = toState.y - toState.radius * Math.sin(angle);
        
        // Draw arrow line
        ctx.beginPath();
        ctx.moveTo(startX, startY);
        ctx.lineTo(endX, endY);
        ctx.strokeStyle = '#4a6fa5';
        ctx.lineWidth = 2;
        ctx.stroke();
        
        // Draw arrowhead
        const headLength = 10;
        const headAngle = Math.PI / 6;
        
        ctx.beginPath();
        ctx.moveTo(endX, endY);
        ctx.lineTo(endX - headLength * Math.cos(angle - headAngle), 
                  endY - headLength * Math.sin(angle - headAngle));
        ctx.lineTo(endX - headLength * Math.cos(angle + headAngle), 
                  endY - headLength * Math.sin(angle + headAngle));
        ctx.closePath();
        ctx.fillStyle = '#4a6fa5';
        ctx.fill();
        
        // Draw transition symbol
        const labelX = (startX + endX) / 2;
        const labelY = (startY + endY) / 2 - 10;
        
        ctx.fillStyle = 'white';
        ctx.beginPath();
        ctx.ellipse(labelX, labelY, 12, 10, 0, 0, Math.PI * 2);
        ctx.fill();
        
        ctx.fillStyle = '#343a40';
        ctx.font = '12px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(transition.symbol, labelX, labelY);
    }
    
    function drawSelfLoop(state, symbol) {
        const x = state.x;
        const y = state.y - state.radius;
        const radius = state.radius / 2;
        
        // Draw loop
        ctx.beginPath();
        ctx.arc(x, y, radius, 0, Math.PI * 2);
        ctx.strokeStyle = '#4a6fa5';
        ctx.lineWidth = 2;
        ctx.stroke();
        
        // Draw arrowhead
        const angle = Math.PI / 4;
        const headLength = 10;
        const arrowX = x + radius * Math.cos(angle);
        const arrowY = y + radius * Math.sin(angle);
        
        ctx.beginPath();
        ctx.moveTo(arrowX, arrowY);
        ctx.lineTo(arrowX - headLength * Math.cos(angle - Math.PI / 6), 
                  arrowY - headLength * Math.sin(angle - Math.PI / 6));
        ctx.lineTo(arrowX - headLength * Math.cos(angle + Math.PI / 6), 
                  arrowY - headLength * Math.sin(angle + Math.PI / 6));
        ctx.closePath();
        ctx.fillStyle = '#4a6fa5';
        ctx.fill();
        
        // Draw symbol
        ctx.fillStyle = 'white';
        ctx.beginPath();
        ctx.ellipse(x, y - radius - 5, 12, 10, 0, 0, Math.PI * 2);
        ctx.fill();
        
        ctx.fillStyle = '#343a40';
        ctx.font = '12px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(symbol, x, y - radius - 5);
    }
    
    function redrawCanvas() {
        // Clear canvas
        ctx.fillStyle = 'white';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // Draw grid
        drawGrid();
        
        // Draw transitions
        transitions.forEach(drawTransition);
        
        // Draw states
        states.forEach(drawState);
    }
    
    function getStateAtPosition(x, y) {
        for (let i = states.length - 1; i >= 0; i--) {
            const state = states[i];
            const dx = x - state.x;
            const dy = y - state.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            if (distance <= state.radius) {
                return state;
            }
        }
        
        return null;
    }
    
    function addState(x, y) {
        const state = {
            id: nextStateId++,
            label: `q${states.length}`,
            x: x,
            y: y,
            radius: 25,
            isStartState: isStartStateCheckbox.checked,
            isAcceptState: isAcceptStateCheckbox.checked,
            selected: false
        };
        
        // If this is marked as start state, unmark any existing start state
        if (state.isStartState) {
            states.forEach(s => s.isStartState = false);
        }
        
        states.push(state);
        redrawCanvas();
    }
    
    function addTransition(fromState, toState) {
        const symbol = transitionSymbolInput.value.trim();
        
        if (!symbol) {
            alert('Please enter a transition symbol.');
            return false;
        }
        
        // Check if transition already exists
        const existingTransition = transitions.find(t => 
            t.from === fromState.id && t.to === toState.id && t.symbol === symbol
        );
        
        if (existingTransition) {
            alert(`Transition from ${fromState.label} to ${toState.label} on symbol '${symbol}' already exists.`);
            return false;
        }
        
        transitions.push({
            from: fromState.id,
            to: toState.id,
            symbol: symbol
        });
        
        redrawCanvas();
        return true;
    }
    
    function clearCanvas() {
        if (confirm('Are you sure you want to clear the canvas? This will remove all states and transitions.')) {
            states = [];
            transitions = [];
            nextStateId = 1;
            selectedState = null;
            transitionStart = null;
            redrawCanvas();
        }
    }
    
    function convertDrawingToDFA() {
        // Validate the drawn DFA
        if (states.length === 0) {
            alert('Please add at least one state to the DFA.');
            return null;
        }
        
        // Check if there's a start state
        const startState = states.find(s => s.isStartState);
        if (!startState) {
            alert('Please mark one state as the start state.');
            return null;
        }
        
        // Check if there's at least one accept state
        const acceptStates = states.filter(s => s.isAcceptState);
        if (acceptStates.length === 0) {
            alert('Please mark at least one state as an accept state.');
            return null;
        }
        
        // Collect all symbols from transitions
        const symbols = new Set();
        transitions.forEach(t => symbols.add(t.symbol));
        
        if (symbols.size === 0) {
            alert('Please add at least one transition with a symbol.');
            return null;
        }
        
        // Check if all states have transitions for all symbols
        for (const state of states) {
            for (const symbol of symbols) {
                const hasTransition = transitions.some(t => 
                    t.from === state.id && t.symbol === symbol
                );
                
                if (!hasTransition) {
                    alert(`State ${state.label} is missing a transition for symbol '${symbol}'.`);
                    return null;
                }
            }
        }
        
        // Create DFA object
        const dfaTransitions = {};
        
        for (const state of states) {
            dfaTransitions[state.label] = {};
        }
        
        for (const transition of transitions) {
            const fromState = states.find(s => s.id === transition.from);
            const toState = states.find(s => s.id === transition.to);
            
            dfaTransitions[fromState.label][transition.symbol] = toState.label;
        }
        
        return {
            states: states.map(s => s.label),
            alphabet: Array.from(symbols),
            transitions: dfaTransitions,
            start_state: startState.label,
            accept_states: acceptStates.map(s => s.label)
        };
    }
    
    function minimizeDrawing() {
        const dfa = convertDrawingToDFA();
        
        if (dfa) {
            sendDFAForMinimization(dfa);
        }
    }
    
    // Event listeners for canvas drawing
    canvas.addEventListener('click', function(e) {
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        if (drawingMode === 'state') {
            // Check if clicked on an existing state
            const clickedState = getStateAtPosition(x, y);
            
            if (clickedState) {
                // Deselect previously selected state
                if (selectedState) {
                    selectedState.selected = false;
                }
                
                // Select the clicked state
                clickedState.selected = true;
                selectedState = clickedState;
                
                // Update checkboxes
                isStartStateCheckbox.checked = clickedState.isStartState;
                isAcceptStateCheckbox.checked = clickedState.isAcceptState;
            } else {
                // Add a new state
                addState(x, y);
                
                // Reset checkboxes
                isStartStateCheckbox.checked = false;
                isAcceptStateCheckbox.checked = false;
            }
        } else if (drawingMode === 'transition') {
            const clickedState = getStateAtPosition(x, y);
            
            if (!clickedState) return;
            
            if (!transitionStart) {
                // First state in transition
                transitionStart = clickedState;
                transitionStart.selected = true;
            } else {
                // Second state in transition
                if (addTransition(transitionStart, clickedState)) {
                    transitionStart.selected = false;
                    transitionStart = null;
                    transitionSymbolInput.value = '';
                }
            }
        }
        
        redrawCanvas();
    });
    
    // Event listeners for drawing controls
    addStateBtn.addEventListener('click', function() {
        drawingMode = 'state';
        addStateBtn.classList.add('active');
        addTransitionBtn.classList.remove('active');
        transitionPropertiesDiv.style.display = 'none';
        
        // Reset transition start if any
        if (transitionStart) {
            transitionStart.selected = false;
            transitionStart = null;
            redrawCanvas();
        }
    });
    
    addTransitionBtn.addEventListener('click', function() {
        drawingMode = 'transition';
        addTransitionBtn.classList.add('active');
        addStateBtn.classList.remove('active');
        transitionPropertiesDiv.style.display = 'block';
    });
    
    isStartStateCheckbox.addEventListener('change', function() {
        if (selectedState) {
            // If this is being marked as start state, unmark any existing start state
            if (this.checked) {
                states.forEach(s => s.isStartState = false);
            }
            
            selectedState.isStartState = this.checked;
            redrawCanvas();
        }
    });
    
    isAcceptStateCheckbox.addEventListener('change', function() {
        if (selectedState) {
            selectedState.isAcceptState = this.checked;
            redrawCanvas();
        }
    });
    
    clearCanvasBtn.addEventListener('click', clearCanvas);
    
    minimizeDrawingBtn.addEventListener('click', minimizeDrawing);
    
    // Initialize canvas when the draw tab is shown
    document.getElementById('draw-tab').addEventListener('shown.bs.tab', function() {
        initCanvas();
    });
    
    // Initialize the application
    initCanvas();
});

// Add event listener for the test string button
document.getElementById('test-string-btn').addEventListener('click', function() {
    testString();
});

// Add event listener for Enter key in the test string input
document.getElementById('test-string').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        testString();
    }
});

function testString() {
    const testStringInput = document.getElementById('test-string');
    const inputString = testStringInput.value.trim();
    const testResultDiv = document.getElementById('test-result');
    
    if (!window.minimizedDFA) {
        testResultDiv.innerHTML = `<div class="alert alert-warning"><i class="fas fa-exclamation-triangle"></i> Please minimize a DFA first.</div>`;
        return;
    }
    
    if (!inputString) {
        testResultDiv.innerHTML = `<div class="alert alert-warning"><i class="fas fa-exclamation-triangle"></i> Please enter a string to test.</div>`;
        return;
    }
    
    // Show loading indicator
    testResultDiv.innerHTML = `<div class="text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div><p class="mt-2">Processing string...</p></div>`;
    
    // Send the string and DFA to the server for testing
    fetch('/test_string', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            dfa: window.minimizedDFA,
            input_string: inputString
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayTestResults(data, inputString);
        } else {
            testResultDiv.innerHTML = `<div class="alert alert-danger"><i class="fas fa-exclamation-circle"></i> Error: ${data.error}</div>`;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        testResultDiv.innerHTML = `<div class="alert alert-danger"><i class="fas fa-exclamation-circle"></i> An error occurred while testing the string.</div>`;
    });
}

function displayTestResults(data, inputString) {
    const testResultDiv = document.getElementById('test-result');
    const visualizationContainer = document.getElementById('visualization-container');
    
    // Display whether the string was accepted or rejected
    const resultClass = data.accepted ? 'success' : 'danger';
    const resultIcon = data.accepted ? 'check-circle' : 'times-circle';
    const resultText = data.accepted ? 'accepted' : 'rejected';
    
    testResultDiv.innerHTML = `
        <div class="alert alert-${resultClass}">
            <i class="fas fa-${resultIcon}"></i> The string "${inputString}" was ${resultText} by the DFA.
        </div>
        <div class="mt-3">
            <h6>State Trace:</h6>
            <div class="state-trace">${generateStateTraceHTML(data.trace, inputString)}</div>
        </div>
        <div class="mt-3">
            <img src="${data.path_image}" class="img-fluid" alt="Path Visualization">
        </div>
    `;
    
    // Initialize 3D visualization
    initThreeJsVisualization(data.trace, inputString, window.minimizedDFA);
}

function generateStateTraceHTML(trace, inputString) {
    let html = '<div class="trace-steps">';
    
    // Start state
    html += `<div class="trace-step"><span class="state">Start: ${trace[0]}</span></div>`;
    
    // Transitions
    for (let i = 0; i < inputString.length; i++) {
        html += `
            <div class="trace-step">
                <span class="symbol">${inputString[i]}</span>
                <span class="arrow"><i class="fas fa-arrow-right"></i></span>
                <span class="state">${trace[i+1]}</span>
            </div>
        `;
    }
    
    // Final state
    const finalState = trace[trace.length - 1];
    const isAccepting = window.minimizedDFA.accept_states.includes(finalState);
    const stateClass = isAccepting ? 'accepting' : 'non-accepting';
    html += `<div class="trace-step final"><span class="state ${stateClass}">${finalState}</span></div>`;
    
    html += '</div>';
    return html;
}

// Three.js visualization
function initThreeJsVisualization(trace, inputString, dfa) {
    const container = document.getElementById('threejs-container');
    
    // Clear previous visualization
    container.innerHTML = '';
    
    // Set up scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf0f0f0);
    
    // Set up camera
    const camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000);
    camera.position.z = 5;
    camera.position.y = 2;
    
    // Set up renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    container.appendChild(renderer.domElement);
    
    // Add orbit controls
    const controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.25;
    
    // Add lights
    const ambientLight = new THREE.AmbientLight(0x404040);
    scene.add(ambientLight);
    
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
    directionalLight.position.set(1, 1, 1);
    scene.add(directionalLight);
    
    // Create a map of state positions
    const statePositions = {};
    const states = dfa.states;
    const radius = 3;
    const angleStep = (2 * Math.PI) / states.length;
    
    states.forEach((state, index) => {
        const angle = index * angleStep;
        statePositions[state] = {
            x: radius * Math.cos(angle),
            y: 0,
            z: radius * Math.sin(angle)
        };
    });
    
    // Create state spheres
    const stateSpheres = {};
    const stateLabels = {};
    
    states.forEach(state => {
        // Create sphere for state
        const geometry = new THREE.SphereGeometry(0.3, 32, 32);
        const material = new THREE.MeshPhongMaterial({ 
            color: dfa.accept_states.includes(state) ? 0x00ff00 : 0x0088ff
        });
        const sphere = new THREE.Mesh(geometry, material);
        
        sphere.position.set(
            statePositions[state].x,
            statePositions[state].y,
            statePositions[state].z
        );
        
        scene.add(sphere);
        stateSpheres[state] = sphere;
        
        // Add state label (not actually visible in Three.js, just for reference)
        stateLabels[state] = { position: sphere.position.clone() };
    });
    
    // Create transition arrows
    const transitions = [];
    for (const state in dfa.transitions) {
        for (const symbol in dfa.transitions[state]) {
            const nextState = dfa.transitions[state][symbol];
            
            // Create a line for the transition
            const start = statePositions[state];
            const end = statePositions[nextState];
            
            const points = [];
            points.push(new THREE.Vector3(start.x, start.y, start.z));
            
            // If it's a self-loop, create an arc
            if (state === nextState) {
                const arcHeight = 0.5;
                const arcPoint = new THREE.Vector3(
                    start.x,
                    start.y + arcHeight,
                    start.z
                );
                points.push(arcPoint);
            }
            
            points.push(new THREE.Vector3(end.x, end.y, end.z));
            
            const geometry = new THREE.BufferGeometry().setFromPoints(points);
            const material = new THREE.LineBasicMaterial({ color: 0x999999 });
            const line = new THREE.Line(geometry, material);
            scene.add(line);
            
            transitions.push({
                from: state,
                to: nextState,
                symbol: symbol,
                line: line
            });
        }
    }
    
    // Create an animated sphere to represent the input string processing
    const inputSphereGeometry = new THREE.SphereGeometry(0.15, 32, 32);
    const inputSphereMaterial = new THREE.MeshPhongMaterial({ color: 0xff0000 });
    const inputSphere = new THREE.Mesh(inputSphereGeometry, inputSphereMaterial);
    
    // Start at the initial state
    const startPos = statePositions[trace[0]];
    inputSphere.position.set(startPos.x, startPos.y, startPos.z);
    scene.add(inputSphere);
    
    // Animation variables
    let currentStep = 0;
    let animationTime = 0;
    const stepDuration = 2; // seconds per step
    
    // Animation function
    function animate() {
        requestAnimationFrame(animate);
        
        // Update controls
        controls.update();
        
        // Update animation
        if (currentStep < inputString.length) {
            animationTime += 0.016; // Approximately 60fps
            
            if (animationTime >= stepDuration) {
                // Move to next step
                currentStep++;
                animationTime = 0;
                
                // Reset all state colors
                for (const state in stateSpheres) {
                    stateSpheres[state].material.color.set(
                        dfa.accept_states.includes(state) ? 0x00ff00 : 0x0088ff
                    );
                }
                
                // Reset all transition colors
                transitions.forEach(t => {
                    t.line.material.color.set(0x999999);
                });
                
                // If we've processed all steps, highlight the final state
                if (currentStep >= inputString.length) {
                    const finalState = trace[trace.length - 1];
                    stateSpheres[finalState].material.color.set(0xff9900);
                }
            } else {
                // Animate the current step
                const progress = animationTime / stepDuration;
                const currentState = trace[currentStep];
                const nextState = trace[currentStep + 1];
                const symbol = inputString[currentStep];
                
                // Highlight current state
                stateSpheres[currentState].material.color.set(0xff9900);
                
                // Highlight the transition being taken
                const currentTransition = transitions.find(
                    t => t.from === currentState && t.to === nextState && t.symbol === symbol
                );
                
                if (currentTransition) {
                    currentTransition.line.material.color.set(0xff0000);
                }
                
                // Move the input sphere along the path
                const startPos = statePositions[currentState];
                const endPos = statePositions[nextState];
                
                // If it's a self-loop, create an arc path
                if (currentState === nextState) {
                    const arcHeight = 0.5;
                    const arcProgress = Math.sin(progress * Math.PI);
                    
                    inputSphere.position.set(
                        startPos.x,
                        startPos.y + arcHeight * arcProgress,
                        startPos.z
                    );
                } else {
                    // Linear interpolation for direct transitions
                    inputSphere.position.set(
                        startPos.x + (endPos.x - startPos.x) * progress,
                        startPos.y + (endPos.y - startPos.y) * progress,
                        startPos.z + (endPos.z - startPos.z) * progress
                    );
                }
            }
        }
        
        renderer.render(scene, camera);
    }
    
    // Handle window resize
    window.addEventListener('resize', () => {
        camera.aspect = container.clientWidth / container.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(container.clientWidth, container.clientHeight);
    });
    
    // Start animation
    animate();
}
