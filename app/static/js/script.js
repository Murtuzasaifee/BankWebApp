// Configuration
const API_ENDPOINT = '/chat';
let conversationHistory = [];
let isLoggedIn = false;
let isChatOpen = false;

const chatWindow = document.getElementById('chat-window');
const typingIndicator = document.getElementById('typing-indicator');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const chatPopup = document.getElementById('chat-popup');
const chatbotBtn = document.getElementById('chatbot-btn');

// Update current date
function updateDate() {
    const dateElement = document.getElementById('current-date');
    if (dateElement) {
        const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        dateElement.textContent = new Date().toLocaleDateString('en-US', options);
    }
}

// Toggle chat popup
function toggleChat() {
    isChatOpen = !isChatOpen;
    if (isChatOpen) {
        chatPopup.classList.add('active');
        chatbotBtn.classList.add('active');
        updateWelcomeMessage(); // Update greeting based on login status
        setTimeout(() => chatInput.focus(), 300);
    } else {
        chatPopup.classList.remove('active');
        chatbotBtn.classList.remove('active');
    }
}

// Update welcome message based on login status
function updateWelcomeMessage() {
    const firstMessage = chatWindow.querySelector('.bot-message .message-content');
    if (firstMessage) {
        if (isLoggedIn) {
            // Personalized greeting for logged-in users
            // Try to get username from nav display or current user data
            let username = document.getElementById('user-name-nav')?.textContent ||
                document.getElementById('username-display')?.textContent ||
                (currentUserData && currentUserData.display_name) ||
                'Guest';
            const firstName = username.split(' ')[0]; // Get first name
            firstMessage.innerHTML = `Hi ${firstName}! 👋<br>How may I assist you today?`;
        } else {
            // Default greeting for guests
            firstMessage.innerHTML = `Welcome to ${window.APP_CONFIG.appName}! How can I assist you today?`;
        }
    }
}

// Open chat from hero button
function openChat() {
    if (!isChatOpen) {
        toggleChat();
    }
}

// Send message function
async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    chatInput.disabled = true;
    sendBtn.disabled = true;

    appendMessage(text, 'user-message');
    chatInput.value = '';
    chatInput.style.height = 'auto';

    conversationHistory.push({ role: 'user', content: text, timestamp: new Date().toISOString() });

    typingIndicator.style.display = 'block';
    chatWindow.scrollTop = chatWindow.scrollHeight;

    try {
        const response = await fetch(API_ENDPOINT, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                history: conversationHistory,
                last_query: text
            })
        });

        typingIndicator.style.display = 'none';

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.response || `Server error: ${response.status}`);
        }

        const data = await response.json();

        if (data.response) {
            appendMessage(data.response, 'bot-message', `${window.APP_CONFIG.appName} Support`);
            conversationHistory.push({
                role: 'assistant',
                agent: `${window.APP_CONFIG.appName} Support`,
                content: data.response,
                timestamp: new Date().toISOString()
            });
        } else {
            throw new Error('No response from agent');
        }

        if (data.ticket_id) {
            appendTicketMessage(data.ticket_id);
        }

    } catch (error) {
        typingIndicator.style.display = 'none';
        const errorMessage = error.message || "I'm sorry, I'm having trouble connecting. Please try again later.";
        appendMessage(errorMessage, 'bot-message', 'System');
        console.error('Chat Error:', error);
    } finally {
        chatInput.disabled = false;
        sendBtn.disabled = false;
        chatInput.focus();
    }
}

// Markdown to HTML converter with table support
function markdownToHtml(text) {
    if (!text) return '';

    var lines = text.split('\n');
    var processedLines = [];
    var inList = false;
    var listType = null;
    var inTable = false;
    var tableRows = [];

    // Check if line is a table separator (|---|---|)
    function isTableSeparator(line) {
        var trimmed = line.trim();
        return /^\|?[\s\-:]+\|[\s\-:|]*\|?$/.test(trimmed) && trimmed.indexOf('-') !== -1;
    }

    // Check if line looks like a table row
    function isTableRow(line) {
        var trimmed = line.trim();
        if (trimmed.indexOf('|') === -1) return false;
        if (trimmed.charAt(0) === '#') return false;
        var pipeCount = (trimmed.match(/\|/g) || []).length;
        return pipeCount >= 2;
    }

    // Parse table row into cells
    function parseTableCells(line) {
        var trimmed = line.trim();
        if (trimmed.charAt(0) === '|') trimmed = trimmed.substring(1);
        if (trimmed.charAt(trimmed.length - 1) === '|') trimmed = trimmed.substring(0, trimmed.length - 1);
        return trimmed.split('|').map(function (cell) { return cell.trim(); });
    }

    // Render collected table rows as HTML
    function renderTable() {
        if (tableRows.length === 0) return '';

        var html = '<div class="table-wrapper"><table>';
        var headerDone = false;
        var bodyStarted = false;

        for (var i = 0; i < tableRows.length; i++) {
            var row = tableRows[i];

            if (isTableSeparator(row)) {
                if (!headerDone && i > 0) {
                    html += '</thead>';
                    headerDone = true;
                }
                continue;
            }

            var cells = parseTableCells(row);
            var isHeader = (i === 0 && tableRows.length > 1 && isTableSeparator(tableRows[1]));

            if (isHeader && !headerDone) {
                html += '<thead><tr>';
                for (var j = 0; j < cells.length; j++) {
                    html += '<th>' + processInlineMarkdown(cells[j]) + '</th>';
                }
                html += '</tr>';
            } else {
                if (!bodyStarted) {
                    html += '<tbody>';
                    bodyStarted = true;
                }
                html += '<tr>';
                for (var k = 0; k < cells.length; k++) {
                    html += '<td>' + processInlineMarkdown(cells[k]) + '</td>';
                }
                html += '</tr>';
            }
        }

        if (bodyStarted) html += '</tbody>';
        html += '</table></div>';
        return html;
    }

    for (var i = 0; i < lines.length; i++) {
        var trimmedLine = lines[i].trim();

        // Handle table rows
        if (isTableRow(trimmedLine) || (inTable && isTableSeparator(trimmedLine))) {
            if (inList) {
                processedLines.push('</' + listType + '>');
                inList = false;
                listType = null;
            }
            inTable = true;
            tableRows.push(trimmedLine);
            continue;
        }

        // End of table - render it
        if (inTable) {
            processedLines.push(renderTable());
            inTable = false;
            tableRows = [];
        }

        // Empty line
        if (!trimmedLine) {
            if (inList) {
                processedLines.push('</' + listType + '>');
                inList = false;
                listType = null;
            }
            processedLines.push('<br>');
            continue;
        }

        // Headers
        var headerMatch = trimmedLine.match(/^(#{1,6})\s+(.+)$/);
        if (headerMatch) {
            if (inList) {
                processedLines.push('</' + listType + '>');
                inList = false;
                listType = null;
            }
            var level = headerMatch[1].length;
            processedLines.push('<h' + level + '>' + processInlineMarkdown(headerMatch[2]) + '</h' + level + '>');
            continue;
        }

        // Unordered list
        var ulMatch = trimmedLine.match(/^[\-\*]\s+(.+)$/);
        if (ulMatch) {
            if (!inList || listType !== 'ul') {
                if (inList) processedLines.push('</' + listType + '>');
                processedLines.push('<ul>');
                inList = true;
                listType = 'ul';
            }
            processedLines.push('<li>' + processInlineMarkdown(ulMatch[1]) + '</li>');
            continue;
        }

        // Ordered list
        var olMatch = trimmedLine.match(/^\d+\.\s+(.+)$/);
        if (olMatch) {
            if (!inList || listType !== 'ol') {
                if (inList) processedLines.push('</' + listType + '>');
                processedLines.push('<ol>');
                inList = true;
                listType = 'ol';
            }
            processedLines.push('<li>' + processInlineMarkdown(olMatch[1]) + '</li>');
            continue;
        }

        // Close list if needed
        if (inList) {
            processedLines.push('</' + listType + '>');
            inList = false;
            listType = null;
        }

        // Regular paragraph
        processedLines.push('<p>' + processInlineMarkdown(trimmedLine) + '</p>');
    }

    // Close any open elements
    if (inTable) {
        processedLines.push(renderTable());
    }
    if (inList) {
        processedLines.push('</' + listType + '>');
    }

    var html = processedLines.join('');
    html = html.replace(/<p><\/p>/g, '');
    html = html.replace(/(<br>){3,}/g, '<br><br>');

    return html;
}

function processInlineMarkdown(text) {
    if (!text) return '';

    let html = text;

    const inlineCodes = [];
    html = html.replace(/`[^`]+`/g, (match) => {
        const id = `__CODE_${inlineCodes.length}__`;
        inlineCodes.push(match);
        return id;
    });

    html = html.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

    inlineCodes.forEach((code, index) => {
        const codeContent = code.replace(/`/g, '');
        html = html.replace(`__CODE_${index}__`, '<code>' + codeContent + '</code>');
    });

    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');

    return html;
}

function appendMessage(text, className, agentName = null) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${className}`;

    if (agentName) {
        const label = document.createElement('div');
        label.className = 'agent-label';
        label.textContent = agentName;
        msgDiv.appendChild(label);
    }

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    if (className === 'bot-message') {
        contentDiv.innerHTML = markdownToHtml(text);
    } else {
        contentDiv.textContent = text;
    }

    msgDiv.appendChild(contentDiv);
    chatWindow.appendChild(msgDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

function appendTicketMessage(ticketId) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'ticket-message';
    msgDiv.innerHTML = `<i class="fas fa-check-circle"></i> Ticket Created Successfully<br>Reference ID: <strong>${ticketId}</strong>`;
    chatWindow.appendChild(msgDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

chatInput.addEventListener('keypress', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

chatInput.addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 150) + 'px';
});

// Modal functions
function openTransferModal() {
    document.getElementById('transfer-modal').classList.add('active');
}

function openPayBillModal() {
    document.getElementById('paybill-modal').classList.add('active');
}

function openCardsModal() {
    document.getElementById('cards-modal').classList.add('active');
}

function openInvestmentModal() {
    document.getElementById('investment-modal').classList.add('active');
}

function openStatementModal() {
    document.getElementById('statement-modal').classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

// Close modals when clicking outside
document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', function (e) {
        if (e.target === this) {
            this.classList.remove('active');
        }
    });
});

// Form submissions
document.getElementById('transfer-form')?.addEventListener('submit', function (e) {
    e.preventDefault();
    alert('Transfer submitted successfully! You will receive a confirmation shortly.');
    closeModal('transfer-modal');
    this.reset();
});

// Loan application state
let uploadedFiles = [];

function updateLoanInfo() {
    const loanType = document.getElementById('loan-type').value;
    const loanInfo = document.getElementById('loan-info');
    const requiredDocs = document.getElementById('required-docs');

    if (loanType) {
        loanInfo.style.display = 'block';

        // Update required documents based on loan type
        const docRequirements = {
            'Personal Loan': 'Emirates ID, Filled <a href="#" onclick="event.preventDefault(); alert(\'Download loan application form from your branch or contact support.\');" style="color: var(--primary); text-decoration: underline; font-weight: 600;">Loan Application Form</a>, Utility Bill, Bank Statement (last 6 months)',
            'Home Loan': 'Emirates ID, Filled <a href="#" onclick="event.preventDefault(); alert(\'Download loan application form from your branch or contact support.\');" style="color: var(--primary); text-decoration: underline; font-weight: 600;">Loan Application Form</a>, Property Documents, Utility Bill, Bank Statement (last 6 months)',
            'Car Loan': 'Emirates ID, Filled <a href="#" onclick="event.preventDefault(); alert(\'Download loan application form from your branch or contact support.\');" style="color: var(--primary); text-decoration: underline; font-weight: 600;">Loan Application Form</a>, Driving License, Utility Bill, Bank Statement (last 3 months)',
            'Business Loan': 'Emirates ID, Trade License, Filled <a href="#" onclick="event.preventDefault(); alert(\'Download loan application form from your branch or contact support.\');" style="color: var(--primary); text-decoration: underline; font-weight: 600;">Loan Application Form</a>, Utility Bill, Business Bank Statement (last 12 months)',
            'Education Loan': 'Emirates ID, Admission Letter, Fee Structure, Filled <a href="#" onclick="event.preventDefault(); alert(\'Download loan application form from your branch or contact support.\');" style="color: var(--primary); text-decoration: underline; font-weight: 600;">Loan Application Form</a>, Utility Bill'
        };

        requiredDocs.innerHTML = docRequirements[loanType] || 'Emirates ID, Filled Loan Application Form, Utility Bill, Bank Statement';
    } else {
        loanInfo.style.display = 'none';
    }
}

function handleFileUpload(event) {
    const files = event.target.files;
    const maxSize = 20 * 1024 * 1024; // 20MB

    for (let file of files) {
        // Check file size
        if (file.size > maxSize) {
            alert(`File "${file.name}" is too large. Maximum size is 20MB.`);
            continue;
        }

        // Check if file already uploaded
        if (uploadedFiles.find(f => f.name === file.name && f.size === file.size)) {
            alert(`File "${file.name}" is already uploaded.`);
            continue;
        }

        // Add file to uploaded list
        uploadedFiles.push({
            name: file.name,
            size: file.size,
            type: file.type,
            uploadedAt: new Date()
        });
    }

    // Clear the input to allow re-uploading same file if removed
    event.target.value = '';

    displayUploadedFiles();
    updateSubmitButton();
}

function displayUploadedFiles() {
    const container = document.getElementById('uploaded-files-container');
    const filesList = document.getElementById('uploaded-files-list');
    const fileCount = document.getElementById('file-count');

    if (uploadedFiles.length === 0) {
        container.style.display = 'none';
        return;
    }

    container.style.display = 'block';
    fileCount.textContent = uploadedFiles.length;

    filesList.innerHTML = uploadedFiles.map((file, index) => {
        const fileSize = (file.size / 1024).toFixed(2) + ' KB';
        const fileIcon = getFileIcon(file.name);

        return `
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 0.8rem; background: #F8F9FA; border-radius: 8px; margin-bottom: 0.5rem; transition: all 0.2s;">
                <div style="display: flex; align-items: center; gap: 1rem; flex: 1;">
                    <i class="${fileIcon}" style="font-size: 1.5rem; color: var(--primary);"></i>
                    <div style="flex: 1; min-width: 0;">
                        <div style="font-weight: 600; color: var(--text-dark); font-size: 0.95rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${file.name}</div>
                        <div style="font-size: 0.8rem; color: var(--text-muted);">${fileSize}</div>
                    </div>
                </div>
                <button type="button" onclick="removeFile(${index})" style="background: transparent; border: none; color: #DC3545; cursor: pointer; padding: 0.5rem; font-size: 1.2rem; transition: all 0.2s;" title="Remove file">
                    <i class="fas fa-times-circle"></i>
                </button>
            </div>
        `;
    }).join('');
}

function getFileIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const icons = {
        'pdf': 'fas fa-file-pdf',
        'doc': 'fas fa-file-word',
        'docx': 'fas fa-file-word',
        'jpg': 'fas fa-file-image',
        'jpeg': 'fas fa-file-image',
        'png': 'fas fa-file-image',
        'gif': 'fas fa-file-image'
    };
    return icons[ext] || 'fas fa-file';
}

function removeFile(index) {
    uploadedFiles.splice(index, 1);
    displayUploadedFiles();
    updateSubmitButton();
}

function updateSubmitButton() {
    const submitBtn = document.getElementById('loan-submit-btn');
    const requirements = document.getElementById('loan-requirements');

    if (uploadedFiles.length > 0) {
        submitBtn.style.display = 'block';
        requirements.style.display = 'none';
    } else {
        submitBtn.style.display = 'none';
        requirements.style.display = 'block';
    }
}

function submitLoanApplication(event) {
    event.preventDefault();

    const loanType = document.getElementById('loan-type').value;
    const comments = document.getElementById('loan-comments').value;

    if (uploadedFiles.length === 0) {
        alert('Please upload at least one document to proceed.');
        return;
    }

    // Disable submit button during processing
    const submitBtn = document.getElementById('loan-submit-btn');
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';

    // Call backend API to submit loan and invoke agent
    fetch('/submit-loan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            loan_type: loanType,
            files_count: uploadedFiles.length,
            comments: comments
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Show the platform trace_id as the Application ID
                document.getElementById('loan-ref-number').textContent = data.trace_id;
                document.getElementById('loan-type-display').textContent = loanType;
                document.getElementById('loan-docs-count').textContent = uploadedFiles.length + ' file' + (uploadedFiles.length > 1 ? 's' : '');

                // Close loan modal and show success modal
                closeModal('loan-modal');

                // Small delay for smooth transition
                setTimeout(() => {
                    document.getElementById('loan-success-modal').classList.add('active');
                }, 300);

                // Reset form for next use
                setTimeout(() => {
                    document.getElementById('loan-form').reset();
                    uploadedFiles = [];
                    displayUploadedFiles();
                    updateSubmitButton();
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                }, 500);
            } else {
                alert('Error: ' + (data.message || 'Failed to submit loan application'));
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
            }
        })
        .catch(error => {
            console.error('Error submitting loan:', error);
            alert('An error occurred while submitting your loan application. Please try again.');
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        });
}

function closeLoanSuccessModal() {
    document.getElementById('loan-success-modal').classList.remove('active');
}

function openLoanModal() {
    // Reset when opening
    uploadedFiles = [];
    document.getElementById('loan-form').reset();
    displayUploadedFiles();
    updateSubmitButton();
    document.getElementById('loan-info').style.display = 'none';
    document.getElementById('loan-modal').classList.add('active');
}

// ---------------------------------------------------------------------------
// Stock Trading Account
// ---------------------------------------------------------------------------

let uploadedStockFiles = [];     // Metadata for display
let uploadedStockRawFiles = [];  // Actual File objects sent to the backend

function handleStockFileUpload(event) {
    const files = event.target.files;
    const maxSize = 20 * 1024 * 1024; // 20MB

    for (let file of files) {
        if (file.size > maxSize) {
            alert(`File "${file.name}" is too large. Maximum size is 20MB.`);
            continue;
        }
        if (uploadedStockFiles.find(f => f.name === file.name && f.size === file.size)) {
            alert(`File "${file.name}" is already uploaded.`);
            continue;
        }
        uploadedStockFiles.push({ name: file.name, size: file.size, type: file.type });
        uploadedStockRawFiles.push(file);
    }

    event.target.value = '';
    displayStockUploadedFiles();
    updateStockSubmitButton();
}

function displayStockUploadedFiles() {
    const container = document.getElementById('stock-uploaded-files-container');
    const filesList = document.getElementById('stock-uploaded-files-list');
    const fileCount = document.getElementById('stock-file-count');

    if (uploadedStockFiles.length === 0) {
        container.style.display = 'none';
        return;
    }

    container.style.display = 'block';
    fileCount.textContent = uploadedStockFiles.length;

    filesList.innerHTML = uploadedStockFiles.map((file, index) => {
        const fileSize = (file.size / 1024).toFixed(2) + ' KB';
        return `
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 0.8rem; background: #F8F9FA; border-radius: 8px; margin-bottom: 0.5rem;">
                <div style="display: flex; align-items: center; gap: 1rem; flex: 1;">
                    <i class="${getFileIcon(file.name)}" style="font-size: 1.5rem; color: var(--primary);"></i>
                    <div style="flex: 1; min-width: 0;">
                        <div style="font-weight: 600; color: var(--text-dark); font-size: 0.95rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${file.name}</div>
                        <div style="font-size: 0.8rem; color: var(--text-muted);">${fileSize}</div>
                    </div>
                </div>
                <button type="button" onclick="removeStockFile(${index})" style="background: transparent; border: none; color: #DC3545; cursor: pointer; padding: 0.5rem; font-size: 1.2rem;" title="Remove file">
                    <i class="fas fa-times-circle"></i>
                </button>
            </div>
        `;
    }).join('');
}

function removeStockFile(index) {
    uploadedStockFiles.splice(index, 1);
    uploadedStockRawFiles.splice(index, 1);
    displayStockUploadedFiles();
    updateStockSubmitButton();
}

function updateStockSubmitButton() {
    const submitBtn = document.getElementById('stock-submit-btn');
    const requirements = document.getElementById('stock-requirements');

    if (uploadedStockFiles.length > 0) {
        submitBtn.style.display = 'block';
        requirements.style.display = 'none';
    } else {
        submitBtn.style.display = 'none';
        requirements.style.display = 'block';
    }
}

function openStockModal() {
    uploadedStockFiles = [];
    uploadedStockRawFiles = [];
    document.getElementById('stock-form').reset();
    displayStockUploadedFiles();
    updateStockSubmitButton();
    document.getElementById('stock-modal').classList.add('active');
}

function closeStockSuccessModal() {
    document.getElementById('stock-success-modal').classList.remove('active');
}

function submitStockApplication(event) {
    event.preventDefault();

    const accountType = document.getElementById('stock-account-type').value;
    const comments = document.getElementById('stock-comments').value;

    if (uploadedStockRawFiles.length === 0) {
        alert('Please upload at least one PDF document to proceed.');
        return;
    }

    const submitBtn = document.getElementById('stock-submit-btn');
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';

    // Build multipart form data — browser sets Content-Type with boundary automatically
    const formData = new FormData();
    for (const file of uploadedStockRawFiles) {
        formData.append('files', file, file.name);
    }

    fetch('/submit-stock-account', {
        method: 'POST',
        body: formData   // No Content-Type header — let the browser set the multipart boundary
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('stock-ref-number').textContent = data.trace_id;
                document.getElementById('stock-type-display').textContent = accountType;
                document.getElementById('stock-docs-count').textContent = uploadedStockRawFiles.length + ' file' + (uploadedStockRawFiles.length > 1 ? 's' : '');

                closeModal('stock-modal');

                setTimeout(() => {
                    document.getElementById('stock-success-modal').classList.add('active');
                }, 300);

                setTimeout(() => {
                    document.getElementById('stock-form').reset();
                    uploadedStockFiles = [];
                    uploadedStockRawFiles = [];
                    displayStockUploadedFiles();
                    updateStockSubmitButton();
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                }, 500);
            } else {
                alert('Error: ' + (data.message || 'Failed to submit stock account application'));
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
            }
        })
        .catch(error => {
            console.error('Error submitting stock account application:', error);
            alert('An error occurred while submitting your application. Please try again.');
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        });
}

document.getElementById('paybill-form')?.addEventListener('submit', function (e) {
    e.preventDefault();
    alert('Bill payment processed successfully!');
    closeModal('paybill-modal');
    this.reset();
});

// Login/Logout functionality
let currentUserData = null;

async function checkAuthStatus() {
    try {
        const response = await fetch('/auth/status');
        const data = await response.json();
        isLoggedIn = data.logged_in;
        currentUserData = data.user_data;
        updateUIForAuthStatus(data.logged_in, data.username, data.user_data);

        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('logout') === 'success') {
            window.history.replaceState({}, document.title, window.location.pathname);
            if (isChatOpen) {
                appendMessage('You have been logged out successfully.', 'bot-message', 'System');
            }
        } else if (urlParams.get('login') === 'success') {
            window.history.replaceState({}, document.title, window.location.pathname);
            if (isChatOpen && data.username) {
                const firstName = data.username.split(' ')[0];
                appendMessage(`Welcome, ${firstName}! 👋 How can I assist you today?`, 'bot-message', `${window.APP_CONFIG.appName} Support`);
            }
        }
    } catch (error) {
        console.error('Error checking auth status:', error);
    }
}

function updateUIForAuthStatus(loggedIn, username, userData) {
    if (loggedIn) {
        document.body.classList.add('logged-in');
        document.getElementById('login-btn').style.display = 'none';
        document.getElementById('user-nav-info').style.display = 'flex';
        document.getElementById('user-name-nav').textContent = username || 'User';

        // Update user avatar initials
        if (username) {
            const initials = username.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2);
            document.getElementById('user-avatar').textContent = initials;
        }

        // Hide pre-login nav, show post-login nav
        document.querySelectorAll('.pre-login-nav').forEach(el => el.style.display = 'none');
        document.querySelectorAll('.post-login-nav').forEach(el => el.style.display = 'inline-block');

        // Update dashboard with user data
        if (userData) {
            updateDashboardData(username, userData);
        }

        // Update chat welcome message for logged-in user
        updateWelcomeMessage();

        updateDate();
    } else {
        document.body.classList.remove('logged-in');
        document.getElementById('login-btn').style.display = 'inline-block';
        document.getElementById('user-nav-info').style.display = 'none';

        // Show pre-login nav, hide post-login nav
        document.querySelectorAll('.pre-login-nav').forEach(el => el.style.display = 'inline-block');
        document.querySelectorAll('.post-login-nav').forEach(el => el.style.display = 'none');
    }
}

function updateDashboardData(username, userData) {
    // Update welcome message
    const welcomeTitle = document.querySelector('.dashboard-welcome h1');
    if (welcomeTitle) {
        welcomeTitle.textContent = `Welcome back, ${username}!`;
    }

    // Update account cards
    if (userData.accounts && userData.accounts.length > 0) {
        const accountsGrid = document.querySelector('.accounts-grid');
        if (accountsGrid) {
            accountsGrid.innerHTML = '';

            const gradients = [
                'linear-gradient(135deg, var(--gradient-start) 0%, var(--gradient-end) 100%)',
                'linear-gradient(135deg, var(--primary-dark) 0%, var(--primary) 100%)',
                'linear-gradient(135deg, var(--primary) 0%, var(--gradient-end) 100%)'
            ];

            const icons = ['fa-wallet', 'fa-credit-card', 'fa-gem'];

            userData.accounts.forEach((account, index) => {
                const accountCard = `
                    <div class="account-card" style="background: ${gradients[index % 3]};">
                        <i class="fas ${icons[index % 3]} account-card-icon"></i>
                        <div class="account-type">${account.type}</div>
                        <div class="account-balance">${window.APP_CONFIG.currency} ${account.balance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
                        <div class="account-number">${account.number.includes('Credit') ? 'Available Credit | ' : 'Account: '}${account.number}</div>
                    </div>
                `;
                accountsGrid.innerHTML += accountCard;
            });
        }
    }

    // Update transactions
    if (userData.transactions && userData.transactions.length > 0) {
        const transactionsTable = document.querySelector('.transactions-table tbody');
        if (transactionsTable) {
            transactionsTable.innerHTML = '';

            userData.transactions.forEach(txn => {
                const isCredit = txn.amount > 0;
                const iconClass = isCredit ? 'credit' : 'debit';
                const amountClass = isCredit ? 'amount-credit' : 'amount-debit';
                const amountPrefix = isCredit ? '+ ' : '- ';
                const statusClass = txn.status === 'Completed' ? 'completed' : '';
                const statusStyle = txn.status !== 'Completed' ? 'background: #FFEBEE; color: #C62828;' : '';

                const row = `
                    <tr>
                        <td>
                            <div class="transaction-details">
                                <div class="transaction-icon ${iconClass}">
                                    <i class="fas fa-${txn.icon}"></i>
                                </div>
                                <div class="transaction-info">
                                    <h4>${txn.merchant}</h4>
                                    <p>${txn.type} | ${txn.id}</p>
                                </div>
                            </div>
                        </td>
                        <td>${txn.date}<br><small style="color: #6C757D;">${txn.time}</small></td>
                        <td class="${amountClass}">${amountPrefix}${window.APP_CONFIG.currency} ${Math.abs(txn.amount).toFixed(2)}</td>
                        <td><span class="status-badge ${statusClass}" style="${statusStyle}">${txn.status}</span></td>
                    </tr>
                `;
                transactionsTable.innerHTML += row;
            });
        }
    }
}

function scrollToDashboard() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function showLoginModal() {
    document.getElementById('login-modal').classList.add('active');
    document.getElementById('login-username').focus();
}

function hideLoginModal() {
    document.getElementById('login-modal').classList.remove('active');
    document.getElementById('login-form').reset();
    document.getElementById('login-error').classList.remove('show');
}

async function handleLogin(event) {
    event.preventDefault();
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value.trim();
    const errorDiv = document.getElementById('login-error');

    if (!username) {
        errorDiv.textContent = 'Please enter your username';
        errorDiv.classList.add('show');
        return;
    }

    const submitBtn = document.querySelector('#login-form button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Logging in...';
    errorDiv.classList.remove('show');

    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (data.success) {
            window.location.href = window.location.pathname + '?login=success';
        } else {
            errorDiv.textContent = data.message || 'Login failed';
            errorDiv.classList.add('show');
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    } catch (error) {
        errorDiv.textContent = 'An error occurred during login. Please try again.';
        errorDiv.classList.add('show');
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
        console.error('Login error:', error);
    }
}

async function handleLogout() {
    try {
        const response = await fetch('/logout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await response.json();

        if (data.success) {
            window.location.href = window.location.pathname + '?logout=success';
        }
    } catch (error) {
        console.error('Logout error:', error);
    }
}

document.getElementById('login-modal').addEventListener('click', function (e) {
    if (e.target === this) {
        hideLoginModal();
    }
});

// Smooth scroll for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth' });
        }
    });
});

// Initialize
checkAuthStatus();