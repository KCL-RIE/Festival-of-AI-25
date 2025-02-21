<template>
    <div class="container-page">
        <div class="container-screen">
            <div class="game-nav-bar">
                <div class="quit-button">

                </div>
                <div class="score-board">
                    {{ human_score }} : {{ rie_score }}
                </div>
                <div class=timer>
                    <div class="timer-img"></div>
                    <div class="time">
                        {{ time }}
                    </div>
                </div>
            </div>
            <div class="container-game-log">
                <div class="container-game">
                    <div class="field" ref="field">
                        <div
                            v-for="(logPlayer, index) in players"
                            :key="index"
                            class="ball"
                            :style="{
                                backgroundColor: getBallColour(logPlayer),
                                position: 'absolute',
                                left: getBallPosition(logPlayer).x + 'px',
                                top: getBallPosition(logPlayer).y + 'px',
                            }">
                        </div>
                    </div>

                    <div class="container-player">
                    </div>
                </div>
                <div class="container-log">
                    <div v-for="(logItem, index) in logs" :key="index" class="log">
                        <div class="log-colour"
                            :style="getLogColour(logItem)">
                        </div>
                        <div class="log-info">
                            <div class="info-player">
                                {{ logItem.player }}
                            </div>
                            <div class="info-description">
                                {{ logItem.msg }}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: 'game',
    components: {},
    data() {
        return {
            rie_score: 3,
            human_score: 1,
            time: 180,
            logs: [
                { player: "Player 1", msg: "Goal scored by Player 1" },
                { player: "Player 2", msg: "Foul by Player 2" },
                { player: "AI 1", msg: "Goal scored by Player 3" },
                { player: "AI 2", msg: "Goal scored by Player 3" },
            ],

            players: [
                { player: "Player 1", x: 100, y: 200},
                { player: "Player 2", x: 200, y: 250},
                { player: "AI 1", x: 300, y: 150},
                { player: "AI 2", x: 400, y: 300},
            ],
        };
    },

    mounted() {
        this.$nextTick(() => {
            const field = this.$refs.field;
            if (field) {
                this.fieldWidth = field.offsetWidth;
                this.fieldHeight = field.offsetHeight;
            }
        });
    },


    methods: {
        getLogColour(logItem) {
            const colorMap = {
                "Player 1": "#ff5959",
                "Player 2": "#fefe49",
                "AI 1": "#484848",
                "AI 2": "#06ffff",
            };

            return { backgroundColor: colorMap[logItem.player]}
        },

        getBallColour(logPlayer) {
            const colorMap = {
                "Player 1": "#ff5959",
                "Player 2": "#fefe49",
                "AI 1": "#484848",
                "AI 2": "#06ffff",
            };

            return colorMap[logPlayer.player]
        },

        getBallPosition(logPlayer) {
            if (!this.$refs.field) return { x: logPlayer.x, y: logPlayer.y };

            const fieldWidth = this.$refs.field.offsetWidth || 500;
            const fieldHeight = this.$refs.field.offsetHeight || 300;

            let x = Math.min(Math.max(logPlayer.x, 0), fieldWidth - 30);
            let y = Math.min(Math.max(logPlayer.y, 0), fieldHeight - 30);

            console.log("Player Position: ", x, y);
            return { x, y };
        },
    },
};
</script>

<style scoped>
@font-face {
    font-family: 'BlackOpsOne-Regular';
    src: url(/fonts/BlackOpsOne-Regular.ttf);
}

.container-page {
    width: 100vw;
    height: 100vh;
    background-color: #3c6c26;
    font-family: 'BlackOpsOne-Regular';
    color: white;
    background-image: url(/sidepannel.png);
    background-size: contain;
}

.container-screen {
    display: flex;
    flex-direction: column;
    width: 80%;
    height: 100vh;
    margin: auto;
    background-color: #62b040;
}

.game-nav-bar {
    display: flex;
    flex-grow: 1;
    flex-direction: row;
    width: 95%;
    margin: auto;
}

.quit-button {
    display: float;
    background-color: white;
    width: 20pt;
    height: 20pt;
}

.score-board {
    display: flex;
    flex-grow: 13;
    justify-content: center;
    font-size: clamp(10pt, 4vw, 48pt);
}

.timer {
    display: flex;
    flex-direction: row;
    flex-grow: 6;
    justify-content: right;
}

.timer-img {
    display: flex;
    background-image: url(/clock.png);
    background-size: contain;
    background-repeat: no-repeat;
    width: 30px;
    height: 30px;
    margin-top: auto;
    margin-bottom: auto;
    margin-right: 10px;
}

.time {
    margin-top: auto;
    margin-bottom: auto;
    display: flex;
    justify-content: right;
    font-size: clamp(10px, 4vw, 48px);
}

.container-game-log {
    display: flex;
    flex-direction: row;
    flex-grow: 199;
    width: 97.2%;
    margin: auto;
}

.container-game {
    overflow: hidden;
    display: flex;
    flex-direction: column;
    flex-grow: 10;
}

.field {
    display: flex;
    flex-grow: 6.5;
    position: relative;
    background-image: url('/field.png');
    background-repeat: no-repeat;
    background-size: contain;
    justify-content: center;

}

.ball {
    position: absolute;
    border-radius: 80px;
    background-color: #cc3c32;
    width: 30px;
    height: 30px;
    z-index: 2;
}

.container-player {
    display: flex;
    flex-grow: 3;
    flex-direction: row;
    font-size: clamp(10px, 4vw, 25px);
    width: 100%;
    margin-left: 2%;
    background-image: url(/frame-player.png);
    background-size: contain;
    background-repeat: no-repeat;  
    justify-self: center;
    justify-content: center;
    flex-wrap: wrap;
}

.container-log {
    display: flex;
    flex-direction: column;
    flex-grow: 3;
    border-radius: 30px;
    background-color: #61a541;
    margin-left: 3%;
    margin-right: 1%;
    height: 92%;
    color: black;
}

.log {
    display: flex;
    height: 8%;
    border-radius: 30px;
    background-color: #ffffff;
    margin-bottom: 3%;
}

.log-colour {
    display: flex;
    flex-direction: column;
    flex-grow: 1;
    border-radius: 80px;
    background-color: #cc3c32;
    margin-left: 3%;
    margin-right: 3%;
    margin-top: auto;
    margin-bottom: auto;
    height: 60%;
}

.log-info {
    display: flex;
    flex-direction: column;
    flex-grow: 5;
    justify-content: center;
}



</style>


<!-- <template>
    <div class="container-0">
        <div class="container-3">
            <div class="field"></div>
        </div>
        <div class="container-1">
            <div class="game-info">
                <div class="score">
                    <div class=container-info>
                        <div class="title">
                            <h1>score</h1>
                        </div>
                        <div class="board">
                            <div class="team-rie"></div>
                            <div class="number">
                                <span>{{ rie_score }}</span>
                                <span> : </span>
                                <span>{{ human_score }}</span>
                            </div>
                            <div class="team-human"></div>
                        </div>
                    </div>
                </div>

                <div class="panel">
                    <h1>panel</h1>
                    <div class="panel_buttons">
                        <span class="part_button">PART</span>
                        <span class="log_button">LOG</span>
                    </div>
                    <div class="panel_screens">
                        <div class></div>
                    </div>
                </div>

                <div class="player">
                    <h1>player</h1>
                </div>
            </div>
        </div>
    </div>

</template> -->

<!-- 
<script>
export default {
    name: 'game',
    components: {},
    data() {
        return {
            rie_score: 3,
            human_score: 1,
        };
    },
};
</script>

<style scoped>
@font-face {
    font-family: 'BlackOpsOne-Regular';
    src: url(/fonts/BlackOpsOne-Regular.ttf);
}

.container-0 {
    display: flex;
    flex-direction: row;
    font-family: 'BlackOpsOne-Regular';

}

.container-3 {
    display: flex;
    flex-grow: 3;
    object-fit: cover;
    height: 100vh;
    background-color: #63b141;
}

.field {
    background-image: url('/field.jpg');
    background-repeat: no-repeat;
    background-size: contain;
    background-position: center;
    width: 100%;
}

.container-1 {
    display: flex;
    flex-grow: 2;
    flex-direction: column;
    height: 100vh;
}

.game-info {
    display: flex;
    flex-direction: column;
    height: 100vh;
}

.score {
    display: flex;
    flex-grow: 2;
    background-image: url('/scoreboardbg.jpg');
    background-repeat: no-repeat;
    background-size: 100% 100%;
    background-position: top;
    color: white;
    position: relative;
    text-align: center;
}

.container-info {
    display: flex;
    flex-direction: column;
}

.title {
    position: absolute;
    top: 20%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: clamp(10px, 4vw, 48px);
}

.board {
    display: flex;
    flex-grow: 4;
    flex-direction: row;
}

.team-rie {
    background-image: url('/team-rie.png');
    background-size: 100% 100%;
    background-position: bottom;
    position: absolute;
    width: 100px;
    height: 100px;
    top: 60%;
    left: 20%;
    transform: translate(-50%, -50%);
}

.number {
    position: absolute;
    top: 60%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: clamp(10px, 4vw, 48px);
}

.team-human {
    background-image: url('/team_human.png');
    background-size: 100% 100%;
    background-position: bottom;
    position: absolute;
    width: 100px;
    height: 100px;
    top: 60%;
    left: 80%;
    transform: translate(-50%, -50%);
}

.panel {
    display: flex;
    flex-grow: 4;
}

.player {
    display: flex;
    flex-grow: 4;
}

</style> -->