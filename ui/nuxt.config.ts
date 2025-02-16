// https://nuxt.com/docs/api/configuration/nuxt-config
import tailwindcss from "@tailwindcss/vite";
import { defineNuxtConfig } from "nuxt/config";

export default defineNuxtConfig({
  compatibilityDate: '2024-11-01',
  devtools: { enabled: true },
  css: ['~/assets/css/main.css'],
  modules: ['@pinia/nuxt'],
  vite: {
    plugins: [
      tailwindcss(),
    ],
  },
  routeRules: {
    '/api/**': {
      proxy: process.env.NODE_ENV === "development" ? "http://127.0.0.1:8000/**" : "/**",
    },
  },

})
