<script lang="ts">
  import BootGate from '$lib/components/BootGate.svelte';

  let bootReady = false;

  const API_BASE = import.meta.env.PUBLIC_API_BASE_URL ?? 'http://127.0.0.1:8000';

  type ReviewType = 'RECOMMENDED' | 'NOT_RECOMMENDED' | 'NEUTRAL';
  type SortMode = 'newest' | 'oldest' | 'review_length' | 'review_type';

  type FeedItem = {
    id: number;
    book: {
      id: number;
      title: string;
      author: string | null;
      genre: string | null;
      cover_image_url?: string | null;
    };
    author: { id: number; username: string | null };
    body_preview: string | null;
    review_type: ReviewType | null;
    review_date: string | null;
    visibility: string;
    like_count: number;
    comment_count: number;
  };

  type FeedResponse = { items: FeedItem[]; next_cursor: string | null };

  // ---- Controls state (UI) ----
  let sort: SortMode = 'newest';
  let reviewType: ReviewType | 'ALL' = 'ALL';
  let genre = ''; // free-text (optional)
  let limit = 20;

  // ---- Data state ----
  let items: FeedItem[] = [];
  let loading = true;
  let error: string | null = null;
  let nextCursor: string | null = null;

  function buildFeedURL(after: string | null = null) {
    const url = new URL(`${API_BASE}/feed`);
    url.searchParams.set('sort', sort);
    url.searchParams.set('limit', String(limit));

    if (genre.trim().length > 0) url.searchParams.set('genre', genre.trim());
    if (reviewType !== 'ALL') url.searchParams.set('review_type', reviewType);

    if (after) url.searchParams.set('after', after);

    return url;
  }

  async function loadFeed(after: string | null = null) {
    loading = true;
    error = null;

    try {
      const url = buildFeedURL(after);
      const res = await fetch(url.toString());
      if (!res.ok) throw new Error(`Feed request failed (${res.status})`);

      const data = (await res.json()) as FeedResponse;

      items = after ? [...items, ...(data.items ?? [])] : (data.items ?? []);
      nextCursor = data.next_cursor ?? null;
    } catch (e: any) {
      error = e?.message ?? 'Failed to load feed';
    } finally {
      loading = false;
    }
  }

  function applyFilters() {
    // reset pagination + reload
    items = [];
    nextCursor = null;
    loadFeed(null);
  }

  // initial load after BootGate
  $: if (bootReady) loadFeed(null);

  function formatDate(s?: string | null) {
    if (!s) return '';
    const d = new Date(s);
    return isNaN(d.getTime()) ? '' : d.toLocaleDateString();
  }
</script>


{#if !bootReady}
  <BootGate onReady={() => (bootReady = true)} />
{:else}
  <main class="wrap">
    <div class="topbar">
      <h1>Public Feed</h1>
      <a class="backlink" href="/">← Home</a>
    </div>

    <!-- ✅ Step 2: Controls bar (paste this) -->
    <div class="controls">
      <div class="control">
        <label for="sort">Sort</label>
        <select id="sort" bind:value={sort}>
          <option value="newest">Newest</option>
          <option value="oldest">Oldest</option>
          <option value="review_length">Review length</option>
          <option value="review_type">Review type</option>
        </select>
      </div>

      <div class="control">
        <label for="reviewType">Review type</label>
        <select id="reviewType" bind:value={reviewType}>
          <option value="ALL">All</option>
          <option value="RECOMMENDED">Recommended</option>
          <option value="NEUTRAL">Neutral</option>
          <option value="NOT_RECOMMENDED">Not recommended</option>
        </select>
      </div>

      <div class="control">
        <label for="genre">Genre (optional)</label>
        <input id="genre" type="text" placeholder="e.g. Fantasy" bind:value={genre} />
      </div>

      <div class="control small">
        <label for="limit">Limit</label>
        <select id="limit" bind:value={limit}>
          <option value={10}>10</option>
          <option value={20}>20</option>
          <option value={50}>50</option>
        </select>
      </div>

      <button class="apply" on:click={applyFilters} disabled={loading}>
        Apply
      </button>
    </div>
    <!-- ✅ end controls -->

    {#if loading && items.length === 0}
      <p class="muted">Loading feed…</p>
    {:else if error}
      <p class="error">Error: {error}</p>
    {:else if items.length === 0}
      <p class="muted">No posts yet.</p>
    {:else}
      <ul class="list">
        {#each items as it (it.id)}
            <li>
                <a class="cardlink" href={`/feed/${it.id}`}>
                <div class="card">
                    <div class="row">
                    <div class="left">
                        <div class="title">
                        {it.book.title}{#if it.book.author} — {it.book.author}{/if}
                        </div>

                        <div class="meta">
                        @{it.author.username ?? 'reader'}
                        {#if it.review_date} • {formatDate(it.review_date)}{/if}
                        {#if it.review_type} • {it.review_type}{/if}
                        </div>
                    </div>

                    <div class="right">
                        <div>❤️ {it.like_count}</div>
                        <div>💬 {it.comment_count}</div>
                    </div>
                    </div>

                    {#if it.body_preview}
                    <p class="body">{it.body_preview}</p>
                    {/if}
                </div>
                </a>
            </li>
            {/each}
      </ul>

      {#if nextCursor}
        <button class="more" disabled={loading} on:click={() => loadFeed(nextCursor)}>
          {#if loading} Loading… {:else} Load more {/if}
        </button>
      {/if}
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

  .list { list-style: none; padding: 0; margin: 16px 0 0; display: grid; gap: 12px; }

  .card {
    background: #1c1f24;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 14px;
  }

  .row { display: flex; justify-content: space-between; gap: 12px; }
  .title { font-weight: 700; }
  .meta { font-size: 0.9rem; color: #8b949e; margin-top: 3px; }
  .right { text-align: right; color: #c9d1d9; font-size: 0.95rem; }

  .body { margin: 10px 0 0; color: #c9d1d9; white-space: pre-wrap; }

  .more {
    margin-top: 14px;
    padding: 10px 14px;
    border-radius: 8px;
    border: none;
    cursor: pointer;
    background: #238636;
    color: white;
    font-weight: 600;
  }
  .more:hover { background: #2ea043; }
  .more:disabled { opacity: 0.7; cursor: not-allowed; }

  .controls {
  margin-top: 10px;
  margin-bottom: 10px;
  padding: 12px;
  border: 1px solid #30363d;
  border-radius: 10px;
  background: #1c1f24;
  display: grid;
  grid-template-columns: 1.2fr 1.2fr 2fr 0.8fr auto;
  gap: 10px;
  align-items: end;
}

.controls .control:nth-child(3) {
  max-width: 280px;
}


.control label {
  display: block;
  font-size: 0.8rem;
  color: #8b949e;
  margin-bottom: 6px;
}

.control input,
.control select {
  width: 100%;
  padding: 10px 7px;
  border-radius: 8px;
  border: 1px solid #30363d;
  background: #0d1117;
  color: #e6edf3;
}

.control select {
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
}

.control select {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%238b949e' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 8px center;
  background-size: 14px;
}

.cardlink {
  display: block;
  color: inherit;
  text-decoration: none;
}

.cardlink:hover .card {
  filter: brightness(1.05);
}

.cardlink:focus-visible {
  outline: 2px solid #a5b816;
  outline-offset: 4px;
  border-radius: 12px;
}



.control.small { max-width: 120px; }

.apply {
  padding: 10px 14px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  background: #238636;
  color: white;
  font-weight: 600;
  height: 42px;
}

.apply:hover { background: #2ea043; }
.apply:disabled { opacity: 0.7; cursor: not-allowed; }

@media (max-width: 860px) {
  .controls {
    grid-template-columns: 1fr 1fr;
  }
  .control.small { max-width: none; }
  .apply { grid-column: span 2; }
}

</style>
