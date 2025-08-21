from flask import Flask, redirect, url_for, request, flash, g
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from config import Config
from models import db, User, Phone, Sale, Product, CashRegister, bcrypt
from flask import render_template
from flask_admin.form import rules
from wtforms import Form, SelectField, IntegerField, DecimalField
from flask import jsonify
from markupsafe import Markup
import requests
import threading
from datetime import datetime, date
# import schedule  # Temporarily commented out - will be enabled after installation
import time

app = Flask(__name__)
app.config.from_object(Config)

# Callmebot configuration
CALLMEBOT_API_KEY = "5116528"
CALLMEBOT_PHONE = "212777514777"

def send_whatsapp_notification(sale_data):
    """Send WhatsApp notification for new sale using Callmebot"""
    try:
        message = f"""🛒 Nueva Venta Registrada!

📱 Producto: {sale_data['item_name']}
📦 Cantidad: {sale_data['quantity']}
💰 Precio: ${sale_data['selling_price']:.2f} c/u
💵 Total: ${sale_data['total']:.2f}
📅 Fecha: {sale_data['sale_date']}
👤 Vendido por: {sale_data['worker_email']}

ID de Venta: #{sale_data['sale_id']}"""

        import urllib.parse
        encoded_message = urllib.parse.quote(message)
        url = f"https://api.callmebot.com/whatsapp.php?phone={CALLMEBOT_PHONE}&text={encoded_message}&apikey={CALLMEBOT_API_KEY}"
        response = requests.get(url, timeout=10)
            
    except Exception as e:
        pass

def send_sale_notification(sale, worker_email):
    """Prepare sale data and send WhatsApp notification in background thread"""
    try:
        if sale.item_type == 'product':
            item = Product.query.get(sale.item_id)
            item_name = item.name if item else 'Producto Desconocido'
        elif sale.item_type == 'phone':
            item = Phone.query.get(sale.item_id)
            item_name = f"{item.brand} {item.model}" if item else 'Teléfono Desconocido'
        else:
            item_name = 'Artículo Desconocido'
        
        sale_data = {
            'sale_id': sale.id,
            'item_name': item_name,
            'quantity': sale.quantity,
            'selling_price': float(sale.selling_price),
            'total': float(sale.quantity * sale.selling_price),
            'sale_date': sale.sale_date.strftime('%d/%m/%Y %H:%M'),
            'worker_email': worker_email
        }
        
        thread = threading.Thread(target=send_whatsapp_notification, args=(sale_data,))
        thread.daemon = True
        thread.start()
        
    except Exception as e:
        pass

@app.route('/')
def index():
    return redirect(url_for('login'))

def send_cash_declaration_notification(cash_register):
    """Send WhatsApp notification to owner about cash declaration"""
    try:
        worker = User.query.get(cash_register.declared_by)
        message = f"""💰 Declaración de Caja

👤 Trabajador: {worker.name} ({worker.email})
💵 Caja Inicial: ${cash_register.opening_cash:.2f}
📅 Fecha: {cash_register.date.strftime('%d/%m/%Y')}
🕐 Hora: {cash_register.created_at.strftime('%H:%M')}

La caja ha sido abierta para el día de hoy."""

        import urllib.parse
        encoded_message = urllib.parse.quote(message)
        url = f"https://api.callmebot.com/whatsapp.php?phone={CALLMEBOT_PHONE}&text={encoded_message}&apikey={CALLMEBOT_API_KEY}"
        requests.get(url, timeout=10)
        
    except Exception as e:
        pass

def send_daily_report():
    """Send daily cash report to owner at 23:59 and close the register"""
    try:
        today = date.today()
        cash_register = CashRegister.query.filter_by(date=today, is_open=True).first()
        
        if not cash_register:
            return
        
        # Calculate daily sales
        today_sales = Sale.query.filter(db.func.date(Sale.sale_date) == today).all()
        total_sales_amount = sum(sale.quantity * sale.selling_price for sale in today_sales)
        
        # Calculate expected closing cash
        expected_closing = cash_register.opening_cash + total_sales_amount
        
        # Get sales breakdown
        sales_by_worker = {}
        for sale in today_sales:
            worker = User.query.get(sale.worker_id)
            worker_name = worker.name if worker else 'Unknown'
            if worker_name not in sales_by_worker:
                sales_by_worker[worker_name] = 0
            sales_by_worker[worker_name] += sale.quantity * sale.selling_price
        
        # Format worker sales
        worker_sales_text = ""
        for worker_name, amount in sales_by_worker.items():
            worker_sales_text += f"👤 {worker_name}: ${amount:.2f}\n"
        
        message = f"""📊 Reporte Diario - {today.strftime('%d/%m/%Y')}

💰 Caja Inicial: ${cash_register.opening_cash:.2f}
💵 Ventas Totales: ${total_sales_amount:.2f}
💳 Caja Esperada: ${expected_closing:.2f}
📦 Total de Ventas: {len(today_sales)} transacciones

👥 Ventas por Trabajador:
{worker_sales_text}

🕐 Reporte generado a las 23:59
🔒 Caja cerrada automáticamente"""

        import urllib.parse
        encoded_message = urllib.parse.quote(message)
        url = f"https://api.callmebot.com/whatsapp.php?phone={CALLMEBOT_PHONE}&text={encoded_message}&apikey={CALLMEBOT_API_KEY}"
        requests.get(url, timeout=10)
        
        # Close the cash register
        cash_register.is_open = False
        cash_register.closed_at = datetime.utcnow()
        cash_register.total_sales = total_sales_amount
        db.session.add(cash_register)
        db.session.commit()
        
    except Exception as e:
        pass

# Schedule daily report at 23:59
def schedule_daily_report():
    # schedule.every().day.at("23:59").do(send_daily_report)  # Temporarily commented out
    
    while True:
        # schedule.run_pending()  # Temporarily commented out
        time.sleep(60)

# Start the scheduler in a background thread
# report_thread = threading.Thread(target=schedule_daily_report, daemon=True)  # Temporarily commented out
# report_thread.start()  # Temporarily commented out

bcrypt.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
db.init_app(app)

# ===== LOGIN MANAGER =====
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Store current user in Flask's g object for reliable access
@app.before_request
def load_current_user():
    g.current_user = current_user

# ===== FLASK-ADMIN =====

class SaleForm(Form):
    item_type = SelectField('Item Type', choices=[('product','Product'), ('phone','Phone')])
    item_id = SelectField('Item ID', choices=[])
    quantity = IntegerField('Quantity')
    selling_price = DecimalField('Selling Price')
    
    def validate_item_id(self, field):
        pass
    
    def validate(self):
        if not self.item_type.data:
            self.item_type.errors.append('Item type is required')
            return False
        
        item_id_from_form = self.item_id.data
        item_id_from_request = request.form.get('item_id') if request else None
        
        if not item_id_from_form and item_id_from_request:
            self.item_id.data = item_id_from_request
            item_id_from_form = item_id_from_request
        
        if not item_id_from_form or item_id_from_form == '':
            self.item_id.errors.append('Please select an item')
            return False
        
        if not self.quantity.data or self.quantity.data <= 0:
            self.quantity.errors.append('Quantity must be greater than 0')
            return False
        
        if not self.selling_price.data or self.selling_price.data <= 0:
            self.selling_price.errors.append('Selling price must be greater than 0')
            return False
        
        return True
    
    def __init__(self, *args, **kwargs):
        super(SaleForm, self).__init__(*args, **kwargs)
        self.item_type.description = '''
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            var itemTypeSelect = document.querySelector('select[name="item_type"]');
            var itemIdSelect = document.querySelector('select[name="item_id"]');
            
            if (itemTypeSelect) {
                itemTypeSelect.addEventListener('change', function() {
                    updateItemChoices(this.value);
                });
            }
            
            function updateItemChoices(selectedType) {
                if (!itemIdSelect) return;
                
                itemIdSelect.innerHTML = '<option value="">Loading...</option>';
                itemIdSelect.disabled = true;
                
                fetch('/admin/_get_items?type=' + encodeURIComponent(selectedType))
                    .then(function(response) {
                        return response.json();
                    })
                    .then(function(data) {
                        itemIdSelect.innerHTML = '<option value="">Select item...</option>';
                        
                        if (data && data.length > 0) {
                            data.forEach(function(item) {
                                var option = document.createElement('option');
                                option.value = item.id;
                                option.textContent = item.label;
                                itemIdSelect.appendChild(option);
                            });
                        }
                        
                        itemIdSelect.disabled = false;
                        
                        var event = new Event('change', { bubbles: true });
                        itemIdSelect.dispatchEvent(event);
                        
                        var inputEvent = new Event('input', { bubbles: true });
                        itemIdSelect.dispatchEvent(inputEvent);
                    })
                    .catch(function(error) {
                        itemIdSelect.innerHTML = '<option value="">Error loading items</option>';
                        itemIdSelect.disabled = false;
                    });
            }
            
            if (itemIdSelect) {
                itemIdSelect.addEventListener('change', function() {
                    this.setAttribute('data-value', this.value);
                    
                    var hiddenField = document.querySelector('input[name="item_id"][type="hidden"]');
                    if (hiddenField) {
                        hiddenField.value = this.value;
                    }
                    
                    if (this.value) {
                        this.selectedIndex = Array.from(this.options).findIndex(option => option.value === this.value);
                    }
                    
                    var changeEvent = new Event('change', { bubbles: true });
                    this.dispatchEvent(changeEvent);
                    
                    var inputEvent = new Event('input', { bubbles: true });
                    this.dispatchEvent(inputEvent);
                    
                    var blurEvent = new Event('blur', { bubbles: true });
                    this.dispatchEvent(blurEvent);
                });
            }
        });
        </script>
        '''

class SaleModelView(ModelView):
    form = SaleForm
    
    # Method 1: Override create_model to set worker_id before saving
    def create_model(self, form):
        try:
            # Get the current user before processing the model
            user = self._get_current_user()
            
            # Create the model from form data
            model = self.model()
            form.populate_obj(model)
            model.product_id = 0

            # Set the worker_id to current user's ID
            if user and user.is_authenticated:
                model.worker_id = user.id
            else:
                # This should not happen if authentication is working properly
                raise ValueError("No authenticated user found")
            
            # Validate the item exists and check stock
            item = None
            if model.item_type == 'product':
                item = Product.query.get(model.item_id)
                if not item:
                    raise ValueError("Selected product does not exist")
            elif model.item_type == 'phone':
                item = Phone.query.get(model.item_id)
                if not item:
                    raise ValueError("Selected phone does not exist")
            
            # Check if there's enough stock
            if item.stock < model.quantity:
                raise ValueError(f"Insufficient stock. Available: {item.stock}, Requested: {model.quantity}")
            
            # Reduce the stock count
            item.stock -= model.quantity
            
            # Save both the sale and the updated item
            self.session.add(model)
            self.session.add(item)  # Make sure the item stock update is saved
            self._on_model_change(form, model, True)
            self.session.commit()
            
            # Send WhatsApp notification in background thread
            send_sale_notification(model, user.email)
            
            return model
        except Exception as e:
            if not self.handle_view_exception(e):
                flash(f'Failed to create record: {str(e)}', 'error')
            self.session.rollback()
            return False
    
    # Method 1a: Override update_model to handle stock adjustments when editing sales
    def update_model(self, form, model):
        try:
            # Get the original quantity before update
            original_quantity = model.quantity
            original_item_id = model.item_id
            original_item_type = model.item_type
            
            # Get the new values from the form
            new_quantity = form.quantity.data
            new_item_id = int(form.item_id.data)
            new_item_type = form.item_type.data
            
            # Handle stock adjustments
            if (original_item_id != new_item_id or 
                original_item_type != new_item_type or 
                original_quantity != new_quantity):
                
                # Restore stock for the original item
                if original_item_type == 'product':
                    original_item = Product.query.get(original_item_id)
                elif original_item_type == 'phone':
                    original_item = Phone.query.get(original_item_id)
                
                if original_item:
                    original_item.stock += original_quantity
                    self.session.add(original_item)
                
                # Reduce stock for the new item
                if new_item_type == 'product':
                    new_item = Product.query.get(new_item_id)
                elif new_item_type == 'phone':
                    new_item = Phone.query.get(new_item_id)
                
                if not new_item:
                    raise ValueError("Selected item does not exist")
                
                # Check if there's enough stock for the new quantity
                if new_item.stock < new_quantity:
                    raise ValueError(f"Insufficient stock for {new_item.name}. Available: {new_item.stock}, Requested: {new_quantity}")
                
                new_item.stock -= new_quantity
                self.session.add(new_item)
            
            # Update the sale model with new values
            form.populate_obj(model)
            
            self.session.add(model)
            self._on_model_change(form, model, False)
            self.session.commit()
            
            return True
            
        except Exception as e:
            if not self.handle_view_exception(e):
                flash(f'Failed to update record: {str(e)}', 'error')
            self.session.rollback()
            return False
    
    # Method 1b: Override delete_model to restore stock when a sale is deleted
    def delete_model(self, model):
        try:
            # Restore stock when deleting a sale
            if model.item_type == 'product':
                item = Product.query.get(model.item_id)
            elif model.item_type == 'phone':
                item = Phone.query.get(model.item_id)
            else:
                item = None
            
            if item:
                item.stock += model.quantity
                self.session.add(item)
            
            self.session.delete(model)
            self.session.commit()
            
            return True
            
        except Exception as e:
            if not self.handle_view_exception(e):
                flash(f'Failed to delete record: {str(e)}', 'error')
            self.session.rollback()
            return False
    def _get_current_user(self):
        """Get current user with multiple fallback methods"""
        if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
            return current_user
        
        if hasattr(g, 'current_user') and g.current_user and hasattr(g.current_user, 'is_authenticated') and g.current_user.is_authenticated:
            return g.current_user
        
        from flask import session
        if 'user_id' in session:
            user = User.query.get(session['user_id'])
            if user:
                return user
        
        return None

    def create_form(self, obj=None):
        form = super().create_form(obj)
        # Initialize with empty choices - will be populated by JavaScript
        form.item_id.choices = []
        form.item_id.data = ''  # Ensure no default selection
        return form

    def edit_form(self, obj=None):
        form = super().edit_form(obj)
        # For editing, populate choices based on the current item_type
        if obj and obj.item_type:
            if obj.item_type == 'product':
                form.item_id.choices = [(str(p.id), f"{p.id} - {p.name}") for p in Product.query.all()]
            elif obj.item_type == 'phone':
                form.item_id.choices = [(str(p.id), f"{p.id} - {p.name}") for p in Phone.query.all()]
            else:
                form.item_id.choices = [('', 'Select item type first')]
        else:
            form.item_id.choices = [('', 'Please select item type first')]
        return form

    # Method 2: Keep the on_model_change as backup with better error handling
    def on_model_change(self, form, model, is_created):
        
        # Only set worker_id if it's not already set and this is a creation
        if is_created and not model.worker_id:
            user = self._get_current_user()
            
            if user and user.is_authenticated:
                model.worker_id = user.id
            else:
                # This should not happen if create_model is working properly
                raise ValueError("Authentication required to create sales")
        
    # Method 3: Override is_accessible to ensure user is authenticated
    def is_accessible(self):
        return current_user.is_authenticated
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))

# ===== CUSTOM DASHBOARD =====
from flask_admin import BaseView, expose

class DashboardView(BaseView):
    """Custom dashboard for owners with sales statistics"""
    
    @expose('/')
    def index(self):
        # Get sales statistics
        from sqlalchemy import func
        from datetime import datetime, timedelta
        
        # Today's sales
        today = datetime.now().date()
        today_sales = Sale.query.filter(func.date(Sale.sale_date) == today).all()
        today_revenue = sum(sale.quantity * sale.selling_price for sale in today_sales)
        
        # This week's sales
        week_ago = today - timedelta(days=7)
        week_sales = Sale.query.filter(Sale.sale_date >= week_ago).all()
        week_revenue = sum(sale.quantity * sale.selling_price for sale in week_sales)
        
        # This month's sales
        month_ago = today - timedelta(days=30)
        month_sales = Sale.query.filter(Sale.sale_date >= month_ago).all()
        month_revenue = sum(sale.quantity * sale.selling_price for sale in month_sales)
        
        # Top selling items (this week)
        from collections import defaultdict
        item_sales = defaultdict(int)
        for sale in week_sales:
            if sale.item_type == 'product':
                item = Product.query.get(sale.item_id)
                item_name = item.name if item else 'Unknown'
            else:
                item = Phone.query.get(sale.item_id)
                item_name = f"{item.brand} {item.model}" if item else 'Unknown'
            item_sales[item_name] += sale.quantity
        
        top_items_week = sorted(item_sales.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Top selling items (this month)
        item_sales_month = defaultdict(int)
        for sale in month_sales:
            if sale.item_type == 'product':
                item = Product.query.get(sale.item_id)
                item_name = item.name if item else 'Unknown'
            else:
                item = Phone.query.get(sale.item_id)
                item_name = f"{item.brand} {item.model}" if item else 'Unknown'
            item_sales_month[item_name] += sale.quantity
        
        top_items_month = sorted(item_sales_month.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Worker performance
        worker_sales = defaultdict(lambda: {'count': 0, 'revenue': 0})
        for sale in week_sales:
            worker = User.query.get(sale.worker_id)
            worker_email = worker.email if worker else 'Unknown'
            worker_sales[worker_email]['count'] += sale.quantity
            worker_sales[worker_email]['revenue'] += sale.quantity * sale.selling_price
        
        return self.render('admin/dashboard.html',
                          today_sales_count=len(today_sales),
                          today_revenue=today_revenue,
                          week_sales_count=len(week_sales),
                          week_revenue=week_revenue,
                          month_sales_count=len(month_sales),
                          month_revenue=month_revenue,
                          top_items=top_items_week,
                          top_items_month=top_items_month,
                          worker_performance=dict(worker_sales))
    
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == 'owner'
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))
class OwnerUserModelView(ModelView):
    """Owner can see and manage all users"""
    can_create = True
    can_edit = True
    can_delete = True
    form_excluded_columns = ['created_at', 'updated_at', 'role']
    def on_model_change(self, form, model, is_created):
        if is_created:
            model.role = 'worker'
        

    # Customize the list view
    column_list = ['id', 'email', 'role', 'name']
    column_searchable_list = ['email', 'role', 'name']
    column_filters = ['role']
    column_labels = {
        'id': 'ID de Usuario',
        'email': 'Dirección de Email',
        'role': 'Rol',
        'name': 'Nombre'
    }
    
    # Override create_model to ensure passwords are properly hashed
    def create_model(self, form):
        try:
            # Create the model from form data
            model = self.model()
            form.populate_obj(model)
            
            # Ensure role is set
            self.on_model_change(form, model, True)
            
            # Hash the password if it's provided
            if hasattr(form, 'password') and form.password.data:
                model.set_password(form.password.data)
            
            # Save to database
            self.session.add(model)
            self.session.commit()
            
            return model
            
        except Exception as e:
            if not self.handle_view_exception(e):
                flash(f'Failed to create user: {str(e)}', 'error')
            self.session.rollback()
            return False
    
    # Override update_model to handle password updates
    def update_model(self, form, model):
        try:
            # Check if password field is being updated
            if hasattr(form, 'password') and form.password.data:
                # Hash the new password
                model.set_password(form.password.data)
            
            # Update other fields
            form.populate_obj(model)
            
            # Save to database
            self.session.add(model)
            self.session.commit()
            
            return True
            
        except Exception as e:
            if not self.handle_view_exception(e):
                flash(f'Failed to update user: {str(e)}', 'error')
            self.session.rollback()
            return False
    
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == 'owner'
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))

class OwnerSaleModelView(ModelView):
    """Owner can see all sales with detailed information including who sold what"""
    can_create = False  # Sales should be created through the worker interface
    can_edit = False    # Prevent editing to maintain data integrity
    can_delete = True   # Owner can delete if needed
    
    # Show detailed information about each sale
    column_list = ['id', 'item_type', 'item_name', 'worker_email', 'quantity', 'selling_price', 'total_amount', 'sale_date']
    column_searchable_list = []  # Remove item_name since it's a computed field
    column_filters = ['item_type', 'sale_date']
    column_sortable_list = ['id', 'item_type', 'quantity', 'selling_price', 'sale_date']
    
    column_labels = {
        'id': 'ID de Venta',
        'item_type': 'Tipo de Artículo',
        'item_name': 'Nombre del Artículo',
        'worker_email': 'Vendido Por',
        'quantity': 'Cantidad',
        'selling_price': 'Precio Unitario',
        'total_amount': 'Monto Total',
        'sale_date': 'Fecha de Venta'
    }
    
    # Add custom columns to show readable information
    column_extra_fields = ['item_name', 'worker_email', 'total_amount']
    
    def _item_name_formatter(view, context, model, name):
        """Get the actual name of the sold item"""
        if model.item_type == 'product':
            item = Product.query.get(model.item_id)
            return item.name if item else 'Producto Desconocido'
        elif model.item_type == 'phone':
            item = Phone.query.get(model.item_id)
            return f"{item.brand} {item.model}" if item else 'Teléfono Desconocido'
        return 'Artículo Desconocido'
    
    def _worker_email_formatter(view, context, model, name):
        """Get the email of the worker who made the sale"""
        worker = User.query.get(model.worker_id)
        return worker.email if worker else 'Trabajador Desconocido'
    
    def _total_amount_formatter(view, context, model, name):
        """Calculate total amount (quantity * selling_price)"""
        return f"${model.quantity * model.selling_price:.2f}"
    
    column_formatters = {
        'item_name': _item_name_formatter,
        'worker_email': _worker_email_formatter,
        'total_amount': _total_amount_formatter
    }
    
    # Customize the date filter to search by day only
    def get_query(self):
        """Override to handle custom date filtering and item name searching"""
        query = super().get_query()
        
        # Get the search term from request args
        search_term = request.args.get('search')
        if search_term:
            # Search in products
            products = Product.query.filter(Product.name.ilike(f'%{search_term}%')).all()
            product_ids = [p.id for p in products]
            
            # Search in phones
            phones = Phone.query.filter(
                (Phone.name.ilike(f'%{search_term}%')) |
                (Phone.brand.ilike(f'%{search_term}%')) |
                (Phone.model.ilike(f'%{search_term}%'))
            ).all()
            phone_ids = [p.id for p in phones]
            
            # Filter sales by matching item IDs
            query = query.filter(
                ((Sale.item_type == 'product') & (Sale.item_id.in_(product_ids))) |
                ((Sale.item_type == 'phone') & (Sale.item_id.in_(phone_ids)))
            )
        
        # Get the date filter value from request args
        date_filter = request.args.get('flt1_sale_date')
        if date_filter:
            try:
                # Parse the date and create a range for the entire day
                from datetime import datetime, timedelta
                filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                next_date = filter_date + timedelta(days=1)
                
                # Filter sales for the entire day
                query = query.filter(
                    Sale.sale_date >= filter_date,
                    Sale.sale_date < next_date
                )
            except ValueError:
                pass  # If date parsing fails, ignore the filter
        
        return query
    
    # Add custom CSS for better readability
    def render(self, template, **kwargs):
        kwargs['custom_css'] = '''
        <style>
        .table-striped > tbody > tr:nth-of-type(odd) {
            background-color: rgba(0,0,0,.05);
        }
        .money {
            color: #28a745;
            font-weight: bold;
        }
        </style>
        '''
        return super().render(template, **kwargs)
    
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == 'owner'
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))

# ===== WORKER-SPECIFIC VIEWS =====
# ===== WORKER-SPECIFIC VIEWS =====
class WorkerSaleModelView(ModelView):
    """Worker-specific sales view - can create sales but can't see who created what"""
    can_create = True
    can_edit = False   # Workers can't edit existing sales
    can_delete = False # Workers can't delete sales
    
    # Show sales information without worker details
    column_list = ['id', 'item_type', 'item_name', 'quantity', 'selling_price', 'total_amount', 'sale_date']
    column_searchable_list = ['item_type']
    column_filters = ['item_type', 'sale_date']
    column_sortable_list = ['id', 'item_type', 'quantity', 'selling_price', 'sale_date']
    
    column_labels = {
        'id': 'Sale ID',
        'item_type': 'Item Type', 
        'item_name': 'Item Name',
        'quantity': 'Qty',
        'selling_price': 'Unit Price',
        'total_amount': 'Total Amount',
        'sale_date': 'Sale Date'
    }
    
    # Add custom columns for workers (without worker info)
    def _item_name_formatter(view, context, model, name):
        """Get the actual name of the sold item"""
        if model.item_type == 'product':
            item = Product.query.get(model.item_id)
            return item.name if item else 'Unknown Product'
        elif model.item_type == 'phone':
            item = Phone.query.get(model.item_id)
            return f"{item.brand} {item.model}" if item else 'Unknown Phone'
        return 'Unknown Item'
    
    def _total_amount_formatter(view, context, model, name):
        """Calculate total amount (quantity * selling_price)"""
        return f"${model.quantity * model.selling_price:.2f}"
    
    column_formatters = {
        'item_name': _item_name_formatter,
        'total_amount': _total_amount_formatter
    }
    
    # Override the form for creating sales
    form = SaleForm
    
    def create_form(self, obj=None):
        form = super().create_form(obj)
        # Initialize with empty choices - will be populated by JavaScript
        form.item_id.choices = []
        form.item_id.data = ''
        return form

    def edit_form(self, obj=None):
        form = super().edit_form(obj)
        # For editing, populate choices based on the current item_type
        if obj and obj.item_type:
            if obj.item_type == 'product':
                form.item_id.choices = [(str(p.id), f"{p.id} - {p.name}") for p in Product.query.all()]
            elif obj.item_type == 'phone':
                form.item_id.choices = [(str(p.id), f"{p.id} - {p.name}") for p in Phone.query.all()]
            else:
                form.item_id.choices = [('', 'Select item type first')]
        else:
            form.item_id.choices = [('', 'Please select item type first')]
        return form

    # Use the same create_model logic as SaleModelView
    def create_model(self, form):
        try:
            # Get the current user before processing the model
            user = self._get_current_user()
            
            # Create the model from form data
            model = self.model()
            form.populate_obj(model)
            
            # Set the worker_id to current user's ID
            if user and user.is_authenticated:
                model.worker_id = user.id
            else:
                raise ValueError("No authenticated user found")
            
            # Validate the item exists and check stock
            item = None
            if model.item_type == 'product':
                item = Product.query.get(model.item_id)
                if not item:
                    raise ValueError("Selected product does not exist")
            elif model.item_type == 'phone':
                item = Phone.query.get(model.item_id)
                if not item:
                    raise ValueError("Selected phone does not exist")
            
            # Check if there's enough stock
            if item.stock < model.quantity:
                raise ValueError(f"Insufficient stock. Available: {item.stock}, Requested: {model.quantity}")
            
            # Reduce the stock count
            item.stock -= model.quantity
            model.product_id = 0
            # Save both the sale and the updated item
            self.session.add(model)
            self.session.add(item)
            self._on_model_change(form, model, True)
            self.session.commit()
            
            # Send notification in background thread
            send_sale_notification(model, user.email)
            
            return model
        except Exception as e:
            if not self.handle_view_exception(e):
                flash(f'Failed to create record: {str(e)}', 'error')
            self.session.rollback()
            return False
    
    # Helper method to get current user reliably
    def _get_current_user(self):
        """Get current user with multiple fallback methods"""
        if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
            return current_user
        
        if hasattr(g, 'current_user') and g.current_user and hasattr(g.current_user, 'is_authenticated') and g.current_user.is_authenticated:
            return g.current_user
        
        from flask import session
        if 'user_id' in session:
            user = User.query.get(session['user_id'])
            if user:
                return user
        
        return None

    def on_model_change(self, form, model, is_created):
        # Only set worker_id if it's not already set and this is a creation
        if is_created and not model.worker_id:
            user = self._get_current_user()
            if user and user.is_authenticated:
                model.worker_id = user.id
            else:
                raise ValueError("Authentication required to create sales")

    def is_accessible(self):
        return current_user.is_authenticated
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))

class WorkerInventoryModelView(ModelView):
    """Workers can view and manage inventory (phones and products)"""
    can_create = True
    can_edit = True
    can_delete = True
    
    # Show essential inventory information
    column_list = ['id', 'name', 'brand', 'model', 'stock', 'cost_price']
    column_searchable_list = ['name', 'brand', 'model']
    column_filters = ['brand', 'stock']
    
    column_labels = {
        'id': 'ID',
        'name': 'Name',
        'brand': 'Brand',
        'model': 'Model',
        'stock': 'In Stock',
        'cost_price': 'Cost Price'
    }
    
    # Add form validation for stock and cost_price
    def validate_form(self, form):
        if hasattr(form, 'stock') and form.stock.data is not None:
            if form.stock.data < 0:
                flash('Stock cannot be negative', 'error')
                return False
        
        if hasattr(form, 'cost_price') and form.cost_price.data is not None:
            if form.cost_price.data <= 0:
                flash('Cost price must be greater than 0', 'error')
                return False
        
        return True
    
    def is_accessible(self):
        return current_user.is_authenticated
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))

class WorkerPhoneModelView(ModelView):
    """Workers can view and manage phones with all phone-specific fields"""
    can_create = True
    can_edit = True
    can_delete = True
    
    # Show all phone fields
    column_list = ['id', 'name', 'brand', 'model', 'storage', 'color', 'condition', 'stock', 'cost_price']
    column_searchable_list = ['name', 'brand', 'model', 'storage', 'color']
    column_filters = ['brand', 'condition', 'stock']
    column_sortable_list = ['id', 'name', 'brand', 'model', 'stock', 'cost_price']
    
    column_labels = {
        'id': 'ID',
        'name': 'Name',
        'brand': 'Brand',
        'model': 'Model',
        'storage': 'Storage',
        'color': 'Color',
        'condition': 'Condition',
        'stock': 'In Stock',
        'cost_price': 'Cost Price'
    }
    
    # Add custom column formatter for stock alerts
    def _stock_formatter(view, context, model, name):
        """Format stock with color coding for low stock"""
        if model.stock <= 5:
            return Markup(f'<span style="color: red; font-weight: bold;">{model.stock} (LOW)</span>')
        elif model.stock <= 10:
            return Markup(f'<span style="color: orange; font-weight: bold;">{model.stock} (MED)</span>')
        else:
            return Markup(f'<span style="color: green;">{model.stock}</span>')
    
    column_formatters = {
        'stock': _stock_formatter
    }
    
    # Form validation
    def validate_form(self, form):
        if hasattr(form, 'stock') and form.stock.data is not None:
            if form.stock.data < 0:
                flash('Stock cannot be negative', 'error')
                return False
        
        if hasattr(form, 'cost_price') and form.cost_price.data is not None:
            if form.cost_price.data <= 0:
                flash('Cost price must be greater than 0', 'error')
                return False
        
        # Validate required fields
        if hasattr(form, 'name') and not form.name.data:
            flash('Name is required', 'error')
            return False
        
        if hasattr(form, 'brand') and not form.brand.data:
            flash('Brand is required', 'error')
            return False
        
        if hasattr(form, 'model') and not form.model.data:
            flash('Model is required', 'error')
            return False
        
        return True
    
    def is_accessible(self):
        return current_user.is_authenticated
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))

class WorkerProductModelView(ModelView):
    """Workers can view and manage products with product-specific fields"""
    can_create = True
    can_edit = True
    can_delete = True
    
    # Show all product fields
    column_list = ['id', 'name', 'brand', 'model', 'cost_price', 'stock']
    column_searchable_list = ['name', 'brand', 'model']
    column_filters = ['brand', 'stock']
    column_sortable_list = ['id', 'name', 'brand', 'model', 'stock', 'cost_price']
    
    column_labels = {
        'id': 'ID',
        'name': 'Name',
        'brand': 'Brand',
        'model': 'Model',
        'cost_price': 'Cost Price',
        'stock': 'In Stock'
    }
    
    # Add custom column formatter for stock alerts
    def _stock_formatter(view, context, model, name):
        """Format stock with color coding for low stock"""
        if model.stock <= 5:
            return Markup(f'<span style="color: red; font-weight: bold;">{model.stock} (LOW)</span>')
        elif model.stock <= 10:
            return Markup(f'<span style="color: orange; font-weight: bold;">{model.stock} (MED)</span>')
        else:
            return Markup(f'<span style="color: green;">{model.stock}</span>')
    
    column_formatters = {
        'stock': _stock_formatter
    }
    
    # Form validation
    def validate_form(self, form):
        if hasattr(form, 'stock') and form.stock.data is not None:
            if form.stock.data < 0:
                flash('Stock cannot be negative', 'error')
                return False
        
        if hasattr(form, 'cost_price') and form.cost_price.data is not None:
            if form.cost_price.data <= 0:
                flash('Cost price must be greater than 0', 'error')
                return False
        
        # Validate required fields
        if hasattr(form, 'name') and not form.name.data:
            flash('Name is required', 'error')
            return False
        
        return True
    
    def is_accessible(self):
        return current_user.is_authenticated
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))

class WorkerDashboardView(BaseView):
    """Worker dashboard showing inventory status, recent sales, and cash declaration"""
    
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        # Handle cash declaration
        if request.method == 'POST':
            if current_user.role != 'worker':
                flash('Only workers can declare cash', 'danger')
                return redirect('/admin')
            
            try:
                opening_cash = float(request.form['opening_cash'])
                if opening_cash < 0:
                    flash('Opening cash cannot be negative', 'danger')
                    return self.index()
                
                # Check if cash already declared today
                today = date.today()
                existing_cash = CashRegister.query.filter_by(date=today, is_open=True).first()
                
                if existing_cash:
                    flash('Cash already declared for today', 'info')
                    return self.index()
                
                # Create new cash register entry
                cash_register = CashRegister(
                    opening_cash=opening_cash,
                    declared_by=current_user.id
                )
                db.session.add(cash_register)
                db.session.commit()
                
                # Send notification to owner
                send_cash_declaration_notification(cash_register)
                
                flash(f'Opening cash declared: ${opening_cash:.2f}', 'success')
                return redirect('/admin')
                
            except ValueError:
                flash('Please enter a valid amount', 'danger')
            except Exception as e:
                flash(f'Error: {str(e)}', 'danger')
        
        # Check if cash already declared today
        today = date.today()
        cash_declared = CashRegister.query.filter_by(date=today, is_open=True).first()
        # Fix: Pass worker object separately for template
        worker = None
        if cash_declared:
            worker = User.query.get(cash_declared.declared_by)
        
        # Get low stock items
        low_stock_phones = Phone.query.filter(Phone.stock <= 5).all()
        low_stock_products = Product.query.filter(Product.stock <= 5).all()
        
        # Get recent sales (last 10)
        from sqlalchemy import desc
        recent_sales = Sale.query.order_by(desc(Sale.sale_date)).limit(10).all()
        
        # Get total inventory counts
        total_phones = Phone.query.count()
        total_products = Product.query.count()
        total_sales = Sale.query.count()
        
        # Calculate total inventory value
        phone_value = sum(float(phone.stock * phone.cost_price) for phone in Phone.query.all())
        product_value = sum(float(product.stock * product.cost_price) for product in Product.query.all())
        total_value = phone_value + product_value
        
        # Calculate today's sales
        today_sales = Sale.query.filter(db.func.date(Sale.sale_date) == today).all()
        today_revenue = sum(sale.quantity * sale.selling_price for sale in today_sales)

        # Ensure worker is None if no cash_declared
        if not cash_declared:
            worker = None

        return self.render('admin/worker_dashboard.html',
                          cash_declared=cash_declared,
                          worker=worker,
                          low_stock_phones=low_stock_phones,
                          low_stock_products=low_stock_products,
                          recent_sales=recent_sales,
                          total_phones=total_phones,
                          total_products=total_products,
                          total_sales=total_sales,
                          total_value=total_value,
                          today_revenue=today_revenue,
                          today_sales_count=len(today_sales))
    
    def is_accessible(self):
        return current_user.is_authenticated
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))

class CashRegisterModelView(ModelView):
    """Owner can view cash register entries"""
    can_create = False
    can_edit = False
    can_delete = False
    
    column_list = ['date', 'opening_cash', 'total_sales', 'expected_closing', 'worker_name', 'is_open', 'actions']
    column_searchable_list = ['date']
    column_filters = ['date', 'is_open']
    column_sortable_list = ['date', 'opening_cash', 'total_sales']
    
    column_labels = {
        'date': 'Fecha',
        'opening_cash': 'Caja Inicial',
        'total_sales': 'Ventas del Día',
        'expected_closing': 'Caja Esperada',
        'worker_name': 'Declarado Por',
        'is_open': 'Estado',
        'actions': 'Acciones'
    }
    
    def _worker_name_formatter(view, context, model, name):
        """Get the name of the worker who declared cash"""
        worker = User.query.get(model.declared_by)
        return worker.name if worker else 'Desconocido'
    
    def _expected_closing_formatter(view, context, model, name):
        """Calculate expected closing cash"""
        return f"${model.opening_cash + model.total_sales:.2f}"
    
    def _is_open_formatter(view, context, model, name):
        """Format open/closed status"""
        if model.is_open:
            return Markup('<span class="badge bg-success">Abierta</span>')
        else:
            closed_time = model.closed_at.strftime('%H:%M') if model.closed_at else 'N/A'
            return Markup(f'<span class="badge bg-secondary">Cerrada ({closed_time})</span>')
    
    def _actions_formatter(view, context, model, name):
        """Show close button for open registers"""
        if model.is_open:
            return Markup(f'<a href="/admin/close_cash_register/{model.id}" class="btn btn-warning btn-sm">🔒 Cerrar</a>')
        else:
            return Markup('<span class="text-muted">Cerrada</span>')
    
    column_formatters = {
        'worker_name': _worker_name_formatter,
        'expected_closing': _expected_closing_formatter,
        'is_open': _is_open_formatter,
        'actions': _actions_formatter
    }
    
    def get_query(self):
        """Override to calculate total sales for each day"""
        query = super().get_query()
        
        # Update total_sales for each cash register entry
        cash_entries = CashRegister.query.all()
        for entry in cash_entries:
            if entry.is_open:  # Only update for open entries
                today_sales = Sale.query.filter(db.func.date(Sale.sale_date) == entry.date).all()
                total_sales_amount = sum(sale.quantity * sale.selling_price for sale in today_sales)
                entry.total_sales = total_sales_amount
                db.session.add(entry)
        
        db.session.commit()
        return query
    
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == 'owner'
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))

admin = Admin(app, name='Tienda de Teléfonos', template_mode='bootstrap4', index_view=None)

# ===== DASHBOARD (Owner only) =====
admin.add_view(DashboardView(name='Panel de Control', endpoint='dashboard'))

# ===== OWNER-ONLY VIEWS =====
admin.add_view(OwnerUserModelView(User, db.session, name='Usuarios', category='Propietario'))
admin.add_view(OwnerSaleModelView(Sale, db.session, name='Reporte de Ventas', category='Propietario', endpoint='owner_sales'))
admin.add_view(CashRegisterModelView(CashRegister, db.session, name='Registros de Caja', category='Propietario', endpoint='cash_registers'))

# ===== WORKER VIEWS =====
admin.add_view(WorkerDashboardView(name='Panel de Trabajador', endpoint='worker_dashboard', category='Trabajador'))
admin.add_view(WorkerSaleModelView(Sale, db.session, name='Ventas', category='Trabajador', endpoint='worker_sales'))
admin.add_view(WorkerPhoneModelView(Phone, db.session, name='Teléfonos', category='Trabajador'))
admin.add_view(WorkerProductModelView(Product, db.session, name='Productos', category='Trabajador'))

# ===== ROUTES =====

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=True)  # Added remember=True for session persistence
            # Store user_id in session as backup
            from flask import session
            session['user_id'] = user.id
            return redirect('/admin')
        flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    from flask import session
    session.pop('user_id', None)
    logout_user()
    return redirect(url_for('login'))

@app.route('/admin/_get_items')
@login_required
def get_items():
    return _get_items_logic()

@app.route('/_get_items')
def get_items_test():
    return _get_items_logic()

def _get_items_logic():
    try:
        item_type = request.args.get('type')
        if not item_type:
            return jsonify({'error': 'Item type is required'}), 400
            
        if item_type == 'product':
            items = Product.query.filter(Product.stock > 0).all()
        elif item_type == 'phone':
            items = Phone.query.filter(Phone.stock > 0).all()
        else:
            return jsonify({'error': 'Invalid item type'}), 400
        
        result = []
        for item in items:
            if item_type == 'product':
                label = f"{item.id} - {item.name}"
                if item.brand:
                    label += f" {item.brand}"
                if item.model:
                    label += f" {item.model}"
                label += f" ${item.cost_price}"
            else:
                label = f"{item.id} - {item.name} {item.brand} {item.model} {item.storage} {item.color} {item.condition} ${item.cost_price}"
            
            result.append({
                "id": item.id, 
                "label": label
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/init_data')
@login_required
def init_data():
    """Initialize database with dummy data for testing"""
    if current_user.role != 'owner':
        flash('Only owners can initialize data', 'danger')
        return redirect('/admin')
    
    try:
        # Check if data already exists
        if User.query.count() > 0:
            flash('Data already exists in database', 'info')
            return redirect('/admin')
        
        # Create users (matching your existing structure)
        owner = User(
            email='mohamed@gmail.com',
            name='mohamed',
            role='owner'
        )
        owner.set_password('password123')
        db.session.add(owner)
        
        worker1 = User(
            email='zaka@gmail.com',
            name='zaka',
            role='worker'
        )
        worker1.set_password('password123')
        db.session.add(worker1)
        
        worker2 = User(
            email='khalid@gmail.com',
            name='khalid',
            role='worker'
        )
        worker2.set_password('password123')
        db.session.add(worker2)
        
        # Create sample products (matching your existing data)
        products = [
            Product(name='pochette', brand='louis vuitton', model='rose', cost_price=100.00, stock=0),
            Product(name='pochette', brand='simple', model='1233', cost_price=10.00, stock=9),
            Product(name='ecouteurs', brand='oraimo', model='pro 3', cost_price=100.00, stock=12),
            Product(name='ecouteurs', brand='iphone', model='pro', cost_price=150.00, stock=300),
            Product(name='Cable USB-C', brand='Samsung', model='Fast Charge', cost_price=5.99, stock=50),
            Product(name='Cargador Inalámbrico', brand='Apple', model='MagSafe', cost_price=39.99, stock=25),
            Product(name='Protector de Pantalla', brand='Generic', model='Tempered Glass', cost_price=8.99, stock=100),
            Product(name='Auriculares Bluetooth', brand='Sony', model='WH-1000XM4', cost_price=299.99, stock=15),
            Product(name='Cable Lightning', brand='Apple', model='Original', cost_price=19.99, stock=75),
            Product(name='Power Bank', brand='Anker', model='20000mAh', cost_price=49.99, stock=30)
        ]
        
        for product in products:
            db.session.add(product)
        
        # Create sample phones (matching your existing data)
        phones = [
            Phone(name='iphone', brand='apple', model='12', storage='256', color='rose', condition='100%', stock=0, cost_price=1000),
            Phone(name='s23', brand='samsung', model='651652365', storage='128', color='verde', condition='novo', stock=0, cost_price=250),
            Phone(name='huawei', brand='huawei', model='p50', storage='128', color='negro', condition='novo', stock=0, cost_price=120),
            Phone(name='iPhone 14 Pro', brand='Apple', model='14 Pro', storage='128GB', color='Space Black', condition='New', stock=10, cost_price=999.99),
            Phone(name='Samsung Galaxy S23', brand='Samsung', model='S23', storage='256GB', color='Phantom Black', condition='New', stock=8, cost_price=899.99),
            Phone(name='iPhone 13', brand='Apple', model='13', storage='128GB', color='Blue', condition='Used', stock=5, cost_price=699.99),
            Phone(name='Google Pixel 7', brand='Google', model='Pixel 7', storage='128GB', color='Obsidian', condition='New', stock=6, cost_price=599.99),
            Phone(name='Samsung Galaxy A54', brand='Samsung', model='A54', storage='128GB', color='Awesome Black', condition='New', stock=12, cost_price=449.99),
            Phone(name='iPhone 12', brand='Apple', model='12', storage='64GB', color='White', condition='Used', stock=7, cost_price=549.99),
            Phone(name='OnePlus 11', brand='OnePlus', model='11', storage='256GB', color='Titan Black', condition='New', stock=4, cost_price=699.99)
        ]
        
        for phone in phones:
            db.session.add(phone)
        
        # Create some sample sales (matching your existing structure)
        from datetime import datetime, timedelta
        
        # Today's sales
        today = datetime.now().date()
        sales_today = [
            Sale(item_type='product', item_id=2, product_id=2, worker_id=2, quantity=1, selling_price=15.00, sale_date=datetime.now()),
            Sale(item_type='phone', item_id=1, product_id=0, worker_id=2, quantity=1, selling_price=1100.00, sale_date=datetime.now()),
            Sale(item_type='product', item_id=3, product_id=3, worker_id=3, quantity=2, selling_price=120.00, sale_date=datetime.now()),
            Sale(item_type='phone', item_id=3, product_id=0, worker_id=3, quantity=1, selling_price=150.00, sale_date=datetime.now())
        ]
        
        # Yesterday's sales
        yesterday = today - timedelta(days=1)
        sales_yesterday = [
            Sale(item_type='product', item_id=1, product_id=1, worker_id=2, quantity=1, selling_price=120.00, sale_date=datetime.combine(yesterday, datetime.min.time()) + timedelta(hours=10)),
            Sale(item_type='phone', item_id=2, product_id=0, worker_id=3, quantity=1, selling_price=300.00, sale_date=datetime.combine(yesterday, datetime.min.time()) + timedelta(hours=14)),
            Sale(item_type='product', item_id=5, product_id=5, worker_id=2, quantity=3, selling_price=20.00, sale_date=datetime.combine(yesterday, datetime.min.time()) + timedelta(hours=16))
        ]
        
        for sale in sales_today + sales_yesterday:
            db.session.add(sale)
        
        # Create a cash register entry for today
        cash_register = CashRegister(
            opening_cash=500.00,
            declared_by=2,
            date=today
        )
        db.session.add(cash_register)
        
        db.session.commit()
        
        flash('✅ Sample data initialized successfully!', 'success')
        flash('📧 Owner: mohamed@gmail.com / password123', 'info')
        flash('👤 Worker 1: zaka@gmail.com / password123', 'info')
        flash('👤 Worker 2: khalid@gmail.com / password123', 'info')
        
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Error initializing data: {str(e)}', 'danger')
    
    return redirect('/admin')

@app.route('/create_database')
@login_required
def create_database():
    """Create all database tables"""
    if current_user.role != 'owner':
        flash('Only owners can create database', 'danger')
        return redirect('/admin')
    
    try:
        # Create all tables
        db.create_all()
        flash('✅ Database tables created successfully!', 'success')
        
    except Exception as e:
        flash(f'❌ Error creating database: {str(e)}', 'danger')
    
    return redirect('/admin')

@app.route('/admin/logout')
@login_required
def admin_logout():
    from flask import session
    session.pop('user_id', None)
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/admin/close_cash_register/<int:register_id>')
@login_required
def close_cash_register(register_id):
    """Owner can manually close a cash register"""
    if current_user.role != 'owner':
        flash('Only owners can close cash registers', 'danger')
        return redirect('/admin')
    
    try:
        cash_register = CashRegister.query.get_or_404(register_id)
        
        if not cash_register.is_open:
            flash('Cash register is already closed', 'info')
            return redirect('/admin')
        
        # Calculate final sales
        today_sales = Sale.query.filter(db.func.date(Sale.sale_date) == cash_register.date).all()
        total_sales_amount = sum(sale.quantity * sale.selling_price for sale in today_sales)
        
        # Close the register
        cash_register.is_open = False
        cash_register.closed_at = datetime.utcnow()
        cash_register.total_sales = total_sales_amount
        db.session.add(cash_register)
        db.session.commit()
        
        flash(f'Cash register for {cash_register.date.strftime("%d/%m/%Y")} has been closed', 'success')
        
    except Exception as e:
        flash(f'Error closing cash register: {str(e)}', 'danger')
    
    return redirect('/admin')

# --- User CRUD Forms ---
from flask import render_template, redirect, url_for, request, flash, abort
from wtforms import StringField, PasswordField, SelectField
from wtforms.validators import DataRequired, Email
from flask_wtf import FlaskForm

class UserForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password')  # Only required on create
    role = SelectField('Role', choices=[('owner', 'Owner'), ('worker', 'Worker')], default='worker', validators=[DataRequired()])

# --- User CRUD Routes ---

@app.route('/users')
@login_required
def user_list():
    if current_user.role != 'owner':
        abort(403)
    users = User.query.all()
    return render_template('user_list.html', users=users)

@app.route('/users/add', methods=['GET', 'POST'])
@login_required
def user_add():
    if current_user.role != 'owner':
        abort(403)
    form = UserForm()
    if request.method == 'GET':
        form.role.data = 'worker'  # Set default role to worker on GET
    if form.validate_on_submit():
        now = datetime.now()
        user = User(
            name=form.name.data,
            email=form.email.data,
            role=form.role.data,
            created_at=now,
            updated_at=now
        )
        if form.password.data:
            user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('User added successfully!', 'success')
        return redirect(url_for('user_list'))
    return render_template('user_form.html', form=form, action='Add')

@app.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def user_edit(user_id):
    if current_user.role != 'owner':
        abort(403)
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)
    if request.method == 'POST' and form.validate_on_submit():
        user.name = form.name.data
        user.email = form.email.data
        user.role = form.role.data
        if form.password.data:
            user.set_password(form.password.data)
        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('user_list'))
    return render_template('user_form.html', form=form, action='Edit')

@app.route('/users/delete/<int:user_id>', methods=['GET', 'POST'])
@login_required
def user_delete(user_id):
    if current_user.role != 'owner':
        abort(403)
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully!', 'success')
        return redirect(url_for('user_list'))
    return render_template('user_confirm_delete.html', user=user)

import webbrowser
import threading
import os

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Timer(1.5, open_browser).start()
    app.run(debug=True)