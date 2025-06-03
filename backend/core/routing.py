from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/visa/status/$', consumers.VisaApplicationConsumer.as_asgi()),
]