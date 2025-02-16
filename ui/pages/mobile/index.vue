<template>
    <p>tell</p>
</template>

<script>
export default {
    data() {
        return {
            socket: null
        }
    },
    mounted() {

        this.socket = new WebSocket((process.env.NODE_ENV === "development" ? "ws://127.0.0.1:8000" : "wss://your-production-url") + "/ws/mobile");

        this.socket.onopen = () => {
            console.log('Connected to websocket');
        }
        this.socket.onmessage = (e) => {
            console.log(e.data);
        }
        this.socket.onerror = (e) => {
            console.error(e);
        }
        this.socket.onclose = (e) => {
            console.log('Disconnected from websocket');
        }
    }
}
</script>