from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import mysql.connector
from mysql.connector import Error,pooling
from werkzeug.security import generate_password_hash, check_password_hash
import pywhatkit as kit
import pyautogui
import threading
import time
import os
 
app = Flask(__name__)
app.secret_key = "8019356963"  # Use a secure, random key for production

DB_CONFIG = {
            'host' : 'marketings.cj6s0ma2yw8j.us-east-1.rds.amazonaws.com',  # Replace with your MySQL Workbench host
            'user':'admin',  # Replace with your MySQL username
            'password':'Ganesh4224',  # Replace with your MySQL password
            'database':'marketing'
}

# MySQL connection configuration
connection_pool = pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=5,  # Define the number of connections in the pool
    **DB_CONFIG
)
def create_connection():
    try:
        connection = connection_pool.get_connection()  # Get a connection from the pool
        return connection
    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return None

@app.route('/')
def home():
    return render_template('index.html')

# Registration route
@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if request.method == 'POST':
        # Get form data
        company_name = request.form['company_name']
        industry = request.form['industry']
        company_size = request.form['company_size']
        country = request.form['country']
        mobile = request.form['phone']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Validate password confirmation
        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'danger')
            return redirect(url_for('registration'))

        # Hash the password
        hashed_password = generate_password_hash(password, method='sha256')

        # Insert company data into the database
        connection = create_connection()
        if connection is None:
            flash("Database connection failed. Please try again.", "danger")
            return redirect(url_for('registration'))
        cursor = connection.cursor()

        try:
            cursor.execute(
                '''INSERT INTO company 
                   (company_name, industry, company_size, country, mobile, email, password) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s)''',
                (company_name, industry, company_size, country, mobile, email, hashed_password)
            )
            connection.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
        except Error as e:
            flash(f"An error occurred: {e}", 'danger')
        finally:
            cursor.close()
            connection.close()

    return render_template('registration.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get form data
        email = request.form['email']
        password = request.form['password']

        # Database connection
        connection = create_connection()
        if connection is None:
            flash("Database connection failed. Please try again.", "danger")
            return redirect(url_for('login'))
        
        cursor = connection.cursor(dictionary=True)

        try:
            # Check if the user exists
            cursor.execute('SELECT * FROM company WHERE email = %s', (email,))
            user = cursor.fetchone()

            if user and check_password_hash(user['password'], password):
                # Store session data
                session['logged_in'] = True
                session['user_id'] = user['id']
                session['user_email'] = user['email']

                flash('Login successful!', 'success')
                # Redirect to the campaign page after successful login
                return redirect(url_for('campaign'))
            else:
                flash('Login failed. Incorrect email or password.', 'danger')
        except mysql.connector.Error as err:
            flash(f"An error occurred: {err}", 'danger')
        finally:
            cursor.close()
            connection.close()

    return render_template('login.html')

@app.route('/campaign', methods=['GET', 'POST'])
def campaign():
    if request.method == 'POST':
        # Get form data
        campaign_name = request.form['campaign-name']
        description = request.form['description']
        service_type = request.form['service-type']  # Free or Paid
        automation_type = request.form['automation-type']  # WhatsApp only

        # Database connection
        connection = create_connection()
        if connection is None:
            flash("Database connection failed. Please try again.", "danger")
            return redirect(url_for('campaign'))  # Redirect to campaign page if connection fails
        
        cursor = connection.cursor()

        try:
            # Insert campaign data into the database
            cursor.execute(
                '''INSERT INTO campaign 
                    (campaign_name, description, service_type, automation_type) 
                    VALUES (%s, %s, %s, %s)''',
                (campaign_name, description, service_type, automation_type)
            )
            connection.commit()
            flash('Campaign created successfully!', 'success')
        except Error as e:
            flash(f"An error occurred: {e}", 'danger')
            return redirect(url_for('campaign'))  # Stay on the campaign page if there's an error
        finally:
            # Ensure cursor and connection are closed properly
            if cursor:
                cursor.close()
            if connection:
                connection.close()

        # Redirect based on WhatsApp service type
        if automation_type == 'whatsapp':
            if service_type == 'free':
                return redirect(url_for('whatsapp_automation', service='free'))
            elif service_type == 'paid':
                return redirect(url_for('whatsapp_automation', service='paid'))
        else:
            return "Invalid Automation Type"
    
    return render_template('campaign.html')

# Global variables to keep track of tasks and threading
task_counter = 0
scheduled_tasks = {}
task_threads = {}
stop_events = {}

@app.route('/whatsapp/<service>', methods=['GET', 'POST'])
def whatsapp_automation(service):
    if service == 'free':
        limit = 5  # Free users can only send messages to 5 members
        flash(f"As a free user, you can only send messages to {limit} members.", 'info')
    
    if service == 'paid':
        flash("As a paid user, you can send messages to an unlimited number of members.", 'info')

    if request.method == 'POST':
        # Get the form data from the WhatsApp messaging form
        message = request.form['message']
        recipients = [recipient.strip() for recipient in request.form['recipients'].split(',')]  # Split and strip whitespace

        # If free, restrict the number of recipients
        if service == 'free' and len(recipients) > limit:
            flash("You can only send messages to 5 members as a free user.", "danger")
            return redirect(url_for('whatsapp_automation', service='free'))

        # Increment task counter for unique ID
        global task_counter
        task_counter += 1
        task_id = task_counter
        scheduled_tasks[task_id] = {"numbers": recipients, "message": message, "status": "pending"}

        # Create a stop event for this task
        stop_event = threading.Event()
        stop_events[task_id] = stop_event

        # Schedule message sending
        thread = threading.Thread(target=lambda: send_whatsapp_messages(recipients, message, task_id, stop_event))
        thread.start()
        task_threads[task_id] = thread  # Store the thread for potential cancellation

        flash('Your message is being sent!', 'success')
        return redirect(url_for('campaign'))  # Redirect back to the campaign page after submission

    # Render the appropriate template based on the service
    if service == 'free':
        return render_template('whatsapp.html', service=service)
    elif service == 'paid':
        return render_template('whatsapp.html', service=service)




def send_whatsapp_messages(numbers, message, task_id, stop_event):
    global scheduled_tasks
    try:
        # Open WhatsApp and send the first message
        kit.sendwhatmsg_instantly(numbers[0], message, 15)  # Opens WhatsApp and sends the first message
        time.sleep(5)  # Wait for the first message to be sent
        
        # Use pyautogui to send messages to the other numbers
        for number in numbers[1:]:
            if stop_event.is_set():  # Stop sending if the event is set
                scheduled_tasks[task_id]['status'] = 'cancelled'
                return

            # Click on the search bar using pyautogui
            pyautogui.click(x=553, y=171)  # Adjust the x and y coordinates to the search bar position
            time.sleep(1)  # Wait for a moment to ensure the click is registered

            # Type the number in the search bar
            pyautogui.typewrite(number)  # Type the contact number
            time.sleep(1)  # Wait for the contact to be found

            # Press 'Enter' to select the contact
            pyautogui.press('enter')
            time.sleep(5)  # Wait for the chat to open

            # Type and send the message
            pyautogui.typewrite(message)  # Type the message
            pyautogui.press('enter')  # Send the message
            time.sleep(1)  # A small delay between sending each message

        # Notify the front-end that the message was sent
        scheduled_tasks[task_id]['status'] = 'sent'
    except Exception as e:
        print(f"Error sending messages: {e}")
        scheduled_tasks[task_id]['status'] = 'failed'  # Update task status in case of failure

@app.route('/schedule', methods=['POST'])
def schedule_message():
    global task_counter
    data = request.get_json()
    numbers = data['numbers']
    message = data['message']
    
    # Increment the task counter for unique ID
    task_counter += 1
    task_id = task_counter

    # Get the scheduled time
    hour, minute = map(int, data['time'].split(':'))
    now = time.localtime()
    send_time = time.mktime((now.tm_year, now.tm_mon, now.tm_mday, hour, minute, 0, 0, 0, -1))

    delay = send_time - time.time()

    if delay < 0:
        return jsonify({"status": "Please set a time in the future."}), 400

    # Schedule the message sending
    scheduled_tasks[task_id] = {"numbers": numbers, "message": message, "status": "pending"}

    # Create a stop event for this task
    stop_event = threading.Event()
    stop_events[task_id] = stop_event

    # Start a thread to wait for the delay and then send the messages
    thread = threading.Thread(target=lambda: wait_and_send(numbers, message, task_id, delay, stop_event))
    thread.start()
    task_threads[task_id] = thread  # Store thread to manage cancellation

    return jsonify({"status": "Message scheduled.", "task_id": task_id})

def wait_and_send(numbers, message, task_id, delay, stop_event):
    start_time = time.time()
    while time.time() - start_time < delay:
        if stop_event.is_set():  # Immediately stop if the event is set
            scheduled_tasks[task_id]['status'] = 'cancelled'
            return
        time.sleep(1)  # Check every second

    send_whatsapp_messages(numbers, message, task_id, stop_event)

@app.route('/cancel', methods=['POST'])
def cancel_message():
    data = request.get_json()
    task_id = data.get('task_id')

    if task_id in scheduled_tasks:
        # Signal the thread responsible for this task to stop
        if task_id in stop_events:
            stop_events[task_id].set()  # Signal the stop event
            task_threads[task_id].join()  # Wait for the thread to stop
            del task_threads[task_id]  # Remove the thread from tracking
            del stop_events[task_id]  # Remove the stop event

        del scheduled_tasks[task_id]
        return jsonify({"status": "Scheduled message cancelled."})
    else:
        return jsonify({"status": "No such task found."}), 404

@app.route('/stop', methods=['POST'])
def stop_all_messages():
    global scheduled_tasks

    # Signal all running threads to stop
    for task_id, stop_event in stop_events.items():
        stop_event.set()  # Signal all threads to stop
    
    # Wait for all threads to complete
    for task_id, thread in task_threads.items():
        thread.join()

    # Clear all threads and stop events
    task_threads.clear()
    stop_events.clear()
    scheduled_tasks.clear()  # Clear all scheduled tasks

    return jsonify({"status": "All scheduled messages stopped."})

@app.route('/events')
def events():
    # Use a simple event-streaming method to notify when messages are sent
    def generate():
        while True:
            time.sleep(1)  # Check every second
            for task_id, task in list(scheduled_tasks.items()):
                if task['status'] == 'sent':
                    yield f"data: {{\"status\": \"message_sent\"}}\n\n"
                    del scheduled_tasks[task_id]  # Remove task once notified

    return app.response_class(generate(), mimetype='text/event-stream')# @app.route('/email', methods=['GET', 'POST'])
# 
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out!', 'success')
    return redirect(url_for('home'))

if __name__ == '__main__':
    print('flask is running')
    app.run(host='0.0.0.0'  , port=5000, debug=True)
