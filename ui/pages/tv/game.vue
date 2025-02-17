<template>
    <div class="container-0">
        <div class="container-3">
            <div class="field"></div>
        </div>
        <div class="container-1">
            <div class="game-info">
                <div class="score">
                    <div class="title">
                        <h1>score</h1>
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

.title {
    position: absolute;
    top: 20%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: clamp(10px, 4vw, 48px);
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