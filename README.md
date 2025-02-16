# KCL-RIE Festival of AI 2025
## Project
The project for 2025 aims to develop a football game where two players each control two robots, and the AI controls the other two robots. The objective is to score goals against the opposing team.

A TV screen is used as a heads-up display, mobile phones are used as controllers and an overhead camera is connected to the server

## Code
This repo contains code for running a backend FastAPI server and frontend Vue.js server.

This repo structure is based off a design by Diogo Miguel, view his blog post [here](https://dimmaski.com/serve-vue-fastapi/) and the source repo [here](https://github.com/dimmaski/fastapi-vue).


npm run dev --prefix ui & uvicorn api.main:app --reload

<!-- ### Serve Backend locally

```sh
cd api

# setup virtualenv
virtualenv -p python3.10 -v venv

# activate the source directory
source venv/bin/activate

pip install -r requirements.txt

# serve
uvicorn main:app --reload
```

### Serve Frontend locally
```sh
cd ui

# install dependencies
npm run install

# serve
npm run watch
```

### Run FE and BE in hot-reload mode
Run from the parent directory.
```
npm run watch --prefix ui & uvicorn api.main:app --reload && fg
``` -->