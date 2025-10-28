<script lang="ts">
  import { login } from '$lib/authStore';
  import type { UserResponse } from '$lib/types';
  import { loginUser, registerUser } from '$lib/api';

  let username = '';
  let password = '';
  let message: string | null = null;
  let isError = false;
  let registeredSuccessfully = false;
  let submitting = false;

  async function handleRegister() {
    isError = false;
    message = 'Registering user...';
    submitting = true;

    const e = username.trim();
    const p = password.trim();
    if (!e || !p) {
      message = '❌ Username and password are required.';
      isError = true;
      submitting = false;
      return;
    }

    try {
      // register new account
      await registerUser({ username: e, password: p });

      // auto-login right after registration
      registeredSuccessfully = true;
      message = '✅ Registration successful! Logging you in...';

      const { access_token } = await loginUser({ username: e, password: p });

      // minimal user
      const userData: UserResponse = { id: 0, username: e };

      // save, global
      login(access_token, userData);

      message = `Welcome, ${userData.username}! You are now logged in!`;
      isError = false;
    } catch (err: any) {
      message = `❌ Error: ${err?.message ?? 'Request failed'}`;
      isError = true;
    } finally {
      submitting = false;
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
    <button type="submit" disabled={registeredSuccessfully || submitting}>
      {submitting ? 'Submitting…' : 'Register'}
    </button>
  </form>

  {#if message}
    <p class:error={isError} class="message">{message}</p>
  {/if}
</div>

<style>
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

  input[type='text'],
  input[type='password'] {
    padding: 10px;
    border-radius: 5px;
    border: 1px solid #30363d;
    background: #0d1117;
    color: #e6edf3;
    margin-top: 5px;
  }

  button {
    padding: 12px;
    background: #c9514c;
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
