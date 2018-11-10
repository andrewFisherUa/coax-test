from flask import (Flask, Request, url_for, render_template, 
                   request, session, url_for, redirect)
from core import get_calc
import settings


calculator = get_calc()
app = Flask(__name__)
app.secret_key = b'_5?y2L"F418z\n\xec]!/'


# @app.route('/index', methods=['GET', 'POST'])
@app.route('/')
def index():
    context = {'results': session.pop('results', []),
               'error': session.pop('error', [])}
    return render_template('index.html', **context)


@app.route('/calc', methods=['POST'])
def calc():
    try:
        wall_width = float(request.form.get('wall_width', None))
        wall_height = float(request.form.get('wall_height', None))
        session['results'] = calculator.calc(wall_height, wall_width)
    except Exception:
        session['error'] = 'Incorect input, values can be : 1.3, 4, 5.666'
    return redirect(url_for('index'))
