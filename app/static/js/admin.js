    // XSS sanitization helper
    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

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
        // Always parse as DD/MM/YYYY (the format stored in the CSV)
        const parts = dateStr.split('/');
        if (parts.length === 3) {
            const date = new Date(parts[2], parts[1] - 1, parts[0]);
            return isNaN(date.getTime()) ? new Date(0) : date;
        }
        let date = new Date(dateStr);
        return isNaN(date.getTime()) ? new Date(0) : date;
    }

    function isRedUser(user) {
        return user.needs_verification === true;
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

    async function loadConversationStats(days) {
        if (!days) days = window._statsDays || 30;
        window._statsDays = days;
        const container = document.getElementById('conversationStats');
        container.innerHTML = '<div style="text-align:center;padding:24px;"><i class="fas fa-spinner fa-spin" style="color:#94a3b8;font-size:16px;"></i></div>';
        // Update active button state
        document.querySelectorAll('.stats-period-btn').forEach(btn => {
            const isActive = parseInt(btn.dataset.days) === days;
            btn.style.background = isActive ? '#0b2e6b' : 'transparent';
            btn.style.color = isActive ? 'white' : '#64748b';
        });
        try {
            const response = await fetch(`/pdn-admin/conversation-stats?session_token=${sessionToken}&days=${days}`);

            if (response.ok) {
                const data = await response.json();
                displayConversationStats(data.stats);
            }
        } catch (error) {
            logError('loadStats', error);
        }
    }

    async function loadTokenUsage(days) {
        if (!days) days = window._tokenDays || 7;
        window._tokenDays = days;
        // Update active button state
        document.querySelectorAll('.token-period-btn').forEach(btn => {
            const isActive = parseInt(btn.dataset.days) === days;
            btn.style.background = isActive ? '#0b2e6b' : 'transparent';
            btn.style.color = isActive ? 'white' : '#64748b';
        });
        const container = document.getElementById('tokenUsageContent');
        container.innerHTML = '<div style="text-align:center;padding:24px;"><i class="fas fa-spinner fa-spin" style="color:#94a3b8;font-size:20px;"></i><p style="font-size:13px;color:#94a3b8;margin-top:8px;">טוען נתוני עלויות...</p></div>';
        try {
            const response = await fetch(`/pdn-admin/token-usage?session_token=${sessionToken}&days=${days}`);
            if (!response.ok) throw new Error('Failed to load');
            const raw = await response.json();
            const { users: stats, daily_totals, projection, period_days } = raw.stats;
            const userNames = Object.keys(stats);
            if (userNames.length === 0) {
                container.innerHTML = '<div style="text-align:center;padding:32px 16px;background:#f8fafc;border-radius:12px;border:1px dashed #cbd5e1;"><i class="fas fa-chart-line" style="font-size:24px;color:#94a3b8;margin-bottom:8px;display:block;"></i><p style="font-size:13px;color:#64748b;margin:0;">אין נתוני שימוש עדיין</p></div>';
                return;
            }
            let tIn=0,tOut=0,tCR=0,tCost=0,tSav=0,tCalls=0;
            userNames.forEach(u=>{const s=stats[u];tIn+=s.input_tokens;tOut+=s.output_tokens;tCR+=s.cache_read_tokens;tCost+=s.total_cost;tSav+=s.cache_savings;tCalls+=s.calls;});
            avgCostPerCall = tCalls > 0 ? tCost / tCalls : 0;
            updateCostEstimate();
            let html=`<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:20px;">
                <div style="background:#f0f4ff;border-radius:12px;padding:16px;text-align:center;border:1px solid #dbeafe;"><div style="font-size:24px;font-weight:800;color:#0b2e6b;">${tCalls}</div><div style="font-size:11px;color:#64748b;margin-top:4px;">קריאות (${period_days} ימים)</div></div>
                <div style="background:#f0f4ff;border-radius:12px;padding:16px;text-align:center;border:1px solid #dbeafe;"><div style="font-size:24px;font-weight:800;color:#0b2e6b;">${((tIn+tOut)/1000).toFixed(1)}K</div><div style="font-size:11px;color:#64748b;margin-top:4px;">סה"כ טוקנים</div></div>
                <div style="background:#ecfdf5;border-radius:12px;padding:16px;text-align:center;border:1px solid #d1fae5;"><div style="font-size:24px;font-weight:800;color:#059669;">$${tCost.toFixed(3)}</div><div style="font-size:11px;color:#64748b;margin-top:4px;">עלות בפועל</div></div>
                <div style="background:#fffbeb;border-radius:12px;padding:16px;text-align:center;border:1px solid #fde68a;"><div style="font-size:24px;font-weight:800;color:#d97706;">$${projection.projected_monthly}</div><div style="font-size:11px;color:#64748b;margin-top:4px;">תחזית חודשית</div></div>
                <div style="background:#fef2f2;border-radius:12px;padding:16px;text-align:center;border:1px solid #fecaca;"><div style="font-size:24px;font-weight:800;color:#dc2626;">$${projection.projected_yearly}</div><div style="font-size:11px;color:#64748b;margin-top:4px;">תחזית שנתית</div></div>
            </div>`;
            const chartDays=Object.keys(daily_totals).sort();
            if(chartDays.length>1){
                const mx=Math.max(...chartDays.map(d=>daily_totals[d].cost),0.001);
                html+=`<div style="margin-bottom:20px;padding:20px;background:white;border-radius:14px;border:1px solid #e2e8f0;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
                    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;">
                        <h4 style="font-size:14px;font-weight:700;color:#1e293b;margin:0;display:flex;align-items:center;gap:8px;"><i class="fas fa-chart-bar" style="color:#0b2e6b;font-size:12px;"></i> עלות יומית</h4>
                        <div style="display:flex;gap:16px;font-size:11px;color:#64748b;"><span>ממוצע: <strong style="color:#0b2e6b;">$${projection.avg_daily_cost.toFixed(4)}</strong></span><span>${projection.active_days} ימים פעילים מתוך ${period_days}</span></div>
                    </div>
                    <div style="display:flex;align-items:flex-end;gap:3px;height:140px;padding:0 4px;">`;
                chartDays.forEach(day=>{
                    const d=daily_totals[day];
                    const bh=Math.max(4,(d.cost/mx)*100);
                    const isToday=day===new Date().toISOString().slice(0,10);
                    const barColor=isToday?'#0b2e6b':'#93c5fd';
                    html+=`<div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;height:100%;position:relative;cursor:pointer;" onmouseenter="this.querySelector('.tip').style.opacity='1'" onmouseleave="this.querySelector('.tip').style.opacity='0'">
                        <div class="tip" style="position:absolute;top:-32px;background:#1e293b;color:white;font-size:10px;padding:4px 8px;border-radius:6px;opacity:0;transition:opacity 0.2s;white-space:nowrap;z-index:10;pointer-events:none;">$${d.cost.toFixed(4)} | ${d.calls} קריאות</div>
                        <div style="width:100%;background:${barColor};border-radius:4px 4px 0 0;height:${bh}%;min-height:4px;transition:background 0.2s;"></div>
                        <div style="font-size:9px;color:#94a3b8;margin-top:6px;transform:rotate(-45deg);transform-origin:top right;white-space:nowrap;">${day.slice(5)}</div>
                    </div>`;
                });
                html+=`</div></div>`;
            }
            html+=`<div style="overflow-x:auto;border-radius:10px;border:1px solid #e2e8f0;">
                <table style="width:100%;font-size:13px;border-collapse:collapse;">
                    <thead><tr style="background:#f8fafc;border-bottom:1px solid #e2e8f0;">
                        <th style="padding:12px 16px;text-align:right;font-weight:600;color:#475569;">משתמש</th>
                        <th style="padding:12px 16px;text-align:center;font-weight:600;color:#475569;">קריאות</th>
                        <th style="padding:12px 16px;text-align:center;font-weight:600;color:#475569;">קלט</th>
                        <th style="padding:12px 16px;text-align:center;font-weight:600;color:#475569;">פלט</th>
                        <th style="padding:12px 16px;text-align:center;font-weight:600;color:#475569;">עלות</th>
                    </tr></thead><tbody>`;
            userNames.sort((a,b)=>stats[b].total_cost-stats[a].total_cost);
            userNames.forEach(user=>{const s=stats[user];
            html+=`<tr style="border-bottom:1px solid #f1f5f9;"><td style="padding:10px 16px;font-weight:500;color:#1e293b;">${user}</td><td style="padding:10px 16px;text-align:center;color:#475569;">${s.calls}</td><td style="padding:10px 16px;text-align:center;color:#475569;">${(s.input_tokens/1000).toFixed(1)}K</td><td style="padding:10px 16px;text-align:center;color:#475569;">${(s.output_tokens/1000).toFixed(1)}K</td><td style="padding:10px 16px;text-align:center;font-weight:700;color:#0b2e6b;">$${s.total_cost.toFixed(4)}</td></tr>`;});
            html+=`<tr style="background:#f8fafc;border-top:2px solid #e2e8f0;"><td style="padding:10px 16px;font-weight:700;color:#1e293b;">סה"כ</td><td style="padding:10px 16px;text-align:center;font-weight:700;">${tCalls}</td><td style="padding:10px 16px;text-align:center;font-weight:700;">${(tIn/1000).toFixed(1)}K</td><td style="padding:10px 16px;text-align:center;font-weight:700;">${(tOut/1000).toFixed(1)}K</td><td style="padding:10px 16px;text-align:center;font-weight:700;color:#0b2e6b;">$${tCost.toFixed(4)}</td></tr></tbody></table></div>`;
            html+=`<p style="font-size:10px;color:#94a3b8;margin-top:12px;text-align:center;">* תמחור לפי Claude Sonnet 4. תחזית מבוססת על ממוצע יומי.</p>`;
            container.innerHTML=html;
        } catch(error){logError('loadTokenUsage',error);container.innerHTML='<div style="text-align:center;padding:24px;color:#dc2626;font-size:13px;"><i class="fas fa-exclamation-circle" style="margin-left:6px;"></i> שגיאה בטעינת נתוני עלויות</div>';}
    }

    function updateCostEstimate() {
        // Show average cost per call in the highlight element
        const highlight = document.getElementById('avgCostHighlight');
        const valueEl = document.getElementById('avgCostValue');
        if (highlight && valueEl && avgCostPerCall > 0) {
            highlight.style.display = 'block';
            valueEl.textContent = '$' + avgCostPerCall.toFixed(4);
        }
    }

    function updateEstimateFromCalls() {
        updateCostEstimate();
    }

    function updateEstimateFromCost() {
        updateCostEstimate();
    }

    function displayConversationStats(stats) {
        const container = document.getElementById('conversationStats');
        
        const allUsers = new Set();
        const dates = Object.keys(stats).sort().reverse();
        
        dates.forEach(date => {
            Object.keys(stats[date]).forEach(email => allUsers.add(email));
        });
        
        const users = Array.from(allUsers).sort();

        // Show empty state if no users have conversations
        if (users.length === 0) {
            container.innerHTML = '<div style="text-align:center;padding:32px 16px;background:#f8fafc;border-radius:12px;border:1px dashed #cbd5e1;"><i class="fas fa-comments" style="font-size:24px;color:#94a3b8;margin-bottom:8px;display:block;"></i><p style="font-size:13px;color:#64748b;margin:0;">אין שיחות בתקופה הנבחרת</p><p style="font-size:11px;color:#94a3b8;margin-top:4px;">נסה לבחור תקופה ארוכה יותר</p></div>';
            return;
        }
        const weeklyTotals = {};
        let grandTotal = 0;
        users.forEach(user => {
            weeklyTotals[user] = dates.reduce((sum, date) => sum + (stats[date][user] || 0), 0);
            grandTotal += weeklyTotals[user];
        });

        // Find max for heat coloring
        const maxPerCell = Math.max(...dates.flatMap(d => users.map(u => stats[d][u] || 0)), 1);
        
        function heatColor(val) {
            if (val === 0) return 'transparent';
            const intensity = Math.min(val / maxPerCell, 1);
            return `rgba(11, 46, 107, ${0.08 + intensity * 0.25})`;
        }

        let html = `
            <div style="grid-column: 1 / -1; width: 100%;">
                <!-- Summary cards -->
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 20px;">
                    <div style="background: #f0f4ff; border-radius: 12px; padding: 16px; text-align: center; border: 1px solid #dbeafe;">
                        <div style="font-size: 24px; font-weight: 800; color: #0b2e6b;">${grandTotal}</div>
                        <div style="font-size: 11px; color: #64748b; margin-top: 4px;">סה"כ שיחות (${dates.length} ימים)</div>
                    </div>
                    <div style="background: #f0f4ff; border-radius: 12px; padding: 16px; text-align: center; border: 1px solid #dbeafe;">
                        <div style="font-size: 24px; font-weight: 800; color: #0b2e6b;">${users.length}</div>
                        <div style="font-size: 11px; color: #64748b; margin-top: 4px;">משתמשים פעילים</div>
                    </div>
                    <div style="background: #f0f4ff; border-radius: 12px; padding: 16px; text-align: center; border: 1px solid #dbeafe;">
                        <div style="font-size: 24px; font-weight: 800; color: #0b2e6b;">${dates.length > 0 ? Math.round(grandTotal / dates.length) : 0}</div>
                        <div style="font-size: 11px; color: #64748b; margin-top: 4px;">ממוצע יומי</div>
                    </div>
                </div>

                <!-- Heat map table -->
                <div style="overflow-x: auto; border-radius: 12px; border: 1px solid #e2e8f0; background: white;">
                    <table style="width: 100%; border-collapse: collapse; font-size: 13px; min-width: 600px;">
                        <thead>
                            <tr style="background: #f8fafc; border-bottom: 2px solid #e2e8f0;">
                                <th style="padding: 12px 16px; text-align: right; font-weight: 700; color: #1e293b; position: sticky; right: 0; background: #f8fafc; z-index: 1;">משתמש</th>
                                ${dates.map(date => `<th style="padding: 12px 10px; text-align: center; font-weight: 600; color: #475569; font-size: 11px; white-space: nowrap;">${date.slice(5)}</th>`).join('')}
                                <th style="padding: 12px 16px; text-align: center; font-weight: 700; color: #0b2e6b; background: #f0f4ff;">סה"כ</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${users.map(user => `
                                <tr style="border-bottom: 1px solid #f1f5f9;">
                                    <td style="padding: 10px 16px; font-weight: 500; color: #1e293b; white-space: nowrap; position: sticky; right: 0; background: white; z-index: 1;">${escapeHtml(user)}</td>
                                    ${dates.map(date => {
                                        const val = stats[date][user] || 0;
                                        return `<td style="padding: 10px; text-align: center; color: ${val > 0 ? '#1e293b' : '#cbd5e1'}; font-weight: ${val > 0 ? '600' : '400'}; background: ${heatColor(val)};">${val}</td>`;
                                    }).join('')}
                                    <td style="padding: 10px 16px; text-align: center; font-weight: 700; color: #0b2e6b; background: #f0f4ff;">${weeklyTotals[user]}</td>
                                </tr>
                            `).join('')}
                            <tr style="background: #f8fafc; border-top: 2px solid #e2e8f0;">
                                <td style="padding: 10px 16px; font-weight: 700; color: #1e293b; position: sticky; right: 0; background: #f8fafc; z-index: 1;">סה"כ</td>
                                ${dates.map(date => {
                                    const dayTotal = Object.values(stats[date]).reduce((sum, count) => sum + count, 0);
                                    return `<td style="padding: 10px; text-align: center; font-weight: 700; color: #1e293b;">${dayTotal}</td>`;
                                }).join('')}
                                <td style="padding: 10px 16px; text-align: center; font-weight: 800; color: #0b2e6b; background: #f0f4ff; font-size: 15px;">${grandTotal}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <p style="font-size: 10px; color: #94a3b8; margin-top: 8px; text-align: center;">צבע רקע מציין עוצמת שימוש יחסית</p>
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
        // Build today string in DD/MM/YYYY format (matching CSV storage format)
        const now = new Date();
        const today = String(now.getDate()).padStart(2, '0') + '/' + String(now.getMonth() + 1).padStart(2, '0') + '/' + now.getFullYear();
        const diagnosedToday = currentData.filter(u => u.date === today).length;
        const anomalies = currentData.filter(u => isRedUser(u)).length;

        document.getElementById('summaryTotal').textContent = total;
        document.getElementById('summaryToday').textContent = diagnosedToday;
        document.getElementById('summaryAnomalies').textContent = anomalies;

        // Fetch active users count
        fetch(`/pdn-admin/logged-in-users?session_token=${sessionToken}`)
            .then(r => {
                if (r.status === 401) return {count: 0};
                return r.ok ? r.json() : {count: 0};
            })
            .then(data => { document.getElementById('summaryActive').textContent = data.count || 0; })
            .catch(() => { document.getElementById('summaryActive').textContent = '0'; });
    }

    function renderTable(data) {
        const tbody = document.getElementById('tableBody');
        tbody.innerHTML = '';

        // Update row count
        document.getElementById('rowCount').textContent = `סה"כ שורות: ${data.length}`;

        if (data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="12" class="text-center py-12 text-gray-500">
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
            <td class="px-4 py-4 font-medium text-gray-900">${escapeHtml(((user.first_name || '') + ' ' + (user.last_name || '')).trim()) || 'N/A'}</td>
            <td class="px-4 py-4 font-medium text-gray-900">
                <span class="cursor-pointer hover:text-blue-700 transition-colors" onclick="navigator.clipboard.writeText('${escapeHtml(user.email)}').then(() => showNotification('אימייל הועתק', 'success'))" title="לחץ להעתקה">
                    ${escapeHtml(user.email)} <i class="fas fa-copy text-gray-300 text-xs mr-1"></i>
                </span>
            </td>
            <td class="px-4 py-4 text-gray-700">${escapeHtml(user.date)}</td>
            <td class="px-4 py-4">
                <span class="px-2 py-1 rounded-full text-xs font-medium ${getPdnBadgeColor(user.pdn_code)}">${escapeHtml(user.pdn_code)}</span>
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
                        '<span class="px-2 py-1 bg-red-100 text-red-800 rounded-full text-xs font-medium" title="נדרש אימות אנושי">אימות</span>' :
                        '<span class="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium">תקין</span>')
                }
            </td>
            <td class="px-4 py-4">
                <span class="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">${escapeHtml(user.pdn_voice_code) || 'N/A'}</span>
            </td>
            <td class="px-4 py-4">
                <span class="px-2 py-1 rounded-full text-xs font-medium ${getPdnBadgeColor(user.diagnose_pdn_code)}">${escapeHtml(user.diagnose_pdn_code) || 'N/A'}</span>
            </td>
            <td class="px-4 py-4 text-gray-700 max-w-xs truncate" title="${escapeHtml(user.diagnose_comments || '')}">${escapeHtml(user.diagnose_comments || '')}</td>
            <td class="px-4 py-4 text-gray-700 max-w-xs truncate" title="${user.pdn_update_comments || ''}">${user.pdn_update_comments || ''}</td>
            <td class="px-4 py-4 text-gray-700">
                ${user.coupon_code ? `<span class="px-2 py-1 bg-amber-100 text-amber-800 rounded-full text-xs font-medium font-mono">${escapeHtml(user.coupon_code)}</span>` : '—'}
            </td>
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
                (user.diagnose_pdn_code && user.diagnose_pdn_code.toLowerCase().includes(searchTerm)) ||
                (user.coupon_code && user.coupon_code.toLowerCase().includes(searchTerm));

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
        <div class="bg-white p-4 rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
        <div class="text-sm text-gray-500 mb-1">קופון</div>
        <div class="font-bold text-gray-900 text-lg break-all" style="direction: ltr; text-align: right;">${metadata["coupon_code"] || '—'}</div>
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
                        showNotification(`אימייל נשלח ל-${email} - נדרש אימות אנושי (הפער בין הציונים קטן מ-2 נקודות)`, 'warning');
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
                        showNotification(`קוד פדן חושב מחדש: ${data.pdn_code} - נדרש אימות אנושי (הפער בין הציונים קטן מ-2 נקודות)`, 'warning');
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
                    ? '<div style="margin-top: 12px; display: inline-flex; align-items: center; gap: 8px; background: #fef3c7; color: #92400e; font-size: 13px; font-weight: 600; padding: 8px 16px; border-radius: 8px;"><i class="fas fa-exclamation-triangle"></i> נדרש אימות אנושי</div>'
                    : '<div style="margin-top: 12px; display: inline-flex; align-items: center; gap: 8px; background: #d1fae5; color: #065f46; font-size: 13px; font-weight: 600; padding: 8px 16px; border-radius: 8px;"><i class="fas fa-check-circle"></i> תקין</div>';

                html += `
                <div style="padding: 28px; background: linear-gradient(135deg, #0b2e6b 0%, #1a3f7a 100%); border-radius: 16px; color: white; text-align: center; box-shadow: 0 8px 32px rgba(11, 46, 107, 0.3);">
                    <div style="font-size: 13px; opacity: 0.7; margin-bottom: 4px;">${email}</div>
                    <div style="font-size: 48px; font-weight: 800; margin: 16px 0; letter-spacing: 2px;">${finalStage.pdn_code}</div>
                    <div style="display: flex; justify-content: center; gap: 40px; font-size: 14px; opacity: 0.9;">
                        <div>
                            <div style="font-size: 11px; opacity: 0.6; margin-bottom: 4px;">תכונה</div>
                            <div style="font-size: 20px; font-weight: 700;">${finalStage.trait}</div>
                            <div style="font-size: 11px; opacity: 0.6;">${traitLabels[finalStage.trait] || finalStage.trait}</div>
                        </div>
                        <div style="width: 1px; background: rgba(255,255,255,0.2);"></div>
                        <div>
                            <div style="font-size: 11px; opacity: 0.6; margin-bottom: 4px;">אנרגיה</div>
                            <div style="font-size: 20px; font-weight: 700;">${finalStage.energy}</div>
                            <div style="font-size: 11px; opacity: 0.6;">${energyLabels[finalStage.energy] || finalStage.energy}</div>
                        </div>
                    </div>
                    ${verifyBadge}
                </div>`; 
            }

            // Stage-by-stage breakdown
            html += '<div style="margin-top: 24px;">';
            html += '<h3 style="font-size: 16px; font-weight: 700; color: #1e293b; margin: 0 0 16px; display: flex; align-items: center; gap: 8px;"><i class="fas fa-list-ol" style="color: #0b2e6b;"></i> פירוט שלבי החישוב</h3>';

            let energyLabelShown = false;
            stages.forEach(stage => {
                if (stage.stage === 'Final') return; // Already shown at top

                const info = stageDescriptions[stage.stage] || { name: stage.stage, icon: '•', desc: '' };
                const hasTraits = stage.scores && ['A','T','P','E'].some(k => stage.scores[k] !== undefined);
                const hasEnergy = stage.scores && ['D','S','F'].some(k => stage.scores[k] !== undefined);

                html += `
                <div style="background: white; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
                    <div style="background: #f8fafc; padding: 12px 20px; border-bottom: 1px solid #e2e8f0; display: flex; align-items: center; justify-content: space-between;">
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <span style="font-size: 20px;">${info.icon}</span>
                            <div>
                                <div style="font-weight: 600; color: #1e293b; font-size: 14px;">${info.name}</div>
                                <div style="font-size: 11px; color: #64748b;">${info.desc}</div>
                            </div>
                        </div>
                        ${stage.dominant ? `<span style="padding: 4px 12px; background: rgba(11,46,107,0.08); color: #0b2e6b; font-size: 12px; font-weight: 700; border-radius: 20px;">דומיננטי: ${stage.dominant}</span>` : ''}
                    </div>
                    <div style="padding: 16px 20px;">`;

                // Trait scores
                if (hasTraits) {
                    const maxTrait = Math.max(...['A','T','P','E'].map(k => stage.scores[k] || 0), 1);
                    ['A', 'T', 'P', 'E'].forEach(key => {
                        if (stage.scores[key] !== undefined) {
                            const isDominant = stage.dominant === key;
                            const barWidth = Math.max(2, (stage.scores[key] / maxTrait) * 100);
                            const barColor = isDominant ? '#0b2e6b' : '#e2e8f0';
                            const labelWeight = isDominant ? '700' : '400';
                            const labelColor = isDominant ? '#0b2e6b' : '#64748b';
                            const scoreColor = isDominant ? '#0b2e6b' : '#64748b';

                            html += `
                            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                                <span style="width: 120px; font-size: 13px; font-weight: ${labelWeight}; color: ${labelColor}; flex-shrink: 0;">${traitLabels[key]}</span>
                                <div style="flex: 1; background: #f1f5f9; border-radius: 20px; height: 22px; overflow: hidden; position: relative;">
                                    <div style="background: ${barColor}; height: 100%; border-radius: 20px; width: ${barWidth}%; transition: width 0.5s ease;"></div>
                                </div>
                                <span style="width: 36px; text-align: center; font-size: 13px; font-weight: 700; color: ${scoreColor}; flex-shrink: 0;">${stage.scores[key]}</span>
                            </div>`;
                        }
                    });
                }

                // Energy scores
                if (hasEnergy) {
                    if (hasTraits) {
                        html += '<div style="border-top: 1px solid #f1f5f9; margin: 12px 0;"></div>';
                    }
                    if (!energyLabelShown) {
                        html += '<div style="font-size: 11px; color: #64748b; font-weight: 600; margin-bottom: 8px;">סוג אנרגיה</div>';
                        energyLabelShown = true;
                    }
                    const maxEnergy = Math.max(...['D','S','F'].map(k => stage.scores[k] || 0), 1);
                    ['D', 'S', 'F'].forEach(key => {
                        if (stage.scores[key] !== undefined) {
                            const isDominant = stage.dominant === key;
                            const barWidth = Math.max(2, (stage.scores[key] / maxEnergy) * 100);
                            const barColor = isDominant ? '#059669' : '#e2e8f0';
                            const labelWeight = isDominant ? '700' : '400';
                            const labelColor = isDominant ? '#065f46' : '#64748b';
                            const scoreColor = isDominant ? '#065f46' : '#64748b';

                            html += `
                            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                                <span style="width: 120px; font-size: 13px; font-weight: ${labelWeight}; color: ${labelColor}; flex-shrink: 0;">${energyLabels[key]}</span>
                                <div style="flex: 1; background: #f1f5f9; border-radius: 20px; height: 22px; overflow: hidden; position: relative;">
                                    <div style="background: ${barColor}; height: 100%; border-radius: 20px; width: ${barWidth}%; transition: width 0.5s ease;"></div>
                                </div>
                                <span style="width: 36px; text-align: center; font-size: 13px; font-weight: 700; color: ${scoreColor}; flex-shrink: 0;">${stage.scores[key]}</span>
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
                    case 'coupon_code':
                        valA = (a.coupon_code || '').toLowerCase();
                        valB = (b.coupon_code || '').toLowerCase();
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

            // Apply current filters to export only visible data
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            const showRedUsersOnly = document.getElementById('redUsersFilter').checked;

            const exportData = currentData.filter(user => {
                const fullName = ((user.first_name || '') + ' ' + (user.last_name || '')).trim().toLowerCase();
                const matchesSearch = user.email.toLowerCase().includes(searchTerm) ||
                    fullName.includes(searchTerm) ||
                    (user.first_name && user.first_name.toLowerCase().includes(searchTerm)) ||
                    (user.last_name && user.last_name.toLowerCase().includes(searchTerm));

                if (showRedUsersOnly) {
                    return matchesSearch && user.needs_verification === true;
                }
                return matchesSearch;
            });

            const headers = ['מזהה מערכת', 'שם', 'אימייל', 'תאריך', 'קוד מערכת', 'אימות', 'ניתוח קול', 'קוד מאבחן', 'הערות', 'עדכון קוד פדן', 'קופון'];
            const rows = exportData.map(u => [
                u.user_id || '', ((u.first_name || '') + ' ' + (u.last_name || '')).trim(),
                u.email, u.date, u.pdn_code || '',
                u.needs_verification ? 'נדרש אימות' : 'תקין',
                u.pdn_voice_code || '',
                u.diagnose_pdn_code || '', u.diagnose_comments || '', u.pdn_update_comments || '',
                u.coupon_code || ''
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
            showNotification(`קובץ CSV יוצא בהצלחה (${exportData.length} שורות)`, 'success');
        }

        async function sendAlgorithmReport() {
            if (!sessionToken) {
                window.location.href = '/pdn-admin/';
                return;
            }

            try {
                showNotification('שולח דוח אלגוריתם...', 'info');
                const response = await fetch(`/pdn-admin/send_algorithm_report?session_token=${sessionToken}`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'}
                });

                if (response.ok) {
                    const data = await response.json();
                    showNotification(data.message || 'דוח נשלח בהצלחה', 'success');
                } else if (response.status === 401) {
                    redirectToLogin();
                } else {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.error || 'Failed to send report');
                }
            } catch (error) {
                logError('sendAlgorithmReport', error);
                showNotification(`שגיאה בשליחת הדוח: ${error.message}`, 'error');
            }
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
    fixed left-6 z-[9999] p-6 rounded-xl shadow-2xl transition-all duration-500 transform -translate-x-full border-2
        `;
            notification.style.bottom = `${24 + offset}px`;

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
                notification.classList.remove('-translate-x-full');
                notification.classList.add('animate-bounce');
                setTimeout(() => {
                    notification.classList.remove('animate-bounce');
                }, 1000);
            }, 100);

            // Auto remove after 8 seconds (increased from 5)
            setTimeout(() => {
                notification.classList.add('-translate-x-full');
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


    // =============================================
    // User Management (Chat Users CRUD)
    // =============================================

    let chatUsersData = [];
    let availablePdnCodes = [];
    let deleteUserEmail = null;

    async function loadChatUsers() {
        const tbody = document.getElementById('chatUsersTableBody');
        tbody.innerHTML = '<tr><td colspan="5" class="text-center py-8 text-gray-400"><i class="fas fa-spinner fa-spin ml-2"></i> טוען...</td></tr>';

        try {
            const [usersResp, codesResp] = await Promise.all([
                fetch(`/pdn-admin/users?session_token=${sessionToken}`),
                fetch(`/pdn-admin/users/pdn-codes?session_token=${sessionToken}`)
            ]);

            if (usersResp.status === 401 || codesResp.status === 401) {
                redirectToLogin();
                return;
            }

            if (!usersResp.ok) throw new Error('Failed to load users');
            if (!codesResp.ok) throw new Error('Failed to load PDN codes');

            const usersData = await usersResp.json();
            const codesData = await codesResp.json();

            chatUsersData = usersData.users || [];
            availablePdnCodes = codesData.codes || [];

            renderChatUsersTable();
        } catch (error) {
            logError('loadChatUsers', error);
            tbody.innerHTML = '<tr><td colspan="5" class="text-center py-8 text-red-500">שגיאה בטעינת משתמשים</td></tr>';
        }
    }

    function renderChatUsersTable() {
        const tbody = document.getElementById('chatUsersTableBody');
        document.getElementById('chatUserCount').textContent = `סה"כ: ${chatUsersData.length}`;

        if (chatUsersData.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center py-8 text-gray-400"><i class="fas fa-inbox text-3xl mb-2 block"></i>אין משתמשים</td></tr>';
            return;
        }

        tbody.innerHTML = chatUsersData.map(user => `
            <tr class="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                <td class="px-4 py-3 font-medium text-gray-900" dir="ltr">${user.email}</td>
                <td class="px-4 py-3 text-gray-800">${user.name}</td>
                <td class="px-4 py-3 text-center text-gray-700">${user.gender === 'male' ? 'גבר' : user.gender === 'female' ? 'אישה' : '-'}</td>
                <td class="px-4 py-3 text-center">
                    <span class="px-2 py-1 rounded-full text-xs font-medium ${getPdnBadgeColor(user.pdn_code)}">${user.pdn_code}</span>
                </td>
                <td class="px-4 py-3 text-center text-gray-700">${user.daily_conversation_limit}</td>
                <td class="px-4 py-3 text-center text-gray-500 text-xs">${user.created_at || '-'}</td>
                <td class="px-4 py-3 text-center">
                    <div class="flex items-center justify-center gap-2">
                        <button onclick="openEditUserModal('${user.email}')"
                                class="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors" title="ערוך">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button onclick="openDeleteUserDialog('${user.email}')"
                                class="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors" title="מחק">
                            <i class="fas fa-trash-alt"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    }

    function populatePdnCodeDropdown(selectedCode) {
        const select = document.getElementById('userFormPdnCode');
        select.innerHTML = '<option value="">בחר קוד PDN...</option>';
        availablePdnCodes.forEach(code => {
            const option = document.createElement('option');
            option.value = code;
            option.textContent = code.toUpperCase();
            if (code === selectedCode) option.selected = true;
            select.appendChild(option);
        });
    }

    function openAddUserModal() {
        document.getElementById('userFormMode').value = 'add';
        document.getElementById('userFormOriginalEmail').value = '';
        document.getElementById('userFormTitle').innerHTML = '<i class="fas fa-user-plus ml-2 text-blue-900"></i> הוסף משתמש';
        document.getElementById('userFormEmail').value = '';
        document.getElementById('userFormEmail').disabled = false;
        document.getElementById('userFormPassword').value = '';
        document.getElementById('userFormPassword').required = true;
        document.getElementById('userFormPassword').placeholder = 'סיסמה (חובה)';
        document.getElementById('userFormName').value = '';
        document.getElementById('userFormLimit').value = 15;
        populatePdnCodeDropdown('');
        document.getElementById('userFormModal').style.display = 'flex';
        setTimeout(() => document.getElementById('userFormEmail').focus(), 100);
    }

    function openEditUserModal(email) {
        const user = chatUsersData.find(u => u.email === email);
        if (!user) return;

        document.getElementById('userFormMode').value = 'edit';
        document.getElementById('userFormOriginalEmail').value = email;
        document.getElementById('userFormTitle').innerHTML = '<i class="fas fa-user-edit ml-2 text-blue-900"></i> ערוך משתמש';
        document.getElementById('userFormEmail').value = email;
        document.getElementById('userFormEmail').disabled = true;
        document.getElementById('userFormPassword').value = '';
        document.getElementById('userFormPassword').required = false;
        document.getElementById('userFormPassword').placeholder = 'השאר ריק לשמירת הסיסמה הנוכחית';
        document.getElementById('userFormName').value = user.name;
        document.getElementById('userFormGender').value = user.gender || '';
        document.getElementById('userFormLimit').value = user.daily_conversation_limit;
        populatePdnCodeDropdown(user.pdn_code);
        document.getElementById('userFormModal').style.display = 'flex';
        setTimeout(() => document.getElementById('userFormName').focus(), 100);
    }

    async function handleUserFormSubmit(e) {
        e.preventDefault();

        const mode = document.getElementById('userFormMode').value;
        const email = document.getElementById('userFormEmail').value.trim().toLowerCase();
        const password = document.getElementById('userFormPassword').value.trim();
        const name = document.getElementById('userFormName').value.trim();
        const gender = document.getElementById('userFormGender').value;
        const pdnCode = document.getElementById('userFormPdnCode').value;
        const limit = parseInt(document.getElementById('userFormLimit').value) || 15;

        // Frontend validation
        if (!email || !name || !pdnCode || !gender) {
            showNotification('אנא מלא את כל השדות הנדרשים', 'warning');
            return;
        }

        if (mode === 'add' && !password) {
            showNotification('סיסמה נדרשת להוספת משתמש חדש', 'warning');
            return;
        }

        // Email format validation
        const emailRegex = /^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$/;
        if (mode === 'add' && !emailRegex.test(email)) {
            showNotification('פורמט אימייל לא תקין', 'warning');
            return;
        }

        // Request admin password
        const adminPassword = await requestAdminPassword('אנא הזן סיסמת מנהל לאישור:');
        if (!adminPassword) return;

        showLoading();
        try {
            let url, method, body;

            if (mode === 'add') {
                url = `/pdn-admin/users?session_token=${sessionToken}`;
                method = 'POST';
                body = { email, password, name, gender, pdn_code: pdnCode, daily_conversation_limit: limit, admin_password: adminPassword };
            } else {
                const originalEmail = document.getElementById('userFormOriginalEmail').value;
                url = `/pdn-admin/users/${encodeURIComponent(originalEmail)}?session_token=${sessionToken}`;
                method = 'PUT';
                body = { name, gender, pdn_code: pdnCode, daily_conversation_limit: limit, admin_password: adminPassword };
                if (password) body.password = password;
            }

            const response = await fetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });

            if (response.status === 401) {
                const data = await response.json();
                if (data.error === 'Invalid admin password') {
                    showNotification('סיסמת מנהל שגויה', 'error');
                } else {
                    redirectToLogin();
                }
                return;
            }

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.error || 'Operation failed');
            }

            closeModal('userFormModal');
            showNotification(mode === 'add' ? 'משתמש נוסף בהצלחה' : 'משתמש עודכן בהצלחה', 'success');
            await loadChatUsers();
        } catch (error) {
            logError('userFormSubmit', error);
            showNotification(`שגיאה: ${error.message}`, 'error');
        } finally {
            hideLoading();
        }
    }

    function openDeleteUserDialog(email) {
        deleteUserEmail = email;
        document.getElementById('deleteUserMessage').textContent = `האם אתה בטוח שברצונך למחוק את המשתמש ${email}?`;
        document.getElementById('deleteUserModal').style.display = 'flex';
    }

    async function confirmDeleteUser() {
        if (!deleteUserEmail) return;

        closeModal('deleteUserModal');

        const adminPassword = await requestAdminPassword('אנא הזן סיסמת מנהל לאישור מחיקה:');
        if (!adminPassword) return;

        showLoading();
        try {
            const response = await fetch(`/pdn-admin/users/${encodeURIComponent(deleteUserEmail)}?session_token=${sessionToken}`, {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ admin_password: adminPassword })
            });

            if (response.status === 401) {
                const data = await response.json();
                if (data.error === 'Invalid admin password') {
                    showNotification('סיסמת מנהל שגויה', 'error');
                } else {
                    redirectToLogin();
                }
                return;
            }

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.error || 'Delete failed');
            }

            showNotification('משתמש נמחק בהצלחה', 'success');
            await loadChatUsers();
        } catch (error) {
            logError('deleteUser', error);
            showNotification(`שגיאה במחיקת משתמש: ${error.message}`, 'error');
        } finally {
            hideLoading();
            deleteUserEmail = null;
        }
    }
