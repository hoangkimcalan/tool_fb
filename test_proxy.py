import requests
import time

def check_proxy(proxy_address: str, username: str = None, password: str = None):
    """
    Checks a proxy for its operational status, HTTPS support, and connection speed.
    This version supports proxies with a username and password.

    Args:
        proxy_address: Proxy address as a string 'ip:port'.
        username: (Optional) The username for proxy authentication.
        password: (Optional) The password for proxy authentication.

    Returns:
        A dictionary containing the test results.
    """
    results = {
        "status": "Inactive",
        "supports_https": False,
        "http_speed_ms": None,
        "https_speed_ms": None
    }
    
    # --- 1. Prepare proxies dictionary with authentication ---
    if username and password:
        auth_string = f"{username}:{password}@"
    else:
        auth_string = ""
    
    proxies = {
        "http": f"http://{auth_string}{proxy_address}",
        "https": f"http://{auth_string}{proxy_address}"
    }

    test_url_http = "http://httpbin.org/ip"
    test_url_https = "https://www.google.com"

    # --- 2. Check operational status and HTTP speed ---
    print(f"Checking proxy: {proxy_address}...")
    try:
        start_time = time.time()
        response = requests.get(test_url_http, proxies=proxies, timeout=10)
        end_time = time.time()
        
        if response.status_code == 200:
            results["status"] = "Active"
            results["http_speed_ms"] = round((end_time - start_time) * 1000, 2)
            print(f"  ✅ Proxy is active. HTTP speed: {results['http_speed_ms']} ms")
        else:
            print(f"  ❌ HTTP error: Status code {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"  ❌ HTTP connection error: {e}")
        return results

    # --- 3. Check HTTPS support and speed ---
    if results["status"] == "Active":
        try:
            start_time = time.time()
            response = requests.get(test_url_https, proxies=proxies, timeout=10)
            end_time = time.time()
            
            if response.status_code == 200:
                results["supports_https"] = True
                results["https_speed_ms"] = round((end_time - start_time) * 1000, 2)
                print(f"  ✅ HTTPS is supported. HTTPS speed: {results['https_speed_ms']} ms")
            else:
                print(f"  ❌ HTTPS is not supported. Status code {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"  ❌ HTTPS connection error: {e}")
            
    return results

# --- How to use the function ---
# Replace with your proxy information
proxy_ip = "116.97.15.251"
proxy_port = "22170"
proxy_user = "muaproxy689ef889877d0"
proxy_pass = "omglrlc5194ghtuy"

proxy_to_check = f"{proxy_ip}:{proxy_port}"

# Call the function with username and password
check_result = check_proxy(proxy_to_check, username=proxy_user, password=proxy_pass)
print("\nFinal Result:")
print(check_result)