from django.db import models
from django.utils import timezone


class PublishedPostManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now()
        ).annotate(
            comment_count=models.Count('comments')
        ).order_by('-pub_date')
