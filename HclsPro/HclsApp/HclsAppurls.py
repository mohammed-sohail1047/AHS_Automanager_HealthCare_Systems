from  . import views
from django.urls import path

urlpatterns = [
    path('', views.home, name='home'),
    path('home/', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),
    path('activate_admin/<int:id>', views.activate_admin, name='activate_admin'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('add/', views.add, name='add'),
    path('add-operational-admin/', views.add_operational_admin, name='add_operational_admin'),
    path('manage/', views.manage, name='manage'),
    path('edit/<int:id>/', views.edit, name='edit'),
    path('delete_admin/<int:id>/', views.delete_admin, name='delete_admin'),
    path('bulk_delete_admins/', views.bulk_delete_admins, name='bulk_delete_admins'),
    path('OAdashboard/', views.OAdashboard, name='OAdashboard'),
    path('OAprofile/', views.OAprofile, name='OAprofile'),
    path('staff/dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('staff/profile/', views.staff_profile, name='staff_profile'),
    path('doctor/dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('doctor/profile/', views.doctor_profile, name='doctor_profile'),
    path('doctoradd/', views.doctoradd, name='doctoradd'),
    path('doctormanage/', views.doctormanage, name='doctormanage'),
    path('helperadd/', views.helperadd, name='helperadd'),  
    path('helpermanage/', views.helpermanage, name='helpermanage'),
    path('receptionistadd/', views.receptionistadd, name='receptionistadd'),
    path('receptionistmanage/', views.receptionistmanage, name='receptionistmanage'),
    
    # Receptionist specific routes
    path('receptionist/dashboard/', views.receptionist_dashboard, name='receptionist_dashboard'),
    path('receptionist/profile/', views.receptionist_profile, name='receptionist_profile'),
    path('receptionist/patient/add/', views.patient_add, name='patient_add'),
    path('receptionist/patient/edit/<int:id>/', views.patient_edit, name='patient_edit'),
    
    # Helper specific routes
    path('helper/dashboard/', views.helper_dashboard, name='helper_dashboard'),
    path('helper/profile/', views.helper_profile, name='helper_profile'),
    
    # Patient specific routes
    path('patient/dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('patient/profile/', views.patient_profile, name='patient_profile'),
]
