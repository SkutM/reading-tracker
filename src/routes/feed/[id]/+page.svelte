<script lang="ts">
  import { page } from '$app/stores';
  import BootGate from '$lib/components/BootGate.svelte';
  import { auth as authStore } from '$lib/authStore';

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

  type CommentItem = {
    id: number;
    book_id: number;
    user: { id: number; username: string | null };
    body: string;
    created_at: string | null;
  };

  let item: FeedDetail | null = null;
  let loading = true;
  let error: string | null = null;

  // auth-derived
  $: accessToken = $authStore.token;

  // like state
  let liked = false;
  let likeBusy = false;

  // comments state
  let comments: CommentItem[] = [];
  let commentsLoading = false;
  let commentsError: string | null = null;

  let newComment = '';
  let commentBusy = false;

  function formatDate(s?: string | null) {
    if (!s) return '';
    const d = new Date(s);
    return isNaN(d.getTime()) ? '' : d.toLocaleDateString();
  }

  function formatDateTime(s?: string | null) {
    if (!s) return '';
    const d = new Date(s);
    return isNaN(d.getTime()) ? '' : d.toLocaleString();
  }

  async function loadLikedStatus(id: string) {
    if (!accessToken) {
      liked = false;
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/feed/${id}/liked`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (!res.ok) return; // don’t hard-fail the page if this fails
      const data = await res.json();
      liked = !!data?.liked;
    } catch {
      // ignore
    }
  }

  async function loadComments(id: string) {
    commentsLoading = true;
    commentsError = null;

    try {
      const res = await fetch(`${API_BASE}/feed/${id}/comments`);
      if (!res.ok) throw new Error(`Comments request failed (${res.status})`);
      const data = await res.json();
      comments = (data.items ?? []) as CommentItem[];
    } catch (e: any) {
      commentsError = e?.message ?? 'Failed to load comments';
      comments = [];
    } finally {
      commentsLoading = false;
    }
  }

  async function loadOne(id: string) {
    loading = true;
    error = null;
    item = null;

    // reset comments per-post while loading
    comments = [];
    commentsError = null;

    try {
      const res = await fetch(`${API_BASE}/feed/${id}`);
      if (!res.ok) throw new Error(`Post request failed (${res.status})`);
      item = (await res.json()) as FeedDetail;

      // once item exists, fetch liked status (if logged in)
      await loadLikedStatus(id);

      // load comments after item is set
      await loadComments(id);
    } catch (e: any) {
      error = e?.message ?? 'Failed to load post';
      item = null;
      comments = [];
    } finally {
      loading = false;
    }
  }

  async function toggleLike() {
    if (!item) return;

    if (!accessToken) {
      alert('Please log in to like.');
      return;
    }
    if (likeBusy) return;

    likeBusy = true;
    const id = String(item.id);

    try {
      const method = liked ? 'DELETE' : 'POST';
      const res = await fetch(`${API_BASE}/feed/${id}/like`, {
        method,
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (!res.ok) throw new Error(`Failed to update like (${res.status})`);

      const data = await res.json();
      liked = !!data?.liked;

      // update count from server (source of truth)
      item.like_count = Number(data?.like_count ?? item.like_count);
    } catch (e: any) {
      alert(e?.message ?? 'Failed to update like');
    } finally {
      likeBusy = false;
    }
  }

  async function submitComment() {
    if (!item) return;

    if (!accessToken) {
      alert('Please log in to comment.');
      return;
    }

    const body = newComment.trim();
    if (!body) return;

    commentBusy = true;
    try {
      const res = await fetch(`${API_BASE}/feed/${item.id}/comments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({ body }),
      });

      if (!res.ok) throw new Error(`Failed to post comment (${res.status})`);
      const data = await res.json();

      const c = data.comment as CommentItem;
      comments = [...comments, c];
      newComment = '';

      // keep the visible count in sync
      item.comment_count = (item.comment_count ?? 0) + 1;
    } catch (e: any) {
      alert(e?.message ?? 'Failed to post comment');
    } finally {
      commentBusy = false;
    }
  }

  // reload when route id changes (and after boot)
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
            <button class="likebtn" disabled={likeBusy} on:click={toggleLike} aria-pressed={liked}>
              {#if liked} ❤️ Liked {:else} 🤍 Like {/if}
            </button>
            <div class="counts">
              <div>❤️ {item.like_count}</div>
              <div>💬 {item.comment_count}</div>
            </div>
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

        <div class="comments">
          <h2>Comments</h2>

          {#if commentsLoading}
            <p class="muted">Loading comments…</p>
          {:else if commentsError}
            <p class="error">{commentsError}</p>
          {:else if comments.length === 0}
            <p class="muted">No comments yet.</p>
          {:else}
            <ul class="commentlist">
              {#each comments as c (c.id)}
                <li class="comment">
                  <div class="commentmeta">
                    <span class="commentuser">@{c.user.username ?? 'reader'}</span>
                    {#if c.created_at}
                      <span class="commentdate">• {formatDateTime(c.created_at)}</span>
                    {/if}
                  </div>
                  <div class="commentbody">{c.body}</div>
                </li>
              {/each}
            </ul>
          {/if}

          {#if accessToken}
            <div class="composer">
              <textarea
                rows="3"
                placeholder="Write a comment…"
                bind:value={newComment}
                disabled={commentBusy}
              />
              <button
                class="btn"
                on:click={submitComment}
                disabled={commentBusy || newComment.trim().length === 0}
              >
                {#if commentBusy} Posting… {:else} Post comment {/if}
              </button>
            </div>
          {:else}
            <p class="muted">Log in to post a comment.</p>
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

  .right { text-align: right; color: #c9d1d9; display: grid; gap: 8px; justify-items: end; }

  .likebtn {
    padding: 8px 10px;
    border-radius: 10px;
    border: 1px solid #30363d;
    background: #0d1117;
    color: #e6edf3;
    cursor: pointer;
    font-weight: 700;
  }
  .likebtn:hover { filter: brightness(1.05); }
  .likebtn:disabled { opacity: 0.7; cursor: not-allowed; }

  .counts { font-size: 0.95rem; }

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

  .comments { margin-top: 18px; padding-top: 14px; border-top: 1px solid #30363d; }
  .comments h2 { margin: 0 0 10px; font-size: 1.05rem; }

  .commentlist { list-style: none; padding: 0; margin: 0; display: grid; gap: 10px; }
  .comment { background: #0d1117; border: 1px solid #30363d; border-radius: 10px; padding: 10px; }
  .commentmeta { font-size: 0.85rem; color: #8b949e; display: flex; gap: 8px; }
  .commentuser { color: #c9d1d9; font-weight: 700; }
  .commentbody { margin-top: 6px; color: #e6edf3; white-space: pre-wrap; }

  .composer { margin-top: 12px; display: grid; gap: 8px; }
  textarea {
    width: 100%;
    padding: 10px;
    border-radius: 10px;
    border: 1px solid #30363d;
    background: #0d1117;
    color: #e6edf3;
    resize: vertical;
  }
  .btn {
    justify-self: end;
    padding: 10px 14px;
    border-radius: 10px;
    border: none;
    cursor: pointer;
    background: #238636;
    color: white;
    font-weight: 700;
  }
  .btn:hover { background: #2ea043; }
  .btn:disabled { opacity: 0.7; cursor: not-allowed; }
</style>
