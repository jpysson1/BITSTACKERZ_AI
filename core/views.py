from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Main dashboard
@login_required
def dashboard(request):
    return render(request, 'dashboard/dashboard.html')

# Main tabs
@login_required
def load_blog(request):
    return render(request, 'dashboard/tabs/blog.html')

@login_required
def load_settings(request):
    return render(request, 'dashboard/tabs/settings.html')

@login_required
def load_reports(request):
    return render(request, 'dashboard/tabs/reports/reports_base.html')

# Report sub-tabs
@login_required
def load_monthly_reports(request):
    return render(request, 'dashboard/tabs/reports/monthly.html')

@login_required
def load_annual_reports(request):
    return render(request, 'dashboard/tabs/reports/annual.html')

@login_required
def load_custom_reports(request):
    return render(request, 'dashboard/tabs/reports/custom.html')

