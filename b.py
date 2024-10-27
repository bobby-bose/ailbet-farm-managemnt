from flask import Flask, jsonify
from flask_mysqldb import MySQL

app = Flask(__name__)

# MySQL Configuration
app.config['MYSQL_HOST'] = 'Bobbykbose37.mysql.pythonanywhere-services.com'
app.config['MYSQL_USER'] = 'Bobbykbose37'
app.config['MYSQL_PASSWORD'] = 'Popefrancis@37'
app.config['MYSQL_DB'] = 'Bobbykbose37$default'

mysql = MySQL(app)

@app.route('/test-db', methods=['GET'])
def test_db():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT DATABASE()")  # Simple query to check the connection
        db_name = cursor.fetchone()
        cursor.close()
        return jsonify({"connected": True, "database": db_name[0]})
    except Exception as e:
        return jsonify({"connected": False, "error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)