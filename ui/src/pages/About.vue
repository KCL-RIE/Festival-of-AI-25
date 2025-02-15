<template>
    <div>
        <h1>About Page</h1>
        <router-link to="/">Go to Home</router-link>

        <div class="text-container">
            <span class="text shadow">Hello World</span>
            <span class="text">Hello World</span>
        </div>


    </div>
</template>

<style>
.text-container {
    position: relative !important;
    display: inline-block !important;
}

.text {
    font-size: 48px;
    font-weight: bold;
    position: absolute !important;
}

.shadow {
    color: gray;
    /* Change to any shadow color */
    left: -5px;
    /* Offset in x direction */
    z-index: -1;
    /* Puts it behind the main text */
}
</style>