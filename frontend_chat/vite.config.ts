import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react' // или vue(), или svelte()

// https://vitejs.dev/config/
export default defineConfig({
  // --- ДОБАВЬТЕ ЭТУ СТРОКУ ---
  base: '/chat/', 
  // -------------------------
  
  plugins: [react()],
  // Если у вас не работает hot-reload в Docker, добавьте это:
  server: {
    host: true,
    strictPort: true,
    port: 5174, // или любой другой порт, который вы используете для разработки
    watch: {
      usePolling: true
    }
  }
})