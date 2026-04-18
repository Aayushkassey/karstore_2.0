from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .form import UserProfileForm
from .models import CustomerActivity

@login_required
def update_profile(request):
    if request.method == 'POST':
        # request.user le garda current login bhayeko user ko data load hunchha
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
    
    return render(request, 'pages/update_p.html', {'form': form})

