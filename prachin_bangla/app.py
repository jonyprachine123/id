from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import re

app = Flask(__name__)

# Configure SQLite database
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'prachin_bangla.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Configure session
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    features = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Integer, default=0)
    image = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    customer_email = db.Column(db.String(120))
    customer_address = db.Column(db.Text, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    product = db.relationship('Product')

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class Banner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    image = db.Column(db.String(255), nullable=False)
    link = db.Column(db.String(255))
    price = db.Column(db.Float, default=0)
    discount = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    products = Product.query.all()
    reviews = Review.query.order_by(Review.date.desc()).limit(3).all()
    current_year = datetime.now().year
    return render_template('index.html', products=products, reviews=reviews, current_year=current_year)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        print(f"Login attempt - Username: {username}")  # Debug log
        
        user = User.query.filter_by(username=username).first()
        
        if user:
            print(f"User found - ID: {user.id}")  # Debug log
            if check_password_hash(user.password, password):
                login_user(user)
                flash('Successfully logged in!', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                print("Password check failed")  # Debug log
        else:
            print("User not found")  # Debug log
            
        flash('Invalid username or password!', 'error')
    
    return render_template('admin_login.html')

@app.route('/create-admin')
def create_admin():
    # Check if admin already exists
    admin = User.query.filter_by(username='admin').first()
    if admin:
        print(f"Admin exists - ID: {admin.id}, Password hash: {admin.password}")  # Debug log
        flash('Admin already exists!', 'info')
        return redirect(url_for('admin_login'))
    
    # Create admin user
    hashed_password = generate_password_hash('admin123')
    print(f"Creating admin - Password hash: {hashed_password}")  # Debug log
    
    admin = User(username='admin', password=hashed_password)
    db.session.add(admin)
    db.session.commit()
    
    print(f"Admin created - ID: {admin.id}")  # Debug log
    flash('Admin account created! Username: admin, Password: admin123', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    products = Product.query.all()
    orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    return render_template('admin_dashboard.html', products=products, orders=orders)

@app.route('/admin/products')
@login_required
def admin_products():
    products = Product.query.all()
    return render_template('admin_products.html', products=products)

@app.route('/admin/orders')
@login_required
def admin_orders():
    # Get all orders sorted by date (newest first)
    orders = Order.query.order_by(Order.created_at.desc()).all()
    print(f"Found {len(orders)} orders")  # Debug log
    return render_template('admin_orders.html', orders=orders)

@app.route('/admin/orders/<int:order_id>/status', methods=['POST'])
@login_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    status = request.form.get('status')
    if status in ['pending', 'completed', 'cancelled']:
        order.status = status
        db.session.commit()
        flash('Order status updated!', 'success')
    return redirect(url_for('admin_orders'))

@app.route('/admin/orders/<int:order_id>/delete', methods=['POST'])
@login_required
def delete_order(order_id):
    order = Order.query.get_or_404(order_id)
    db.session.delete(order)
    db.session.commit()
    flash('Order deleted successfully!', 'success')
    return redirect(url_for('admin_orders'))

@app.route('/admin/banners')
@login_required
def admin_banners():
    banners = Banner.query.all()
    return render_template('admin_banners.html', banners=banners)

@app.route('/admin/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        features = request.form.get('features')
        price = float(request.form['price'])
        discount = int(request.form.get('discount', 0))
        
        image = request.files['image']
        if image:
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            filename = None
            
        product = Product(
            name=name,
            description=description,
            features=features,
            price=price,
            discount=discount,
            image=filename
        )
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('admin_products'))
    
    return render_template('admin_product_form.html')

@app.route('/admin/products/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    if request.method == 'POST':
        product.name = request.form['name']
        product.description = request.form['description']
        product.features = request.form.get('features')
        product.price = float(request.form['price'])
        product.discount = int(request.form.get('discount', 0))
        
        image = request.files.get('image')
        if image:
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            product.image = filename
            
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin_products'))
    
    return render_template('admin_product_form.html', product=product)

@app.route('/admin/product/delete/<int:id>', methods=['POST'])
@login_required
def delete_product(id):
    print(f"Attempting to delete product {id}")  # Debug log
    product = Product.query.get_or_404(id)
    print(f"Found product: {product.name}")  # Debug log
    
    if product.image:
        try:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], product.image)
            print(f"Deleting image: {image_path}")  # Debug log
            os.remove(image_path)
        except Exception as e:
            print(f"Error deleting image: {e}")  # Debug log
            pass
    
    try:
        db.session.delete(product)
        db.session.commit()
        print(f"Product deleted successfully")  # Debug log
        flash('Product deleted successfully!', 'success')
    except Exception as e:
        print(f"Error deleting product: {e}")  # Debug log
        db.session.rollback()
        flash('Error deleting product!', 'error')
    
    return redirect(url_for('admin_products'))

@app.route('/place_order/<int:product_id>', methods=['POST'])
def place_order(product_id):
    try:
        # Get form data
        customer_name = request.form['customer_name']
        phone = request.form['customer_phone']
        email = request.form.get('customer_email', '')
        address = request.form['customer_address']
        quantity = int(request.form['quantity'])
        
        # Validate form data
        if not customer_name or not phone or not address or quantity < 1:
            flash('সব তথ্য পূরণ করুন', 'error')
            return redirect(url_for('index'))
            
        if not re.match(r'^01[3-9][0-9]{8}$', phone):
            flash('সঠিক বাংলাদেশি ফোন নম্বর দিন', 'error')
            return redirect(url_for('index'))
            
        if len(address) < 10:
            flash('বিস্তারিত ঠিকানা দিন', 'error')
            return redirect(url_for('index'))
            
        if email and not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash('সঠিক ইমেইল ঠিকানা দিন', 'error')
            return redirect(url_for('index'))

        # Get product and calculate price
        product = Product.query.get_or_404(product_id)
        unit_price = product.price
        if product.discount:
            unit_price = unit_price * (1 - product.discount/100)
            
        total_price = unit_price * quantity

        # Create order
        order = Order(
            customer_name=customer_name,
            customer_phone=phone,
            customer_email=email,
            customer_address=address,
            payment_method='cash',
            total_amount=total_price,
            status='pending'
        )
        db.session.add(order)
        db.session.flush()

        # Add order item
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=quantity,
            price=unit_price
        )
        db.session.add(order_item)
        db.session.commit()

        flash('অর্ডার সফলভাবে প্লেস করা হয়েছে!', 'success')
        return redirect(url_for('order_success'))
        
    except Exception as e:
        db.session.rollback()
        print(f"Error placing order: {str(e)}")
        flash('অর্ডার প্লেস করতে সমস্যা হয়েছে। আবার চেষ্টা করুন।', 'error')
        return redirect(url_for('index'))

@app.route('/order/<int:product_id>', methods=['GET', 'POST'])
def order(product_id):
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        try:
            customer_name = request.form['customer_name']
            phone = request.form['customer_phone']
            email = request.form.get('customer_email', '')
            address = request.form['customer_address']
            payment_method = request.form['payment_method']

            # Calculate total amount with discount
            price = product.price
            if product.discount:
                price = price * (1 - product.discount/100)

            # Create order
            order = Order(
                customer_name=customer_name,
                customer_phone=phone,
                customer_email=email,
                customer_address=address,
                payment_method=payment_method,
                total_amount=price,
                status='pending',
                created_at=datetime.utcnow()
            )
            db.session.add(order)
            db.session.flush()  # Get order.id before committing

            # Add order item
            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=1,
                price=price
            )
            db.session.add(order_item)

            db.session.commit()
            flash('অর্ডার সফলভাবে প্লেস করা হয়েছে!', 'success')
            return redirect(url_for('order_success'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error placing order: {str(e)}")
            flash('অর্ডার প্লেস করতে সমস্যা হয়েছে। আবার চেষ্টা করুন।', 'error')
            return redirect(url_for('order', product_id=product_id))

    return render_template('order_form.html', product=product)

@app.route('/order/success')
def order_success():
    active_banners = Banner.query.filter_by(is_active=True).all()
    return render_template('order_success.html', banners=active_banners)

@app.route('/admin/orders/<int:id>/details')
@login_required
def get_order_details(id):
    order = Order.query.get_or_404(id)
    return jsonify({
        'id': order.id,
        'customer_name': order.customer_name,
        'customer_phone': order.customer_phone,
        'customer_email': order.customer_email,
        'customer_address': order.customer_address,
        'total_amount': order.total_amount,
        'status': order.status,
        'created_at': order.created_at.strftime('%Y-%m-%d')
    })

@app.route('/admin/reviews')
@login_required
def admin_reviews():
    reviews = Review.query.order_by(Review.date.desc()).all()
    return render_template('admin_reviews.html', reviews=reviews)

@app.route('/admin/review/add', methods=['POST'])
@login_required
def add_review():
    review = Review(
        customer_name=request.form.get('customer_name'),
        rating=int(request.form.get('rating')),
        comment=request.form.get('comment')
    )
    db.session.add(review)
    db.session.commit()
    flash('Review added successfully!')
    return redirect(url_for('admin_reviews'))

@app.route('/admin/review/delete/<int:id>', methods=['POST'])
@login_required
def delete_review(id):
    review = Review.query.get_or_404(id)
    db.session.delete(review)
    db.session.commit()
    flash('Review deleted successfully!')
    return redirect(url_for('admin_reviews'))

@app.route('/admin/banner/add', methods=['GET', 'POST'])
@login_required
def add_banner():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        link = request.form.get('link')
        price = float(request.form.get('price', 0))
        discount = int(request.form.get('discount', 0))
        image = request.files.get('image')
        
        if image:
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'banners', filename)
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            image.save(image_path)
            
            banner = Banner(
                title=title,
                description=description,
                image=filename,
                link=link,
                price=price,
                discount=discount
            )
            
            db.session.add(banner)
            db.session.commit()
            flash('ব্যানার সফলভাবে যোগ করা হয়েছে!', 'success')
            return redirect(url_for('admin_banners'))
    
    return render_template('add_banner.html')

@app.route('/admin/banner/delete/<int:id>', methods=['POST'])
@login_required
def delete_banner(id):
    banner = Banner.query.get_or_404(id)
    if banner.image:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'banners', banner.image)
        if os.path.exists(image_path):
            os.remove(image_path)
    
    db.session.delete(banner)
    db.session.commit()
    flash('Banner deleted successfully!', 'success')
    return redirect(url_for('admin_banners'))

@app.route('/admin/banner/toggle/<int:id>', methods=['POST'])
@login_required
def toggle_banner(id):
    banner = Banner.query.get_or_404(id)
    banner.is_active = not banner.is_active
    db.session.commit()
    flash('Banner status updated!', 'success')
    return redirect(url_for('admin_banners'))

@app.route('/admin/orders/<int:id>/view')
@login_required
def admin_view_order(id):
    order = Order.query.get_or_404(id)
    return render_template('admin_view_order.html', order=order)

@app.route('/admin/orders/<int:id>/delete')
@login_required
def admin_delete_order(id):
    order = Order.query.get_or_404(id)
    db.session.delete(order)
    db.session.commit()
    flash('অর্ডার মুছে ফেলা হয়েছে!', 'success')
    return redirect(url_for('admin_orders'))

@app.route('/admin/orders/<int:id>/update', methods=['POST'])
@login_required
def admin_update_order_status(id):
    order = Order.query.get_or_404(id)
    status = request.form.get('status')
    if status in ['pending', 'processing', 'completed', 'cancelled']:
        order.status = status
        db.session.commit()
        flash('অর্ডার স্ট্যাটাস আপডেট করা হয়েছে!', 'success')
    return redirect(url_for('admin_orders'))

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('admin_login'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/cart')
def cart():
    cart = session.get('cart', {})
    cart_items = []
    total = 0
    
    for product_id, item in cart.items():
        product = Product.query.get(int(product_id))
        if product:
            subtotal = float(item['price']) * item['quantity']
            cart_items.append({
                'product': product,
                'quantity': item['quantity'],
                'price': float(item['price']),
                'subtotal': subtotal
            })
            total += subtotal
    
    return render_template('cart.html', cart_items=cart_items, total=total)

# Add context processor for current time
@app.context_processor
def inject_current_time():
    return {'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

if __name__ == '__main__':
    with app.app_context():
        # Only create tables if they don't exist
        db.create_all()
    app.run(debug=True)
