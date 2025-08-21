#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

def test_single_proxy(proxy_info, index):
    """Test một proxy đơn lẻ"""
    proxy_data = proxy_info.split(':')
    proxy_ip = proxy_data[0]
    proxy_port = proxy_data[1]
    proxy_user = proxy_data[2]
    proxy_pass = proxy_data[3]
    
    proxies = {
        "http": f"http://{proxy_user}:{proxy_pass}@{proxy_ip}:{proxy_port}",
        "https": f"http://{proxy_user}:{proxy_pass}@{proxy_ip}:{proxy_port}"
    }
    
    result = {
        "index": index,
        "proxy": f"{proxy_ip}:{proxy_port}",
        "status": "❌ FAILED",
        "response_time": None,
        "ip_address": None,
        "error": None
    }
    
    try:
        print(f"[{index}] Testing {proxy_ip}:{proxy_port}...")
        
        # Test HTTP
        start_time = time.time()
        response = requests.get('http://httpbin.org/ip', proxies=proxies, timeout=15)
        end_time = time.time()
        
        if response.status_code == 200:
            response_data = response.json()
            result["status"] = "✅ SUCCESS"
            result["response_time"] = round((end_time - start_time) * 1000, 2)
            result["ip_address"] = response_data.get("origin", "Unknown")
            print(f"[{index}] ✅ Success - IP: {result['ip_address']}, Time: {result['response_time']}ms")
        else:
            result["error"] = f"HTTP Status: {response.status_code}"
            print(f"[{index}] ❌ Failed - Status: {response.status_code}")
            
    except requests.exceptions.Timeout:
        result["error"] = "Connection timeout (>15s)"
        print(f"[{index}] ❌ Failed - Timeout")
    except requests.exceptions.ProxyError as e:
        result["error"] = f"Proxy error: {str(e)[:100]}..."
        print(f"[{index}] ❌ Failed - Proxy error")
    except requests.exceptions.ConnectionError as e:
        result["error"] = f"Connection error: {str(e)[:100]}..."
        print(f"[{index}] ❌ Failed - Connection error")
    except Exception as e:
        result["error"] = f"Unknown error: {str(e)[:100]}..."
        print(f"[{index}] ❌ Failed - {str(e)[:50]}...")
    
    return result

def test_all_proxies():
    """Test tất cả proxy"""
    
    # Danh sách 9 proxy từ nhà cung cấp
    proxies = [
        '42.118.161.103:35270:muaproxy689ef8202bc87:lyl1nqbxq4ghgpyu',
        '1.55.143.33:27434:muaproxy689ef8202bc87:lyl1nqbxq4ghgpyu',
        '42.118.161.76:13016:muaproxy689ef8202bc87:lyl1nqbxq4ghgpyu',
        '1.54.225.88:19869:muaproxy689ef8202bc87:lyl1nqbxq4ghgpyu',
        '42.114.0.110:21556:muaproxy689ef8202bc87:lyl1nqbxq4ghgpyu',
        '1.55.143.0:24617:muaproxy689ef8202bc87:lyl1nqbxq4ghgpyu',
        '1.55.143.146:33185:muaproxy689ef8202bc87:lyl1nqbxq4ghgpyu',
        '42.118.161.99:27434:muaproxy689ef8202bc87:lyl1nqbxq4ghgpyu',
        '42.116.47.23:13502:muaproxy689ef8202bc87:lyl1nqbxq4ghgpyu'
    ]
    
    # Tên tài khoản tương ứng
    account_names = [
        'Chị Nhạn', 'Hoàng Linh', 'Ngọc Hà', 'Ngô Dung', 'A Hán',
        'Hải Yến', 'C. Phượng', 'Lưu Thị Thư', 'Bích Ngọc'
    ]
    
    print("=" * 60)
    print("🔍 TESTING ALL 9 PROXIES")
    print("=" * 60)
    print(f"⏰ Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Total proxies to test: {len(proxies)}")
    print("=" * 60)
    
    # Test song song để nhanh hơn
    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        # Submit all tasks
        future_to_index = {
            executor.submit(test_single_proxy, proxy, i+1): i 
            for i, proxy in enumerate(proxies)
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_index):
            result = future.result()
            results.append(result)
    
    # Sort results by index
    results.sort(key=lambda x: x['index'])
    
    # Print detailed results
    print("\n" + "=" * 80)
    print("📋 DETAILED TEST RESULTS")
    print("=" * 80)
    
    success_count = 0
    total_time = 0
    
    for i, result in enumerate(results):
        account_name = account_names[i]
        print(f"\n[{result['index']}] {account_name}")
        print(f"    🌐 Proxy: {result['proxy']}")
        print(f"    📊 Status: {result['status']}")
        
        if result['status'] == "✅ SUCCESS":
            success_count += 1
            total_time += result['response_time']
            print(f"    🎯 IP Address: {result['ip_address']}")
            print(f"    ⚡ Response Time: {result['response_time']}ms")
        else:
            print(f"    ❌ Error: {result['error']}")
    
    # Summary
    print("\n" + "=" * 80)
    print("📈 SUMMARY")
    print("=" * 80)
    print(f"✅ Working proxies: {success_count}/{len(proxies)}")
    print(f"❌ Failed proxies: {len(proxies) - success_count}/{len(proxies)}")
    print(f"📊 Success rate: {(success_count/len(proxies)*100):.1f}%")
    
    if success_count > 0:
        avg_time = total_time / success_count
        print(f"⚡ Average response time: {avg_time:.2f}ms")
    
    print(f"⏰ Test completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Save results to file
    with open('proxy_test_results.json', 'w', encoding='utf-8') as f:
        json.dump({
            'test_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_proxies': len(proxies),
            'working_proxies': success_count,
            'success_rate': round(success_count/len(proxies)*100, 1),
            'results': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Results saved to: proxy_test_results.json")
    
    return results

if __name__ == "__main__":
    test_all_proxies()
