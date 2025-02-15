import { createRouter, createWebHistory } from 'vue-router';
import Home from './pages/Home.vue';
import LevelSelector from './pages/TV/LevelSelector.vue';

const routes = [
    { path: '/', component: Home },
    { path: '/tv/levelselector', component: LevelSelector },
];

const router = createRouter({
    history: createWebHistory(),
    routes,
});

export default router;
