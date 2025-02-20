<template>
    <div>
        <div class="bg-image">
            <div class="col px-30 py-30 relative">
                <h1 class="text-center">
                    <div class="relative inline-block">
                        <span class="glitchtextfront pulse-effect">LEVEL</span>
                        <span class="glitchtextback pulse-effect">LEVEL</span>
                    </div>
                </h1>
            </div>
            <div class="level-container">
                <span class="pulse-effect easy"></span>
                <span class="pulse-effect normal"></span>
                <span class="pulse-effect hard"></span>
            </div>

        </div>
    </div>
</template>

<style scoped>
.bg-image {
    background-image: url('/levelselectbg.jpg');
    background-color: rgba(0, 0, 0, 0.6);
    background-blend-mode: darken;
    background-position: center;
    background-size: cover;
    height: 100vh;
}

.glitchtextback {
    font-family: 'Black Ops One', sans-serif;
    font-size: 9rem;
    position: relative;
    /* Base color */
    display: inline-block;
    color: #ffffff;
    line-height: 6rem;
    letter-spacing: 5px;

}

.glitchtextfront {
    font-family: 'Black Ops One', sans-serif;
    font-size: 9rem;
    position: absolute;
    /* Base color */
    display: inline-block;
    color: #222F75;
    line-height: 6rem;
    letter-spacing: 5px;
    left: -1rem;

}

.level-container {
    display: flex;
    flex-direction: row;
    width: 80vw;
    margin: 0 auto
}

.easy {
    margin: auto;
    display: flex;
    background-size: 100% 100%;
    width: 350px;
    height: 350px;
    background-image: url('/level-easy.png');
    background-position: center;
}

.normal {
    margin: auto;

    display: flex;
    background-size: 100% 100%;
    width: 350px;
    height: 350px;
    background-image: url('/level-normal.png');
    background-position: center;
}

.hard {
    margin: auto;
    background-size: 100% 100%;
    width: 350px;
    height: 350px;
    display: flex;
    background-image: url('/level-hard.png');
    background-position: center;
}

@keyframes pulse-glitch {

    0%,
    100% {
        transform: scale(1);

    }

    50% {
        transform: scale(1.05);

    }
}

.pulse-effect {
    animation: pulse-glitch 1.5s infinite ease-in-out;
}
</style>