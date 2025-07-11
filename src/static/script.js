// Configuración de la API
const API_BASE_URL = '/api/rag';

// Referencias a elementos del DOM
const elements = {
    welcomeSection: document.getElementById('welcomeSection'),
    chatContainer: document.getElementById('chatContainer'),
    messagesContainer: document.getElementById('messagesContainer'),
    messageInput: document.getElementById('messageInput'),
    sendButton: document.getElementById('sendButton'),
    loadingOverlay: document.getElementById('loadingOverlay'),
    statusIndicator: document.getElementById('statusIndicator'),
    statusText: document.getElementById('statusText'),
    statsBtn: document.getElementById('statsBtn'),
    statsModal: document.getElementById('statsModal'),
    closeStatsModal: document.getElementById('closeStatsModal'),
    statsContent: document.getElementById('statsContent')
};

// Estado de la aplicación
const appState = {
    isLoading: false,
    systemReady: false,
    conversationStarted: false
};

// Inicialización de la aplicación
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    checkSystemHealth();
});

function initializeApp() {
    // Auto-resize del textarea
    autoResizeTextarea();
    
    // Configurar preguntas de ejemplo
    setupExampleQuestions();
    
    console.log('Aplicación inicializada');
}

function setupEventListeners() {
    // Envío de mensajes
    elements.sendButton.addEventListener('click', sendMessage);
    elements.messageInput.addEventListener('keydown', handleKeyDown);
    elements.messageInput.addEventListener('input', handleInputChange);
    
    // Modal de estadísticas
    elements.statsBtn.addEventListener('click', showStatsModal);
    elements.closeStatsModal.addEventListener('click', hideStatsModal);
    elements.statsModal.addEventListener('click', function(e) {
        if (e.target === elements.statsModal) {
            hideStatsModal();
        }
    });
    
    // Escape para cerrar modal
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && elements.statsModal.classList.contains('active')) {
            hideStatsModal();
        }
    });
}

function setupExampleQuestions() {
    const questionCards = document.querySelectorAll('.question-card');
    questionCards.forEach(card => {
        card.addEventListener('click', function() {
            const question = this.getAttribute('data-question');
            elements.messageInput.value = question;
            handleInputChange();
            sendMessage();
        });
    });
}

function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

function handleInputChange() {
    const hasText = elements.messageInput.value.trim().length > 0;
    elements.sendButton.disabled = !hasText || appState.isLoading;
    
    // Auto-resize
    autoResizeTextarea();
}

function autoResizeTextarea() {
    elements.messageInput.style.height = 'auto';
    elements.messageInput.style.height = elements.messageInput.scrollHeight + 'px';
}

async function sendMessage() {
    const message = elements.messageInput.value.trim();
    if (!message || appState.isLoading) return;
    
    // Mostrar mensaje del usuario
    addMessage('user', message);
    
    // Limpiar input
    elements.messageInput.value = '';
    handleInputChange();
    
    // Cambiar a vista de chat si es la primera vez
    if (!appState.conversationStarted) {
        showChatView();
        appState.conversationStarted = true;
    }
    
    // Mostrar loading
    setLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        });
        
        if (!response.ok) {
            throw new Error(`Error ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Mostrar respuesta del asistente
        addMessage('assistant', data.response, data.sources);
        
    } catch (error) {
        console.error('Error enviando mensaje:', error);
        addMessage('assistant', 
            'Lo siento, ocurrió un error al procesar tu mensaje. Por favor, inténtalo de nuevo.', 
            [], 
            true
        );
    } finally {
        setLoading(false);
    }
}

function addMessage(type, content, sources = [], isError = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    const avatar = type === 'user' ? 'U' : 'AI';
    const author = type === 'user' ? 'Tú' : 'Asistente';
    
    let sourcesHtml = '';
    if (sources && sources.length > 0) {
        sourcesHtml = `
            <div class="sources-section">
                <div class="sources-title">
                    <i class="fas fa-book"></i>
                    Fuentes consultadas:
                </div>
                <div class="sources-list">
                    ${sources.map(source => `
                        <div class="source-item">
                            <div class="source-title">${source.title}</div>
                            <div class="source-meta">
                                ${source.type === 'paper' ? 
                                    `${source.authors} (${source.year}) • Similitud: ${(source.similarity * 100).toFixed(1)}%` :
                                    `Tipo: ${source.type} • Similitud: ${(source.similarity * 100).toFixed(1)}%`
                                }
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    messageDiv.innerHTML = `
        <div class="message-header">
            <div class="message-avatar">${avatar}</div>
            <div class="message-author">${author}</div>
        </div>
        <div class="message-content ${isError ? 'error' : ''}">
            ${formatMessageContent(content)}
            ${sourcesHtml}
        </div>
    `;
    
    elements.messagesContainer.appendChild(messageDiv);
    
    // Scroll al final
    elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;
}

function formatMessageContent(content) {
    // Convertir saltos de línea a <br>
    content = content.replace(/\n/g, '<br>');
    
    // Formatear texto en negrita
    content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Formatear listas
    content = content.replace(/^- (.+)$/gm, '<li>$1</li>');
    content = content.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
    
    return content;
}

function showChatView() {
    elements.welcomeSection.style.display = 'none';
    elements.chatContainer.classList.add('active');
}

function setLoading(loading) {
    appState.isLoading = loading;
    elements.loadingOverlay.classList.toggle('active', loading);
    elements.sendButton.disabled = loading || elements.messageInput.value.trim().length === 0;
}

async function checkSystemHealth() {
    try {
        updateStatus('connecting', 'Conectando...');
        
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        
        if (data.status === 'healthy' && data.system_ready) {
            updateStatus('ready', `Sistema listo (${data.documents_loaded} documentos)`);
            appState.systemReady = true;
        } else {
            updateStatus('error', 'Sistema no disponible');
        }
    } catch (error) {
        console.error('Error verificando estado del sistema:', error);
        updateStatus('error', 'Error de conexión');
    }
}

function updateStatus(status, text) {
    elements.statusIndicator.className = `status-indicator ${status}`;
    elements.statusText.textContent = text;
}

async function showStatsModal() {
    elements.statsModal.classList.add('active');
    
    try {
        const response = await fetch(`${API_BASE_URL}/stats`);
        const stats = await response.json();
        
        elements.statsContent.innerHTML = `
            <div class="stats-grid">
                <div class="stat-item">
                    <span class="stat-value">${stats.total_documents || 0}</span>
                    <div class="stat-label">Total de Documentos</div>
                </div>
                <div class="stat-item">
                    <span class="stat-value">${stats.papers || 0}</span>
                    <div class="stat-label">Papers Académicos</div>
                </div>
                <div class="stat-item">
                    <span class="stat-value">${stats.synthesis || 0}</span>
                    <div class="stat-label">Documentos de Síntesis</div>
                </div>
                <div class="stat-item">
                    <span class="stat-value">${stats.clusters || 0}</span>
                    <div class="stat-label">Clusters Conceptuales</div>
                </div>
                <div class="stat-item">
                    <span class="stat-value">${stats.innovations || 0}</span>
                    <div class="stat-label">Indicadores de Innovación</div>
                </div>
            </div>
            <div style="margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid var(--border-color); font-size: 0.875rem; color: var(--text-secondary);">
                <p><strong>Fuente:</strong> Annual Review of Psychology - Comprehensive Psychological Science and Mental Health Research</p>
                <p><strong>Metodología:</strong> ELM (Enhanced Literature Mining) Journal Enhanced 1.0</p>
                <p><strong>Modelo de embeddings:</strong> all-MiniLM-L6-v2</p>
            </div>
        `;
    } catch (error) {
        console.error('Error cargando estadísticas:', error);
        elements.statsContent.innerHTML = `
            <div style="text-align: center; color: var(--error-color);">
                <i class="fas fa-exclamation-triangle" style="font-size: 2rem; margin-bottom: 1rem;"></i>
                <p>Error al cargar las estadísticas</p>
            </div>
        `;
    }
}

function hideStatsModal() {
    elements.statsModal.classList.remove('active');
}

// Utilidades
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Manejo de errores globales
window.addEventListener('error', function(e) {
    console.error('Error global:', e.error);
});

window.addEventListener('unhandledrejection', function(e) {
    console.error('Promise rechazada:', e.reason);
});

// Verificar estado del sistema periódicamente
setInterval(checkSystemHealth, 30000); // Cada 30 segundos

