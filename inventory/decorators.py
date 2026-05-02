import time
from functools import wraps
from django.core.cache import cache
from django.shortcuts import render

def rate_limit(requests=5, window=60):
    """
    Limits views to `requests` hits per `window` seconds per IP address.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            ip = request.META.get('REMOTE_ADDR')
            # Handle reverse proxies (like Render's load balancer)
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0].strip()
            
            cache_key = f"rate_limit_{ip}_{view_func.__name__}"
            
            history = cache.get(cache_key, [])
            now = time.time()
            
            # Filter history to only include hits within the rolling window
            history = [ts for ts in history if now - ts < window]
            
            if len(history) >= requests:
                return render(request, '429.html', status=429)
                
            history.append(now)
            cache.set(cache_key, history, timeout=window)
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
