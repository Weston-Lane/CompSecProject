async function loginUser() {

    const user = document.getElementById('username').value;
    const pass = document.getElementById('password').value;

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: user, password: pass })
        });

        const result = await response.json();

        if (response.ok) {
            alert('Login successful!');
            
            // Redirect to the main dashboard
            window.location.href = result.redirect;
        } 
        else if (response.status === 429) 
        {
            // Specifically handle the rate limit warning
            alert('Too many attempts! ' + result.message);
        } 
        else 
        {
            alert('Login failed: ' + result.message);
        }
    } catch (error) {
        console.error('Error during login:', error);
        alert('A network error occurred.');
    }
}
async function goToRegister()
{
    window.location.href = "/register"
}

