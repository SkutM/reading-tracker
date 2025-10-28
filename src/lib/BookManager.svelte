<script lang="ts">

  import { createEventDispatcher } from 'svelte';
  import { createBook, updateBook, deleteBook, type Book } from '$lib/api';

  const dispatch = createEventDispatcher<{
    bookUpdated: Book;
    bookDeleted: Book;
  }>();

  export let book: Book | undefined = undefined;
  export let isEditMode: boolean = false;

  // form state variables
  let title = '';
  let author = '';
  let reviewText = '';
  let isRecommended: boolean = true; // default thumbs up
  let message: string | null = null;
  let isError = false;

  // this always checks !! when editing
  $: if (isEditMode && book) {
    title = book.title;
    author = book.author || '';
    reviewText = book.review_text || '';
    isRecommended = book.is_recommended ?? true;
  }

  function buildCreatePayload() {
    return {
      title,
      author: author || undefined,
      review_text: reviewText || undefined,
      is_recommended: isRecommended
    };
  }

  function buildUpdatePayload() {
    return {
      title,
      author: author || undefined,
      review_text: reviewText || undefined,
      is_recommended: isRecommended
    };
  }

  async function handleSubmit() {
    isError = false;
    message = isEditMode ? 'Updating review...' : 'Saving new read...';

    if (!isEditMode && !title.trim()) {
      message = '❌ Title is required.';
      isError = true;
      return;
    }

    try {
      let saved: Book;

      if (isEditMode && book) {
        const payload = buildUpdatePayload();
        saved = await updateBook(book.id, payload);
      } else {
        const payload = buildCreatePayload();
        saved = await createBook(payload);
      }

      message = `✅ "${saved.title}" ${isEditMode ? 'updated' : 'saved'} successfully!`;
      isError = false;

      dispatch('bookUpdated', saved);
    } catch (e: any) {
      message = `❌ Error: ${e?.message ?? 'Request failed'}`;
      isError = true;
    }
  }

  async function handleDelete() {
    if (!book) return;
    if (!confirm(`Are you sure you want to delete "${book.title}"? This cannot be undone.`)) {
      return;
    }

    isError = false;
    message = 'Deleting book...';

    try {
      await deleteBook(book.id); // 204 No Content expected
      message = `🗑️ Deleted "${book.title}" successfully.`;
      isError = false;

      // notify parent to remove it from list
      dispatch('bookDeleted', book);
    } catch (e: any) {
      message = `❌ Error: ${e?.message ?? 'Delete failed'}`;
      isError = true;
    }
  }
</script>

<div class="form-card">
  <h2>{isEditMode ? 'Edit Read' : 'Add New Read'}</h2>

  <form on:submit|preventDefault={handleSubmit}>
    <label>
      Title <span class="required">*</span>
      <input type="text" bind:value={title} required={!isEditMode} />
    </label>

    <label>
      Author
      <input type="text" bind:value={author} />
    </label>

    <label>
      Your Review (Max 500 chars)
      <textarea bind:value={reviewText} maxlength="500"></textarea>
    </label>

    <div class="rating toggle">
      <p>Recommendation:</p>
      <label>
        <input type="radio" bind:group={isRecommended} value={true} /> Thumbs Up 👍
      </label>
      <label>
        <input type="radio" bind:group={isRecommended} value={false} /> Thumbs Down 👎
      </label>
    </div>

    <div class="button-group">
      <button type="submit" disabled={!isEditMode && !title}>
        {isEditMode ? 'Save Changes' : 'Save New Book'}
      </button>

      {#if isEditMode}
        <button type="button" on:click={handleDelete} class="delete-button">
          Delete Book
        </button>
      {/if}
    </div>
  </form>

  {#if message}
    <p class:error={isError} class="message">{message}</p>
  {/if}
</div>

<style>
  .form-card {
    background: #465d7c;
    padding: 25px;
    border-radius: 10px;
    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.3);
    margin: 20px auto;
    max-width: 400px;
  }
  form { display: grid; gap: 15px; }
  label { display: grid; font-size: 0.9em; }
  input[type="text"], textarea {
    padding: 10px;
    border-radius: 5px;
    border: 1px solid #30363d;
    background: #0d1117;
    color: #e6edf3;
    margin-top: 5px;
  }
  .required { color: #f89582; }
  .button-group { display: flex; gap: 8px; }
  button {
    padding: 12px;
    background: #238636;
    color: white;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    transition: background-color 0.2s;
  }
  button:disabled { background: #30363d; cursor: not-allowed; }
  .delete-button { background: #f85149; }
  .error { color: #f89582; }
  .message {
    margin-top: 15px;
    padding: 10px;
    border-radius: 5px;
    background: rgba(35, 134, 54, 0.1);
  }
</style>
