<template>

    <div class="bg-image">
        <div class="col px-30 pt-10 relative">
            <!-- <div class="relative inline-block">

                    <h1 class="glitchtext absolute -left-0.5 text-gray-400" data-text="ROBOT SOCCER">ROBOT <br> SOCCER
                    </h1>
                    <h1 class="glitchtext relative -left-0.5 text-black" data-text="ROBOT SOCCER">ROBOT <br> SOCCER</h1>

                </div> -->

            <div class="text-center pt-10">
                <div class="relative inline-block">
                    <span class="glitchtextfront pulse-effect">CONNECTED</span>
                    <span class="glitchtextback pulse-effect">CONNECTED</span>
                </div>
            </div>

            <div class="text-center pt-10">
                <div class="relative inline-block">
                    <span class="glitchtextfront pulse-effect">WAITING FOR ANOTHER PLAYER</span>
                    <span class="glitchtextback pulse-effect">WAITING FOR ANOTHER PLAYER</span>
                </div>
            </div>
            <!-- <div class="pt-8 flex items-center">
                    <router-link to="/tv/levelselector">
                        <img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=http://127.0.0.1:8000/"
                            alt="QR Code" class="h-60 w-60 p-10 bg-white">
                    </router-link>
                    <div class="ml-4">
                        <p class="text-white text-3xl">Connected:</p>
                        <p class="text-white text-3xl">{{ message }}</p>
                    </div>
                </div> -->

        </div>

    </div>

</template>


<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Black+Ops+One&display=swap');

.bg-image {
    background-image: url('/levelselectbg.jpg');
    background-color: rgba(0, 0, 0, 0.8);
    background-blend-mode: darken;
    background-position: center;
    background-size: cover;
    height: 100vh;
}

.glitchtextback {
    font-family: 'Black Ops One', sans-serif;
    font-size: 4rem;
    position: relative;
    /* Base color */
    display: inline-block;
    color: #ffffff;
    line-height: 3rem;
    letter-spacing: 5px;

}

.glitchtextfront {
    font-family: 'Black Ops One', sans-serif;
    font-size: 4rem;
    position: absolute;
    /* Base color */
    display: inline-block;
    color: #222F75;
    line-height: 3rem;
    letter-spacing: 5px;
    left: -0.5rem;

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
