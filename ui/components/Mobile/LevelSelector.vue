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
                    <span class="glitchtextfront pulse-effect">SELECT DIFFICULTY</span>
                    <span class="glitchtextback pulse-effect">SELECT DIFFICULTY</span>
                </div>
            </div>


            <div v-if="userid === 1">
                <div class="level-container flex justify-around pt-10">
                    <div class="card bg-blue-500 w-1/3 mx-2 shadow-lg rounded-lg h-40 cursor-pointer"
                        @click="setDifficulty('easy')">
                        <div class="card-body text-center flex items-center justify-center h-full">
                            <h5 class="card-title text-white text-2xl">EASY</h5>
                        </div>
                    </div>
                    <div class="card bg-blue-500 w-1/3 mx-2 shadow-lg rounded-lg h-40 cursor-pointer"
                        @click="setDifficulty('medium')">
                        <div class="card-body text-center flex items-center justify-center h-full">
                            <h5 class="card-title text-white text-2xl">MEDIUM</h5>
                        </div>
                    </div>
                    <div class="card bg-blue-500 w-1/3 mx-2 shadow-lg rounded-lg h-40 cursor-pointer"
                        @click="setDifficulty('hard')">
                        <div class="card-body text-center flex items-center justify-center h-full">
                            <h5 class="card-title text-white text-2xl">HARD</h5>
                        </div>
                    </div>
                </div>
            </div>
            <div v-else>
                <p class="text-white">
                    THIS UI NEEDS TO BE CLEANED UPP!! only user 1 can pick difficulty; choose on their phone!
                </p>
            </div>

            <p class=" text-white"> THIS UI NEEDS TO BE CLEANED UPP!! you are user {{ userid }}, only user 1 can pick !
            </p>

        </div>
    </div>
</template>

<script>
export default {
    props: ['userid'],
    methods: {
        setDifficulty(difficulty) {
            this.$emit('setDifficulty', difficulty);
        }
    }
}
</script>


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
