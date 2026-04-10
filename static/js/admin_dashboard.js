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
        
        // 1. Create a dropdown menu with the user's current role pre-selected
        const roles = ['admin', 'user', 'guest'];
        let dropdownHTML = `<select id="role-select-${user.username}">`;
        roles.forEach(r => {
            const isSelected = user.role === r ? 'selected' : '';
            dropdownHTML += `<option value="${r}" ${isSelected}>${r}</option>`;
        });
        dropdownHTML += `</select>`;

        // 2. Render the user row with the dropdown and Update button
        const li = document.createElement('li');
        li.innerHTML = `
            <strong>${user.username}</strong> - ${user.email} 
            ${dropdownHTML}
            <button onclick="changeRole('${user.username}')" style="background-color: #4CAF50; color: white;">Update Role</button>
            <span style="color: red;">${lockedStatus}</span>
            Failures: ${user.failed_attempts}
        `;
        list.appendChild(li);
    });
}

// 3. New function to handle the API call
async function changeRole(username) {
    // Grab the new role from the dropdown specific to this user
    const newRole = document.getElementById(`role-select-${username}`).value;

    try {
        const response = await fetch('/api/admin/update-role', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: username, role: newRole })
        });

        const result = await response.json();

        if (response.ok) {
            alert(result.message);
            // Reload the user list to show the change
            loadAllUsers(); 
        } else {
            alert("Failed to update role: " + result.error);
        }
    } catch (error) {
        console.error("Error updating role:", error);
        alert("A network error occurred while updating the role.");
    }
}