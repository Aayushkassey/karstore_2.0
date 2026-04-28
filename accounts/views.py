from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .form import UserProfileForm
from .models import CustomerActivity
from .models import CustomerUser 

@login_required
def view_profile(request):
    return render(request, 'pages/profile.html', {'user': request.user})

@login_required
def update_profile(request):
    error_msg = None  # सुरुमा एरर खाली राख्ने
    
    if request.method == 'POST':
        u_name = request.POST.get("username")
        
        if CustomerUser.objects.filter(username__iexact=u_name).exclude(pk=request.user.pk).exists():
            error_msg = "Username already taken. Please choose another."
            form = UserProfileForm(request.POST, instance=request.user)
        else:
            form = UserProfileForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                
                if request.user.is_authenticated and not request.user.is_superuser and not request.user.is_staff and not request.user.role=='SELLER' and request.user.role == 'CUSTOMER':
                    CustomerActivity.objects.create(
                        user=request.user,
                        action='update_profile'
                    )
                return redirect('home') 
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'pages/update_p.html', {'form': form, "error": error_msg})




