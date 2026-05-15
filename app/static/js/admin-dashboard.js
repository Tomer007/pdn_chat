// Debounce utility
function debounce(fn, delay) {
    let timer;
    return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), delay); };
}

// Utility: Get user email from modal content (assumes email is present in a data attribute or visible field)
function getDiagnosisUserEmail() {
    // Try to find an element with data-email or fallback to text content
    const emailElem = document.querySelector('#questionnaireContent [data-email]');
    if (emailElem) return emailElem.getAttribute('data-email');
    // Fallback: try to find a visible email in the content
    const match = document.getElementById('questionnaireContent').innerText.match(/[\w.-]+@[\w.-]+/);
    return match ? match[0] : 'user';
}

// Main download function that handles multiple formats
function downloadReport(format = 'pdf') {
    switch (format) {
        case 'pdf':
            downloadDiagnosisAsPDF();
            break;
        case 'json':
            downloadUserJSON();
            break;
        default:
            alert('פורמט לא נתמך');
    }
}

// Main PDF export function
function downloadDiagnosisAsPDF() {
    const content = document.getElementById('questionnaireContent');
    if (!content) {
        alert('לא נמצאו נתונים לייצוא');
        return;
    }

    // Create a new container for the complete report
    const reportContainer = document.createElement('div');
    reportContainer.style.cssText = `
    font-family: 'Noto Sans Hebrew', 'Arial', sans-serif !important;
    direction: rtl !important;
    text-align: right !important;
    font-size: 14px !important;
    line-height: 1.6 !important;
    color: #000 !important;
    background: white !important;
    padding: 20px !important;
    width: 100% !important;
    max-width: 800px !important;
    margin: 0 auto !important;
`;
    reportContainer.setAttribute('dir', 'rtl');
    reportContainer.setAttribute('lang', 'he');

    // Clone the questionnaire content
    const questionnaireClone = content.cloneNode(true);

    // Remove the user metadata section from the clone
    const metadataSection = questionnaireClone.querySelector('.bg-gradient-to-br.from-blue-50.via-blue-50.to-blue-100');
    if (metadataSection) {
        metadataSection.remove();
    }

    // Find the questionnaire section and add user ID before it
    const questionnaireSection = questionnaireClone.querySelector('.bg-white.p-8.rounded-2xl.border.border-gray-200.shadow-lg.mt-6');
    if (questionnaireSection) {
        // Create user ID section
        const userIdSection = document.createElement('div');
        userIdSection.style.cssText = `
        background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
        border: 1px solid #d1d5db;
        text-align: center;
        font-family: 'Noto Sans Hebrew', 'Arial', sans-serif !important;
        direction: rtl !important;
    `;

        const userId = getUserMetadata('user_id');
        userIdSection.innerHTML = `
        <div style="font-size: 16px; font-weight: bold; color: #374151; margin-bottom: 8px; font-family: 'Noto Sans Hebrew', 'Arial', sans-serif;">
            מזהה מערכת
        </div>
        <div style="font-family: monospace; font-size: 18px; font-weight: bold; color: #1e40af; background: white; padding: 8px 16px; border-radius: 8px; display: inline-block; border: 1px solid #d1d5db;">
            ${userId}
        </div>
    `;

        // Insert the user ID section before the questionnaire section
        questionnaireSection.parentNode.insertBefore(userIdSection, questionnaireSection);
    }

    // Apply RTL and font styles to all elements in the clone
    const allElements = questionnaireClone.querySelectorAll('*');
    allElements.forEach(element => {
        element.style.fontFamily = "'Noto Sans Hebrew', 'Arial', sans-serif";
        element.style.direction = 'rtl';
        element.style.textAlign = 'right';
    });

    // Add the modified content to the report container
    reportContainer.appendChild(questionnaireClone);

    // Generate filename with user ID and date
    const userId = getUserMetadata('user_id');
    const date = new Date().toLocaleDateString('he-IL', {year: 'numeric', month: '2-digit', day: '2-digit'});

    // Create filename: user_id_date.pdf
    const filename = `${userId}_${date}.pdf`;

    // PDF options with better Hebrew support
    const opt = {
        margin: [0.5, 0.5, 0.5, 0.5], // inches (top, left, bottom, right)
        filename: filename,
        image: {type: 'jpeg', quality: 0.98},
        html2canvas: {
            scale: 2,
            useCORS: true,
            allowTaint: true,
            backgroundColor: '#ffffff'
        },
        jsPDF: {
            unit: 'in',
            format: 'a4',
            orientation: 'portrait',
            compress: true
        },
        pagebreak: {mode: ['avoid-all', 'css', 'legacy']}
    };

    // Use html2pdf
    html2pdf().set(opt).from(reportContainer).save();
}

// Function to prompt for admin password (same logic as email sending)
function promptAdminPassword() {
    // Prompt for admin password using the same logic as email sending
    const password = prompt('הזן סיסמת מנהל להורדת JSON:');
    if (!password) {
        return;
    }

    if (password !== 'admin') {
        showNotification('סיסמה שגויה', 'error');
        return;
    }

    // Download JSON with admin password
    downloadUserJSON(password);
}

// JSON export function - downloads existing user JSON file
async function downloadUserJSON(adminPassword) {
    try {
        // Get user email from the current modal
        const userEmail = getDiagnosisUserEmail();
        if (!userEmail) {
            alert('לא ניתן לזהות את המשתמש');
            return;
        }

        // Convert email to folder name format (remove @ and . and convert to lowercase)
        const folderName = userEmail.replace('@', '').replace('.', '').toLowerCase();

        // Construct the path to the user's JSON file
        const jsonFilePath = `saved_results/${folderName}/${userEmail}_answers.json`;

        // Fetch the JSON file from the server with admin password
        const response = await fetch(`/pdn-admin/download-json?file_path=${encodeURIComponent(jsonFilePath)}&session_token=${sessionToken}&admin_password=${encodeURIComponent(adminPassword)}`);

        if (response.ok) {
            // Get the file content
            const jsonContent = await response.json();

            // Create and download the file
            const jsonString = JSON.stringify(jsonContent, null, 2);
            const blob = new Blob([jsonString], {type: 'application/json;charset=utf-8'});
            const url = URL.createObjectURL(blob);

            const link = document.createElement('a');
            link.href = url;
            link.download = `${userEmail}_answers.json`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            URL.revokeObjectURL(url);

        } else if (response.status === 401) {
            if (response.headers.get('X-Error-Type') === 'invalid_password') {
                alert('סיסמת מנהל שגויה. אנא נסה שוב.');
            } else {
                // Session expired, redirect to login
                localStorage.removeItem('adminSessionToken');
                window.location.href = '/pdn-admin/';
            }
        } else if (response.status === 404) {
            alert('קובץ ה-JSON לא נמצא. יתכן שהמשתמש לא השלים את השאלון.');
        } else {
            throw new Error(`Failed to download JSON: ${response.status}`);
        }

    } catch (error) {
        console.error('Error downloading JSON:', error);
        alert('שגיאה בהורדת קובץ ה-JSON. אנא נסה שוב.');
    }
}

// Helper function to get user metadata from the current data
function getUserMetadata(field) {
    // Try to get from the current user data
    const currentUser = getCurrentUserFromModal();
    if (currentUser && currentUser[field]) {
        return currentUser[field];
    }

    // Try to get from the metadata in the modal content
    const metadataElement = document.querySelector('#questionnaireContent .font-mono.font-bold.text-blue-600.text-lg');
    if (metadataElement && field === 'user_id') {
        return metadataElement.textContent.trim();
    }

    // Try to get from the metadata object in the displayQuestionsWithText function
    const metadataSection = document.querySelector('#questionnaireContent .bg-gradient-to-br.from-blue-50.via-blue-50.to-blue-100');
    if (metadataSection) {
        const userIdElement = metadataSection.querySelector('.font-mono.font-bold.text-blue-600.text-lg');
        if (userIdElement && field === 'user_id') {
            return userIdElement.textContent.trim();
        }
    }

    // Fallback values
    const fallbacks = {
        'user_id': 'לא זמין',
        'email': getDiagnosisUserEmail(),
        'date': 'לא זמין',
        'pdn_code': 'לא זמין',
        'pdn_voice_code': 'לא זמין',
        'diagnose_pdn_code': 'לא זמין',
        'diagnose_comments': 'אין הערות'
    };

    return fallbacks[field] || 'לא זמין';
}

// Helper function to get current user data from the modal
function getCurrentUserFromModal() {
    const userEmail = getDiagnosisUserEmail();
    if (userEmail && currentData) {
        return currentData.find(user => user.email === userEmail);
    }
    return null;
}

let sessionToken = null;
let currentData = [];
let currentEditEmail = null;

// Function to format timestamp
function formatTimestamp(timestamp) {
    if (!timestamp) return 'לא זמין';

    try {
        // Handle different timestamp formats
        let cleanTimestamp = timestamp.replace(/_/g, ' ').trim();

        // If it's already in a readable format, return as is
        if (cleanTimestamp.includes('-') || cleanTimestamp.includes('/')) {
            return cleanTimestamp;
        }

        // Parse timestamp in format "YYYY MM DD HH MM" or "YYYY_MM_DD_HH_MM"
        const parts = cleanTimestamp.split(/[\s_]+/);

        if (parts.length >= 5) {
            const [year, month, day, hour, minute] = parts;

            // Validate parts
            if (year && month && day && hour && minute) {
                // Format as Hebrew date: DD/MM/YYYY HH:MM
                return `${day}/${month}/${year} ${hour}:${minute}`;
            }
        }

        // If parsing fails, return the cleaned timestamp
        return cleanTimestamp;
    } catch (error) {
        console.error('Error formatting timestamp:', error);
        return timestamp.replace(/_/g, ' ');
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', function () {
    // Get session token from localStorage
    sessionToken = localStorage.getItem('adminSessionToken');

    // If no session token, redirect to login
    if (!sessionToken) {
        window.location.href = '/pdn-admin/';
        return;
    }

    setupEventListeners();
    loadMetadata();
    loadConversationStats();
    loadVersion();

    // Add global error handler for 401 responses
    window.addEventListener('unhandledrejection', function (event) {
        if (event.reason && event.reason.status === 401) {
            localStorage.removeItem('adminSessionToken');
            window.location.href = '/pdn-admin/';
        }
    });
});

function setupEventListeners() {
    // Search functionality with debounce
    document.getElementById('searchInput').addEventListener('input', debounce(handleSearch, 300));

    // Red users filter
    document.getElementById('redUsersFilter').addEventListener('change', handleFilter);

    // Refresh button
    document.getElementById('refreshBtn').addEventListener('click', () => {
        loadMetadata();
        loadConversationStats();
    });

    // Logout button
    document.getElementById('logoutBtn').addEventListener('click', handleLogout);

    // Logged in users button
    document.getElementById('loggedInUsersBtn').addEventListener('click', showLoggedInUsers);

    // Edit diagnose form
    document.getElementById('editDiagnoseForm').addEventListener('submit', handleEditDiagnose);

}

async function handleLogout() {
    if (sessionToken) {
        try {
            await fetch(`/pdn-admin/logout?session_token=${sessionToken}`);
        } catch (error) {
            console.error('Logout error:', error);
        }
    }
    sessionToken = null;
    // Clear session token from localStorage
    localStorage.removeItem('adminSessionToken');
    // Redirect to login page
    window.location.replace('/pdn-admin/');
}

async function showLoggedInUsers() {
    try {
        const response = await fetch(`/pdn-admin/logged-in-users?session_token=${sessionToken}`);
        if (!response.ok) {
            throw new Error('Failed to fetch logged-in users');
        }

        const data = await response.json();
        const content = document.getElementById('loggedInUsersContent');

        if (data.count === 0) {
            content.innerHTML = '<p class="text-gray-600 text-center py-4">אין משתמשים מחוברים כרגע</p>';
        } else {
            let html = `<div class="mb-4 text-sm text-gray-600">סה"כ: ${data.count} משתמשים</div>`;
            html += '<div class="space-y-3">';

            data.users.forEach(user => {
                const appName = user.type === 'admin' ? 'מנהל' : user.type === 'diagnosis' ? 'אבחון' : 'צ׳אט';
                const appColor = user.type === 'admin' ? 'bg-blue-100 text-blue-800' : user.type === 'diagnosis' ? 'bg-green-100 text-green-800' : 'bg-purple-100 text-purple-800';
                html += `
                    <div class="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center space-x-3 space-x-reverse">
                                <i class="fas fa-user-circle text-blue-900 text-2xl"></i>
                                <div>
                                    <div class="flex items-center gap-2">
                                        <p class="font-semibold text-gray-800">${user.email}</p>
                                        <span class="px-2 py-1 text-xs font-semibold rounded ${appColor}">${appName}</span>
                                    </div>
                                    <p class="text-sm text-gray-600">התחבר: ${user.login_time}</p>
                                    ${user.expires_at ? `<p class="text-xs text-gray-500">תוקף עד: ${user.expires_at}</p>` : ''}
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            });

            html += '</div>';
            content.innerHTML = html;
        }

        document.getElementById('loggedInUsersModal').style.display = 'flex';
    } catch (error) {
        console.error('Error fetching logged-in users:', error);
        alert('שגיאה בטעינת משתמשים מחוברים');
    }
}

async function loadMetadata() {
    const refreshBtn = document.getElementById('refreshBtn');

    // Check if button is already disabled (prevent multiple calls)
    if (refreshBtn.disabled) {
        return;
    }

    // Disable refresh button
    refreshBtn.disabled = true;

    // Safety timeout to re-enable button after 30 seconds
    const safetyTimeout = setTimeout(() => {
        if (refreshBtn.disabled) {
            refreshBtn.disabled = false;
        }
    }, 30000);

    showLoading();
    try {
        const response = await fetch('/pdn-admin/metadata/csv?session_token=' + sessionToken);
        if (response.ok) {
            const data = await response.json();
            currentData = data.data;

            // Calculate verification status for each user
            currentData.forEach(user => {
                // For existing data, we'll set needs_verification to false by default
                // The actual verification will be calculated when recalculating PDN codes
                user.needs_verification = false;
            });

            // Helper function to parse dates in different formats
            const parseDate = (dateStr) => {
                if (!dateStr || dateStr === 'N/A' || dateStr === '') {
                    return new Date(0); // Return epoch date for invalid dates
                }

                // Try to parse different date formats
                let date = new Date(dateStr);

                // If invalid date, try parsing Hebrew date format (DD/MM/YYYY)
                if (isNaN(date.getTime())) {
                    const parts = dateStr.split('/');
                    if (parts.length === 3) {
                        // Assume DD/MM/YYYY format
                        date = new Date(parts[2], parts[1] - 1, parts[0]);
                    }
                }

                return date;
            };

            // Sort by date (newest first)
            currentData.sort((a, b) => parseDate(b.date) - parseDate(a.date));

            displayData(currentData);
        } else if (response.status === 401) {
            localStorage.removeItem('adminSessionToken');
            window.location.href = '/pdn-admin/';
        } else {
            throw new Error('Failed to load metadata');
        }
    } catch (error) {
        console.error('Error loading metadata:', error);
        alert('שגיאה בטעינת נתונים');
    } finally {
        hideLoading();
        // Clear safety timeout and re-enable refresh button
        clearTimeout(safetyTimeout);
        refreshBtn.disabled = false;
    }
}

async function loadConversationStats() {
    try {
        const response = await fetch(`/pdn-admin/conversation-stats?session_token=${sessionToken}&days=7`);

        if (response.ok) {
            const data = await response.json();
            displayConversationStats(data.stats);
        }
    } catch (error) {
        console.error('Error loading conversation stats:', error);
    }
}

function displayConversationStats(stats) {
    const container = document.getElementById('conversationStats');
    
    const allUsers = new Set();
    const dates = Object.keys(stats).sort().reverse();
    
    dates.forEach(date => {
        Object.keys(stats[date]).forEach(email => allUsers.add(email));
    });
    
    const users = Array.from(allUsers).sort();
    const weeklyTotals = {};
    users.forEach(user => {
        weeklyTotals[user] = dates.reduce((sum, date) => sum + (stats[date][user] || 0), 0);
    });
    
    let html = `
        <div class="bg-white p-6 rounded-xl border border-gray-200 shadow-sm" style="grid-column: 1 / -1; width: 100%;">
            <style>
                .stats-table { 
                    width: 100%;
                    min-width: 1200px;
                    border-collapse: collapse;
                    font-family: 'Inter', sans-serif;
                }
                .stats-table th, .stats-table td { 
                    padding: 12px;
                    text-align: center;
                    border: 1px solid #e5e7eb;
                }
                .stats-table th { 
                    background: linear-gradient(135deg, #e0e7ff 0%, #f1f5f9 100%);
                    font-weight: 600;
                    color: #374151;
                }
                .stats-table tbody tr:hover { 
                    background: #f9fafb;
                }
                .stats-table .total-col { 
                    background: #f3f4f6;
                    font-weight: 600;
                }
                .stats-table .user-col { 
                    text-align: right;
                    font-weight: 500;
                }
                .stats-table .total-row {
                    background: #f3f4f6;
                    font-weight: 600;
                }
            </style>
            
            <div style="overflow-x: auto; width: 100%;">
                <table class="stats-table">
                    <thead>
                        <tr>
                            <th class="user-col">משתמש</th>
                            ${dates.map(date => `<th>${date}</th>`).join('')}
                            <th class="total-col">סה"כ</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${users.map(user => `
                            <tr>
                                <td class="user-col">${user}</td>
                                ${dates.map(date => `<td>${stats[date][user] || 0}</td>`).join('')}
                                <td class="total-col">${weeklyTotals[user]}</td>
                            </tr>
                        `).join('')}
                        <tr class="total-row">
                            <td class="user-col">סה"כ</td>
                            ${dates.map(date => {
                                const dayTotal = Object.values(stats[date]).reduce((sum, count) => sum + count, 0);
                                return `<td>${dayTotal}</td>`;
                            }).join('')}
                            <td class="total-col">${Object.values(weeklyTotals).reduce((sum, count) => sum + count, 0)}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

function displayData(data) {
    renderTable(data);
}

function renderTable(data) {
    const tbody = document.getElementById('tableBody');
    tbody.innerHTML = '';

    // Update row count
    document.getElementById('rowCount').textContent = `סה"כ שורות: ${data.length}`;

    if (data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="11" class="text-center py-12 text-gray-500"><i class="fas fa-inbox text-4xl mb-3 block"></i>לא נמצאו נתונים</td></tr>';
        return;
    }

    data.forEach(user => {
        const row = document.createElement('tr');

        // Highlight row if user needs verification
        const isDifferent = user.needs_verification === true;

        // Add red background class if verification needed
        if (isDifferent) {
            row.classList.add('highlight-difference');
        }

        row.innerHTML = `
        <td class="px-4 py-4">
            <span class="px-2 py-1 bg-gray-100 text-gray-800 rounded-full text-xs font-medium font-mono">${user.user_id || 'N/A'}</span>
        </td>
        <td class="px-4 py-4">
            <div class="relative" x-data="{ open: false, loadingBtn: '', modalText: '', showModal: false }">
                <button @click="open = !open"
                        class="action-btn bg-blue-900 hover:bg-blue-900 text-white px-4 py-2 rounded-lg transition-all duration-300 flex items-center">
                    פעולות
                    <i class="fas fa-chevron-down mr-2 transition-transform" :class="{ 'rotate-180': open }"></i>
                </button>

                <div x-show="open"
                     @click.away="open = false"
                     x-transition:enter="transition ease-out duration-100"
                     x-transition:enter-start="transform opacity-0 scale-95"
                     x-transition:enter-end="transform opacity-100 scale-100"
                     x-transition:leave="transition ease-in duration-75"
                     x-transition:leave-start="transform opacity-100 scale-100"
                     x-transition:leave-end="transform opacity-0 scale-95"
                     class="absolute left-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-blue-200 z-50">

                    <div class="py-1">
                        <button @click="loadingBtn = 'questionnaire'; modalText = 'טוען נתוני שאלון...'; showModal = true; viewQuestionnaire('${user.email}'); open = false"
                                class="w-full text-right px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 flex items-center"
                                :disabled="loadingBtn === 'questionnaire'">
                            <i class="fas fa-clipboard-list ml-2"></i>
                            צפה בשאלון
                        </button>

                        <button @click="loadingBtn = 'voice'; modalText = 'טוען הקלטה קולית...'; showModal = true; playVoice('${user.email}'); open = false"
                                class="w-full text-right px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 flex items-center"
                                :disabled="loadingBtn === 'voice'">
                            <i class="fas fa-microphone ml-2"></i>
                            האזן להקלטה
                        </button>

                        <button @click="loadingBtn = 'edit'; modalText = 'ערוך איבחון...'; showModal = true; editDiagnose('${user.email}'); open = false"
                                class="w-full text-right px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 flex items-center"
                                :disabled="loadingBtn === 'edit'">
                            <i class="fas fa-edit ml-2"></i>
                            ערוך אבחון
                        </button>

                        <div class="relative" x-data="{ emailOpen: false }">
                            <button @click="emailOpen = !emailOpen"
                                    class="w-full text-right px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 flex items-center justify-between"
                                    :disabled="loadingBtn === 'email'">
                                <span class="flex items-center">
                                    <i class="fas fa-envelope ml-2"></i>
                                    שלח אימייל
                                </span>
                                <i class="fas fa-chevron-left text-xs transition-transform" :class="{ 'rotate-90': emailOpen }"></i>
                            </button>
                            <div x-show="emailOpen" class="pr-6 border-r border-blue-200 mr-2">
                                <button @click="loadingBtn = 'email'; modalText = 'שולח אימייל קוד PDN...'; showModal = true; sendEmail('${user.email}', 'pdn'); open = false; emailOpen = false"
                                        class="w-full text-right px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 flex items-center">
                                    <i class="fas fa-file-alt ml-2 text-blue-500"></i>
                                    קוד PDN
                                </button>
                                <button @click="loadingBtn = 'email'; modalText = 'שולח הזמנה לבינת...'; showModal = true; sendEmail('${user.email}', 'binat'); open = false; emailOpen = false"
                                        class="w-full text-right px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 flex items-center">
                                    <i class="fas fa-comments ml-2 text-green-500"></i>
                                    בינת
                                </button>
                            </div>
                        </div>

                        <button @click="loadingBtn = 'recalculate'; modalText = 'מחשב מחדש קוד פדן...'; showModal = true; recalculatePdnCode('${user.email}'); open = false"
                                class="w-full text-right px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 flex items-center"
                                :disabled="loadingBtn === 'recalculate'">
                            <i class="fas fa-calculator ml-2"></i>
                            חשב מחדש קוד פדן
                        </button>
                    </div>
                </div>
            </div>
        </td>
        <td class="px-4 py-4 font-medium text-gray-900">${((user.first_name || '') + ' ' + (user.last_name || '')).trim() || 'N/A'}</td>
        <td class="px-4 py-4 font-medium text-gray-900">${user.email}</td>
        <td class="px-4 py-4 text-gray-700">${user.date}</td>
        <td class="px-4 py-4">
            <span class="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium"> ${user.pdn_code}</span>
        </td>
        <td class="px-4 py-4">
            ${user.needs_verification ?
                '<span class="px-2 py-1 bg-red-100 text-red-800 rounded-full text-xs font-medium" title="נדרש אימות אנושי - הפער בין הציונים קטן מ-2 נקודות">⚠️ אימות</span>' :
                '<span class="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium">✓ תקין</span>'
            }
        </td>
        <td class="px-4 py-4">
            <span class="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">${user.pdn_voice_code || 'N/A'}</span>
        </td>
        <td class="px-4 py-4">
            <span class="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium">${user.diagnose_pdn_code || 'N/A'}</span>
        </td>
        <td class="px-4 py-4 text-gray-700 max-w-xs truncate" title="${user.diagnose_comments || ''}">${user.diagnose_comments || ''}</td>
        <td class="px-4 py-4 text-gray-700 max-w-xs truncate" title="${user.pdn_update_comments || ''}">${user.pdn_update_comments || ''}</td>
    `;
        tbody.appendChild(row);
    });

    // Initialize tooltips after rendering
    initializeTooltips();
}

function initializeTooltips() {
    // Remove any existing tooltip elements
    const existingTooltips = document.querySelectorAll('.custom-tooltip');
    existingTooltips.forEach(tooltip => tooltip.remove());

    // Add event listeners to all tooltip elements
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', showCustomTooltip);
        element.addEventListener('mouseleave', hideCustomTooltip);
    });
}

function showCustomTooltip(event) {
    const element = event.target;
    const tooltipText = element.getAttribute('data-tooltip');

    if (!tooltipText) return;

    // Create tooltip element
    const tooltip = document.createElement('div');
    tooltip.className = 'custom-tooltip';
    tooltip.textContent = tooltipText;
    tooltip.style.cssText = `
    position: absolute;
    background: rgba(0, 0, 0, 0.9);
    color: white;
    padding: 6px 10px;
    border-radius: 6px;
    font-size: 12px;
    white-space: nowrap;
    z-index: 99999;
    pointer-events: none;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    opacity: 0;
    transition: opacity 0.3s ease;
`;

    document.body.appendChild(tooltip);

    // Position tooltip
    const rect = element.getBoundingClientRect();
    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 8 + 'px';

    // Show tooltip
    setTimeout(() => {
        tooltip.style.opacity = '1';
    }, 10);
}

function hideCustomTooltip(event) {
    const tooltips = document.querySelectorAll('.custom-tooltip');
    tooltips.forEach(tooltip => {
        tooltip.style.opacity = '0';
        setTimeout(() => {
            if (tooltip.parentElement) {
                tooltip.remove();
            }
        }, 300);
    });
}

function handleSearch(e) {
    applyFilters();
}

function handleFilter(e) {
    applyFilters();
}

function applyFilters() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const showRedUsersOnly = document.getElementById('redUsersFilter').checked;

    let filteredData = currentData.filter(user => {
        // Search filter - check both email and name
        const fullName = ((user.first_name || '') + ' ' + (user.last_name || '')).trim().toLowerCase();
        const matchesSearch = user.email.toLowerCase().includes(searchTerm) ||
            fullName.includes(searchTerm) ||
            (user.first_name && user.first_name.toLowerCase().includes(searchTerm)) ||
            (user.last_name && user.last_name.toLowerCase().includes(searchTerm));

        // Red users filter - show users that need verification
        const isRedUser = user.needs_verification === true;

        if (showRedUsersOnly) {
            return matchesSearch && isRedUser;
        } else {
            return matchesSearch;
        }
    });

    renderTable(filteredData);
}

async function viewQuestionnaire(email) {
    if (!sessionToken) {
        window.location.href = '/pdn-admin/';
        return;
    }

    try {
        const response = await fetch(`/pdn-admin/user/questionnaire/${email}?session_token=${sessionToken}`);
        if (response.ok) {
            const data = await response.json();
            displayQuestionnaire(data);
            // Reset loading state for this specific row
            resetRowLoadingState(email, 'questionnaire');
        } else if (response.status === 401) {
            // Session expired or invalid, redirect to login
            localStorage.removeItem('adminSessionToken');
            window.location.href = '/pdn-admin/';
        } else {
            throw new Error('Failed to load questionnaire');
        }
    } catch (error) {
        console.error('Error loading questionnaire:', error);
        showNotification('שגיאה בטעינת השאלון', 'error');
        // Reset loading state for this specific row
        resetRowLoadingState(email, 'questionnaire');
    }
}

function displayQuestionnaire(data) {

    const content = document.getElementById('questionnaireContent');

    // Extract metadata and questions
    const metadata = data.metadata || {};
    const questions = {};
    const questionsData = data.questions_data || {};

    // Separate questions from metadata
    Object.keys(data).forEach(key => {
        if (key !== 'metadata' && key !== 'questions_data' && !isNaN(key)) {
            questions[key] = data[key];
        }
    });
    displayQuestionsWithText(questions, metadata, questionsData);
}

function displayQuestionsWithText(questions, metadata, questionsData) {
    const content = document.getElementById('questionnaireContent');

    content.innerHTML = `
    <div class="bg-gradient-to-br from-blue-50 via-blue-50 to-blue-100 p-8 rounded-2xl border border-blue-200 shadow-lg">
        <div class="flex items-center justify-between mb-6">
            <h3 class="text-2xl font-bold text-gray-800">
                פרטי משתמש
            </h3>
            <div class="relative" x-data="{ open: false }">
                <button id="downloadPdfBtn"
                    @click="open = !open"
                    class="flex items-center gap-3 px-6 py-3 bg-gradient-to-r from-blue-900 to-blue-900 text-white font-bold rounded-xl shadow-lg hover:from-blue-900 hover:to-blue-900 transition-all duration-300 text-base transform hover:scale-105">
                    <i class="fas fa-file-arrow-down mr-2 text-lg"></i>
                    הורד דוח
                    <i class="fas fa-chevron-down mr-2 transition-transform" :class="{ 'rotate-180': open }"></i>
                </button>

                <div x-show="open"
                     @click.away="open = false"
                     x-transition:enter="transition ease-out duration-100"
                     x-transition:enter-start="transform opacity-0 scale-95"
                     x-transition:enter-end="transform opacity-100 scale-100"
                     x-transition:leave="transition ease-in duration-75"
                     x-transition:leave-start="transform opacity-100 scale-100"
                     x-transition:leave-end="transform opacity-0 scale-95"
                     class="absolute left-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-blue-200 z-50">

                    <div class="py-1">
                        <button @click="open = false; downloadReport('pdf')"
                                class="w-full text-right px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 flex items-center">
                            <i class="fas fa-file-pdf ml-2 text-red-500"></i>
                            הורד PDF
                        </button>

                        <button @click="open = false; promptAdminPassword()"
                                class="w-full text-right px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 flex items-center">
                            <i class="fas fa-file-code ml-2 text-green-500"></i>
                            הורד JSON
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
            <!-- Personal Information Section -->
    <div class="space-y-4">
    <div class="bg-white p-4 rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
    <div class="text-sm text-gray-500 mb-1">שם פרטי</div>
    <div class="font-bold text-gray-900 text-lg">${metadata["first_name"] || 'לא זמין'}</div>
    </div>
    <div class="bg-white p-4 rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
    <div class="text-sm text-gray-500 mb-1">שם משפחה</div>
    <div class="font-bold text-gray-900 text-lg">${metadata["last_name"] || 'לא זמין'}</div>
    </div>
    <div class="bg-white p-4 rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
    <div class="text-sm text-gray-500 mb-1">אימייל</div>
    <div class="font-bold text-gray-900 text-sm break-all">${metadata["Email"] || 'לא זמין'}</div>
    </div>
    <div class="bg-white p-4 rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
    <div class="text-sm text-gray-500 mb-1">מספר טלפון</div>
    <div class="font-bold text-gray-900 text-lg break-all">${metadata["phone"] || 'לא זמין'}</div>
    </div>
    <div class="bg-white p-4 rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
    <div class="text-sm text-gray-500 mb-1">שם מפנה</div>
    <div class="font-bold text-gray-900 text-lg break-all">${metadata["referral_source"] || 'לא זמין'}</div>
    </div>
    </div>

        <!-- System Information Section -->
    <div class="space-y-4">
    <div class="bg-white p-4 rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
    <div class="text-sm text-gray-500 mb-1">מזהה מערכת</div>
    <div  class="font-bold text-gray-900 text-lg break-all">${metadata["User ID"] || 'לא זמין'}</div>
    </div>
    <div class="bg-white p-4 rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
    <div class="text-sm text-gray-500 mb-1">שנת לידה</div>
    <div class="font-bold text-gray-900 text-lg break-all">${metadata["birth_year"] || 'לא זמין'}</div>
    </div>
    <div class="bg-white p-4 rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
    <div class="text-sm text-gray-500 mb-1">שפת אם</div>
    <div class="font-bold text-gray-900 text-lg break-all">${metadata["mother_language"] || 'לא זמין'}</div>
    </div>
    <div class="bg-white p-4 rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
    <div class="text-sm text-gray-500 mb-1">מגדר</div>
    <div class="font-bold text-gray-900 text-lg break-all">${metadata["gender"] || 'לא זמין'}</div>
    </div>
    </div>

        <!-- Diagnosis Information Section -->
    <div class="space-y-4">
    <div class="bg-white p-4 rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
    <div class="text-sm text-gray-500 mb-1">קוד פדן</div>
    <div >${metadata["Diagnose PDN Code"] || metadata["PDN Code"] || 'לא זמין'}</div>
    </div>
    <div class="bg-white p-4 rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
    <div class="text-sm text-gray-500 mb-1">תאריך אבחון</div>
    <div class="font-bold text-gray-900 text-lg">${metadata["Date"] || 'לא זמין'}</div>
    </div>
    <div class="bg-white p-4 rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
    <div class="text-sm text-gray-500 mb-1">השכלה</div>
    <div class="font-bold text-gray-900 text-lg break-all">${metadata["education"] || 'לא זמין'}</div>
    </div>
    <div class="bg-white p-4 rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
    <div class="text-sm text-gray-500 mb-1">תפקיד</div>
    <div class="font-bold text-gray-900 text-lg break-all">${metadata["job_title"] || 'לא זמין'}</div>
    </div>
    </div>
    </div>
    </div>

    <div class="bg-white p-8 rounded-2xl border border-gray-200 shadow-lg mt-6">
    <h3 class="text-2xl font-bold text-gray-800 mb-6">
    תשובות מאובחן (${Object.keys(questions).length} שאלות)
    </h3>
    <div class="space-y-6">
    ${Object.entries(questions).map(([questionNumber, questionData]) => {
        // Handle different question types
        let answerDisplay = '';
        let codeDisplay = '';
        let questionText = \`שאלה \${questionNumber}\`;

        // Get question text from questions data
        if (questionsData) {
            // Search for question in all phases
            for (const phaseKey in questionsData.phases) {
                const phase = questionsData.phases[phaseKey];
                if (phase.questions && phase.questions[questionNumber]) {
                    questionText = phase.questions[questionNumber].text;
                    break;
                }
            }
        }

        // If question text is not found in questions data, try to get it from the saved answer data
        if (questionText === \`שאלה \${questionNumber}\` && questionData.question_text) {
            questionText = questionData.question_text;
        }

        if (questionData.ranking) {
            // Check if this is a scale question (has exactly 2 options with numeric values)
            const rankingEntries = Object.entries(questionData.ranking);

            if (rankingEntries.length === 2 &&
                typeof rankingEntries[0][1] === 'number' &&
                typeof rankingEntries[1][1] === 'number') {

                // This is a scale question - decode it properly
                const [leftCode, leftValue] = rankingEntries[0];
                const [rightCode, rightValue] = rankingEntries[1];

                // Get the question options to find the text labels
                let leftText = leftCode;
                let rightText = rightCode;

                if (questionData.question_options && questionData.question_options.length >= 2) {
                    const leftOption = questionData.question_options.find(opt => opt.code === leftCode);
                    const rightOption = questionData.question_options.find(opt => opt.code === rightCode);

                    if (leftOption) leftText = leftOption.text;
                    if (rightOption) rightText = rightOption.text;
                }

                // Determine the scale position and create readable description
                const scaleMap = [
                    {position: 0, description: \`\${leftText} (במידה רבה מאוד)\`, leftValue: 12, rightValue: 0},
                    {position: 1, description: \`\${leftText} (במידה רבה)\`, leftValue: 10, rightValue: 2},
                    {position: 2, description: \`\${leftText} (במידה מסוימת)\`, leftValue: 8, rightValue: 4},
                    {position: 3, description: \`באמצע (ניטרלי)\`, leftValue: 6, rightValue: 6},
                    {position: 4, description: \`\${rightText} (במידה מסוימת)\`, leftValue: 4, rightValue: 8},
                    {position: 5, description: \`\${rightText} (במידה רבה)\`, leftValue: 2, rightValue: 10},
                    {position: 6, description: \`\${rightText} (במידה רבה מאוד)\`, leftValue: 0, rightValue: 12}
                ];

                // Find the matching scale position
                const scalePosition = scaleMap.find(pos =>
                    pos.leftValue === leftValue && pos.rightValue === rightValue
                );

                if (scalePosition) {
                    // Create visual scale indicator
                    const filledDots = '●'.repeat(scalePosition.position + 1);
                    const emptyDots = '○'.repeat(6 - scalePosition.position);
                    const scaleIndicator = filledDots + emptyDots;

                    answerDisplay = \`

                                    <div class="space-y-2">
                                        <div class="flex items-center justify-between text-xs text-gray-600">
                                            <span>\${leftText}</span>
                                            <span>\${rightText}</span>
                                        </div>
                                        <div class="flex items-center justify-center">
                                            <span class="text-lg tracking-wider">\${scaleIndicator}</span>
                                        </div>
                                        <div class="text-center text-sm font-medium text-blue-600">
\${scalePosition.description}
                                        </div>
                                    </div>

    \`;
                    codeDisplay = 'סולם העדפה';
                } else {
                    // Fallback if exact match not found
                    answerDisplay = \`

                                    <div class="space-y-2">
                                        <div class="text-sm text-gray-600">
\${leftText}: \${leftValue} | \${rightText}: \${rightValue}
                                        </div>
                                        <div class="text-xs text-gray-500">
                                            (לא ניתן לפענח את המיקום המדויק בסולם)
                                        </div>
                                    </div>

    \`;
                    codeDisplay = 'סולם העדפה';
                }

            } else {
                // This is a regular ranking question - use existing logic
                const sortedRanking = rankingEntries.sort((a, b) => a[1] - b[1]);

                let rankedTexts = [];
                if (questionData.question_options && questionData.question_options.length > 0) {
                    rankedTexts = sortedRanking.map(([code, rank]) => {
                        const option = questionData.question_options.find(opt => opt.code === code);
                        return \`\${rank}. \${option ? option.text : code}\`;
                    });
                } else {
                    rankedTexts = sortedRanking.map(([code, rank]) => \`\${rank}. \${code}\`);
                }

                answerDisplay = rankedTexts.join('<br>');
                codeDisplay = 'דירוג';
            }
        } else if (questionData.selected_option_code) {
            // For questions with selected_option_code - find the actual text
            let selectedText = questionData.selected_option_code; // Default to code if text not found

            // Try to find the selected text from question options
            if (questionData.question_options && questionData.question_options.length > 0) {
                const selectedOption = questionData.question_options.find(option =>
                    option.code === questionData.selected_option_code
                );
                if (selectedOption) {
                    selectedText = selectedOption.text;
                }
            }

            answerDisplay = selectedText;
            codeDisplay = questionText;
        } else if (questionData.answer && questionData.code) {
            // For regular questions with answer and code
            let cleanAnswer = questionData.answer;

            // Clean up the answer to show only the selected option text
            if (questionData.question_options && questionData.question_options.length > 0) {
                // Try to find the selected option by matching the answer text
                const selectedOption = questionData.question_options.find(option =>
                    questionData.answer.includes(option.text)
                );
                if (selectedOption) {
                    cleanAnswer = selectedOption.text;
                }
            }

            // Remove any question text that might be mixed in
            if (cleanAnswer.includes('?')) {
                cleanAnswer = cleanAnswer.split('?').pop()?.trim() || cleanAnswer;
            }

            // For ranking questions, extract only the selected position
            const rankingMatch = cleanAnswer.match(/(\d+)\.\s*([^0-9\n]+)/);
            if (rankingMatch) {
                cleanAnswer = \`\${rankingMatch[1]}. \${rankingMatch[2].trim()}\`;
            }

            answerDisplay = cleanAnswer;
            codeDisplay = questionText;
        } else {
            // Fallback for any other structure
            answerDisplay = 'לא זמין';
            codeDisplay = 'לא זמין';
        }

        return \`

                        <div class="border-b border-gray-200 pb-6 last:border-b-0">
                            <div class="mb-4">
                                <p class="text-gray-800 text-lg leading-relaxed">\${questionNumber}. \${questionText}</p>
                            </div>
                            <div class="bg-gray-50 px-4 py-3 rounded-lg border border-gray-200">
                                <p class="text-gray-600 text-sm mb-1">תשובה:</p>
                                <p class="text-gray-800 text-sm mb-1">\${answerDisplay}</p>
                            </div>
                        </div>

    \`;
    }).join('')}
    </div>
    </div>
    `
    ;

    document.getElementById('questionnaireModal').style.display = 'flex';
}
