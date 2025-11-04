import os
import sqlite3
import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps

# Configure Flask app
app = Flask(__name__)
app.secret_key = 'real_estate_management_secret_key'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'images', 'properties')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Database setup
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database', 'realestate.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        full_name TEXT,
        email TEXT,
        role TEXT DEFAULT 'admin',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create landlords table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS landlords (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        phone TEXT NOT NULL,
        email TEXT,
        address TEXT,
        id_number TEXT,
        bank_name TEXT,
        account_number TEXT,
        current_balance REAL DEFAULT 0.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create properties table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS properties (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        type TEXT NOT NULL,
        location TEXT NOT NULL,
        size TEXT,
        landlord_id INTEGER NOT NULL,
        price REAL,
        status TEXT DEFAULT 'Vacant',
        description TEXT,
        image_path TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (landlord_id) REFERENCES landlords (id)
    )
    ''')
    
    # Create property_units table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS property_units (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        property_id INTEGER NOT NULL,
        unit_name TEXT NOT NULL,
        size TEXT,
        price REAL,
        status TEXT DEFAULT 'Vacant',
        tenant_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (property_id) REFERENCES properties (id),
        FOREIGN KEY (tenant_id) REFERENCES tenants (id)
    )
    ''')
    
    # Create tenants table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tenants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        phone TEXT NOT NULL,
        whatsapp TEXT,
        email TEXT,
        id_number TEXT,
        medium_of_reach TEXT,
        permanent_address TEXT,
        occupation TEXT,
        employer TEXT,
        lease_start_date TEXT,
        lease_end_date TEXT,
        receipt_info TEXT,
        bank_name TEXT,
        account_number TEXT,
        age INTEGER,
        sex TEXT,
        state_of_origin TEXT,
        nationality TEXT,
        tribe TEXT,
        remarks TEXT,
        guarantor_name TEXT,
        guarantor_phone TEXT,
        guarantor_address TEXT,
        next_of_kin_name TEXT,
        next_of_kin_address TEXT,
        property_id INTEGER,
        unit_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (property_id) REFERENCES properties (id),
        FOREIGN KEY (unit_id) REFERENCES property_units (id)
    )
    ''')
    
    # Create payments table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id INTEGER NOT NULL,
        property_id INTEGER NOT NULL,
        unit_id INTEGER,
        amount REAL NOT NULL,
        payment_type TEXT NOT NULL,
        payment_method TEXT NOT NULL,
        payment_date TEXT DEFAULT CURRENT_DATE,
        balance_due REAL DEFAULT 0,
        status TEXT DEFAULT 'Paid',
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (tenant_id) REFERENCES tenants (id),
        FOREIGN KEY (property_id) REFERENCES properties (id),
        FOREIGN KEY (unit_id) REFERENCES property_units (id)
    )
    ''')
    
    # Create accounts (ledger) table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        landlord_id INTEGER NOT NULL,
        property_id INTEGER,
        unit_id INTEGER,
        amount REAL NOT NULL,
        transaction_type TEXT NOT NULL,
        description TEXT,
        payment_id INTEGER,
        balance_after REAL NOT NULL,
        transaction_date TEXT DEFAULT CURRENT_DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (landlord_id) REFERENCES landlords (id),
        FOREIGN KEY (property_id) REFERENCES properties (id),
        FOREIGN KEY (unit_id) REFERENCES property_units (id),
        FOREIGN KEY (payment_id) REFERENCES payments (id)
    )
    ''')
    
    # Create documents table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        file_path TEXT NOT NULL,
        document_type TEXT NOT NULL,
        tenant_id INTEGER,
        property_id INTEGER,
        landlord_id INTEGER,
        upload_date TEXT DEFAULT CURRENT_DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (tenant_id) REFERENCES tenants (id),
        FOREIGN KEY (property_id) REFERENCES properties (id),
        FOREIGN KEY (landlord_id) REFERENCES landlords (id)
    )
    ''')
    
    # Create complaints table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS complaints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id INTEGER NOT NULL,
        property_id INTEGER,
        unit_id INTEGER,
        subject TEXT NOT NULL,
        description TEXT NOT NULL,
        status TEXT DEFAULT 'Open',
        resolution TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        resolved_at TIMESTAMP,
        FOREIGN KEY (tenant_id) REFERENCES tenants (id),
        FOREIGN KEY (property_id) REFERENCES properties (id),
        FOREIGN KEY (unit_id) REFERENCES property_units (id)
    )
    ''')
    
    # Create notifications table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Create settings table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        setting_name TEXT NOT NULL UNIQUE,
        setting_value TEXT,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Check if default admin user exists
    cursor.execute("SELECT id FROM users WHERE username = 'admin1'")
    admin = cursor.fetchone()
    
    if not admin:
        # Create default admin user
        admin_password_hash = generate_password_hash('admin123')
        cursor.execute(
            "INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
            ('admin1', admin_password_hash, 'Admin User', 'admin')
        )
        
        # Insert default settings
        cursor.execute(
            "INSERT INTO settings (setting_name, setting_value, description) VALUES (?, ?, ?)",
            ('rent_reminder_days', '7', 'Days before rent due to send reminder')
        )
        cursor.execute(
            "INSERT INTO settings (setting_name, setting_value, description) VALUES (?, ?, ?)",
            ('partial_payment_reminder_days', '3', 'Days after partial payment to follow up')
        )
        
        # Insert sample data
        # Sample Landlord
        """cursor.execute(
            "INSERT INTO landlords (full_name, phone, email, address, bank_name, account_number) VALUES (?, ?, ?, ?, ?, ?)",
            ('John Smith', '1234567890', 'john.smith@example.com', '123 Main St', 'First Bank', '1234567890')
        )
        """
        """ # Sample Property
        cursor.execute(
            "INSERT INTO properties (title, type, location, size, landlord_id, price, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ('Luxury Apartment', 'Apartment', 'Downtown', '1200 sqft', 1, 1500.0, 'Modern luxury apartment in downtown area')
        )
        
        # Sample Tenement Property
        cursor.execute(
            "INSERT INTO properties (title, type, location, size, landlord_id, description) VALUES (?, ?, ?, ?, ?, ?)",
            ('City Tenement', 'Tenement', 'Uptown', '5000 sqft', 1, 'Large tenement building with multiple units')
        )
        
        # Sample Units for the Tenement
        cursor.execute(
            "INSERT INTO property_units (property_id, unit_name, size, price) VALUES (?, ?, ?, ?)",
            (2, 'Unit A', '800 sqft', 800.0)
        )
        cursor.execute(
            "INSERT INTO property_units (property_id, unit_name, size, price) VALUES (?, ?, ?, ?)",
            (2, 'Unit B', '700 sqft', 750.0)
        )
        cursor.execute(
            "INSERT INTO property_units (property_id, unit_name, size, price) VALUES (?, ?, ?, ?)",
            (2, 'Unit C', '900 sqft', 850.0)
        )"""
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

# Login decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

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
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    
    # Get total counts
    total_properties = conn.execute('SELECT COUNT(*) as count FROM properties').fetchone()['count']
    total_tenants = conn.execute('SELECT COUNT(*) as count FROM tenants').fetchone()['count']
    total_landlords = conn.execute('SELECT COUNT(*) as count FROM landlords').fetchone()['count']
    
    # Get rent due this month
    current_month = datetime.datetime.now().strftime('%Y-%m')
# Get TOTAL outstanding rent (all unpaid balances)
# Get TOTAL outstanding rent (all unpaid balances)
    rent_due = conn.execute('''
        SELECT SUM(balance_due) as total_due
        FROM payments
        WHERE balance_due > 0
    ''').fetchone()

    total_rent_due = rent_due['total_due'] if rent_due['total_due'] is not None else 0

    # -------------------------
    # GENERAL ACCOUNT CALCULATION
    # -------------------------
    general_rows = conn.execute('''
        SELECT
            l.id AS landlord_id,
            COALESCE((
                SELECT SUM(p.amount) FROM payments p
                LEFT JOIN properties pr ON p.property_id = pr.id
                WHERE pr.landlord_id = l.id
            ), 0.0) AS payments_total,
            COALESCE((
                SELECT SUM(CASE WHEN lt.transaction_type = 'credit' THEN lt.amount ELSE 0 END)
                FROM landlord_transactions lt
                WHERE lt.landlord_id = l.id
            ), 0.0) AS manual_credits,
            COALESCE((
                SELECT SUM(CASE WHEN lt.transaction_type = 'debit' THEN lt.amount ELSE 0 END)
                FROM landlord_transactions lt
                WHERE lt.landlord_id = l.id
            ), 0.0) AS manual_debits
        FROM landlords l
    ''').fetchall()

    general_balance = 0.0
    for row in general_rows:
        payments_total = float(row['payments_total'] or 0)
        manual_credits = float(row['manual_credits'] or 0)
        manual_debits = float(row['manual_debits'] or 0)
        landlord_balance = payments_total + manual_credits - manual_debits
        general_balance += landlord_balance

    # -------------------------
    # ✅ MONTHLY EXPECTED EARNINGS CALCULATION
    # -------------------------
    # Get filter parameters from query string (default to NEXT month)
    filter_month = request.args.get('filter_month', type=int)
    filter_year = request.args.get('filter_year', type=int)
    
    # Calculate next month by default
    today = datetime.datetime.now()
    if filter_month is None or filter_year is None:
        # Default to NEXT month
        next_month = today.month + 1 if today.month < 12 else 1
        next_year = today.year if today.month < 12 else today.year + 1
        selected_month = next_month
        selected_year = next_year
    else:
        selected_month = filter_month
        selected_year = filter_year
    
    # Create start and end dates for the selected month
    filter_start_date = f"{selected_year}-{selected_month:02d}-01"
    
    # Calculate last day of month
    if selected_month == 12:
        filter_end_date = f"{selected_year}-12-31"
    else:
        next_month_year = selected_year if selected_month < 12 else selected_year + 1
        next_month_num = selected_month + 1 if selected_month < 12 else 1
        last_day = (datetime.datetime(next_month_year, next_month_num, 1) - datetime.timedelta(days=1)).day
        filter_end_date = f"{selected_year}-{selected_month:02d}-{last_day}"
    
    # Get tenants whose lease ends in the selected month and have paid before (renewals only)
    expected_renewals_data = conn.execute('''
        SELECT 
            t.id as tenant_id,
            t.full_name as tenant_name,
            t.lease_end_date,
            CASE WHEN t.unit_id IS NOT NULL THEN u.price ELSE p.price END as rent_amount,
            (SELECT COUNT(*) FROM payments pay WHERE pay.tenant_id = t.id AND pay.payment_type = 'Full' AND pay.balance_due = 0) as completed_payments
        FROM tenants t
        JOIN properties p ON t.property_id = p.id
        LEFT JOIN property_units u ON t.unit_id = u.id
        WHERE t.lease_end_date BETWEEN ? AND ?
        AND t.property_id IS NOT NULL
    ''', (filter_start_date, filter_end_date)).fetchall()
    
    # Calculate expected earnings (10% of renewals only)
    expected_earnings = 0.0
    expected_renewals = 0
    
    for tenant in expected_renewals_data:
        completed_payments = int(tenant['completed_payments'] or 0)
        # Only count if tenant has completed at least 1 payment (renewal)
        if completed_payments >= 1:
            rent_amount = float(tenant['rent_amount'] or 0)
            expected_earnings += rent_amount * 0.10  # 10% management fee
            expected_renewals += 1
    
    # Format display month name
    month_names = ['', 'January', 'February', 'March', 'April', 'May', 'June', 
                   'July', 'August', 'September', 'October', 'November', 'December']
    earnings_month_display = f"{month_names[selected_month]} {selected_year}"

    # -------------------------
    # Recent payments (last 5)
    # -------------------------
    recent_payments = conn.execute('''
        SELECT p.id, p.amount, p.payment_date, p.payment_type, t.full_name as tenant_name, 
               prop.title as property_title, u.unit_name
        FROM payments p
        JOIN tenants t ON p.tenant_id = t.id
        JOIN properties prop ON p.property_id = prop.id
        LEFT JOIN property_units u ON p.unit_id = u.id
        ORDER BY p.created_at DESC
        LIMIT 5
    ''').fetchall()
    
    # Occupancy data for charts
    vacant_props = conn.execute('SELECT COUNT(*) as count FROM properties WHERE status = "Vacant"').fetchone()['count']
    occupied_props = conn.execute('SELECT COUNT(*) as count FROM properties WHERE status = "Occupied"').fetchone()['count']
    vacant_units = conn.execute('SELECT COUNT(*) as count FROM property_units WHERE status = "Vacant"').fetchone()['count']
    occupied_units = conn.execute('SELECT COUNT(*) as count FROM property_units WHERE status = "Occupied"').fetchone()['count']
    
    # Upcoming rent dues (next 30 days)
    thirty_days_later = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime('%Y-%m-%d')
    today_str = datetime.datetime.now().strftime('%Y-%m-%d')
    
    upcoming_dues = conn.execute('''
        SELECT t.full_name as tenant_name, p.title as property_title, u.unit_name,
               t.lease_end_date, (julianday(t.lease_end_date) - julianday(?)) as days_remaining
        FROM tenants t
        JOIN properties p ON t.property_id = p.id
        LEFT JOIN property_units u ON t.unit_id = u.id
        WHERE t.lease_end_date BETWEEN ? AND ?
        ORDER BY t.lease_end_date ASC
    ''', (today_str, today_str, thirty_days_later)).fetchall()
    
    conn.close()
    
    return render_template('dashboard.html', 
                           total_properties=total_properties,
                           total_tenants=total_tenants,
                           total_landlords=total_landlords,
                           total_rent_due=total_rent_due,
                           general_balance=general_balance,
                           expected_earnings=expected_earnings,
                           expected_renewals=expected_renewals,
                           earnings_month_display=earnings_month_display,
                           selected_month=selected_month,
                           selected_year=selected_year,
                           recent_payments=recent_payments,
                           vacant_props=vacant_props,
                           occupied_props=occupied_props,
                           vacant_units=vacant_units,
                           occupied_units=occupied_units,
                           upcoming_dues=upcoming_dues,
                           now=datetime.datetime.now())

#landlord detail
"""@app.route('/landlords/<int:id>')
@login_required
def landlord_detail(id):
    conn = get_db_connection()
    
    landlord = conn.execute('SELECT * FROM landlords WHERE id = ?', (id,)).fetchone()
    
    if landlord is None:
        conn.close()
        flash('Landlord not found.')
        return redirect(url_for('dashboard'))
    
    # Fetch properties associated with this landlord
    properties = conn.execute('SELECT * FROM properties WHERE landlord_id = ?', (id,)).fetchall()
    
    conn.close()
    
    return render_template('landlords/landlord_detail.html',
                           landlord=landlord,
                           properties=properties)
"""

# Properties routes
@app.route('/properties/add', methods=['GET', 'POST'])
@login_required
def add_property():
    if request.method == 'POST':
        title = request.form.get('title')
        type = request.form.get('type')
        location = request.form.get('location')
        size = request.form.get('size')
        landlord_id = request.form.get('landlord_id')
        description = request.form.get('description')
        
        # Handle image upload
        image_path = None
        if 'property_image' in request.files:
            file = request.files['property_image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
                new_filename = f"{timestamp}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
                file.save(file_path)
                image_path = f"images/properties/{new_filename}"
        
        conn = get_db_connection()
        
        # Begin transaction
        conn.execute("BEGIN TRANSACTION")
        
        try:
            if type in ['Tenement', 'Shop']:
                # For Tenement/Shop, we don't use global price
                cursor = conn.execute(
                    '''INSERT INTO properties (title, type, location, size, landlord_id, description, image_path) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    (title, type, location, size, landlord_id, description, image_path)
                )
                property_id = cursor.lastrowid
                
                # Add units
                num_units = int(request.form.get('num_units', 0))
                for i in range(1, num_units + 1):
                    unit_name = request.form.get(f'unit_name_{i}')
                    unit_size = request.form.get(f'unit_size_{i}')
                    unit_price = request.form.get(f'unit_price_{i}')
                    
                    if unit_name and unit_price:
                        conn.execute(
                            '''INSERT INTO property_units (property_id, unit_name, size, price) 
                            VALUES (?, ?, ?, ?)''',
                            (property_id, unit_name, unit_size, float(unit_price))
                        )
            else:
                # For regular properties with single price
                price = request.form.get('price')
                conn.execute(
                    '''INSERT INTO properties (title, type, location, size, landlord_id, price, description, image_path) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                    (title, type, location, size, landlord_id, price, description, image_path)
                )
            
            # Commit transaction
            conn.commit()
            flash('Property added successfully')
            
        except Exception as e:
            # Rollback in case of error
            conn.rollback()
            flash(f'Error: {str(e)}')
        
        conn.close()
        return redirect(url_for('properties_list'))
        
    conn = get_db_connection()
    landlords = conn.execute('SELECT id, full_name FROM landlords').fetchall()
    conn.close()
    
    return render_template('properties/add_property.html', landlords=landlords)

# ✅ Updated Properties List Route
@app.route('/properties/list')
@login_required
def properties_list():
    conn = get_db_connection()

    # Get all properties with landlord info and occupancy status
    properties = conn.execute('''
        SELECT p.*, l.full_name AS landlord_name,
               (SELECT COUNT(*) FROM property_units WHERE property_id = p.id) AS total_units,
               (SELECT COUNT(*) FROM property_units WHERE property_id = p.id AND status = 'Occupied') AS occupied_units
        FROM properties p
        JOIN landlords l ON p.landlord_id = l.id
        ORDER BY p.created_at DESC
    ''').fetchall()

    # Get all tenants who are not yet linked to any property
    unlinked_tenants = conn.execute('''
        SELECT id, full_name 
        FROM tenants 
        WHERE property_id IS NULL OR property_id = ''
        ORDER BY full_name ASC
    ''').fetchall()

    conn.close()

    return render_template(
        'properties/properties_list.html',
        properties=properties,
        unlinked_tenants=unlinked_tenants
    )

# ✅ Route to Link Tenant to Property with Lease Dates
@app.route('/link_tenant_to_property', methods=['POST'])
@login_required
def link_tenant_to_property():
    tenant_id = request.form.get('tenant_id')
    property_id = request.form.get('property_id')
    unit_id = request.form.get('unit_id')
    lease_start_date = request.form.get('lease_start_date')
    lease_end_date = request.form.get('lease_end_date')

    conn = get_db_connection()
    cur = conn.cursor()

    # Update the tenant record
    cur.execute('''
        UPDATE tenants
        SET property_id = ?, unit_id = ?, lease_start_date = ?, lease_end_date = ?
        WHERE id = ?
    ''', (property_id, unit_id, lease_start_date, lease_end_date, tenant_id))

    # Update property/unit status
    if unit_id and unit_id.strip():
        cur.execute('UPDATE property_units SET status = "Occupied" WHERE id = ?', (unit_id,))
    else:
        cur.execute('UPDATE properties SET status = "Occupied" WHERE id = ?', (property_id,))

    conn.commit()
    conn.close()

    flash('Tenant successfully linked to property and lease recorded.', 'success')
    return redirect(url_for('properties_list'))


@app.route('/properties/vacant')
@login_required
def vacant_properties():
    conn = get_db_connection()
    
    # Get vacant standalone properties
    vacant_properties = conn.execute('''
        SELECT p.*, l.full_name as landlord_name
        FROM properties p
        JOIN landlords l ON p.landlord_id = l.id
        WHERE p.status = 'Vacant' AND p.type NOT IN ('Tenement', 'Shop')
        ORDER BY p.created_at DESC
    ''').fetchall()
    
    # Get properties with vacant units
    properties_with_vacant_units = conn.execute('''
        SELECT p.*, l.full_name as landlord_name,
               (SELECT COUNT(*) FROM property_units WHERE property_id = p.id) as total_units,
               (SELECT COUNT(*) FROM property_units WHERE property_id = p.id AND status = 'Vacant') as vacant_units
        FROM properties p
        JOIN landlords l ON p.landlord_id = l.id
        WHERE p.type IN ('Tenement', 'Shop') 
        AND EXISTS (SELECT 1 FROM property_units WHERE property_id = p.id AND status = 'Vacant')
        ORDER BY p.created_at DESC
    ''').fetchall()
    
    # Get all vacant units
    vacant_units = conn.execute('''
        SELECT u.*, p.title as property_title, p.location, l.full_name as landlord_name
        FROM property_units u
        JOIN properties p ON u.property_id = p.id
        JOIN landlords l ON p.landlord_id = l.id
        WHERE u.status = 'Vacant'
        ORDER BY u.created_at DESC
    ''').fetchall()
    
    conn.close()
    
    return render_template('properties/vacant_properties.html', 
                          vacant_properties=vacant_properties,
                          properties_with_vacant_units=properties_with_vacant_units,
                          vacant_units=vacant_units)

@app.route('/properties/occupied')
@login_required
def occupied_properties():
    conn = get_db_connection()
    
    # 1️⃣ Occupied standalone properties (linked directly to tenants)
    occupied_properties = conn.execute('''
        SELECT p.*, l.full_name AS landlord_name,
               t.id AS tenant_id, t.full_name AS tenant_name
        FROM properties p
        JOIN landlords l ON p.landlord_id = l.id
        JOIN tenants t ON t.property_id = p.id AND t.unit_id IS NULL
        WHERE p.status = 'Occupied'
        ORDER BY p.created_at DESC
    ''').fetchall()

    # 2️⃣ Properties that have some occupied units (multi-unit)
    properties_with_occupied_units = conn.execute('''
        SELECT p.*, l.full_name AS landlord_name,
               (SELECT COUNT(*) FROM property_units WHERE property_id = p.id) AS total_units,
               (SELECT COUNT(*) FROM property_units WHERE property_id = p.id AND status = 'Occupied') AS occupied_units
        FROM properties p
        JOIN landlords l ON p.landlord_id = l.id
        WHERE p.type IN ('Tenement', 'Shop')
          AND EXISTS (SELECT 1 FROM property_units WHERE property_id = p.id AND status = 'Occupied')
        ORDER BY p.created_at DESC
    ''').fetchall()

    # 3️⃣ Occupied units (individual unit info)
    occupied_units = conn.execute('''
        SELECT u.*, p.title AS property_title, p.location, 
               l.full_name AS landlord_name,
               t.id AS tenant_id, t.full_name AS tenant_name
        FROM property_units u
        JOIN properties p ON u.property_id = p.id
        JOIN landlords l ON p.landlord_id = l.id
        JOIN tenants t ON t.unit_id = u.id
        WHERE u.status = 'Occupied'
        ORDER BY u.created_at DESC
    ''').fetchall()

    conn.close()
    
    return render_template('properties/occupied_properties.html',
                           occupied_properties=occupied_properties,
                           properties_with_occupied_units=properties_with_occupied_units,
                           occupied_units=occupied_units)

@app.route('/properties/assign-tenant', methods=['POST'])
@login_required
def assign_tenant():
    """
    Assign a tenant to a property or specific unit.
    Accepts JSON body (recommended) or form POST:
      { "tenant_id": <int>, "property_id": <int>, "unit_id": <int|null> }
    """
    data = request.get_json(silent=True) or request.form
    tenant_id = data.get('tenant_id')
    property_id = data.get('property_id')
    unit_id = data.get('unit_id') or None

    if not tenant_id or not property_id:
        return jsonify({'success': False, 'message': 'Missing tenant_id or property_id'}), 400

    conn = get_db_connection()
    try:
        conn.execute("BEGIN TRANSACTION")

        # Verify tenant exists and is unassigned
        tenant = conn.execute('SELECT id, property_id, unit_id FROM tenants WHERE id = ?', (tenant_id,)).fetchone()
        if not tenant:
            conn.rollback()
            return jsonify({'success': False, 'message': 'Tenant not found'}), 404

        if tenant['property_id'] or tenant['unit_id']:
            conn.rollback()
            return jsonify({'success': False, 'message': 'Tenant already assigned to a property or unit'}), 400

        # If unit assignment requested
        if unit_id:
            unit = conn.execute('SELECT id, property_id, status FROM property_units WHERE id = ?', (unit_id,)).fetchone()
            if not unit:
                conn.rollback()
                return jsonify({'success': False, 'message': 'Unit not found'}), 404
            if int(unit['property_id']) != int(property_id):
                conn.rollback()
                return jsonify({'success': False, 'message': 'Unit does not belong to the selected property'}), 400
            if unit['status'] != 'Vacant':
                conn.rollback()
                return jsonify({'success': False, 'message': 'Unit is not available'}), 409

            # Assign tenant and mark unit occupied
            conn.execute('UPDATE tenants SET property_id = ?, unit_id = ? WHERE id = ?', (property_id, unit_id, tenant_id))
            conn.execute('UPDATE property_units SET status = ?, tenant_id = ? WHERE id = ?', ('Occupied', tenant_id, unit_id))

            # If all units now occupied update property status
            total_units = conn.execute('SELECT COUNT(*) AS cnt FROM property_units WHERE property_id = ?', (property_id,)).fetchone()['cnt']
            occupied_units = conn.execute('SELECT COUNT(*) AS cnt FROM property_units WHERE property_id = ? AND status = "Occupied"', (property_id,)).fetchone()['cnt']
            if total_units and total_units == occupied_units:
                conn.execute('UPDATE properties SET status = ? WHERE id = ?', ('Occupied', property_id))

        else:
            # Assign tenant to a standalone property
            prop = conn.execute('SELECT id, status FROM properties WHERE id = ?', (property_id,)).fetchone()
            if not prop:
                conn.rollback()
                return jsonify({'success': False, 'message': 'Property not found'}), 404
            if prop['status'] != 'Vacant':
                conn.rollback()
                return jsonify({'success': False, 'message': 'Property is not available'}), 409

            conn.execute('UPDATE tenants SET property_id = ?, unit_id = NULL WHERE id = ?', (property_id, tenant_id))
            conn.execute('UPDATE properties SET status = ? WHERE id = ?', ('Occupied', property_id))

        conn.commit()
        return jsonify({'success': True, 'message': 'Tenant assigned successfully'})

    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

    finally:
        conn.close()

@app.route('/properties/<int:property_id>')
@login_required
def property_detail(property_id):
    conn = get_db_connection()
    
    property = conn.execute('''
        SELECT p.*, l.full_name as landlord_name
        FROM properties p
        JOIN landlords l ON p.landlord_id = l.id
        WHERE p.id = ?
    ''', (property_id,)).fetchone()
    
    units = []
    tenants = []
    
    if property['type'] in ['Tenement', 'Shop']:
        units = conn.execute('''
            SELECT u.*, t.full_name as tenant_name
            FROM property_units u
            LEFT JOIN tenants t ON u.tenant_id = t.id
            WHERE u.property_id = ?
            ORDER BY u.unit_name
        ''', (property_id,)).fetchall()
    else:
        tenants = conn.execute('''
            SELECT t.*
            FROM tenants t
            WHERE t.property_id = ? AND t.unit_id IS NULL
        ''', (property_id,)).fetchall()
    
    # Get payment history for this property
    payments = conn.execute('''
        SELECT p.*, t.full_name as tenant_name, u.unit_name
        FROM payments p
        JOIN tenants t ON p.tenant_id = t.id
        LEFT JOIN property_units u ON p.unit_id = u.id
        WHERE p.property_id = ?
        ORDER BY p.payment_date DESC
    ''', (property_id,)).fetchall()
    
    conn.close()
    
    return render_template('properties/property_detail.html', 
                          property=property,
                          units=units,
                          tenants=tenants,
                          payments=payments)

@app.route('/properties/available-units/<int:property_id>')
@login_required
def available_units(property_id):
    conn = get_db_connection()
    
    units = conn.execute('''
        SELECT id, unit_name, size, price
        FROM property_units
        WHERE property_id = ? AND status = 'Vacant'
    ''', (property_id,)).fetchall()
    
    conn.close()
    
    return jsonify([dict(unit) for unit in units])

# Tenant routes
@app.route('/tenants/add', methods=['GET', 'POST'])
@login_required
def add_tenant():
    if request.method == 'POST':
        # Extract tenant data from form
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        whatsapp = request.form.get('whatsapp')
        email = request.form.get('email')
        id_number = request.form.get('id_number')
        medium_of_reach = request.form.get('medium_of_reach')
        
        # NEW FIELDS
        marital_status = request.form.get('marital_status')
        spouse_name = request.form.get('spouse_name')
        spouse_phone = request.form.get('spouse_phone')
        number_of_children = request.form.get('number_of_children')
        
        permanent_address = request.form.get('permanent_address')
        occupation = request.form.get('occupation')
        employer = request.form.get('employer')
        lease_start_date = request.form.get('lease_start_date')
        lease_end_date = request.form.get('lease_end_date')
        receipt_info = request.form.get('receipt_info')
        bank_name = request.form.get('bank_name')
        account_number = request.form.get('account_number')
        age = request.form.get('age')
        sex = request.form.get('sex')
        state_of_origin = request.form.get('state_of_origin')
        nationality = request.form.get('nationality')
        tribe = request.form.get('tribe')
        remarks = request.form.get('remarks')
        guarantor_name = request.form.get('guarantor_name')
        guarantor_phone = request.form.get('guarantor_phone')
        guarantor_address = request.form.get('guarantor_address')
        next_of_kin_name = request.form.get('next_of_kin_name')
        next_of_kin_address = request.form.get('next_of_kin_address')
        property_id = request.form.get('property_id')
        unit_id = request.form.get('unit_id')
        
        conn = get_db_connection()
        
        # Begin transaction
        conn.execute("BEGIN TRANSACTION")
        
        try:
            # Insert tenant with NEW FIELDS
            cursor = conn.execute('''
                INSERT INTO tenants (
                    full_name, phone, whatsapp, email, id_number, medium_of_reach,
                    marital_status, spouse_name, spouse_phone, number_of_children,
                    permanent_address, occupation, employer, lease_start_date, lease_end_date, receipt_info,
                    bank_name, account_number, age, sex, state_of_origin, nationality, tribe,
                    remarks, guarantor_name, guarantor_phone, guarantor_address,
                    next_of_kin_name, next_of_kin_address, property_id, unit_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                full_name, phone, whatsapp, email, id_number, medium_of_reach,
                marital_status, spouse_name, spouse_phone, number_of_children,
                permanent_address, occupation, employer, lease_start_date, lease_end_date, receipt_info,
                bank_name, account_number, age, sex, state_of_origin, nationality, tribe,
                remarks, guarantor_name, guarantor_phone, guarantor_address,
                next_of_kin_name, next_of_kin_address, property_id, unit_id
            ))
            
            tenant_id = cursor.lastrowid
            
            # Update property or unit status to Occupied
            if unit_id:
                conn.execute('''
                    UPDATE property_units 
                    SET status = 'Occupied', tenant_id = ? 
                    WHERE id = ?
                ''', (tenant_id, unit_id))
                
                # Check if all units are occupied and update property status
                total_units = conn.execute('''
                    SELECT COUNT(*) as count FROM property_units WHERE property_id = ?
                ''', (property_id,)).fetchone()['count']
                
                occupied_units = conn.execute('''
                    SELECT COUNT(*) as count FROM property_units 
                    WHERE property_id = ? AND status = 'Occupied'
                ''', (property_id,)).fetchone()['count']
                
                if total_units == occupied_units:
                    conn.execute('''
                        UPDATE properties SET status = 'Occupied' WHERE id = ?
                    ''', (property_id,))
            else:
                conn.execute('''
                    UPDATE properties SET status = 'Occupied' WHERE id = ?
                ''', (property_id,))
            
            # Commit transaction
            conn.commit()
            flash('Tenant added successfully')
            
        except Exception as e:
            # Rollback in case of error
            conn.rollback()
            flash(f'Error: {str(e)}')
        
        conn.close()
        return redirect(url_for('tenants_list'))
    
    conn = get_db_connection()
    
    # Get vacant properties (excluding tenements/shops)
    vacant_properties = conn.execute('''
        SELECT p.*, l.full_name as landlord_name
        FROM properties p
        JOIN landlords l ON p.landlord_id = l.id
        WHERE p.status = 'Vacant' AND p.type NOT IN ('Tenement', 'Shop')
    ''').fetchall()
    
    # Get properties with vacant units
    properties_with_vacant_units = conn.execute('''
        SELECT DISTINCT p.id, p.title, p.location, l.full_name as landlord_name
        FROM properties p
        JOIN landlords l ON p.landlord_id = l.id
        JOIN property_units u ON u.property_id = p.id
        WHERE p.type IN ('Tenement', 'Shop') AND u.status = 'Vacant'
    ''').fetchall()
    
    conn.close()
    
    return render_template('tenants/add_tenant.html', 
                          vacant_properties=vacant_properties,
                          properties_with_vacant_units=properties_with_vacant_units)


@app.route('/tenants/list')
@login_required
def tenants_list():
    sort_by = request.args.get('sort_by', 'lease_end_date')
    
    conn = get_db_connection()
    
    query = '''
        SELECT t.*, p.title as property_title, 
               CASE WHEN u.unit_name IS NOT NULL THEN u.unit_name ELSE '' END as unit_name,
               l.full_name as landlord_name,
               (julianday(t.lease_end_date) - julianday('now')) as days_remaining
        FROM tenants t
        JOIN properties p ON t.property_id = p.id
        JOIN landlords l ON p.landlord_id = l.id
        LEFT JOIN property_units u ON t.unit_id = u.id
    '''
    
    if sort_by == 'lease_end_date':
        query += ' ORDER BY t.lease_end_date ASC'
    elif sort_by == 'property_title':
        query += ' ORDER BY p.title ASC'
    elif sort_by == 'landlord_name':
        query += ' ORDER BY l.full_name ASC'
    else:
        query += ' ORDER BY t.lease_end_date ASC'  # Default sorting
    
    tenants = conn.execute(query).fetchall()
    
    conn.close()
    
    return render_template('tenants/tenants_list.html', tenants=tenants, sort_by=sort_by)

@app.route('/tenants/<int:tenant_id>')
@login_required
def tenant_detail(tenant_id):
    conn = get_db_connection()
    
    tenant = conn.execute('''
        SELECT t.*, p.title as property_title, u.unit_name,
               l.full_name as landlord_name
        FROM tenants t
        JOIN properties p ON t.property_id = p.id
        JOIN landlords l ON p.landlord_id = l.id
        LEFT JOIN property_units u ON t.unit_id = u.id
        WHERE t.id = ?
    ''', (tenant_id,)).fetchone()
    
    # Get payment history
    payments = conn.execute('''
        SELECT p.*
        FROM payments p
        WHERE p.tenant_id = ?
        ORDER BY p.payment_date DESC
    ''', (tenant_id,)).fetchall()
    
    # Get documents
    documents = conn.execute('''
        SELECT d.*
        FROM documents d
        WHERE d.tenant_id = ?
        ORDER BY d.upload_date DESC
    ''', (tenant_id,)).fetchall()
    
    conn.close()
    
    return render_template('tenants/tenant_detail.html',
                          tenant=tenant,
                          payments=payments,
                          documents=documents)

# Landlord routes
@app.route('/landlords/add', methods=['GET', 'POST'])
@login_required
def add_landlord():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        address = request.form.get('address')
        id_number = request.form.get('id_number')
        bank_name = request.form.get('bank_name')
        account_number = request.form.get('account_number')
        
        conn = get_db_connection()
        
        try:
            conn.execute('''
                INSERT INTO landlords (full_name, phone, email, address, id_number, bank_name, account_number)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (full_name, phone, email, address, id_number, bank_name, account_number))
            
            conn.commit()
            flash('Landlord added successfully')
            
        except Exception as e:
            flash(f'Error: {str(e)}')
        
        conn.close()
        return redirect(url_for('landlords_list'))
    
    return render_template('landlords/add_landlord.html')

@app.route('/landlords/list')
@login_required
def landlords_list():
    conn = get_db_connection()
    
    landlords = conn.execute('''
        SELECT l.*, 
               (SELECT COUNT(*) FROM properties WHERE landlord_id = l.id) as total_properties
        FROM landlords l
        ORDER BY l.full_name
    ''').fetchall()
    
    conn.close()
    
    return render_template('landlords/landlords_list.html', landlords=landlords)

@app.route('/landlords/<int:landlord_id>')
@login_required
def landlord_detail(landlord_id):
    conn = get_db_connection()
    
    landlord = conn.execute('SELECT * FROM landlords WHERE id = ?', (landlord_id,)).fetchone()
    
    # Get properties
    properties = conn.execute('''
        SELECT p.*, 
               (SELECT COUNT(*) FROM property_units WHERE property_id = p.id) as total_units,
               (SELECT COUNT(*) FROM property_units WHERE property_id = p.id AND status = 'Occupied') as occupied_units
        FROM properties p
        WHERE p.landlord_id = ?
        ORDER BY p.title
    ''', (landlord_id,)).fetchall()
    
    # Get transaction history
    transactions = conn.execute('''
        SELECT a.*, p.title as property_title, u.unit_name
        FROM accounts a
        LEFT JOIN properties p ON a.property_id = p.id
        LEFT JOIN property_units u ON a.unit_id = u.id
        WHERE a.landlord_id = ?
        ORDER BY a.transaction_date DESC
    ''', (landlord_id,)).fetchall()
    
    conn.close()
    
    return render_template('landlords/landlord_detail.html',
                          landlord=landlord,
                          properties=properties,
                          transactions=transactions)

# Payment routes
# Payment routes - FIXED VERSION
# Payment routes - FIXED VERSION (Using accounts table)
# Payment routes - FULLY FIXED VERSION
@app.route('/payments/add', methods=['GET', 'POST'])
@login_required
def add_payment():
    if request.method == 'POST':
        tenant_id = request.form.get('tenant_id')
        amount = float(request.form.get('amount'))
        payment_type = request.form.get('payment_type')
        payment_method = request.form.get('payment_method')
        payment_date = request.form.get('payment_date', datetime.datetime.now().strftime('%Y-%m-%d'))
        description = request.form.get('description')
        
        conn = get_db_connection()
        conn.execute("BEGIN TRANSACTION")
        
        try:
            # Get tenant info
            tenant = conn.execute('''
                SELECT t.*, p.id as property_id, p.landlord_id, u.id as unit_id, 
                       CASE 
                           WHEN t.unit_id IS NOT NULL THEN u.price 
                           ELSE p.price 
                       END as rent_amount
                FROM tenants t
                JOIN properties p ON t.property_id = p.id
                LEFT JOIN property_units u ON t.unit_id = u.id
                WHERE t.id = ?
            ''', (tenant_id,)).fetchone()
            
            if not tenant:
                conn.rollback()
                conn.close()
                return jsonify({'success': False, 'message': 'Tenant not found'}), 404
            
            property_id = tenant['property_id']
            landlord_id = tenant['landlord_id']
            unit_id = tenant['unit_id']
            rent_amount = float(tenant['rent_amount'])
            
            # Check for outstanding balance
            outstanding = conn.execute('''
                SELECT SUM(balance_due) as total_outstanding
                FROM payments
                WHERE tenant_id = ? AND balance_due > 0
            ''', (tenant_id,)).fetchone()
            
            total_outstanding = float(outstanding['total_outstanding'] or 0)
            
            # Check payment history for renewal detection
            completed_cycles = conn.execute('''
                SELECT COUNT(*) as count
                FROM payments
                WHERE tenant_id = ? AND payment_type = 'Full' AND balance_due = 0
            ''', (tenant_id,)).fetchone()['count']
            
            is_renewal = (completed_cycles >= 1)
            
            # Calculate payment type and balance
            if total_outstanding > 0:
                # Completing previous partial
                if amount > total_outstanding:
                    conn.rollback()
                    conn.close()
                    return jsonify({
                        'success': False, 
                        'message': f'Payment amount (₦{amount:,.2f}) exceeds outstanding balance (₦{total_outstanding:,.2f}).'
                    }), 400
                
                payment_type = 'Full' if amount >= total_outstanding else 'Partial'
                balance_due = 0 if amount >= total_outstanding else total_outstanding - amount
                
            else:
                # New payment cycle
                if amount > rent_amount:
                    conn.rollback()
                    conn.close()
                    return jsonify({
                        'success': False, 
                        'message': f'Payment amount (₦{amount:,.2f}) exceeds rent amount (₦{rent_amount:,.2f}).'
                    }), 400
                
                payment_type = 'Full' if amount >= rent_amount else 'Partial'
                balance_due = 0 if amount >= rent_amount else rent_amount - amount
            
            # Calculate credit/debit for this payment
            # ✅ KEY: Store credit/debit directly in payments table
            if balance_due == 0:
                # Payment complete
                if is_renewal and total_outstanding == 0:
                    # Renewal - apply 10% fee
                    deduction = amount * 0.10
                    credit_amount = amount - deduction
                    debit_amount = deduction
                    success_message = f'✅ Renewal payment! ₦{credit_amount:,.2f} credited (10% fee: ₦{debit_amount:,.2f})'
                else:
                    # First payment or completing partial - no fee
                    credit_amount = amount
                    debit_amount = 0
                    success_message = f'✅ Payment completed! ₦{amount:,.2f} credited to landlord.'
            else:
                # Partial - no credit yet
                credit_amount = 0
                debit_amount = 0
                success_message = f'📝 Partial payment: ₦{amount:,.2f}. Remaining: ₦{balance_due:,.2f}.'
            
            # Insert payment with credit/debit columns
            cursor = conn.execute('''
                INSERT INTO payments (
                    tenant_id, property_id, unit_id, amount, payment_type, payment_method, 
                    payment_date, balance_due, description, credit, debit
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                tenant_id, property_id, unit_id, amount, payment_type, payment_method,
                payment_date, balance_due, description, credit_amount, debit_amount
            ))
            
            # Clear old partial payments if completing
            if total_outstanding > 0 and balance_due == 0:
                conn.execute('''
                    UPDATE payments 
                    SET balance_due = 0, payment_type = 'Full'
                    WHERE tenant_id = ? AND balance_due > 0 AND id != ?
                ''', (tenant_id, cursor.lastrowid))
            
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'message': success_message})
            
        except Exception as e:
            conn.rollback()
            conn.close()
            return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    
    # GET request
    conn = get_db_connection()
    
    tenants = conn.execute('''
        SELECT t.id, t.full_name, p.title as property_title, u.unit_name,
               CASE WHEN t.unit_id IS NOT NULL THEN u.price ELSE p.price END as rent_amount,
               COALESCE((SELECT SUM(balance_due) FROM payments WHERE tenant_id = t.id AND balance_due > 0), 0) as outstanding_balance
        FROM tenants t
        JOIN properties p ON t.property_id = p.id
        LEFT JOIN property_units u ON t.unit_id = u.id
        WHERE t.property_id IS NOT NULL
        ORDER BY t.full_name
    ''').fetchall()
    
    conn.close()
    
    return render_template('payments/add_payment.html', tenants=tenants)

@app.route('/payments/list')
@login_required
def payments_list():
    conn = get_db_connection()
    
    payments = conn.execute('''
        SELECT p.*, t.full_name as tenant_name, 
               prop.title as property_title, u.unit_name,
               l.full_name as landlord_name
        FROM payments p
        JOIN tenants t ON p.tenant_id = t.id
        JOIN properties prop ON p.property_id = prop.id
        JOIN landlords l ON prop.landlord_id = l.id
        LEFT JOIN property_units u ON p.unit_id = u.id
        ORDER BY p.payment_date DESC
    ''').fetchall()
    
    conn.close()
    
    return render_template('payments/payments_list.html', payments=payments)

@app.route('/payments/<int:payment_id>')
@login_required
def payment_detail(payment_id):
    conn = get_db_connection()
    
    payment = conn.execute('''
        SELECT p.*, t.full_name as tenant_name, 
               prop.title as property_title, u.unit_name,
               l.full_name as landlord_name
        FROM payments p
        JOIN tenants t ON p.tenant_id = t.id
        JOIN properties prop ON p.property_id = prop.id
        JOIN landlords l ON prop.landlord_id = l.id
        LEFT JOIN property_units u ON p.unit_id = u.id
        WHERE p.id = ?
    ''', (payment_id,)).fetchone()
    
    # Get related ledger entries
    ledger_entries = conn.execute('''
        SELECT a.*
        FROM accounts a
        WHERE a.payment_id = ?
        ORDER BY a.created_at
    ''', (payment_id,)).fetchall()
    
    conn.close()
    
    return render_template('payments/payment_detail.html',
                          payment=payment,
                          ledger_entries=ledger_entries)

# Document routes
@app.route('/documents/add', methods=['GET', 'POST'])
@login_required
def add_document():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        document_type = request.form.get('document_type')
        
        # Get related entity ID based on document type
        entity_id = None
        if document_type == 'tenant':
            entity_id = request.form.get('tenant_id')
        elif document_type == 'property':
            entity_id = request.form.get('property_id')
        elif document_type == 'landlord':
            entity_id = request.form.get('landlord_id')
        
        # Handle file upload
        file_path = None
        if 'document_file' in request.files:
            file = request.files['document_file']
            if file and file.filename:
                # Create documents directory if it doesn't exist
                docs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'documents')
                os.makedirs(docs_dir, exist_ok=True)
                
                filename = secure_filename(file.filename)
                timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
                new_filename = f"{timestamp}_{filename}"
                file_path = os.path.join(docs_dir, new_filename)
                file.save(file_path)
                file_path = f"documents/{new_filename}"
        
        conn = get_db_connection()
        
        try:
            # Insert document record
            if document_type == 'tenant':
                conn.execute('''
                    INSERT INTO documents (
                        title, description, file_path, document_type, tenant_id, upload_date
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (title, description, file_path, document_type, entity_id, datetime.datetime.now().strftime('%Y-%m-%d')))
            elif document_type == 'property':
                conn.execute('''
                    INSERT INTO documents (
                        title, description, file_path, document_type, property_id, upload_date
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (title, description, file_path, document_type, entity_id, datetime.datetime.now().strftime('%Y-%m-%d')))
            elif document_type == 'landlord':
                conn.execute('''
                    INSERT INTO documents (
                        title, description, file_path, document_type, landlord_id, upload_date
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (title, description, file_path, document_type, entity_id, datetime.datetime.now().strftime('%Y-%m-%d')))
            
            conn.commit()
            flash('Document added successfully')
            
        except Exception as e:
            flash(f'Error: {str(e)}')
        
        conn.close()
        return redirect(url_for('documents_list'))
    
    conn = get_db_connection()
    
    tenants = conn.execute('SELECT id, full_name FROM tenants ORDER BY full_name').fetchall()
    properties = conn.execute('SELECT id, title FROM properties ORDER BY title').fetchall()
    landlords = conn.execute('SELECT id, full_name FROM landlords ORDER BY full_name').fetchall()
    
    conn.close()
    
    return render_template('documents/add_document.html',
                          tenants=tenants,
                          properties=properties,
                          landlords=landlords)

@app.route('/documents/list')
@login_required
def documents_list():
    document_type = request.args.get('type', 'all')
    
    conn = get_db_connection()
    
    query = '''
        SELECT d.*, 
               t.full_name as tenant_name,
               p.title as property_title,
               l.full_name as landlord_name
        FROM documents d
        LEFT JOIN tenants t ON d.tenant_id = t.id
        LEFT JOIN properties p ON d.property_id = p.id
        LEFT JOIN landlords l ON d.landlord_id = l.id
    '''
    
    if document_type != 'all':
        query += f" WHERE d.document_type = '{document_type}'"
    
    query += " ORDER BY d.upload_date DESC"
    
    documents = conn.execute(query).fetchall()
    
    conn.close()
    
    return render_template('documents/documents_list.html',
                          documents=documents,
                          document_type=document_type)

# Reports routes
@app.route('/reports/occupancy')
@login_required
def occupancy_report():
    conn = get_db_connection()
    
    # Get overall occupancy statistics
    total_properties = conn.execute('SELECT COUNT(*) as count FROM properties').fetchone()['count']
    occupied_properties = conn.execute('SELECT COUNT(*) as count FROM properties WHERE status = "Occupied"').fetchone()['count']
    vacant_properties = total_properties - occupied_properties
    
    total_units = conn.execute('SELECT COUNT(*) as count FROM property_units').fetchone()['count']
    occupied_units = conn.execute('SELECT COUNT(*) as count FROM property_units WHERE status = "Occupied"').fetchone()['count']
    vacant_units = total_units - occupied_units
    
    # Get occupancy by property type
    occupancy_by_type = conn.execute('''
        SELECT p.type, COUNT(*) as total,
               SUM(CASE WHEN p.status = 'Occupied' THEN 1 ELSE 0 END) as occupied
        FROM properties p
        GROUP BY p.type
    ''').fetchall()
    
    # Get occupancy by location
    occupancy_by_location = conn.execute('''
        SELECT p.location, COUNT(*) as total,
               SUM(CASE WHEN p.status = 'Occupied' THEN 1 ELSE 0 END) as occupied
        FROM properties p
        GROUP BY p.location
    ''').fetchall()
    
    # Get lease expiry in next 90 days
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    ninety_days_later = (datetime.datetime.now() + datetime.timedelta(days=90)).strftime('%Y-%m-%d')
    
    expiring_leases = conn.execute('''
        SELECT t.full_name, p.title as property_title, u.unit_name,
               t.lease_end_date, julianday(t.lease_end_date) - julianday(?) as days_remaining
        FROM tenants t
        JOIN properties p ON t.property_id = p.id
        LEFT JOIN property_units u ON t.unit_id = u.id
        WHERE t.lease_end_date BETWEEN ? AND ?
        ORDER BY t.lease_end_date ASC
    ''', (today, today, ninety_days_later)).fetchall()
    
    conn.close()
    
    return render_template('reports/occupancy.html',
                          total_properties=total_properties,
                          occupied_properties=occupied_properties,
                          vacant_properties=vacant_properties,
                          total_units=total_units,
                          occupied_units=occupied_units,
                          vacant_units=vacant_units,
                          occupancy_by_type=occupancy_by_type,
                          occupancy_by_location=occupancy_by_location,
                          expiring_leases=expiring_leases)

@app.route('/reports/revenue')
@login_required
def revenue_report():
    # Get date range parameters
    start_date = request.args.get('start_date', (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.datetime.now().strftime('%Y-%m-%d'))
    
    conn = get_db_connection()
    
    # Get total revenue in period
    total_revenue = conn.execute('''
        SELECT SUM(amount) as total
        FROM payments
        WHERE payment_date BETWEEN ? AND ?
    ''', (start_date, end_date)).fetchone()['total'] or 0
    
    # Get revenue by payment type
    revenue_by_type = conn.execute('''
        SELECT payment_type, SUM(amount) as total
        FROM payments
        WHERE payment_date BETWEEN ? AND ?
        GROUP BY payment_type
    ''', (start_date, end_date)).fetchall()
    
    # Get revenue by property type
    revenue_by_property_type = conn.execute('''
        SELECT p.type, SUM(pay.amount) as total
        FROM payments pay
        JOIN properties p ON pay.property_id = p.id
        WHERE pay.payment_date BETWEEN ? AND ?
        GROUP BY p.type
    ''', (start_date, end_date)).fetchall()
    
    # Get revenue by landlord
    revenue_by_landlord = conn.execute('''
        SELECT l.full_name, SUM(pay.amount) as total,
               SUM(CASE WHEN a.transaction_type = 'Fee' THEN a.amount ELSE 0 END) as fees
        FROM payments pay
        JOIN properties p ON pay.property_id = p.id
        JOIN landlords l ON p.landlord_id = l.id
        LEFT JOIN accounts a ON a.payment_id = pay.id
        WHERE pay.payment_date BETWEEN ? AND ?
        GROUP BY l.id
        ORDER BY total DESC
    ''', (start_date, end_date)).fetchall()
    
    # Get monthly revenue trend (last 12 months)
    twelve_months_ago = (datetime.datetime.now() - datetime.timedelta(days=365)).strftime('%Y-%m-%d')
    
    monthly_revenue = conn.execute('''
        SELECT strftime('%Y-%m', payment_date) as month, SUM(amount) as total
        FROM payments
        WHERE payment_date BETWEEN ? AND ?
        GROUP BY strftime('%Y-%m', payment_date)
        ORDER BY month
    ''', (twelve_months_ago, end_date)).fetchall()
    
    # Get outstanding balances
    outstanding_balances = conn.execute('''
        SELECT t.full_name, p.title as property_title, u.unit_name,
               SUM(pay.balance_due) as total_due
        FROM payments pay
        JOIN tenants t ON pay.tenant_id = t.id
        JOIN properties p ON pay.property_id = p.id
        LEFT JOIN property_units u ON pay.unit_id = u.id
        WHERE pay.balance_due > 0
        GROUP BY pay.tenant_id
        ORDER BY total_due DESC
    ''').fetchall()
    
    conn.close()
    
    return render_template('reports/revenue.html',
                          start_date=start_date,
                          end_date=end_date,
                          total_revenue=total_revenue,
                          revenue_by_type=revenue_by_type,
                          revenue_by_property_type=revenue_by_property_type,
                          revenue_by_landlord=revenue_by_landlord,
                          monthly_revenue=monthly_revenue,
                          outstanding_balances=outstanding_balances)

@app.route('/reports/tenants')
@login_required
def tenants_report():
    conn = get_db_connection()
    
    # Get total tenant count
    total_tenants = conn.execute('SELECT COUNT(*) as count FROM tenants').fetchone()['count']
    
    # Get tenants by property type
    tenants_by_property_type = conn.execute('''
        SELECT p.type, COUNT(*) as count
        FROM tenants t
        JOIN properties p ON t.property_id = p.id
        GROUP BY p.type
    ''').fetchall()
    
    # Get tenants by location
    tenants_by_location = conn.execute('''
        SELECT p.location, COUNT(*) as count
        FROM tenants t
        JOIN properties p ON t.property_id = p.id
        GROUP BY p.location
    ''').fetchall()
    
    # Get tenants with expiring leases
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    thirty_days_later = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime('%Y-%m-%d')
    ninety_days_later = (datetime.datetime.now() + datetime.timedelta(days=90)).strftime('%Y-%m-%d')
    
    tenants_expiring_30d = conn.execute('''
        SELECT COUNT(*) as count
        FROM tenants
        WHERE lease_end_date BETWEEN ? AND ?
    ''', (today, thirty_days_later)).fetchone()['count']
    
    tenants_expiring_90d = conn.execute('''
        SELECT COUNT(*) as count
        FROM tenants
        WHERE lease_end_date BETWEEN ? AND ?
    ''', (today, ninety_days_later)).fetchone()['count']
    
    # Get tenants by tenure length
    tenants_by_tenure = conn.execute('''
        SELECT 
            CASE 
                WHEN julianday('now') - julianday(lease_start_date) < 90 THEN 'Less than 3 months'
                WHEN julianday('now') - julianday(lease_start_date) < 180 THEN '3-6 months'
                WHEN julianday('now') - julianday(lease_start_date) < 365 THEN '6-12 months'
                ELSE 'Over 1 year'
            END as tenure,
            COUNT(*) as count
        FROM tenants
        GROUP BY tenure
    ''').fetchall()
    
    # Get tenant listing with details
    tenants = conn.execute('''
        SELECT t.full_name, t.phone, t.email, t.lease_start_date, t.lease_end_date,
               p.title as property_title, u.unit_name,
               julianday(t.lease_end_date) - julianday('now') as days_remaining
        FROM tenants t
        JOIN properties p ON t.property_id = p.id
        LEFT JOIN property_units u ON t.unit_id = u.id
        ORDER BY days_remaining ASC
    ''').fetchall()
    
    conn.close()
    
    return render_template('reports/tenants.html',
                          total_tenants=total_tenants,
                          tenants_by_property_type=tenants_by_property_type,
                          tenants_by_location=tenants_by_location,
                          tenants_expiring_30d=tenants_expiring_30d,
                          tenants_expiring_90d=tenants_expiring_90d,
                          tenants_by_tenure=tenants_by_tenure,
                          tenants=tenants)

# --- Show renew form and perform renewal ---
@app.route('/tenants/renew/<int:tenant_id>', methods=['GET', 'POST'])
@login_required
def tenant_renew(tenant_id):
    conn = get_db_connection()

    if request.method == 'POST':
        # Process renewal
        start_date = request.form.get('lease_start_date')
        end_date = request.form.get('lease_end_date')

        if not start_date or not end_date:
            flash('Please provide both start and end dates.', 'danger')
            return redirect(url_for('tenant_renew', tenant_id=tenant_id))

        # Update tenant lease info and mark tenant active
        conn.execute('''
            UPDATE tenants
            SET lease_start_date = ?, lease_end_date = ?, is_active = 1
            WHERE id = ?
        ''', (start_date, end_date, tenant_id))

        # Ensure property/unit are marked Occupied
        t = conn.execute('SELECT property_id, unit_id FROM tenants WHERE id = ?', (tenant_id,)).fetchone()
        if t:
            if t['unit_id']:
                conn.execute('UPDATE property_units SET status = "Occupied" WHERE id = ?', (t['unit_id'],))
            elif t['property_id']:
                conn.execute('UPDATE properties SET status = "Occupied" WHERE id = ?', (t['property_id'],))

        conn.commit()
        conn.close()
        flash('Lease renewed successfully.', 'success')
        return redirect(url_for('tenant_detail', tenant_id=tenant_id))

    # GET -> show form
    tenant = conn.execute('''
        SELECT t.*, p.title AS property_title, u.unit_name
        FROM tenants t
        LEFT JOIN properties p ON t.property_id = p.id
        LEFT JOIN property_units u ON t.unit_id = u.id
        WHERE t.id = ?
    ''', (tenant_id,)).fetchone()
    conn.close()

    if not tenant:
        flash('Tenant not found.', 'danger')
        return redirect(url_for('tenants_list'))

    return render_template('tenants/renew_tenant.html', tenant=tenant)

# --- End lease / Vacate tenant (GET used for convenience) ---
@app.route('/tenants/end/<int:tenant_id>')
@login_required
def tenant_end(tenant_id):
    conn = get_db_connection()
    tenant = conn.execute('SELECT property_id, unit_id FROM tenants WHERE id = ?', (tenant_id,)).fetchone()

    if not tenant:
        conn.close()
        flash('Tenant not found.', 'danger')
        return redirect(url_for('properties/renew'))

    # Mark property/unit as vacant and unlink tenant
    if tenant['unit_id']:
        conn.execute('UPDATE property_units SET status = "Vacant" WHERE id = ?', (tenant['unit_id'],))
    elif tenant['property_id']:
        conn.execute('UPDATE properties SET status = "Vacant" WHERE id = ?', (tenant['property_id'],))

    # Option A: keep tenant record but mark not active and clear links
    conn.execute('UPDATE tenants SET is_active = 0, property_id = NULL, unit_id = NULL WHERE id = ?', (tenant_id,))

    conn.commit()
    conn.close()
    flash('Lease ended and property/unit marked as vacant.', 'info')
    return redirect(url_for('renew_rent'))


# --- Renew / Expiry listing (properties/renew) ---
from datetime import date, timedelta  # add near other imports if not already imported

@app.route('/properties/renew', methods=['GET', 'POST'])
@login_required
def renew_rent():
    """Display list of tenants and handle rent renewal with payment"""
    conn = get_db_connection()
    
    if request.method == 'POST':
        # Get form data from modal
        tenant_id = request.form.get('tenant_id')
        new_start_date = request.form.get('new_start_date')
        new_end_date = request.form.get('new_end_date')
        amount = request.form.get('amount')
        payment_method = request.form.get('payment_method')
        payment_type = request.form.get('payment_type', 'Full')
        payment_date = request.form.get('payment_date', datetime.datetime.now().strftime('%Y-%m-%d'))
        description = request.form.get('description', '')
        
        # Validate inputs
        if not all([tenant_id, new_start_date, new_end_date, amount, payment_method]):
            flash('All required fields must be filled.', 'danger')
            conn.close()
            return redirect(url_for('renew_rent'))
        
        try:
            amount = float(amount)
        except ValueError:
            flash('Invalid amount entered.', 'danger')
            conn.close()
            return redirect(url_for('renew_rent'))
        
        # Begin transaction
        conn.execute("BEGIN TRANSACTION")
        
        try:
            # Get tenant and property details
            tenant = conn.execute('''
                SELECT t.*, p.id as property_id, p.landlord_id, p.price as property_price,
                       u.id as unit_id, u.price as unit_price,
                       l.full_name as landlord_name
                FROM tenants t
                JOIN properties p ON t.property_id = p.id
                JOIN landlords l ON p.landlord_id = l.id
                LEFT JOIN property_units u ON t.unit_id = u.id
                WHERE t.id = ?
            ''', (tenant_id,)).fetchone()
            
            if not tenant:
                conn.rollback()
                flash('Tenant not found.', 'danger')
                conn.close()
                return redirect(url_for('renew_rent'))
            
            property_id = tenant['property_id']
            landlord_id = tenant['landlord_id']
            unit_id = tenant['unit_id']
            rent_amount = float(tenant['unit_price'] if unit_id else tenant['property_price'])
            
            # Check if tenant has made COMPLETED payments before (to determine if renewal fee applies)
            prev_completed_payments = conn.execute('''
                SELECT COUNT(*) AS cnt 
                FROM payments 
                WHERE tenant_id = ? AND payment_type = 'Full' AND balance_due = 0
            ''', (tenant_id,)).fetchone()
            prev_payments = int(prev_completed_payments['cnt'] or 0)
            
            # Determine if 10% fee should apply (only on renewals - when tenant has paid before)
            is_renewal = (prev_payments >= 1)
            
            # Calculate balance due for partial payments
            balance_due = 0
            if payment_type == 'Partial':
                balance_due = rent_amount - amount
            
            # 1. Update tenant lease dates
            conn.execute('''
                UPDATE tenants
                SET lease_start_date = ?, lease_end_date = ?
                WHERE id = ?
            ''', (new_start_date, new_end_date, tenant_id))
            
            # 2. Insert payment record (store the original amount tenant paid)
            cursor = conn.execute('''
                INSERT INTO payments (
                    tenant_id, property_id, unit_id, amount, payment_type, payment_method,
                    payment_date, balance_due, description, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                tenant_id, property_id, unit_id, amount, payment_type, payment_method,
                payment_date, balance_due, 
                description or f'Lease renewal payment ({new_start_date} to {new_end_date})', 
                'Paid'
            ))
            
            payment_id = cursor.lastrowid
            
            # 3. ✅ Record landlord transactions
            if is_renewal:
                # ✅ RENEWAL: Record 2 transactions
                
                # ✅ Transaction 1: CREDIT (FULL amount tenant paid - EXACTLY as entered)
                conn.execute('''
                    INSERT INTO landlord_transactions (
                        landlord_id, date, narration, transaction_type, amount, payment_method
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    landlord_id, 
                    payment_date,
                    description or f'Rent renewal - {tenant["full_name"]}',
                    'credit',
                    amount,  # ✅ FULL amount entered by user
                    payment_method
                ))
                
                # Calculate 10% deduction
                deduction_amount = amount * 0.10
                
                # ✅ Transaction 2: DEBIT (10% management fee deduction)
                conn.execute('''
                    INSERT INTO landlord_transactions (
                        landlord_id, date, narration, transaction_type, amount, payment_method
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    landlord_id, 
                    payment_date,
                    f'Management fee deduction (10% of ₦{amount:,.2f})',
                    'debit',
                    deduction_amount,
                    'Automatic Deduction'
                ))
                
                # Calculate net amount landlord receives
                landlord_net_amount = amount - deduction_amount
                
                # Prepare success message
                if payment_type == 'Partial':
                    flash(f'✅ Partial renewal payment of ₦{amount:,.2f} recorded! Net amount to landlord: ₦{landlord_net_amount:,.2f} (10% fee: ₦{deduction_amount:,.2f} deducted). Remaining balance: ₦{balance_due:,.2f}', 'success')
                else:
                    flash(f'✅ Lease renewed successfully! Payment of ₦{amount:,.2f} recorded. Net amount to landlord: ₦{landlord_net_amount:,.2f} (10% renewal fee: ₦{deduction_amount:,.2f} deducted).', 'success')
                
            else:
                # ✅ FIRST PAYMENT: Record only 1 transaction (100% credit, no deduction)
                conn.execute('''
                    INSERT INTO landlord_transactions (
                        landlord_id, date, narration, transaction_type, amount, payment_method
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    landlord_id, 
                    payment_date,
                    description or f'Rent payment - {tenant["full_name"]} (First payment)',
                    'credit',
                    amount,  # ✅ FULL amount entered by user
                    payment_method
                ))
                
                # Prepare success message
                if payment_type == 'Partial':
                    flash(f'✅ Partial payment of ₦{amount:,.2f} recorded! Full amount credited to landlord (First payment - no fee). Remaining balance: ₦{balance_due:,.2f}. Next renewal will have 10% fee.', 'success')
                else:
                    flash(f'✅ Lease renewed successfully! Payment of ₦{amount:,.2f} recorded. Full amount credited to landlord (First payment - no fee). Next renewal will have 10% fee.', 'success')
            
            # Commit all changes
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            flash(f'❌ Error processing renewal: {str(e)}', 'danger')
        
        conn.close()
        return redirect(url_for('renew_rent'))
    
    # GET request - Display tenants list
    try:
        tenants = conn.execute('''
            SELECT t.id as tenant_id, t.full_name, t.lease_start_date, t.lease_end_date,
                   p.id as property_id, p.title as property_title, 
                   u.id as unit_id, u.unit_name,
                   l.id as landlord_id, l.full_name as landlord_name,
                   CASE 
                       WHEN t.unit_id IS NOT NULL THEN u.price 
                       ELSE p.price 
                   END as rent_amount,
                   CASE
                       WHEN date(t.lease_end_date) < date('now') THEN 'Expired'
                       WHEN date(t.lease_end_date) <= date('now', '+30 day') THEN 'Expiring Soon'
                       ELSE 'Active'
                   END as lease_status,
                   (julianday(t.lease_end_date) - julianday('now')) as days_remaining
            FROM tenants t
            JOIN properties p ON t.property_id = p.id
            JOIN landlords l ON p.landlord_id = l.id
            LEFT JOIN property_units u ON t.unit_id = u.id
            WHERE t.property_id IS NOT NULL
            ORDER BY t.lease_end_date ASC
        ''').fetchall()
    except Exception as e:
        flash(f'Error loading tenants: {str(e)}', 'danger')
        tenants = []
    
    conn.close()
    return render_template('properties/renew_rent.html', tenants=tenants)


@app.route('/api/tenant-payment-history/<int:tenant_id>')
@login_required
def api_tenant_payment_history(tenant_id):
    conn = get_db_connection()
    
    history = conn.execute('''
        SELECT COUNT(*) as count
        FROM payments
        WHERE tenant_id = ? AND payment_type = 'Full' AND balance_due = 0
    ''', (tenant_id,)).fetchone()
    
    conn.close()
    
    return jsonify({'has_full_payment': history['count'] > 0})

@app.route('/tenants/end_lease/<int:tenant_id>', methods=['POST'])
@login_required
def end_lease(tenant_id):
    """End/terminate a tenant's lease and vacate property"""
    conn = get_db_connection()
    
    try:
        conn.execute("BEGIN TRANSACTION")
        
        # Fetch tenant details
        tenant = conn.execute('''
            SELECT property_id, unit_id 
            FROM tenants 
            WHERE id = ?
        ''', (tenant_id,)).fetchone()
        
        if not tenant:
            conn.rollback()
            conn.close()
            return jsonify({'success': False, 'message': 'Tenant not found'}), 404
        
        # Free up property or unit
        if tenant['unit_id']:
            conn.execute('''
                UPDATE property_units 
                SET status = "Vacant", tenant_id = NULL 
                WHERE id = ?
            ''', (tenant['unit_id'],))
        
        if tenant['property_id']:
            # Check if this was the only tenant or if it's a standalone property
            other_tenants = conn.execute('''
                SELECT COUNT(*) as count 
                FROM tenants 
                WHERE property_id = ? AND id != ? AND unit_id IS NOT NULL
            ''', (tenant['property_id'], tenant_id)).fetchone()
            
            # Only mark property vacant if no other tenants or if standalone
            if not tenant['unit_id'] or other_tenants['count'] == 0:
                conn.execute('''
                    UPDATE properties 
                    SET status = "Vacant" 
                    WHERE id = ?
                ''', (tenant['property_id'],))
        
        # Clear tenant's property assignment (keep tenant record for history)
        conn.execute('''
            UPDATE tenants
            SET property_id = NULL, unit_id = NULL
            WHERE id = ?
        ''', (tenant_id,))
        
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Lease ended successfully'})
    
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    
@app.route('/landlords/<int:landlord_id>/add-statement', methods=['GET', 'POST'])
@login_required
def add_landlord_transaction(landlord_id):
    """
    Add a manual credit or debit transaction to landlord_transactions table.
    """
    conn = get_db_connection()
    landlord = conn.execute('SELECT * FROM landlords WHERE id = ?', (landlord_id,)).fetchone()
    if not landlord:
        conn.close()
        flash('Landlord not found.', 'danger')
        return redirect(url_for('landlord_account_statement'))

    if request.method == 'POST':
        # Validate input
        date = request.form.get('date') or None
        txn_type = request.form.get('type')  # 'credit' or 'debit'
        narration = request.form.get('narration', '').strip()
        mode_of_payment = request.form.get('mode_of_payment', '').strip()
        amount_raw = request.form.get('amount', '0').strip()

        try:
            amount = float(amount_raw)
        except ValueError:
            conn.close()
            flash('Enter a valid amount.', 'danger')
            return redirect(url_for('add_landlord_transaction', landlord_id=landlord_id))

        if txn_type not in ('credit', 'debit'):
            conn.close()
            flash('Select transaction type (credit or debit).', 'danger')
            return redirect(url_for('add_landlord_transaction', landlord_id=landlord_id))

        if not date:
            # default to today
            from datetime import date as dt_date
            date = dt_date.today().isoformat()

        # insert into landlord_transactions
        conn.execute('''
            INSERT INTO landlord_transactions (landlord_id, date, narration, transaction_type, amount, payment_method)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (landlord_id, date, narration, txn_type, amount, mode_of_payment))
        conn.commit()
        conn.close()

        flash('Transaction saved.', 'success')
        return redirect(url_for('landlord_account_detail', landlord_id=landlord_id))

    conn.close()
    return render_template('landlords/add_landlord_transaction.html', landlord=landlord)
# -------------------------------
# LANDLORD ACCOUNT STATEMENT FIXED
# -------------------------------
@app.route('/landlords/account-statement')
@login_required
def landlord_account_statement():
    conn = get_db_connection()
    landlords = conn.execute('''
        SELECT l.*, 
               (SELECT COUNT(*) FROM properties p WHERE p.landlord_id = l.id) as total_properties
        FROM landlords l
        ORDER BY l.full_name COLLATE NOCASE
    ''').fetchall()
    conn.close()
    return render_template('landlords/landlord_account_statement.html', landlords=landlords)


@app.route('/landlords/<int:landlord_id>/add-statement', methods=['GET', 'POST'])
@login_required
def add_landlord_account(landlord_id):
    conn = get_db_connection()

    landlord = conn.execute('SELECT * FROM landlords WHERE id = ?', (landlord_id,)).fetchone()
    if not landlord:
        flash('Landlord not found.', 'danger')
        conn.close()
        return redirect(url_for('landlord_account_statement'))

    if request.method == 'POST':
        date = request.form['date']
        transaction_type = request.form['type']
        narration = request.form['narration']
        mode_of_payment = request.form['mode_of_payment']
        amount = float(request.form['amount'])

        credit = amount if transaction_type == 'credit' else 0
        debit = amount if transaction_type == 'debit' else 0

        # ✅ Try to link to existing tenant/property for this landlord
        tenant_row = conn.execute('''
            SELECT t.id, t.property_id, t.unit_id
            FROM tenants t
            JOIN properties p ON t.property_id = p.id
            WHERE p.landlord_id = ?
            LIMIT 1
        ''', (landlord_id,)).fetchone()

        if tenant_row:
            tenant_id = tenant_row['id']
            property_id = tenant_row['property_id']
            unit_id = tenant_row['unit_id']
        else:
            # Fallback to system tenant and property if landlord has none
            sys_tenant = conn.execute('SELECT id FROM tenants WHERE full_name = ?', ('System Tenant',)).fetchone()
            if not sys_tenant:
                conn.execute('''
                    INSERT INTO tenants (full_name, phone, email, address)
                    VALUES (?, ?, ?, ?)
                ''', ('System Tenant', '0000000000', 'system@internal.com', 'System Generated'))
                conn.commit()
                sys_tenant = conn.execute('SELECT id FROM tenants WHERE full_name = ?', ('System Tenant',)).fetchone()

            tenant_id = sys_tenant['id']

            sys_property = conn.execute('SELECT id FROM properties WHERE landlord_id = ? AND title = ?', (landlord_id, 'System Property')).fetchone()
            if not sys_property:
                conn.execute('''
                    INSERT INTO properties (landlord_id, title, location, type, rent_amount, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (landlord_id, 'System Property', 'Auto-created', 'System', 0, 'Occupied'))
                conn.commit()
                sys_property = conn.execute('SELECT id FROM properties WHERE landlord_id = ? AND title = ?', (landlord_id, 'System Property')).fetchone()

            property_id = sys_property['id']
            unit_id = None

        # ✅ Insert transaction with proper linkage
        conn.execute('''
            INSERT INTO payments (
                tenant_id, property_id, unit_id,
                amount, payment_method, description,
                payment_date, debit, credit, payment_type
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            tenant_id,
            property_id,
            unit_id,
            amount,
            mode_of_payment,
            narration,
            date,
            debit,
            credit,
            'Full'
        ))

        conn.commit()
        conn.close()

        flash(f'{transaction_type.capitalize()} transaction recorded successfully for {landlord["full_name"]}.', 'success')
        return redirect(url_for('landlord_account_detail', landlord_id=landlord_id))

    conn.close()
    return render_template('landlords/add_landlord_account.html', landlord=landlord)


@app.route('/landlords/<int:landlord_id>/account-statement')
@login_required
def landlord_account_detail(landlord_id):
    conn = get_db_connection()
    landlord = conn.execute('SELECT * FROM landlords WHERE id = ?', (landlord_id,)).fetchone()
    if not landlord:
        flash('Landlord not found.', 'danger')
        conn.close()
        return redirect(url_for('landlord_account_statement'))

    # 1) Payments made by tenants for properties belonging to this landlord
    payments = conn.execute('''
        SELECT 
            p.id as payment_id,
            p.payment_date as date,
            p.description as narration,
            p.payment_method as mode_of_payment,
            p.amount as amount,
            t.full_name as tenant_name,
            'payment' as source
        FROM payments p
        LEFT JOIN tenants t ON p.tenant_id = t.id
        LEFT JOIN properties prop ON p.property_id = prop.id
        WHERE prop.landlord_id = ?
    ''', (landlord_id,)).fetchall()

    # 2) Manual landlord transactions from new table
    manual = conn.execute('''
        SELECT 
            lt.id as txn_id,
            lt.date as date,
            lt.narration as narration,
            lt.payment_method as mode_of_payment,
            lt.amount as amount,
            lt.transaction_type as txn_type,
            'manual' as source
        FROM landlord_transactions lt
        WHERE lt.landlord_id = ?
    ''', (landlord_id,)).fetchall()

    conn.close()

    # Normalize into common list of dicts with credit/debit fields and a date type
    merged = []
    for p in payments:
        merged.append({
            'date': p['date'],
            'narration': p['narration'] or f"Payment from {p['tenant_name'] or 'Unknown tenant'}",
            'mode_of_payment': p['mode_of_payment'] or '',
            'credit': float(p['amount'] or 0),
            'debit': 0.0,
            'source': 'payment',
            'meta_id': p['payment_id']
        })

    for m in manual:
        if (m['txn_type'] or '').lower() == 'credit':
            credit = float(m['amount'] or 0)
            debit = 0.0
        else:
            credit = 0.0
            debit = float(m['amount'] or 0)
        merged.append({
            'date': m['date'],
            'narration': m['narration'] or '',
            'mode_of_payment': m['mode_of_payment'] or '',
            'credit': credit,
            'debit': debit,
            'source': 'manual',
            'meta_id': m['txn_id']
        })

    # Sort by date ascending (older first). If dates are strings in YYYY-MM-DD it's fine.
    merged.sort(key=lambda x: x['date'] or '')

    # Compute running balance
    balance = 0.0
    detailed = []
    for i, tx in enumerate(merged, start=1):
        balance += (tx['credit'] or 0) - (tx['debit'] or 0)
        detailed.append({
            'sn': i,
            'date': tx['date'],
            'narration': tx['narration'],
            'mode_of_payment': tx.get('mode_of_payment', ''),
            'credit': tx['credit'],
            'debit': tx['debit'],
            'balance': balance,
            'source': tx['source'],
            'meta_id': tx['meta_id']
        })

    return render_template(
        'landlords/landlord_account_detail.html',
        landlord=landlord,
        transactions=detailed,
        balance=balance
    )

# Landlord Account Statement - Detail view with filters + running balance
@app.route('/landlords/<int:landlord_id>/account-statement', methods=['GET'])
@login_required
def landlord_account_view(landlord_id):
    conn = get_db_connection()

    landlord = conn.execute('SELECT * FROM landlords WHERE id = ?', (landlord_id,)).fetchone()
    if not landlord:
        flash('Landlord not found.', 'danger')
        return redirect(url_for('landlord_account_index'))

    # filters
    search_q = request.args.get('q', '').strip()
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()

    # Build base SQL and params
    base_sql = '''
        SELECT
            p.id as payment_id,
            p.payment_date as date,
            p.description as narration,
            p.payment_method as payment_method,
            p.amount as amount,
            t.full_name as tenant_name,
            prop.title as property_title
        FROM payments p
        LEFT JOIN tenants t ON p.tenant_id = t.id
        LEFT JOIN properties prop ON p.property_id = prop.id
        WHERE prop.landlord_id = ?
    '''
    params = [landlord_id]

    # Add date filters if provided
    if start_date:
        base_sql += ' AND date(p.payment_date) >= date(?)'
        params.append(start_date)
    if end_date:
        base_sql += ' AND date(p.payment_date) <= date(?)'
        params.append(end_date)

    # Add search filter (search tenant name or narration or property title)
    if search_q:
        base_sql += " AND (LOWER(t.full_name) LIKE ? OR LOWER(p.description) LIKE ? OR LOWER(prop.title) LIKE ?)"
        like = '%' + search_q.lower() + '%'
        params.extend([like, like, like])

    base_sql += ' ORDER BY date(p.payment_date) ASC, p.created_at ASC'

    rows = conn.execute(base_sql, tuple(params)).fetchall()

    # compute running balance. Here payments are credits to landlord; debit support reserved (none in table)
    running_balance = 0
    transactions = []
    for i, r in enumerate(rows, start=1):
        credit = r['amount'] if r['amount'] is not None else 0
        debit = 0.0  # if you later add outgoing transaction table, populate debit accordingly
        running_balance += credit - debit

        transactions.append({
            'sn': i,
            'date': r['date'],
            'property': r['property_title'],
            'tenant': r['tenant_name'],
            'narration': r['narration'] if r['narration'] else f'Payment by {r["tenant_name"] or ""}',
            'payment_method': r['payment_method'],
            'credit': credit,
            'debit': debit,
            'balance': running_balance
        })

    conn.close()
    return render_template('landlords/landlord_account_view.html',
                           landlord=landlord,
                           transactions=transactions,
                           q=search_q,
                           start_date=start_date,
                           end_date=end_date)



# Settings route
@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_reminders':
            rent_reminder_days = request.form.get('rent_reminder_days')
            partial_payment_reminder_days = request.form.get('partial_payment_reminder_days')
            
            conn = get_db_connection()
            
            try:
                conn.execute(
                    'UPDATE settings SET setting_value = ?, updated_at = CURRENT_TIMESTAMP WHERE setting_name = ?',
                    (rent_reminder_days, 'rent_reminder_days')
                )
                conn.execute(
                    'UPDATE settings SET setting_value = ?, updated_at = CURRENT_TIMESTAMP WHERE setting_name = ?',
                    (partial_payment_reminder_days, 'partial_payment_reminder_days')
                )
                
                conn.commit()
                flash('Reminder settings updated successfully')
                
            except Exception as e:
                flash(f'Error: {str(e)}')
            
            conn.close()
            
        elif action == 'change_password':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if new_password != confirm_password:
                flash('New passwords do not match')
                return redirect(url_for('settings'))
            
            conn = get_db_connection()
            
            user = conn.execute(
                'SELECT * FROM users WHERE id = ?',
                (session['user_id'],)
            ).fetchone()
            
            if not check_password_hash(user['password_hash'], current_password):
                flash('Current password is incorrect')
                conn.close()
                return redirect(url_for('settings'))
            
            try:
                password_hash = generate_password_hash(new_password)
                conn.execute(
                    'UPDATE users SET password_hash = ? WHERE id = ?',
                    (password_hash, session['user_id'])
                )
                
                conn.commit()
                flash('Password changed successfully')
                
            except Exception as e:
                flash(f'Error: {str(e)}')
            
            conn.close()
        
        return redirect(url_for('settings'))
    
    conn = get_db_connection()
    
    reminder_settings = {}
    
    settings = conn.execute('SELECT * FROM settings').fetchall()
    for setting in settings:
        reminder_settings[setting['setting_name']] = setting['setting_value']
    
    conn.close()
    
    return render_template('settings.html', reminder_settings=reminder_settings)

# API routes for AJAX requests
@app.route('/api/property-units/<int:property_id>')
def api_property_units(property_id):
    conn = get_db_connection()
    
    units = conn.execute('''
        SELECT id, unit_name, size, price, status
        FROM property_units
        WHERE property_id = ?
    ''', (property_id,)).fetchall()
    
    conn.close()
    
    return jsonify([dict(u) for u in units])

@app.route('/api/rent-property', methods=['POST'])
@login_required
def api_rent_property():
    property_id = request.form.get('property_id')
    unit_id = request.form.get('unit_id')
    
    # Redirect to add tenant form with property/unit pre-selected
    if unit_id:
        return redirect(url_for('add_tenant', property_id=property_id, unit_id=unit_id))
    else:
        return redirect(url_for('add_tenant', property_id=property_id))

@app.route('/api/tenant-details/<int:tenant_id>')
def api_tenant_details(tenant_id):
    conn = get_db_connection()
    
    tenant = conn.execute('''
        SELECT t.*, p.title as property_title, u.unit_name, p.type as property_type,
               CASE WHEN t.unit_id IS NOT NULL THEN u.price ELSE p.price END as rent_amount
        FROM tenants t
        JOIN properties p ON t.property_id = p.id
        LEFT JOIN property_units u ON t.unit_id = u.id
        WHERE t.id = ?
    ''', (tenant_id,)).fetchone()
    
    conn.close()
    
    if tenant:
        return jsonify(dict(tenant))
    else:
        return jsonify({'error': 'Tenant not found'}), 404

@app.route('/api/property-details/<int:property_id>')
def api_property_details(property_id):
    conn = get_db_connection()
    
    property = conn.execute('''
        SELECT p.*, l.full_name as landlord_name
        FROM properties p
        JOIN landlords l ON p.landlord_id = l.id
        WHERE p.id = ?
    ''', (property_id,)).fetchone()
    
    conn.close()
    
    if property:
        return jsonify(dict(property))
    else:
        return jsonify({'error': 'Property not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)