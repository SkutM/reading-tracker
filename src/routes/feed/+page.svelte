<script lang="ts">
  import BootGate from '$lib/components/BootGate.svelte';
  import { auth as authStore } from '$lib/authStore';
  import { BASE } from '$lib/api';

  let bootReady = false;

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
    created_at: string | null;
    like_count: number;
    comment_count: number;
  };

  type FeedResponse = { items: FeedItem[]; next_cursor: string | null };

  //  controls state (UI)
  let sort: SortMode = 'newest';
  let reviewType: ReviewType | 'ALL' = 'ALL';
  let limit = 20;

  //  data state 
  let items: FeedItem[] = [];
  let loading = true;
  let error: string | null = null;
  let nextCursor: string | null = null;

  //  auth state (for likes) 
  let accessToken: string | null = null;
  let isAuthenticated = false;

  $: accessToken = $authStore.token;
  $: isAuthenticated = $authStore.isAuthenticated;

  // per-item like UI state (for the button)
  let liked: Record<number, boolean> = {};
  let liking: Record<number, boolean> = {};

  let likedByMe: Record<number, boolean> = {};

  async function loadLikedForVisibleItems(list: FeedItem[]) {
    if (!accessToken) {
      likedByMe = {};
      liked = {};
      return;
    }

    try {
      const entries = await Promise.all(
        list.map(async (it) => {
          const res = await fetch(`${BASE}/feed/${it.id}/liked`, {
            headers: { Authorization: `Bearer ${accessToken}` },
          });

          if (!res.ok) return [it.id, false] as const;

          const data = (await res.json()) as { liked: boolean };
          return [it.id, !!data.liked] as const;
        })
      );

      const map = Object.fromEntries(entries) as Record<number, boolean>;
      likedByMe = map;
      liked = map;
    } catch {
      likedByMe = {};
      liked = {};
    }
  }

  function buildFeedURL(after: string | null = null) {
    const url = new URL(`${BASE}/feed`);
    url.searchParams.set('sort', sort);
    url.searchParams.set('limit', String(limit));

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

      await loadLikedForVisibleItems(items);
    } catch (e: any) {
      error = e?.message ?? 'Failed to load feed';
    } finally {
      loading = false;
    }
  }

  function applyFilters() {
    items = [];
    nextCursor = null;
    likedByMe = {};
    liked = {};
    loadFeed(null);
  }

  // initial load after BootGate
  $: if (bootReady) loadFeed(null);

  function formatDate(s?: string | null) {
    if (!s) return '';
    const d = new Date(s);
    return isNaN(d.getTime()) ? '' : d.toLocaleDateString();
  }

  async function toggleLike(e: Event, bookId: number) {
    e.preventDefault();
    e.stopPropagation();

    if (!isAuthenticated || !accessToken) {
      alert('Log in to like posts.');
      return;
    }

    liking = { ...liking, [bookId]: true };

    const currentlyLiked = !!liked[bookId];
    const method = currentlyLiked ? 'DELETE' : 'POST';

    try {
      const res = await fetch(`${BASE}/feed/${bookId}/like`, {
        method,
        headers: { Authorization: `Bearer ${accessToken}` },
      });

      if (!res.ok) throw new Error(`Like request failed (${res.status})`);

      const data = await res.json(); // { liked: boolean, like_count: number }

      liked = { ...liked, [bookId]: !!data.liked };
      likedByMe = { ...likedByMe, [bookId]: !!data.liked };

      items = items.map((it) =>
        it.id === bookId ? { ...it, like_count: data.like_count ?? it.like_count } : it
      );
    } catch (err) {
      console.error(err);
      alert('Failed to update like.');
    } finally {
      liking = { ...liking, [bookId]: false };
    }
  }
</script>

{#if !bootReady}
  <BootGate onReady={() => (bootReady = true)} />
{:else}
  <main class="wrap">
    <div class="topbar">
      <h1>Public Feed</h1>
      <a class="backlink" href="/library">My Library</a>
    </div>

    <div class="controls">
      <div class="control">
        <label for="sort">Sort</label>
        <select id="sort" bind:value={sort}>
          <option value="newest">Newest</option>
          <option value="oldest">Oldest</option>
        </select>
      </div>

      <div class="control">
        <label for="reviewType">Review type</label>
        <select id="reviewType" bind:value={reviewType}>
          <option value="ALL">All</option>
          <option value="RECOMMENDED">Recommended</option>
          <option value="NOT_RECOMMENDED">Not recommended</option>
        </select>
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
                      {#if it.review_date}
                        • {formatDate(it.review_date)}
                      {:else if it.created_at}
                        • {formatDate(it.created_at)}
                      {/if}

                      {#if it.review_type}
                        • {it.review_type}
                      {/if}
                    </div>
                  </div>

                  <div class="right">
                    <div>{likedByMe[it.id] ? '❤️' : '🤍'} {it.like_count}</div>
                    <div>💬 {it.comment_count}</div>

                    <button
                      type="button"
                      class="likebtn"
                      disabled={!!liking[it.id]}
                      on:click={(e) => toggleLike(e, it.id)}
                    >
                      {liked[it.id] ? '♥ Liked' : '♡ Like'}
                    </button>
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

  .right { text-align: right; color: #c9d1d9; font-size: 0.95rem; min-width: 120px; }

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
    grid-template-columns: 1fr 1fr 120px auto;
    gap: 10px;
    align-items: end;
  }

  .control label {
    display: block;
    font-size: 0.8rem;
    color: #8b949e;
    margin-bottom: 6px;
  }

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
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%238b949e' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 8px center;
    background-size: 14px;
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
    white-space: nowrap;
  }

  .apply:hover { background: #2ea043; }
  .apply:disabled { opacity: 0.7; cursor: not-allowed; }

  @media (max-width: 860px) {
    .controls {
      grid-template-columns: 1fr 1fr;
    }
    .control.small { max-width: none; }
    .apply { grid-column: span 2; width: 100%; }
  }

  .cardlink {
    display: block;
    color: inherit;
    text-decoration: none;
  }

  .cardlink:hover .card { filter: brightness(1.05); }

  .cardlink:focus-visible {
    outline: 2px solid #a5b816;
    outline-offset: 4px;
    border-radius: 12px;
  }

  .likebtn {
    margin-top: 10px;
    padding: 8px 10px;
    border-radius: 8px;
    border: 1px solid #30363d;
    background: #0d1117;
    color: #e6edf3;
    cursor: pointer;
    width: 100%;
  }

  .likebtn:hover { filter: brightness(1.05); }
  .likebtn:disabled { opacity: 0.6; cursor: not-allowed; }
</style>
