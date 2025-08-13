# apps/users/utils/signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


@receiver(post_save, sender='feedback.Feedback')
def update_taste_profile_on_review_create(sender, instance, created, **kwargs):
    """
    리뷰 생성 시 사용자 취향 프로필 업데이트
    📍 User 도메인에서 모든 취향 계산 로직 처리
    """
    if created and instance.product.drink:
        if hasattr(instance.user, 'taste_profile'):
            # 복잡한 취향 학습 로직은 모두 User 도메인에서 처리
            instance.user.taste_profile.update_from_detailed_review(instance)


@receiver(post_delete, sender='feedback.Feedback')
def update_taste_profile_on_review_delete(sender, instance, **kwargs):
    """
    리뷰 삭제 시 사용자 취향 프로필 재계산
    📍 삭제된 리뷰를 제외하고 취향 프로필 재계산
    """
    if instance.product.drink:
        if hasattr(instance.user, 'taste_profile'):
            # 해당 사용자의 모든 리뷰를 기반으로 취향 프로필 재계산
            instance.user.taste_profile.recalculate_from_all_reviews()