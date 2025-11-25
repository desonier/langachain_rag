// Model Selector Fix Script
// Add this to fix the configuration loading issue

console.log('🔧 Model Selector Fix Script loaded');

// Preserve original functions if they exist
window.originalShowMessage = window.showMessage;
window.originalLoadConfigurationTables = window.loadConfigurationTables;

// Override the loadConfigurationTables function with a working version
window.loadConfigurationTables = async function() {
    try {
        console.log('🔄 Loading configuration tables...');
        
        // Show loading indicators
        const llmTbody = document.getElementById('llm-models-tbody');
        const embeddingTbody = document.getElementById('embedding-models-tbody');
        
        if (llmTbody) {
            llmTbody.innerHTML = `
                <tr><td colspan="5" class="text-center py-4">
                    <i class="fas fa-spinner fa-spin fa-2x mb-2"></i><br>
                    Loading configuration...
                </td></tr>`;
        }
        
        if (embeddingTbody) {
            embeddingTbody.innerHTML = `
                <tr><td colspan="5" class="text-center py-4">
                    <i class="fas fa-spinner fa-spin fa-2x mb-2"></i><br>
                    Loading configuration...
                </td></tr>`;
        }
        
        // Create fetch requests with timeout
        const fetchWithTimeout = (url, timeout = 5000) => {
            return Promise.race([
                fetch(url),
                new Promise((_, reject) => 
                    setTimeout(() => reject(new Error(`Request timeout (${timeout}ms)`)), timeout)
                )
            ]);
        };
        
        console.log('📡 Fetching models and providers data...');
        
        // Load all configured models with timeout
        const [modelsResponse, providersResponse] = await Promise.all([
            fetchWithTimeout('/api/models/list', 5000),
            fetchWithTimeout('/api/providers/list', 5000)
        ]);
        
        console.log('✅ Got responses, parsing JSON...');
        
        if (!modelsResponse.ok) {
            throw new Error(`Models API error: ${modelsResponse.status}`);
        }
        if (!providersResponse.ok) {
            throw new Error(`Providers API error: ${providersResponse.status}`);
        }
        
        const modelsData = await modelsResponse.json();
        const providersData = await providersResponse.json();
        
        console.log('📊 Models data:', modelsData);
        console.log('🏢 Providers data:', providersData);
        
        if (modelsData.success && providersData.success) {
            console.log('🎯 Populating tables...');
            
            // Use the existing populateModelsTable function if available
            if (typeof populateModelsTable === 'function') {
                populateModelsTable('llm', modelsData.models, providersData.providers);
                populateModelsTable('embedding', modelsData.models, providersData.providers);
            } else {
                // Fallback: simple table population
                populateSimpleTable('llm', modelsData.models, providersData.providers);
                populateSimpleTable('embedding', modelsData.models, providersData.providers);
            }
            
            if (typeof updateConfigurationCounts === 'function') {
                updateConfigurationCounts(modelsData.models);
            }
            
            console.log('✅ Configuration tables loaded successfully');
        } else {
            const errorMsg = modelsData.error || providersData.error || 'Unknown error';
            console.error('❌ API response error:', errorMsg);
            showTableError('Failed to load configuration data: ' + errorMsg);
        }
    } catch (error) {
        console.error('❌ Error loading configuration:', error);
        showTableError('Error loading configuration: ' + error.message);
    }
};

// Fallback simple table population
function populateSimpleTable(modelType, allModels, allProviders) {
    const tbody = document.getElementById(`${modelType}-models-tbody`);
    if (!tbody) return;
    
    const models = allModels[modelType] || {};
    let html = '';
    
    Object.keys(models).forEach(providerId => {
        const providerModels = models[providerId] || [];
        const providerInfo = allProviders[modelType] ? allProviders[modelType][providerId] : {};
        const providerName = providerInfo.display_name || providerId;
        
        providerModels.forEach((modelName, index) => {
            const encodedModel = encodeURIComponent(modelName);
            html += `
                <tr id="model-row-${modelType}-${providerId}-${encodedModel}">
                    <td>
                        ${index === 0 ? `<span class="badge bg-primary">${providerName}</span>` : ''}
                    </td>
                    <td><strong>${modelName}</strong></td>
                    <td>
                        <span class="badge ${modelType === 'llm' ? 'bg-success' : 'bg-info'}">
                            ${modelType.toUpperCase()}
                        </span>
                    </td>
                    <td>
                        <button type="button" class="btn btn-sm btn-outline-success" 
                                onclick="testSingleModel('${providerId}', '${modelName}', '${modelType}')" 
                                title="Test model connection">
                            <i class="fas fa-check"></i>
                        </button>
                    </td>
                    <td>
                        <div class="btn-group" role="group">
                            <button type="button" class="btn btn-sm btn-outline-primary" 
                                    onclick="editModel('${providerId}', '${modelName}', '${modelType}')" 
                                    title="Edit model">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button type="button" class="btn btn-sm btn-outline-danger" 
                                    onclick="deleteModel('${providerId}', '${modelName}', '${modelType}')" 
                                    title="Delete model">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>`;
        });
    });
    
    if (html === '') {
        html = `
            <tr>
                <td colspan="5" class="text-center text-muted py-4">
                    <i class="fas fa-inbox fa-2x mb-2"></i><br>
                    No ${modelType.toUpperCase()} models configured yet.
                </td>
            </tr>`;
    }
    
    tbody.innerHTML = html;
}

// Model action functions
window.editModel = function(providerId, modelName, modelType) {
    const newModelName = prompt(`Edit model name:`, modelName);
    if (!newModelName || newModelName === modelName) return;
    
    console.log(`🔧 Editing model: ${providerId}:${modelName} -> ${newModelName}`);
    showMessage('Updating model...', 'info');
    
    // First add new model
    fetch('/api/models/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            provider_type: modelType,
            provider_id: providerId,
            model_name: newModelName
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Then delete old model
            return fetch('/api/models/delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    provider_type: modelType,
                    provider_id: providerId,
                    model_name: modelName
                })
            });
        } else {
            throw new Error(data.error);
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage(`✅ Model renamed to: ${newModelName}`, 'success');
            loadConfigurationTables(); // Refresh tables
            if (typeof loadCustomModels === 'function') {
                loadCustomModels(); // Refresh dropdowns if available
            }
        } else {
            throw new Error(data.error);
        }
    })
    .catch(error => {
        console.error('Edit error:', error);
        showMessage(`❌ Error editing model: ${error.message}`, 'error');
    });
};

window.deleteModel = function(providerId, modelName, modelType) {
    if (!confirm(`Delete model "${modelName}" from ${providerId}?\n\nThis action cannot be undone.`)) return;
    
    console.log(`🗑️ Deleting model: ${providerId}:${modelName}`);
    showMessage('Deleting model...', 'info');
    
    fetch('/api/models/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            provider_type: modelType,
            provider_id: providerId,
            model_name: modelName
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage(`✅ Model "${modelName}" deleted`, 'success');
            // Remove the row with animation
            const encodedModel = encodeURIComponent(modelName);
            const row = document.getElementById(`model-row-${modelType}-${providerId}-${encodedModel}`);
            if (row) {
                row.style.transition = 'opacity 0.3s';
                row.style.opacity = '0';
                setTimeout(() => {
                    loadConfigurationTables(); // Refresh tables
                    if (typeof loadCustomModels === 'function') {
                        loadCustomModels(); // Refresh dropdowns if available
                    }
                }, 300);
            } else {
                // Fallback: immediate refresh
                loadConfigurationTables();
            }
        } else {
            throw new Error(data.error);
        }
    })
    .catch(error => {
        console.error('Delete error:', error);
        showMessage(`❌ Error deleting model: ${error.message}`, 'error');
    });
};

window.testSingleModel = function(providerId, modelName, modelType) {
    console.log(`🧪 Testing model: ${providerId}:${modelName}`);
    showMessage(`Testing ${providerId}:${modelName}...`, 'info');
    
    fetch('/api/models/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            provider: providerId,
            model: modelName,
            test_type: modelType
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage(`✅ ${providerId}:${modelName} test successful`, 'success');
        } else {
            showMessage(`❌ ${providerId}:${modelName} test failed: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        console.error('Test error:', error);
        showMessage(`❌ Test error: ${error.message}`, 'error');
    });
};

// Message display function
window.showMessage = function(message, type = 'info') {
    console.log(`📢 ${type.toUpperCase()}: ${message}`);
    
    // Try to use existing showMessage function if available
    if (window.originalShowMessage && typeof window.originalShowMessage === 'function') {
        window.originalShowMessage(message, type);
        return;
    }
    
    // Fallback: simple alert for critical messages
    if (type === 'error') {
        alert(message);
    }
    
    // Try to find and update a message container
    let messageContainer = document.getElementById('message-container');
    if (!messageContainer) {
        messageContainer = document.querySelector('.alert');
    }
    
    if (messageContainer) {
        messageContainer.className = `alert alert-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info'}`;
        messageContainer.innerHTML = `<i class="fas fa-${type === 'error' ? 'exclamation-triangle' : type === 'success' ? 'check' : 'info-circle'}"></i> ${message}`;
        messageContainer.style.display = 'block';
        
        // Auto-hide after 3 seconds for non-error messages
        if (type !== 'error') {
            setTimeout(() => {
                if (messageContainer.style.display !== 'none') {
                    messageContainer.style.display = 'none';
                }
            }, 3000);
        }
    }
};

// Error display function
function showTableError(message) {
    const llmTbody = document.getElementById('llm-models-tbody');
    const embeddingTbody = document.getElementById('embedding-models-tbody');
    
    const errorHtml = `
        <tr><td colspan="5" class="text-center text-danger py-4">
            <i class="fas fa-exclamation-triangle fa-2x mb-2"></i><br>
            ${message}<br>
            <button onclick="loadConfigurationTables()" class="btn btn-sm btn-outline-primary mt-2">
                <i class="fas fa-redo"></i> Retry
            </button>
        </td></tr>`;
    
    if (llmTbody) llmTbody.innerHTML = errorHtml;
    if (embeddingTbody) embeddingTbody.innerHTML = errorHtml;
}

// Auto-load when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadConfigurationTables);
} else {
    // DOM already loaded
    setTimeout(loadConfigurationTables, 100);
}

console.log('✅ Model Selector Fix Script ready');