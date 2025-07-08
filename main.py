import psycopg2
import cv2
import numpy as np
import uuid
from flask_socketio import SocketIO, emit, send, join_room, leave_room
from flask_bcrypt import Bcrypt
import random
from datetime import datetime, date, timedelta
from flask import Flask, render_template, request, redirect, url_for, Response, jsonify
from flask import session

app = Flask(__name__)
socketio = SocketIO(app)

app.config['DB_HOST'] = 'localhost'
app.config['DB_NAME'] = 'MyDB1'
app.config['DB_USER'] = 'postgres'
app.config['DB_PASSWORD'] = 'Sam@234'
app.config['SECRET_KEY'] = 'my secret'


def connect_to_db():
    conn = psycopg2.connect(
        host=app.config['DB_HOST'],
        database=app.config['DB_NAME'],
        user=app.config['DB_USER'],
        password=app.config['DB_PASSWORD']
    )
    return conn

@app.route('/')
def index():
    if 'session_id' in session:
        username = get_username_from_session(session['session_id'])
        if username:
            return render_template('dashboard.html', username=username)
    return render_template('home.html')

def create_session(username):
    session_id = str(uuid.uuid4()) 
    expire_date = datetime.now() + timedelta(hours=24)  

    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO sessiondetails (username, sessionid, expiredate) VALUES (%s, %s, %s)", (username, session_id, expire_date))
    conn.commit()
    cur.close()
    conn.close()
    return session_id

def delete_session(session_id):
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM sessiondetails WHERE sessionid = %s", (session_id,))
    conn.commit()
    cur.close()
    conn.close()

@app.route('/get_username')
def username():
    return get_username_from_session(session['session_id'])
def get_username_from_session(session_id):
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute("SELECT username FROM sessiondetails WHERE sessionid = %s AND expiredate > NOW()", (session_id,)) 
    result = cur.fetchone()
    cur.close()
    conn.close()

    if result:
        return result[0] 
    else:
        return None 

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'session_id' in session:
        username = get_username_from_session(session['session_id'])
        print(username)
        if username:
            return redirect('dashboard')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = connect_to_db()
        cur = conn.cursor()
        cur.execute("SELECT password FROM userlogindetails WHERE username = %s", (username,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        if result:
            stored_password = result[0]
            if password == stored_password:
                session_id = create_session(username)
                session['session_id'] = session_id
                return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'session_id' in session:
        username = get_username_from_session(session['session_id'])
        if username:
            return redirect('dashboard')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = connect_to_db()
        cur = conn.cursor()
        try:
            cur.execute('''INSERT INTO userlogindetails (username, password) VALUES \
                        (%s, %s)''', (username, password))
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for('login')) 
        except psycopg2.errors.UniqueViolation:
            return render_template('register.html', error="Username already exists")
    return render_template('register.html') 

@app.route('/dashboard')
def dashboard():
    if 'session_id' in session:
        username = get_username_from_session(session['session_id'])
        if username:
            return render_template('dashboard.html', username=username)
    return redirect(url_for('login'))

@app.route('/profile')
def profile():
    if 'session_id' in session:
        username = get_username_from_session(session['session_id'])
        if username:
            conn = connect_to_db()
            cur = conn.cursor()

            try:
                cur.execute("""
                    SELECT weight, height FROM userpersonaldetails WHERE username = %s
                """, (username,))
                user_data = cur.fetchone()  # Assuming only one row per user

                if user_data:
                    weight, height = user_data
                    bmi = get_bmi(username)  # Assuming you have a function for BMI calculation
                    return render_template('profile.html', username=username, weight=weight, height=height, bmi=bmi)
                else:
                    return render_template('profile.html', username=username, weight=None, height=None, bmi=None)

            except psycopg2.Error as e:
                print("Error fetching data:", e)

            finally:
                cur.close()
                conn.close()

    return redirect(url_for('login'))





def generate_exercise_plan(bmi, num_days):
    exercise_plan = {}
    for day in range(1, num_days + 1):
        day_tasks = {}
        if bmi < 18.5:  # Underweight
            day_tasks['pushups'] = random.randint(10 + day, 20 + day)  # Increasing reps
            day_tasks['squats'] = random.randint(15 + day, 25 + day)  # Increasing reps
            day_tasks['situps'] = random.randint(15 + day, 25 + day)  # Increasing reps
            day_tasks['running'] = f"{random.randint(1, 2)} miles"  # Light jogging
        elif 18.5 <= bmi < 24.9:  # Normal weight
            day_tasks['pushups'] = random.randint(20 + day, 30 + day)  # Increasing reps
            day_tasks['squats'] = random.randint(25 + day, 35 + day)  # Increasing reps
            day_tasks['situps'] = random.randint(25 + day, 35 + day)  # Increasing reps
            day_tasks['running'] = f"{random.randint(2, 3)} miles"  # Moderate running
        elif 25 <= bmi < 29.9:  # Overweight
            day_tasks['pushups'] = random.randint(15 + day, 25 + day)  # Increasing reps
            day_tasks['squats'] = random.randint(20 + day, 30 + day)  # Increasing reps
            day_tasks['situps'] = random.randint(20 + day, 30 + day)  # Increasing reps
            day_tasks['running'] = f"{random.randint(1, 3)} miles"  # Light to moderate running
        else:  # Obese
            day_tasks['pushups'] = random.randint(10 + day, 20 + day)  # Increasing reps
            day_tasks['squats'] = random.randint(15 + day, 25 + day)  # Increasing reps
            day_tasks['situps'] = random.randint(15 + day, 25 + day)  # Increasing reps
            day_tasks['running'] = f"{random.randint(1, 2)} miles"  # Light jogging

        exercise_plan[f'day{day}'] = day_tasks

    return exercise_plan

def store_exercise_plan(username, exercise_plan):
    conn = connect_to_db()
    cur = conn.cursor()

    for day, tasks in exercise_plan.items():
        cur.execute("""
            INSERT INTO exercise_plans (username, day_number, pushups, squats, situps, running)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (username, int(day[3:]), tasks['pushups'], tasks['squats'], tasks['situps'], tasks['running']))

    conn.commit()
    cur.close()
    conn.close()

def get_bmi(username):
    conn = connect_to_db()
    cur = conn.cursor()

    try:
        cur.execute("SELECT height, weight FROM userpersonaldetails WHERE username = %s", (username,))
        user_details = cur.fetchone()

        if user_details:
            height = user_details[0]
            weight = user_details[1]

            # Calculate BMI
            bmi = weight / (height * height)

            cur.close()
            conn.commit()

            return bmi
        else:
            return None  # User details not found

    except psycopg2.Error as e:
        print("Error:", e)
        return None

    finally:
        cur.close()
        conn.close()

def get_exercise_plan(username):
    conn = connect_to_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT day_number, pushups, squats, situps, running, completed
        FROM exercise_plans
        WHERE username = %s
        ORDER BY day_number
    """, (username,))
    rows = cur.fetchall()

    exercise_plan = {}
    for row in rows:
        day_number, pushups, squats, situps, running, completed = row
        exercise_plan[f'day{day_number}'] = {
            'pushups': pushups,
            'squats': squats,
            'situps': situps,
            'running': running,
            'completed': completed
        }

    cur.close()
    conn.close()

    return exercise_plan

@app.route('/practise')
def practise():
    if 'session_id' in session:
        username = get_username_from_session(session['session_id'])
        if username:
            bmi = get_bmi(username)
            if bmi is None:
                message = "Please provide your height and weight in the profile section."
                return render_template('practise.html', username=username, message=message)
            else:
                # Retrieve the exercise plan from the database
                exercise_plan = get_exercise_plan(username)
                if not exercise_plan:
                    # Generate and store a new exercise plan if one doesn't exist
                    exercise_plan = generate_exercise_plan(bmi, 5)
                    store_exercise_plan(username, exercise_plan)

                return render_template('practise.html', username=username, exercise_plan=exercise_plan)
    return redirect(url_for('login'))





def gen_frames():
    camera = cv2.VideoCapture(0)
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/posture')
def posture():
    if 'session_id' in session:
        username = get_username_from_session(session['session_id'])
        if username:
            return render_template('posture.html', username=username)
        return redirect(url_for('login'))
    return redirect(url_for('login'))

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')



@app.route('/userpersonaldetails', methods=['POST'])
def userpersonaldetails():
    if 'session_id' in session:
        username = get_username_from_session(session['session_id'])
        if username:
            weight = request.form['weight']
            height = request.form['height']
            email = request.form['email']
            phone = request.form['phone']
            conn = connect_to_db()
            cur = conn.cursor()

            try:
                cur.execute("""
                    INSERT INTO userpersonaldetails (username, weight, height, email, phone)
                    VALUES (%s, %s, %s, %s, %s)
                """, (username, weight, height, email, phone))
                conn.commit()
                return redirect(url_for('profile'))

            except psycopg2.Error as e:
                print("Error inserting data:", e)
                conn.rollback()

            finally:
                cur.close()
                conn.close()

    return redirect(url_for('login')) 

def store_socket_id(username, socket_id):
    conn = connect_to_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE sockets 
        SET socketid = %s
        WHERE username = %s
    """, (socket_id, username))
    
    if cur.rowcount == 0:
        cur.execute("""
            INSERT INTO sockets (socketid, username) 
            VALUES (%s, %s)
        """, (socket_id, username))

    conn.commit()
    cur.close()
    conn.close()

def get_socket_ids(username):
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute("SELECT socketid FROM sockets WHERE username = %s", (username,))
    results = cur.fetchall()
    cur.close()
    conn.close()
    return [row[0] for row in results]

def delete_socket_id(socket_id):
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM sockets WHERE socketid = %s", (socket_id,))
    conn.commit()
    cur.close()
    conn.close()

@socketio.on('connect')
def on_connect():
    if 'session_id' in session:
        username = get_username_from_session(session['session_id'])
        if username:
            store_socket_id(username, request.sid)
            print('Client connected:', request.sid)

def get_user_sockets_from_db():
    user_sockets = {}
    conn = connect_to_db()
    cur = conn.cursor()

    cur.execute("SELECT username, socketid FROM sockets")
    results = cur.fetchall()

    for row in results:
        username = row[0]
        socketid = row[1]
        if username not in user_sockets:
            user_sockets[username] = []
        user_sockets[username].append(socketid)

    cur.close()
    conn.close()
    return user_sockets


@socketio.on('submit_request')
def submit_request(data):
    recipient_user = data.get('username')
    print(recipient_user)
    user_sockets = get_user_sockets_from_db()
    print(user_sockets)
    print("Recipient username:", recipient_user)
    print("Contents of user_sockets:", user_sockets) 
    print("Condition check:", recipient_user in user_sockets)  
    current_user = get_username_from_session(session['session_id'])
    if recipient_user in user_sockets and recipient_user != current_user:
        room = str(uuid.uuid4()) 
        socket_ids = user_sockets[recipient_user]
        emit('send_user_request', {'room': room}, room=socket_ids) 
        
    else:
        #hmmmm🤔.....
        pass

@socketio.on('disconnect')
def on_disconnect():
    delete_socket_id(request.sid) 
    print('Client disconnected:', request.sid)


@socketio.on('join_call')
def join_call(data):
    username = data['username']
    room = data['room']
    join_room(room)
    emit('user_joined', {'username': username}, room=room)

@socketio.on('offer')
def on_offer(data):
    socketio.emit('offer', data, room=data['room'])

@socketio.on('answer')
def on_answer(data):
    socketio.emit('answer', data, room=data['room'])

@socketio.on('ice_candidate')
def on_ice_candidate(data):
    socketio.emit('ice_candidate', data, room=data['room'])

@app.route('/video_call/<room>')
def video_call(room):
    if 'session_id' in session:
        username = get_username_from_session(session['session_id'])
        if username:
             
            return render_template('video_call.html', room=room)
        
    else:
        return redirect(url_for('login'))





@app.route('/contests')
def contests():
    if 'session_id' in session:
        username = get_username_from_session(session['session_id'])
        if username:
            return render_template('contests.html', username=username)
        return redirect(url_for('login'))
    return redirect(url_for('login'))










@app.route('/logout')
def logout():
    if 'session_id' in session:
        session_id = session['session_id']
        delete_session(session_id)
        session.pop('session_id', None)
    return redirect(url_for('login'))



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080) 