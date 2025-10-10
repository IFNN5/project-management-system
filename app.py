from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///projects.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    department = db.Column(db.String(100))

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    client_name = db.Column(db.String(200))
    description = db.Column(db.Text)
    estimated_cost = db.Column(db.Float)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    status = db.Column(db.String(50), default='pending_approval')
    progress_percent = db.Column(db.Integer, default=0)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(50), default='not_started')
    progress_percent = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PurchaseRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    requested_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    description = db.Column(db.Text)
    estimated_cost = db.Column(db.Float)
    status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    invoice_type = db.Column(db.String(50))
    amount = db.Column(db.Float)
    payment_status = db.Column(db.String(50), default='pending')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Initialize database and create users
def init_db():
    with app.app_context():
        db.create_all()
        
        # Check if users exist
        if User.query.count() == 0:
            users = [
                User(username='master', password=generate_password_hash('admin123'), role='master', department='الإدارة العامة'),
                User(username='sales', password=generate_password_hash('sales123'), role='sales', department='المبيعات'),
                User(username='manager', password=generate_password_hash('manager123'), role='management', department='الإدارة العليا'),
                User(username='projects', password=generate_password_hash('projects123'), role='projects', department='إدارة المشاريع'),
                User(username='operations', password=generate_password_hash('operations123'), role='operations', department='التشغيل'),
                User(username='procurement', password=generate_password_hash('procurement123'), role='procurement', department='المشتريات'),
                User(username='finance', password=generate_password_hash('finance123'), role='finance', department='المالية'),
                User(username='hr', password=generate_password_hash('hr123'), role='hr', department='الموارد البشرية'),
            ]
            db.session.add_all(users)
            db.session.commit()
            print("✅ Users created successfully!")

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['department'] = user.department
            flash(f'مرحباً {user.username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    role = session.get('role')
    user_id = session.get('user_id')
    
    # Get statistics
    total_projects = Project.query.count()
    pending_projects = Project.query.filter_by(status='pending_approval').count()
    in_progress = Project.query.filter_by(status='in_progress').count()
    completed = Project.query.filter_by(status='completed').count()
    
    # Get projects based on role
    if role == 'master':
        projects = Project.query.order_by(Project.created_at.desc()).all()
    elif role == 'sales':
        projects = Project.query.filter_by(created_by=user_id).order_by(Project.created_at.desc()).all()
    elif role == 'management':
        projects = Project.query.filter_by(status='pending_approval').order_by(Project.created_at.desc()).all()
    else:
        projects = Project.query.filter(Project.status.in_(['approved', 'in_progress', 'completed', 'on_hold'])).order_by(Project.created_at.desc()).all()
    
    # Get purchase requests for procurement
    purchase_requests = []
    if role in ['procurement', 'master', 'operations']:
        if role == 'operations':
            purchase_requests = PurchaseRequest.query.filter_by(requested_by=user_id).all()
        else:
            purchase_requests = PurchaseRequest.query.all()
    
    # Get invoices for finance
    invoices = []
    if role in ['finance', 'master']:
        invoices = Invoice.query.all()
    
    return render_template('dashboard.html', 
                         projects=projects,
                         purchase_requests=purchase_requests,
                         invoices=invoices,
                         stats={
                             'total': total_projects,
                             'pending': pending_projects,
                             'in_progress': in_progress,
                             'completed': completed
                         })

@app.route('/project/add', methods=['GET', 'POST'])
def add_project():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session.get('role') not in ['sales', 'master']:
        flash('ليس لديك صلاحية لإضافة مشاريع', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        project = Project(
            project_code=request.form.get('project_code'),
            name=request.form.get('name'),
            client_name=request.form.get('client_name'),
            description=request.form.get('description'),
            estimated_cost=float(request.form.get('estimated_cost', 0)),
            start_date=datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date() if request.form.get('start_date') else None,
            end_date=datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date() if request.form.get('end_date') else None,
            created_by=session.get('user_id'),
            status='pending_approval'
        )
        db.session.add(project)
        db.session.commit()
        flash('تم إضافة المشروع بنجاح! في انتظار الاعتماد', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('add_project.html')

@app.route('/project/<int:project_id>/approve')
def approve_project(project_id):
    if 'user_id' not in session or session.get('role') not in ['management', 'master']:
        flash('ليس لديك صلاحية لاعتماد المشاريع', 'error')
        return redirect(url_for('dashboard'))
    
    project = Project.query.get_or_404(project_id)
    project.status = 'approved'
    project.approved_by = session.get('user_id')
    db.session.commit()
    flash(f'تم اعتماد المشروع: {project.name}', 'success')
    return redirect(url_for('dashboard'))

@app.route('/project/<int:project_id>/reject')
def reject_project(project_id):
    if 'user_id' not in session or session.get('role') not in ['management', 'master']:
        flash('ليس لديك صلاحية لرفض المشاريع', 'error')
        return redirect(url_for('dashboard'))
    
    project = Project.query.get_or_404(project_id)
    project.status = 'rejected'
    db.session.commit()
    flash(f'تم رفض المشروع: {project.name}', 'error')
    return redirect(url_for('dashboard'))

@app.route('/project/<int:project_id>/status/<status>')
def update_project_status(project_id, status):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    allowed_statuses = ['in_progress', 'on_hold', 'completed', 'cancelled']
    if status not in allowed_statuses:
        flash('حالة غير صحيحة', 'error')
        return redirect(url_for('dashboard'))
    
    project = Project.query.get_or_404(project_id)
    project.status = status
    db.session.commit()
    
    status_names = {
        'in_progress': 'قيد التنفيذ',
        'on_hold': 'متوقف',
        'completed': 'مكتمل',
        'cancelled': 'ملغي'
    }
    
    flash(f'تم تحديث حالة المشروع إلى: {status_names[status]}', 'success')
    return redirect(url_for('dashboard'))

@app.route('/purchase/add', methods=['GET', 'POST'])
def add_purchase_request():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session.get('role') not in ['operations', 'master', 'projects']:
        flash('ليس لديك صلاحية لإضافة طلبات شراء', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        purchase = PurchaseRequest(
            project_id=int(request.form.get('project_id')),
            requested_by=session.get('user_id'),
            description=request.form.get('description'),
            estimated_cost=float(request.form.get('estimated_cost', 0)),
            status='pending'
        )
        db.session.add(purchase)
        db.session.commit()
        flash('تم إضافة طلب الشراء بنجاح!', 'success')
        return redirect(url_for('dashboard'))
    
    projects = Project.query.filter(Project.status.in_(['approved', 'in_progress'])).all()
    return render_template('add_purchase.html', projects=projects)

@app.route('/purchase/<int:purchase_id>/approve')
def approve_purchase(purchase_id):
    if 'user_id' not in session or session.get('role') not in ['procurement', 'master']:
        flash('ليس لديك صلاحية لاعتماد طلبات الشراء', 'error')
        return redirect(url_for('dashboard'))
    
    purchase = PurchaseRequest.query.get_or_404(purchase_id)
    purchase.status = 'approved'
    db.session.commit()
    flash('تم اعتماد طلب الشراء', 'success')
    return redirect(url_for('dashboard'))

@app.route('/purchase/<int:purchase_id>/reject')
def reject_purchase(purchase_id):
    if 'user_id' not in session or session.get('role') not in ['procurement', 'master']:
        flash('ليس لديك صلاحية لرفض طلبات الشراء', 'error')
        return redirect(url_for('dashboard'))
    
    purchase = PurchaseRequest.query.get_or_404(purchase_id)
    purchase.status = 'rejected'
    db.session.commit()
    flash('تم رفض طلب الشراء', 'error')
    return redirect(url_for('dashboard'))

@app.route('/invoice/add', methods=['GET', 'POST'])
def add_invoice():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session.get('role') not in ['finance', 'master']:
        flash('ليس لديك صلاحية لإضافة فواتير', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        invoice = Invoice(
            project_id=int(request.form.get('project_id')),
            invoice_type=request.form.get('invoice_type'),
            amount=float(request.form.get('amount', 0)),
            payment_status='pending',
            created_by=session.get('user_id')
        )
        db.session.add(invoice)
        db.session.commit()
        flash('تم إضافة الفاتورة بنجاح!', 'success')
        return redirect(url_for('dashboard'))
    
    projects = Project.query.filter(Project.status.in_(['approved', 'in_progress', 'completed'])).all()
    return render_template('add_invoice.html', projects=projects)

@app.route('/invoice/<int:invoice_id>/paid')
def mark_invoice_paid(invoice_id):
    if 'user_id' not in session or session.get('role') not in ['finance', 'master']:
        flash('ليس لديك صلاحية لتحديث الفواتير', 'error')
        return redirect(url_for('dashboard'))
    
    invoice = Invoice.query.get_or_404(invoice_id)
    invoice.payment_status = 'paid'
    db.session.commit()
    flash('تم تحديث حالة الفاتورة إلى: مدفوعة', 'success')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
