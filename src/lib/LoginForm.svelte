<script lang="ts">
	import { login } from './authStore';
	import type { Token, UserResponse } from '$lib/types';
	import { login as doLogin, getProfile } from './api';

	let username = '';
	let password = '';
	let message: string | null = null;
	let isError = false;

	async function handleLogin() {
		isError = false;
		message = 'Logging in...';

		try {
			// 1️⃣ Call the login helper (POST /auth/login)
			const tokenData: Token = await doLogin(username, password);
			const accessToken = tokenData.access_token;

			// 2️⃣ Fetch user profile (GET /auth/profile)
			const userData: UserResponse = await getProfile(accessToken);

			// 3️⃣ Update the global auth store
			login(accessToken, userData);

			message = `Welcome, ${userData.username}!`;
			isError = false;
		} catch (e: any) {
			message = `Login Error: ${e.message}`;
			isError = true;
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
		<button type="submit">Log In</button>
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
	.error {
		color: #f85149;
	}
	.message {
		margin-top: 15px;
		color: #e6edf3;
	}
</style>
