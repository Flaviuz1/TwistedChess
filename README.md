# TwistedChess

Chess with a rotating board. Play online with friends.

## Local development

```bash
pip install -r requirements.txt
# Terminal 1: run server
uvicorn server:app --host 0.0.0.0 --port 5555
# Terminal 2: run game
python main.py
```

## Deploy to Render

1. Push this repo to GitHub.
2. Go to [dashboard.render.com](https://dashboard.render.com) → New → Web Service.
3. Connect your repo, set **Root Directory** to `TwistedChess`.
4. Build: `pip install -r requirements.txt`
5. Start: `uvicorn server:app --host 0.0.0.0 --port $PORT`
6. Deploy. Your server URL will be `https://your-app.onrender.com`.

## Play online

After deploying, set the server URL for the game:

```bash
set TWISTEDCHESS_SERVER=wss://your-app.onrender.com/ws
python main.py
```

Or edit `main.py` and set `SERVER_URL = "wss://your-app.onrender.com/ws"`.

Share the game folder and server URL with friends. They run `python main.py` and join with your room code.