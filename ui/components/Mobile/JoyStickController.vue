<template>
    <div class="flex flex-col items-center justify-center h-screen touch-none bg-black">
        <div class="flex w-full h-1/2">
            <div class="flex items-center justify-center w-1/2 h-full">
                <VueJoystick :size="300" :baseColor="'#999999'" :stickColor="'#666666'" :baseLineWidth="5"
                    :stickLineWidth="5" @move="handleJoystickMove" @start="handleJoystickStart"
                    @end="handleJoystickEnd">
                </VueJoystick>
            </div>
            <div class="flex flex-wrap items-center justify-center w-1/2">
                <button v-for="button in buttons" :key="button.label"
                    class="w-32 h-32 m-4 text-4xl font-bold border-none rounded-full bg-blue-600 text-white cursor-pointer select-none touch-manipulation active:bg-blue-700"
                    @touchstart="handleButtonPress(button.label)" @touchend="handleButtonRelease(button.label)"
                    @mousedown="handleButtonPress(button.label)" @mouseup="handleButtonRelease(button.label)">
                    {{ button.label }}
                </button>
            </div>
        </div>
        <div class="text-center font-mono mt-8">
            <p>Joystick: {{ joystickOutput }}</p>
            <p>Buttons: {{ buttonsOutput }}</p>
        </div>
    </div>
</template>

<script>
import { Joystick } from 'vue-joystick-component';
export default {
    props: ['userid'],
    components: {
        VueJoystick: Joystick
    },
    data() {
        return {
            joystickOutput: 'Idle',
            buttonsOutput: [],
            robotcontrolsocket: null,
            buttons: [
                { label: 'A' },
                { label: 'B' },
                { label: 'X' },
                { label: 'Y' },
            ]
        };
    },
    methods: {
        handleJoystickMove(data) {
            const { x, y } = data;
            this.joystickOutput = `x: ${x.toFixed(2)}, y: ${y.toFixed(2)}`;
        },
        handleJoystickStart() {
            this.joystickOutput = 'Started';
        },
        handleJoystickEnd() {
            this.joystickOutput = 'Ended';
        },
        handleButtonPress(label) {
            this.buttonsOutput.push(label);
        },
        handleButtonRelease(label) {
            const index = this.buttonsOutput.indexOf(label);
            if (index !== -1) {
                this.buttonsOutput.splice(index, 1);
            }
        }
    },
    watch: {
        buttonsOutput(newVal) {
            this.robotcontrolsocket.send(JSON.stringify({
                type: 'buttons',
                userid: this.userid,
                buttons: newVal
            }));
        },
        joystickOutput(newVal) {
            this.robotcontrolsocket.send(JSON.stringify({
                type: 'joystick',
                userid: this.userid,
                joystick: newVal
            }));
        }
    },
    mounted() {

        this.robotcontrolsocket = new WebSocket((process.env.NODE_ENV === "development" ? "ws://127.0.0.1:8000" : "wss://your-production-url") + "/ws/robotcontrol");

        this.robotcontrolsocket.onopen = () => {
            console.log('Connected to websocket');
        }

        document.body.addEventListener(
            'touchmove',
            (e) => {
                e.preventDefault();
            },
            { passive: false }
        );
    }
};
</script>

<style scoped>
/* Removed CSS as it is now replaced with Tailwind classes */
</style>
