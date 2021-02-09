from flask import make_response

# begin 1)
# this should disable page caching
# (but for all pages)
# got it from: https://flask.palletsprojects.com/en/1.1.x/config/#SEND_FILE_MAX_AGE_DEFAULT
#app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
# end 1)

# begin 2)
# another way to disable page caching
# (but for all too)
# got from: https://blog.sneawo.com/blog/2017/12/20/no-cache-headers-in-flask/
#@app.after_request
#def set_response_headers(response):
#    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
#    response.headers['Pragma'] = 'no-cache'
#    response.headers['Expires'] = '0'
#    return response
# end 2)

# begin 3)
# a third (not really flasky) way to disable page caching
# (but for all too)
# got from: https://gist.github.com/arusahni/9434953 (arusahni/nocache.py)
from functools import wraps, update_wrapper
from datetime import datetime

def nocache(view):
    @wraps(view)
    def no_cache(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers['Last-Modified'] = datetime.now()
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response

    return update_wrapper(no_cache, view)
# end 3)

