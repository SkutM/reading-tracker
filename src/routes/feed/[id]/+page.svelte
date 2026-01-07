<script lang="ts">
  import { page } from '$app/stores';
  import BootGate from '$lib/components/BootGate.svelte';

  let bootReady = false;

  const API_BASE = import.meta.env.PUBLIC_API_BASE_URL ?? 'http://127.0.0.1:8000';

  type ReviewType = 'RECOMMENDED' | 'NOT_RECOMMENDED' | 'NEUTRAL';

  type FeedDetail = {
    id: number;
    book: { id: number; title: string; author: string | null; cover_image_url?: string | null };
    author: { id: number | null; username: string | null };
    body: string | null;
    review_type: ReviewType | null;
    review_date: string | null;
    like_count: number;
    comment_count: number;
    created_at: string | null;
  };

  let item: FeedDetail | null = null;
  let loading = true;
  let error: string | null = null;

  function formatDate(s?: string | null) {
    if (!s) return '';
    const d = new Date(s);
    return isNaN(d.getTime()) ? '' : d.toLocaleDateString();
  }

  async function loadOne(id: string) {
    loading = true;
    error = null;

    try {
      const res = await fetch(`${API_BASE}/feed/${id}`);
      if (!res.ok) throw new Error(`Post request failed (${res.status})`);
      item = (await res.json()) as FeedDetail;
    } catch (e: any) {
      error = e?.message ?? 'Failed to load post';
      item = null;
    } finally {
      loading = false;
    }
  }

  $: if (bootReady) {
    const id = $page.params.id;
    if (id) loadOne(id);
  }
</script>

{#if !bootReady}
  <BootGate onReady={() => (bootReady = true)} />
{:else}
  <main class="wrap">
    <div class="topbar">
      <h1>Post</h1>
      <a class="backlink" href="/feed">← Back to feed</a>
    </div>

    {#if loading}
      <p class="muted">Loading…</p>
    {:else if error}
      <p class="error">{error}</p>
    {:else if item}
      <div class="card">
        <div class="row">
          <div class="left">
            <div class="title">
              {item.book.title}{#if item.book.author} — {item.book.author}{/if}
            </div>
            <div class="meta">
              @{item.author.username ?? 'reader'}
              {#if item.review_date} • {formatDate(item.review_date)}{/if}
              {#if item.review_type} • {item.review_type}{/if}
            </div>
          </div>
          <div class="right">
            <div>❤️ {item.like_count}</div>
            <div>💬 {item.comment_count}</div>
          </div>
        </div>

        {#if item.book.cover_image_url}
          <img class="cover" src={item.book.cover_image_url} alt={`Cover for ${item.book.title}`} />
        {/if}

        <div class="body">
          {#if item.body}
            <pre>{item.body}</pre>
          {:else}
            <p class="muted">No review text.</p>
          {/if}
        </div>
      </div>
    {/if}
  </main>
{/if}

<style>
  :global(body) { background-color: #0d1117; }
  .wrap { max-width: 900px; margin: 0 auto; padding: 20px; color: #e6edf3; }
  .topbar { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; }
  .backlink { color: #a5b816; text-decoration: none; }
  .backlink:hover { text-decoration: underline; }

  .muted { color: #8b949e; }
  .error { color: #f89582; }

  .card {
    margin-top: 14px;
    background: #1c1f24;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 16px;
  }

  .row { display: flex; justify-content: space-between; gap: 12px; }
  .title { font-weight: 800; font-size: 1.15rem; }
  .meta { font-size: 0.9rem; color: #8b949e; margin-top: 4px; }
  .right { text-align: right; color: #c9d1d9; }

  .cover {
    margin-top: 12px;
    max-height: 220px;
    border-radius: 10px;
    border: 1px solid #30363d;
  }

  .body { margin-top: 12px; }
  pre {
    margin: 0;
    white-space: pre-wrap;
    word-break: break-word;
    font-family: inherit;
    color: #c9d1d9;
    line-height: 1.5;
  }
</style>
