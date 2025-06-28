from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

def get_pedidos():
    conn = sqlite3.connect('pedidos.db')
    cursor = conn.cursor()
    cursor.execute("SELECT item, horario FROM pedidos ORDER BY id DESC")
    pedidos = cursor.fetchall()
    conn.close()
    return pedidos

@app.route('/')
def index():
    pedidos = get_pedidos()
    return render_template('index.html', pedidos=pedidos)

if __name__ == '__main__':
    app.run(debug=True)
