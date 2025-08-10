/**
 * PDN Chat JavaScript Functions
 * Centralized functionality for the chat interface
 */

// Global variables
let chatHistory = [];
let isTyping = false;
let currentConversationId = null;

/**
 * Initialize chat functionality
 */
function initializeChat() {
    // Set up event listeners
    setupChatEventListeners();
    
    // Load chat history
    loadChatHistory();
    
    // Set up auto-scroll
    setupAutoScroll();
    
    // Initialize typing indicator
    initializeTypingIndicator();
}

/**
 * Set up event listeners for chat elements
 */
function setupChatEventListeners() {
    // Send button
    const sendButton = document.getElementById('sendButton');
    if (sendButton) {
        sendButton.addEventListener('click', sendMessage);
    }
    
    // Input field
    const inputField = document.getElementById('inputField');
    if (inputField) {
        inputField.addEventListener('keypress', handleKeyPress);
        inputField.addEventListener('input', handleInput);
    }
    
    // Quick reply buttons
    const quickReplyButtons = document.querySelectorAll('.quick-reply-btn');
    quickReplyButtons.forEach(button => {
        button.addEventListener('click', () => {
            const message = button.textContent;
            sendQuickReply(message);
        });
    });
    
    // Theme toggle
    const themeToggle = document.querySelector('.theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
}

/**
 * Handle key press in input field
 * @param {KeyboardEvent} event - Key press event
 */
function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

/**
 * Handle input field changes
 * @param {Event} event - Input event
 */
function handleInput(event) {
    const inputField = event.target;
    const sendButton = document.getElementById('sendButton');
    
    if (sendButton) {
        if (inputField.value.trim()) {
            sendButton.disabled = false;
            sendButton.classList.remove('opacity-50', 'cursor-not-allowed');
        } else {
            sendButton.disabled = true;
            sendButton.classList.add('opacity-50', 'cursor-not-allowed');
        }
    }
}

/**
 * Send message to chat
 */
async function sendMessage() {
    const inputField = document.getElementById('inputField');
    const message = inputField.value.trim();
    
    if (!message || isTyping) return;
    
    // Clear input
    inputField.value = '';
    updateSendButton();
    
    // Add user message to chat
    addMessageToChat('user', message);
    
    // Show typing indicator
    showTypingIndicator();
    
    try {
        // Send message to server
        const response = await fetch('/pdn-chat-ai/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                conversation_id: currentConversationId
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            
            // Hide typing indicator
            hideTypingIndicator();
            
            // Add bot response to chat
            if (data.response) {
                addMessageToChat('bot', data.response);
            }
            
            // Update conversation ID
            if (data.conversation_id) {
                currentConversationId = data.conversation_id;
            }
            
            // Save to history
            saveToChatHistory(message, data.response);
            
        } else {
            throw new Error('Failed to send message');
        }
        
    } catch (error) {
        console.error('Error sending message:', error);
        hideTypingIndicator();
        showErrorMessage('שגיאה בשליחת ההודעה. אנא נסה/י שוב.');
    }
}

/**
 * Send quick reply message
 * @param {string} message - Quick reply message
 */
function sendQuickReply(message) {
    const inputField = document.getElementById('inputField');
    inputField.value = message;
    updateSendButton();
    sendMessage();
}

/**
 * Add message to chat interface
 * @param {string} sender - 'user' or 'bot'
 * @param {string} message - Message content
 */
function addMessageToChat(sender, message) {
    const messagesContainer = document.getElementById('messages');
    if (!messagesContainer) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-bubble ${sender} animated`;
    
    const timestamp = getCurrentTime();
    
    messageDiv.innerHTML = `
        <div class="flex items-start space-x-3 space-x-reverse">
            <div class="flex-shrink-0">
                <div class="w-8 h-8 rounded-full bg-${sender === 'user' ? 'blue' : 'gray'}-500 flex items-center justify-center">
                    <i class="fas fa-${sender === 'user' ? 'user' : 'robot'} text-white text-sm"></i>
                </div>
            </div>
            <div class="flex-1 min-w-0">
                <div class="text-sm text-gray-500 mb-1">
                    ${sender === 'user' ? 'אתה' : 'PDN AI'} • ${timestamp}
                </div>
                <div class="text-gray-900 leading-relaxed">
                    ${message}
                </div>
            </div>
        </div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    scrollToBottom();
    
    // Add to history
    chatHistory.push({
        sender: sender,
        message: message,
        timestamp: new Date(),
        type: 'text'
    });
}

/**
 * Show typing indicator
 */
function showTypingIndicator() {
    isTyping = true;
    const messagesContainer = document.getElementById('messages');
    if (!messagesContainer) return;
    
    const typingDiv = document.createElement('div');
    typingDiv.id = 'typingIndicator';
    typingDiv.className = 'chat-bubble bot typing-indicator';
    
    typingDiv.innerHTML = `
        <div class="flex items-center space-x-2 space-x-reverse">
            <div class="flex space-x-1 space-x-reverse">
                <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
            </div>
            <span class="text-gray-500 text-sm">PDN AI כותב...</span>
        </div>
    `;
    
    messagesContainer.appendChild(typingDiv);
    scrollToBottom();
}

/**
 * Hide typing indicator
 */
function hideTypingIndicator() {
    isTyping = false;
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

/**
 * Show error message
 * @param {string} message - Error message
 */
function showErrorMessage(message) {
    const messagesContainer = document.getElementById('messages');
    if (!messagesContainer) return;
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'chat-bubble bot error-message';
    
    errorDiv.innerHTML = `
        <div class="flex items-center space-x-2 space-x-reverse text-red-600">
            <i class="fas fa-exclamation-triangle"></i>
            <span>${message}</span>
        </div>
    `;
    
    messagesContainer.appendChild(errorDiv);
    scrollToBottom();
}

/**
 * Update send button state
 */
function updateSendButton() {
    const inputField = document.getElementById('inputField');
    const sendButton = document.getElementById('sendButton');
    
    if (inputField && sendButton) {
        if (inputField.value.trim()) {
            sendButton.disabled = false;
            sendButton.classList.remove('opacity-50', 'cursor-not-allowed');
        } else {
            sendButton.disabled = true;
            sendButton.classList.add('opacity-50', 'cursor-not-allowed');
        }
    }
}

/**
 * Scroll chat to bottom
 */
function scrollToBottom() {
    const messagesContainer = document.getElementById('messages');
    if (messagesContainer) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}

/**
 * Set up auto-scroll functionality
 */
function setupAutoScroll() {
    const messagesContainer = document.getElementById('messages');
    if (messagesContainer) {
        messagesContainer.addEventListener('scroll', () => {
            const isAtBottom = isAtBottom(messagesContainer);
            // You can add visual indicators here if needed
        });
    }
}

/**
 * Initialize typing indicator
 */
function initializeTypingIndicator() {
    // This function can be used to set up any typing indicator related functionality
    console.log('Typing indicator initialized');
}

/**
 * Load chat history from localStorage
 */
function loadChatHistory() {
    try {
        const savedHistory = localStorage.getItem('pdnChatHistory');
        if (savedHistory) {
            chatHistory = JSON.parse(savedHistory);
            
            // Render saved messages
            chatHistory.forEach(item => {
                if (item.type === 'text') {
                    addMessageToChat(item.sender, item.message);
                }
            });
        }
    } catch (error) {
        console.error('Error loading chat history:', error);
    }
}

/**
 * Save message to chat history
 * @param {string} userMessage - User message
 * @param {string} botResponse - Bot response
 */
function saveToChatHistory(userMessage, botResponse) {
    try {
        // Save to localStorage
        localStorage.setItem('pdnChatHistory', JSON.stringify(chatHistory));
        
        // Optionally save to server
        saveConversationToServer(userMessage, botResponse);
        
    } catch (error) {
        console.error('Error saving chat history:', error);
    }
}

/**
 * Save conversation to server
 * @param {string} userMessage - User message
 * @param {string} botResponse - Bot response
 */
async function saveConversationToServer(userMessage, botResponse) {
    try {
        await fetch('/pdn-chat-ai/api/save-conversation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_message: userMessage,
                bot_response: botResponse,
                conversation_id: currentConversationId,
                timestamp: new Date().toISOString()
            })
        });
    } catch (error) {
        console.error('Error saving conversation to server:', error);
    }
}

/**
 * Clear chat history
 */
function clearChatHistory() {
    if (confirm('האם אתה בטוח שברצונך למחוק את היסטוריית הצ\'אט?')) {
        chatHistory = [];
        localStorage.removeItem('pdnChatHistory');
        
        const messagesContainer = document.getElementById('messages');
        if (messagesContainer) {
            messagesContainer.innerHTML = '';
        }
        
        // Show welcome message
        addMessageToChat('bot', 'שלום! אני PDN AI, איך אוכל לעזור לך היום?');
    }
}

/**
 * Export chat history
 */
function exportChatHistory() {
    try {
        const dataStr = JSON.stringify(chatHistory, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        
        const link = document.createElement('a');
        link.href = URL.createObjectURL(dataBlob);
        link.download = `pdn-chat-history-${new Date().toISOString().split('T')[0]}.json`;
        link.click();
        
    } catch (error) {
        console.error('Error exporting chat history:', error);
        alert('שגיאה בייצוא היסטוריית הצ\'אט.');
    }
}

/**
 * Search chat history
 * @param {string} query - Search query
 */
function searchChatHistory(query) {
    if (!query.trim()) return chatHistory;
    
    return chatHistory.filter(item => 
        item.type === 'text' && 
        (item.message.toLowerCase().includes(query.toLowerCase()) ||
         item.sender.toLowerCase().includes(query.toLowerCase()))
    );
}

/**
 * Get chat statistics
 * @returns {Object} Chat statistics
 */
function getChatStatistics() {
    const totalMessages = chatHistory.length;
    const userMessages = chatHistory.filter(item => item.sender === 'user').length;
    const botMessages = chatHistory.filter(item => item.sender === 'bot').length;
    
    return {
        total: totalMessages,
        user: userMessages,
        bot: botMessages,
        averageLength: totalMessages > 0 ? 
            Math.round(chatHistory.reduce((sum, item) => sum + item.message.length, 0) / totalMessages) : 0
    };
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeChat();
});

// Export functions for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initializeChat,
        sendMessage,
        addMessageToChat,
        clearChatHistory,
        exportChatHistory,
        searchChatHistory,
        getChatStatistics
    };
}
