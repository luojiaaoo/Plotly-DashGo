from common.exception import OAuth2Error
from flask import request

authorize_html = """
<p>The application <strong>{{client_id}}</strong> is requesting:
<strong>{{ scope }}</strong>
</p>

<p>
  from You - a.k.a. <strong>{{ user_name }}</strong>
</p>

<form action="" method="post">
  <label>
    <input type="checkbox" name="confirm">
    <span>Consent?</span>
  </label>
  <br>
  <button>Submit</button>
</form>
"""

def require_oauth(required_scope):
    from functools import wraps

    def wrapper(func):
        @wraps(func)
        def decorator(*args, **kwargs):
            token = current_token()
            if not token:
                raise OAuth2Error('Invalid access token', 401)
            if not token.is_valid():
                raise OAuth2Error('Token expired', 401)
            if required_scope not in token.scope.split():
                raise OAuth2Error('Invalid scope', 401)
            func(*args, **kwargs)

        return decorator

    return wrapper


def current_token():
    from database.sql_db.dao.dao_oauth2 import exist_token

    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        raise OAuth2Error('Invalid token', 401)
    return exist_token(auth_header.split(' ')[-1])