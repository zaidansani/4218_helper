from flaskwebgui import FlaskUI
from app.app import app
from waitress import serve

def start_server(**kwargs):
    serve(app, host="127.0.0.1", port=5050)

if __name__ == "__main__":
    FlaskUI(
        server=start_server,
        server_kwargs={"app": app},
        width=1200,
        height=800,
        port=5050
    ).run()
