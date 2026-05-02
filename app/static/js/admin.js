    // Debounce utility
    function debounce(fn, delay) {
        let timer;
        return function(...args) {
            clearTimeout(timer);
            timer = setTimeout(() => fn.apply(this, args), delay);
        };
    }

    // Shared helpers
    function redirectToLogin() {
        localStorage.removeItem('adminSessionToken');
        window.location.href = '/pdn-admin/';
    }

    // Password modal state
    let _passwordResolve = null;
    let _passwordReject = null;

    function requestAdminPassword(message) {
        return new Promise((resolve, reject) => {
            _passwordResolve = resolve;
            _passwordReject = reject;
            document.getElementById('passwordModalMessage').textContent = message;
            document.getElementById('adminPasswordInput').value = '';
            document.getElementById('adminPasswordModal').style.display = 'flex';
            setTimeout(() => document.getElementById('adminPasswordInput').focus(), 100);
        });
    }

    function submitPasswordModal() {
        const password = document.getElementById('adminPasswordInput').value.trim();
        document.getElementById('adminPasswordModal').style.display = 'none';
        if (_passwordResolve) {
            _passwordResolve(password);
            _passwordResolve = null;
            _passwordReject = null;
        }
    }

    function cancelPasswordModal() {
        document.getElementById('adminPasswordModal').style.display = 'none';
        if (_passwordResolve) {
            _passwordResolve(null);
            _passwordResolve = null;
            _passwordReject = null;
        }
    }

    function parseDate(dateStr) {
        if (!dateStr || dateStr === 'N/A' || dateStr === '') return new Date(0);
        let date = new Date(dateStr);
        if (isNaN(date.getTime())) {
            const parts = dateStr.split('/');
            if (parts.length === 3) {
                date = new Date(parts[2], parts[1] - 1, parts[0]);
            }
        }
        return isNaN(date.getTime()) ? new Date(0) : date;
    }

    function isRedUser(user) {
        return (user.pdn_code !== user.diagnose_pdn_code && user.diagnose_pdn_code !== "N/A" && user.diagnose_pdn_code !== "") ||
            (user.pdn_code !== user.pdn_voice_code && user.pdn_voice_code !== "N/A" && user.pdn_voice_code !== "") ||
            (user.pdn_voice_code !== user.diagnose_pdn_code && user.diagnose_pdn_code !== "N/A" && user.diagnose_pdn_code !== "" && user.pdn_voice_code !== "N/A" && user.pdn_voice_code !== "");
    }

    function getPdnBadgeColor(code) {
        if (!code) return 'bg-gray-100 text-gray-800';
        const prefix = code.charAt(0).toUpperCase();
        switch(prefix) {
            case 'E': return 'bg-blue-100 text-blue-800';
            case 'A': return 'bg-green-100 text-green-800';
            case 'T': return 'bg-amber-100 text-amber-800';
            case 'P': return 'bg-purple-100 text-purple-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    }

    function logError(context, error) {
        // Centralized error logging - can be extended to send to a remote service
        if (typeof error === 'object' && error.message) {
            // Keep minimal error logging for debugging
        }
    }

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
                showNotification('פורמט לא נתמך', 'error');
        }
    }

    // Main PDF export function
    function downloadDiagnosisAsPDF() {
        const content = document.getElementById('questionnaireContent');
        if (!content) {
            showNotification('לא נמצאו נתונים לייצוא', 'error');
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
    async function promptAdminPassword() {
        const password = await requestAdminPassword('הזן סיסמת מנהל להורדת JSON:');
        if (!password) return;
        if (password !== 'admin') {
            showNotification('סיסמה שגויה', 'error');
            return;
        }
        downloadUserJSON(password);
    }

    // JSON export function - downloads existing user JSON file
    async function downloadUserJSON(adminPassword) {
        try {
            // Get user email from the current modal
            const userEmail = getDiagnosisUserEmail();
            if (!userEmail) {
                showNotification('לא ניתן לזהות את המשתמש', 'error');
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
                    showNotification('סיסמת מנהל שגויה', 'error');
                } else {
                    // Session expired, redirect to login
                    redirectToLogin();
                }
            } else if (response.status === 404) {
                showNotification('קובץ ה-JSON לא נמצא', 'error');
            } else {
                throw new Error(`Failed to download JSON: ${response.status}`);
            }

        } catch (error) {
            logError('downloadJSON', error);
            showNotification('שגיאה בהורדת קובץ ה-JSON', 'error');
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
    let avgCostPerCall = 0; // Updated when token usage loads
    let _lastFocusedElement = null;

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
                redirectToLogin();
            }
        });
    });

    function setupEventListeners() {
        // Search functionality with debounce
        document.getElementById('searchInput').addEventListener('input', debounce(handleSearch, 300));

        // Clear search button visibility
        document.getElementById('searchInput').addEventListener('input', function() {
            document.getElementById('clearSearchBtn').style.display = this.value ? 'block' : 'none';
        });

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
                logError('logout', error);
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
            setTimeout(() => { document.getElementById('loggedInUsersModal').querySelector('button, input')?.focus(); }, 100);
        } catch (error) {
            logError('loggedInUsers', error);
            showNotification('שגיאה בטעינת משתמשים מחוברים', 'error');
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

                // Sort by date (newest first)
                currentData.sort((a, b) => parseDate(b.date) - parseDate(a.date));

                displayData(currentData);
            } else if (response.status === 401) {
                redirectToLogin();
            } else {
                throw new Error('Failed to load metadata');
            }
        } catch (error) {
            showNotification('שגיאה בטעינת נתונים', 'error');
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
            logError('loadStats', error);
        }
    }

    async function loadTokenUsage() {
        const container = document.getElementById('tokenUsageContent');
        container.innerHTML = '<p class="text-sm text-gray-500 text-center py-4"><i class="fas fa-spinner fa-spin ml-2"></i> טוען נתוני עלויות...</p>';
        try {
            const response = await fetch(`/pdn-admin/token-usage?session_token=${sessionToken}`);
            if (!response.ok) throw new Error('Failed to load');
            const raw = await response.json();
            const { users: stats, daily_totals, projection, period_days } = raw.stats;
            const userNames = Object.keys(stats);
            if (userNames.length === 0) {
                container.innerHTML = '<p class="text-sm text-gray-500 text-center py-6">אין נתוני שימוש עדיין. נתונים יצטברו לאחר שיחות בבינת.</p>';
                return;
            }
            let tIn=0,tOut=0,tCR=0,tCost=0,tSav=0,tCalls=0;
            userNames.forEach(u=>{const s=stats[u];tIn+=s.input_tokens;tOut+=s.output_tokens;tCR+=s.cache_read_tokens;tCost+=s.total_cost;tSav+=s.cache_savings;tCalls+=s.calls;});
            avgCostPerCall = tCalls > 0 ? tCost / tCalls : 0;
            updateCostEstimate();
            let html=`<div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-5">
                <div class="bg-blue-50 rounded-xl p-4 text-center border border-blue-100"><div class="text-2xl font-bold text-blue-900">${tCalls}</div><div class="text-xs text-gray-600 mt-1">קריאות (${period_days} ימים)</div></div>
                <div class="bg-blue-50 rounded-xl p-4 text-center border border-blue-100"><div class="text-2xl font-bold text-blue-900">${((tIn+tOut)/1000).toFixed(1)}K</div><div class="text-xs text-gray-600 mt-1">סה"כ טוקנים</div></div>
                <div class="bg-green-50 rounded-xl p-4 text-center border border-green-100"><div class="text-2xl font-bold text-green-700">$${tCost.toFixed(3)}</div><div class="text-xs text-gray-600 mt-1">עלות בפועל</div></div>
                <div class="bg-emerald-50 rounded-xl p-4 text-center border border-emerald-100"><div class="text-2xl font-bold text-emerald-700">$${tSav.toFixed(3)}</div><div class="text-xs text-gray-600 mt-1">חיסכון cache</div></div>
                <div class="bg-amber-50 rounded-xl p-4 text-center border border-amber-100"><div class="text-2xl font-bold text-amber-700">$${projection.projected_monthly}</div><div class="text-xs text-gray-600 mt-1">תחזית חודשית</div></div>
                <div class="bg-red-50 rounded-xl p-4 text-center border border-red-100"><div class="text-2xl font-bold text-red-700">$${projection.projected_yearly}</div><div class="text-xs text-gray-600 mt-1">תחזית שנתית</div></div>
            </div>`;
            const days=Object.keys(daily_totals).sort();
            if(days.length>1){const mx=Math.max(...days.map(d=>daily_totals[d].cost),0.001);
            html+=`<div class="mb-5 p-4 bg-gray-50 rounded-xl border border-gray-200"><h4 class="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2"><i class="fas fa-chart-line text-blue-900 text-xs"></i> עלות יומית (${period_days} ימים אחרונים)</h4><div class="flex items-end gap-1" style="height:120px;">`;
            days.forEach(day=>{const d=daily_totals[day];const bh=Math.max(4,(d.cost/mx)*100);
            html+=`<div class="flex-1 flex flex-col items-center justify-end h-full group relative"><div class="absolute -top-6 bg-gray-800 text-white text-[10px] px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">$${d.cost.toFixed(4)} | ${d.calls} קריאות</div><div class="w-full bg-blue-600 rounded-t transition-all hover:bg-blue-500" style="height:${bh}%;min-height:4px;"></div><div class="text-[9px] text-gray-500 mt-1 transform -rotate-45 origin-top-right">${day.slice(5)}</div></div>`;});
            html+=`</div><div class="flex justify-between mt-2 text-[10px] text-gray-400"><span>ממוצע יומי: $${projection.avg_daily_cost.toFixed(4)}</span><span>${projection.active_days} ימים פעילים</span></div></div>`;}
            html+=`<div class="overflow-x-auto rounded-lg border border-gray-200"><table class="w-full text-sm"><thead><tr class="bg-gray-50 border-b border-gray-200"><th class="px-4 py-3 text-right font-semibold text-gray-700">משתמש</th><th class="px-4 py-3 text-center font-semibold text-gray-700">קריאות</th><th class="px-4 py-3 text-center font-semibold text-gray-700">קלט</th><th class="px-4 py-3 text-center font-semibold text-gray-700">פלט</th><th class="px-4 py-3 text-center font-semibold text-gray-700">Cache Read</th><th class="px-4 py-3 text-center font-semibold text-gray-700">עלות</th><th class="px-4 py-3 text-center font-semibold text-gray-700">חיסכון</th></tr></thead><tbody>`;
            userNames.sort((a,b)=>stats[b].total_cost-stats[a].total_cost);
            userNames.forEach(user=>{const s=stats[user];
            html+=`<tr class="border-b border-gray-100 hover:bg-gray-50"><td class="px-4 py-3 font-medium text-gray-900">${user}</td><td class="px-4 py-3 text-center text-gray-700">${s.calls}</td><td class="px-4 py-3 text-center text-gray-700">${(s.input_tokens/1000).toFixed(1)}K</td><td class="px-4 py-3 text-center text-gray-700">${(s.output_tokens/1000).toFixed(1)}K</td><td class="px-4 py-3 text-center">${s.cache_read_tokens>0?`<span class="text-green-700 font-medium">${(s.cache_read_tokens/1000).toFixed(1)}K</span>`:'<span class="text-gray-400">\u2014</span>'}</td><td class="px-4 py-3 text-center font-semibold text-blue-900">$${s.total_cost.toFixed(4)}</td><td class="px-4 py-3 text-center">${s.cache_savings>0?`<span class="text-emerald-700 font-medium">$${s.cache_savings.toFixed(4)}</span>`:'<span class="text-gray-400">\u2014</span>'}</td></tr>`;});
            html+=`<tr class="bg-gray-50 font-semibold border-t-2 border-gray-300"><td class="px-4 py-3 text-gray-900">סה"כ</td><td class="px-4 py-3 text-center text-gray-900">${tCalls}</td><td class="px-4 py-3 text-center text-gray-900">${(tIn/1000).toFixed(1)}K</td><td class="px-4 py-3 text-center text-gray-900">${(tOut/1000).toFixed(1)}K</td><td class="px-4 py-3 text-center text-green-700">${(tCR/1000).toFixed(1)}K</td><td class="px-4 py-3 text-center text-blue-900">$${tCost.toFixed(4)}</td><td class="px-4 py-3 text-center text-emerald-700">$${tSav.toFixed(4)}</td></tr></tbody></table></div>`;
            html+=`<p class="text-xs text-gray-400 mt-3 text-center">* נתונים נשמרים לקובץ. תמחור לפי Claude Sonnet 4. תחזית מבוססת על ממוצע יומי.</p>`;
            container.innerHTML=html;
        } catch(error){logError('loadTokenUsage',error);container.innerHTML='<p class="text-sm text-red-500 text-center py-4">שגיאה בטעינת נתוני עלויות</p>';}
    }

    function updateCostEstimate() {
        updateEstimateFromCalls();
    }

    function updateEstimateFromCalls() {
        const callsInput = document.getElementById('estimateCalls');
        const costInput = document.getElementById('estimateCost');
        const monthlyEl = document.getElementById('estimateMonthly');
        if (!callsInput || !costInput) return;

        const calls = parseInt(callsInput.value) || 0;
        if (avgCostPerCall <= 0) {
            costInput.value = '';
            costInput.placeholder = 'טען נתונים';
            monthlyEl.textContent = '—';
            return;
        }

        const estimated = calls * avgCostPerCall;
        costInput.value = estimated.toFixed(4);
        monthlyEl.textContent = `$${(estimated * 30).toFixed(2)}`;
    }

    function updateEstimateFromCost() {
        const callsInput = document.getElementById('estimateCalls');
        const costInput = document.getElementById('estimateCost');
        const monthlyEl = document.getElementById('estimateMonthly');
        if (!callsInput || !costInput) return;

        const cost = parseFloat(costInput.value) || 0;
        if (avgCostPerCall <= 0) {
            callsInput.value = '';
            monthlyEl.textContent = '—';
            return;
        }

        const calls = Math.round(cost / avgCostPerCall);
        callsInput.value = calls;
        monthlyEl.textContent = `$${(cost * 30).toFixed(2)}`;
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
        updateDashboardSummary();
    }

    function updateDashboardSummary() {
        const total = currentData.length;
        const today = new Date().toLocaleDateString('he-IL', {day: '2-digit', month: '2-digit', year: 'numeric'});
        const todayAlt = new Date().toLocaleDateString('en-GB', {day: '2-digit', month: '2-digit', year: 'numeric'});
        const diagnosedToday = currentData.filter(u => u.date === today || u.date === todayAlt).length;
        const anomalies = currentData.filter(u => isRedUser(u)).length;

        document.getElementById('summaryTotal').textContent = total;
        document.getElementById('summaryToday').textContent = diagnosedToday;
        document.getElementById('summaryAnomalies').textContent = anomalies;

        // Fetch active users count
        fetch(`/pdn-admin/logged-in-users?session_token=${sessionToken}`)
            .then(r => r.ok ? r.json() : {count: 0})
            .then(data => { document.getElementById('summaryActive').textContent = data.count || 0; })
            .catch(() => { document.getElementById('summaryActive').textContent = '—'; });
    }

    function renderTable(data) {
        const tbody = document.getElementById('tableBody');
        tbody.innerHTML = '';

        // Update row count
        document.getElementById('rowCount').textContent = `סה"כ שורות: ${data.length}`;

        if (data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="11" class="text-center py-12 text-gray-500">
                <i class="fas fa-inbox text-4xl mb-3 block"></i>
                <p class="text-lg">לא נמצאו נתונים</p>
            </td></tr>`;
            return;
        }

        data.forEach(user => {
            const row = document.createElement('tr');

            // Add red background class if codes are different
            if (isRedUser(user)) {
                row.classList.add('highlight-difference');
            }

            row.innerHTML = `
            <td class="px-4 py-4">
                <span class="px-2 py-1 bg-gray-100 text-gray-800 rounded-full text-xs font-medium font-mono">${user.user_id || 'N/A'}</span>
            </td>
            <td class="px-4 py-4">
                <div class="relative" x-data="{ open: false, loadingBtn: '', modalText: '', showModal: false }">
                    <button @click.stop="open = !open"
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
                            <button @click="viewJourney('${user.email}'); open = false"
                                    class="w-full text-right px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 flex items-center">
                                <i class="fas fa-route ml-2"></i>
                                מסע משתמש
                            </button>

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
            <td class="px-4 py-4 font-medium text-gray-900">
                <span class="cursor-pointer hover:text-blue-700 transition-colors" onclick="navigator.clipboard.writeText('${user.email}').then(() => showNotification('אימייל הועתק', 'success'))" title="לחץ להעתקה">
                    ${user.email} <i class="fas fa-copy text-gray-300 text-xs mr-1"></i>
                </span>
            </td>
            <td class="px-4 py-4 text-gray-700">${user.date}</td>
            <td class="px-4 py-4">
                <span class="px-2 py-1 rounded-full text-xs font-medium ${getPdnBadgeColor(user.pdn_code)}">${user.pdn_code}</span>
            </td>
            <td class="px-4 py-4">
                ${user.confidence_score !== undefined && user.confidence_score !== null ?
                    `<div class="flex items-center gap-2">
                        <div class="w-12 bg-gray-200 rounded-full h-2 overflow-hidden">
                            <div class="h-2 rounded-full ${user.confidence_score >= 80 ? 'bg-green-500' : user.confidence_score >= 60 ? 'bg-yellow-500' : 'bg-red-500'}" style="width: ${user.confidence_score}%"></div>
                        </div>
                        <span class="text-xs font-mono ${user.confidence_score >= 80 ? 'text-green-700' : user.confidence_score >= 60 ? 'text-yellow-700' : 'text-red-700'}">${user.confidence_score}%</span>
                    </div>` :
                    (user.needs_verification ?
                        '<span class="px-2 py-1 bg-red-100 text-red-800 rounded-full text-xs font-medium" title="נדרש אימות אנושי">⚠️ אימות</span>' :
                        '<span class="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium">✓ תקין</span>')
                }
            </td>
            <td class="px-4 py-4">
                <span class="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">${user.pdn_voice_code || 'N/A'}</span>
            </td>
            <td class="px-4 py-4">
                <span class="px-2 py-1 rounded-full text-xs font-medium ${getPdnBadgeColor(user.diagnose_pdn_code)}">${user.diagnose_pdn_code || 'N/A'}</span>
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
                (user.last_name && user.last_name.toLowerCase().includes(searchTerm)) ||
                (user.pdn_code && user.pdn_code.toLowerCase().includes(searchTerm)) ||
                (user.diagnose_pdn_code && user.diagnose_pdn_code.toLowerCase().includes(searchTerm));

            // Red users filter
            if (showRedUsersOnly) {
                return matchesSearch && isRedUser(user);
            } else {
                return matchesSearch;
            }
        });

        renderTable(filteredData);

        // Show search results count when filtering
        const searchActive = searchTerm || showRedUsersOnly;
        document.getElementById('rowCount').textContent = searchActive
            ? `נמצאו ${filteredData.length} מתוך ${currentData.length}`
            : `סה"כ שורות: ${currentData.length}`;

        // Update search result count and clear button visibility
        const searchInput = document.getElementById('searchInput');
        const clearBtn = document.getElementById('clearSearchBtn');
        const countEl = document.getElementById('searchResultCount');
        if (searchTerm) {
            clearBtn.classList.remove('hidden');
            countEl.classList.remove('hidden');
            countEl.textContent = `נמצאו ${filteredData.length} תוצאות`;
        } else {
            clearBtn.classList.add('hidden');
            countEl.classList.add('hidden');
        }
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
                redirectToLogin();
            } else {
                throw new Error('Failed to load questionnaire');
            }
        } catch (error) {
            logError('loadQuestionnaire', error);
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

    function renderQuestion(questionNumber, questionData, questionsData) {
        let answerDisplay = '';
        let questionText = `שאלה ${questionNumber}`;

        // Get question text from questions data
        if (questionsData) {
            for (const phaseKey in questionsData.phases) {
                const phase = questionsData.phases[phaseKey];
                if (phase.questions && phase.questions[questionNumber]) {
                    questionText = phase.questions[questionNumber].text;
                    break;
                }
            }
        }

        if (questionText === `שאלה ${questionNumber}` && questionData.question_text) {
            questionText = questionData.question_text;
        }

        if (questionData.ranking) {
            answerDisplay = renderRankingAnswer(questionData);
        } else if (questionData.selected_option_code) {
            answerDisplay = renderSelectedAnswer(questionData);
        } else if (questionData.answer && questionData.code) {
            answerDisplay = renderCodeAnswer(questionData);
        } else {
            answerDisplay = 'לא זמין';
        }

        return `<div class="border-b border-gray-200 pb-6 last:border-b-0">
            <div class="mb-4">
                <p class="text-gray-800 text-lg leading-relaxed">${questionNumber}. ${questionText}</p>
            </div>
            <div class="bg-gray-50 px-4 py-3 rounded-lg border border-gray-200">
                <p class="text-gray-600 text-sm mb-1">תשובה:</p>
                <p class="text-gray-800 text-sm mb-1">${answerDisplay}</p>
            </div>
        </div>`;
    }

    function renderRankingAnswer(questionData) {
        const rankingEntries = Object.entries(questionData.ranking);

        if (rankingEntries.length === 2 && typeof rankingEntries[0][1] === 'number' && typeof rankingEntries[1][1] === 'number') {
            return renderScaleAnswer(rankingEntries, questionData);
        }

        // Regular ranking
        const sortedRanking = rankingEntries.sort((a, b) => a[1] - b[1]);
        let rankedTexts = [];
        if (questionData.question_options && questionData.question_options.length > 0) {
            rankedTexts = sortedRanking.map(([code, rank]) => {
                const option = questionData.question_options.find(opt => opt.code === code);
                return `${rank}. ${option ? option.text : code}`;
            });
        } else {
            rankedTexts = sortedRanking.map(([code, rank]) => `${rank}. ${code}`);
        }
        return rankedTexts.join('<br>');
    }

    function renderScaleAnswer(rankingEntries, questionData) {
        const [leftCode, leftValue] = rankingEntries[0];
        const [rightCode, rightValue] = rankingEntries[1];
        let leftText = leftCode, rightText = rightCode;

        if (questionData.question_options && questionData.question_options.length >= 2) {
            const leftOption = questionData.question_options.find(opt => opt.code === leftCode);
            const rightOption = questionData.question_options.find(opt => opt.code === rightCode);
            if (leftOption) leftText = leftOption.text;
            if (rightOption) rightText = rightOption.text;
        }

        const scaleMap = [
            {position: 0, description: `${leftText} (במידה רבה מאוד)`, leftValue: 12, rightValue: 0},
            {position: 1, description: `${leftText} (במידה רבה)`, leftValue: 10, rightValue: 2},
            {position: 2, description: `${leftText} (במידה מסוימת)`, leftValue: 8, rightValue: 4},
            {position: 3, description: `באמצע (ניטרלי)`, leftValue: 6, rightValue: 6},
            {position: 4, description: `${rightText} (במידה מסוימת)`, leftValue: 4, rightValue: 8},
            {position: 5, description: `${rightText} (במידה רבה)`, leftValue: 2, rightValue: 10},
            {position: 6, description: `${rightText} (במידה רבה מאוד)`, leftValue: 0, rightValue: 12}
        ];

        const scalePosition = scaleMap.find(pos => pos.leftValue === leftValue && pos.rightValue === rightValue);

        if (scalePosition) {
            const filledDots = '●'.repeat(scalePosition.position + 1);
            const emptyDots = '○'.repeat(6 - scalePosition.position);
            return `<div class="space-y-2">
                <div class="flex items-center justify-between text-xs text-gray-600"><span>${leftText}</span><span>${rightText}</span></div>
                <div class="flex items-center justify-center"><span class="text-lg tracking-wider">${filledDots}${emptyDots}</span></div>
                <div class="text-center text-sm font-medium text-blue-600">${scalePosition.description}</div>
            </div>`;
        }

        return `<div class="space-y-2">
            <div class="text-sm text-gray-600">${leftText}: ${leftValue} | ${rightText}: ${rightValue}</div>
            <div class="text-xs text-gray-500">(לא ניתן לפענח את המיקום המדויק בסולם)</div>
        </div>`;
    }

    function renderSelectedAnswer(questionData) {
        let selectedText = questionData.selected_option_code;
        if (questionData.question_options && questionData.question_options.length > 0) {
            const selectedOption = questionData.question_options.find(option => option.code === questionData.selected_option_code);
            if (selectedOption) selectedText = selectedOption.text;
        }
        return selectedText;
    }

    function renderCodeAnswer(questionData) {
        let cleanAnswer = questionData.answer;
        if (questionData.question_options && questionData.question_options.length > 0) {
            const selectedOption = questionData.question_options.find(option => questionData.answer.includes(option.text));
            if (selectedOption) cleanAnswer = selectedOption.text;
        }
        if (cleanAnswer.includes('?')) {
            cleanAnswer = cleanAnswer.split('?').pop()?.trim() || cleanAnswer;
        }
        const rankingMatch = cleanAnswer.match(/(\d+)\.\s*([^0-9\n]+)/);
        if (rankingMatch) cleanAnswer = `${rankingMatch[1]}. ${rankingMatch[2].trim()}`;
        return cleanAnswer;
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
        ${Object.entries(questions).map(([qNum, qData]) => renderQuestion(qNum, qData, questionsData)).join('')}
        </div>
        </div>
        `
        ;

        document.getElementById('questionnaireModal').style.display = 'flex';
        setTimeout(() => { document.getElementById('questionnaireModal').querySelector('button, input')?.focus(); }, 100);
    }

        async function playVoice(email) {
            if (!sessionToken) {
                window.location.href = '/pdn-admin/';
                return;
            }

            try {

                const response = await fetch(
                    `/pdn-admin/user/voice/${email}?session_token=${sessionToken}`
                );

                if (response.ok) {
                    const data = await response.json();
                    displayVoice(data);
                    // Reset loading state for this specific row
                    resetRowLoadingState(email, 'voice');
                } else if (response.status === 401) {
                    // Session expired or invalid, redirect to login
                    redirectToLogin();
                } else {
                    const errorText = await response.text();
                    throw new Error(
                        `Failed to load voice: ${response.status} ${errorText}`
                    );
                }
            } catch (error) {
                logError('loadVoice', error);
                showNotification('שגיאה בטעינת ההקלטה', 'error');
                // Reset loading state for this specific row
                resetRowLoadingState(email, 'voice');
            }
        }

        function displayVoice(data) {
            const content = document.getElementById('voiceContent');

            // Check if we have the required data
            if (!data || !data.voice_recordings || Object.keys(data.voice_recordings).length === 0) {
                content.innerHTML =
                    `
        <div class="bg-red-50 p-6 rounded-xl border border-red-200">
        <h3 class="text-lg font-semibold mb-4 text-red-800 flex items-center">
        <i class="fas fa-exclamation-triangle mr-2"></i>שגיאה
        </h3>
        <p class="text-red-700">לא נמצא קובץ הקלטה למשתמש זה</p>
        </div>
        `
                ;
                document.getElementById('voiceModal').style.display = 'flex';
                setTimeout(() => { document.getElementById('voiceModal').querySelector('button, input')?.focus(); }, 100);
                return;
            }

            // Build HTML for multiple recordings
            let recordingsHtml = '';
            const recordings = data.voice_recordings;

            // Helper function to create audio URL
            function createAudioUrl(filePath) {
                // Extract just the relative path from the full file path
                let processedPath = filePath;

                // Remove 'saved_results/' prefix if it exists
                if (processedPath.startsWith('saved_results/')) {
                    processedPath = processedPath.substring('saved_results/'.length);
                }

                // Remove '/pdn/saved_results/' prefix if it exists
                if (processedPath.startsWith('/pdn/saved_results/')) {
                    processedPath = processedPath.substring('/pdn/saved_results/'.length);
                }

                // Remove 'pdn/saved_results/' prefix if it exists
                if (processedPath.startsWith('pdn/saved_results/')) {
                    processedPath = processedPath.substring('pdn/saved_results/'.length);
                }

                return `/pdn-admin/audio/${encodeURIComponent(processedPath)}?session_token=${sessionToken}`;
            }

            // Add question1 recording if exists
            if (recordings.question1) {
                const audioUrl = createAudioUrl(recordings.question1.path);
                recordingsHtml +=
                    `
        <div class="bg-white p-6 rounded-xl border border-gray-200 mb-4">
        <h4 class="text-lg font-semibold mb-4 text-gray-800 flex items-center">
        <i class="fas fa-microphone mr-2 text-blue-600"></i>שאלה 1 - חוויה חיובית
        </h4>
        <audio controls class="w-full" preload="metadata">
        <source src="${audioUrl}" type="audio/wav">
        <source src="${audioUrl}" type="audio/mp3">
        <source src="${audioUrl}" type="audio/mpeg">
        הדפדפן שלך לא תומך בנגינת אודיו.
        </audio>
        </div>
        `;
            }

            // Add question2 recording if exists
            if (recordings.question2) {
                const audioUrl = createAudioUrl(recordings.question2.path);
                recordingsHtml += `

                <div class="bg-white p-6 rounded-xl border border-gray-200 mb-4">
                    <h4 class="text-lg font-semibold mb-4 text-gray-800 flex items-center">
                        <i class="fas fa-microphone mr-2 text-blue-600"></i>שאלה 2 - אתגר משמעותי
                    </h4>
                    <audio controls class="w-full" preload="metadata">
                        <source src="${audioUrl}" type="audio/wav">
                        <source src="${audioUrl}" type="audio/mp3">
                        <source src="${audioUrl}" type="audio/mpeg">
                        הדפדפן שלך לא תומך בנגינת אודיו.
                    </audio>
                </div>

        `;
            }

            // Add legacy recording if exists
            if (recordings.legacy) {
                const audioUrl = createAudioUrl(recordings.legacy.path);
                recordingsHtml += `

                <div class="bg-white p-6 rounded-xl border border-gray-200 mb-4">
                    <h4 class="text-lg font-semibold mb-4 text-gray-800 flex items-center">
                        <i class="fas fa-microphone ml-2 text-blue-900"></i> הקלטה קולית
                    </h4>
                    <audio controls class="w-full" preload="metadata">
                        <source src="${audioUrl}" type="audio/wav">
                        <source src="${audioUrl}" type="audio/mp3">
                        <source src="${audioUrl}" type="audio/mpeg">
                        הדפדפן שלך לא תומך בנגינת אודיו.
                    </audio>
                </div>

        `;
            }

            content.innerHTML = `
        <div class="bg-gradient-to-r from-blue-100 to-blue-100 p-6 rounded-xl border border-blue-200 mb-6">
        <h3 class="text-lg font-semibold mb-4 text-gray-800 flex items-center">
        <i class="fas fa-info-circle ml-2 text-blue-900"></i> פרטי הקלטה
        </h3>
        <div class="grid grid-cols-2 gap-4">
        <div><strong>אימייל:</strong> ${data.email || 'לא זמין'}</div>
        <div><strong>מספר הקלטות:</strong> <span class="px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm">${Object.keys(recordings).length}</span></div>
        </div>
        </div>
        ${recordingsHtml}
        `;

            document.getElementById('voiceModal').style.display = 'flex';
            setTimeout(() => { document.getElementById('voiceModal').querySelector('button, input')?.focus(); }, 100);

            // Add event listeners to all audio elements for debugging
            const audioElements = content.querySelectorAll('audio');
            audioElements.forEach((audioElement, index) => {
                audioElement.addEventListener('error', (e) => {
                    logError('audioPlayback', e);
                });
            });
        }

        function editDiagnose(email) {
            currentEditEmail = email;
            const user = currentData.find(u => u.email === email);

            if (user) {
                document.getElementById('diagnosePdnCode').value = user.diagnose_pdn_code;
                document.getElementById('diagnoseComments').value = user.diagnose_comments;
                document.getElementById('editDiagnoseModal').style.display = 'flex';
                setTimeout(() => { document.getElementById('diagnosePdnCode').focus(); }, 100);
                // Reset loading state for this specific row
                resetRowLoadingState(email, 'edit');
            }
        }

        async function handleEditDiagnose(e) {
            e.preventDefault();
            if (!sessionToken || !currentEditEmail) {
                if (!sessionToken) {
                    window.location.href = '/pdn-admin/';
                }
                return;
            }

            const pdnCode = document.getElementById('diagnosePdnCode').value.trim();
            const comments = document.getElementById('diagnoseComments').value.trim();

            // Check if both fields are empty
            if (!pdnCode && !comments) {
                showNotification('אנא מלא לפחות אחד מהשדות', 'warning');
                return;
            }

            showLoading();
            try {
                const formData = {
                    diagnose_pdn_code: pdnCode,
                    diagnose_comments: comments
                };

                const response = await fetch(`/pdn-admin/user/diagnose/${currentEditEmail}?session_token=${sessionToken}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(formData)
                });

                if (response.ok) {
                    const data = await response.json();
                    // Update local data
                    const userIndex = currentData.findIndex(u => u.email === currentEditEmail);
                    if (userIndex !== -1) {
                        currentData[userIndex] = data.user;
                        renderTable(currentData);
                    }
                    closeModal('editDiagnoseModal');
                } else if (response.status === 401) {
                    // Session expired or invalid, redirect to login
                    redirectToLogin();
                } else {
                    throw new Error('Failed to update diagnose');
                }
            } catch (error) {
                logError('updateDiagnose', error);
                showNotification('שגיאה בעדכון האבחון', 'error');
            } finally {
                hideLoading();
            }
        }

        async function sendEmail(email, emailType = 'pdn') {
            if (!sessionToken) {
                window.location.href = '/pdn-admin/';
                return;
            }

            // Find user data
            const user = currentData.find(u => u.email === email);
            if (!user) {
                showNotification('משתמש לא נמצא', 'error');
                resetRowLoadingState(email, 'email');
                return;
            }

            // Only check code match for PDN emails, not Binat invites
            if (emailType === 'pdn') {
                const codesMatch = user.pdn_code === user.diagnose_pdn_code &&
                    user.diagnose_pdn_code !== "N/A" &&
                    user.diagnose_pdn_code !== "";

                if (!codesMatch) {
                    showNotification('לא ניתן לשלוח אימייל - קוד פדן אינו תואם לקוד המאבחן', 'error');
                    resetRowLoadingState(email, 'email');
                    return;
                }
            }

            // Prompt for admin password
            const passwordPrompt = emailType === 'binat' ? 'הזן סיסמת מנהל לשליחת הזמנה לבינת:' : 'הזן סיסמת מנהל לשליחת אימייל:';
            const password = await requestAdminPassword(passwordPrompt);
            if (!password) {
                resetRowLoadingState(email, 'email');
                return;
            }

            if (password !== 'admin') {
                showNotification('סיסמה שגויה', 'error');
                resetRowLoadingState(email, 'email');
                return;
            }

            try {
                const endpoint = emailType === 'binat'
                    ? `/pdn-admin/user/send_binat_invite/${email}?session_token=${sessionToken}`
                    : `/pdn-admin/user/send_email/${email}?session_token=${sessionToken}`;

                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({password: password})
                });

                if (response.ok) {
                    const data = await response.json();

                    // Show appropriate notification based on verification status
                    if (data.needs_verification) {
                        showNotification(`אימייל נשלח ל-${email} - ⚠️ נדרש אימות אנושי (הפער בין הציונים קטן מ-2 נקודות)`, 'warning');
                    } else {
                        showNotification(`אימייל נשלח בהצלחה ל-${email}`, 'success');
                    }

                    // Update local data with verification status
                    const userIndex = currentData.findIndex(u => u.email === email);
                    if (userIndex !== -1) {
                        currentData[userIndex].needs_verification = data.needs_verification || false;
                        renderTable(currentData);
                    }

                    // Reset loading state for this specific row
                    resetRowLoadingState(email, 'email');
                } else if (response.status === 401) {
                    // Session expired or invalid, redirect to login
                    redirectToLogin();
                } else {
                    let errorMessage = 'Failed to send email';
                    try {
                        const errorData = await response.json();
                        errorMessage = errorData.detail || errorData.error || errorMessage;
                    } catch (parseError) {
                        // If response is not JSON (e.g., HTML error page), use status text
                        errorMessage = `HTTP ${response.status}: ${response.statusText}`;
                    }
                    throw new Error(errorMessage);
                }
            } catch (error) {
                logError('sendEmail', error);
                showNotification(`
    שגיאה בשליחת האימייל: ${error.message}
        `, 'error');
                // Reset loading state for this specific row
                resetRowLoadingState(email, 'email');
            }
        }

        async function recalculatePdnCode(email) {
            if (!sessionToken) {
                window.location.href = '/pdn-admin/';
                return;
            }

            // Find user data
            const user = currentData.find(u => u.email === email);
            if (!user) {
                showNotification('משתמש לא נמצא', 'error');
                resetRowLoadingState(email, 'recalculate');
                return;
            }

            // Prompt for admin password
            const password = await requestAdminPassword('הזן סיסמת מנהל לחישוב מחדש של קוד פדן:');
            if (!password) {
                resetRowLoadingState(email, 'recalculate');
                return;
            }

            if (password !== 'admin') {
                showNotification('סיסמה שגויה', 'error');
                resetRowLoadingState(email, 'recalculate');
                return;
            }

            try {
                const response = await fetch(`/pdn-admin/user/recalculate_pdn/${email}?session_token=${sessionToken}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({password: password})
                });

                if (response.ok) {
                    const data = await response.json();

                    // Show appropriate notification based on verification status
                    if (data.needs_verification) {
                        showNotification(`קוד פדן חושב מחדש: ${data.pdn_code} - ⚠️ נדרש אימות אנושי (הפער בין הציונים קטן מ-2 נקודות)`, 'warning');
                    } else {
                        showNotification(`קוד פדן חושב מחדש בהצלחה: ${data.pdn_code} על ידי ${data.updated_by}`, 'success');
                    }

                    // Display calculation details in modal if available
                    if (data.calculation_details) {
                        showCalculationDetails(email, data);
                    }

                    // Update local data
                    const userIndex = currentData.findIndex(u => u.email === email);
                    if (userIndex !== -1) {
                        currentData[userIndex].pdn_code = data.pdn_code;
                        currentData[userIndex].date = data.date;
                        currentData[userIndex].needs_verification = data.needs_verification || false;
                        if (data.confidence_score !== undefined) {
                            currentData[userIndex].confidence_score = data.confidence_score;
                        }
                        // Update the PDN update comments if available
                        if (data.pdn_update_comments) {
                            currentData[userIndex].pdn_update_comments = data.pdn_update_comments;
                        }
                        renderTable(currentData);
                    }

                    // Reset loading state for this specific row
                    resetRowLoadingState(email, 'recalculate');
                } else if (response.status === 401) {
                    // Session expired or invalid, redirect to login
                    redirectToLogin();
                } else {
                    let errorMessage = 'Failed to recalculate PDN code';
                    try {
                        const errorData = await response.json();
                        errorMessage = errorData.detail || errorData.error || errorMessage;
                    } catch (parseError) {
                        // If response is not JSON (e.g., HTML error page), use status text
                        errorMessage = `HTTP ${response.status}: ${response.statusText}`;
                    }
                    throw new Error(errorMessage);
                }
            } catch (error) {
                logError('recalculatePdn', error);
                showNotification(`שגיאה בחישוב מחדש של קוד פדן: ${error.message}`, 'error');
                // Reset loading state for this specific row
                resetRowLoadingState(email, 'recalculate');
            }
        }

        let appVersionData = null;

        async function loadVersion() {
            try {
                const response = await fetch('/pdn-admin/version');
                if (response.ok) {
                    appVersionData = await response.json();
                    document.getElementById('versionText').textContent = `v${appVersionData.version}`;
                }
            } catch (error) {
                logError('loadVersion', error);
                document.getElementById('versionText').textContent = 'N/A';
            }
        }

        function showReleaseNotes() {
            if (!appVersionData) return;

            const container = document.getElementById('releaseNotesContent');
            const notesHtml = appVersionData.release_notes.map(note =>
                `<div class="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                    <span class="text-green-500 mt-0.5"><i class="fas fa-check-circle"></i></span>
                    <span class="text-gray-800 text-sm">${note}</span>
                </div>`
            ).join('');

            container.innerHTML = `
                <div class="p-4 bg-blue-50 rounded-lg border border-blue-200 text-center mb-4">
                    <div class="text-2xl font-bold text-blue-900 mb-1">v${appVersionData.version}</div>
                    <div class="text-sm text-gray-600">${appVersionData.release_date}</div>
                </div>
                <div class="space-y-2">
                    ${notesHtml}
                </div>
            `;

            document.getElementById('releaseNotesModal').style.display = 'flex';
            setTimeout(() => { document.getElementById('releaseNotesModal').querySelector('button, input')?.focus(); }, 100);
        }

        function showCalculationDetails(email, data) {
            const container = document.getElementById('pdnCalculationContent');
            const stages = data.calculation_details;
            const traitLabels = { A: 'הישגיות (Achievement)', T: 'ביטחון (Trust)', P: 'הנאה (Pleasure)', E: 'אדנות (Empower)' };
            const traitShort = { A: 'A', T: 'T', P: 'P', E: 'E' };
            const energyLabels = { D: 'דינמית (Dynamic)', S: 'יציבה (Stability)', F: 'גמישה (Flexibility)' };
            const stageDescriptions = {
                A: { name: 'חישוב תכונה ראשית', icon: '①', desc: 'שאלות 1-26: זיהוי התכונה הדומיננטית' },
                B: { name: 'חישוב סוג אנרגיה', icon: '②', desc: 'שאלות 27-37: זיהוי סוג האנרגיה המניעה' },
                C: { name: 'אימות תכונות', icon: '③', desc: 'שאלות 38-42: שבירת שוויון בין תכונות' },
                D: { name: 'אימות תכונות', icon: '④', desc: 'שאלות 43-56: חיזוק וחידוד התכונות' },
                E: { name: 'חיזוק דומיננטי', icon: '⑤', desc: 'שאלות 57-60: דירוג סופי של התכונות' }
            };

            // Find the final stage first to show at top
            const finalStage = stages.find(s => s.stage === 'Final');
            let html = '';

            // Final result card at top
            if (finalStage) {
                const verifyBadge = finalStage.needs_verification
                    ? '<div class="mt-3 inline-flex items-center gap-2 bg-yellow-100 text-yellow-800 text-sm font-semibold px-4 py-2 rounded-lg"><i class="fas fa-exclamation-triangle"></i> נדרש אימות אנושי</div>'
                    : '<div class="mt-3 inline-flex items-center gap-2 bg-green-100 text-green-800 text-sm font-semibold px-4 py-2 rounded-lg"><i class="fas fa-check-circle"></i> תקין</div>';

                html += `
                <div class="p-6 bg-gradient-to-br from-blue-900 to-blue-800 rounded-2xl text-white text-center shadow-lg">
                    <div class="text-sm opacity-80 mb-1">${email}</div>
                    <div class="text-5xl font-bold my-4 tracking-wide">${finalStage.pdn_code}</div>
                    <div class="flex justify-center gap-8 text-sm opacity-90">
                        <div>
                            <div class="text-xs opacity-70 mb-1">תכונה</div>
                            <div class="font-semibold text-lg">${finalStage.trait}</div>
                            <div class="text-xs opacity-70">${traitLabels[finalStage.trait] || finalStage.trait}</div>
                        </div>
                        <div class="w-px bg-white/30"></div>
                        <div>
                            <div class="text-xs opacity-70 mb-1">אנרגיה</div>
                            <div class="font-semibold text-lg">${finalStage.energy}</div>
                            <div class="text-xs opacity-70">${energyLabels[finalStage.energy] || finalStage.energy}</div>
                        </div>
                    </div>
                    ${verifyBadge}
                    ${finalStage.confidence_score !== undefined ? `
                    <div class="mt-3 flex items-center justify-center gap-3">
                        <span class="text-xs opacity-70">רמת ביטחון:</span>
                        <div class="w-24 bg-white/20 rounded-full h-3 overflow-hidden">
                            <div class="h-3 rounded-full ${finalStage.confidence_score >= 80 ? 'bg-green-400' : finalStage.confidence_score >= 60 ? 'bg-yellow-400' : 'bg-red-400'}" style="width: ${finalStage.confidence_score}%"></div>
                        </div>
                        <span class="text-sm font-bold">${finalStage.confidence_score}%</span>
                    </div>` : ''}
                </div>`;
            }

            // Stage-by-stage breakdown
            html += '<div class="mt-6 space-y-4">';
            html += '<h3 class="text-lg font-bold text-gray-800 flex items-center gap-2"><i class="fas fa-list-ol text-blue-900"></i> פירוט שלבי החישוב</h3>';

            stages.forEach(stage => {
                if (stage.stage === 'Final') return; // Already shown at top

                const info = stageDescriptions[stage.stage] || { name: stage.stage, icon: '•', desc: '' };
                const hasTraits = stage.scores && ['A','T','P','E'].some(k => stage.scores[k] !== undefined);
                const hasEnergy = stage.scores && ['D','S','F'].some(k => stage.scores[k] !== undefined);

                html += `
                <div class="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
                    <div class="bg-gray-50 px-5 py-3 border-b border-gray-200 flex items-center justify-between">
                        <div class="flex items-center gap-3">
                            <span class="text-xl">${info.icon}</span>
                            <div>
                                <div class="font-semibold text-gray-900">${info.name}</div>
                                <div class="text-xs text-gray-500">${info.desc}</div>
                            </div>
                        </div>
                        ${stage.dominant ? `<span class="px-3 py-1 bg-blue-100 text-blue-800 text-xs font-bold rounded-full">דומיננטי: ${stage.dominant}</span>` : ''}
                    </div>
                    <div class="p-5 space-y-3">`;

                // Trait scores
                if (hasTraits) {
                    const maxTrait = Math.max(...['A','T','P','E'].map(k => stage.scores[k] || 0), 1);
                    ['A', 'T', 'P', 'E'].forEach(key => {
                        if (stage.scores[key] !== undefined) {
                            const isDominant = stage.dominant === key;
                            const barWidth = Math.max(2, (stage.scores[key] / maxTrait) * 100);
                            const barColor = isDominant ? 'bg-blue-600' : 'bg-gray-200';
                            const labelStyle = isDominant ? 'font-bold text-blue-900' : 'text-gray-600';
                            const scoreStyle = isDominant ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700';

                            html += `
                            <div class="flex items-center gap-3">
                                <span class="w-28 text-sm ${labelStyle} flex-shrink-0">${traitLabels[key]}</span>
                                <div class="flex-1 bg-gray-100 rounded-full h-6 relative overflow-hidden">
                                    <div class="${barColor} h-6 rounded-full transition-all duration-500 ease-out" style="width: ${barWidth}%"></div>
                                </div>
                                <span class="w-10 text-center text-sm font-mono font-bold ${scoreStyle} rounded-md px-2 py-0.5 flex-shrink-0">${stage.scores[key]}</span>
                            </div>`;
                        }
                    });
                }

                // Energy scores
                if (hasEnergy) {
                    if (hasTraits) {
                        html += '<div class="border-t border-gray-100 my-3"></div>';
                        html += '<div class="text-xs text-gray-500 font-semibold mb-2">סוג אנרגיה</div>';
                    }
                    const maxEnergy = Math.max(...['D','S','F'].map(k => stage.scores[k] || 0), 1);
                    ['D', 'S', 'F'].forEach(key => {
                        if (stage.scores[key] !== undefined) {
                            const isDominant = stage.dominant === key;
                            const barWidth = Math.max(2, (stage.scores[key] / maxEnergy) * 100);
                            const barColor = isDominant ? 'bg-emerald-600' : 'bg-gray-200';
                            const labelStyle = isDominant ? 'font-bold text-emerald-900' : 'text-gray-600';
                            const scoreStyle = isDominant ? 'bg-emerald-600 text-white' : 'bg-gray-100 text-gray-700';

                            html += `
                            <div class="flex items-center gap-3">
                                <span class="w-28 text-sm ${labelStyle} flex-shrink-0">${energyLabels[key]}</span>
                                <div class="flex-1 bg-gray-100 rounded-full h-6 relative overflow-hidden">
                                    <div class="${barColor} h-6 rounded-full transition-all duration-500 ease-out" style="width: ${barWidth}%"></div>
                                </div>
                                <span class="w-10 text-center text-sm font-mono font-bold ${scoreStyle} rounded-md px-2 py-0.5 flex-shrink-0">${stage.scores[key]}</span>
                            </div>`;
                        }
                    });
                }

                html += '</div></div>';
            });

            html += '</div>';

            container.innerHTML = html;
            document.getElementById('pdnCalculationModal').style.display = 'flex';
            setTimeout(() => { document.getElementById('pdnCalculationModal').querySelector('button, input')?.focus(); }, 100);
        }

        function closeModal(modalId) {
            const modal = document.getElementById(modalId);
            modal.style.display = 'none';
            if (modalId === 'editDiagnoseModal') {
                currentEditEmail = null;
            }
            // Return focus to the previously focused element
            if (document.activeElement) {
                document.activeElement.blur();
            }
        }

        function showLoading() {
            document.getElementById('loadingSpinner').classList.remove('hidden');
        }

        function hideLoading() {
            document.getElementById('loadingSpinner').classList.add('hidden');
        }

        // Close modals when clicking outside
        document.addEventListener('click', function (e) {
            if (e.target.classList.contains('modal-backdrop')) {
                e.target.style.display = 'none';
            }
        });

        // Add keyboard event listeners for all modals
        document.addEventListener('keydown', function (event) {
            if (event.key === 'Escape') {
                const modals = ['questionnaireModal', 'voiceModal', 'editDiagnoseModal', 'loggedInUsersModal', 'pdnCalculationModal', 'releaseNotesModal', 'adminPasswordModal', 'journeyModal'];
                modals.forEach(id => {
                    const modal = document.getElementById(id);
                    if (modal && modal.style.display === 'flex') {
                        closeModal(id);
                    }
                });
            }
        });

        // Function to re-sort data by date (legacy, now delegates to sortTable)
        function resortByDate() {
            sortTable('date');
        }

        let sortColumn = 'date';
        let sortDirection = 'desc';

        function sortTable(column) {
            if (sortColumn === column) {
                sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
            } else {
                sortColumn = column;
                sortDirection = 'asc';
            }

            currentData.sort((a, b) => {
                let valA, valB;
                switch(column) {
                    case 'name':
                        valA = ((a.first_name || '') + ' ' + (a.last_name || '')).trim().toLowerCase();
                        valB = ((b.first_name || '') + ' ' + (b.last_name || '')).trim().toLowerCase();
                        break;
                    case 'email':
                        valA = a.email.toLowerCase();
                        valB = b.email.toLowerCase();
                        break;
                    case 'date':
                        return sortDirection === 'asc' ? parseDate(a.date) - parseDate(b.date) : parseDate(b.date) - parseDate(a.date);
                    case 'pdn_code':
                        valA = (a.pdn_code || '').toLowerCase();
                        valB = (b.pdn_code || '').toLowerCase();
                        break;
                    default:
                        valA = (a[column] || '').toString().toLowerCase();
                        valB = (b[column] || '').toString().toLowerCase();
                }
                if (valA < valB) return sortDirection === 'asc' ? -1 : 1;
                if (valA > valB) return sortDirection === 'asc' ? 1 : -1;
                return 0;
            });

            // Update sort indicators in headers
            document.querySelectorAll('.sort-indicator').forEach(el => {
                if (el.dataset.col === column) {
                    el.textContent = sortDirection === 'asc' ? '↑' : '↓';
                } else {
                    el.textContent = '';
                }
            });

            renderTable(currentData);
        }

        async function exportTableCSV() {
            const password = await requestAdminPassword('הזן סיסמת מנהל לייצוא CSV:');
            if (!password) return;
            if (password !== 'admin') {
                showNotification('סיסמה שגויה', 'error');
                return;
            }

            const headers = ['מזהה מערכת', 'שם', 'אימייל', 'תאריך', 'קוד מערכת', 'ניתוח קול', 'קוד מאבחן', 'הערות', 'עדכון קוד פדן'];
            const rows = currentData.map(u => [
                u.user_id || '', ((u.first_name || '') + ' ' + (u.last_name || '')).trim(),
                u.email, u.date, u.pdn_code || '', u.pdn_voice_code || '',
                u.diagnose_pdn_code || '', u.diagnose_comments || '', u.pdn_update_comments || ''
            ]);

            const BOM = '\uFEFF';
            const csv = BOM + [headers.join(','), ...rows.map(r => r.map(v => `"${(v||'').replace(/"/g, '""')}"`).join(','))].join('\n');
            const blob = new Blob([csv], {type: 'text/csv;charset=utf-8'});
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `pdn_admin_export_${new Date().toISOString().slice(0,10)}.csv`;
            link.click();
            URL.revokeObjectURL(url);
            showNotification('קובץ CSV יוצא בהצלחה', 'success');
        }

        async function viewJourney(email) {
            try {
                const response = await fetch(`/pdn-admin/user/journey/${email}?session_token=${sessionToken}`);
                if (!response.ok) throw new Error('Failed to load journey');
                const data = await response.json();
                displayJourney(data);
            } catch (error) {
                logError('loadJourney', error);
                showNotification('שגיאה בטעינת מסע משתמש', 'error');
            }
        }

        function displayJourney(data) {
            const container = document.getElementById('journeyContent');
            const m = data.metrics;

            let html = `
            <div class="p-5 bg-gradient-to-br from-blue-900 to-blue-800 rounded-2xl text-white text-center mb-6">
                <div class="text-lg font-bold mb-1">${data.user_name}</div>
                <div class="text-sm opacity-80">${data.email}</div>
                <div class="mt-2 inline-block px-3 py-1 rounded-full text-sm font-bold bg-white/20">${data.pdn_code}</div>
            </div>

            <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
                <div class="bg-blue-50 rounded-xl p-3 text-center border border-blue-100">
                    <div class="text-xl font-bold text-blue-900">${m.days_since_diagnosis !== null ? m.days_since_diagnosis : '—'}</div>
                    <div class="text-[10px] text-gray-600 mt-1">ימים מאז אבחון</div>
                </div>
                <div class="bg-green-50 rounded-xl p-3 text-center border border-green-100">
                    <div class="text-xl font-bold text-green-700">${m.total_conversations}</div>
                    <div class="text-[10px] text-gray-600 mt-1">סה"כ שיחות</div>
                </div>
                <div class="bg-purple-50 rounded-xl p-3 text-center border border-purple-100">
                    <div class="text-xl font-bold text-purple-700">${m.active_days}</div>
                    <div class="text-[10px] text-gray-600 mt-1">ימים פעילים</div>
                </div>
                <div class="bg-amber-50 rounded-xl p-3 text-center border border-amber-100">
                    <div class="text-xl font-bold text-amber-700">${m.avg_conversations_per_active_day}</div>
                    <div class="text-[10px] text-gray-600 mt-1">ממוצע שיחות/יום</div>
                </div>
            </div>`;

            // Timeline
            if (data.events.length > 0) {
                html += '<h3 class="text-sm font-semibold text-gray-700 mb-3">ציר זמן</h3>';
                html += '<div class="relative pr-6 border-r-2 border-blue-200 space-y-4">';
                data.events.forEach(event => {
                    const iconMap = { diagnosis: 'fa-stethoscope text-blue-600', conversation: 'fa-comments text-green-600', binat_usage: 'fa-robot text-purple-600' };
                    const bgMap = { diagnosis: 'bg-blue-50 border-blue-200', conversation: 'bg-green-50 border-green-200', binat_usage: 'bg-purple-50 border-purple-200' };
                    const icon = iconMap[event.type] || 'fa-circle text-gray-400';
                    const bg = bgMap[event.type] || 'bg-gray-50 border-gray-200';

                    html += `
                    <div class="relative">
                        <div class="absolute -right-[21px] top-2 w-4 h-4 rounded-full bg-white border-2 border-blue-400 flex items-center justify-center">
                            <div class="w-2 h-2 rounded-full bg-blue-400"></div>
                        </div>
                        <div class="p-3 rounded-lg border ${bg}">
                            <div class="flex items-center justify-between">
                                <div class="flex items-center gap-2">
                                    <i class="fas ${icon} text-sm"></i>
                                    <span class="text-sm font-medium text-gray-800">${event.label}</span>
                                </div>
                                <span class="text-xs text-gray-500">${event.date}</span>
                            </div>
                            ${event.detail ? `<div class="text-xs text-gray-500 mt-1">${event.detail}</div>` : ''}
                        </div>
                    </div>`;
                });
                html += '</div>';
            } else {
                html += '<p class="text-sm text-gray-500 text-center py-6">אין אירועים עדיין</p>';
            }

            container.innerHTML = html;
            document.getElementById('journeyModal').style.display = 'flex';
            setTimeout(() => { document.getElementById('journeyModal').querySelector('button, input')?.focus(); }, 100);
        }

        function showNotification(message, type = 'info') {
            // Create notification element
            const notification = document.createElement('div');

            // Calculate offset based on existing notifications
            const existingNotifications = document.querySelectorAll('.notification-item');
            const offset = existingNotifications.length * 90;

            notification.className = `
    fixed right-6 z-[9999] p-6 rounded-xl shadow-2xl transition-all duration-500 transform translate-x-full border-2
        `;
            notification.style.top = `${24 + offset}px`;

            // Enhanced styling based on type
            let bgColor, borderColor, icon, textColor;
            switch (type) {
                case 'success':
                    bgColor = 'bg-green-50';
                    borderColor = 'border-green-500';
                    icon = 'fa-check-circle';
                    textColor = 'text-green-800';
                    break;
                case 'error':
                    bgColor = 'bg-red-50';
                    borderColor = 'border-red-500';
                    icon = 'fa-exclamation-triangle';
                    textColor = 'text-red-800';
                    break;
                case 'warning':
                    bgColor = 'bg-yellow-50';
                    borderColor = 'border-yellow-500';
                    icon = 'fa-exclamation-circle';
                    textColor = 'text-yellow-800';
                    break;
                default:
                    bgColor = 'bg-blue-50';
                    borderColor = 'border-blue-500';
                    icon = 'fa-info-circle';
                    textColor = 'text-blue-800';
            }

            notification.className += ` ${bgColor} ${borderColor}`;
            notification.innerHTML = `

            <div class="flex items-start space-x-3 space-x-reverse">
                <div class="flex-shrink-0">
                    <i class="fas ${icon} text-xl ${textColor}"></i>
                </div>
                <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium ${textColor} leading-5">${message}</p>
                </div>
                <div class="flex-shrink-0">
                    <button onclick="this.closest('.notification-item').remove()"
                            class="inline-flex text-gray-400 hover:text-gray-600 transition-colors duration-200">
                        <i class="fas fa-times mr-2 text-lg"></i>
                    </button>
                </div>
            </div>

        `;

            // Add a unique class for easier targeting
            notification.classList.add('notification-item');

            document.body.appendChild(notification);

            // Animate in with bounce effect
            setTimeout(() => {
                notification.classList.remove('translate-x-full');
                notification.classList.add('animate-bounce');
                setTimeout(() => {
                    notification.classList.remove('animate-bounce');
                }, 1000);
            }, 100);

            // Auto remove after 8 seconds (increased from 5)
            setTimeout(() => {
                notification.classList.add('translate-x-full');
                setTimeout(() => {
                    if (notification.parentElement) {
                        notification.remove();
                    }
                }, 500);
            }, 8000);

            // Add sound for error notifications
            if (type === 'error') {
                // Create a simple beep sound
                const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                const oscillator = audioContext.createOscillator();
                const gainNode = audioContext.createGain();

                oscillator.connect(gainNode);
                gainNode.connect(audioContext.destination);

                oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
                oscillator.frequency.setValueAtTime(600, audioContext.currentTime + 0.1);

                gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);

                oscillator.start(audioContext.currentTime);
                oscillator.stop(audioContext.currentTime + 0.2);
            }
        }

        // Add this new function to reset loading state for a specific row
        function resetRowLoadingState(email, buttonType) {
            // Find the row for this email
            const rows = document.querySelectorAll('#tableBody tr');
            rows.forEach(row => {
                const emailCell = row.querySelector('td:first-child');
                if (emailCell && emailCell.textContent.trim() === email) {
                    // Find the Alpine component in this row
                    const alpineComponent = row.querySelector('[x-data]');
                    if (alpineComponent && alpineComponent._x_dataStack && alpineComponent._x_dataStack[0]) {
                        alpineComponent._x_dataStack[0].loadingBtn = '';
                        alpineComponent._x_dataStack[0].showModal = false;
                    }
                }
            });
        }

        // Update the existing resetAlpineLoadingState function
        function resetAlpineLoadingState() {
            // Reset all Alpine components
            document.querySelectorAll('[x-data]').forEach(element => {
                if (element._x_dataStack && element._x_dataStack[0]) {
                    element._x_dataStack[0].loadingBtn = '';
                    element._x_dataStack[0].showModal = false;
                }
            });
        }

