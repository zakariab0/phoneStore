from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
import requests
import threading
import time
# import schedule  # Temporarily commented out

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://zakariab0$med:Andiibaloz123@zakariab0.mysql.pythonanywhere-services.com/zakariab0$default'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Callmebot configuration
CALLMEBOT_API_KEY = '2290339'
CALLMEBOT_PHONE = '34602007411'

# Import models after db initialization
from models import User, Product, Sale, Phone, CashRegister, ProductLog

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# WhatsApp notification functions
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
        requests.get(url, timeout=10)
        
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

def send_cash_declaration_notification(amount, worker_email):
    """Send WhatsApp notification for cash declaration"""
    try:
        message = f"""💰 Declaración de Caja

👤 Trabajador: {worker_email}
💵 Monto Inicial: ${amount:.2f}
📅 Fecha: {date.today().strftime('%d/%m/%Y')}
⏰ Hora: {datetime.now().strftime('%H:%M')}

La caja ha sido abierta para el día de hoy."""

        import urllib.parse
        encoded_message = urllib.parse.quote(message)
        url = f"https://api.callmebot.com/whatsapp.php?phone={CALLMEBOT_PHONE}&text={encoded_message}&apikey={CALLMEBOT_API_KEY}"
        requests.get(url, timeout=10)
        
    except Exception as e:
        pass

# Temporarily disabled daily report functionality
# def send_daily_report():
#     """Send daily cash report and close register"""
#     pass

# def schedule_daily_report():
#     """Schedule daily report at 23:59"""
#     pass

# Background thread for scheduling (temporarily disabled)
# def run_scheduler():
#     schedule.every().day.at("23:59").do(send_daily_report)
#     while True:
#         schedule.run_pending()
#         time.sleep(60)

# Start scheduler in background (temporarily disabled)
# scheduler_thread = threading.Thread(target=run_scheduler)
# scheduler_thread.daemon = True
# scheduler_thread.start()

# Rest of your app code remains the same...
# (Copy all the routes and admin views from your original app.py)

if __name__ == '__main__':
    app.run(debug=True) 