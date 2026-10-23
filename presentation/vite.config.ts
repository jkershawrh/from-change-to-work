/// <reference types="vitest/config" />
import {defineConfig} from 'vite'
import react from '@vitejs/plugin-react'
export default defineConfig({base:'/show/',plugins:[react()],resolve:{dedupe:['react','react-dom','three','@react-three/fiber','@react-three/drei']},server:{host:'127.0.0.1',port:5174,strictPort:true,proxy:{'/api/action-demo':'http://127.0.0.1:8090','/models':'http://127.0.0.1:8090','/action-proof.json':'http://127.0.0.1:8090'}},build:{chunkSizeWarningLimit:1300},test:{globals:true,environment:'jsdom',setupFiles:'./src/test/setup.ts',include:['src/**/*.test.{ts,tsx}']}})
