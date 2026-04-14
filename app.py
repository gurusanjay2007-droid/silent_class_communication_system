import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, Institution, User, Period, Doubt

# For deployment compatibility
app = Flask(__name__)
index = app 

app.config['SECRET_KEY'] = 'sccs_secret_key_2026'
# Vercel filesystem is read-only. For temporary use, we can try /tmp/sccs.db
# but it won't persist. Ideally switch to a real DB.
if os.environ.get('VERCEL'):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/sccs.db'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sccs.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize database only if it doesn't exist
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register_institution', methods=['GET', 'POST'])
def register_institution():
    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')
        
        # Generate a unique 6-character ID for institution
        inst_id = str(uuid.uuid4())[:6].upper()
        
        new_inst = Institution(id=inst_id, name=name, password_hash=generate_password_hash(password))
        db.session.add(new_inst)
        db.session.commit()
        
        flash(f'Institution registered successfully! Your Institution ID is: {inst_id}. Save this for staff/student registration.', 'success')
        return redirect(url_for('login'))
    return render_template('register_institution.html')

@app.route('/register_student', methods=['GET', 'POST'])
def register_student():
    if request.method == 'POST':
        inst_id = request.form.get('institution_id')
        inst = Institution.query.get(inst_id)
        if not inst:
            flash('Invalid Institution ID.', 'danger')
            return redirect(url_for('register_student'))
        
        username = request.form.get('username')
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('register_student'))
            
        new_user = User(
            institution_id=inst_id,
            role='student',
            name=request.form.get('name'),
            username=username,
            password_hash=generate_password_hash(request.form.get('password')),
            reg_no=request.form.get('reg_no'),
            dob=datetime.strptime(request.form.get('dob'), '%Y-%m-%d').date() if request.form.get('dob') else None,
            department=request.form.get('department'),
            year_of_study=request.form.get('year_of_study'),
            student_class=request.form.get('student_class')
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Student registered successfully!', 'success')
        return redirect(url_for('login'))
    return render_template('register_student.html')

from datetime import datetime

@app.route('/register_staff', methods=['GET', 'POST'])
def register_staff():
    if request.method == 'POST':
        inst_id = request.form.get('institution_id')
        inst = Institution.query.get(inst_id)
        if not inst:
            flash('Invalid Institution ID.', 'danger')
            return redirect(url_for('register_staff'))
            
        username = request.form.get('username')
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('register_staff'))
            
        new_user = User(
            institution_id=inst_id,
            role='staff',
            name=request.form.get('name'),
            username=username,
            password_hash=generate_password_hash(request.form.get('password')),
            degree_completed=request.form.get('degree'),
            subject_handled=request.form.get('subject')
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Staff registered successfully!', 'success')
        return redirect(url_for('login'))
    return render_template('register_staff.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        inst_id = request.form.get('institution_id')
        
        user = User.query.filter_by(username=username, institution_id=inst_id).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            if user.role == 'student':
                return redirect(url_for('student_dashboard'))
            else:
                return redirect(url_for('staff_dashboard'))
        else:
            flash('Login failed. Check details.', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/student_dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        return redirect(url_for('index'))
    # Fetch active periods for the student's class and department
    active_periods = Period.query.filter_by(
        institution_id=current_user.institution_id,
        department=current_user.department,
        year=current_user.year_of_study,
        student_class=current_user.student_class,
        is_active=True
    ).all()
    
    return render_template('student_dashboard.html', active_periods=active_periods)

@app.route('/staff_dashboard', methods=['GET', 'POST'])
@login_required
def staff_dashboard():
    if current_user.role != 'staff':
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Start a new period
        new_period = Period(
            institution_id=current_user.institution_id,
            staff_id=current_user.id,
            subject=request.form.get('subject'),
            department=request.form.get('department'),
            year=request.form.get('year'),
            student_class=request.form.get('student_class')
        )
        db.session.add(new_period)
        db.session.commit()
        flash('Period started successfully!', 'success')
        return redirect(url_for('staff_dashboard'))
        
    my_periods = Period.query.filter_by(staff_id=current_user.id).order_by(Period.created_at.desc()).all()
    active_period = next((p for p in my_periods if p.is_active), None)
    
    doubts = []
    if active_period:
        doubts = Doubt.query.filter_by(period_id=active_period.id).all()
        
    return render_template('staff_dashboard.html', periods=my_periods, active_period=active_period, doubts=doubts)

@app.route('/end_period/<int:period_id>', methods=['POST'])
@login_required
def end_period(period_id):
    if current_user.role != 'staff':
        return jsonify({'error': 'Unauthorized'}), 403
    period = Period.query.get_or_404(period_id)
    if period.staff_id == current_user.id:
        period.is_active = False
        db.session.commit()
        flash('Period ended.', 'success')
    return redirect(url_for('staff_dashboard'))

@app.route('/ask_doubt', methods=['POST'])
@login_required
def ask_doubt():
    if current_user.role != 'student':
        return jsonify({'error': 'Unauthorized'}), 403
    
    period_id = request.form.get('period_id')
    content = request.form.get('content')
    
    new_doubt = Doubt(period_id=period_id, content=content)
    db.session.add(new_doubt)
    db.session.commit()
    
    flash('Doubt submitted anonymously!', 'success')
    return redirect(url_for('student_dashboard'))

@app.route('/resolve_doubt/<int:doubt_id>', methods=['POST'])
@login_required
def resolve_doubt(doubt_id):
    if current_user.role != 'staff':
        return jsonify({'error': 'Unauthorized'}), 403
        
    doubt = Doubt.query.get_or_404(doubt_id)
    action = request.form.get('action') # 'cleared' or 'removed'
    reason = request.form.get('reason', '')
    
    if action in ['cleared', 'removed']:
        doubt.status = action
        if action == 'removed':
            doubt.removed_reason = reason
        db.session.commit()
        
    return redirect(url_for('staff_dashboard'))

if __name__ == '__main__':
    app.run(debug=True, port=8080)
