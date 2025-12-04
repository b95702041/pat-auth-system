# PAT Auth System 測試套件

完整的測試套件，用於驗證 Personal Access Token 認證系統的功能。

## 測試結構

```
tests/
├── conftest.py              # 測試配置和 fixtures
├── test_permissions.py      # 權限層級繼承測試
├── test_token_expiry.py     # Token 過期和撤銷測試
├── test_token_storage.py    # Token 安全儲存測試
├── test_token_regenerate.py # Token 重新產生測試
└── test_token_ip_whitelist.py # Token IP 白名單測試
```

## Fixtures 說明

### conftest.py 提供的 Fixtures

- `test_db`: 測試資料庫會話（SQLite）
- `test_client`: FastAPI 測試客戶端
- `test_user`: 建立測試使用者並回傳 JWT token
- `test_token`: 建立測試 PAT token
- `expired_token`: 建立已過期的 PAT token
- `revoked_token`: 建立已撤銷的 PAT token

## 執行測試

### 執行所有測試

```bash
pytest tests/ -v
```

### 執行特定測試檔案

```bash
# 權限測試
pytest tests/test_permissions.py -v

# Token 過期測試
pytest tests/test_token_expiry.py -v

# Token 儲存測試
pytest tests/test_token_storage.py -v
```

### 執行特定測試函式

```bash
pytest tests/test_permissions.py::test_workspaces_admin_includes_lower_permissions -v
```

### 顯示測試覆蓋率

```bash
pytest tests/ --cov=app --cov-report=html
```

## 測試說明

### 1. 權限層級繼承測試 (test_permissions.py)

驗證權限系統的層級結構：

- **test_workspaces_admin_includes_lower_permissions**: 
  - workspaces:admin 應包含 workspaces:read/write/delete
  - workspaces:admin 不應包含 fcs:read（不跨資源）

- **test_fcs_analyze_includes_lower_permissions**:
  - fcs:analyze 應包含 fcs:read/write
  - fcs:analyze 不應包含 workspaces:read（不跨資源）

- **test_permission_hierarchy_levels**:
  - 驗證每個權限級別的正確性

- **test_no_cross_resource_inheritance**:
  - 確保權限不跨資源繼承

### 2. Token 過期和撤銷測試 (test_token_expiry.py)

驗證 token 生命週期管理：

- **test_expired_token_returns_401**: 
  - 過期的 token 回傳 401 "Token expired"

- **test_revoked_token_returns_401**:
  - 撤銷的 token 回傳 401 "Token revoked"

- **test_error_messages_are_distinct**:
  - 過期和撤銷的錯誤訊息不同

- **test_valid_token_works**:
  - 有效 token 正常運作

- **test_token_lifecycle**:
  - 完整的 token 生命週期測試

### 3. Token 安全儲存測試 (test_token_storage.py)

驗證 token 儲存安全性：

- **test_token_not_stored_in_plaintext**:
  - 資料庫不儲存明文 token
  - 儲存 prefix（前12字元）
  - 儲存 SHA-256 hash

- **test_correct_token_authenticates**:
  - 正確的 token 能通過認證

- **test_wrong_token_with_same_prefix_fails**:
  - 相同 prefix 但錯誤的 token 無法認證

- **test_token_hash_is_deterministic**:
  - 相同 token 總是產生相同 hash

- **test_multiple_tokens_have_different_hashes**:
  - 不同 token 產生不同 hash

### 4. Token 重新產生測試 (test_token_regenerate.py)

驗證 token 重新產生功能：

- **test_regenerate_token_creates_new_token_string**:
  - 重新產生後獲得新的 token 字串
  - 舊 token 自動失效
  - 保持相同的 name 和 scopes

- **test_regenerate_token_with_extended_expiration**:
  - 可以延長過期時間
  - 新的過期時間正確計算

- **test_regenerate_token_without_expiration_keeps_original**:
  - 不指定過期時間時保持原有過期時間

- **test_cannot_regenerate_revoked_token**:
  - 已撤銷的 token 無法重新產生
  - 返回 400 錯誤

- **test_cannot_regenerate_other_users_token**:
  - 無法重新產生其他使用者的 token
  - 返回 404 錯誤

- **test_regenerate_resets_created_at**:
  - 重新產生後 created_at 更新為當前時間

### 5. Token IP 白名單測試 (test_token_ip_whitelist.py)

驗證 token IP 白名單功能：

- **test_create_token_with_ip_whitelist**:
  - 建立有 IP 限制的 token
  - 支援 IP 列表

- **test_create_token_without_ip_restriction**:
  - 建立無 IP 限制的 token（null）

- **test_token_with_matching_ip_works**:
  - 符合白名單 IP 的請求可以通過
  - localhost (127.0.0.1) 驗證

- **test_token_with_cidr_range_works**:
  - 支援 CIDR 範圍（如 127.0.0.0/8）
  - 範圍內的 IP 可以通過

- **test_update_token_ip_whitelist**:
  - 可以更新 token 的 IP 白名單
  - 更新後立即生效

- **test_remove_ip_restriction**:
  - 可以移除 IP 限制（設為 null）

- **test_remove_ip_restriction_with_empty_list**:
  - 空陣列等同於 null（無限制）

- **test_cannot_update_other_users_token_ips**:
  - 無法更新其他使用者的 token IP 白名單
  - 返回 404 錯誤

## 測試資料庫

測試使用獨立的 SQLite 資料庫 (`test.db`)，每個測試函式都會：
1. 建立乾淨的資料庫
2. 執行測試
3. 清理資料庫

這確保測試之間完全隔離。

## 相依套件

```
pytest==7.4.4
pytest-asyncio==0.23.3
httpx==0.26.0
```

## CI/CD 整合

可以在 CI/CD 流程中執行測試：

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: |
    pytest tests/ -v --cov=app --cov-report=xml
```

## 貢獻指南

新增測試時：
1. 在 `conftest.py` 中新增可重複使用的 fixtures
2. 在相應的測試檔案中新增測試案例
3. 確保測試有清楚的文件字串（docstring）
4. 執行所有測試確保沒有破壞現有功能

## 測試範例

### 執行單一測試並顯示詳細輸出

```bash
pytest tests/test_permissions.py::test_workspaces_admin_includes_lower_permissions -v -s
```

### 執行測試並在失敗時立即停止

```bash
pytest tests/ -v -x
```

### 僅執行標記為 slow 的測試（需要先加上標記）

```bash
pytest tests/ -v -m slow
```

## 測試最佳實踐

1. **每個測試應該獨立**：不依賴其他測試的執行結果
2. **使用有意義的測試名稱**：測試名稱應該清楚描述測試內容
3. **一個測試只測試一件事**：保持測試簡單和專注
4. **使用 fixtures 共用設定**：避免重複程式碼
5. **測試正常情況和異常情況**：包含成功和失敗的場景

## 疑難排解

### 測試資料庫鎖定問題

如果遇到 SQLite 資料庫鎖定，可以刪除測試資料庫：

```bash
rm test.db
pytest tests/ -v
```

### 測試失敗但本地執行成功

確認：
1. Python 版本一致
2. 相依套件版本一致
3. 環境變數設定正確

### 測試執行緩慢

可以平行執行測試（需要安裝 pytest-xdist）：

```bash
pip install pytest-xdist
pytest tests/ -v -n auto
```