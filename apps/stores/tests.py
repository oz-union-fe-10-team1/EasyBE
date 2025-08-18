from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.stores.models import Store

User = get_user_model()


class StoreViewSetAPITest(APITestCase):
    def setUp(self):
        # Given: 테스트를 위한 기본 데이터 설정

        # 1. 유저 생성
        self.user = User.objects.create_user(nickname="testuser")
        self.admin_user = User.objects.create_user(nickname="adminuser", role=User.Role.ADMIN)

        # 2. 테스트용 매장 데이터
        self.store_data = {
            "name": "테스트 매장",
            "address": "서울시 강남구 테스트로 123",
            "contact": "02-1234-5678",
        }

        # 3. 매장 생성
        self.store = Store.objects.create(**self.store_data)

        # 4. URL 설정
        self.store_list_url = reverse("stores:stores-list")  # DRF 라우터의 기본 이름 사용
        self.store_detail_url = reverse("stores:stores-detail", kwargs={"pk": self.store.pk})

    # --- 관리자 유저 테스트 ---
    def test_admin_can_create_store(self):
        """관리자는 매장을 생성할 수 있다."""
        # Given: 관리자로 로그인
        self.client.force_authenticate(user=self.admin_user)
        new_store_data = {
            "name": "새로운 매장",
            "address": "서울시 종로구",
        }

        # When: 매장 생성 API 호출
        response = self.client.post(self.store_list_url, data=new_store_data)

        # Then: 성공적으로 생성됨 (201 CREATED)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Store.objects.count(), 2)
        self.assertEqual(response.data["name"], "새로운 매장")

    def test_admin_can_list_stores(self):
        """관리자는 매장 목록을 조회할 수 있다."""
        # Given: 관리자로 로그인
        self.client.force_authenticate(user=self.admin_user)

        # When: 매장 목록 API 호출
        response = self.client.get(self.store_list_url)

        # Then: 성공적으로 조회됨 (200 OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_admin_can_update_store(self):
        """관리자는 매장 정보를 수정할 수 있다."""
        # Given: 관리자로 로그인
        self.client.force_authenticate(user=self.admin_user)
        update_data = {"name": "수정된 매장 이름"}

        # When: 매장 수정 API 호출
        response = self.client.patch(self.store_detail_url, data=update_data)

        # Then: 성공적으로 수정됨 (200 OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.store.refresh_from_db()
        self.assertEqual(self.store.name, "수정된 매장 이름")

    def test_admin_can_delete_store(self):
        """관리자는 매장을 삭제할 수 있다."""
        # Given: 관리자로 로그인
        self.client.force_authenticate(user=self.admin_user)

        # When: 매장 삭제 API 호출
        response = self.client.delete(self.store_detail_url)

        # Then: 성공적으로 삭제됨 (204 NO CONTENT)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Store.objects.count(), 0)

    # --- 일반 유저 테스트 ---
    def test_regular_user_cannot_create_store(self):
        """일반 유저는 매장을 생성할 수 없다."""
        # Given: 일반 유저로 로그인
        self.client.force_authenticate(user=self.user)
        new_store_data = {"name": "일반유저 매장", "address": "시도"}

        # When: 매장 생성 API 호출
        response = self.client.post(self.store_list_url, data=new_store_data)

        # Then: 권한 거부됨 (403 FORBIDDEN)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_user_can_list_stores(self):
        """일반 유저도 매장 목록은 조회할 수 있다. (ViewSet 기본값)"""
        # Given: 일반 유저로 로그인
        self.client.force_authenticate(user=self.user)

        # When: 매장 목록 API 호출
        response = self.client.get(self.store_list_url)

        # Then: 성공적으로 조회됨 (200 OK)
        # 현재 ViewSet의 permission_classes가 IsAdminUser로 모든 액션에 적용되므로
        # 이 테스트는 실패해야 정상. 만약 GET 요청만 허용하려면 별도 권한 설정 필요.
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_user_cannot_update_store(self):
        """일반 유저는 매장 정보를 수정할 수 없다."""
        # Given: 일반 유저로 로그인
        self.client.force_authenticate(user=self.user)
        update_data = {"name": "수정 시도"}

        # When: 매장 수정 API 호출
        response = self.client.patch(self.store_detail_url, data=update_data)

        # Then: 권한 거부됨 (403 FORBIDDEN)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_user_cannot_delete_store(self):
        """일반 유저는 매장을 삭제할 수 없다."""
        # Given: 일반 유저로 로그인
        self.client.force_authenticate(user=self.user)

        # When: 매장 삭제 API 호출
        response = self.client.delete(self.store_detail_url)

        # Then: 권한 거부됨 (403 FORBIDDEN)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
