from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def index():
    params = {
        'title': 'Онлайн-магазин'
    }
    return render_template('index.html', **params)


def main():
    app.run()


if __name__ == '__main__':
    main()
