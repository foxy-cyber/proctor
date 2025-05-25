from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import Student, Administrator,User
# from exam_app.cv.Code.updated_cv import first_function

def home(request):
    return render(request, 'home.html')

def webcam(request):
    if request.method == 'POST':
        usn = request.POST.get('usn')
        if Student.objects.filter(usn=usn).exists():
            return render(request, 'webcam.html',{'usn': usn})
        else:
            return render(request, 'home.html', {'error': 'Invalid USN'})
    return render(request, 'home.html')

def admin_login(request):
    if request.method == 'POST':
        admin_id = request.POST.get('admin_id')
        password = request.POST.get('password')
        try:
            admin = Administrator.objects.get(admin_id=admin_id)
            if admin.user.password==password:
                return redirect('admin_dashboard')
            else:
                return render(request, 'admin_login.html', {'error': 'wrong password'})
        except Administrator.DoesNotExist:
            return render(request, 'admin_login.html', {'error': 'Invalid admin ID or password'})
    return render(request, 'admin_login.html')

def admin_dashboard(request):
    students = Student.objects.all()  # Retrieve all students from the database
    return render(request, 'admin_dashboard.html', {'students': students})

from django.http import JsonResponse

# exam_app/views.py

import base64
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import os

import os
import json
import pika
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# exam_app/cv/Code/images
SAVE_DIR = 'exam_app/cv/Code/images/'

@csrf_exempt
def video_stream(request):
    if request.method == 'POST':
        usn = request.POST.get('usn')

        if usn:
            save_dir = os.path.join(SAVE_DIR, usn)
            os.makedirs(save_dir, exist_ok=True)

            frame = request.FILES.get('frame')
            if frame:
                frame_name = os.path.join(save_dir, f'frame{len(os.listdir(save_dir))}.png')
                with open(frame_name, 'wb') as f:
                    for chunk in frame.chunks():
                        f.write(chunk)

                # Push image to queue
                push_to_queue(usn, frame_name)

                return JsonResponse({'message': 'Frame saved & queued'}, status=200)
            else:
                return JsonResponse({'error': 'No frame data received'}, status=400)
        else:
            return JsonResponse({'error': 'No USN provided'}, status=400)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

def push_to_queue(usn, image_path):
    """Push image details to RabbitMQ queue"""
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='proctoring_queue')
    image_path = image_path.replace('\\', '/')
    message = json.dumps({'usn': usn, 'image_path': image_path[17:]})
    channel.basic_publish(exchange='', routing_key='proctoring_queue', body=message)
    
    connection.close()


# def run_cv(request):
#     if request.method == 'GET':
#         usn = request.GET.get('usn')
#         print("running")
#         score = first_function(usn)
#         print("done")
#         score = int(score)
#         return JsonResponse({'score': score})
#     else:
#         return JsonResponse({'error': 'Only GET requests are allowed'}, status=405)
    
    


import json
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import condition
import time

# Store warnings in memory
warnings_dict = {}

@csrf_exempt
def send_warning(request):
    """Receive cheating warnings and store them."""
    if request.method == 'POST':
        data = json.loads(request.body)
        usn = data.get('usn')
        stop_bool = data.get('stop_capture')
        stop_warning = data.get('warning')
        warnings_dict[usn] = {'message': stop_warning, 'stop_capture': stop_bool}  # Stop capture if cheating
        return JsonResponse({'message': 'Warning stored'}, status=200)
    return JsonResponse({'error': 'Only POST allowed'}, status=405)

def event_stream(usn):
    """Generator function to stream warnings via SSE."""
    last_warning = None
    while True:
        if usn in warnings_dict and warnings_dict[usn] != last_warning:
            last_warning = warnings_dict[usn]
            yield f"data: {json.dumps(last_warning)}\n\n"
        time.sleep(1)  # Prevent high CPU usage

def stream_warnings(request, usn):
    """SSE endpoint to send warnings to frontend."""
    response = StreamingHttpResponse(event_stream(usn), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    return response
