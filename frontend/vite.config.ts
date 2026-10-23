/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
export default defineConfig({plugins:[react()],define:{'import.meta.env.VITE_STANDALONE_ACTIONS':JSON.stringify('1')},server:{host:'127.0.0.1',port:5173,strictPort:true,proxy:{'/api/action-demo':process.env.AERIS_ACTION_PROXY??'http://127.0.0.1:8090'}},build:{chunkSizeWarningLimit:1200},test:{globals:true,environment:'jsdom',setupFiles:'./src/test/setup.ts',include:['src/**/*.test.{ts,tsx}']}})
