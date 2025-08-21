import requests
import time

def test_multiple_proxies():
    """Test multiple proxy servers to find working ones"""
    
    # Thêm các proxy khác để test
    proxies_to_test = [
        {
            "ip": "42.118.161.235",
            "port": "19869", 
            "user": "muaproxy689ef8202bc87",
            "pass": "lyl1nqbxq4ghgpyu",
            "name": "Proxy cũ"
        },
        # Thêm proxy mới vào đây nếu có
        # {
        #     "ip": "NEW_IP",
        #     "port": "NEW_PORT",
        #     "user": "NEW_USER", 
        #     "pass": "NEW_PASS",
        #     "name": "Proxy mới"
        # }
    ]
    
    working_proxies = []
    
    for proxy_info in proxies_to_test:
        print(f"\n🔍 Testing {proxy_info['name']}: {proxy_info['ip']}:{proxy_info['port']}")
        
        # Test without authentication first
        result1 = test_proxy_simple(proxy_info['ip'], proxy_info['port'])
        
        # Test with authentication  
        result2 = test_proxy_auth(proxy_info['ip'], proxy_info['port'], 
                                 proxy_info['user'], proxy_info['pass'])
        
        if result1['status'] == 'Active' or result2['status'] == 'Active':
            working_proxies.append(proxy_info)
            print(f"✅ {proxy_info['name']} WORKS!")
        else:
            print(f"❌ {proxy_info['name']} FAILED")
    
    return working_proxies

def test_proxy_simple(ip, port):
    """Test proxy without authentication"""
    proxies = {
        "http": f"http://{ip}:{port}",
        "https": f"http://{ip}:{port}"
    }
    
    try:
        response = requests.get("http://httpbin.org/ip", proxies=proxies, timeout=10)
        if response.status_code == 200:
            return {"status": "Active", "method": "No Auth"}
    except:
        pass
    
    return {"status": "Inactive"}

def test_proxy_auth(ip, port, user, password):
    """Test proxy with authentication"""
    proxies = {
        "http": f"http://{user}:{password}@{ip}:{port}",
        "https": f"http://{user}:{password}@{ip}:{port}"
    }
    
    try:
        response = requests.get("http://httpbin.org/ip", proxies=proxies, timeout=10)
        if response.status_code == 200:
            return {"status": "Active", "method": "With Auth"}
    except:
        pass
    
    return {"status": "Inactive"}

def test_direct_connection():
    """Test direct connection without proxy"""
    print("\n🌐 Testing direct connection...")
    try:
        response = requests.get("http://httpbin.org/ip", timeout=10)
        if response.status_code == 200:
            print("✅ Direct connection works!")
            print(f"Your IP: {response.json()['origin']}")
            return True
    except Exception as e:
        print(f"❌ Direct connection failed: {e}")
    return False

if __name__ == "__main__":
    print("🚀 Starting proxy testing...")
    
    # Test direct connection first
    direct_works = test_direct_connection()
    
    # Test proxies
    working = test_multiple_proxies()
    
    print("\n" + "="*50)
    print("📋 SUMMARY:")
    print(f"Direct connection: {'✅ OK' if direct_works else '❌ FAILED'}")
    print(f"Working proxies: {len(working)}")
    
    if working:
        print("\n🎉 Working proxies found:")
        for proxy in working:
            print(f"  - {proxy['name']}: {proxy['ip']}:{proxy['port']}")
    else:
        print("\n⚠️  No working proxies found!")
        if direct_works:
            print("💡 Suggestion: Use direct connection or get new proxy")
        else:
            print("💡 Suggestion: Check internet connection")
