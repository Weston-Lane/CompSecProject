async function logoutUser() {
    try {
        // Send a POST request to your logout route
        const response = await fetch('/api/logout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
            // Note: The browser automatically attaches the session cookie to this request!
        });

        const result = await response.json();

        if (response.ok) {
            // The server successfully destroyed the session and cleared the cookie.
            // Redirect the user back to the login page.
            window.location.href = '/'; 
        } else {
            alert('Logout failed: ' + result.message);
        }
    } catch (error) {
        console.error('Error during logout:', error);
        alert('A network error occurred.');
    }
}

window.onload = function() {
    loadMyDocuments();
    loadSharedDocuments();
};

// --- Data Loading ---

async function loadMyDocuments() {
    try {
        // The browser automatically includes the HTTP-only session cookie
        const response = await fetch('/api/my-files', { method: 'GET' });
        
        if (response.ok) {
            const data = await response.json();
            displayMyDocuments(data.files);
        } else if (response.status === 401) {
            window.location.href = '/'; // Redirect to login if unauthorized
        }
    } catch (error) {
        console.error("Failed to fetch my documents", error);
    }
}

async function loadSharedDocuments() {
    try {
        const response = await fetch('/api/shared-with-me', { method: 'GET' });
        
        if (response.ok) {
            const data = await response.json();
            displaySharedDocuments(data.files);
        }
    } catch (error) {
        console.error("Failed to fetch shared documents", error);
    }
}

// --- UI Rendering ---
function displaySharedDocuments(docs) {
    const list = document.getElementById('shared-document-list');
    list.innerHTML = ''; 
    
    if (docs.length === 0) {
        list.innerHTML = '<li>No documents shared with you.</li>';
        return;
    }

    docs.forEach(doc => {
        const li = document.createElement('li');
        li.innerHTML = `
            <strong>${doc.filename}</strong> (Owner: ${doc.owner_id})
            <button onclick="viewFile('${doc.file_id}')">View/Download</button>
        `;
        list.appendChild(li);
    });
}

function displayMyDocuments(docs) {
    const list = document.getElementById('my-document-list');
    list.innerHTML = ''; 
    
    if (docs.length === 0) {
        list.innerHTML = '<li>No documents uploaded yet.</li>';
        return;
    }

    docs.forEach(doc => {
        // Re-adding the shared status logic
        const sharedWithStr = doc.shared_with && doc.shared_with.length > 0 
            ? `<span style="color: #666; font-style: italic;">(Shared with: ${doc.shared_with.join(', ')})</span>` 
            : '<span style="color: #999;">(Private)</span>';

        const li = document.createElement('li');
        li.innerHTML = `
            <strong>${doc.filename}</strong> ${sharedWithStr}
            <div style="margin-top: 5px;">
                <button onclick="viewFile('${doc.file_id}')">View</button>
                <button onclick="window.location.href='/api/download/${doc.file_id}'">Download</button>
                <button onclick="openShareForm('${doc.file_id}')">Share</button>
                <button onclick="deleteFile('${doc.file_id}')" style="background-color: #ff4d4d; color: white;">Delete</button>
            </div>
        `;
        list.appendChild(li);
    });
}

function displayMyDocuments(docs) {
    const list = document.getElementById('my-document-list');
    list.innerHTML = ''; 
    
    if (docs.length === 0) {
        list.innerHTML = '<li>No documents uploaded yet.</li>';
        return;
    }

    docs.forEach(doc => {
        const sharedWithStr = doc.shared_with && doc.shared_with.length > 0 
            ? `(Shared with: ${doc.shared_with.join(', ')})` 
            : '(Private)';

        const li = document.createElement('li');
        li.innerHTML = `
            <strong>${doc.filename}</strong> ${sharedWithStr}
            <button onclick="viewFile('${doc.file_id}')">View/Download</button>
            <button onclick="openShareForm('${doc.file_id}')">Share</button>
            <button onclick="deleteFile('${doc.file_id}')" style="background-color: #ff4d4d; color: white;">Delete</button>
        `;
        list.appendChild(li);
    });
}

// --- Actions ---

async function uploadFile() {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
    
    if (!file) {
        alert("Please select a file first.");
        return;
    }

    const formData = new FormData();
    formData.append('document', file);

    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            fileInput.value = ''; // clear input
            loadMyDocuments(); // refresh list
        } else {
            const errorData = await response.json();
            alert("Upload failed: " + errorData.error);
        }
    } catch (error) {
        console.error("Upload error:", error);
    }
}

function viewFile(fileId) {
    window.open(`/api/view/${fileId}`, '_blank');
}

// --- Sharing Logic ---

function openShareForm(fileId) {
    document.getElementById('share-file-id').value = fileId;
    document.getElementById('share-file-id-display').innerText = fileId;
    document.getElementById('share-form-container').style.display = 'block';
}

function closeShareForm() {
    document.getElementById('share-form-container').style.display = 'none';
    document.getElementById('share-target-user').value = '';
}

async function submitShare() {
    const fileId = document.getElementById('share-file-id').value;
    const targetUser = document.getElementById('share-target-user').value;

    if (!targetUser) {
        alert("Enter a username.");
        return;
    }

    try {
        const response = await fetch('/api/share', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ file_id: fileId, target_user: targetUser })
        });

        const result = await response.json();
        
        if (response.ok) {
            alert("File shared successfully.");
            closeShareForm();
            loadMyDocuments(); // Refresh to show updated "Shared with" status
        } else {
            alert("Error: " + result.error);
        }
    } catch (error) {
        console.error("Sharing error:", error);
    }
}

async function deleteFile(fileId) {
    if (!confirm("Are you sure you want to permanently delete this document?")) {
        return;
    }

    try {
        const response = await fetch(`/api/delete/${fileId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            // Refresh the document list to remove the deleted file from the UI
            loadMyDocuments(); 
        } else {
            const errorData = await response.json();
            alert("Delete failed: " + (errorData.error || "Unknown error"));
        }
    } catch (error) {
        console.error("Delete error:", error);
        alert("A network error occurred while deleting the file.");
    }
}