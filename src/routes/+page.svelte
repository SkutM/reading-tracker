<script lang="ts">
  // import { onMount } from 'svelte'; // not used
  import { auth as authStore, logout } from '$lib/authStore';
  import type { UserResponse } from '$lib/types';
  import type { Book } from '$lib/api';
  import BookManager from '$lib/BookManager.svelte';
  import RegisterForm from '$lib/RegisterForm.svelte';
  import LoginForm from '$lib/LoginForm.svelte';
  import { listBooks } from '$lib/api';

  let isAuthenticated = false;
  let currentUser: UserResponse | null = null;
  let accessToken: string | null = null;

  $: isAuthenticated = $authStore.isAuthenticated;
  $: currentUser = $authStore.user;
  $: accessToken = $authStore.token;

  let showRegistration = false;
  let books: Book[] = [];
  let loading = true;
  let error: string | null = null;

  let showForm = false;
  let bookToEdit: Book | undefined = undefined;

  let flippedBookId: number | null = null;
  function toggleFlip(bookId: number) {
    flippedBookId = flippedBookId === bookId ? null : bookId;
  }

  function formatDateISO(s?: string | null): string {
    if (!s) return "—";
    const d = new Date(s);
    return isNaN(d.getTime()) ? "—" : d.toLocaleDateString();
  }

  async function fetchBooks() {
    loading = true;
    error = null;

    if (!accessToken) {
      loading = false;
      return;
    }
    try {
      books = await listBooks();
    } catch (e: any) {
      if (typeof e?.message === 'string' && e.message.includes('401')) logout();
      error = e?.message ?? 'Failed to load books';
    } finally {
      loading = false;
    }
  }

  $: if (accessToken) {
    fetchBooks();
  } else {
    books = [];
    loading = false;
  }

  function handleBookSaved(event: CustomEvent<Book>) {
    books = [event.detail, ...books];
    showForm = false;
  }

  function handleBookUpdated(event: CustomEvent<Book>) {
    const updatedBook = event.detail;
    books = books.map(b => (b.id === updatedBook.id ? updatedBook : b));
    flippedBookId = null;
    bookToEdit = undefined;
  }

  function handleBookDeleted(event: CustomEvent<Book>) {
    const deletedBook = event.detail;
    books = books.filter(b => b.id !== deletedBook.id);
    flippedBookId = null;
    bookToEdit = undefined;
  }
</script>


<svelte:head>
  <title>Reading Tracker</title>
</svelte:head>

<div class="main-container">
  <h1>Reading Tracker</h1>
  <p>Track and review your favorite books!</p>

  <div class="auth-bar">
    {#if isAuthenticated && currentUser}
      <span class="welcome-msg">
        Welcome, {currentUser.username ?? $authStore.email ?? 'Reader'}!
      </span>
      <button on:click={logout} class="logout-btn">Log Out</button>
    {:else}
      <span class="welcome-msg">Please Log In to continue.</span>
    {/if}
  </div>

  {#if isAuthenticated}
    <button on:click={() => { showForm = !showForm; bookToEdit = undefined }}>
      {#if showForm} Close Form ☝️ {:else} + Add New Read {/if}
    </button>

    {#if showForm}
      <!-- still passing token prop: harmless if your API now reads from localStorage -->
      <BookManager on:bookUpdated={handleBookSaved} accessToken={accessToken} />
    {:else if bookToEdit}
      <BookManager
        book={bookToEdit}
        isEditMode={true}
        on:bookUpdated={handleBookUpdated}
        on:bookDeleted={handleBookDeleted}
        accessToken={accessToken}
      />
    {/if}

    {#if loading}
      <p>Loading your reads...</p>
    {:else if error}
      <p class="error">Error: {error}</p>
    {:else if books.length === 0}
      <p class="no-books">You haven't added any books yet.</p>
    {:else}
      <div class="book-grid">
        {#each books as book (book.id)}
          <div
            class="book-box"
            class:is-flipped={book.id === flippedBookId}
            on:click={() => toggleFlip(book.id)}
            role="button" tabindex="0"
            on:keydown={(e) => { if (e.key === 'Enter' || e.key === ' ') toggleFlip(book.id); }}
          >
            <div class="flipper">
              <div class="front">
                <h2>{book.title}</h2>
                <p>by {book.author || 'Unknown Author'}</p>

                {#if book.cover_image_url}
                  <img src={book.cover_image_url} alt={`Cover for ${book.title}`} class="book-cover" />
                {/if}

                <div class="rating">
                  {#if book.is_recommended === true}
                    <span class="thumb-up">Recommended 👍</span>
                  {:else if book.is_recommended === false}
                    <span class="thumb-down">Not Recommended 👎</span>
                  {:else}
                    <span class="thumb-neutral">No Rating</span>
                  {/if}
                </div>
                <p class="read-on">Read: {formatDateISO(book.read_on)}</p>
                <p class="click-hint">(Click to see review)</p>
              </div>

              <div class="back">
                <h3>{book.title} Review</h3>
                <p class="review-text">
                  {#if book.review_text}{book.review_text}{:else}No review written yet.{/if}
                </p>
                <button
                  on:click|stopPropagation={() => { bookToEdit = book; showForm = false; }}
                  class="edit-btn"
                >
                  Edit Reflection
                </button>
              </div>
            </div>
          </div>
        {/each}
      </div>
    {/if}
  {:else}
    <div class="auth-toggle-container">
      {#if showRegistration}
        <RegisterForm />
        <p class="small-link">
          Already have an account? <span on:click={() => showRegistration = false}>Log In</span>
        </p>
      {:else}
        <LoginForm />
        <p class="small-link">
          Need an account? <span on:click={() => showRegistration = true}>Register Here</span>
        </p>
      {/if}
    </div>
  {/if}
</div>

<style>
  :global(body) { background-color: #0d1117; }

  .main-container {
    max-width: 900px;
    margin: 0 auto;
    padding: 20px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    text-align: center;
  }

  button {
    padding: 12px 20px;
    background: #238636;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    transition: background-color 0.2s;
    font-size: 1em;
    font-weight: 500;
    margin-bottom: 20px;
  }
  button:hover { background: #2ea043; }

  .auth-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background-color: #1c1f24;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 10px 15px;
    margin-bottom: 20px;
  }
  .welcome-msg { color: #e6edf3; font-size: 0.9em; }

  .logout-btn {
    background: #465d7c;
    padding: 8px 15px;
    font-size: 0.9em;
    margin-bottom: 0;
  }
  .logout-btn:hover { background: #5a769d; }

  h1 { color: #e6edf3; }
  .main-container > p { margin-bottom: 25px; color: #8b949e; }

  .book-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 20px;
    margin-top: 20px;
    perspective: 1000px;
  }

  .book-cover {
    position: absolute; bottom: -10px; right: -10px; z-index: 10;
    max-height: 100px; max-width: 70px; height: auto; width: auto;
    border-radius: 4px; box-shadow: 0 2px 5px rgba(0,0,0,0.5);
  }

  .front { justify-content: flex-start; align-items: center; }

  .book-box {
    background-color: #1c1f24;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 20px;
    min-height: 220px;
    cursor: pointer;
    transform-style: preserve-3d;
    transition: transform 0.6s;
    position: relative;
    color: #9cafc0;
  }
  .book-box h2, .book-box h3, .book-box p { color: inherit; }
  .book-box.is-flipped { transform: rotateY(180deg); }

  .flipper { width: 100%; height: 100%; position: relative; transform-style: preserve-3d; }
  .front, .back {
    position: absolute; width: 100%; height: 100%;
    backface-visibility: hidden; -webkit-backface-visibility: hidden;
    display: flex; flex-direction: column;
  }
  .back { transform: rotateY(180deg); overflow: hidden; justify-content: center; align-items: center; }
  .front h2, .back h3 { margin-top: 0; }

  .thumb-up { color: #238636; }
  .thumb-down { color: #f85149; }
  .thumb-neutral { color: #8b949e; }

  .read-on { font-size: 0.8em; color: #8b949e; margin-top: auto; }
  .click-hint { font-size: 0.75em; color: #484f58; text-align: center; margin-top: 10px; }

  .review-text {
    max-height: 120px; overflow-y: auto;
    white-space: pre-wrap; word-break: break-word;
    font-style: italic; padding: 5px; margin: 5px 0; text-align: left;
  }

  .no-books { text-align: center; margin-top: 40px; color: #8b949e; }
  .error { color: #f89582; }

  .edit-btn {
    padding: 8px 15px; background: #465d7c; color: white;
    border: none; border-radius: 4px; cursor: pointer; font-size: 0.9em; margin-top: 10px;
  }

  .small-link { font-size: 0.9em; color: #8b949e; margin-top: 15px; }
  .small-link span { color: #a5b816; cursor: pointer; text-decoration: underline; }
</style>
