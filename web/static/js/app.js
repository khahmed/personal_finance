// Portfolio Query Interface JavaScript

const API_BASE = '/api';

// DOM Elements
const queryInput = document.getElementById('queryInput');
const executeBtn = document.getElementById('executeBtn');
const generateCodeBtn = document.getElementById('generateCodeBtn');
const clearBtn = document.getElementById('clearBtn');
const generateCodeCheckbox = document.getElementById('generateCodeCheckbox');
const loadingIndicator = document.getElementById('loadingIndicator');
const errorMessage = document.getElementById('errorMessage');
const sqlDisplay = document.getElementById('sqlDisplay');
const sqlCode = document.getElementById('sqlCode');
const copySqlBtn = document.getElementById('copySqlBtn');
const resultsDisplay = document.getElementById('resultsDisplay');
const resultsTable = document.getElementById('resultsTable');
const rowCount = document.getElementById('rowCount');
const codeDisplay = document.getElementById('codeDisplay');
const generatedCode = document.getElementById('generatedCode');
const copyCodeBtn = document.getElementById('copyCodeBtn');
const addToFileBtn = document.getElementById('addToFileBtn');
const examplesList = document.getElementById('examplesList');
const schemaInfo = document.getElementById('schemaInfo');
const chartContainer = document.getElementById('chartContainer');
const chartCanvas = document.getElementById('resultsChart');

// Chart instance
let currentChart = null;
let currentData = null;
let currentColumns = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkServerHealth();
    loadExamples();
    loadSchema();
    setupEventListeners();
    setupMultiAgentListeners();
});

async function checkServerHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const status = await response.json();
        
        if (!response.ok) {
            console.warn('Server health check failed:', status);
            showError(`Server initialization issue: ${JSON.stringify(status, null, 2)}`);
        } else {
            console.log('Server health check passed:', status);
        }
    } catch (error) {
        console.error('Cannot connect to server:', error);
        showError(`Cannot connect to server. Is it running? Error: ${error.message}\n\nTry: python -m web.app`);
    }
}

function setupEventListeners() {
    executeBtn.addEventListener('click', executeQuery);
    generateCodeBtn.addEventListener('click', generateCodeOnly);
    clearBtn.addEventListener('click', clearAll);
    copySqlBtn.addEventListener('click', () => copyToClipboard(sqlCode.textContent));
    copyCodeBtn.addEventListener('click', () => copyToClipboard(generatedCode.textContent));
    addToFileBtn.addEventListener('click', addCodeToFile);
    
    // Chart type selector buttons
    document.querySelectorAll('.chart-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const chartType = btn.dataset.type;
            switchChartType(chartType);
        });
    });
    
    // Enter key to execute (Ctrl+Enter or Cmd+Enter)
    queryInput.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            executeQuery();
        }
    });
}

async function loadExamples() {
    try {
        const response = await fetch(`${API_BASE}/examples`);
        const data = await response.json();
        
        examplesList.innerHTML = '';
        data.examples.forEach(example => {
            const chip = document.createElement('div');
            chip.className = 'example-chip';
            chip.textContent = example.query;
            chip.title = example.description;
            chip.addEventListener('click', () => {
                queryInput.value = example.query;
                queryInput.focus();
            });
            examplesList.appendChild(chip);
        });
    } catch (error) {
        console.error('Error loading examples:', error);
    }
}

async function loadSchema() {
    try {
        const response = await fetch(`${API_BASE}/schema`);
        const data = await response.json();
        
        if (data.schema) {
            schemaInfo.innerHTML = '';
            data.schema.forEach(table => {
                const li = document.createElement('li');
                li.innerHTML = `<strong>${table.table}</strong> (${table.columns.length} columns)`;
                schemaInfo.appendChild(li);
            });
        }
    } catch (error) {
        console.error('Error loading schema:', error);
        schemaInfo.innerHTML = '<li>Error loading schema</li>';
    }
}

async function executeQuery() {
    const query = queryInput.value.trim();
    if (!query) {
        showError('Please enter a query');
        return;
    }

    hideAll();
    showLoading();

    try {
        const response = await fetch(`${API_BASE}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: query,
                generate_code: generateCodeCheckbox.checked
            })
        });

        // Check content type before parsing
        const contentType = response.headers.get('content-type');
        let data;
        
        if (contentType && contentType.includes('application/json')) {
            try {
                data = await response.json();
            } catch (jsonError) {
                // If JSON parsing fails, try to get text response
                const text = await response.text();
                hideLoading();
                showError(`Server error: ${text.substring(0, 200)}`);
                return;
            }
        } else {
            // Non-JSON response (likely an error page)
            const text = await response.text();
            hideLoading();
            showError(`Server returned non-JSON response: ${text.substring(0, 200)}`);
            return;
        }

        if (!response.ok) {
            hideLoading();
            showError(data.error || 'An error occurred');
            if (data.sql) {
                showSQL(data.sql);
            }
            return;
        }

        hideLoading();
        showSQL(data.sql);
        showResults(data.data, data.columns, data.row_count);
        
        if (data.generated_code) {
            showGeneratedCode(data.generated_code);
        }

    } catch (error) {
        hideLoading();
        let errorMsg = `Network error: ${error.message}`;
        
        // Provide more helpful error messages
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            errorMsg += '\n\nPossible causes:\n';
            errorMsg += '1. Server is not running - Check if Flask app is started\n';
            errorMsg += '2. Wrong URL - Verify the server is running on http://localhost:5000\n';
            errorMsg += '3. CORS issue - Check server logs\n';
            errorMsg += '4. Database connection error - Check database configuration\n\n';
            errorMsg += 'Check the browser console and server logs for more details.';
        }
        
        showError(errorMsg);
        console.error('Full error:', error);
        console.error('Error details:', {
            message: error.message,
            stack: error.stack,
            url: `${API_BASE}/query`
        });
    }
}

async function generateCodeOnly() {
    const query = queryInput.value.trim();
    if (!query) {
        showError('Please enter a query first');
        return;
    }

    // First execute the query to get SQL
    hideAll();
    showLoading();

    try {
        const response = await fetch(`${API_BASE}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: query,
                generate_code: false
            })
        });

        const data = await response.json();

        if (!response.ok) {
            showError(data.error || 'An error occurred');
            return;
        }

        // Now generate code
        const codeResponse = await fetch(`${API_BASE}/generate_code`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                method_name: query.toLowerCase().replace(/[^a-z0-9]/g, '_').substring(0, 50),
                description: query,
                sql: data.sql,
                return_type: 'pd.DataFrame'
            })
        });

        const codeData = await codeResponse.json();

        if (!codeResponse.ok) {
            showError(codeData.error || 'Error generating code');
            return;
        }

        hideLoading();
        showSQL(data.sql);
        showResults(data.data, data.columns, data.row_count);
        showGeneratedCode(codeData.method_code);

    } catch (error) {
        hideLoading();
        showError(`Error: ${error.message}`);
    }
}

async function addCodeToFile() {
    const code = generatedCode.textContent;
    if (!code) {
        showError('No code to add');
        return;
    }

    const methodName = extractMethodName(code);
    const description = queryInput.value.trim() || 'Custom analysis method';
    const sql = sqlCode.textContent;

    try {
        const response = await fetch(`${API_BASE}/generate_code`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                method_name: methodName,
                description: description,
                sql: sql,
                add_to_file: true,
                return_type: 'pd.DataFrame'
            })
        });

        const data = await response.json();

        if (!response.ok) {
            showError(data.error || 'Error adding code to file');
            return;
        }

        if (data.added_to_file) {
            alert('✅ Code successfully added to portfolio_analyzer.py!');
        } else {
            showError('Failed to add code to file');
        }

    } catch (error) {
        showError(`Error: ${error.message}`);
    }
}

function extractMethodName(code) {
    const match = code.match(/def\s+(\w+)\s*\(/);
    return match ? match[1] : 'get_custom_analysis';
}

function showSQL(sql) {
    sqlCode.textContent = sql;
    sqlDisplay.style.display = 'block';
}

function showResults(data, columns, count) {
    if (!data || data.length === 0) {
        resultsDisplay.style.display = 'block';
        resultsTable.innerHTML = '<p>No results found</p>';
        rowCount.textContent = '0 rows';
        chartContainer.style.display = 'none';
        return;
    }

    // Store data for chart switching
    currentData = data;
    currentColumns = columns;

    rowCount.textContent = `${count || data.length} row${count !== 1 ? 's' : ''}`;
    
    // Auto-detect best chart type
    const autoChartType = detectBestChartType(data, columns);
    
    // Set active button
    document.querySelectorAll('.chart-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.type === autoChartType) {
            btn.classList.add('active');
        }
    });
    
    // Show results
    resultsDisplay.style.display = 'block';
    
    // Render initial view
    switchChartType(autoChartType);
}

function detectBestChartType(data, columns) {
    if (!data || data.length === 0) return 'table';
    
    // Check for time series (date columns)
    const dateColumns = columns.filter(col => 
        col.toLowerCase().includes('date') || 
        col.toLowerCase().includes('time') ||
        col.toLowerCase().includes('period')
    );
    
    // Check for numeric columns
    const numericColumns = columns.filter(col => {
        const sample = data[0][col];
        return typeof sample === 'number' || !isNaN(parseFloat(sample));
    });
    
    // Check for categorical columns
    const categoricalColumns = columns.filter(col => {
        const uniqueValues = new Set(data.map(row => String(row[col])));
        return uniqueValues.size <= 10 && uniqueValues.size < data.length;
    });
    
    // Time series data -> line chart
    if (dateColumns.length > 0 && numericColumns.length > 0) {
        return 'line';
    }
    
    // Single numeric column with categories -> bar or pie
    if (categoricalColumns.length > 0 && numericColumns.length > 0) {
        if (categoricalColumns.length === 1 && numericColumns.length === 1) {
            return data.length <= 10 ? 'pie' : 'bar';
        }
        if (categoricalColumns.length > 1) {
            return 'stacked';
        }
        return 'bar';
    }
    
    // Multiple numeric columns -> bar chart
    if (numericColumns.length > 1) {
        return 'bar';
    }
    
    // Default to table
    return 'table';
}

function switchChartType(chartType) {
    // Update active button
    document.querySelectorAll('.chart-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.type === chartType);
    });
    
    // Destroy existing chart
    if (currentChart) {
        currentChart.destroy();
        currentChart = null;
    }
    
    if (chartType === 'table') {
        renderTable();
        chartContainer.style.display = 'none';
    } else {
        renderChart(chartType);
        resultsTable.style.display = 'none';
        chartContainer.style.display = 'block';
    }
}

function renderTable() {
    if (!currentData || !currentColumns) return;
    
    let html = '<table><thead><tr>';
    currentColumns.forEach(col => {
        html += `<th>${escapeHtml(col)}</th>`;
    });
    html += '</tr></thead><tbody>';

    currentData.forEach(row => {
        html += '<tr>';
        currentColumns.forEach(col => {
            const value = row[col];
            html += `<td>${formatValue(value)}</td>`;
        });
        html += '</tr>';
    });

    html += '</tbody></table>';
    resultsTable.innerHTML = html;
    resultsTable.style.display = 'block';
}

function renderChart(chartType) {
    if (!currentData || !currentColumns) return;
    
    const ctx = chartCanvas.getContext('2d');
    
    // Prepare chart data based on type
    let chartData, chartOptions;
    
    switch (chartType) {
        case 'line':
            ({ chartData, chartOptions } = prepareLineChart());
            break;
        case 'bar':
            ({ chartData, chartOptions } = prepareBarChart());
            break;
        case 'pie':
            ({ chartData, chartOptions } = preparePieChart());
            break;
        case 'stacked':
            ({ chartData, chartOptions } = prepareStackedChart());
            break;
        default:
            return;
    }
    
    currentChart = new Chart(ctx, {
        type: chartType === 'pie' ? 'pie' : chartType === 'stacked' ? 'bar' : chartType,
        data: chartData,
        options: chartOptions
    });
}

function prepareLineChart() {
    // Find date column and numeric column
    const dateCol = currentColumns.find(col => 
        col.toLowerCase().includes('date') || 
        col.toLowerCase().includes('time')
    );
    const numericCols = currentColumns.filter(col => {
        const sample = currentData[0][col];
        return typeof sample === 'number' || !isNaN(parseFloat(sample));
    });
    
    if (!dateCol || numericCols.length === 0) {
        // Fallback: use first column as labels, first numeric as data
        const labelCol = currentColumns[0];
        const dataCol = numericCols[0] || currentColumns[1];
        
        return {
            chartData: {
                labels: currentData.map(row => String(row[labelCol])),
                datasets: [{
                    label: dataCol,
                    data: currentData.map(row => parseFloat(row[dataCol]) || 0),
                    borderColor: 'rgb(102, 126, 234)',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.1
                }]
            },
            chartOptions: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { display: true },
                    title: { display: true, text: dataCol }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        };
    }
    
    // Sort by date
    const sortedData = [...currentData].sort((a, b) => {
        const dateA = new Date(a[dateCol]);
        const dateB = new Date(b[dateCol]);
        return dateA - dateB;
    });
    
    const datasets = numericCols.map((col, idx) => {
        const colors = [
            'rgb(102, 126, 234)',
            'rgb(118, 75, 162)',
            'rgb(76, 175, 80)',
            'rgb(255, 152, 0)',
            'rgb(244, 67, 54)'
        ];
        return {
            label: col,
            data: sortedData.map(row => parseFloat(row[col]) || 0),
            borderColor: colors[idx % colors.length],
            backgroundColor: colors[idx % colors.length].replace('rgb', 'rgba').replace(')', ', 0.1)'),
            tension: 0.1
        };
    });
    
    return {
        chartData: {
            labels: sortedData.map(row => {
                const date = new Date(row[dateCol]);
                return date.toLocaleDateString();
            }),
            datasets: datasets
        },
        chartOptions: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: true }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    };
}

function prepareBarChart() {
    // Use first categorical column as labels, first numeric as data
    const labelCol = currentColumns[0];
    const numericCols = currentColumns.filter(col => {
        const sample = currentData[0][col];
        return typeof sample === 'number' || !isNaN(parseFloat(sample));
    });
    
    if (numericCols.length === 0) return prepareLineChart();
    
    const datasets = numericCols.slice(0, 5).map((col, idx) => {
        const colors = [
            'rgba(102, 126, 234, 0.8)',
            'rgba(118, 75, 162, 0.8)',
            'rgba(76, 175, 80, 0.8)',
            'rgba(255, 152, 0, 0.8)',
            'rgba(244, 67, 54, 0.8)'
        ];
        return {
            label: col,
            data: currentData.map(row => parseFloat(row[col]) || 0),
            backgroundColor: colors[idx % colors.length]
        };
    });
    
    return {
        chartData: {
            labels: currentData.map(row => String(row[labelCol]).substring(0, 20)),
            datasets: datasets
        },
        chartOptions: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: datasets.length > 1 }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    };
}

function preparePieChart() {
    const labelCol = currentColumns[0];
    const numericCol = currentColumns.find(col => {
        const sample = currentData[0][col];
        return typeof sample === 'number' || !isNaN(parseFloat(sample));
    }) || currentColumns[1];
    
    const colors = [
        'rgba(102, 126, 234, 0.8)',
        'rgba(118, 75, 162, 0.8)',
        'rgba(76, 175, 80, 0.8)',
        'rgba(255, 152, 0, 0.8)',
        'rgba(244, 67, 54, 0.8)',
        'rgba(33, 150, 243, 0.8)',
        'rgba(156, 39, 176, 0.8)',
        'rgba(0, 188, 212, 0.8)',
        'rgba(255, 87, 34, 0.8)',
        'rgba(121, 85, 72, 0.8)'
    ];
    
    return {
        chartData: {
            labels: currentData.map(row => String(row[labelCol]).substring(0, 30)),
            datasets: [{
                data: currentData.map(row => parseFloat(row[numericCol]) || 0),
                backgroundColor: colors.slice(0, currentData.length)
            }]
        },
        chartOptions: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { 
                    display: true,
                    position: 'right'
                },
                title: {
                    display: true,
                    text: numericCol
                }
            }
        }
    };
}

function prepareStackedChart() {
    // Find categorical columns for grouping
    const categoricalCols = currentColumns.filter((col, idx) => {
        if (idx === 0) return true; // First column is usually category
        const uniqueValues = new Set(currentData.map(row => String(row[col])));
        return uniqueValues.size <= 10;
    });
    
    const numericCols = currentColumns.filter(col => {
        const sample = currentData[0][col];
        return typeof sample === 'number' || !isNaN(parseFloat(sample));
    });
    
    if (categoricalCols.length < 2 || numericCols.length === 0) {
        return prepareBarChart();
    }
    
    const groupCol = categoricalCols[0];
    const stackCol = categoricalCols[1];
    
    // Group data
    const groups = {};
    currentData.forEach(row => {
        const group = String(row[groupCol]);
        const stack = String(row[stackCol]);
        const value = parseFloat(row[numericCols[0]]) || 0;
        
        if (!groups[group]) groups[group] = {};
        groups[group][stack] = (groups[group][stack] || 0) + value;
    });
    
    const stackValues = [...new Set(currentData.map(row => String(row[stackCol])))];
    const colors = [
        'rgba(102, 126, 234, 0.8)',
        'rgba(118, 75, 162, 0.8)',
        'rgba(76, 175, 80, 0.8)',
        'rgba(255, 152, 0, 0.8)',
        'rgba(244, 67, 54, 0.8)'
    ];
    
    const datasets = stackValues.map((stack, idx) => ({
        label: stack,
        data: Object.keys(groups).map(group => groups[group][stack] || 0),
        backgroundColor: colors[idx % colors.length]
    }));
    
    return {
        chartData: {
            labels: Object.keys(groups),
            datasets: datasets
        },
        chartOptions: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: true }
            },
            scales: {
                x: { stacked: true },
                y: { stacked: true, beginAtZero: true }
            }
        }
    };
}

function showGeneratedCode(code) {
    generatedCode.textContent = code;
    codeDisplay.style.display = 'block';
}

function showLoading() {
    loadingIndicator.style.display = 'block';
}

function hideLoading() {
    loadingIndicator.style.display = 'none';
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
}

function hideAll() {
    errorMessage.style.display = 'none';
    sqlDisplay.style.display = 'none';
    resultsDisplay.style.display = 'none';
    codeDisplay.style.display = 'none';
    loadingIndicator.style.display = 'none';
}

function clearAll() {
    queryInput.value = '';
    hideAll();
    if (currentChart) {
        currentChart.destroy();
        currentChart = null;
    }
    currentData = null;
    currentColumns = null;
    queryInput.focus();
}

function formatValue(value) {
    if (value === null || value === undefined) {
        return '<em>null</em>';
    }
    if (typeof value === 'number') {
        // Format numbers with commas
        if (value % 1 === 0) {
            return value.toLocaleString();
        } else {
            return value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        }
    }
    if (typeof value === 'boolean') {
        return value ? '✓' : '✗';
    }
    return escapeHtml(String(value));
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        // Visual feedback
        const btn = event.target;
        const originalText = btn.textContent;
        btn.textContent = '✓ Copied!';
        btn.style.background = '#4caf50';
        setTimeout(() => {
            btn.textContent = originalText;
            btn.style.background = '';
        }, 2000);
    } catch (error) {
        console.error('Failed to copy:', error);
        alert('Failed to copy to clipboard');
    }
}

// ==================== Multi-Agent Functionality ====================

function setupMultiAgentListeners() {
    // Mode selector buttons
    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const mode = btn.dataset.mode;
            switchMode(mode);
        });
    });

    // Analysis type buttons
    document.querySelectorAll('.analysis-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const analysisType = btn.dataset.analysis;
            executeAnalysis(analysisType);
        });
    });

    // Agent query button
    const executeAgentQueryBtn = document.getElementById('executeAgentQueryBtn');
    if (executeAgentQueryBtn) {
        executeAgentQueryBtn.addEventListener('click', executeAgentQuery);
    }
}

function switchMode(mode) {
    // Update button states
    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.mode === mode);
    });

    // Show/hide mode sections
    const sqlMode = document.getElementById('sqlMode');
    const agentMode = document.getElementById('agentMode');

    if (mode === 'sql') {
        sqlMode.style.display = 'block';
        agentMode.style.display = 'none';
    } else {
        sqlMode.style.display = 'none';
        agentMode.style.display = 'block';
    }
}

function getUserContext() {
    const taxRate = parseFloat(document.getElementById('taxRate').value) / 100;
    const province = document.getElementById('province').value;
    const age = document.getElementById('age').value;
    const riskProfile = document.getElementById('riskProfile').value;

    const context = {
        tax_rate: taxRate,
        province: province,
        risk_profile: riskProfile
    };

    if (age) {
        context.age = parseInt(age);
    }

    return context;
}

async function executeAnalysis(analysisType) {
    const userContext = getUserContext();
    const agentLoadingIndicator = document.getElementById('agentLoadingIndicator');
    const agentErrorMessage = document.getElementById('agentErrorMessage');
    const comprehensiveResults = document.getElementById('comprehensiveResults');
    const individualResults = document.getElementById('individualResults');

    // Hide previous results
    agentErrorMessage.style.display = 'none';
    comprehensiveResults.style.display = 'none';
    individualResults.style.display = 'none';

    // Show loading
    agentLoadingIndicator.style.display = 'block';

    try {
        let endpoint, responseData;

        switch (analysisType) {
            case 'comprehensive':
                endpoint = `${API_BASE}/v2/comprehensive-review`;
                responseData = await fetchJSON(endpoint, { user_context: userContext });
                displayComprehensiveResults(responseData);
                break;

            case 'tax':
                endpoint = `${API_BASE}/v2/tax-analysis`;
                responseData = await fetchJSON(endpoint, { user_context: userContext });
                displayIndividualAnalysis('Tax Analysis', responseData, '💰');
                break;

            case 'estate':
                endpoint = `${API_BASE}/v2/estate-analysis`;
                responseData = await fetchJSON(endpoint, { user_context: userContext });
                displayIndividualAnalysis('Estate Planning', responseData, '🏛️');
                break;

            case 'investment':
                endpoint = `${API_BASE}/v2/investment-analysis`;
                responseData = await fetchJSON(endpoint, { user_context: userContext });
                displayIndividualAnalysis('Investment Analysis', responseData, '📈');
                break;

            case 'portfolio-data':
                endpoint = `${API_BASE}/v2/portfolio-data`;
                responseData = await fetchJSON(endpoint, null, 'GET');
                displayIndividualAnalysis('Portfolio Data', responseData, '📊');
                break;

            default:
                throw new Error('Unknown analysis type');
        }

    } catch (error) {
        console.error('Analysis error:', error);
        agentErrorMessage.textContent = `Error: ${error.message}`;
        agentErrorMessage.style.display = 'block';
    } finally {
        agentLoadingIndicator.style.display = 'none';
    }
}

async function executeAgentQuery() {
    const agentQueryInput = document.getElementById('agentQueryInput');
    const query = agentQueryInput.value.trim();

    if (!query) {
        alert('Please enter a query');
        return;
    }

    const userContext = getUserContext();
    const agentLoadingIndicator = document.getElementById('agentLoadingIndicator');
    const agentErrorMessage = document.getElementById('agentErrorMessage');
    const comprehensiveResults = document.getElementById('comprehensiveResults');
    const individualResults = document.getElementById('individualResults');

    // Hide previous results
    agentErrorMessage.style.display = 'none';
    comprehensiveResults.style.display = 'none';
    individualResults.style.display = 'none';

    // Show loading
    agentLoadingIndicator.style.display = 'block';

    try {
        const endpoint = `${API_BASE}/v2/agent-query`;
        const responseData = await fetchJSON(endpoint, {
            query: query,
            user_context: userContext,
            workflow_type: 'sequential'
        });

        displayComprehensiveResults(responseData);

    } catch (error) {
        console.error('Agent query error:', error);
        agentErrorMessage.textContent = `Error: ${error.message}`;
        agentErrorMessage.style.display = 'block';
    } finally {
        agentLoadingIndicator.style.display = 'none';
    }
}

async function fetchJSON(url, body = null, method = 'POST') {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        }
    };

    if (body && method === 'POST') {
        options.body = JSON.stringify(body);
    }

    const response = await fetch(url, options);

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Request failed');
    }

    return await response.json();
}

function displayComprehensiveResults(data) {
    const comprehensiveResults = document.getElementById('comprehensiveResults');

    // Portfolio Summary
    if (data.portfolio_data) {
        const content = document.getElementById('portfolioSummaryContent');
        content.innerHTML = formatPortfolioSummary(data.portfolio_data);
    }

    // Tax Analysis
    if (data.tax_analysis) {
        const content = document.getElementById('taxAnalysisContent');
        content.innerHTML = formatTaxAnalysis(data.tax_analysis);
    }

    // Estate Analysis
    if (data.estate_analysis) {
        const content = document.getElementById('estateAnalysisContent');
        content.innerHTML = formatEstateAnalysis(data.estate_analysis);
    }

    // Investment Analysis
    if (data.investment_analysis) {
        const content = document.getElementById('investmentAnalysisContent');
        content.innerHTML = formatInvestmentAnalysis(data.investment_analysis);
    }

    comprehensiveResults.style.display = 'block';
}

function displayIndividualAnalysis(title, data, icon) {
    const individualResults = document.getElementById('individualResults');

    let html = `<h3>${icon} ${title}</h3>`;
    html += '<div class="result-card">';

    if (title === 'Tax Analysis') {
        html += formatTaxAnalysis(data);
    } else if (title === 'Estate Planning') {
        html += formatEstateAnalysis(data);
    } else if (title === 'Investment Analysis') {
        html += formatInvestmentAnalysis(data);
    } else if (title === 'Portfolio Data') {
        html += formatPortfolioSummary(data);
    }

    html += '</div>';

    individualResults.innerHTML = html;
    individualResults.style.display = 'block';
}

function formatPortfolioSummary(data) {
    let html = '<div class="summary-grid">';

    if (data.portfolio_summary) {
        const summary = data.portfolio_summary;
        html += `
            <div class="summary-item">
                <span class="summary-label">Total Value:</span>
                <span class="summary-value">$${formatNumber(summary.total_value)}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">Accounts:</span>
                <span class="summary-value">${summary.num_accounts}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">Securities:</span>
                <span class="summary-value">${summary.num_securities}</span>
            </div>
        `;

        if (summary.by_asset_category) {
            html += '<div class="summary-section"><h5>Asset Allocation</h5><ul>';
            for (const [category, value] of Object.entries(summary.by_asset_category)) {
                html += `<li>${category}: $${formatNumber(value)}</li>`;
            }
            html += '</ul></div>';
        }
    }

    html += '</div>';
    return html;
}

function formatTaxAnalysis(data) {
    let html = '';

    if (data.tax_optimization_report) {
        const report = data.tax_optimization_report;
        html += '<div class="analysis-section">';
        html += `<p><strong>Total Unrealized Gains:</strong> $${formatNumber(report.total_unrealized_gains)}</p>`;
        html += `<p><strong>Total Unrealized Losses:</strong> $${formatNumber(report.total_unrealized_losses)}</p>`;
        html += `<p><strong>Estimated Tax Liability:</strong> $${formatNumber(report.estimated_tax_liability)}</p>`;
        html += `<p><strong>Potential Tax Savings:</strong> $${formatNumber(report.potential_tax_savings)}</p>`;
        html += '</div>';
    }

    if (data.recommendations && data.recommendations.length > 0) {
        html += '<div class="recommendations-section"><h5>Recommendations</h5><ul>';
        data.recommendations.forEach(rec => {
            html += `<li><strong>${rec.priority}:</strong> ${rec.action}`;
            if (rec.timing) html += ` (${rec.timing})`;
            if (rec.tax_impact) html += ` - Tax Impact: $${formatNumber(rec.tax_impact)}`;
            html += '</li>';
        });
        html += '</ul></div>';
    }

    if (data.llm_insights) {
        html += formatLLMInsights(data.llm_insights);
    }

    return html;
}

function formatEstateAnalysis(data) {
    let html = '';

    if (data.estate_planning_report) {
        const report = data.estate_planning_report;
        html += '<div class="analysis-section">';
        html += `<p><strong>Total Estate Value:</strong> $${formatNumber(report.total_estate_value)}</p>`;
        html += `<p><strong>Estimated Probate Fees:</strong> $${formatNumber(report.estimated_probate_fees)}</p>`;
        html += `<p><strong>Accounts with Beneficiaries:</strong> ${report.accounts_with_beneficiaries}</p>`;
        html += `<p><strong>Accounts without Beneficiaries:</strong> ${report.accounts_without_beneficiaries}</p>`;
        html += '</div>';
    }

    if (data.recommendations && data.recommendations.length > 0) {
        html += '<div class="recommendations-section"><h5>Recommendations</h5><ul>';
        data.recommendations.forEach(rec => {
            html += `<li><strong>${rec.priority}:</strong> ${rec.action}`;
            if (rec.rationale) html += `<br><em>${rec.rationale}</em>`;
            html += '</li>';
        });
        html += '</ul></div>';
    }

    if (data.product_recommendations && data.product_recommendations.length > 0) {
        html += '<div class="recommendations-section"><h5>Product Recommendations</h5><ul>';
        data.product_recommendations.forEach(prod => {
            html += `<li><strong>${prod.product_type}</strong> (${prod.allocation_percentage}% allocation)`;
            if (prod.rationale) html += `<br><em>${prod.rationale}</em>`;
            html += '</li>';
        });
        html += '</ul></div>';
    }

    if (data.llm_insights) {
        html += formatLLMInsights(data.llm_insights);
    }

    return html;
}

function formatInvestmentAnalysis(data) {
    let html = '';

    if (data.investment_analysis_report) {
        const report = data.investment_analysis_report;
        html += '<div class="analysis-section">';
        html += `<p><strong>Portfolio Health Score:</strong> ${report.portfolio_health_score}/10</p>`;
        html += `<p><strong>Concentration Risk Level:</strong> ${report.concentration_risk_level}</p>`;
        html += `<p><strong>Rebalancing Urgency:</strong> ${report.rebalancing_urgency}</p>`;
        html += '</div>';
    }

    if (data.security_recommendations && data.security_recommendations.length > 0) {
        html += '<div class="recommendations-section"><h5>Security Recommendations</h5><ul>';
        data.security_recommendations.slice(0, 10).forEach(rec => {
            html += `<li><strong>${rec.security_name || rec.symbol}:</strong> ${rec.recommendation}`;
            if (rec.rationale) html += `<br><em>${rec.rationale}</em>`;
            html += '</li>';
        });
        html += '</ul></div>';
    }

    if (data.rebalancing_plan && data.rebalancing_plan.length > 0) {
        html += '<div class="recommendations-section"><h5>Rebalancing Plan</h5><ul>';
        data.rebalancing_plan.forEach(action => {
            html += `<li><strong>${action.action}:</strong> ${action.security}`;
            if (action.quantity) html += ` (${action.quantity} shares)`;
            if (action.reason) html += `<br><em>${action.reason}</em>`;
            html += '</li>';
        });
        html += '</ul></div>';
    }

    if (data.llm_insights) {
        html += formatLLMInsights(data.llm_insights);
    }

    return html;
}

function formatLLMInsights(insights) {
    let html = '<div class="llm-insights-section">';
    html += `<h5>AI Analysis <span style="font-size: 0.8em; color: #666;">(${insights.llm_provider})</span></h5>`;

    if (insights.explanation) {
        html += `<p>${insights.explanation}</p>`;
    }

    if (insights.recommendations && insights.recommendations.length > 0) {
        html += '<ul>';
        insights.recommendations.forEach(rec => {
            html += `<li><strong>${rec.priority}:</strong> ${rec.action}`;
            if (rec.rationale) html += `<br><em>${rec.rationale}</em>`;
            if (rec.impact) html += `<br>Impact: ${rec.impact}`;
            html += '</li>';
        });
        html += '</ul>';
    }

    html += '</div>';
    return html;
}

function formatNumber(value) {
    if (typeof value !== 'number') return value;
    return value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

