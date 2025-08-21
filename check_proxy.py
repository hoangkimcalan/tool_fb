#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

# Đọc file user_accounts.json
with open('user_accounts.json', 'r', encoding='utf-8') as f:
    accounts = json.load(f)

# Danh sách proxy mới từ nhà cung cấp
new_proxies = [
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

# Tìm các tài khoản có proxy
proxy_accounts = []
for account in accounts:
    if 'proxy_ip' in account:
        current_proxy = f"{account['proxy_ip']}:{account['proxy_port']}:{account['proxy_user']}:{account['proxy_pass']}"
        proxy_accounts.append({
            'note': account['note'],
            'current_proxy': current_proxy
        })

print('=== KIỂM TRA PROXY TRONG FILE ===')
print(f'Tổng số tài khoản có proxy: {len(proxy_accounts)}')
print()

for i, acc in enumerate(proxy_accounts, 1):
    print(f'{i}. {acc["note"]}: {acc["current_proxy"]}')

print()
print('=== PROXY MỚI TỪ NHÀ CUNG CẤP ===')
for i, proxy in enumerate(new_proxies, 1):
    print(f'{i}. {proxy}')

print()
print('=== SO SÁNH ===')
current_proxies = [acc['current_proxy'] for acc in proxy_accounts]

matched = 0
for i, new_proxy in enumerate(new_proxies, 1):
    if new_proxy in current_proxies:
        print(f'✅ Proxy {i}: KHỚP')
        matched += 1
    else:
        print(f'❌ Proxy {i}: KHÔNG KHỚP - {new_proxy}')

print(f'\nKết quả: {matched}/{len(new_proxies)} proxy khớp với file hiện tại')

# Test thử 1 proxy để xem có hoạt động không
print('\n=== TEST PROXY ĐẦU TIÊN ===')
import requests
import time

proxy_info = new_proxies[0].split(':')
proxy_ip = proxy_info[0]
proxy_port = proxy_info[1]
proxy_user = proxy_info[2]
proxy_pass = proxy_info[3]

proxies = {
    "http": f"http://{proxy_user}:{proxy_pass}@{proxy_ip}:{proxy_port}",
    "https": f"http://{proxy_user}:{proxy_pass}@{proxy_ip}:{proxy_port}"
}

try:
    print(f'Testing proxy: {proxy_ip}:{proxy_port}...')
    response = requests.get('http://httpbin.org/ip', proxies=proxies, timeout=10)
    if response.status_code == 200:
        result = response.json()
        print(f'✅ Proxy hoạt động! IP: {result.get("origin", "Unknown")}')
    else:
        print(f'❌ Proxy không hoạt động. Status: {response.status_code}')
except Exception as e:
    print(f'❌ Lỗi kết nối proxy: {e}')
