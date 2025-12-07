import os

import sqlite3 
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date, timedelta, datetime
from helpers import login_required, apology

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

conn = sqlite3.connect("data.db", check_same_thread = False)
conn.row_factory = sqlite3.Row
db = conn.cursor()

@app.route("/")
def dashboard():
    if session.get("user_id"):
        return redirect("/dashboard")

    # If NOT logged in, show the Landing Page
    return render_template("landing.html")

@app.route("/dashboard")
@login_required
def index():
    """Show the user's main dashboard"""
    if session["user_id"]:
        user_id = session["user_id"]
        db.execute("SELECT * FROM habits WHERE user_id = ?", (user_id, ))
        habits_data = db.fetchall()
        # today date
        today_date = date.today().isoformat()
        # day
        day_index = datetime.today().weekday()
        days_map = {
            0: 'monday',
            1: 'tuesday',
            2: 'wednesday',
            3: 'thursday',
            4: 'friday',
            5: 'saturday',
            6: 'sunday'
        }
        current_day = days_map[day_index]
        db.execute(f"SELECT * FROM schedule WHERE user_id = ? AND {current_day} = 1 ORDER BY start_time ASC", (user_id, ))
        schedule_data = db.fetchall()
        for row in habits_data:
            if row["last_progress_date"] != today_date:
                db.execute("UPDATE habits SET current_progress = 0, last_progress_date = ? WHERE id = ? AND user_id = ?", (today_date, row["id"], user_id, ))
        conn.commit()

        return render_template("index.html", habits = habits_data, schedule_data = schedule_data, current_day = current_day)
    else :
        return redirect("/")

@app.route("/register" , methods = ["GET", "POST"])
def register():
    # show form
    if request.method == "GET":
        return render_template("register.html")
    #Register user
    if request.method == "POST":
        email = request.form.get("email_address")
        #check for email
        if not email:
            return apology("Enter Your Email", 400)
        username = request.form.get("username")
        #check for username
        if not username:
            return apology("Enter username", 400)
        db.execute("SELECT * FROM users WHERE username = ?", (username, ))
        check_user = db.fetchall()
        if len(check_user) > 0:
            return apology("Username is already taken", 400)
        password = request.form.get("password")
        #check for password
        if not password:
            return apology("Enter Password", 400)
        confirmation = request.form.get("confirmation")
        #check for confirm password
        if not confirmation:
            return apology("Confirm Your Password", 400)
        if password != confirmation:
            return apology("Password do not match", 400)
        #Generate password hash
        hash_password = generate_password_hash(password)
        # register user in table
        db.execute("INSERT INTO users (username, email, hash) VALUES(?, ?, ?)", (username, email, hash_password, ))
        conn.commit()
        user_id = db.lastrowid

        # login user
        session["user_id"] = user_id
        return redirect("/onboarding")

@app.route("/login", methods = ["POST", "GET"])
def login():
    session.clear()
    if request.method == "GET":
        return render_template("login.html")
    if request.method == "POST":
        email = request.form.get("email")
        # check for email
        if not email:
            return apology("Invalid", 400)
        username = request.form.get("username")
        #check for username
        if not username:
            return apology("Invalid", 400)
        password = request.form.get("password")
        # check for password
        if not password:
            return apology("Invalid", 400)
        #get user data
        db.execute("SELECT * FROM users WHERE username = ?", (username, ))
        rows = db.fetchall()
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            return apology("Invalid", 400)
        # login user
        session["user_id"] = rows[0]["id"]
        db.execute("SELECT * FROM user_goals WHERE user_id = ?", (rows[0]["id"], ))
        data = db.fetchall()
        if not data:
            return redirect("/onboarding")
        return redirect("/dashboard")
    else:
        return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect("/")


@app.route("/delete_account", methods = ["POST", "GET"])
@login_required
def delete_account():
    if request.method == "GET":
        return render_template("delete.html")
    if request.method == "POST":
        user_id = session["user_id"]
        # promp user to enter password
        password = request.form.get("password")
        if not password:
            return apology("Enter Your password", 400)
        db.execute("SELECT * FROM users WHERE id = ?",(user_id, ))
        row = db.fetchall()
        # check if password is correct or not
        if not check_password_hash(row[0]["hash"], password):
            return apology("Wrong Password", 400)
        db.execute("DELETE FROM user_goals WHERE user_id = ?", (user_id, ))
        conn.commit()
        db.execute("DELETE FROM users WHERE id = ?", (user_id, ))
        conn.commit()
        session.clear()
        return redirect("/login")


@app.route("/onboarding", methods = ["POST", "GET"])
@login_required
def onboarding():
    user_id = session["user_id"]
    db.execute("SELECT * FROM users WHERE id = ?", (user_id, ))
    user_data = db.fetchall()
    if not user_data[0]["name"] :

        if request.method == "GET":
            user_id = session["user_id"]
            db.execute("SELECT * FROM goals")
            data = db.fetchall()
            # return the template
            return render_template("onboarding.html", goals = data)
        if request.method == "POST":
            user_id = session["user_id"]
            # get the data
            name_form = request.form.get("name")
            if not name_form:
                return apology("Enter name", 400)
            # capitalize name
            name = name_form.title()
            height = request.form.get("height")
            weight = request.form.get("weight")
            height_num = None
            weight_lb = 0
            if weight and height:
                height_num = float(height)
                weight_num = float(weight)
                unit = request.form.get("weight-unit")
                if unit == "kg":
                    weight_lb = weight_num * 2.20462
            selected_goals = request.form.getlist("goals")
            db.execute("UPDATE users SET name = ?, height_cm = ?, weight_lb = ? WHERE id = ?", (name, height_num, weight_lb, user_id, ))
            conn.commit()
            for goals in selected_goals:
                db.execute("INSERT INTO user_goals (user_id, goals_id) VALUES (?, ?)", (user_id, goals, ))
            conn.commit()
            return redirect("/dashboard")
    else :
        if request.method == "GET":
            # return personalise form
            user_id = session["user_id"]
            db.execute("SELECT * FROM users WHERE id = ?", (user_id, ))
            user_data = db.fetchall()
            db.execute("SELECT * FROM goals")
            data = db.fetchall()
            return render_template("personalise.html", user_data = user_data[0], goals = data)
        if request.method == "POST":
            user_id = session["user_id"]
            # get the data
            name_form = request.form.get("name")
            if not name_form:
                return apology("Enter name", 400)
            # capitalize name
            name = name_form.title()
            height = request.form.get("height")
            weight = request.form.get("weight")
            weight_lb = 0
            if weight and height:
                weight_num = float(weight)
                unit = request.form.get("weight-unit")
                if unit == "kg":
                    weight_lb = weight_num * 2.20462
                else :
                    weight_lb = weight_num
            selected_goals = request.form.getlist("goals")
            db.execute("UPDATE users SET name = ?, height_cm = ?, weight_lb = ? WHERE id = ?", (name, height, weight_lb, user_id, ))
            conn.commit()
            db.execute("DELETE FROM user_goals WHERE user_id = ?", (user_id, ))
            conn.commit()
            for goals in selected_goals:

                db.execute("UPDATE user_goals SET goals_id = ? WHERE user_id = ?", (goals, user_id, ))
            conn.commit()
            return redirect("/dashboard")


@app.route("/account", methods = ["POST", "GET"])
@login_required
def account():
    if request.method == "GET":
        user_id = session["user_id"]
        db.execute("SELECT * FROM users WHERE id = ?", (user_id, ))
        user_data = db.fetchall()
        return render_template("account.html", user= user_data[0])


@app.route("/delete_account", methods =["POST", "GET"])
@login_required
def delete():
    if request.method == "GET":
        user_id = session["user_id"]
        # show the form
        return render_template("delete.html")
    if request.method == "POST":
        user_id = session["user_id"]
        # get the entered password
        password = request.form.get("password")
        user_id = session["user_id"]
        db.execute("SELECT * FROM users WHERE id = ?", (user_id, ))
        user_password = db.fetchall()
        # check if the password is correct or not
        if not check_password_hash(user_password[0]["hash"], password):
            return apology("Wrong Password", 400)
        # delete all the data of that user
        db.execute("DELETE FROM user_goals WHERE user_id = ?", (user_id, ))
        conn.commit()
        db.execute("DELETE FROM habits WHERE user_id = ?", (user_id, ))
        conn.commit()
        db.execute("DELETE FROM schedule WHERE user_id = ?", (user_id, ))
        conn.commit()
        db.execute("DELETE FROM users WHERE id = ?", (user_id, ))
        conn.commit()
        #logout user
        session.clear()
        return redirect("/login")


@app.route("/habit", methods =["POST", "GET"])
@login_required
def habit():
    if request.method == "GET":
        # get user_id
        user_id = session["user_id"]
        # fetch user habits
        db.execute("SELECT * FROM  habits WHERE user_id = ?", (user_id, ))
        habits = db.fetchall()
        return render_template("habit.html", habits = habits)
    if request.method == "POST":
        user_id = session["user_id"]
        habit_name_list = request.form.get("habit_name")
        if not habit_name_list:
            return apology("Invalid Habit Name", 400)
        habit_name = habit_name_list.title()
        habit_amount_list = request.form.get("habit_amount")
        if not habit_amount_list:
            return apology("Invalid Habit Amount", 400)
        habit_amount = int(habit_amount_list)
        habit_unit_list  = request.form.get("habit_unit")
        if not habit_unit_list:
            return apology("Invalid Habit Unit", 400)
        habit_unit = habit_unit_list.title()
        db.execute("INSERT INTO habits (user_id, habit_name, target, unit) VALUES (?, ?, ?, ?)", (user_id, habit_name, habit_amount, habit_unit, ))
        conn.commit()
        return redirect("/habit")

@app.route("/update", methods = ["POST"])
@login_required
def update():
    user_id = session["user_id"]
    # get the habit_id user wants to update
    habit_id = request.form.get("habit_id")
    action = request.form.get("action")
    # fetch data
    db.execute("SELECT * FROM habits WHERE user_id = ? AND id = ?", (user_id, habit_id, ))
    rows = db.fetchall()
    current_progress = int(rows[0]["current_progress"])
    target = int(rows[0]["target"])
    new_progress = current_progress
    # check if user wants to increment
    if action == "increment":
        new_progress = current_progress + 1
    # else user completed
    elif action == "completed":
        new_progress = target
    # get date of today
    today_date = date.today().isoformat()
    new_streak = 0
    current_streak = int(rows[0]["streak"])
    if  new_progress >= target:
        #check if we already marked for today
        if rows[0]["last_completed_date"] != today_date:
            # get date of yesterday
            yest_date = (date.today() - timedelta(days = 1)).isoformat()
            if rows[0]["last_completed_date"] == yest_date:
                new_streak  = current_streak + 1
            else :
                new_streak = 1
            db.execute("UPDATE habits SET streak = ?, last_completed_date = ? WHERE user_id = ? AND id = ?", (new_streak, today_date, user_id, habit_id, ))
            conn.commit()
    db.execute("UPDATE habits SET current_progress = ? WHERE user_id = ? AND id = ?", (new_progress, user_id, habit_id, ))
    conn.commit()
    return redirect("/dashboard")

@app.route("/update_habit", methods = ["GET", "POST"])
@login_required
def update_habit():
    if request.method == "GET":
        user_id = session["user_id"]
        # get which habit users wants to change
        id = request.args.get("habit_id")
        # fetch data for that particular habit
        db.execute("SELECT * FROM habits WHERE user_id = ? AND id = ?", (user_id, id, ))
        habit = db.fetchall()
        return render_template("update_habit.html", habit = habit[0])

    if request.method == "POST":
        user_id = session["user_id"]
        habit_id = request.form.get("habit_id")
        action = request.form.get("action")
        if action == "save_changes":
            habit_name_list = request.form.get("habit_name")
            if not habit_name_list:
                return apology("Enter Your Habit name", 400)
            habit_name = habit_name_list.title()
            habit_target = request.form.get("habit_amount")
            if not habit_target:
                return apology("Enter Target for your habit", 400)
            habit_unit_list = request.form.get("habit_unit")
            if not habit_unit_list:
                return apology("Enter unit for your habit", 400)
            habit_unit = habit_unit_list.title()
            db.execute("UPDATE habits SET habit_name = ?, target = ?, unit = ? WHERE user_id = ? AND id = ?", (habit_name, habit_target, habit_unit, user_id, habit_id, ))
            conn.commit()
            return redirect("/habit")

        if action == "delete":
            db.execute("UPDATE schedule SET habit_id = NULL WHERE habit_id = ?", (habit_id, ))
            conn.commit()
            db.execute("DELETE FROM habits WHERE user_id = ? AND id = ?", (user_id, habit_id, ))
            conn.commit()
            return redirect("/habit")


@app.route("/myroutine", methods = ["POST", "GET"])
@login_required
def myroutine():
    if request.method == "GET":
        user_id = session["user_id"]
        db.execute("SELECT * FROM habits WHERE user_id = ?", (user_id, ))
        habits = db.fetchall()
        db.execute("SELECT * FROM schedule WHERE user_id = ? ORDER BY start_time ASC", (user_id, ))
        schedule = db.fetchall()
        return render_template("schedule.html", habits = habits, schedule_items = schedule)
    if request.method == "POST":
        user_id = session["user_id"]
        # get the data user entered
        activity = request.form.get("activity_name")
        if not activity:
            return apology("Enter Activity name", 400)
        habit = request.form.get("linked-habit_id")
        start_time = request.form.get("start")
        if not start_time:
            return apology("Provide start time", 400)
        end_time = request.form.get("end")
        if not end_time:
            return apology("Provide end time", 400)
        activity_name = activity.title()
        habit_id = 0
        # check if its is linked with the habit or not
        if not habit:
            habit_id = None
        else:
            habit_id = int(habit)
        days = request.form.getlist("days")
        mon = 'mon' in days
        tue = 'tue' in days
        wed = 'wed' in days
        thu = 'thu' in days
        fri = 'fri' in days
        sat = 'sat' in days
        sun = 'sun' in days


        db.execute("INSERT INTO schedule (user_id, habit_id, activity_name, start_time, end_time, monday, tuesday, wednesday, thursday,friday, saturday, sunday) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (user_id, habit_id, activity_name, start_time, end_time, mon, tue, wed, thu, fri, sat, sun, ))
        conn.commit()
        return redirect("/myroutine")

@app.route("/update_schedule", methods = ["POST", "GET"])
@login_required
def update_schedule():
    if request.method == "GET":
        user_id = session["user_id"]
        # get the id for which user wants to change
        id = request.args.get("id")
        db.execute("SELECT * FROM habits WHERE user_id = ?", (user_id, ))
        habits = db.fetchall()
        # get the schedule data for that habit
        db.execute("SELECT * FROM schedule WHERE id = ? AND user_id = ?", (id, user_id, ))
        schedule_data = db.fetchall()
        if len(schedule_data) != 1:
            return apology("Activity not found", 404)

        return render_template("update_schedule.html", schedule_data = schedule_data[0], habits = habits)

    if request.method == "POST":
        user_id = session["user_id"]
        # Get the new data
        activity = request.form.get("activity_name")
        if not activity:
            return apology("Enter Activity name", 400)
        db.execute("SELECT * FROM habits WHERE user_id = ?", (user_id, ))
        habits = db.fetchall()
        # if there is habit related
        id = request.form.get("activity_id")
        action = request.form.get("action")
        # if user wants to update
        if action == "save":

            start_time = request.form.get("start")
            if not start_time:
                return apology("Enter Start Time", 400)
            end_time = request.form.get("end")
            if not end_time:
                return apology("Enter End Time", 400)
            habit_id = request.form.get("linked-habit-id")
            habit = 0
            if not habit_id :
                habit = None
            else:
                habit = int(habit_id)
            days = request.form.getlist("days")
            mon = 'mon' in days
            tue  = 'tue' in days
            wed = 'wed' in days
            thu = 'thu' in days
            fri = 'fri' in days
            sat = 'sat' in days
            sun = 'sun' in days

            db.execute("UPDATE schedule SET habit_id = ?, activity_name = ?, start_time = ?, end_time = ?, monday = ?, tuesday = ?, wednesday= ?, thursday = ?, friday = ?, saturday = ?, sunday = ? WHERE user_id = ? AND id = ?", (habit, activity, start_time, end_time, mon, tue, wed, thu, fri, sat, sun, user_id, id, ))
            conn.commit()
            return redirect("/myroutine")

        if action == "delete":
            db.execute("DELETE FROM schedule WHERE id = ? AND user_id = ?", (id, user_id, ))
            conn.commit()
            return redirect("/myroutine")


@app.route("/progress", methods = ["POST", "GET"])
@login_required
def porgress():
    user_id = session["user_id"]
    db.execute("SELECT * FROM habits WHERE user_id = ?", (user_id, ))
    habits = db.fetchall()
    return render_template("myprogress.html", habits = habits)
