async function registerUser() {
    const user = document.getElementById('username').value;
    const pass = document.getElementById('password').value;
    const passMatch = document.getElementById('re-enter password').value;
    const email = document.getElementById('email').value;

    const response = await fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: user, password: pass, 
                                passwordMatch: passMatch, email: email })
    });

    const result = await response.json();
    alert(result.message);
    if(response.ok)
    {
        goToLogin()
    }
}

async function goToLogin()
{
    window.location.href = "/"
}