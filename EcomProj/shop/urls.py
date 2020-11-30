from django.contrib import admin
from django.urls import path
from . import views
from .views import *

urlpatterns = [
    path('', views.index,name="index"),
    path("about/", views.about, name="AboutUs"),
    path("contact/", views.contact, name="ContactUs"),
    path("tracker/", views.tracker, name="TrackingStatus"),
    path("search/", views.search, name="Search"),
    path("products/<int:myid>", views.productView, name="ProductView"),
    path("checkout/", views.checkout, name="Checkout"),
    path("categories/",views.categories,name="Categories"),
    path("register/",CustomerRegister.as_view(),name="register"),
    path('logout/',CustomerLogout.as_view(),name="customerLogout"),
    path('login/',CustomerLogin.as_view(),name="login"),
    path('profile/',CustomerProfile.as_view(),name="profile"),
    path('handlerequest/',views.handlerequest,name="handlerequest"),

]