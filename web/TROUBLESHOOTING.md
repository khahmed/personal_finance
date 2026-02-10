# Troubleshooting Guide

## Network Error: "NetworkError when attempting to fetch resource"

This error typically means the frontend cannot connect to the backend server. Follow these steps:

### 1. Check if the Server is Running

**Check if Flask is running:**
```bash
# Check if port 5000 is in use
lsof -i :5000
# or
netstat -tuln | grep 5000
```

**Start the server:**
```bash
cd /home/khalid/personal_finance
python -m web.app
```

Or use the startup script:
```bash
./run_web_app.sh
```

**Expected output:**
```
 * Running on http://0.0.0.0:5000
 * Debug mode: on
```

### 2. Check Server Logs

Look for errors in the terminal where Flask is running. Common issues:

**Database Connection Error:**
```
Error creating connection pool: ...
```
**Solution:** Check your `config.py` or environment variables:
```bash
export DB_HOST=localhost
export DB_NAME=portfolio_db
export DB_USER=your_user
export DB_PASSWORD=your_password
export DB_PORT=5432
```

**Import Errors:**
```
ModuleNotFoundError: No module named 'flask'
```
**Solution:** Install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Check Browser Console

Open browser Developer Tools (F12) and check:
- **Console tab:** Look for JavaScript errors
- **Network tab:** Check if the request to `/api/query` is being made
  - Status code (should be 200 for success)
  - Response preview
  - Request URL (should be `http://localhost:5000/api/query`)

### 4. Verify URL Configuration

Check that the frontend is pointing to the correct backend URL:

In `web/static/js/app.js`, line 3:
```javascript
const API_BASE = '/api';
```

This assumes the frontend and backend are on the same origin. If they're not:
- Change to: `const API_BASE = 'http://localhost:5000/api';`

### 5. Test Backend Directly

Test if the backend is responding:

```bash
# Test the root endpoint
curl http://localhost:5000/

# Test the API
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is my total portfolio value?"}'
```

### 6. Check CORS Issues

If you see CORS errors in the browser console, the server might not be allowing requests. The app already has `CORS(app)` configured, but verify it's working.

### 7. Database Connection Issues

**Check database is running:**
```bash
# PostgreSQL
sudo systemctl status postgresql
# or
pg_isready
```

**Test database connection:**
```python
python -c "from database.db_manager import DatabaseManager; from config import DB_CONFIG; db = DatabaseManager(DB_CONFIG); print('Connected!')"
```

### 8. Port Already in Use

If port 5000 is already in use:

**Option 1:** Change the port in `web/app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Change to 5001
```

**Option 2:** Kill the process using port 5000:
```bash
lsof -ti:5000 | xargs kill -9
```

### 9. Check Firewall

If you're accessing from a different machine:
```bash
# Allow port 5000
sudo ufw allow 5000
```

### 10. Common Error Messages and Solutions

| Error Message | Solution |
|--------------|----------|
| "Database manager not initialized" | Check database connection in `config.py` |
| "ModuleNotFoundError: No module named 'X'" | Run `pip install -r requirements.txt` |
| "Connection refused" | Server is not running - start Flask app |
| "CORS policy" | Check CORS configuration in `app.py` |
| "Timeout" | Database might be slow or unresponsive |

### Quick Diagnostic Script

Run this to check all components:

```bash
#!/bin/bash
echo "Checking Flask server..."
curl -s http://localhost:5000/ > /dev/null && echo "✓ Server is running" || echo "✗ Server is not running"

echo "Checking database..."
python -c "from database.db_manager import DatabaseManager; from config import DB_CONFIG; db = DatabaseManager(DB_CONFIG)" 2>/dev/null && echo "✓ Database connection OK" || echo "✗ Database connection failed"

echo "Checking dependencies..."
python -c "import flask, pandas, psycopg2" 2>/dev/null && echo "✓ Dependencies installed" || echo "✗ Missing dependencies"
```

### Still Having Issues?

1. **Enable verbose logging:**
   In `web/app.py`, change:
   ```python
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Check server output:** Look for stack traces or error messages

3. **Test with a simple query:** Try "What is my total portfolio value?" first

4. **Verify file permissions:** Ensure all files are readable

5. **Check Python version:** Should be Python 3.7+
   ```bash
   python --version
   ```


