<script lang="ts">
  import { onMount } from 'svelte';
  import { authStore, logout } from '$lib/authStore'; // new
  import type { Book } from '$lib/types';
  import type { UserResponse } from '$lib/types'; // new
  import { writable } from 'svelte/store'
  import BookManager from '$lib/BookManager.svelte';
  import RegisterForm from '$lib/RegisterForm.svelte'
  import LoginForm from '$lib/LoginForm.svelte'; // new

  // "subscribe to the store"
  // automatically update component when store changes (auth)
  let isAuthenticated = false;
  let currentUser: UserResponse | null = null;
  let accessToken: string | null = null;

  // $ prefix is Svelte's shortcut for subscribing to a store
  $: isAuthenticated = $authStore.isAuthenticated;
  $: currentUser = $authStore.user;
  $: accessToken = $authStore.token;

  // RegisterForm stuff
  let showRegistration = false;

  let books: Book[] = [];
  let loading = true;
  let error: string | null = null;

  // state for showing/hiding form
  let showForm = false;
  let bookToEdit: Book | undefined = undefined; // holds book obj to be passed for editing

  // state for card flip
  let flippedBookId: number | null = null;
  function toggleFlip(bookId: number) {
    if (flippedBookId === bookId) {
      flippedBookId = null; // flip back
      // bookToEdit = undefined; // clear edit context
    } else {
      flippedBookId = bookId; // flip forward
      // bookToEdit = book; // set context for editing/deleting
    }
  }

  // Defined function to fetch books, callable from anywhere
  async function fetchBooks() {
    loading = true; // Ensure loading state is set when fetching
    error = null;

    // auth
    if (!accessToken) { // don't fetch if not logged in
      loading = false;
      return;
    }
    try {

      // now, include auth header
      const response = await fetch('/api/books/', {
        headers: { 'Authorization': `Bearer ${accessToken}`}
      });
      
      if (!response.ok) {
        // if token expired, force logout
        if (response.status === 401) logout();
        throw new Error(`API error: ${response.statusText}`);
      }

      books = await response.json();
    } catch (e: any) {
      error = e.message;
    } finally {
      loading = false;
    }
  }

  // initial load & auth change listener
  // runs when component mounts OR when accessToken changes
  $: if (accessToken) {
    fetchBooks();
  } else {
    // clear data when logging out
    books = [];
    loading = false;
  }

  // *redundant now with above code for auth*
  //
  // Use onMount to trigger the initial fetch
  // onMount(() => {
  //   fetchBooks();
  // });
  
  // handler for when BookManager successfully saves a book
  function handleBookSaved(event: CustomEvent<Book>) {
    // add the new book to the top of the list without re-fetching
    books = [event.detail, ...books];
    showForm = false; // close form after saving
  }

  function handleBookUpdated(event: CustomEvent<Book>) {
    // find updated book & replace the old version
    const updatedBook = event.detail;
    books = books.map(book =>
      book.id === updatedBook.id ? updatedBook : book
    );
    flippedBookId = null; // close the box after update
    bookToEdit = undefined;
  }

  function handleBookDeleted(event: CustomEvent<Book>) {
    // filter the deleted book out of the list
    const deletedBook = event.detail;
    books = books.filter(book => book.id !== deletedBook.id);
    flippedBookId = null; // close the box
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
      <span class="welcome-msg">Welcome, {currentUser.username}!</span>
      <button on:click={logout} class="logout-btn">Log Out</button>
    {:else}
      <span class="welcome-msg">Please Log In to continue.</span>
    {/if}
  </div>
  
  {#if isAuthenticated}
    <button on:click={() => { showForm = !showForm; bookToEdit = undefined}}>
      {#if showForm}
        Close Form ☝️
      {:else}
        + Add New Read
      {/if}
    </button>
  
    {#if showForm}
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
                <p class="read-on">Read: {new Date(book.read_on).toLocaleDateString()}</p>
                <p class="click-hint">(Click to see review)</p>
              </div>

          
            <div class="back">
                  <h3>{book.title} Review</h3>
                  <p class="review-text">
                      {#if book.review_text}
                          {book.review_text}
        
                      {:else}
                          No review written yet.
                      {/if}
                  </p>
                  <button on:click|stopPropagation={() => { bookToEdit = book; showForm = false; }} class="edit-btn">
                      Edit Reflection
                  </button>
              </div>
            </div>
          </div>
        {/each}
      </div>
    {/if}
  <!-- ALL THIS FOR REGISTER (below login logic) -->
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
  
  :global(body) {
    background-color: #0d1117;
  }

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

  button:hover {
    background: #2ea043;
  }

    /* AUTH BAR STYLES */
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

  .welcome-msg {
    color: #e6edf3;
    font-size: 0.9em;
  }

  .logout-btn {
    background: #465d7c;
    padding: 8px 15px;
    font-size: 0.9em;
    margin-bottom: 0;
  }

  .logout-btn:hover {
    background: #5a769d; /* lighter hover effect */
  }
  /* end of auth bar styles */


  h1 {
    color: #e6edf3;
  }
  
  .main-container > p {
    margin-bottom: 25px;
    color: #8b949e;
  }

  .book-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 20px;
    margin-top: 20px;
    perspective: 1000px; /* 3D flip effect */
  }

  .book-cover {
    position: absolute;
    bottom: -10px; /* this & below are fixes for book centering */
    right: -10px;
    z-index: 10; /* image sits above the text if they overlap */

    /* sizing & styling */
    max-height: 100px;
    max-width: 70px;
    height: auto;
    width: auto;
    border-radius: 4px;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.5);
  }

  .front {
    justify-content: flex-start;
    align-items: center;
  }

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

  
  .book-box h2, .book-box h3, .book-box p {
      color: inherit; /* forces all child text elements to use the color set above */
  }

  .book-box.is-flipped {
    transform: rotateY(180deg);
  }

  .flipper {
    width: 100%;
    height: 100%;
    position: relative;
    transform-style: preserve-3d;
  }

  .front, .back {
    position: absolute;
    width: 100%;
    height: 100%;
    backface-visibility: hidden; /* hides the back of the element when flipped */
    -webkit-backface-visibility: hidden;
    display: flex;
    flex-direction: column;
  }

  .back {
    transform: rotateY(180deg);
    /* ensures content doesn't force the back element to expand */
    overflow: hidden;
    justify-content: center;
    align-items: center;
  }
  
  .front h2, .back h3 {
    margin-top: 0;
  }

  .thumb-up { color: #238636; }
  .thumb-down { color: #f85149; }
  .thumb-neutral { color: #8b949e; }
  
  .read-on {
    font-size: 0.8em;
    color: #8b949e;
    margin-top: auto;
  }

  .click-hint {
    font-size: 0.75em;
    color: #484f58;
    text-align: center;
    margin-top: 10px;
  }

  .review-text {
    /*  important: enforce scrolling and height */
    max-height: 120px; /* set scrollable height */
    overflow-y: auto; /* display scrollbar when overflow (only on overflow)*/
    
    /* important: text wrapping */
    white-space: pre-wrap; /* formatting and wraps long lines */
    word-break: break-word; /* prevents text from staying on one line */
    
    font-style: italic;
    padding: 5px;
    margin-top: 5px;
    margin-bottom: 5px;
    text-align: left;
  }

  .no-books {
    text-align: center;
    margin-top: 40px;
    color: #8b949e;
  }

  .error {
    color: #f89582;
  }

  .edit-btn {
    padding: 8px 15px;
    background: #465d7c;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.9em;
    margin-top: 10px;
  }

  .small-link {
    font-size: 0.9em;
    color: #8b949e;
    margin-top: 15px;
  }

  .small-link span {
    color: #a5b816;
    cursor: pointer;
    text-decoration: underline;
  }

</style>