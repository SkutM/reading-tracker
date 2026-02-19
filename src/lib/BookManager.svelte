<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { createBook, updateBook, deleteBook, type Book } from '$lib/api';

  const dispatch = createEventDispatcher<{
    bookUpdated: Book;
    bookDeleted: Book;
  }>();

  export let book: Book | undefined = undefined;
  export let isEditMode: boolean = false;

  let title = '';
  let author = '';
  let reviewText = '';
  let isRecommended: boolean = true;
  let message: string | null = null;
  let isError = false;

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
      is_recommended: isRecommended,
    };
  }

  function buildUpdatePayload() {
    return {
      title,
      author: author || undefined,
      review_text: reviewText || undefined,
      is_recommended: isRecommended,
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
      await deleteBook(book.id);
      message = `🗑️ Deleted "${book.title}" successfully.`;
      isError = false;

      dispatch('bookDeleted', book);
    } catch (e: any) {
      message = `❌ Error: ${e?.message ?? 'Delete failed'}`;
      isError = true;
    }
  }
</script>

<div class="wrap">
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

      <div class="rating">
        <p>Recommendation:</p>

        <div class="radio-row">
          <label class="radio">
            <input type="radio" bind:group={isRecommended} value={true} />
            <span>Thumbs Up 👍</span>
          </label>

          <label class="radio">
            <input type="radio" bind:group={isRecommended} value={false} />
            <span>Thumbs Down 👎</span>
          </label>
        </div>
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
      <p class:err={isError} class="message">{message}</p>
    {/if}
  </div>
</div>

<style>
  .wrap {
    display: flex;
    justify-content: center;
    padding: 20px 0;
  }

  .form-card {
    background: #465d7c;
    padding: 25px;
    border-radius: 10px;
    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.3);
    margin: 20px auto;
    max-width: 520px;
    width: min(520px, 92vw);
    text-align: center;
  }

  h2 {
    margin: 0 0 10px;
  }

  form {
    display: grid;
    gap: 15px;
    justify-items: center;
  }

  label {
    display: grid;
    font-size: 0.9em;
    width: 100%;
    text-align: center;
  }

  input[type='text'],
  textarea {
    width: 100%;
    padding: 10px;
    border-radius: 6px;
    border: 1px solid #30363d;
    background: #0d1117;
    color: #e6edf3;
    margin-top: 6px;
    box-sizing: border-box;
  }

  textarea {
    min-height: 110px;
    resize: vertical;
  }

  .required {
    color: #f89582;
  }

  .rating {
    width: 100%;
    text-align: center;
    display: grid;
    gap: 10px;
    justify-items: center;
    margin-top: 6px;
  }

  .rating p {
    margin: 0;
    font-weight: 600;
  }

  .radio-row {
    display: grid;
    gap: 10px;
    justify-items: start;
    width: fit-content;
    margin: 0 auto;
  }

  .radio {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    font-size: 1rem;
  }

  .radio input {
    margin: 0;
  }

  .button-group {
    display: flex;
    gap: 10px;
    justify-content: center;
    width: 100%;
    margin-top: 8px;
    flex-wrap: wrap;
  }

  button {
    padding: 12px 14px;
    background: #238636;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    transition: background-color 0.2s;
    min-width: 160px;
  }

  button:hover {
    background: #2ea043;
  }

  button:disabled {
    background: #30363d;
    cursor: not-allowed;
  }

  .delete-button {
    background: #f85149;
  }

  .delete-button:hover {
    filter: brightness(1.05);
  }

  .message {
    margin-top: 15px;
    padding: 10px;
    border-radius: 6px;
    background: rgba(35, 134, 54, 0.1);
    text-align: center;
  }

  .err {
    color: #f89582;
  }
</style>
