import jwt
a = jwt.encode({'a':'a'}, 'aaaaa', algorithm='HS256')
print(a)