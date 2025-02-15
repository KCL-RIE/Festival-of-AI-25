<template>
    <div>
        <div class="bg-image">
            <div class="col px-30 py-30 relative">
                <!-- <div class="relative inline-block">

                    <h1 class="glitchtext absolute -left-0.5 text-gray-400" data-text="ROBOT SOCCER">ROBOT <br> SOCCER
                    </h1>
                    <h1 class="glitchtext relative -left-0.5 text-black" data-text="ROBOT SOCCER">ROBOT <br> SOCCER</h1>

                </div> -->

                <div class="relative inline-block">
                    <span class="glitchtextfront">ROBOT <br> SOCCER</span>
                    <span class="glitchtextback">ROBOT <br> SOCCER</span>
                </div>

                <div class="pt-8">
                    <img src="https://docs.lightburnsoftware.com/legacy/img/QRCode/ExampleCode.png" alt="QR Code"
                        class="h-60 w-60 p-10 bg-white">
                </div>

            </div>

        </div>
    </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Black+Ops+One&display=swap');

.bg-image {
    background-image: linear-gradient(to right, rgba(0, 0, 0, 0.4) 20%, rgba(0, 0, 0, 0)), url('/robotsoccerbg.png');
    background-position: center;
    background-size: cover;
    height: 100vh;
}

.glitchtextback {
    font-family: 'Black Ops One', sans-serif;
    font-size: 12rem;
    position: relative;
    /* Base color */
    display: inline-block;
    color: #ffffff;
    line-height: 9rem;
    letter-spacing: 5px;

}

.glitchtextfront {
    font-family: 'Black Ops One', sans-serif;
    font-size: 12rem;
    position: absolute;
    /* Base color */
    display: inline-block;
    color: #222F75;
    line-height: 9rem;
    letter-spacing: 5px;
    left: -1rem;

}
</style>