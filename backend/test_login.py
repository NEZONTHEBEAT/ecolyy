import requests
import json

def test_login():
    url = "http://localhost:8000/api/v1/auth/login"
    
    # Partner Login
    print("=" * 50)
    print("Testing Partner Login")
    print("=" * 50)
    
    partner_data = {
        "email": "himanshu.b.11231@gmail.com",
        "password": "partner123",
        "role": "partner"
    }
    
    try:
        response = requests.post(url, json=partner_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Partner Login Successful!")
            print(f"   Name: {data['user']['name']}")
            print(f"   Role: {data['role']}")  # Fixed
            print(f"   Redirect: {data['user']['redirect_url']}")
            print(f"   Token: {data['access_token'][:50]}...")
        else:
            print(f"Partner Login Failed: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 50)
    print("Testing Institute Login")
    print("=" * 50)
    
    institute_data = {
        "email": "shamik.b.1123@inspiria.edu.in",
        "password": "institute123",
        "role": "institution"
    }
    
    try:
        response = requests.post(url, json=institute_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Institute Login Successful!")
            print(f"   Name: {data['user']['name']}")
            print(f"   Role: {data['role']}")  # Fixed
            print(f"   Redirect: {data['user']['redirect_url']}")
            print(f"   Token: {data['access_token'][:50]}...")
        else:
            print(f"Institute Login Failed: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_login()
