<script lang="ts">
    import { login } from './authStore'; // instant login after registration
    import type { Token, UserResponse } from '$lib/types';
    
    let username = '';
    let password = '';
    let message: string | null = null;
    let isError = false;
    let registeredSuccessfully = false;

    async function handleRegister() {
        isError = false;
        message = 'Registering user...';

        try {
            // 1. /auth/register POST
            const registerResponse = await fetch('/api/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            if (!registerResponse.ok) {
                const errorData = await registerResponse.json();
                throw new Error(errorData.detail || 'Registration failed.');
            }
            
            // log in immediately upon register
            registeredSuccessfully = true;
            message = '✅ Registration successful! Logging you in...';
            
            // --- Auto-Login Sequence (Same as in LoginForm) ---
            
            // 2. authenticate
            const tokenResponse = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            
            const tokenData: Token = await tokenResponse.json();
            const accessToken = tokenData.access_token;

            // 3. GET profile /api/auth/profile
            const profileResponse = await fetch('/api/auth/profile', {
                method: 'GET',
                headers: { 'Authorization': `Bearer ${accessToken}` }
            });
            
            const userData: UserResponse = await profileResponse.json();

            // 4. update global store
            login(accessToken, userData);
            
            message = `Welcome, ${userData.username}! You are now logged in!`;
            isError = false;

        } catch (e: any) {
            // register FAIL
            message = `❌ Error: ${e.message}`;
            isError = true;
        }
    }
</script>

<div class="register-card">
    <h2>Register an Account</h2>
    <form on:submit|preventDefault={handleRegister}>
        <label>
            Username
            <input type="text" bind:value={username} required />
        </label>
        <label>
            Password
            <input type="password" bind:value={password} required />
        </label>
        <button type="submit" disabled={registeredSuccessfully}>Register</button>
    </form>
    {#if message}
        <p class:error={isError} class="message">{message}</p>
    {/if}
</div>

<style>
    /* similar to LoginForm */
    .register-card {
        background: #274e73;
        padding: 30px;
        border-radius: 10px;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.5);
        margin: 50px auto;
        max-width: 350px;
        text-align: center;
    }
    form {
        display: grid;
        gap: 15px;
        margin-top: 20px;
    }
    label {
        display: grid;
        text-align: left;
    }
    input[type="text"], input[type="password"] {
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #30363d;
        background: #0d1117;
        color: #e6edf3;
        margin-top: 5px;
    }
    button {
        padding: 12px;
        background: #c9514c; /* different color for registration/auth button */
        color: white;
        border: none;
        border-radius: 5px;
        cursor: pointer;
        transition: background-color 0.2s;
        margin-top: 10px;
    }
    button:disabled {
        background: #5a3836;
        cursor: not-allowed;
    }
    .error {
        color: #f85149;
    }
    .message {
        margin-top: 15px;
        color: #e6edf3;
    }
</style>