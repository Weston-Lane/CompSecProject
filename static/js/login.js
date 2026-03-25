async function loginUser() {

    const user = document.getElementById('username').value;
    const pass = document.getElementById('password').value;

    try {
        const response = await fetch('http://127.0.0.1:5000/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: user, password: pass })
        });

        const result = await response.json();

        if (response.ok) {
            // Save the JWT to localStorage
            localStorage.setItem('jwt_token', result.token);
            alert('Login successful!');
            
            // Redirect to the main dashboard
            window.location.href = '/dashboard'; 
        } else {
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

