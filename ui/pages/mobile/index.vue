<template>
    <div>
        <div v-if="stage === 0">
            <MobilePendingTwoConnection />
        </div>
        <div v-else-if="stage === 1">
            <MobileLevelSelector :userid="userid" @setDifficulty="setDifficulty" />
        </div>
        <div v-else-if="stage === 2">
            <MobileJoyStickController :userid="userid" />
        </div>
    </div>
</template>

<script>

export default {
    data() {
        return {
            socket: null,
            stage: 0,
            userid: null
        }
    },
    methods: {
        setDifficulty(difficulty) {
            console.log("Difficulty set to: ", difficulty);
            this.socket.send(JSON.stringify({
                type: "difficulty",
                difficulty: difficulty
            }));
            this.stage = 2;
        }
    },
    mounted() {
        this.socket = new WebSocket((process.env.NODE_ENV === "development" ? "ws://127.0.0.1:8000" : "wss://your-production-url") + "/ws/mobile");

        this.socket.onmessage = (e) => {
            console.log("Message received by component!: ", e.data);
            const sentjson = JSON.parse(e.data);

            if (!this.userid) {
                this.userid = sentjson.userid;
            }

            if (sentjson.connectedUsers === 2) {
                this.stage = 1;
            }

            if (sentjson.difficulty != "") {
                this.stage = 2;
            }
        }
    }
}
</script>
