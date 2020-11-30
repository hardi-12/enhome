from django.contrib.auth.models import User
from django.shortcuts import render,redirect
from django.contrib.auth import authenticate,login,logout
from django.urls import reverse_lazy
from .models import Product
from .models import Contact
from .models import Orders
from .models import OrderUpdate
from PayTm import Checksum
from .models import Customer
from math import ceil
from .forms import RegisterForm,LoginForm
from django.views.decorators.csrf import csrf_exempt
import json
from django.views.generic import View, TemplateView, CreateView, FormView
# Create your views here.
from django.http import HttpResponse
MERCHANT_KEY = ''

def index(request):
    # products = Product.objects.all()
    # print(products)
    # n = len(products)
    # nSlides = n//4 + ceil((n/4)-(n//4))

    allProds = []
    catprods = Product.objects.values('category', 'id')
    cats = {item['category'] for item in catprods}
    for cat in cats:
        prod = Product.objects.filter(category=cat)
        n = len(prod)
        nSlides = n // 4 + ceil((n / 4) - (n // 4))
        allProds.append([prod, range(1, nSlides), nSlides])

    # params = {'no_of_slides':nSlides, 'range': range(1,nSlides),'product': products}
    # allProds = [[products, range(1, nSlides), nSlides],
    #             [products, range(1, nSlides), nSlides]]
    params = {'allProds':allProds}
    return render(request, 'shop/index.html', params)

def searchMatch(query, item):
    '''return true only if query matches the item'''
    if query in item.desc.lower() or query in item.product_name.lower() or query in item.category.lower():
        return True
    else:
        return False

def search(request):
    query = request.GET.get('search')
    allProds = []
    catprods = Product.objects.values('category', 'id')
    cats = {item['category'] for item in catprods}
    for cat in cats:
        prodtemp = Product.objects.filter(category=cat)
        prod = [item for item in prodtemp if searchMatch(query, item)]

        n = len(prod)
        nSlides = n // 4 + ceil((n / 4) - (n // 4))
        if len(prod) != 0:
            allProds.append([prod, range(1, nSlides), nSlides])
    params = {'allProds': allProds, "msg": ""}
    if len(allProds) == 0 or len(query)<4:
        params = {'msg': "Please make sure to enter relevant search query"}
    return render(request, 'shop/search.html', params)

def about(request):
    return render(request, 'shop/about.html')

def contact(request):
    if request.method=="POST":
        name=request.POST.get('name','')
        phone=request.POST.get('phone','')
        email=request.POST.get('email','')
        subject=request.POST.get('subject','')
        desc=request.POST.get('desc','')
        print(name,email,phone,desc)
        contact=Contact(name=name,email=email,phone=phone,desc=desc)
        contact.save()

    return render(request,'shop/contact.html')

def tracker(request):
    if request.method == "POST":
        orderId = request.POST.get('orderId', '')
        email = request.POST.get('email', '')
        try:
            order = Orders.objects.filter(order_id=orderId, email=email)
            if len(order) > 0:
                update = OrderUpdate.objects.filter(order_id=orderId)
                updates = []
                for item in update:
                    updates.append({'text': item.update_desc, 'time': item.timestamp})
                    response = json.dumps([updates,order[0].items_json], default=str)
                return HttpResponse(response)
            else:
                return HttpResponse('{}')
        except Exception as e:
            return HttpResponse('{}')

    return render(request, 'shop/tracker.html')

def productView(request,myid):
    #fetch the products using id
    product=Product.objects.filter(id=myid)
    print(product)
    params={'product':product[0]}
    return render(request,'shop/prodview.html',params)

def checkout(request):
    if request.method=="POST":
        items_json = request.POST.get('itemsJson', '')
        name = request.POST.get('name', '')
        amount = request.POST.get('amount', '')
        email = request.POST.get('email', '')
        address = request.POST.get('address1', '') + " " + request.POST.get('address2', '')
        city = request.POST.get('city', '')
        state = request.POST.get('state', '')
        zip_code = request.POST.get('zip_code', '')
        phone = request.POST.get('phone', '')
        order = Orders(items_json=items_json, name=name, email=email, address=address, city=city,
                       state=state, zip_code=zip_code, phone=phone,amount=amount)
        order.save()
        update = OrderUpdate(order_id=order.order_id, update_desc="The order has been placed")
        update.save()
        thank = True
        id = order.order_id
        #return render(request, 'shop/checkout.html', {'thank':thank, 'id': id})
        #Request paytm to transfer the amount to your account after payment by user
        param_dict={
            'MID': '',
            'ORDER_ID': str(order.order_id),
            'TXN_AMOUNT': str(amount),
            'CUST_ID': 'email',
            'INDUSTRY_TYPE_ID': 'Retail',
            'WEBSITE': 'WEBSTAGING',
            'CHANNEL_ID': 'WEB',
            'CALLBACK_URL': 'http://127.0.0.1:8000/shop/handlerequest/',

        }
        param_dict['CHECKSUMHASH']=Checksum.generate_checksum(param_dict,MERCHANT_KEY)
        return render(request,'shop/paytm.html',{'param_dict':param_dict})


    return render(request, 'shop/checkout.html')
@csrf_exempt
def handlerequest(request):
        #paytm will send post request here
        form=request.POST
        response_dict={}
        for i in form.keys():
            response_dict[i]=form[i]
            if i=='CHECKSUMHASH':
                checksum=form[i]
        verify=Checksum.verify_checksum(response_dict,MERCHANT_KEY,checksum)
        if verify:
            if response_dict['RESPCODE']=='01':
                print("order successful")
            else:
                print("unsuccessfull" + response_dict['RESPMSG'])
        return render(request,'shop/paymentstatus.html',{'response':response_dict})

def categories(request):
    products = Product.objects.all()
    params={'products':products}
    return render(request, 'shop/categories.html',params)

class CustomerRegister(CreateView):
    template_name ="shop/register.html"
    form_class =RegisterForm
    success_url = reverse_lazy('index')
    def form_valid(self,form):
        username=form.cleaned_data.get('username')
        password=form.cleaned_data.get('password')
        email=form.cleaned_data.get('email')
        user=User.objects.create_user(username,email,password)
        form.instance.user=user
        login(self.request,user)
        return super().form_valid(form)

class CustomerLogout(View):
    def get(self,request):
        logout(request)
        return redirect('index')

class CustomerLogin(FormView):
    template_name = "shop/login.html"
    form_class = LoginForm
    success_url = reverse_lazy('index')
    def form_valid(self,form):
        uname=form.cleaned_data.get("username")
        pword=form.cleaned_data.get("password")
        usr=authenticate(username=uname,password=pword)
        if usr is not None and usr.customer:
            login(self.request,usr)
        else:
            return render(self.request,self.template_name,{"form":self.form_class,"error":"Invalid credentials"})
        return  super().form_valid(form)

class CustomerProfile(TemplateView):
    template_name = "shop/profile.html"
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.customer:
            pass
        else:
            return redirect("/login/?next=/profile")
        return super().dispatch(request, *args, **kwargs)
    def get_context_data(self, **kwargs):
        context=super().get_context_data(**kwargs)
        customer=self.request.user.customer
        context['customer']=customer
        return context