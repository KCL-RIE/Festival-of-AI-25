<template>
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
                </div>

                <div class="player">
                    <h1>player</h1>
                </div>
            </div>
        </div>   
    </div>
    
</template>

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

</style>