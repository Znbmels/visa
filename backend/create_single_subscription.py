#!/usr/bin/env python
import os
import sys
import django

# Настройка Django
sys.path.append(os.path.join(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'visa.settings')
django.setup()

from core.models import Subscription

# Удаляем все существующие планы подписки
Subscription.objects.all().delete()

# Создаем только один план подписки
subscription = Subscription.objects.create(
    name='Премиум подписка',
    description='Доступ к анализу вероятности получения визы и рекомендациям по дополнительным документам',
    price=19.99,
    duration_days=30,
    is_active=True
)

print('Создан единственный план подписки:')
print(f'- {subscription.name}: ${subscription.price} на {subscription.duration_days} дней')
print(f'- Описание: {subscription.description}') 