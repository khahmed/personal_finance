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

