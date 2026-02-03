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
  $: currentUser = $authStore.user;

  // like state
  let liked = false;
  let likeBusy = false;

  // comments state
  let comments: CommentItem[] = [];
  let commentsLoading = false;
  let commentsError: string | null = null;

  let newComment = '';
  let commentBusy = false;

  // deletion UI state
  let deletingCommentId: number | null = null;
  let deleteError: string | null = null;

  // --------------------------------------------------
  // "Read more" state (GFG-style, but Svelte-idiomatic)
  // --------------------------------------------------
  const PREVIEW_CHARS = 280; // <-- tweak this
  let expandedComments: Record<number, boolean> = {};

  function isExpanded(id: number) {
    return !!expandedComments[id];
  }

  function toggleExpand(id: number) {
    expandedComments = {
      ...expandedComments,
      [id]: !expandedComments[id]
    };
  }

  function previewText(text: string, limit = PREVIEW_CHARS) {
    const t = (text ?? '').trim();
    if (!t) return { text: '', truncated: false };
    if (t.length <= limit) return { text: t, truncated: false };

    // try to avoid cutting mid-word by backing up to last whitespace
    const slice = t.slice(0, limit);
    const lastSpace = slice.search(/\s(?!.*\s)/); // last whitespace index
    const cutIndex = lastSpace > 40 ? lastSpace : limit; // fallback for no-whitespace strings

    const out = t.slice(0, cutIndex).trimEnd();
    return { text: out, truncated: true };
  }

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

      // reset expansion state per-post
      expandedComments = {};
    } catch (e: any) {
      commentsError = e?.message ?? 'Failed to load comments';
      comments = [];
      expandedComments = {};
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
    deleteError = null;
    deletingCommentId = null;
    expandedComments = {};

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
      expandedComments = {};
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

  async function deleteOneComment(commentId: number) {
    if (!item) return;

    if (!accessToken) {
      alert('Please log in.');
      return;
    }
    if (deletingCommentId) return;

    deletingCommentId = commentId;
    deleteError = null;

    try {
      const res = await fetch(`${API_BASE}/feed/comments/${commentId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });

      if (res.status === 403) {
        throw new Error('You can only delete your own comments.');
      }
      if (!res.ok) {
        throw new Error(`Failed to delete comment (${res.status})`);
      }

      // optimistic local update
      comments = comments.filter((c) => c.id !== commentId);

      // also clean up expanded state
      if (expandedComments[commentId]) {
        const { [commentId]: _, ...rest } = expandedComments;
        expandedComments = rest;
      }

      // keep the visible count in sync
      item.comment_count = Math.max(0, (item.comment_count ?? 0) - 1);
    } catch (e: any) {
      deleteError = e?.message ?? 'Failed to delete comment';
    } finally {
      deletingCommentId = null;
    }
  }

  function canDelete(c: CommentItem) {
    return !!currentUser && c.user?.id === currentUser.id;
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

          {#if deleteError}
            <p class="error">{deleteError}</p>
          {/if}

          {#if commentsLoading}
            <p class="muted">Loading comments…</p>
          {:else if commentsError}
            <p class="error">{commentsError}</p>
          {:else if comments.length === 0}
            <p class="muted">No comments yet.</p>
          {:else}
            <ul class="commentlist">
              
              {#each comments as c (c.id)}
                {@const p = previewText(c.body)}

                <li class="comment">
                  <div class="commentmeta">
                    <span class="commentuser">@{c.user.username ?? 'reader'}</span>
                    {#if c.created_at}
                      <span class="commentdate">• {formatDateTime(c.created_at)}</span>
                    {/if}

                    {#if canDelete(c)}
                      <button
                        class="delbtn"
                        disabled={deletingCommentId === c.id}
                        on:click={() => deleteOneComment(c.id)}
                        aria-label="Delete comment"
                        title="Delete"
                        type="button"
                      >
                        {#if deletingCommentId === c.id} Deleting… {:else} Delete {/if}
                      </button>
                    {/if}
                  </div>

                  <div class="commentbody">
                    {#if isExpanded(c.id)}
                      {c.body}
                    {:else}
                      {p.text}{#if p.truncated}<span class="dots">...</span>{/if}
                    {/if}
                  </div>

                  {#if p.truncated || isExpanded(c.id)}
                    <button
                      class="readmore"
                      type="button"
                      on:click|stopPropagation|preventDefault={() => toggleExpand(c.id)}
                    >
                      {#if isExpanded(c.id)} Read less {:else} Read more... {/if}
                    </button>
                  {/if}
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
              ></textarea>
              <button
                class="btn"
                on:click={submitComment}
                disabled={commentBusy || newComment.trim().length === 0}
                type="button"
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
  .comment {
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 10px;
    overflow: hidden; /* safety: prevents horizontal bleed */
  }
  .commentmeta { font-size: 0.85rem; color: #8b949e; display: flex; gap: 8px; align-items: center; }
  .commentuser { color: #c9d1d9; font-weight: 700; }

  /* Wrap correctly (no scroll, no overflow) */
  .commentbody {
    margin-top: 6px;
    color: #e6edf3;
    white-space: pre-wrap;
    overflow-wrap: anywhere; /* breaks long URLs/tokens */
    word-break: normal;
    max-width: 100%;
  }

  .dots {
    display: inline;
  }

  .readmore {
    margin-top: 4px;
    background: none;
    border: none;
    color: #58a6ff;
    cursor: pointer;
    font-size: 0.85rem;
    padding: 0;
  }
  .readmore:hover { text-decoration: underline; }

  .delbtn {
    margin-left: auto;
    font-size: 0.8rem;
    padding: 2px 8px;
    border-radius: 999px;
    border: 1px solid #30363d;
    background: transparent;
    color: #f89582;
    cursor: pointer;
  }
  .delbtn:hover { filter: brightness(1.1); }
  .delbtn:disabled { opacity: 0.6; cursor: not-allowed; }

  .composer { margin-top: 12px; display: grid; gap: 8px; min-width: 0; }
  textarea {
    width: 100%;
    padding: 10px;
    border-radius: 10px;
    border: 1px solid #30363d;
    background: #0d1117;
    color: #e6edf3;
    resize: vertical;
    box-sizing: border-box;
    min-width: 0;
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
