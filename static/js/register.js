async function registerUser() {
    const user = document.getElementById('username').value;
    const pass = document.getElementById('password').value;

    const response = await fetch('http://127.0.0.1:5000/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: user, password: pass })
    });

    const result = await response.json();
    alert(result.message);
}

async function goToLogin()
{
    window.location.href = "/"
}