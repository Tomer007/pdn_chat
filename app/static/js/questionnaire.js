/**
 * PDN Questionnaire JavaScript Functions
 * Centralized functionality for the questionnaire interface
 */

// Global variables
let currentQuestion = 0;
let questionHistory = [];
let currentStage = '';
let isRecording = false;
let mediaRecorder = null;
let audioChunks = [];
let recordStartTime = 0;
let recordTimer = null;

// Constants
const TOTAL_QUESTIONS = 65; // Based on phases A-F (1-65)
const TOTAL_STEPS = 2 + TOTAL_QUESTIONS; // 2 voice steps + questions
const MIN_RECORDING_DURATION = 60; // 1 minute
const MAX_RECORDING_DURATION = 90; // 1.5 minutes

/**
 * Initialize questionnaire functionality
 */
function initializeQuestionnaire() {
    // Set up event listeners
    setupEventListeners();

    // Initialize progress
    updateProgress(0, 'מתחילים...');

    // Show first stage
    showNextStage();
}

/**
 * Set up event listeners for questionnaire elements
 */
function setupEventListeners() {
    // Back button
    const backButton = document.getElementById('backButton');
    if (backButton) {
        backButton.addEventListener('click', goBack);
    }

    // Modal close button
    const modalClose = document.getElementById('modalClose');
    if (modalClose) {
        modalClose.addEventListener('click', () => {
            hideModal('instructionModal');
        });
    }

    // Voice recording buttons
    const recordBtn = document.getElementById('recordBtn');
    if (recordBtn) {
        recordBtn.addEventListener('click', startRecording);
    }

    const stopBtn = document.getElementById('stopBtn');
    if (stopBtn) {
        stopBtn.addEventListener('click', stopRecording);
    }

    const retryRecordBtn = document.getElementById('retryRecordBtn');
    if (retryRecordBtn) {
        retryRecordBtn.addEventListener('click', retryRecording);
    }

    const retryRecordBtn2 = document.getElementById('retryRecordBtn2');
    if (retryRecordBtn2) {
        retryRecordBtn2.addEventListener('click', retryRecording2);
    }
}

/**
 * Update progress bar and label
 * @param {number} step - Current step number
 * @param {string} label - Progress label text
 */
function updateProgress(step, label) {
    const progressBar = document.getElementById('progressBar');
    const progressLabel = document.getElementById('progressLabel');
    const progressPercent = document.getElementById('progressPercent');

    if (progressBar && progressLabel && progressPercent) {
        const percentage = Math.round((step / TOTAL_STEPS) * 100);
        progressBar.style.width = percentage + '%';
        progressLabel.textContent = label;
        progressPercent.textContent = `${percentage}%`;
    }
}

/**
 * Show the next stage in the questionnaire
 */
function showNextStage() {
    if (currentQuestion === 0) {
        showVoiceRecordingStage(1);
    } else if (currentQuestion === 1) {
        showVoiceRecordingStage(2);
    } else if (currentQuestion <= TOTAL_QUESTIONS) {
        showQuestionStage();
    } else {
        showCompletion();
    }
}

/**
 * Show voice recording stage
 * @param {number} stageNumber - Stage number (1 or 2)
 */
function showVoiceRecordingStage(stageNumber) {
    currentStage = `voice${stageNumber}`;
    const messagesDiv = document.getElementById('messages');

    if (messagesDiv) {
        messagesDiv.innerHTML = `
            <div class="text-center space-y-6">
                <div class="text-2xl font-bold text-blue-900 mb-4">
                    הקלטה ${stageNumber}/2
                </div>
                
                <div class="bg-blue-50 p-6 rounded-2xl border-2 border-blue-200">
                    <h3 class="text-lg font-semibold text-blue-900 mb-3">הוראות הקלטה:</h3>
                    <ul class="text-right text-blue-800 space-y-2">
                        <li>• מצא/י מקום שקט להקלטה</li>
                        <li>• הקלט/י בין דקה לדקה וחצי</li>
                        <li>• דבר/י בקצב טבעי ורגוע</li>
                        <li>• תוכל/י להקליט מחדש אם תרצה/י</li>
                    </ul>
                </div>
                
                <div id="recordStatus" class="text-lg text-blue-900 font-medium">
                    לחץ/י על כפתור ההקלטה כדי להתחיל
                </div>
                
                <div class="flex justify-center space-x-4 space-x-reverse">
                    <button id="recordBtn" class="bg-red-600 hover:bg-red-700 text-white px-8 py-4 rounded-2xl font-semibold text-lg transition-all duration-300 transform hover:scale-105 shadow-lg">
                        <i class="fas fa-microphone mr-2"></i>
                        התחל הקלטה
                    </button>
                    <button id="stopBtn" class="bg-gray-600 hover:bg-gray-700 text-white px-8 py-4 rounded-2xl font-semibold text-lg transition-all duration-300 transform hover:scale-105 shadow-lg hidden">
                        <i class="fas fa-stop mr-2"></i>
                        עצור הקלטה
                    </button>
                </div>
                
                <div id="recordingControls" class="hidden space-y-4">
                    <div class="flex justify-center space-x-4 space-x-reverse">
                        <button id="retryRecordBtn" class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl font-medium transition-all duration-300 transform hover:scale-105">
                            <i class="fas fa-redo mr-2"></i>
                            הקלט מחדש
                        </button>
                        <button onclick="continueToNext()" class="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-xl font-medium transition-all duration-300 transform hover:scale-105">
                            <i class="fas fa-check mr-2"></i>
                            המשך
                        </button>
                    </div>
                </div>
            </div>
        `;

        // Re-setup event listeners for new elements
        setupVoiceRecordingListeners(stageNumber);
    }

    updateProgress(currentQuestion + 1, `הקלטה ${stageNumber}/2`);
}

/**
 * Set up event listeners for voice recording elements
 * @param {number} stageNumber - Stage number
 */
function setupVoiceRecordingListeners(stageNumber) {
    const recordBtn = document.getElementById('recordBtn');
    const stopBtn = document.getElementById('stopBtn');
    const retryRecordBtn = document.getElementById('retryRecordBtn');

    if (recordBtn) {
        recordBtn.addEventListener('click', startRecording);
    }

    if (stopBtn) {
        stopBtn.addEventListener('click', stopRecording);
    }

    if (retryRecordBtn) {
        retryRecordBtn.addEventListener('click', () => {
            if (stageNumber === 1) {
                retryRecording();
            } else {
                retryRecording2();
            }
        });
    }
}

/**
 * Start voice recording
 */
async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({audio: true});
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = () => {
            const audioBlob = new Blob(audioChunks, {type: 'audio/wav'});
            handleRecordingComplete(audioBlob);
        };

        mediaRecorder.start();
        isRecording = true;
        recordStartTime = Date.now();

        // Update UI
        document.getElementById('recordBtn').classList.add('hidden');
        document.getElementById('stopBtn').classList.remove('hidden');

        // Start timer
        startRecordingTimer();

        // Update status
        const recordStatus = document.getElementById('recordStatus');
        if (recordStatus) {
            recordStatus.innerHTML = '<span class="recording">מקליט... (00:00 / 01:00-01:30)</span>';
        }

    } catch (error) {
        console.error('Error starting recording:', error);
        alert('שגיאה בהתחלת ההקלטה. אנא ודא/י שיש לך הרשאה למיקרופון.');
    }
}

/**
 * Stop voice recording
 */
function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;

        // Stop timer
        if (recordTimer) {
            clearInterval(recordTimer);
            recordTimer = null;
        }

        // Update UI
        document.getElementById('recordBtn').classList.remove('hidden');
        document.getElementById('stopBtn').classList.add('hidden');

        // Get all tracks and stop them
        if (mediaRecorder.stream) {
            mediaRecorder.stream.getTracks().forEach(track => track.stop());
        }
    }
}

/**
 * Start recording timer
 */
function startRecordingTimer() {
    recordTimer = setInterval(() => {
        const elapsed = Math.floor((Date.now() - recordStartTime) / 1000);
        const min = Math.floor(elapsed / 60);
        const sec = elapsed % 60;

        const recordStatus = document.getElementById('recordStatus');
        if (recordStatus) {
            let statusText = `מקליט... (${("0" + min).slice(-2)}:${("0" + sec).slice(-2)} / 01:00-01:30)`;

            if (elapsed >= MIN_RECORDING_DURATION && elapsed <= MAX_RECORDING_DURATION) {
                statusText += ' ✅';
            } else if (elapsed > MAX_RECORDING_DURATION) {
                statusText += ' ⚠️';
            }

            recordStatus.innerHTML = `<span class="recording">${statusText}</span>`;
        }
    }, 1000);
}

/**
 * Handle recording completion
 * @param {Blob} audioBlob - Recorded audio data
 */
function handleRecordingComplete(audioBlob) {
    const recordElapsed = Math.floor((Date.now() - recordStartTime) / 1000);
    const recordStatus = document.getElementById('recordStatus');

    // Check if recording duration is valid
    if (recordElapsed >= MIN_RECORDING_DURATION && recordElapsed <= MAX_RECORDING_DURATION) {
        if (recordStatus) {
            recordStatus.innerHTML = '<span class="text-green-600 font-semibold">✅ הקלטה הושלמה בהצלחה!</span>';
        }

        // Show recording controls
        const recordingControls = document.getElementById('recordingControls');
        if (recordingControls) {
            recordingControls.classList.remove('hidden');
        }

        // Save audio
        saveRecording(audioBlob);

    } else {
        if (recordStatus) {
            recordStatus.innerHTML = '<span class="text-red-600 font-semibold">⚠️ משך ההקלטה לא תקין. אנא הקלט/י בין דקה לדקה וחצי.</span>';
        }

        // Show retry button
        const recordingControls = document.getElementById('recordingControls');
        if (recordingControls) {
            recordingControls.classList.remove('hidden');
        }
    }
}

/**
 * Save recording to server
 * @param {Blob} audioBlob - Audio data to save
 */
async function saveRecording(audioBlob) {
    try {
        const username = document.getElementById('userName')?.value || 'user';
        const question = currentStage === 'voice1' ? 'question1' : 'question2';

        const result = await saveUserAudio(username, audioBlob, question);
        console.log('Recording saved:', result);

    } catch (error) {
        console.error('Error saving recording:', error);
        alert('שגיאה בשמירת ההקלטה. אנא נסה/י שוב.');
    }
}

/**
 * Retry first recording
 */
function retryRecording() {
    // Reset UI
    document.getElementById('recordStatus').innerHTML = 'לחץ/י על כפתור ההקלטה כדי להתחיל';
    document.getElementById('recordingControls').classList.add('hidden');

    // Reset state
    isRecording = false;
    audioChunks = [];
    if (recordTimer) {
        clearInterval(recordTimer);
        recordTimer = null;
    }
}

/**
 * Retry second recording
 */
function retryRecording2() {
    retryRecording();
}

/**
 * Continue to next stage
 */
function continueToNext() {
    currentQuestion++;
    showNextStage();
}

/**
 * Go back to previous question/stage
 */
function goBack() {
    if (questionHistory.length > 0) {
        currentQuestion--;
        const previousData = questionHistory.pop();
        showQuestion(previousData);
    }
}

/**
 * Show question stage
 */
function showQuestionStage() {
    currentStage = 'question';

    // Fetch question data from server
    fetchQuestionData(currentQuestion);
}

/**
 * Fetch question data from server
 * @param {number} questionNumber - Question number to fetch
 */
async function fetchQuestionData(questionNumber) {
    try {
        const response = await fetch('/pdn-diagnose/api/question', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                question_number: questionNumber,
                user_id: document.getElementById('userId')?.value || ''
            })
        });

        if (response.ok) {
            const data = await response.json();
            showQuestion(data);
        } else {
            throw new Error('Failed to fetch question');
        }

    } catch (error) {
        console.error('Error fetching question:', error);
        showError('שגיאה בטעינת השאלה. אנא רענן/י את הדף.');
    }
}

/**
 * Show question interface
 * @param {Object} data - Question data
 */
function showQuestion(data) {
    const messagesDiv = document.getElementById('messages');

    if (messagesDiv) {
        messagesDiv.innerHTML = `
            <div class="text-center space-y-6">
                <div class="text-2xl font-bold text-blue-900 mb-4">
                    שאלה ${data.question_number} מתוך ${TOTAL_QUESTIONS}
                </div>
                
                <div class="bg-white p-6 rounded-2xl border-2 border-blue-200">
                    <p class="text-lg text-gray-800 leading-relaxed">
                        ${data.question}
                    </p>
                </div>
                
                <div id="options" class="space-y-4">
                    <!-- Options will be rendered here -->
                </div>
                
                <div class="flex justify-center space-x-4 space-x-reverse">
                    <button id="backButton" class="bg-gray-600 hover:bg-gray-700 text-white px-6 py-3 rounded-xl font-medium transition-all duration-300 transform hover:scale-105 ${questionHistory.length === 0 ? 'hidden' : ''}">
                        <i class="fas fa-arrow-right mr-2"></i>
                        חזור
                    </button>
                </div>
            </div>
        `;

        // Render question options
        renderQuestionOptions(data);

        // Update progress
        updateProgress(currentQuestion + 1, `שאלה ${data.question_number} מתוך ${TOTAL_QUESTIONS}`);
    }
}

/**
 * Render question options
 * @param {Object} data - Question data
 */
function renderQuestionOptions(data) {
    const optionsDiv = document.getElementById('options');

    if (['PartC', 'PartD'].includes(data.stage)) {
        renderScaleQuestion(data, data.question_number);
        return;
    }

    if (data.type === 'ranking') {
        renderRankingQuestion(data, data.question_number);
        return;
    }

    // Create regular option buttons
    const buttons = data.options.map(opt => {
        const btn = document.createElement('button');
        btn.innerText = opt.text;
        btn.className = 'text-lg fade-in w-full py-4 px-6 bg-gradient-to-r from-blue-900 to-blue-900 text-white font-medium rounded-xl hover:from-blue-900 hover:to-blue-900 focus:outline-none focus:ring-4 focus:ring-blue-900/50 transition-all duration-300 transform hover:scale-[1.02] active:scale-[0.98] shadow-lg';
        btn.onclick = () => submitAnswer(data.question_number, opt.code, opt.text);
        return btn;
    });

    // Randomize button order
    buttons.sort(() => Math.random() - 0.5);

    // Append buttons
    buttons.forEach(btn => optionsDiv.appendChild(btn));
}

/**
 * Submit answer to server
 * @param {number} questionNumber - Question number
 * @param {string} answerCode - Answer code
 * @param {string} answerText - Answer text
 */
async function submitAnswer(questionNumber, answerCode, answerText) {
    try {
        const response = await fetch('/pdn-diagnose/api/answer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                question_number: questionNumber,
                answer: answerCode,
                answer_text: answerText,
                user_id: document.getElementById('userId')?.value || ''
            })
        });

        if (response.ok) {
            // Store in history
            questionHistory.push({
                question_number: questionNumber,
                answer: answerCode,
                answer_text: answerText
            });

            // Move to next question
            currentQuestion++;
            showNextStage();

        } else {
            throw new Error('Failed to submit answer');
        }

    } catch (error) {
        console.error('Error submitting answer:', error);
        showError('שגיאה בשליחת התשובה. אנא נסה/י שוב.');
    }
}

/**
 * Show completion message
 */
function showCompletion() {
    const messagesDiv = document.getElementById('messages');

    if (messagesDiv) {
        messagesDiv.innerHTML = `
            <div class="text-center space-y-6">
                <div class="text-3xl font-bold text-green-600 mb-4">
                    🎉 סיימת את האבחון בהצלחה!
                </div>
                
                <div class="bg-green-50 p-6 rounded-2xl border-2 border-green-200">
                    <p class="text-lg text-green-800 leading-relaxed">
                        תודה שהשלמת את האבחון. תוצאותיך יישלחו אליך במייל בקרוב.
                    </p>
                </div>
                
                <button onclick="window.location.href='/pdn-diagnose/report'" class="bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 rounded-2xl font-semibold text-lg transition-all duration-300 transform hover:scale-105">
                    <i class="fas fa-chart-bar mr-2"></i>
                    צפה בתוצאות
                </button>
            </div>
        `;

        updateProgress(TOTAL_STEPS, 'הושלם!');
    }
}

/**
 * Show error message
 * @param {string} message - Error message
 */
function showError(message) {
    const messagesDiv = document.getElementById('messages');

    if (messagesDiv) {
        messagesDiv.innerHTML = `
            <div class="text-center space-y-6">
                <div class="text-2xl font-bold text-red-600 mb-4">
                    ⚠️ שגיאה
                </div>
                
                <div class="bg-red-50 p-6 rounded-2xl border-2 border-red-200">
                    <p class="text-lg text-red-800 leading-relaxed">
                        ${message}
                    </p>
                </div>
                
                <button onclick="location.reload()" class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl font-medium transition-all duration-300 transform hover:scale-105">
                    <i class="fas fa-redo mr-2"></i>
                    נסה שוב
                </button>
            </div>
        `;
    }
}

/**
 * Show modal with instructions
 * @param {string} title - Modal title
 * @param {string} text - Modal text
 */
function showInstructionModal(title, text) {
    const modal = document.getElementById('instructionModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalText = document.getElementById('modalText');

    if (modal && modalTitle && modalText) {
        modalTitle.textContent = title;
        modalText.textContent = text;
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }
}

/**
 * Hide modal
 * @param {string} modalId - Modal ID to hide
 */
function hideModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
}

// Scale question rendering (placeholder)
function renderScaleQuestion(data, questionNumber) {
    // Implementation for scale questions
    console.log('Rendering scale question:', data);
}

// Ranking question rendering (placeholder)
function renderRankingQuestion(data, questionNumber) {
    // Implementation for ranking questions
    console.log('Rendering ranking question:', data);
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    initializeQuestionnaire();
});

// Export functions for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initializeQuestionnaire,
        updateProgress,
        showNextStage,
        startRecording,
        stopRecording,
        submitAnswer,
        goBack
    };
}
