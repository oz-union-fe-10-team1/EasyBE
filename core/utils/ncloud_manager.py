import logging  # 로깅을 위해 임포트
from datetime import datetime  # 타임스탬프 추가
from typing import IO, Optional

import boto3  # type: ignore[import-untyped]
from botocore.exceptions import NoCredentialsError  # type: ignore[import-untyped]
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile

logger = logging.getLogger(__name__)  # 로거 인스턴스 생성


# 파일업로드 공통 유틸 클래스, 프로젝트 내 여러 앱에서 재사용할 수 있도록 core에 정의
class S3Uploader:

    def __init__(self) -> None:  # 반환 타입 힌팅 유지
        # AWS 대신 NCP 설정 사용
        ncp_access_key_id = settings.NCLOUD_ACCESS_KEY_ID
        ncp_secret_access_key = settings.NCLOUD_SECRET_ACCESS_KEY
        ncp_region = settings.NCLOUD_REGION_NAME
        ncp_endpoint_url = settings.NCLOUD_ENDPOINT_URL  # NCP 엔드포인트 URL

        self.bucket = settings.NCLOUD_BUCKET_NAME
        self.client = boto3.client(
            "s3",
            aws_access_key_id=ncp_access_key_id,
            aws_secret_access_key=ncp_secret_access_key,
            region_name=ncp_region,
            endpoint_url=ncp_endpoint_url,
        )

    # 단일 파일 업로드 후 URL 반환. 실패 시 None 반환
    def upload_file(self, file_obj: UploadedFile, s3_key: str) -> Optional[str]:

        try:
            self.client.upload_fileobj(
                file_obj,
                self.bucket,
                s3_key,
                ExtraArgs={"ContentType": file_obj.content_type, "ACL": "public-read"},
            )
            # URL 생성 시 NCP 엔드포인트 사용
            return f"{settings.NCLOUD_ENDPOINT_URL}/{self.bucket}/{s3_key}"
        except NoCredentialsError:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S KST")
            logger.error(f"AWS 자격 증명이 설정되지 않았습니다. - {timestamp}")
            return None
        except Exception as e:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S KST")
            logger.error(f"S3/NCP 파일 업로드 실패: {e} - {timestamp}")
            return None

    def delete_file(self, s3_url: str) -> bool:
        """S3/NCP URL에서 파일 삭제"""
        try:
            # URL에서 S3 키 추출 (NCP URL 형식에 맞게 수정)
            base_url = f"{settings.NCLOUD_ENDPOINT_URL}/{self.bucket}/"
            if not s3_url.startswith(base_url):
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S KST")
                logger.warning(f"예상치 못한 S3 URL 형식: {s3_url} - {timestamp}")
                return False
            s3_key = s3_url.replace(base_url, "", 1)  # 한 번만 교체

            self.client.delete_object(Bucket=self.bucket, Key=s3_key)
            return True
        except Exception as e:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S KST")
            logger.error(f"S3/NCP delete_file failed: {e} - {timestamp}")
            return False

    # 기존 파일 위치에 새 파일을 덮어쓰고 동일 URL 반환. 실패 시 None 반환
    def update_file(self, file_obj: UploadedFile, s3_url: str) -> Optional[str]:
        try:
            # S3/NCP URL에서 Key 추출 (NCP URL 형식에 맞게 수정)
            base_url = f"{settings.NCLOUD_ENDPOINT_URL}/{self.bucket}/"
            if not s3_url.startswith(base_url):
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S KST")
                logger.warning(f"예상치 못한 S3 URL 형식: {s3_url} - {timestamp}")
                return None
            s3_key = s3_url.replace(base_url, "", 1)  # 한 번만 교체

            if not s3_key:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S KST")
                logger.warning(f"S3 키 추출 실패: {s3_url} - {timestamp}")
                return None

            # 기존 Key에 파일 덮어쓰기
            self.client.upload_fileobj(
                file_obj,
                self.bucket,
                s3_key,
                ExtraArgs={"ContentType": file_obj.content_type, "ACL": "public-read"},
            )
            return s3_url  # Key는 같으니 기존 URL 반환
        except Exception as e:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S KST")
            logger.error(f"S3/NCP update_file failed: {e} - {timestamp}")
            return None
