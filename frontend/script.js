// Global variables
let currentFile = null;
let lastAnalysisResult = null;
let isPremium = false;

// API Configuration
let userApiKey = localStorage.getItem('userApiKey') || '';
let llmProvider = localStorage.getItem('llmProvider') || 'openai';

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    setupDragAndDrop();
    initializeApiSettings();
});

// Initialize API settings
function initializeApiSettings() {
    // API Key button
    const apiKeyBtn = document.getElementById('apiKeyBtn');
    if (apiKeyBtn) {
        apiKeyBtn.addEventListener('click', () => {
            document.getElementById('apiKeyModal').style.display = 'block';
            document.getElementById('llmProvider').value = llmProvider;
            document.getElementById('apiKeyInput').value = userApiKey;
        });
    }
}

// Initialize event listeners
function initializeEventListeners() {
    // File input change
    document.getElementById('policyFile').addEventListener('change', handleFileSelect);
    
    // Form submission
    document.getElementById('policyForm').addEventListener('submit', handleFormSubmit);
    
    // Tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });
    
    // Modal close
    document.querySelectorAll('.close').forEach(closeBtn => {
        closeBtn.addEventListener('click', (e) => {
            e.target.closest('.modal').style.display = 'none';
        });
    });
    window.addEventListener('click', (e) => {
        if (e.target.className === 'modal') {
            e.target.style.display = 'none';
        }
    });
}

// Setup drag and drop
function setupDragAndDrop() {
    const fileDisplay = document.querySelector('.file-input-display');
    const fileInput = document.getElementById('policyFile');
    
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        fileDisplay.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });
    
    ['dragenter', 'dragover'].forEach(eventName => {
        fileDisplay.addEventListener(eventName, () => {
            fileDisplay.style.borderColor = '#2563eb';
            fileDisplay.style.background = '#eff6ff';
        });
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        fileDisplay.addEventListener(eventName, () => {
            fileDisplay.style.borderColor = '#d1d5db';
            fileDisplay.style.background = '#f9fafb';
        });
    });
    
    fileDisplay.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            fileInput.files = files;
            handleFileSelect({ target: fileInput });
        }
    });
}

// Prevent default drag behaviors
function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

// Handle file selection
function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        currentFile = file;
        const fileDisplay = document.querySelector('.file-input-display');
        fileDisplay.textContent = `Selected: ${file.name} (${formatFileSize(file.size)})`;
        fileDisplay.style.color = '#2563eb';
    }
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Handle form submission
async function handleFormSubmit(e) {
    e.preventDefault();
    
    if (!currentFile) {
        showNotification('Please select a file', 'error');
        return;
    }
    
    isPremium = false;
    await analyzePolicy(false);
}

// Analyze policy with time-based simulation
async function analyzePolicy(premium = false) {
    const formData = new FormData();
    formData.append('file', currentFile);
    formData.append('premium', premium.toString());
    
    if (premium) {
        formData.append('payment_id', 'TEST_123');
    }
    
    // Add API configuration
    if (userApiKey) {
        formData.append('api_key', userApiKey);
    }
    formData.append('llm_provider', llmProvider);
    
    showLoadingState(premium);
    
    // Use time-based simulation (reliable and working)
    await analyzeWithTimeSimulation(formData, premium);
}

// Handle streamed data
function handleStreamData(data, premium) {
    if (data.progress) {
        document.getElementById('progressBar').style.width = data.progress + '%';
        document.getElementById('progressText').textContent = data.progress + '%';
    }
    
    if (data.message) {
        document.getElementById('statusMessage').textContent = data.message;
    }
    
    if (data.step) {
        updateStepProgress(data.step);
    }
    
    if (data.complete && data.result) {
        stopProcessingTimer();
        lastAnalysisResult = data.result;
        isPremium = premium;
        displayResults(data.result, premium);
    }
    
    if (data.error) {
        hideLoadingState();
        stopProcessingTimer();
        showNotification('Error: ' + data.error, 'error');
    }
}

// Fallback: Time-based simulation
async function analyzeWithTimeSimulation(formData, premium) {
    console.log('Using time-based simulation');
    
    const startTime = Date.now();
    const estimatedTime = 35000; // 35 seconds
    const steps = premium ? 4 : 3;
    
    // Simulate progress
    const progressInterval = setInterval(() => {
        const elapsed = Date.now() - startTime;
        const progress = Math.min((elapsed / estimatedTime) * 95, 95);
        
        document.getElementById('progressBar').style.width = progress + '%';
        document.getElementById('progressText').textContent = Math.round(progress) + '%';
        
        // Update steps
        const currentStep = Math.ceil((progress / 95) * steps);
        updateStepProgress(currentStep);
        
        // Update status messages
        const messages = [
            'Uploading and validating document...',
            'Policy Reader Agent analyzing document...',
            'Compliance Auditor checking standards...',
            'AI Consultant generating recommendations...'
        ];
        const messageIndex = Math.min(Math.floor((progress / 95) * steps), steps - 1);
        document.getElementById('statusMessage').textContent = messages[messageIndex];
    }, 500);
    
    try {
        // Make regular API call
        const response = await fetch('http://127.0.0.1:8000/analyze_policy/', {
            method: 'POST',
            body: formData
        });
        
        clearInterval(progressInterval);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(formatErrorMessage(errorData));
        }
        
        const result = await response.json();
        
        // Check if the result indicates failure
        if (result.success === false || result.error) {
            clearInterval(progressInterval);
            hideLoadingState();
            stopProcessingTimer();
            showDetailedError(result);
            return;
        }
        
        // Complete progress
        document.getElementById('progressBar').style.width = '100%';
        document.getElementById('progressText').textContent = '100%';
        
        // Mark all steps as completed
        for (let i = 1; i <= steps; i++) {
            const step = document.getElementById(`step${i}`);
            if (step) {
                step.classList.add('completed');
                step.classList.remove('active');
            }
        }
        
        stopProcessingTimer();
        lastAnalysisResult = result;
        isPremium = premium;
        displayResults(result, premium);
        
    } catch (error) {
        clearInterval(progressInterval);
        hideLoadingState();
        stopProcessingTimer();
        console.error('Analysis error:', error);
        showNotification('Analysis failed: ' + error.message, 'error');
    }
}

// Format error message from backend
function formatErrorMessage(errorData) {
    if (typeof errorData === 'string') return errorData;
    if (errorData.detail) {
        if (typeof errorData.detail === 'string') return errorData.detail;
        if (errorData.detail.message) return errorData.detail.message;
    }
    if (errorData.message) return errorData.message;
    if (errorData.error) return errorData.error;
    return 'Unknown error occurred';
}

// Show detailed error in a modal
function showDetailedError(errorData) {
    const errorHtml = `
        <div style="background: #fee; border: 2px solid #f00; padding: 20px; border-radius: 8px; margin: 20px;">
            <h3 style="color: #d00; margin-top: 0;">❌ Analysis Failed</h3>
            <p><strong>Error Type:</strong> ${errorData.error_type || 'Unknown'}</p>
            <p><strong>Message:</strong> ${errorData.message || errorData.error_message || errorData.error || 'No message'}</p>
            ${errorData.technical_details ? `
                <details style="margin-top: 15px;">
                    <summary style="cursor: pointer; font-weight: bold;">🔍 Technical Details (Click to expand)</summary>
                    <pre style="background: #f5f5f5; padding: 10px; margin-top: 10px; overflow-x: auto; font-size: 12px;">${errorData.technical_details}</pre>
                </details>
            ` : ''}
            ${errorData.error_details ? `
                <details style="margin-top: 15px;">
                    <summary style="cursor: pointer; font-weight: bold;">📋 Full Stack Trace (Click to expand)</summary>
                    <pre style="background: #f5f5f5; padding: 10px; margin-top: 10px; overflow-x: auto; font-size: 11px;">${errorData.error_details}</pre>
                </details>
            ` : ''}
            ${errorData.full_trace ? `
                <details style="margin-top: 15px;">
                    <summary style="cursor: pointer; font-weight: bold;">🐛 Complete Trace (Click to expand)</summary>
                    <pre style="background: #f5f5f5; padding: 10px; margin-top: 10px; overflow-x: auto; font-size: 11px;">${errorData.full_trace}</pre>
                </details>
            ` : ''}
            <button onclick="analyzeAnother()" style="margin-top: 20px; padding: 10px 20px; background: #2563eb; color: white; border: none; border-radius: 6px; cursor: pointer;">Try Again</button>
        </div>
    `;
    
    // Show error in results section
    document.getElementById('processSteps').style.display = 'none';
    document.querySelector('.upload-section').style.display = 'none';
    document.getElementById('results').style.display = 'block';
    document.getElementById('results').innerHTML = errorHtml;
}

// Update step progress
function updateStepProgress(stepNumber) {
    // Mark previous steps as completed
    for (let i = 1; i < stepNumber; i++) {
        const prevStep = document.getElementById(`step${i}`);
        if (prevStep) {
            prevStep.classList.remove('active');
            prevStep.classList.add('completed');
        }
    }
    
    // Mark current step as active
    const currentStep = document.getElementById(`step${stepNumber}`);
    if (currentStep) {
        currentStep.classList.remove('completed');
        currentStep.classList.add('active');
    }
}

// Show loading state
function showLoadingState(isPremium) {
    // Hide upload section
    document.querySelector('.upload-section').style.display = 'none';
    
    // Show process steps
    document.getElementById('processSteps').style.display = 'block';
    
    // Reset step states
    document.querySelectorAll('.step').forEach(step => {
        step.classList.remove('active', 'completed');
    });
    
    // Show/hide step 4 based on premium
    document.getElementById('step4').style.display = isPremium ? 'flex' : 'none';
    
    // Hide results initially
    document.getElementById('results').style.display = 'none';
    
    // Update file info
    if (currentFile) {
        document.getElementById('fileName').textContent = currentFile.name;
        document.getElementById('fileSize').textContent = formatFileSize(currentFile.size);
    }
    
    // Start processing timer
    startProcessingTimer();
    
    // Reset progress bar
    document.getElementById('progressBar').style.width = '0%';
    document.getElementById('progressText').textContent = '0%';
    document.getElementById('statusMessage').textContent = 'Initializing analysis...';
}

// Hide loading state
function hideLoadingState() {
    document.getElementById('processSteps').style.display = 'none';
    document.querySelector('.upload-section').style.display = 'block';
}

// Display results
function displayResults(result, isPremium) {
    // Hide process steps
    document.getElementById('processSteps').style.display = 'none';
    
    // Show results section
    document.getElementById('results').style.display = 'block';
    
    // Update score circle
    updateScoreCircle(result.score || 0);
    
    // Update summary tab
    updateSummaryTab(result);
    
    // Update strengths tab
    updateStrengthsTab(result.strengths || []);
    
    // Update gaps tab
    updateGapsTab(result.gaps || []);
    
    // Update recommendations tab
    if (isPremium && result.recommendations) {
        updateRecommendationsTab(result.recommendations);
    }
    
    // Update raw data tab
    updateRawDataTab(result);
    
    // Switch to summary tab
    switchTab('summary');
}

// Update score circle
function updateScoreCircle(score) {
    const scoreValue = document.querySelector('.score-value');
    const progressRing = document.querySelector('.progress-ring__progress');
    
    scoreValue.textContent = score;
    
    // Calculate stroke offset
    const circumference = 2 * Math.PI * 52; // radius = 52
    const offset = circumference - (score / 100) * circumference;
    
    progressRing.style.strokeDashoffset = offset;
    
    // Change color based on score
    if (score >= 80) {
        progressRing.style.stroke = '#10b981'; // Green
    } else if (score >= 60) {
        progressRing.style.stroke = '#f59e0b'; // Orange
    } else {
        progressRing.style.stroke = '#ef4444'; // Red
    }
}

// Update summary tab
function updateSummaryTab(result) {
    const content = document.getElementById('summaryContent');
    
    let html = `
        <div class="summary-grid">
            <div class="summary-item">
                <h4>📊 Overall Score</h4>
                <p class="summary-value">${result.score || 0}%</p>
            </div>
            <div class="summary-item">
                <h4>✅ Strengths</h4>
                <p class="summary-value">${result.strengths?.length || 0} controls</p>
            </div>
            <div class="summary-item">
                <h4>⚠️ Gaps</h4>
                <p class="summary-value">${result.gaps?.length || 0} missing</p>
            </div>
            <div class="summary-item">
                <h4>🔍 Sections Found</h4>
                <p class="summary-value">${result.sections_found?.length || 0} sections</p>
            </div>
        </div>
    `;
    
    if (result.sections_found && result.sections_found.length > 0) {
        html += '<h4 style="margin-top: 30px;">Policy Sections Identified:</h4>';
        html += '<div class="sections-list">';
        result.sections_found.forEach(section => {
            html += `<span class="section-tag">${section}</span>`;
        });
        html += '</div>';
    }
    
    if (result.summary) {
        html += `<div class="summary-text" style="margin-top: 30px;">
            <h4>Analysis Summary</h4>
            <pre style="background: #f9fafb; color: #1f2937; padding: 15px; white-space: pre-wrap;">${result.summary}</pre>
        </div>`;
    }
    
    content.innerHTML = html;
}

// Update strengths tab
function updateStrengthsTab(strengths) {
    const content = document.getElementById('strengthsContent');
    
    if (strengths.length === 0) {
        content.innerHTML = '<p style="color: #6b7280;">No strengths identified</p>';
        return;
    }
    
    let html = '<div class="controls-list">';
    strengths.forEach(strength => {
        const [framework, control] = parseControl(strength);
        html += `
            <div class="control-item">
                <div>
                    <span class="control-framework">${framework}</span>
                    <span class="control-name">${control}</span>
                </div>
                <span class="control-badge badge-success">Implemented</span>
            </div>
        `;
    });
    html += '</div>';
    
    content.innerHTML = html;
}

// Update gaps tab
function updateGapsTab(gaps) {
    const content = document.getElementById('gapsContent');
    
    if (gaps.length === 0) {
        content.innerHTML = '<p style="color: #10b981; font-weight: 600;">✅ Excellent! No compliance gaps found.</p>';
        return;
    }
    
    let html = '<div class="controls-list">';
    gaps.forEach(gap => {
        const [framework, control] = parseControl(gap);
        const priority = getPriorityFromGap(gap);
        html += `
            <div class="control-item gap ${priority === 'Critical' ? 'critical' : ''}">
                <div>
                    <span class="control-framework">${framework}</span>
                    <span class="control-name">${control}</span>
                </div>
                <span class="control-badge badge-warning">Missing</span>
            </div>
        `;
    });
    html += '</div>';
    
    content.innerHTML = html;
}

// Update recommendations tab
function updateRecommendationsTab(recommendations) {
    const content = document.getElementById('recommendationsContent');
    
    if (!recommendations || recommendations.length === 0) {
        content.innerHTML = `
            <div class="premium-notice">
                <p>No recommendations available</p>
            </div>
        `;
        return;
    }
    
    let html = '<div class="recommendations-list">';
    recommendations.forEach((rec, index) => {
        const priorityClass = rec.priority.toLowerCase();
        html += `
            <div class="recommendation-card ${priorityClass}">
                <div class="recommendation-header">
                    <h4>${index + 1}. ${rec.control}</h4>
                    <span class="priority-badge priority-${priorityClass}">${rec.priority}</span>
                </div>
                <p><strong>📌 Recommendation:</strong> ${rec.recommendation}</p>
                <div class="recommendation-details">
                    💡 ${rec.details}
                </div>
            </div>
        `;
    });
    html += '</div>';
    
    content.innerHTML = html;
}

// Update raw data tab
function updateRawDataTab(result) {
    const content = document.getElementById('rawContent');
    content.textContent = JSON.stringify(result, null, 2);
}

// Parse control string
function parseControl(controlStr) {
    const parts = controlStr.split(' ');
    if (parts.length >= 2) {
        return [parts[0], parts.slice(1).join(' ')];
    }
    return ['', controlStr];
}

// Get priority from gap
function getPriorityFromGap(gap) {
    if (gap.toLowerCase().includes('critical') || gap.toLowerCase().includes('dpdp')) {
        return 'Critical';
    }
    return 'High';
}

// Switch tab
function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });
    
    // Update tab content
    document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.toggle('active', pane.id === tabName);
    });
}

// Unlock premium
async function unlockPremium() {
    if (!currentFile) {
        showNotification('Please upload a file first', 'error');
        return;
    }
    
    isPremium = true;
    await analyzePolicy(true);
}

// Download report
function downloadReport() {
    if (!lastAnalysisResult) {
        showNotification('No report available', 'error');
        return;
    }
    
    const dataStr = JSON.stringify(lastAnalysisResult, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
    
    const filename = isPremium ? 'premium_compliance_report.json' : 'compliance_report.json';
    
    const link = document.createElement('a');
    link.setAttribute('href', dataUri);
    link.setAttribute('download', filename);
    link.click();
}

// Analyze another policy
function analyzeAnother() {
    // Reset state
    currentFile = null;
    lastAnalysisResult = null;
    isPremium = false;
    
    // Reset file input
    const fileInput = document.getElementById('policyFile');
    if (fileInput) fileInput.value = '';
    
    const fileDisplay = document.querySelector('.file-input-display');
    if (fileDisplay) {
        fileDisplay.textContent = 'Choose file or drag here';
        fileDisplay.style.color = '#666';
    }
    
    // Reset progress
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    if (progressBar) progressBar.style.width = '0%';
    if (progressText) progressText.textContent = '0%';
    
    // Reset steps
    document.querySelectorAll('.step').forEach(step => {
        step.classList.remove('active', 'completed');
    });
    
    // Hide results, show upload
    const resultsSection = document.getElementById('results');
    const uploadSection = document.querySelector('.upload-section');
    const processSteps = document.getElementById('processSteps');
    
    if (resultsSection) resultsSection.style.display = 'none';
    if (uploadSection) uploadSection.style.display = 'block';
    if (processSteps) processSteps.style.display = 'none';
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
    
    showNotification('Ready to analyze another policy', 'success');
}

// Show notification
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'error' ? '#ef4444' : type === 'success' ? '#10b981' : '#2563eb'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 2000;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Close modal
function closeModal() {
    document.getElementById('jsonModal').style.display = 'none';
}

// Close API modal
function closeApiModal() {
    document.getElementById('apiKeyModal').style.display = 'none';
}

// Save API settings
function saveApiSettings() {
    userApiKey = document.getElementById('apiKeyInput').value;
    llmProvider = document.getElementById('llmProvider').value;
    
    // Store in localStorage
    localStorage.setItem('userApiKey', userApiKey);
    localStorage.setItem('llmProvider', llmProvider);
    
    showNotification(`Settings saved! Using ${llmProvider.toUpperCase()}`, 'success');
    closeApiModal();
}

// Processing timer
let processingTimer = null;
let processingStartTime = null;

function startProcessingTimer() {
    processingStartTime = Date.now();
    processingTimer = setInterval(() => {
        const elapsed = Math.floor((Date.now() - processingStartTime) / 1000);
        document.getElementById('processingTime').textContent = `${elapsed}s`;
    }, 1000);
}

function stopProcessingTimer() {
    if (processingTimer) {
        clearInterval(processingTimer);
        processingTimer = null;
    }
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .summary-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 20px;
        margin-bottom: 30px;
    }
    
    .summary-item {
        background: white;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
    }
    
    .summary-item h4 {
        color: #6b7280;
        font-size: 0.9rem;
        margin-bottom: 10px;
    }
    
    .summary-value {
        color: #1f2937;
        font-size: 1.5rem;
        font-weight: 700;
    }
    
    .sections-list {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 10px;
    }
    
    .section-tag {
        background: #dbeafe;
        color: #1e40af;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    .control-framework {
        background: #e5e7eb;
        color: #374151;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 8px;
    }
    
    .control-name {
        color: #1f2937;
        font-weight: 500;
    }
`;
document.head.appendChild(style);
