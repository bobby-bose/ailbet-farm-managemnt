import ast
import json
from flask import Flask, render_template, request, redirect, url_for, session,flash,jsonify
from datetime import datetime, timedelta
import os
import logging
import pymysql
import mysql.connector
import connect
app = Flask(__name__)
logging.basicConfig(filename='app.log', level=logging.ERROR, format='%(asctime)s %(levelname)s %(name)s %(message)s')
app.secret_key = '1234567890#' 
start_date = datetime(2024,10,29)
pasture_growth_rate = 65   
stock_consumption_rate = 14 
db_connection = None
def getCursor():
    try:
        """Gets a new dictionary cursor for the database.
        If necessary, a new database connection is created here and used for all
        subsequent to getCursor()."""
        global db_connection
    
        if db_connection is None or not db_connection.is_connected():
            db_connection = mysql.connector.connect(user=connect.dbuser, \
                password=connect.dbpass, host=connect.dbhost,
                database=connect.dbname, autocommit=True)
        
        cursor = db_connection.cursor(buffered=False)   # returns a list
        # cursor = db_connection.cursor(dictionary=True, buffered=False)  # use a dictionary cursor if you prefer
        return cursor
    except pymysql.MySQLError as e:
        logging.error("ERROR ERROR ERROR ERROR ERROR")
        print(f"Error connecting to database: {e}")


def get_date():
    cursor = getCursor()
    query = "SELECT curr_date FROM curr_date;"  
    cursor.execute(query)
    logging.error("Database cursor.fetchone()")
    result = cursor.fetchone()
    if result is None:
        logging.error("No rows returned from query.")
        return None
    logging.error(result)
    next_day = result[0] 
    d = next_day.strftime("%d") + (
            "th" if 11 <= next_day.day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(next_day.day % 10, "th")
        ) + f" {next_day.strftime('%B %Y')}"
    
    return d

def get_raw_date():
    cursor = getCursor()
    
    query = "SELECT curr_date FROM curr_date;"  
    cursor.execute(query)
    logging.error("Database cursor.fetchone()")
    result = cursor.fetchone()
    if result is None:
        logging.error("No rows returned from query.")
        return None
    logging.error(result)
    next_day = result[0] 
    return next_day

@app.route('/')
def home():
    try:
        date_obj = get_date()
        return render_template("home.html", current_date=date_obj)
    except Exception as e:
        logging.error("Error in home route: %s", str(e), exc_info=True)
        return "An error occurred while processing your request.", 500
    

@app.route('/movenextday')
def move_next_day():
    try:
        # Get the current date from the database
        date_obj = get_date()
        if date_obj is None:
            return "No date found in the database.", 404
        # Increase the day by 24 hours
        raw_date_obj=get_raw_date()
        next_day = raw_date_obj + timedelta(days=1)
        # Update the date in the database
        
        cursor = getCursor()    
        cursor.execute("UPDATE curr_date SET curr_date = %s;", (next_day,))
        db_connection.commit()
        
        
        cursor = getCursor()    
        cursor.execute("SELECT id, area, dm_per_ha,total_dm FROM paddocks;")
        paddocks = cursor.fetchall()
        results = []
        logging.error("PAddocks")
        logging.error("PAddocks")
        logging.error("PAddocks")
        logging.error("PAddocks")
        logging.error(paddocks)
        for paddock in paddocks:
            paddock_id = paddock[0]
            area = paddock[1]
            dm_per_ha = paddock[2]
            total_dm = paddock[3]

            
            # Calculate pasture growth and consumption
            total_dm=total_dm+int(area * pasture_growth_rate*0.01)-int(dm_per_ha * (stock_consumption_rate*0.01))
            dm_per_ha = dm_per_ha+int(dm_per_ha * stock_consumption_rate*0.01)
# Update paddock in the database
            cursor.execute("UPDATE paddocks SET total_dm = %s, dm_per_ha = %s WHERE id = %s;", 
                           (total_dm, dm_per_ha, paddock_id))

            # Store updated information for response
            results.append({
                'paddock_id': paddock_id,
                'total_dm': int(total_dm),
                'dm_per_ha': int(dm_per_ha)
            })

     
        db_connection.commit()
        
        # Format the updated date for display
        formatted_date = next_day.strftime("%d") + (
            "th" if 11 <= next_day.day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(next_day.day % 10, "th")
        ) + f" {next_day.strftime('%B %Y')}"

        return redirect(url_for('paddocks'))
    except Exception as e:
        logging.error("Error in move_next_day route: %s", str(e), exc_info=True)
        return "An error occurred while processing your request.", 500


def execute_sql_file(filepath):
    
    cursor = getCursor()    
    try:
        with open(filepath, 'r') as sql_file:
            sql_commands = sql_file.read().split(';')  # Split commands by semicolon
            for command in sql_commands:
                command = command.strip()
                if command:  # Ignore empty commands
                    cursor.execute(command)
        db_connection.commit()  # Commit the changes
        return True
    except mysql.connector.Error as e:
        print(f"Error executing SQL file: {e}")
        return False
    finally:
        cursor.close()
        

@app.route('/reset')
def reset_database():
    sql_file_path = 'fms-reset.sql'  # Path to your SQL file
    if not os.path.exists(sql_file_path):
        logging.error("SQL FILE NOT FOUND")
        return jsonify({"error": "SQL file not found."}), 404
    success = execute_sql_file(sql_file_path)
    if success:
        logging.error("DATABSE RESET SUCCESSFULLY")
        return redirect(url_for('home'))
    else:
        return jsonify({"error": "Failed to execute SQL commands."}), 500


@app.route('/mobs')
def mobs():
    try:
        date_obj = get_date()
        cursor = getCursor()
#         cursor.execute("""
#           SELECT 
#     mobs.name AS mob_name,
#     paddocks.name AS paddock_name
# FROM 
#     mobs
# INNER JOIN 
#     paddocks ON mobs.paddock_id = paddocks.id
# ORDER BY 
#     mob_name;

#                        """)
        cursor.execute("""
            SELECT 
    s.id AS animal_id, 
    s.mob_id AS mob_id, 
    s.dob AS dob, 
    s.weight AS weight, 
    m.name AS mob_name, 
    p.name AS paddock_name
FROM 
    stock s
JOIN 
    mobs m ON s.mob_id = m.id
JOIN 
    paddocks p ON m.paddock_id = p.id
ORDER BY 
    m.name;
    s.id;                   
        """)
        mobs_data = cursor.fetchall()
        cursor.close()
        grouped_data = {}
        for stock in mobs_data:
            mob_id = stock[1]
            if mob_id not in grouped_data:
                grouped_data[mob_id] = {
                    'animals': [],  # List to hold individual animal data
                    'total_weight': 0,  # To track the total weight
                    'total_animals': 0,  # To track the total count of animals
                    'mob_name':'',
                    'paddock_name':''
                }

            
            grouped_data[mob_id]['animals'].append({
                'mob_name': stock[4],
                'paddock_name': stock[5],
                'animal_id': stock[0],
                'age': 0,
                'weight': stock[3]
            })

            # Update the total weight and total number of animals
            grouped_data[mob_id]['total_weight'] += stock[3]
            grouped_data[mob_id]['total_animals'] += 1
            grouped_data[mob_id]['mob_name'] =stock[4]
            grouped_data[mob_id]['paddock_name'] = stock[5]

        # After categorizing, calculate the average weight for each mob_id
        for mob_id, data in grouped_data.items():
            total_animals = data['total_animals']
            total_weight = data['total_weight']
            if total_animals > 0:
                average_weight = total_weight / total_animals
                average_weight=int(average_weight)
            else:
                average_weight = 0
        each=[]
        combined=[]
        logging.error(grouped_data)
        logging.error("grouped_data")
        logging.error("grouped_data")
        logging.error("grouped_data")
        logging.error("grouped_data")
        logging.error("grouped_data")
        logging.error("grouped_data")
        logging.error("grouped_data")
        logging.error("grouped_data")
        logging.error(grouped_data)
        logging.error(grouped_data)
        logging.error(grouped_data)
        for i in grouped_data:
            logging.error(i)
            logging.error("mob_name")
            logging.error(grouped_data[i]['mob_name'])
            logging.error("paddock_name")
            logging.error(grouped_data[i]['paddock_name'])
            logging.error("total_animals")
            logging.error(grouped_data[i]["total_animals"])
            logging.error("77777777777777777")
            each.append(grouped_data[i]['mob_name'])
            each.append(grouped_data[i]['paddock_name'])
            each.append(grouped_data[i]['total_animals'])
            combined.append(each)
            each=[]

        
#         logging.error(grouped_data)
#         cursor = getCursor()
        
#         cursor.execute("""
#          select mob_id,count(*) as count
# from stock
# group by mob_id
# order by mob_id;
#                        """)
#         mobs_data_two = cursor.fetchall()
#         logging.error(mobs_data) 
#     except Exception as e:
#         logging.error("Error in mobs route: %s", str(e), exc_info=True)
#         mobs_data = []
    finally:
#         cursor.close()
#  # Ensure connection is closed
#     logging.error("combined")
#     each=[]
#     combined=[]
#     for i,j in zip(mobs_data,mobs_data_two):
#         each.append(i[0])
#         each.append(i[1])
#         each.append(j[1])
#         combined.append(each)
#         each=[]
        logging.error("combined")
        logging.error(combined)
    return render_template('mobs.html',combined=combined,current_date=date_obj)
    

# @app.route('/move_mob', methods=['GET', 'POST'])
# def move_mob():
#     date_obj = get_date()            
#     try:
#         if request.method == 'POST':
#             mob_id = request.form.get('mob')  
#             paddock_id = request.form.get('paddock')  
#             logging.error("Pass 1")
#             if mob_id and paddock_id:
#                 cursor = getCursor()
#                 query = "UPDATE mobs SET paddock_id = %s WHERE id = %s;"  
#                 cursor.execute(query, (paddock_id, mob_id))
#                 db_connection.commit()
#                 logging.error("Pass 2")
#                 logging.error("Pass 5")
#                 flash('Mob moved successfully!', 'success')
#             else:
#                 flash('Please select both Mob and Paddock.', 'danger')
#         else:
#             data1 = []
#             data2 = []
#             db_connection.commit() 
#             cursor = getCursor()
#             query = "UPDATE mobs SET paddock_id = %s WHERE id = %s;"  
#             cursor.execute(query, (paddock_id, mob_id))
#             db_connection.commit()
#             cursor = getCursor()
#             query = "SELECT id, name FROM mobs"  
#             cursor.execute(query)
#             data1=cursor.fetchone()
#             db_connection.commit() 
#             cursor = getCursor()
#             query = "SELECT id, name FROM paddocks WHERE id NOT IN (SELECT paddock_id FROM mobs);"
#             cursor.execute(query, (paddock_id, mob_id))
#             data2=cursor.fetchone()
#             db_connection.commit()  
#             return render_template('move_mob.html', mobs=data1, paddocks=data2,current_date=date_obj)
#     except Exception as e:
#         logging.error("Error while fetching or updating data")
#         logging.error(e)
#         flash('An error occurred while moving the mob. Please try again.', 'danger')
    
    




@app.route('/move_mob', methods=['GET', 'POST'])
def move_mob():
    date_obj = get_date()
    try:
        if request.method == 'POST':
            mob_id = request.form.get('mob')
            paddock_id = request.form.get('paddock')
            logging.error("Pass 1")
            if mob_id and paddock_id:
                cursor = getCursor()
                query = "UPDATE mobs SET paddock_id = %s WHERE id = %s;"
                cursor.execute(query, (paddock_id, mob_id))
                db_connection.commit()
                logging.error("Pass 2")
                flash('Mob moved successfully!', 'success')
            else:
                flash('Please select both Mob and Paddock.', 'danger')
        else:
            cursor = getCursor()

            query1 = "SELECT id, name FROM mobs;"
            cursor.execute(query1)
            data1 = cursor.fetchall()
            query2 = "SELECT id, name FROM paddocks WHERE id NOT IN (SELECT paddock_id FROM mobs);"
            cursor.execute(query2)
            data2 = cursor.fetchall()
            return render_template('move_mob.html', mobs=data1, paddocks=data2, current_date=date_obj)
    except Exception as e:
        logging.error("Error while fetching or updating data")
        logging.error(e)
        flash('An error occurred while moving the mob. Please try again.', 'danger')
        return render_template('move_mob.html', mobs=[], paddocks=[], current_date=date_obj)
    return redirect(url_for('paddocks'))










@app.route('/edit_paddock/<int:id>', methods=['GET', 'POST'])
def edit_paddock(id):
    date_obj = get_date()
    try:
        cursor = getCursor()
        

        if request.method == 'POST':
            logging.error("1111111111111")
            # Get the updated data from the form
            paddock_name = request.form['paddock_name']
            paddock_area = float(request.form['paddock_area'])
            paddock_dm = float(request.form['paddock_dm'])
            total_dm=paddock_area*paddock_dm
            logging.error("1111111111111")
            # Update the paddock in the database
            update_query = """
                UPDATE paddocks 
                SET name = %s, area = %s, dm_per_ha = %s, total_dm=%s
                WHERE id = %s
            """
            cursor.execute(update_query, (paddock_name, paddock_area, paddock_dm,total_dm, id))
            connection.commit()
            logging.error("Updated paddock ID %s successfully", id)

            # Redirect back to the paddocks list
            return redirect(url_for('paddocks'))

        else:
            # Retrieve paddock details for the selected ID (GET request)
            cursor.execute("""
                SELECT 
                    id AS paddock_id, 
                    name AS paddock_name, 
                    area AS paddock_area, 
                    dm_per_ha AS paddock_dm, 
                    total_dm AS paddocks_total_dm 
                FROM paddocks 
                WHERE id = %s
            """, (id,))
            paddock = cursor.fetchone()
            logging.error("Paddocks **** %s", paddock)
            logging.error("Paddocks **** %s", paddock)

            logging.error("Paddocks **** %s", paddock)

            logging.error("Paddocks **** %s", paddock)

            if paddock is None:
                logging.error("Paddock with ID %s not found", id)
                return redirect(url_for('paddocks'))  

            paddock_data = {
                'paddock_id': paddock[0],
                'paddock_name': paddock[1],
                'paddock_area': paddock[2],
                'paddock_dm': paddock[3],
                'paddocks_total_dm': paddock[4]
            }

    except Exception as e:
        logging.error("Error in edit_paddock route: %s", str(e), exc_info=True)
        return redirect(url_for('paddocks'))

    finally:
        cursor.close()

    return render_template('edit_paddock.html', paddock=paddock_data, current_date=date_obj)


@app.route('/paddocks')
def paddocks():
    date_obj = get_date()
    try:
        cursor = getCursor()
          
        cursor.execute("""
     SELECT 
    paddocks.id AS paddock_id, 
    paddocks.name AS paddock_name, 
    paddocks.area AS paddock_area,
    paddocks.dm_per_ha AS paddock_dm,
    paddocks.total_dm AS paddocks_total_dm,
    mobs.id AS mob_id,
    mobs.name AS mob_name,
    COALESCE(stock.mob_count, 0) AS mob_count
FROM 
    paddocks
LEFT JOIN 
    mobs ON paddocks.id = mobs.paddock_id
LEFT JOIN 
    (SELECT mob_id, COUNT(*) AS mob_count FROM stock GROUP BY mob_id) AS stock 
    ON mobs.id = stock.mob_id
ORDER BY 
    paddocks.name;

        """)
        paddocks_data = cursor.fetchall()
        logging.info("Fetched paddocks data: %s", paddocks_data)
        paddocks_list = []
        logging.error(paddocks_data)
        logging.error(paddocks_data)
        logging.error(paddocks_data)
        logging.error(paddocks_data)
        for row in paddocks_data:
            paddocks_list.append({
                'paddock_id': row[0],
                'paddock_name': row[1],
                'paddock_area': row[2],
                'paddock_dm': int(row[3]),
                'paddocks_total_dm': int(row[4]),
                'mob_name': row[6] if row[5] is not None else 'Empty',
                'mob_count':row[5]
            })

    except Exception as e:
        logging.error("Error in paddocks route: %s", str(e), exc_info=True)
        paddocks_list = []  

    finally:
        cursor.close()

    return render_template('paddocks.html', paddocks=paddocks_list,current_date=date_obj)






@app.route('/stocks')
def stocks():
    try:
        date_obj = get_date() 
        raw_date=get_raw_date() 
        logging.error("Stocks")
        logging.error(date_obj)
        
        cursor = getCursor()
#         cursor.execute("""
#             SELECT 
#     s.id AS animal_id, 
#     s.mob_id AS mob_id, 
#     s.dob AS dob, 
#     s.weight AS weight, 
#     m.name AS mob_name, 
#     p.name AS paddock_name
# FROM 
#     stock s
# JOIN 
#     mobs m ON s.mob_id = m.id
# JOIN 
#     paddocks p ON m.paddock_id = p.id
# ORDER BY 
#     m.name;
#     s.id;                   
#         """)
        cursor.execute("""
            SELECT 
    s.id AS animal_id, 
    s.mob_id AS mob_id, 
    s.dob AS dob, 
    s.weight AS weight, 
    m.name AS mob_name, 
    p.name AS paddock_name
FROM 
    stock s
JOIN 
    mobs m ON s.mob_id = m.id
JOIN 
    paddocks p ON m.paddock_id = p.id
ORDER BY 
    m.name;
    s.id;                   
        """)
        stocks_data = cursor.fetchall()
        logging.error('Stocks DATA')
        logging.error('Stocks DATA')
        logging.error('Stocks DATA')
        logging.error('Stocks DATA')
        logging.error('Stocks DATA')
        logging.error(stocks_data)
        grouped_data = {}
        for stock in stocks_data:
            mob_id = stock[1]
            if mob_id not in grouped_data:
                grouped_data[mob_id] = {
                    'animals': [],  # List to hold individual animal data
                    'total_weight': 0,  # To track the total weight
                    'total_animals': 0,  # To track the total count of animals
                    'mob_name':'',
                    'paddock_name':''
                }

            animal_age = (raw_date - stock[2]).days / 365
            grouped_data[mob_id]['animals'].append({
                'mob_name': stock[4],
                'paddock_name': stock[5],
                'animal_id': stock[0],
                'age': int(animal_age),
                'weight': stock[3]
            })

            # Update the total weight and total number of animals
            grouped_data[mob_id]['total_weight'] += stock[3]
            grouped_data[mob_id]['total_animals'] += 1
            grouped_data[mob_id]['mob_name'] =stock[4]
            grouped_data[mob_id]['paddock_name'] = stock[5]

        # After categorizing, calculate the average weight for each mob_id
        for mob_id, data in grouped_data.items():
            total_animals = data['total_animals']
            total_weight = data['total_weight']
            if total_animals > 0:
                average_weight = total_weight / total_animals
                average_weight=int(average_weight)
            else:
                average_weight = 0

            # Append the average weight and total animal count to the data
            grouped_data[mob_id]['average_weight'] = average_weight
            # Remove unnecessary 'total_weight' and 'total_animals' keys
            del grouped_data[mob_id]['total_weight']
            # del grouped_data[mob_id]['total_animals']
        logging.error("Organized mobs_dict: %s", grouped_data)
    except Exception as e:
        logging.error("Error in stocks route: %s", str(e), exc_info=True)
        grouped_data = {}
    

    return render_template('stocks.html', mobs=grouped_data, current_date=date_obj)


@app.route('/paddocks/add', methods=['GET', 'POST'])
def add_paddock():
    date_obj=get_date()
    cursor = getCursor()
    
    if request.method == 'POST':
        logging.error("Pass 123232323232332323232")
        try:
            name = request.form['name']
            dm_per_ha = int(request.form['dm_per_ha'])
            area = int(request.form['area'])
            total_dm=dm_per_ha*area
            logging.error("Pass 1")
            cursor.execute("""
                INSERT INTO paddocks (name, dm_per_ha, area,total_dm)
                VALUES (%s, %s, %s, %s)
            """, (name, dm_per_ha, area,total_dm))
            connection.commit()
            logging.error("Pass 2")
            flash('Paddock added successfully!', 'success')
            return redirect(url_for('paddocks'))
        except Exception as e:
            logging.error("Error adding paddock: %s", str(e), exc_info=True)
            flash('An error occurred while adding the paddock.', 'danger')
    logging.error("Pass 3333")
    return render_template('add_paddock.html',current_date=date_obj)


if __name__ == '__main__':
    app.run(debug=True)