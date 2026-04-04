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