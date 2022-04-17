import json
import requests
'''
A test program to send a post request to our product server. This is used to test the create function.

Steps:
1. Use command 'flask run' to start the server.
2. Run this program.
3. Now a new product will be created and store in database.
4. You can run this program multiple times to create more than one product.
5. Access "http://127.0.0.1:8000/products" in your browser to see the result.

'''

url = "http://127.0.0.1:8000/products"
data = json.dumps({'name':'iPhone13 Pro Max', 'category':'Phone', 'description':'post test', 'price':1099, 'stock':5})
headers = {'content-type': 'application/json'}
resp = requests.post(url, data=data, headers=headers)
print(resp.text)