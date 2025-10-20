<script lang="ts">
    import type { Book } from '$lib/types';
    // this below event will be dispatched when a book is
    // successfully saved, allowing the parent comment
    // (+page.svelte) to update the book list
    import { createEventDispatcher } from 'svelte';
    const dispatch = createEventDispatcher();

    // props to handle existing book data for put/delete
    // 'book' prop will be passed from parent (+page.svelte) if
    // we are editing an exisiting book
    export let book: Book | undefined = undefined;
    export let isEditMode: boolean = false;

    // form state variables
    let title = '';
    let author = '';
    let reviewText = '';
    let isRecommended = true; // default = thumbs up
    let message: string | null = null;
    let isError = false;

    $: if (isEditMode && book) {
        title = book.title;
        author = book.author || '';
        reviewText = book.review_text || '';
        isRecommended = book.is_recommended ?? true;
    }

    // uses book?.id to determine POST or PUT
    const endpoint = book ? `/api/books/${book.id}` : '/api/books/';
    const method = book ? 'PUT' : 'POST';

    async function handleSubmit() {
        isError = false;
        message = method === 'POST' ? 'Saving new read...' : 'Updating review...';

        // 1. Build the data obj
        const bookData = {
            title,
            author: author || undefined, // undef = optional (FastAPI)
            review_text: reviewText || undefined,
            is_recommended: isRecommended
        };

        // for POST, all fields must be sent. for PUT, we only
        // send what might change
        // const bodyData = method === 'POST' 
        //   ? bookData 
        //   : {
        //     review_text: reviewText,
        //     is_recommended: isRecommended
        //   };

        try {
            // 2. send POST req to FastAPI via proxy
            const response = await fetch(endpoint, {
              method: method,
              headers: {
                'Content-Type': 'application/json'
              },
              body: JSON.stringify(bookData)
            });

            if (!response.ok) {
                // if error
                const errorData = await response.json();
                throw new Error(errorData.detail || `Failed to ${method === 'POST' ? 'save' : 'update'} book.`);
            }

            const savedBook: Book = await response.json();

            message = `✅ ${savedBook.title} ${method === 'POST' ? 'saved' : 'updated'} successfully!`;
            isError = false;

            // 3. notify parent component
            dispatch('bookUpdated', savedBook); // same event for POST & PUT
        } catch (e: any) {
            message = `❌ Error: ${e.message}`;
            isError = true;
        }
    }

    async function handleDelete() {
      // confirmation dialog for safety
      if (!book || !confirm(`Are you sure you want to delete "${book.title}"? This cannot be undone.`)) {
        return;
      }

      isError = false;
      message = 'Deleting book...'

      try {
        const response = await fetch(`/api/books/${book.id}`, {
          method: 'DELETE'
        });

        if (response.status !== 204) { // delete returns 204
          throw new Error(`Failed to delete book: Server returned ${response.status}`);
        }

        message = `🗑️ Deleted "${book.title}" successfully.`;
        isError = false;

        // notify parent to remove book from list
        dispatch('bookDeleted', book);
      
      } catch (e: any) {
        message = `❌ Error: ${e.message}`;
        isError = true;
      }
    }
</script>

<div class="form-card">
    <h2>Add New Read</h2>
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
  form {
    display: grid;
    gap: 15px;
  }
  label {
    display: grid;
    font-size: 0.9em;
  }
  input[type="text"], textarea {
    padding: 10px;
    border-radius: 5px;
    border: 1px solid #30363d;
    background: #0d1117;
    color: #e6edf3;
    margin-top: 5px;
  }
  .required {
    color: #f89582;
  }
  button {
    padding: 12px;
    background: #238636;
    color: white;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    transition: background-color 0.2s;
  }
  button:disabled {
    background: #30363d;
    cursor: not-allowed;
  }
  .error {
    color: #f89582;
  }
  .message {
    margin-top: 15px;
    padding: 10px;
    border-radius: 5px;
    background: rgba(35, 134, 54, 0.1);
  }
  .rating-toggle p {
    margin-bottom: 5px;
  }
</style>