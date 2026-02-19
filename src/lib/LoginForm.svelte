<script lang="ts">
  import { login } from '$lib/authStore';
  import type { UserResponse } from '$lib/types';
  import { loginUser, getProfile } from '$lib/api';

  let username = '';
  let password = '';
  let message: string | null = null;
  let isError = false;
  let submitting = false;

  async function handleLogin() {
    isError = false;
    message = 'Logging in...';
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
      // 1) get token
      const { access_token } = await loginUser({ username: e, password: p });

      // 2) fetch real user profile (must include real id)
      const me = (await getProfile(access_token)) as UserResponse;

      // 3) persist auth state (token + real user)
      login(access_token, me);

      message = `Welcome, ${me.username ?? e}!`;
      isError = false;
    } catch (err: any) {
      message = `❌ Login error: ${err?.message ?? 'Request failed'}`;
      isError = true;
    } finally {
      submitting = false;
    }
  }
</script>

<div class="login-card">
  <h2>Log In</h2>
  <form on:submit|preventDefault={handleLogin}>
    <label>
      Username
      <input type="text" bind:value={username} required />
    </label>

    <label>
      Password
      <input type="password" bind:value={password} required />
    </label>

    <button type="submit" disabled={submitting}>
      {submitting ? 'Logging in…' : 'Log In'}
    </button>
  </form>

  {#if message}
    <p class:error={isError} class="message">{message}</p>
  {/if}
</div>

<style>
  .login-card {
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
    background: #2ea043;
    color: white;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    transition: background-color 0.2s;
    margin-top: 10px;
  }
  button:disabled {
    background: #30363d;
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
