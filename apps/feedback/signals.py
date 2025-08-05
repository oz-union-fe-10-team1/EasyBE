from django.db.models import Avg, F
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.products.models import Product

from .models import Feedback


def update_product_rating(product_id):
    """
    특정 상품의 평균 평점과 리뷰 개수를 다시 계산하고 업데이트합니다.
    """
    # 해당 상품에 대한 모든 피드백의 'overall_rating' 필드의 평균을 계산
    # 피드백이 하나도 없으면 0을 기본값으로 사용
    average = (
        Feedback.objects.filter(order_item__product_id=product_id).aggregate(avg=Avg("overall_rating"))["avg"] or 0
    )

    review_count = Feedback.objects.filter(order_item__product_id=product_id).count()

    Product.objects.filter(id=product_id).update(average_rating=average, review_count=review_count)


@receiver(post_save, sender=Feedback)
def feedback_saved(sender, instance, created, **kwargs):
    """
    피드백이 생성되거나 업데이트된 후 호출됩니다.
    """
    # 'instance'는 방금 저장된 Feedback 객체입니다.
    product_id = instance.order_item.product.id
    update_product_rating(product_id)


@receiver(post_delete, sender=Feedback)
def feedback_deleted(sender, instance, **kwargs):
    """
    피드백이 삭제된 후 호출됩니다.
    """
    product_id = instance.order_item.product.id
    update_product_rating(product_id)
