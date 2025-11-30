📘 Python Web Application for Govt Ration Slot Booking and Queue Management

A modern, web-based slot booking system designed for Government Ration Shops (Fair Price Shops) to reduce crowding, eliminate long queues, and streamline ration distribution.
Built using Python (Flask), HTML/CSS, and SQLite.

🚀 Features
🟦 User Features

Login using Ration Card Number + OTP (last 4 digits).
View admin-approved issue dates.
View available 5-minute time slots.
Book exactly one slot per user per month.

See live slot status:
Available
Booked
Your Booking (highlighted)
Professional UI with Gov. of Karnataka theme.

🟩 Admin Features

Admin login using secure credentials.

Set start and end date for ration issue.

Auto-generate all 5-minute slots between:

9:00 AM – 1:30 PM

3:00 PM – 8:00 PM

Delete previously generated slots.

View active dates and total slots created.

🧰 Technology Stack
Frontend

HTML, CSS

Jinja2 Templates

Responsive UI with Gov. of Karnataka theme

Backend

Python 3

Flask web framework

Database

SQLite (via SQLAlchemy ORM)

📁 Project Structure
govt-ration-slot-booking/
│
├── app.py
├── requirements.txt
├── Procfile
├── .gitignore
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── admin_login.html
│   ├── user_login.html
│   ├── admin_panel.html
│   ├── user_panel.html
│   ├── booking_confirm.html
│   ├── slots.html
│
├── static/
│   ├── style.css
│   ├── images/
│       ├── gok.png
│       ├── food.png
│
└── instance/
    └── app.db   (auto-created)

🎯 How to Run Locally
1. Clone the repository
git clone https://github.com/likiajay8/govt-ration-slot-booking.git
cd govt-ration-slot-booking

2. Create virtual environment
python -m venv venv

3. Activate virtual environment

Windows

venv\Scripts\activate


Mac/Linux

source venv/bin/activate

4. Install dependencies
pip install -r requirements.txt

5. Run the app
python app.py


Visit:

http://127.0.0.1:5000/

🔐 Admin Credentials (Sample for Project Demo)
Admin Phone: 9999999999
Password: Admin@123

🪪 Sample User Credentials
User	Ration Card No.	OTP
User One	1002003001	3001
User Two	1002003002	3002
User Three	1002003003	3003
User Four	1002003004	3004
User Five	1002003005	3005
🏛️ Purpose of the Project

This system is designed to support Digital Public Distribution System (e-PDS) initiatives, enabling ration shops to manage citizens efficiently, eliminate long queues, and reduce congestion by using time-based digital scheduling.

📌 Future Enhancements

SMS-based OTP authentication

Integration with Aadhaar/Ration API

Multi-language support (Kannada/English)

Detailed analytics for admin

PDF slot confirmation receipt

❤️ Developed By

Likith H P
Govt Ration Slot Booking Web Application
Python | Flask | SQLAlchemy
