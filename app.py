# app.py - full application
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from datetime import datetime, date, time, timedelta
import os
import secrets

# -------------------------
# Configuration
# -------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = "dev-secret-change-me"

# Ensure instance folder exists and use sqlite file there
INSTANCE_DIR = os.path.join(app.root_path, 'instance')
os.makedirs(INSTANCE_DIR, exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(INSTANCE_DIR, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Admin credentials
ADMIN_PHONE = "9999999999"
ADMIN_PASSWORD = "Admin@123"

# -------------------------
# Models
# -------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=True)
    ration_card = db.Column(db.String(32), unique=True, nullable=False)
    phone = db.Column(db.String(32), nullable=True)

class IssueDate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True, nullable=False)

class Slot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    duration_mins = db.Column(db.Integer, default=5)
    booked = db.Column(db.Boolean, default=False)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey('slot.id'), nullable=False)
    booking_date = db.Column(db.Date, nullable=False)
    ref_code = db.Column(db.String(32), nullable=False, unique=True)

    user = db.relationship('User', backref='bookings')
    slot = db.relationship('Slot', backref='bookings')

# -------------------------
# Helpers
# -------------------------
def get_issue_date_list():
    rows = IssueDate.query.order_by(IssueDate.date).all()
    return [r.date.isoformat() for r in rows]

def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)

def times_for_day():
    slots = []

    def make_range(h1, m1, h2, m2):
        cur = datetime.combine(date.today(), time(h1, m1))
        end = datetime.combine(date.today(), time(h2, m2))
        while cur <= end:
            slots.append(cur.time())
            cur += timedelta(minutes=5)

    make_range(9, 0, 13, 30)   # morning
    make_range(15, 0, 20, 0)   # evening
    return slots

@app.context_processor
def inject_year():
    return {"current_year": date.today().year}

# -------------------------
# Index
# -------------------------
@app.route('/')
def index():
    return render_template("index.html")

# -------------------------
# Admin login
# -------------------------
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('password')

        if phone == ADMIN_PHONE and password == ADMIN_PASSWORD:
            session.clear()
            session['admin_logged_in'] = True
            session['admin_phone'] = phone
            return redirect(url_for('admin_panel'))
        else:
            flash("Invalid credentials", "error")
    return render_template("admin_login.html")

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_phone', None)
    return redirect(url_for('index'))

# -------------------------
# Admin panel
# -------------------------
@app.route('/admin/panel', methods=['GET', 'POST'])
def admin_panel():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    active_dates = get_issue_date_list()

    if request.method == 'POST':
        start = request.form.get('start_date')
        end = request.form.get('end_date')

        try:
            start_d = datetime.fromisoformat(start).date()
            end_d = datetime.fromisoformat(end).date()
        except:
            flash("Invalid date format", "error")
            return redirect(url_for('admin_panel'))

        if end_d < start_d:
            flash("End date cannot be before start date", "error")
            return redirect(url_for('admin_panel'))

        created_slots = 0
        for d in daterange(start_d, end_d):
            if not IssueDate.query.filter_by(date=d).first():
                db.session.add(IssueDate(date=d))
                db.session.commit()

            for t in times_for_day():
                if not Slot.query.filter_by(date=d, start_time=t).first():
                    db.session.add(Slot(date=d, start_time=t, duration_mins=5))
                    created_slots += 1

        db.session.commit()
        flash(f"Slots generated: {created_slots}", "success")
        active_dates = get_issue_date_list()

    existing = Slot.query.count()
    return render_template("admin_panel.html",
                           active_dates=active_dates,
                           existing_count=existing)
# -------------------------
# Admin: delete a single issue date (and its slots + bookings)
# -------------------------
@app.route('/admin/delete_date/<date_iso>', methods=['POST'])
def admin_delete_date(date_iso):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    # parse expected ISO YYYY-MM-DD
    try:
        d = datetime.fromisoformat(date_iso).date()
    except Exception:
        flash("Invalid date.", "error")
        return redirect(url_for('admin_panel'))

    # find IssueDate
    issue = IssueDate.query.filter_by(date=d).first()
    if not issue:
        flash("Date not found.", "error")
        return redirect(url_for('admin_panel'))

    # find slots for that date
    slots = Slot.query.filter_by(date=d).all()
    # delete bookings for those slots first
    for s in slots:
        Booking.query.filter_by(slot_id=s.id).delete()
    # delete slots
    Slot.query.filter_by(date=d).delete()
    # delete issue date row
    db.session.delete(issue)
    db.session.commit()

    flash(f"Removed issue date {d.isoformat()} and its {len(slots)} slots/bookings.", "success")
    return redirect(url_for('admin_panel'))

# -------------------------
# Admin: clear (delete) slots & bookings for selected date range
# -------------------------
@app.route('/admin/clear_slots', methods=['POST'])
def admin_clear_slots():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    start = request.form.get('start_date')
    end = request.form.get('end_date')
    try:
        start_d = datetime.fromisoformat(start).date()
        end_d = datetime.fromisoformat(end).date()
    except Exception:
        flash("Invalid date format for clear operation.", "error")
        return redirect(url_for('admin_panel'))

    if end_d < start_d:
        flash("End date cannot be before start date.", "error")
        return redirect(url_for('admin_panel'))

    total_slots_removed = 0
    total_bookings_removed = 0

    for d in daterange(start_d, end_d):
        # find slots for date d
        slots = Slot.query.filter_by(date=d).all()
        # delete bookings for those slots
        for s in slots:
            # count bookings deleted
            bs = Booking.query.filter_by(slot_id=s.id).all()
            if bs:
                total_bookings_removed += len(bs)
            Booking.query.filter_by(slot_id=s.id).delete()
        # delete slots
        removed = Slot.query.filter_by(date=d).delete()
        total_slots_removed += removed
        # delete IssueDate row (if exists)
        issue = IssueDate.query.filter_by(date=d).first()
        if issue:
            db.session.delete(issue)

    db.session.commit()

    flash(f"Cleared {total_slots_removed} slots and {total_bookings_removed} bookings for {start_d} → {end_d}.", "success")
    return redirect(url_for('admin_panel'))

# -------------------------
# User login
# -------------------------
@app.route('/user/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        ration = request.form.get('ration_card')
        otp = request.form.get('otp')

        user = User.query.filter_by(ration_card=ration).first()
        if not user:
            flash("Ration card not found", "error")
            return redirect(url_for('user_login'))

        expected_otp = ration[-4:]

        if otp == expected_otp:
            session.clear()
            session['user_id'] = user.id
            return redirect(url_for('user_panel'))
        else:
            flash("Invalid OTP", "error")

    return render_template("user_login.html")

@app.route('/user/logout')
def user_logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

# -------------------------
# User panel
# -------------------------
# -------------------------
# User panel
# -------------------------
@app.route('/user/panel')
def user_panel():
    if not session.get('user_id'):
        return redirect(url_for('user_login'))

    user = User.query.get(session['user_id'])
    allowed_dates = get_issue_date_list()

    # only load slots if user explicitly clicked "View Slots" (form sets show=1)
    show_flag = request.args.get('show') == '1'

    selected = request.args.get('date')
    selected_date = None
    slots = []
    user_booking = None

    if allowed_dates and show_flag:
        # determine selected_date (ISO expected)
        if selected:
            try:
                selected_date = datetime.fromisoformat(selected).date()
            except Exception:
                try:
                    selected_date = datetime.strptime(selected, "%d-%m-%Y").date()
                except Exception:
                    selected_date = datetime.fromisoformat(allowed_dates[0]).date()
        else:
            selected_date = datetime.fromisoformat(allowed_dates[0]).date()

        slots = Slot.query.filter_by(date=selected_date).order_by(Slot.start_time).all()

        # Check if user has a booking in any active date (one booking for whole active set)
        bookings = Booking.query.filter_by(user_id=user.id).all()
        for b in bookings:
            s = Slot.query.get(b.slot_id)
            if s and s.date.isoformat() in allowed_dates:
                user_booking = b
                break

    return render_template("user_panel.html",
                           user=user,
                           allowed_dates=allowed_dates,
                           selected_date=selected_date,
                           slots=slots,
                           user_booking=user_booking,
                           show_slots=show_flag)

# -------------------------
# Book a slot
# -------------------------
@app.route('/book/<int:slot_id>', methods=['POST'])
def book(slot_id):
    if not session.get('user_id'):
        return redirect(url_for('user_login'))

    user = User.query.get(session['user_id'])
    slot = Slot.query.get(slot_id)

    active_dates = get_issue_date_list()

    # Check already booked this cycle
    bookings = Booking.query.filter_by(user_id=user.id).all()
    for b in bookings:
        s = Slot.query.get(b.slot_id)
        if s.date.isoformat() in active_dates:
            flash("You already booked a slot this month.", "info")
            return redirect(url_for('user_panel', date=slot.date.isoformat()))

    if slot.booked:
        flash("Slot already taken", "error")
        return redirect(url_for('user_panel', date=slot.date.isoformat()))

    # Make booking
    slot.booked = True
    booking = Booking(
        user_id=user.id,
        slot_id=slot.id,
        booking_date=slot.date,
        ref_code=secrets.token_hex(4)
    )

    db.session.add(booking)
    db.session.commit()

    return redirect(url_for('booking_confirm', booking_id=booking.id))

# -------------------------
# Booking confirmation
# -------------------------
@app.route('/booking/<int:booking_id>')
def booking_confirm(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    return render_template("booking_confirm.html", booking=booking)

# -------------------------
# Admin: view bookings
# -------------------------
@app.route('/admin/bookings')
def admin_bookings():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    bookings = Booking.query.order_by(Booking.id.desc()).all()
    return render_template("admin_bookings.html", bookings=bookings)

# -------------------------
# DB Init for Flask 3.x
# -------------------------
with app.app_context():
    db.create_all()

    # Seed 5 users if not exist
    sample_cards = [
        ("User One", "1002003001", "9100000001"),
        ("User Two", "1002003002", "9100000002"),
        ("User Three", "1002003003", "9100000003"),
        ("User Four", "1002003004", "9100000004"),
        ("User Five", "1002003005", "9100000005"),
    ]
    for name, rc, ph in sample_cards:
        if not User.query.filter_by(ration_card=rc).first():
            db.session.add(User(name=name, ration_card=rc, phone=ph))

    db.session.commit()

# -------------------------
# Run
# -------------------------
if __name__ == '__main__':
    app.run(debug=True)
