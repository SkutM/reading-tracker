<script lang="ts">
  import { onMount } from 'svelte';

  // ✅ Option A: make the prop optional
  export let onReady: () => void = () => {};

  let msg = "Please wait while the server wakes up";
  let dots = "";
  let spin: ReturnType<typeof setInterval> | undefined;
  let poll: ReturnType<typeof setInterval> | undefined;

  const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

  function cleanup() {
    if (spin) clearInterval(spin);
    if (poll) clearInterval(poll);
    spin = undefined;
    poll = undefined;
  }

  function notifyReady() {
    cleanup();
    onReady(); // ✅ Option A: safe optional call
  }

  async function checkHealth() {
    try {
      const res = await fetch(`${API_BASE}/health`, { cache: 'no-store' });
      if (!res.ok) return;

      const data = await res.json();
      if (data?.status === 'ok' && data?.db === 'ok') {
        notifyReady();
      }
    } catch {
      // ignore; try again on next poll
    }
  }

  onMount(() => {
    spin = setInterval(() => {
      dots = dots.length < 3 ? dots + "." : "";
    }, 400);

    // optionally check immediately so we don’t wait 2s on warm backend
    checkHealth();
    poll = setInterval(checkHealth, 2000);

    return cleanup;
  });
</script>

<div class="gate">
  <h2>{msg}<span class="dots">{dots}</span></h2>
  <p class="sub">This can take a moment when the Render backend is cold.</p>
</div>

<style>
  .gate {
    min-height: 60vh;
    display: grid;
    place-items: center;
    text-align: center;
    padding: 2rem;
  }
  .sub {
    opacity: 0.7;
    font-size: 0.9rem;
  }
  .dots {
    display: inline-block;
    width: 1.5em;
    text-align: left;
  }
</style>
