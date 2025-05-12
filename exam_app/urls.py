from django.urls import path
from .views import home, webcam, admin_login, admin_dashboard,video_stream
from .views import send_warning,stream_warnings
urlpatterns = [
    path('', home, name='home'),
    path('webcam/', webcam, name='webcam'),
    path('admin_login/', admin_login, name='admin_login'),
    path('admin_dashboard/', admin_dashboard, name='admin_dashboard'),
    path('video_stream/',video_stream,name='video_stream'),
    # path('run_cv/', run_cv, name='run_cv'),
    
    path('send_warning/', send_warning, name='send_warning'),
    path('stream_warnings/<str:usn>/', stream_warnings, name='stream_warnings'),
]
