<script lang="ts">
  import { auth as authStore } from '$lib/authStore';
  import BootGate from '$lib/components/BootGate.svelte';

  let bootReady = false;
  $: isAuthenticated = $authStore.isAuthenticated;
</script>

{#if !bootReady}
  <BootGate onReady={() => (bootReady = true)} />
{:else}
  <main class="main-container">
    <h1>Reading Tracker</h1>
    <p>Choose where to go:</p>

    <div class="links">
      <a class="link-btn" href="/feed">→ Public Feed</a>

      {#if isAuthenticated}
        <a class="link-btn" href="/library">→ My Library</a>
      {:else}
        <a class="link-btn" href="/library">→ Log in to use My Library</a>
      {/if}
    </div>
  </main>
{/if}

<style>
  :global(body) { background-color: #0d1117; }
  .main-container { max-width: 900px; margin: 0 auto; padding: 20px; text-align: center; color: #e6edf3; }
  .links { display: grid; gap: 12px; justify-content: center; margin-top: 18px; }
  .link-btn {
    display: inline-block;
    padding: 12px 20px;
    background: #238636;
    color: white;
    border-radius: 6px;
    text-decoration: none;
    font-weight: 500;
  }
  .link-btn:hover { background: #2ea043; }
</style>
