from django.contrib.auth.backends import BaseBackend
from .serializers import RegisterSerializer
import logging
from django.views.decorators.csrf import csrf_exempt
logger = logging.getLogger(__name__)
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.response import Response
import logging
from django.contrib.auth.hashers import check_password
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.core.mail import send_mail
from django.conf import settings
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.shortcuts import render
from .models import User

from .serializers import EventSerializer, CurrencySerializer, UserSerializer
from twilio.rest import Client
from rest_framework_simplejwt.tokens import RefreshToken
import random
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
logger = logging.getLogger(__name__)
# Create your views here.
from django.contrib.auth.tokens import default_token_generator

def generate_confirmation_code():
    return ''.join(random.choices('0123456789', k=6))

def send_confirmation_email(user, confirmation_code):
    subject = 'Подтверждение регистрации'
    message = f'Здравствуйте, {user.username}! Подтвердите вашу почту с помощью следующего кода: {confirmation_code}'
    from_email = 'ExchangeWork <aziretdzumabekov19@gmail.com>'
    recipient_list = [user.email]

    html_message = f'''
    <html>
        <head>
            <style>
                body {{
                    background-color: #f2f4f6;
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    max-width: 600px;
                    margin: 40px auto;
                    background-color: #ffffff;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 20px;
                }}
                .header h2 {{
                    color: #333333;
                }}
                .content p {{
                    font-size: 16px;
                    color: #555555;
                    line-height: 1.6;
                }}
                .code {{
                    margin: 20px auto;
                    font-size: 28px;
                    font-weight: bold;
                    background-color: #e0f7e9;
                    color: #2e7d32;
                    padding: 15px;
                    text-align: center;
                    border-radius: 5px;
                    width: 200px;
                }}
                .footer {{
                    text-align: center;
                    font-size: 12px;
                    color: #999999;
                    margin-top: 30px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Подтверждение регистрации</h2>
                </div>
                <div class="content">
                    <p>Здравствуйте, <strong>{user.username}</strong>!</p>
                    <p>Спасибо за регистрацию на ExchangeWork.</p>
                    <p>Пожалуйста, используйте следующий код для подтверждения вашей почты:</p>
                    <div class="code">{confirmation_code}</div>
                    <p>Если вы не регистрировались, просто проигнорируйте это письмо.</p>
                </div>
                <div class="footer">
                    <p>&copy; 2025 ExchangeWork. Все права защищены.</p>
                </div>
            </div>
        </body>
    </html>
    '''

    try:
        print(user.email)
        send_mail(subject, message, from_email, recipient_list, html_message=html_message)
    except Exception as e:
        logger.error(f"Ошибка отправки письма подтверждения: {str(e)}")

def send_password_reset_email(user, reset_code):
    subject = 'Сброс пароля'
    message = f'Здравствуйте, {user.username}! Ваш код для сброса пароля: {reset_code}'
    from_email = 'ExchangeWork'
    recipient_list = [user.email]

    html_message = f'''
    <html>
        <head>
            <style>
                body {{
                    background-color: #f2f4f6;
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    max-width: 600px;
                    margin: 40px auto;
                    background-color: #ffffff;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 20px;
                }}
                .header h2 {{
                    color: #333333;
                }}
                .content p {{
                    font-size: 16px;
                    color: #555555;
                    line-height: 1.6;
                }}
                .code {{
                    margin: 20px auto;
                    font-size: 28px;
                    font-weight: bold;
                    background-color: #fff3cd;
                    color: #856404;
                    padding: 15px;
                    text-align: center;
                    border-radius: 5px;
                    width: 200px;
                }}
                .footer {{
                    text-align: center;
                    font-size: 12px;
                    color: #999999;
                    margin-top: 30px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Сброс пароля</h2>
                </div>
                <div class="content">
                    <p>Здравствуйте, <strong>{user.username}</strong>!</p>
                    <p>Мы получили запрос на сброс вашего пароля.</p>
                    <p>Пожалуйста, введите следующий код для создания нового пароля:</p>
                    <div class="code">{reset_code}</div>
                    <p>Если вы не запрашивали сброс пароля, проигнорируйте это письмо.</p>
                </div>
                <div class="footer">
                    <p>&copy; 2025 ExchangeWork. Все права защищены.</p>
                </div>
            </div>
        </body>
    </html>
    '''


    send_mail(subject, message, from_email, recipient_list, html_message=html_message)



@csrf_exempt
def confirm_email_view(request):
    if request.method == 'POST':
        confirmation_code = request.POST.get('confirmation_code')
        try:
            user = User.objects.get(confirmation_code=confirmation_code)
            if user:
                user.email_confirmed = True
                user.confirmation_code = None  # Clear the confirmation code
                user.save()
                messages.success(request, 'Your account has been activated! You can now log in.')
                return redirect('login')
        except User.DoesNotExist:
            messages.error(request, 'Invalid confirmation code. Please try again.')

    return render(request, 'users/waiting_for_confirmation.html')

class ForgotPasswordAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({"message": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            reset_code = generate_confirmation_code()
            user.reset_code = reset_code  # assuming you added reset_code field to your User model
            user.save()

            send_password_reset_email(user, reset_code)

            return Response({"message": "Password reset code sent to your email."}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"message": "User with this email not found."}, status=status.HTTP_400_BAD_REQUEST)

class ResetPasswordAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        reset_code = request.data.get('reset_code')
        new_password = request.data.get('new_password')

        if not email or not reset_code or not new_password:
            return Response({"message": "Email, reset code, and new password are required."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)

            # Проверяем, совпадает ли код сброса
            if user.reset_code == reset_code:
                user.set_password(new_password)  # Обновляем пароль
                user.reset_code = None  # Очищаем код сброса
                user.save()

                return Response({"message": "Password has been successfully reset."}, status=status.HTTP_200_OK)
            else:
                return Response({"message": "Invalid reset code."}, status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:
            return Response({"message": "User with this email not found."}, status=status.HTTP_400_BAD_REQUEST)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            confirmation_code = generate_confirmation_code()
            user.confirmation_code = confirmation_code
            user.save()

            send_confirmation_email(user, confirmation_code)

            return Response({'message': 'User registered, please confirm your email'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserAuthentication(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        try:
            user = User.objects.get(username=username)
            if check_password(password, user.password):
                # Generate token
                refresh = RefreshToken.for_user(user)
                return Response({
                    "message": "Authentication successful",
                    "tokens": {
                        "refresh": str(refresh),
                        "access": str(refresh.access_token),
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid password"}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

class ConfirmEmailAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Получаем email и код подтверждения из запроса
        email = request.data.get('email')
        confirmation_code = request.data.get('confirmation_code')

        if not email or not confirmation_code:
            return Response({"message": "Email and confirmation code are required."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            # Ищем пользователя по email
            user = User.objects.get(email=email)

            # Проверяем, совпадает ли код подтверждения
            if user.confirmation_code == confirmation_code:
                # Если код правильный, активируем email пользователя
                user.email_confirmed = True
                user.confirmation_code = None  # Очищаем код после подтверждения
                user.save()

                return Response({"message": "Your email has been confirmed! You can now log in."},
                                status=status.HTTP_200_OK)
            else:
                return Response({"message": "Invalid confirmation code."}, status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:
            # Если пользователь с таким email не найден
            return Response({"message": "User with this email not found."}, status=status.HTTP_400_BAD_REQUEST)


class CustomBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None
        if check_password(password, user.password):
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None