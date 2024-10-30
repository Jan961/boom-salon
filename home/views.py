from django.shortcuts import render, redirect
from django.core.mail import EmailMessage
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm
from django.template.defaulttags import register
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse

from django.urls import reverse, reverse_lazy
from home.models import Magazine, UserProfile, Hashtag, MagazineIssue, DiscountCode, Membership
from datetime import datetime
import random, string, secrets
import dateutil.relativedelta

from home.forms import UserForm, UserProfileForm, UploadCodesFileForm, CodesFileForm, UserPasswordChangeForm
from datetime import datetime
import random, string, secrets
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.db.models.query_utils import Q
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_text
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.sites.shortcuts import get_current_site
from home.tokens import account_activation_token
from django.contrib.auth import views as auth_views
from paypal.standard.forms import PayPalPaymentsForm
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from paypal.standard.models import ST_PP_COMPLETED
from paypal.standard.ipn.signals import valid_ipn_received
from django.dispatch import receiver
from django.views.generic import TemplateView



def is_mobile_device(request):
    # check visitor agent
    try:
        user_agent = request.META['HTTP_USER_AGENT']
    except:
        return False

    keywords = ['Mobile', 'Opera Mini', 'Android']

    if any(word in user_agent for word in keywords):
        return True
    else:
        return False


def home(request):
    ctx = {}

    ctx['magazines'] = Magazine.objects.all()

    if is_mobile_device(request):
        # mobile
        temp = 'mobiletemplates/homemobile.html'
    else:
        # desktop
        temp = 'home.html'

    return render(request, temp, context=ctx)


def user_login(request):

    if is_mobile_device(request):
        # mobile
        temp = 'mobiletemplates/login_separate_page_mobile.html'
    else:
        # desktop
        temp = "login.html"

    # if HTTP POST pull relevant info
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)

        if user:
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect(reverse('home:home'))
            else:
                return HttpResponse("Your account is disabled")
        else:
            print("Invalid login details: {0}, {1}.".format(username, password))
            return HttpResponse("Invalid login details supplied.")

    return render(request, temp, {})


def user_signup(request):
    registered = False

    if is_mobile_device(request):
        # mobile
        temp = 'mobiletemplates/signupmobile.html'
    else:
        # desktop
        temp = 'signup.html'

    # if HTTP POST then process form
    if request.method == 'POST':
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        # if both forms are valid
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            user.set_password(user.password)
            user.save()

            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()

            registered = True
            send_confirmation_email(user, request)
            user = authenticate(username=user_form.cleaned_data['username'],
                                password=user_form.cleaned_data['password'])
            login(request, user)
            return redirect(reverse('home:home'))

        else:
            print(user_form.errors, profile_form.errors)
            return render(request, temp, {'form': user_form})
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()

    ctx = {'user_form': user_form, 'profile_form': profile_form, 'registered': registered}

    return render(request, temp, context=ctx)

# Mobile version uses myprofile view to render as at seemed that this would require less duplicate code
# - i.e. coping the functions for several views using differnt urls on desktop but renderd all on the same page for mobile
@login_required
def my_profile(request):
    ctx = {}
    password_form = UserPasswordChangeForm(request.user, prefix='password_form')
    user = UserProfile.objects.get(user=request.user)
    issues = user.saved_issues.order_by("magazine")
    user2 = request.user

    ctx['magazines'] = Magazine.objects.all()
    ctx['savedissues'] = issues.all()
    ctx['curr_user'] = user


    if request.user.is_authenticated:
        ctx['subscribed'] = UserProfile.objects.get(user=request.user).is_subscribed
        if ctx['subscribed']==True:
            ctx['date_subscribed']=UserProfile.objects.get(user=request.user).date_subscribed
            ctx['date_valid']=Membership.objects.get(user=request.user).date_valid

    codes=DiscountCode.objects.all().count()
    ctx['codes']=codes


    if codes==0:
        ctx['countdown']="No codes left."
    elif codes==1:
        ctx['countdown']="Only 1 code left."
    else:
        ctx['countdown']="There are {} codes left.".format(codes)

    host = request.get_host()
    paypal_dict={
        'business':settings.PAYPAL_RECEIVER_EMAIL,
        'amount':5.00,
        'item_name':"Membership",
        #'invoice': DiscountCode.objects.all()[0],
        'currency_code':'GBP',
        'return_url': 'http://{}{}'.format(host, reverse('home:payment_done')),


        'cancel_return': 'http://{}{}'.format(host,
                                              reverse('home:payment_cancelled')),
            "sra": "1",                        # reattempt payment on payment error
    }
    ctx['form']=PayPalPaymentsForm(initial=paypal_dict, button_type="subscribe")


    if request.method == 'POST':
        action = request.POST['action']

        if action == 'verify_email':
            send_confirmation_email(user2, request)
            messages.success(request, 'Email Sent')
            return redirect(reverse('home:myprofile'))

        if action == 'edit_password':
            password_form = UserPasswordChangeForm(request.user, request.POST, prefix='password_form')
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password updated')
                return redirect(reverse('home:myprofile'))

    ctx['password_form'] = password_form
    
    if request.user.is_authenticated:
        ctx['subscribed'] = UserProfile.objects.get(user=request.user).is_subscribed
        if ctx['subscribed']==True:
            ctx['date_subscribed']=UserProfile.objects.get(user=request.user).date_subscribed
            ctx['date_valid']=Membership.objects.get(user=request.user).date_valid

    if is_mobile_device(request):
        # mobile
        temp = 'mobiletemplates/membershipmenumobile.html'
    else:
        # desktop
        temp = 'myprofile.html'


    return render(request, temp, ctx)


def renewMemberships(request):
    memberships=Membership.objects.all()
    if memberships.count()!=0:
        if memberships[0].date_valid < datetime.now().date():
            for membership in memberships:
                user=membership.user
                u=UserProfile.objects.get(user=user)
                u.is_subscribed=False
                u.has_code=False
                u.save()
            memberships.delete()


def membership(request):

    renewMemberships(request)

    ctx = {}
    ctx['magazines'] = Magazine.objects.all()
    

    if request.user.is_authenticated:
        ctx['subscribed'] = UserProfile.objects.get(user=request.user).is_subscribed
        ctx['email_confirmed']=UserProfile.objects.get(user=request.user).email_confirmed
        if ctx['subscribed']==True:
            ctx['date_subscribed']=UserProfile.objects.get(user=request.user).date_subscribed
            ctx['date_valid']=Membership.objects.get(user=request.user).date_valid

    codes=DiscountCode.objects.all().count()
    ctx['codes']=codes
    
    
    
    if codes==0:
        ctx['countdown']="No codes left."
    elif codes==1:
        ctx['countdown']="Only 1 code left."
    else:
        ctx['countdown']="There are {} codes left.".format(codes)
    letters=string.ascii_letters
    random_var=''.join(random.choice(letters) for i in range (20))
    
    host=request.get_host()
    paypal_dict={
        'business':settings.PAYPAL_RECEIVER_EMAIL,
        'amount':5.00,
        'item_name':"Membership",
        #'invoice': DiscountCode.objects.all()[0],
        'currency_code':'GBP',
        'return_url': 'http://{}{}'.format(host, reverse('home:payment_done')),


        'cancel_return': 'http://{}{}'.format(host,
                                              reverse('home:payment_cancelled')),
            "sra": "1",                        # reattempt payment on payment error
    }
    ctx['form']=PayPalPaymentsForm(initial=paypal_dict, button_type="subscribe")
    


    return render(request, 'membership.html', context=ctx)



@login_required
def user_signout(request):
    logout(request)
    return redirect(reverse('home:home'))


def magazine(request, id):
    ctx = {}

    mag = Magazine.objects.get(id=id)

    ctx['this'] = mag
    ctx['magazines'] = Magazine.objects.all()
    ctx['issues'] = MagazineIssue.objects.filter(magazine=mag).order_by("-date")
    ctx['latest_issue'] = MagazineIssue.objects.filter(magazine=mag).first()

    if is_mobile_device(request):
        temp = 'mobiletemplates/magazinemobile.html'
    else:
        temp = 'magazine.html'

    return render(request, temp, context=ctx)


def issue(request, id, slug):
    ctx = {}

    mag = Magazine.objects.get(id=id)
    issue = MagazineIssue.objects.get(slug=slug)

    ctx['this'] = mag
    ctx['thisIssue'] = issue
    ctx['magazines'] = Magazine.objects.all()
    ctx['issues'] = MagazineIssue.objects.filter(magazine=mag)

    if request.user.is_authenticated:
        user = UserProfile.objects.get(user=request.user)
        ctx['saved_issues'] = user.saved_issues.all()
        ctx['subscribed'] = UserProfile.objects.get(user=request.user).is_subscribed

    if is_mobile_device(request):
        temp = 'mobiletemplates/issuemobile.html'
    else:
        temp = 'issue.html'

    return render(request, temp, context=ctx)





def password_reset_done(request):
    if is_mobile_device(request):
        temp = 'mobiletemplates/password_reset_done_mobile.html'
    else:
        temp = 'resetpassword/password_reset_done.html'

    return auth_views.PasswordResetDoneView.as_view(template_name=temp)(request)



def password_reset_complete(request):
    if is_mobile_device(request):
        temp = 'mobiletemplates/password_reset_complete_mobile.html'
    else:
        temp = 'resetpassword/password_reset_complete.html'

    return auth_views.PasswordResetCompleteView.as_view(template_name=temp)(request)



def password_reset_confirm(request):
    if is_mobile_device(request):
        temp = 'mobiletemplates/password_reset_confirm_mobile.html'
    else:
        temp = 'resetpassword/password_reset_confirm.html'

    return auth_views.PasswordResetConfirmView.as_view(template_name=temp,
                                                       success_url=reverse_lazy('home:password_reset_complete'))(request)




@login_required
def mymags(request):
    ctx = {}

    user = UserProfile.objects.get(user=request.user)
    issues = user.saved_issues.order_by("magazine")

    ctx['magazines'] = Magazine.objects.all()
    ctx['savedissues'] = issues.all()

    return render(request, 'mymagazines.html', context=ctx)


@login_required
def save_issue(request):
    if request.method == 'POST':
        issue_name = request.POST.get('name')

        issue = MagazineIssue.objects.get(slug=issue_name)
        user = UserProfile.objects.get(user=request.user)

        for i in user.saved_issues.all():
            # This removes attraction from the list if already present hence acting as a toggle
            if i == issue:
                user.saved_issues.remove(issue)
                user.save()
                return JsonResponse({'success': 'true', 'value': 0})

        user.saved_issues.add(issue)
        user.save()

        return JsonResponse({'success': 'true', 'value': 1})

    return JsonResponse({'success': 'false'})


def contact(request):
    ctx = {}

    ctx['magazines'] = Magazine.objects.all()

    return render(request, 'contact.html', context=ctx)


@staff_member_required
def staff(request):
    ctx = {}

    ctx['magazines'] = Magazine.objects.all()

    return render(request, 'staff.html', context=ctx)


@staff_member_required
def codes(request):
    ctx = {}
    ctx['magazines'] = Magazine.objects.all()
    ctx['codefile'] = None
    ctx['done'] = None

    form = CodesFileForm()
    form2 = UploadCodesFileForm()

    if request.method == 'POST':
        if request.FILES:
            form2 = UploadCodesFileForm(request.POST, request.FILES)

            if form2.is_valid():
                file = request.FILES['file']
                codes = file.read().decode('utf-8').split(',')[:-1]

                # delete existing codes
                DiscountCode.objects.all().delete()

                # reset users has_code field meaning they can recieve new email
                for user in UserProfile.objects.all():
                    user.has_code = False
                    user.save()

                # Save codes to DB
                for code in codes:
                    new_code = DiscountCode(code=code)
                    new_code.save()

                ctx['done'] = "Success!"
        else:
            form = CodesFileForm(request.POST)

            if form.is_valid():
                time, codes = gen_codes(request.POST.get("amount"))
                ctx['codefile'] = time

    ctx['range'] = range(5, 501, 5)
    ctx['form'] = form
    ctx['form2'] = form2
    ctx['errors'] = form.errors or None
    ctx['errors2'] = form2.errors or None

    return render(request, 'codes.html', context=ctx)


def gen_codes(amount):
    time = datetime.now().strftime("%d-%m-%Y-%H%M%S")
    #This path is what will work on the pythonanywhere deployment platform
    #path = '/home/CloMagazines/boom_saloon/static/code_templates/' + time + '.csv'
    path = 'static/code_templates/' + time + '.csv'
    codes = []
    code_length = 16

    with open(path, 'w+') as f:
        for i in range(int(amount)):
            # ---This line of code has come from https://www.javatpoint.com/python-program-to-generate-a-random-string
            code = ''.join(secrets.choice(string.ascii_letters + string.digits) for x in range(code_length)) + ','
            f.write(code)
            codes.append(code)

    return time, codes


@login_required
def send_code(request):
    user = UserProfile.objects.get(user=request.user)

    if user.is_subscribed == False:
        return HttpResponse("Sorry, you are not a subscriber!")
    elif user.has_code:
        return HttpResponse("You have already recieved your discount code for this month. Please check your inbox!")

    try:
        code = DiscountCode.objects.all()[0]
    except IndexError:
        return HttpResponse(
            "There are no available codes at the moment. If you think there should be, please get in touch.")

    text = """
Hey """ + request.user.username + """,


Thank you so much for making the decision to subscribe to Clò this month. Here is your unique discount code which 
can be used once across any of the magazines on our site marked with a 'subscriber price'.

Please ensure to keep this email or your code safe as it cannot be resent.

    """ + code.code + """


The Clò Team. """

    email = EmailMessage(
        subject='Your unique Clò discount code',
        body=text,
        from_email='clo.magazines@gmail.com',
        to=[request.user.email],
    )

    try:
        email.send()
    except Exception as e:
        print(e)
        return HttpResponse("Oops! Something went wrong.")


    memb=Membership(user=request.user,date_subscribed=datetime.today(), date_valid=code.date_valid,code=code.code)
    memb.save()
    
    HttpResponse("Membership should be created")
    code.delete()

    user.has_code = True
    user.save()

    return HttpResponseRedirect(reverse('home:membership'))


@csrf_exempt
def payment_done(request):


    if is_mobile_device(request):
        # mobile
        temp_done = 'mobiletemplates/payment_done_mobile.html'
        temp_reverse_membership = 'home:myprofile'
    else:
        # desktop
        temp_reverse_membership = 'home:membership'
        temp_done = 'payment_done.html'




    payerid=request.GET.get("PayerID")
    if payerid==None:
        return HttpResponseRedirect(reverse(temp_reverse_membership))
    else:
        user = UserProfile.objects.get(user=request.user)
        #if user.paid==True:
        user.is_subscribed = True
        user.date_subscribed=datetime.today()
        user.save()

        code=DiscountCode.objects.all()[0]
        date = datetime.today()

        send_code(request)


        return render(request, temp_done)


@csrf_exempt
def payment_cancelled(request):
    return render(request, 'payment_cancelled.html')


def password_reset_request(request):

    if is_mobile_device(request):
        temp_password_reset = 'mobiletemplates/password_reset_mobile.html'
    else:
        temp_password_reset = "resetpassword/password_reset.html"

    if request.method == "POST":
        password_reset_form = PasswordResetForm(request.POST)
        if password_reset_form.is_valid():
            data = password_reset_form.cleaned_data['email']
            associated_users = User.objects.filter(Q(email=data))
            if associated_users.exists():
                for user in associated_users:
                    email_template_name = "resetpassword/password_reset_email.txt"
                    c = {
                        "email": user.email,
                        'domain': '127.0.0.1:8000',
                        'site_name': 'Website',
                        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                        "user": user,
                        'token': default_token_generator.make_token(user),
                        'protocol': 'http',
                    }
                    email_text = render_to_string(email_template_name, c)
                    user_email = [user.email]

                    to_be_sent_email = EmailMessage(
                        subject='Clò Password Reset',
                        body=email_text,
                        from_email='clo.magazines@gmail.com',
                        to=user_email
                    )
                    try:
                        to_be_sent_email.send()
                    except Exception as e:
                        print(e)
                        return HttpResponse("Oops! Something went wrong.")
                    return redirect("password_reset/done/")

    password_reset_form = PasswordResetForm()

    return render(request=request, template_name=temp_password_reset,
                  context={"password_reset_form": password_reset_form})


def send_confirmation_email(user, request):
    site = get_current_site(request)
    email_template_name = "confirm_email.html"
    c = {
        "user": user,
        'domain': site,
        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
        'protocol': 'http',
    }
    email_text = render_to_string(email_template_name, c)
    user_email = [user.email]

    to_be_sent_email = EmailMessage(
        subject='Confirm your Clò email',
        body=email_text,
        from_email='clo.magazines@gmail.com',
        to=user_email
    )
    try:
        to_be_sent_email.send()
    except Exception as e:
        print(e)
        return HttpResponse("Oops! Something went wrong.")
    return redirect("home:login")


def confirm_email(request, uidb64, token):
    ctx={}
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)

    except Exception as e:
        user = None

    if is_mobile_device(request):
        # mobile
        tempfail = 'mobiletemplates/emailverifyfailmobile.html'
        tempsuccess = 'mobiletemplates/emailverifysuccessmobile.html'
    else:
        # desktop
        tempfail = 'emailverifyfail.html'
        tempsuccess = 'emailverifysuccess.html'


    if user and account_activation_token.check_token(user, token):
        user2 = UserProfile.objects.get(user=user)
        user2.email_confirmed = True
        user2.save()
        ctx['curr_user'] = user2
        return render(request, tempsuccess)
    else:
        return render(request, tempfail, ctx)








