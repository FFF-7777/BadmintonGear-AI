"""API 层测试：验证核心端点的响应、认证与错误处理。"""
import os
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")

from utils.security import create_access_token


class TestHealth:
    def test_health_returns_ok_or_degraded(self, client):
        res = client.get("/api/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] in ("ok", "degraded")
        assert "database" in data

    def test_root(self, client):
        res = client.get("/")
        assert res.status_code == 200
        assert "羽智选" in res.json()["message"]


class TestPublicEndpoints:
    def test_category_list_has_four_categories(self, client):
        res = client.get("/api/category/list")
        assert res.status_code == 200
        data = res.json()
        assert data["code"] == 200
        assert len(data["data"]) >= 4

    def test_product_list_returns_page(self, client):
        res = client.get("/api/product/list", params={"page": 1, "page_size": 10})
        assert res.status_code == 200
        data = res.json()
        assert data["code"] == 200
        assert "list" in data["data"]
        assert "total" in data["data"]

    def test_product_detail_not_found(self, client):
        res = client.get("/api/product/detail/999999")
        assert res.json()["code"] == 404


class TestAuth:
    def test_admin_login_wrong_password(self, client):
        res = client.post("/api/auth/admin/login", json={"username": "admin", "password": "wrong"})
        assert res.json()["code"] == 401

    def test_admin_login_success(self, client):
        res = client.post("/api/auth/admin/login", json={"username": "admin", "password": "admin"})
        assert res.json()["code"] == 200
        assert "token" in res.json()["data"]

    def test_admin_endpoints_require_token(self, client):
        """未认证访问 admin 接口应返回 401/403。"""
        res = client.get("/api/knowledge/admin/list")
        assert res.status_code in (401, 403)

    def test_admin_endpoints_with_valid_token(self, client):
        token = create_access_token({"sub": "1", "type": "admin"})
        res = client.get(
            "/api/knowledge/admin/list",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        assert res.json()["code"] == 200

    def test_user_register_and_login(self, client):
        username = "testuser_api"
        # 注册
        res = client.post("/api/auth/user/register", json={
            "username": username,
            "password": "testpass123",
            "nickname": "测试用户",
        })
        assert res.json()["code"] == 200
        # 登录
        res = client.post("/api/auth/user/login", json={
            "username": username,
            "password": "testpass123",
        })
        assert res.json()["code"] == 200
        assert "token" in res.json()["data"]
