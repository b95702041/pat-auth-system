# 常用命令速查表

## 🚀 啟動與停止

```bash
# 啟動所有服務
docker-compose up -d

# 停止所有服務
docker-compose down

# 重啟服務
docker-compose restart

# 停止並刪除資料
docker-compose down -v
```

## 📋 查看狀態

```bash
# 查看服務狀態
docker-compose ps

# 查看 API 日誌
docker-compose logs -f api

# 查看資料庫日誌
docker-compose logs -f db

# 查看所有日誌
docker-compose logs -f
```

## 🗄️ 資料庫操作

```bash
# 執行 migration
docker-compose exec api alembic upgrade head

# 查看當前版本
docker-compose exec api alembic current

# 查看 migration 歷史
docker-compose exec api alembic history

# 進入資料庫
docker-compose exec db psql -U pat_user -d pat_db

# 資料庫常用 SQL
\dt                    # 列出所有資料表
\d users              # 查看 users 表結構
SELECT * FROM users;  # 查詢使用者
\q                    # 退出
```

## 🧪 測試

```bash
# 執行所有測試
docker-compose exec api pytest tests/ -v

# 執行特定測試
docker-compose exec api pytest tests/test_permissions.py -v

# 執行單一測試函數
docker-compose exec api pytest tests/test_permissions.py::test_permission_hierarchy_inheritance -v

# 查看測試覆蓋率
docker-compose exec api pytest tests/ --cov=app

# 生成 HTML 覆蓋率報告
docker-compose exec api pytest tests/ --cov=app --cov-report=html
```

## 🔧 開發

```bash
# 進入 API 容器
docker-compose exec api /bin/bash

# 進入資料庫容器
docker-compose exec db /bin/bash

# 安裝新的 Python 套件
docker-compose exec api pip install package_name
docker-compose exec api pip freeze > requirements.txt

# 重建映像檔
docker-compose build --no-cache api
```

## 📝 API 測試命令

### 1. 註冊使用者

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "password123"}'
```

### 2. 登入

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "password123"}'
```

### 3. 建立 PAT (需先登入取得 JWT)

```bash
JWT="your_jwt_token_here"

curl -X POST http://localhost:8000/api/v1/tokens \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Token",
    "scopes": ["fcs:analyze"],
    "expires_in_days": 90
  }'
```

### 4. 使用 PAT 存取資源

```bash
PAT="pat_your_token_here"

# FCS 參數
curl -X GET http://localhost:8000/api/v1/fcs/parameters \
  -H "Authorization: Bearer $PAT"

# FCS 事件
curl -X GET "http://localhost:8000/api/v1/fcs/events?limit=10&offset=0" \
  -H "Authorization: Bearer $PAT"

# FCS 統計
curl -X GET http://localhost:8000/api/v1/fcs/statistics \
  -H "Authorization: Bearer $PAT"
```

### 5. 列出所有 Token

```bash
curl -X GET http://localhost:8000/api/v1/tokens \
  -H "Authorization: Bearer $JWT"
```

### 6. 查看 Token 日誌

```bash
TOKEN_ID="your_token_id"

curl -X GET http://localhost:8000/api/v1/tokens/$TOKEN_ID/logs \
  -H "Authorization: Bearer $JWT"
```

### 7. 撤銷 Token

```bash
curl -X DELETE http://localhost:8000/api/v1/tokens/$TOKEN_ID \
  -H "Authorization: Bearer $JWT"
```

## 🔍 除錯命令

```bash
# 檢查 API 容器內的檔案
docker-compose exec api ls -la /app

# 檢查 FCS 檔案
docker-compose exec api ls -la /app/data

# 檢查 Python 套件
docker-compose exec api pip list

# 測試資料庫連接
docker-compose exec api python -c "from app.database import engine; print(engine.url)"

# 查看環境變數
docker-compose exec api env | grep DATABASE
```

## 📦 備份與還原

```bash
# 備份資料庫
docker-compose exec db pg_dump -U pat_user pat_db > backup.sql

# 還原資料庫
docker-compose exec -T db psql -U pat_user pat_db < backup.sql

# 備份上傳的檔案
tar -czf uploads_backup.tar.gz data/uploads/
```

## 🧹 清理

```bash
# 清理未使用的 Docker 映像
docker image prune -a

# 清理未使用的卷
docker volume prune

# 清理所有未使用的資源
docker system prune -a --volumes
```

## 📊 監控

```bash
# 查看容器資源使用
docker stats

# 查看特定容器資源使用
docker stats pat_api pat_postgres

# 查看容器日誌最後 100 行
docker-compose logs --tail=100 api
```

## 🎯 快捷鍵 (使用 Makefile)

```bash
make help       # 查看所有命令
make up         # 啟動服務
make down       # 停止服務
make logs       # 查看日誌
make test       # 執行測試
make shell      # 進入容器
make migrate    # 執行 migration
make clean      # 清理所有資源
```

## 🌐 API 端點速查

- **API 文件**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **健康檢查**: http://localhost:8000/health
- **根端點**: http://localhost:8000/

## 💡 小技巧

### 自動取得 JWT Token

```bash
# 儲存 JWT 到檔案
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "password123"}' \
  | jq -r '.data.access_token' > jwt.txt

# 使用儲存的 JWT
curl -X GET http://localhost:8000/api/v1/tokens \
  -H "Authorization: Bearer $(cat jwt.txt)"
```

### 一鍵建立並使用 PAT

```bash
# 建立 PAT 並儲存
curl -s -X POST http://localhost:8000/api/v1/tokens \
  -H "Authorization: Bearer $(cat jwt.txt)" \
  -H "Content-Type: application/json" \
  -d '{"name": "Quick Token", "scopes": ["fcs:read"], "expires_in_days": 30}' \
  | jq -r '.data.token' > pat.txt

# 使用 PAT
curl -X GET http://localhost:8000/api/v1/fcs/parameters \
  -H "Authorization: Bearer $(cat pat.txt)"
```

### 美化 JSON 輸出

```bash
# 使用 jq 美化
curl -s http://localhost:8000/api/v1/fcs/parameters \
  -H "Authorization: Bearer $(cat pat.txt)" | jq '.'

# 只顯示特定欄位
curl -s http://localhost:8000/api/v1/fcs/parameters \
  -H "Authorization: Bearer $(cat pat.txt)" | jq '.data.total_events'
```

---

**記住**: 所有這些命令都假設您在專案根目錄執行！
