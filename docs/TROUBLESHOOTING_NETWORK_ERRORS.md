# Troubleshooting Network Errors in Video Generation

## Issue: DNS Resolution Error

### Error Message
```
[Errno 8] nodename nor servname provided, or not known
```

### What This Means
This error indicates that your system cannot resolve the hostname when trying to connect to the Replicate API. This is a **network connectivity issue**, not a code bug.

### Common Causes
1. **Internet connectivity problems** - Your system may have lost internet connection
2. **DNS resolution issues** - DNS servers may be unreachable or misconfigured
3. **Firewall/proxy blocking** - Corporate firewalls or proxies may be blocking API requests
4. **VPN issues** - VPN connections can sometimes interfere with DNS resolution
5. **Temporary API outage** - The Replicate API may be temporarily unavailable

## Troubleshooting Steps

### 1. Check Internet Connectivity
```bash
# Test basic internet connectivity
ping -c 4 8.8.8.8

# Test DNS resolution
nslookup api.replicate.com

# Test HTTPS connectivity to Replicate
curl -I https://api.replicate.com
```

### 2. Check DNS Configuration
```bash
# Check your DNS servers
cat /etc/resolv.conf

# Try using Google DNS temporarily
# macOS:
sudo networksetup -setdnsservers Wi-Fi 8.8.8.8 8.8.4.4

# Linux:
# Edit /etc/resolv.conf or use systemd-resolved
```

### 3. Check Firewall/Proxy Settings
- If you're behind a corporate firewall, ensure `api.replicate.com` is whitelisted
- Check if a proxy is required and configure it if needed
- Verify that outbound HTTPS (port 443) is allowed

### 4. Test Replicate API Directly
```bash
# Test API connectivity (requires REPLICATE_API_TOKEN)
export REPLICATE_API_TOKEN="your-token-here"
python3 -c "
import replicate
client = replicate.Client(api_token='$REPLICATE_API_TOKEN')
print('API connection successful')
"
```

### 5. Check System Logs
```bash
# Check application logs for detailed error messages
tail -n 100 logs/app.log | grep -i "network\|dns\|error"
```

## Code Improvements Made

The video generation service has been updated with better error handling:

1. **Network Error Detection** - The code now specifically detects DNS/network errors
2. **Clearer Error Messages** - Error messages now provide actionable guidance
3. **Better Logging** - Network errors are logged with more context

### Example Improved Error Message
```
Network connectivity error: Unable to reach Replicate API. 
Error: [Errno 8] nodename nor servname provided, or not known. 
Please check your internet connection, DNS settings, and firewall configuration. 
If the issue persists, the Replicate API may be temporarily unavailable.
```

## Prevention

### Network Health Check (Future Enhancement)
Consider adding a network connectivity check before starting video generation:

```python
async def check_network_connectivity():
    """Check if Replicate API is reachable before starting generation."""
    import socket
    try:
        socket.gethostbyname('api.replicate.com')
        return True
    except socket.gaierror:
        return False
```

## When to Retry

- **Temporary network hiccup**: Wait 30-60 seconds and retry
- **DNS issues**: Fix DNS configuration and retry
- **Firewall blocking**: Contact network administrator
- **Persistent issues**: Check Replicate API status page

## Related Files
- `backend/app/services/pipeline/video_generation.py` - Video generation service with improved error handling
- `backend/app/api/routes/generations.py` - API route handlers

