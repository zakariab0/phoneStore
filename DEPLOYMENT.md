# PythonAnywhere Deployment Guide

## Step 1: Upload Files
1. Go to **Files** tab in PythonAnywhere
2. Create directory: `boubkari`
3. Upload all files to `/home/zakariab0/boubkari/`

## Step 2: Install Dependencies
1. Go to **Consoles** tab
2. Open **Bash console**
3. Run:
```bash
cd boubkari
pip install -r requirements.txt
```

## Step 3: Set Up Web App
1. Go to **Web** tab
2. Click **Add a new web app**
3. Choose **Flask**
4. Python version: **3.9** or **3.10**
5. Source code: `/home/zakariab0/boubkari`
6. WSGI file: `/var/www/zakariab0_pythonanywhere_com_wsgi.py`

## Step 4: Configure WSGI File
Replace content with:
```python
import sys
import os

path = '/home/zakariab0/boubkari'
if path not in sys.path:
    sys.path.append(path)

from app import app as application

if __name__ == "__main__":
    application.run()
```

## Step 5: Create Database Tables
1. Go to your web app URL: `https://zakariab0.pythonanywhere.com`
2. Create a temporary user or log in
3. Visit: `https://zakariab0.pythonanywhere.com/create_database`
4. This creates all tables matching your exact database structure

## Step 6: Add Sample Data
1. Visit: `https://zakariab0.pythonanywhere.com/init_data`
2. This will create:
   - 3 users (matching your existing users)
   - 10 sample products (including your existing ones)
   - 10 sample phones (including your existing ones)
   - Sample sales data
   - Cash register entry

## Step 7: Test Your App
- **Owner Login:** mohamed@gmail.com / password123
- **Worker 1:** zaka@gmail.com / password123
- **Worker 2:** khalid@gmail.com / password123
- Test cash declaration functionality
- Test WhatsApp notifications

## Database Structure Created:
- ✅ `users` - Users with roles (owner/worker)
- ✅ `products` - Product inventory with timestamps
- ✅ `phone` - Phone inventory (note: table name is 'phone')
- ✅ `sales` - Sales records with item_type and product_id
- ✅ `cash_register` - Daily cash declarations
- ✅ `product_logs` - Product activity logs

## Features Included:
- ✅ Cash register system
- ✅ WhatsApp notifications
- ✅ Daily reports at 23:59
- ✅ Automatic cash register closing
- ✅ Worker dashboard with cash declaration
- ✅ Owner admin panel
- ✅ Exact database structure matching your SQL 