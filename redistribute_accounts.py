#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import random

def redistribute_accounts():
    """Phân chia lại 38 tài khoản thành 3 nhóm: 15-15-8"""
    
    # Đọc file hiện tại
    with open('user_accounts.json', 'r', encoding='utf-8') as f:
        accounts = json.load(f)
    
    # Backup file gốc
    with open('user_accounts_backup.json', 'w', encoding='utf-8') as f:
        json.dump(accounts, f, ensure_ascii=False, indent=2)
    
    print(f"Tổng số tài khoản: {len(accounts)}")
    
    # Tạo danh sách index ngẫu nhiên
    indices = list(range(len(accounts)))
    random.shuffle(indices)
    
    # Phân chia theo yêu cầu
    group1_indices = indices[:15]  # 15 tài khoản cho 22773024 (A Hán)
    group2_indices = indices[15:30]  # 15 tài khoản cho 22615815 (C. Phượng)
    group3_indices = indices[30:38]  # 8 tài khoản cho 22614471 (Chị Liên)
    
    # Cập nhật trường "to"
    for i in group1_indices:
        accounts[i]["to"] = "22773024"
    
    for i in group2_indices:
        accounts[i]["to"] = "22615815"
    
    for i in group3_indices:
        accounts[i]["to"] = "22614471"
    
    # Lưu file đã cập nhật
    with open('user_accounts.json', 'w', encoding='utf-8') as f:
        json.dump(accounts, f, ensure_ascii=False, indent=2)
    
    # In kết quả
    groups = {"22773024": [], "22615815": [], "22614471": []}
    
    for account in accounts:
        to_value = account.get("to", "")
        if to_value in groups:
            groups[to_value].append(account["note"])
    
    print("\n=== PHÂN CHIA TÀI KHOẢN ===")
    print(f"Nhóm 22773024 (A Hán): {len(groups['22773024'])} tài khoản")
    for i, note in enumerate(groups["22773024"], 1):
        print(f"  {i:2d}. {note}")
    
    print(f"\nNhóm 22615815 (C. Phượng): {len(groups['22615815'])} tài khoản")
    for i, note in enumerate(groups["22615815"], 1):
        print(f"  {i:2d}. {note}")
    
    print(f"\nNhóm 22614471 (Chị Liên): {len(groups['22614471'])} tài khoản")
    for i, note in enumerate(groups["22614471"], 1):
        print(f"  {i:2d}. {note}")
    
    print(f"\nTổng cộng: {len(accounts)} tài khoản")
    print("✅ Phân chia hoàn tất!")

if __name__ == "__main__":
    redistribute_accounts()
