<script lang="ts">
  import { onMount } from 'svelte';
  export let onReady: () => void;

  let msg = "Please wait while the server wakes up";
  let dots = "";
  let spin: any;
  let poll: any;

  const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

  async function checkHealth() {
    try {
      const res = await fetch(`${API_BASE}/health`, { cache: 'no-store' });
      if (res.ok) {
        const data = await res.json();
        if (data?.status === 'ok' && data?.db === 'ok') {
          clearInterval(spin);
          clearInterval(poll);
          onReady?.();
        }
      }
    } catch {
      // ignore; try again on next poll
    }
  }

  onMount(() => {
    spin = setInterval(() => {
      dots = dots.length < 3 ? dots + "." : "";
    }, 400);

    poll = setInterval(checkHealth, 2000);

    return () => {
      clearInterval(spin);
      clearInterval(poll);
    };
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
