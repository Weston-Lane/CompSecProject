window.onload = function() {
    loadMyDocuments();
    loadSharedDocuments();
    loadAllSystemDocuments();
    loadAllUsers();
};

async function loadAllSystemDocuments() {
    try {
        const response = await fetch('/api/admin/all-files', { method: 'GET' });
        if (response.ok) {
            const data = await response.json();
            displayAllSystemDocuments(data.files);
        } else if (response.status === 403) {
            alert("Unauthorized: Admin privileges required.");
        }
    } catch (error) {
        console.error("Failed to fetch all documents", error);
    }
}

async function loadAllUsers() {
    try {
        const response = await fetch('/api/admin/users', { method: 'GET' });
        if (response.ok) {
            const data = await response.json();
            displayAllUsers(data.users);
        }
    } catch (error) {
        console.error("Failed to fetch users", error);
    }
}

function displayAllSystemDocuments(docs) {
    const list = document.getElementById('all-document-list');
    list.innerHTML = ''; 
    
    if (docs.length === 0) {
        list.innerHTML = '<li>No documents exist in the system.</li>';
        return;
    }

    docs.forEach(doc => {
        const li = document.createElement('li');
        li.innerHTML = `
            <strong>${doc.filename}</strong> (Owner: ${doc.owner_id}) 
            [Shared with: ${doc.shared_with.length > 0 ? doc.shared_with.join(', ') : 'None'}]
            <button onclick="viewFile('${doc.file_id}')">View/Download</button>
            <button onclick="deleteFile('${doc.file_id}')" style="background-color: #ff4d4d; color: white;">Force Delete</button>
        `;
        list.appendChild(li);
    });
}

function displayAllUsers(users) {
    const list = document.getElementById('user-list');
    list.innerHTML = ''; 
    
    if (users.length === 0) {
        list.innerHTML = '<li>No users found.</li>';
        return;
    }

    users.forEach(user => {
        const lockedStatus = user.locked_until ? `(Locked until ${new Date(user.locked_until * 1000).toLocaleTimeString()})` : '';
        const li = document.createElement('li');
        li.innerHTML = `
            <strong>${user.username}</strong> - ${user.email} 
            <span style="color: blue;">[Role: ${user.role}]</span>
            <span style="color: red;">${lockedStatus}</span>
            Failures: ${user.failed_attempts}
        `;
        list.appendChild(li);
    });
}