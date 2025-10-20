import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
    plugins: [sveltekit()],
    server: {
        // proxy intercepts requests & forwards to a diff location
        proxy: {
            // intercept requests from /api/
            '/api': {
                target: 'http://127.0.0.1:8000',
                // changeOrigin = new host
                changeOrigin: true,
                // rewrite strips /api prefix before sending to the
                // FastAPI -- /api/books/ becomes /books/
                rewrite: (path) => path.replace(/^\/api/, '')
            }
        }
    }
});