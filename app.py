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
    full_name = db.Column(db.String(200))
    email = db.Column(db.String(200))
    phone = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)

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
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PurchaseRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    requested_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=True)
    description = db.Column(db.Text)
    estimated_cost = db.Column(db.Float)
    status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    contact_person = db.Column(db.String(200))
    email = db.Column(db.String(200))
    phone = db.Column(db.String(50))
    address = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    invoice_type = db.Column(db.String(50))
    amount = db.Column(db.Float)
    payment_status = db.Column(db.String(50), default='pending')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    comment_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Initialize database
def init_db():
    with app.app_context():
        db.create_all()
        
        if User.query.count() == 0:
            users = [
                User(username='master', password=generate_password_hash('admin123'), role='master', department='الإدارة العامة', full_name='المدير العام'),
                User(username='sales', password=generate_password_hash('sales123'), role='sales', department='المبيعات', full_name='موظف المبيعات'),
                User(username='manager', password=generate_password_hash('manager123'), role='management', department='الإدارة العليا', full_name='المدير التنفيذي'),
                User(username='projects', password=generate_password_hash('projects123'), role='projects', department='إدارة المشاريع', full_name='مدير المشاريع'),
                User(username='operations', password=generate_password_hash('operations123'), role='operations', department='التشغيل', full_name='مدير التشغيل'),
                User(username='procurement', password=generate_password_hash('procurement123'), role='procurement', department='المشتريات', full_name='مدير المشتريات'),
                User(username='finance', password=generate_password_hash('finance123'), role='finance', department='المالية', full_name='المدير المالي'),
                User(username='hr', password=generate_password_hash('hr123'), role='hr', department='الموارد البشرية', full_name='مدير الموارد البشرية'),
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
    
    total_projects = Project.query.count()
    pending_projects = Project.query.filter_by(status='pending_approval').count()
    in_progress = Project.query.filter_by(status='in_progress').count()
    completed = Project.query.filter_by(status='completed').count()
    
    if role == 'master':
        projects = Project.query.order_by(Project.created_at.desc()).all()
    elif role == 'sales':
        projects = Project.query.filter_by(created_by=user_id).order_by(Project.created_at.desc()).all()
    elif role == 'management':
        projects = Project.query.filter_by(status='pending_approval').order_by(Project.created_at.desc()).all()
    else:
        projects = Project.query.filter(Project.status.in_(['approved', 'in_progress', 'completed', 'on_hold'])).order_by(Project.created_at.desc()).all()
    
    purchase_requests = []
    if role in ['procurement', 'master', 'operations']:
        if role == 'operations':
            purchase_requests = PurchaseRequest.query.filter_by(requested_by=user_id).all()
        else:
            purchase_requests = PurchaseRequest.query.all()
    
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

@app.route('/project/<int:project_id>')
def project_details(project_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    project = Project.query.get_or_404(project_id)
    tasks = Task.query.filter_by(project_id=project_id).all()
    purchase_requests = PurchaseRequest.query.filter_by(project_id=project_id).all()
    invoices = Invoice.query.filter_by(project_id=project_id).all()
    comments = Comment.query.filter_by(project_id=project_id).order_by(Comment.created_at.desc()).all()
    
    # Get users for tasks
    users = User.query.filter_by(is_active=True).all()
    
    # Get comment users
    comment_users = {}
    for comment in comments:
        user = User.query.get(comment.user_id)
        if user:
            comment_users[comment.id] = user
    
    return render_template('project_details.html', 
                         project=project,
                         tasks=tasks,
                         purchase_requests=purchase_requests,
                         invoices=invoices,
                         comments=comments,
                         comment_users=comment_users,
                         users=users)

@app.route('/project/<int:project_id>/update_progress', methods=['POST'])
def update_progress(project_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    project = Project.query.get_or_404(project_id)
    progress = int(request.form.get('progress', 0))
    project.progress_percent = progress
    db.session.commit()
    flash(f'تم تحديث نسبة الإنجاز إلى {progress}%', 'success')
    return redirect(url_for('project_details', project_id=project_id))

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

# Tasks Routes
@app.route('/project/<int:project_id>/task/add', methods=['POST'])
def add_task(project_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    task = Task(
        project_id=project_id,
        name=request.form.get('name'),
        description=request.form.get('description'),
        assigned_to=int(request.form.get('assigned_to')) if request.form.get('assigned_to') else None,
        start_date=datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date() if request.form.get('start_date') else None,
        end_date=datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date() if request.form.get('end_date') else None,
        status='not_started'
    )
    db.session.add(task)
    db.session.commit()
    flash('تم إضافة المهمة بنجاح!', 'success')
    return redirect(url_for('project_details', project_id=project_id))

@app.route('/task/<int:task_id>/status/<status>')
def update_task_status(task_id, status):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    task = Task.query.get_or_404(task_id)
    task.status = status
    
    if status == 'done':
        task.progress_percent = 100
    elif status == 'in_progress' and task.progress_percent == 0:
        task.progress_percent = 50
    
    db.session.commit()
    flash('تم تحديث حالة المهمة', 'success')
    return redirect(url_for('project_details', project_id=task.project_id))

# Comments Routes
@app.route('/project/<int:project_id>/comment/add', methods=['POST'])
def add_comment(project_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    comment_text = request.form.get('comment_text')
    if comment_text:
        comment = Comment(
            project_id=project_id,
            user_id=session.get('user_id'),
            comment_text=comment_text
        )
        db.session.add(comment)
        db.session.commit()
        flash('تم إضافة التعليق بنجاح!', 'success')
    
    return redirect(url_for('project_details', project_id=project_id))

# Purchase Routes
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
            supplier_id=int(request.form.get('supplier_id')) if request.form.get('supplier_id') else None,
            description=request.form.get('description'),
            estimated_cost=float(request.form.get('estimated_cost', 0)),
            status='pending'
        )
        db.session.add(purchase)
        db.session.commit()
        flash('تم إضافة طلب الشراء بنجاح!', 'success')
        return redirect(url_for('dashboard'))
    
    projects = Project.query.filter(Project.status.in_(['approved', 'in_progress'])).all()
    suppliers = Supplier.query.filter_by(is_active=True).all()
    return render_template('add_purchase.html', projects=projects, suppliers=suppliers)

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

# Invoice Routes
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

# Employees Routes (HR)
@app.route('/employees')
def employees():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session.get('role') not in ['hr', 'master']:
        flash('ليس لديك صلاحية لعرض الموظفين', 'error')
        return redirect(url_for('dashboard'))
    
    employees = User.query.all()
    return render_template('employees.html', employees=employees)

@app.route('/employee/add', methods=['GET', 'POST'])
def add_employee():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session.get('role') not in ['hr', 'master']:
        flash('ليس لديك صلاحية لإضافة موظفين', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        employee = User(
            username=request.form.get('username'),
            password=generate_password_hash(request.form.get('password')),
            role=request.form.get('role'),
            department=request.form.get('department'),
            full_name=request.form.get('full_name'),
            email=request.form.get('email'),
            phone=request.form.get('phone'),
            is_active=True
        )
        db.session.add(employee)
        db.session.commit()
        flash('تم إضافة الموظف بنجاح!', 'success')
        return redirect(url_for('employees'))
    
    return render_template('add_employee.html')

# Suppliers Routes
@app.route('/suppliers')
def suppliers():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session.get('role') not in ['procurement', 'master']:
        flash('ليس لديك صلاحية لعرض الموردين', 'error')
        return redirect(url_for('dashboard'))
    
    suppliers = Supplier.query.all()
    return render_template('suppliers.html', suppliers=suppliers)

@app.route('/supplier/add', methods=['GET', 'POST'])
def add_supplier():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session.get('role') not in ['procurement', 'master']:
        flash('ليس لديك صلاحية لإضافة موردين', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        supplier = Supplier(
            name=request.form.get('name'),
            contact_person=request.form.get('contact_person'),
            email=request.form.get('email'),
            phone=request.form.get('phone'),
            address=request.form.get('address'),
            is_active=True
        )
        db.session.add(supplier)
        db.session.commit()
        flash('تم إضافة المورد بنجاح!', 'success')
        return redirect(url_for('suppliers'))
    
    return render_template('add_supplier.html')

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
