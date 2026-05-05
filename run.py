from dotenv import load_dotenv
load_dotenv()

from flask_migrate import upgrade
from server import create_app

app = create_app()

with app.app_context():
    upgrade()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5020, debug=True)
