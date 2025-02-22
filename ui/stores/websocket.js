// stores/websocket.js
import { defineStore } from 'pinia'

export const useWebSocketStore = defineStore('websocket', {
  state: () => ({
    ws: null,  // WebSocket connection
  }),
  actions: {
    connect(url) {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
        this.ws = new WebSocket(url)
        this.ws.onopen = () => {
          console.log('WebSocket connected')
        }
        this.ws.onclose = () => {
          console.log('WebSocket closed')
        }
      }
    },
    disconnect() {
      if (this.ws) {
        this.ws.close()
      }
    },
  },
})
