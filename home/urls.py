from django.urls import include, path, reverse_lazy
from home import views
from django.contrib.auth import views as auth_views



app_name = 'home'

urlpatterns = [
    path('', views.home, name="home"),
    path('login/', views.user_login, name="login"),
    path('myprofile/', views.my_profile, name="myprofile"),
    path('signup/', views.user_signup, name="signup"),
    path('<int:id>/', views.magazine, name="magazine"),
    path('<int:id>/<slug:slug>/', views.issue, name="issue"),
    path('contact/', views.contact, name="contact"),
    path('mymagazines/', views.mymags, name="mymagazines"),
    path('signout/', views.user_signout, name="signout"),
    path('saveissue/', views.save_issue, name="save-issue"),
    path('membership/', views.membership, name="membership"),
    path('staff/', views.staff, name="staff"),
    path('codes/', views.codes, name='codes'),
    path('password_reset/done/', views.password_reset_done, name='password_reset_done'),
    path("password_reset", views.password_reset_request, name="password_reset"),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name="resetpassword/password_reset_confirm.html", success_url=reverse_lazy(
        'home:password_reset_complete')), name='password_reset_confirm'),
    path('reset/done/', views.password_reset_complete, name='password_reset_complete'),
    path('email/', views.send_code, name="sendcode"),
    path('payment-done/', views.payment_done, name='payment_done'),
    path('payment-cancelled/', views.payment_cancelled, name='payment_cancelled'),
    path('confirm_email/<uidb64>/<token>/', views.confirm_email, name='activate'),
    path('verify_email/', views.send_confirmation_email, name="sendvemail"),

]
