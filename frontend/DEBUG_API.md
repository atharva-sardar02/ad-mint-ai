# Debugging API Connection Issues

## Quick Checks

1. **Check API URL in browser console:**
   ```javascript
   // Open browser console and run:
   console.log('API Base URL:', import.meta.env.VITE_API_URL || 'http://localhost:8000');
   ```

2. **Check if token exists:**
   ```javascript
   // In browser console:
   console.log('Token:', localStorage.getItem('token'));
   ```

3. **Test API directly:**
   ```javascript
   // In browser console:
   fetch('http://localhost:8000/api/health')
     .then(r => r.json())
     .then(console.log)
     .catch(console.error);
   ```

4. **Check CORS:**
   - Open Network tab
   - Look for OPTIONS request (preflight)
   - Check if it returns 200 OK

## Common Issues

### Issue: Backend not running
**Solution:** Start backend:
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn app.main:app --reload
```

### Issue: Wrong API URL
**Solution:** Create `frontend/.env` file:
```bash
VITE_API_URL=http://localhost:8000
```
Then restart the frontend dev server.

### Issue: CORS blocking
**Solution:** Check backend CORS config includes your frontend URL:
- Default: `http://localhost:5173`
- Check: `backend/app/core/config.py` - `CORS_ALLOWED_ORIGINS`

### Issue: Token expired or missing
**Solution:** Log out and log back in to get a new token.

