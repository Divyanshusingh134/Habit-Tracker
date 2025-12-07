# Habit Tracker
#### Video Demo: [YouTube](https://youtu.be/3f8_n14KA18)

#### Description:
Habit Tracker is a dynamic web application designed to help users build consistency and improve their daily productivity. The application serves two main purposes: habit formation and schedule management.It allows users to define and track specific daily goals—such as "drink 8 glasses of water" or "study for 8 hours"—providing a visual record of their progress over time. Additionally, the application includes a scheduling feature that helps users organize their day, aiming to solve the common problem of procrastination by encouraging punctuality and structured workflows.I chose to build this project because I wanted to create a tool that I could actually use in my daily life as a student. Managing time between classes and self-study can be difficult, so I wanted to challenge myself to build a full-stack application that solves a real-world problem using the Flask framework and SQL.

### Key Features

* **User Authentication:** Secure registration and login functionality using password hashing (`werkzeug.security`).
* **Onboarding System:** A personalised setup wizard that captures user details (name, height, weight) and specific goals to tailor the experience.
* **Habit Management:** Users can create custom habits with specific targets and units (e.g., "Water" -> 8 "glasses").
* **Daily Dashboard:** A dynamic view that resets daily progress automatically and shows the current day's schedule.
* **Streak Tracking:** Logic to track consistency. The app calculates streaks based on the `last_completed_date` to motivate users.
* **Schedule Builder:** A routine planner where users can map out their day, link specific time slots to habits, and select specific days of the week (Mon-Sun) for activities.

### Project Structure

#### `app.py`
This is the main controller of the application, built using Flask. It handles all backend logic and routing. Key functions include:
* **`dashboard()`**: Checks the current date against the `last_progress_date` in the database. If the dates differ, it resets the user's daily progress to ensure a fresh start for the new day.
* **`update()`**: Handles the logic for incrementing habit progress. It also manages streak calculations by checking if the habit was completed yesterday (increment streak) or not (reset streak).
* **`onboarding()`**: Manages the multi-step process of setting up a user profile after registration.
* **`myroutine()`**: Handles the complex logic of inserting schedule items and mapping them to specific days of the week (Boolean columns in the database).

#### `helpers.py`
Contains helper functions like `login_required` decorator to protect routes and `apology` to render error messages.

#### `templates/`
* `landing.html`: The welcome page for non-logged-in users.
* `index.html`: The main dashboard displaying active habits and the day's schedule.
* `register.html` & `login.html`: Authentication forms.
* `onboarding.html` & `personalise.html`: Forms for initial user setup.
* `habit.html`: Interface for creating and managing habits.
* `schedule.html`: Interface for adding activities to the daily routine.

### Design Choices

#### Database Schema
I chose to use **SQLite** with the CS50 library for simplicity and ease of use. I structured the database with separate tables for `users`, `habits`, and `schedule` to maintain normalization.
* **Linking Habits to Schedule:** In the `schedule` table, I included a `habit_id` as a foreign key. This allows users to link a generic time slot (like "Morning Study") to a specific trackable habit (like "Study 2 hours"), integrating the two main features of the app.

#### Progress Reset Logic
One challenge was how to handle a new day. Instead of running a background cron job (which is complex to set up), I implemented a "lazy" check in the `/dashboard` route. Every time a user loads the dashboard, the app checks if `last_progress_date` matches today's date. If it doesn't, the app automatically resets the progress to 0 for that day. This ensures the data is always correct when the user sees it, without needing server-side timers.

#### Streak Calculation
In the `update` route, I implemented logic to check if `last_completed_date` was yesterday. If yes, the streak increments; if no (and it wasn't today), the streak resets to 1. This encourages users to be consistent daily.
