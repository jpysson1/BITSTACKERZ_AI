from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from blog.models import BlogPost

# Main dashboard
@login_required
def dashboard(request):
    return render(request, 'dashboard/dashboard.html')

@login_required
def load_settings(request):
    # Check if this is an HTMX request
    if request.headers.get('HX-Request'):
        # For HTMX requests, return just the content
        return render(request, 'dashboard/tabs/settings.html')
    
    # For regular requests, return the full dashboard
    return render(request, 'dashboard/dashboard.html', {
        'content_template': 'dashboard/tabs/settings.html'
    })

@login_required
def load_reports(request):
    # Check if this is an HTMX request
    if request.headers.get('HX-Request'):
        # For HTMX requests, return just the content
        return render(request, 'dashboard/tabs/reports/reports_base.html')
    
    # For regular requests, return the full dashboard
    return render(request, 'dashboard/dashboard.html', {
        'content_template': 'dashboard/tabs/reports/reports_base.html'
    })

# Report sub-tabs
@login_required
def load_monthly_reports(request):
    if request.headers.get('HX-Request'):
        return render(request, 'dashboard/tabs/reports/monthly.html')
    return render(request, 'dashboard/dashboard.html', {
        'content_template': 'dashboard/tabs/reports/monthly.html'
    })

@login_required
def load_annual_reports(request):
    if request.headers.get('HX-Request'):
        return render(request, 'dashboard/tabs/reports/annual.html')
    return render(request, 'dashboard/dashboard.html', {
        'content_template': 'dashboard/tabs/reports/annual.html'
    })

@login_required
def load_custom_reports(request):
    if request.headers.get('HX-Request'):
        return render(request, 'dashboard/tabs/reports/custom.html')
    return render(request, 'dashboard/dashboard.html', {
        'content_template': 'dashboard/tabs/reports/custom.html'
    })