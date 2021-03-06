# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from models import *
from passlib.hash import sha256_crypt
import json
import os
from django.template import RequestContext
from collections import OrderedDict
from django.core.mail import send_mail
from datetime import datetime
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import resolve
import datetime
from django.utils import timezone
from distanceLongitudeLatitude import getLatitudeLongitude, getDistanceBetweenTwoPoints
from operator import itemgetter
from django.conf import settings
from datetime import date
from .serializers import *
from .models import *
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from rest_framework.views import APIView
from rest_framework import mixins
from rest_framework import generics
from rest_framework import permissions
from django.contrib.auth import authenticate, login
from rest_framework_jwt.settings import api_settings
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_200_OK
)


jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

path = getattr(settings, "CSV_FOLDER", None) +'CountryToCodeMapping.csv'
CountryToCodeMappingFile = open(path, "r")
CountryToCodeMapping = {}
for rows in CountryToCodeMappingFile:
    rows = rows[0:-1].decode('UTF-8')
    fullForm, ShortForm = rows.split("|")
    CountryToCodeMapping[fullForm] = ShortForm
    
@csrf_exempt
@api_view(["POST"])
@permission_classes((AllowAny,))
def loginTokenGeneration(request):
    username = request.data.get("username")
    password = request.data.get("password")
    if username is None or password is None:
        return Response({'error': 'Please provide both username and password'},
                        status=HTTP_400_BAD_REQUEST)
    user = authenticate(username=username, password=password)
    if not user:
        return Response({'error': 'Invalid Credentials'},
                        status=HTTP_404_NOT_FOUND)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({'token': token.key},
                    status=HTTP_200_OK)
    

@csrf_exempt
@api_view(['GET', 'POST'])
def user_list(request):
    if request.method == 'GET':
        snippets = users_profile.objects.all()
        serializer = UserSerializer(snippets, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors,  status=status.HTTP_400_BAD_REQUEST)

class UserBloodList(APIView):    
    def get(self, request, blood_group, format=None):
        print blood_group
        if(blood_group not in ['O+', 'B+', 'A+', 'AB+', 'O-', 'B-', 'A-', 'AB-']):
            return Response(data={"message": "Invalid Blood Group"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            queryset = users_profile.objects.filter(BLOOD_GP=blood_group)
            serializer = UserSerializer(queryset, many=True)
            return Response(serializer.data)
            
           
class CreateCampaignView(generics.ListCreateAPIView):
    queryset = active_campaigns.objects.all()
    global len_set
    len_set = len(queryset)+1
    serializer_class = ActiveCampaigns    
    
    def post(self, request, *args, **kwargs):
        LATITUDE, LONGITUDE = getLatitudeLongitude.getLatitudeLongitude(request.data["ADDRESS"].strip() + ", " + request.data["CITY"].strip() + ", " + request.data["STATE"].strip() + ", " + request.data["COUNTRY"].strip())
        print request.data
        mutable = request.data._mutable
        request.data._mutable = True
        request.data["CAMPAIGN_ID"] = "C"+str(len_set)
        request.data["LATITUDE"] = LATITUDE
        request.data["LONGITUDE"] = LONGITUDE
        request.data._mutable = mutable
        print request.data
        serializer = ActiveCampaigns(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
   
    def put(self, request, *args, **kwargs):
        try:
            campaign = self.queryset.get(CAMPAIGN_ID=kwargs["id"])
            serializer = ActiveCampaigns(instance=campaign, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except active_campaigns.DoesNotExist:
            return Response(
                data={
                    "message": "Campaign with id: {} does not exist".format(kwargs["id"])
                },
                status=status.HTTP_404_NOT_FOUND
            )
    
    
class UserList(mixins.ListModelMixin, mixins.CreateModelMixin, generics.GenericAPIView):
    queryset = users_profile.objects.all()
    serializer_class = UserSerializer
    
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)
        
    '''/*def get(self, request, format=None):
        snippets = users_profile.objects.all()
        serializer = UserSerializer(snippets, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors,  status=status.HTTP_400_BAD_REQUEST)*/'''


def homePage(request):
    return render(request, 'homePage.html', {})
    
def cuVolunteer(request):
    login_info = request.session.get('username', 'guest')
    if request.method == 'GET':
        if(login_info[0].encode("utf-8")==""):
            return render(request, 'cuVolunteer.html', {})
        else:
            user = OrderedDict() 
            user["USERNAME"]=login_info[1].encode("utf-8")
            user["USEREMAIL"]=login_info[0].encode("utf-8")
            user["MESSAGE"]=""
            user["DATA"]=[]
            if(user["USEREMAIL"]==""):
                return render(request, 'cuVolunteer.html', {})  
            else:
                output = {}
                rows = GetUserDetails(user["USEREMAIL"])
                if(rows):
                    country_lookup = rows.COUNTRY
                    if (rows.COUNTRY in CountryToCodeMapping.keys()):
                        country_lookup = CountryToCodeMapping[rows.COUNTRY].strip()
                    today_date = str(date.today())
                    print(today_date)
                    data_row = getActiveBloodCampaigns(country_lookup, today_date)
                    if(data_row):
                        for value in data_row:
                            distance = getDistanceBetweenTwoPoints.distance(float(rows.LATITUDE), float(rows.LONGITUDE), float(value.LATITUDE), float(value.LONGITUDE))
                            if (distance <=40):
                                distance = round(distance, 2)
                                user["DATA"].append({'ADDRESS':value.ADDRESS, 'CITY':value.CITY, 'STATE':value.STATE, 'COUNTRY':value.COUNTRY, 'DATE':value.DATE, 'DISTANCE':distance})
                        user["MESSAGE"] = "Success"
                        return render(request, 'cuVolunteer.html', {"data":user})
                    else:
                        user["MESSAGE"] = "No campaigns available"
                    return render(request, 'cuVolunteer.html', {"data":user})
                else:
                    user["MESSAGE"] = "Enter details in profile first"
                    return render(request, 'cuVolunteer.html', {"data":user})
    elif request.method == 'POST':
        return render(request, 'cuVolunteer.html', {})    
        
def cuNeedBlood(request):
    login_info = request.session.get('username', 'guest')
    if request.method == 'GET':
        if(login_info[0].encode("utf-8")==""):
            return render(request, 'cuNeedBlood.html', {})
        else:
            user = OrderedDict() 
            user["ACCOUNTNAME"]=login_info[1].encode("utf-8")
            user["ACCOUNTEMAIL"]=login_info[0].encode("utf-8")
            user["LOOKUP_KEY"]="".encode('utf-8')
            user["ZIP"]="".encode('utf-8')
            user["ADDRESS"]="".encode('utf-8')
            user["CITY"]="".encode('utf-8')
            user["STATE"]="".encode('utf-8')
            user["COUNTRY"]="".encode('utf-8')
            user["BLOOD_GP"]="".encode('utf-8')
            user["USERNAME"]="".encode('utf-8')
            user["CONTACT"]="".encode('utf-8')
            user["USEREMAIL"]="".encode('utf-8')
            user["DATE"]="".encode('utf-8')
            data = getUserNeedBloodDetails(login_info[0].encode("utf-8"))
            if(data):
                bloodGroup = ""
                if(data.BLOOD_GP[1] == "P"):
                    bloodGroup = data.BLOOD_GP[0] + "+"
                elif(data.BLOOD_GP[2] == "P"):
                    bloodGroup = data.BLOOD_GP[0:2] + "+"
                elif(data.BLOOD_GP[1] == "N"):
                    bloodGroup = data.BLOOD_GP[0] + "-"
                elif(data.BLOOD_GP[2] == "N"):
                    bloodGroup = data.BLOOD_GP[0:2] + "-"                    
                user["LOOKUP_KEY"]=data.LOOKUP_KEY.encode('utf-8')
                user["ZIP"]=data.ZIP.encode('utf-8')
                user["ADDRESS"]=data.ADDRESS.encode('utf-8')
                user["CITY"]=data.CITY.encode('utf-8')
                user["STATE"]=data.STATE.encode('utf-8')
                user["COUNTRY"]=data.COUNTRY.encode('utf-8')
                user["BLOOD_GP"]=bloodGroup.encode('utf-8')
                user["USERNAME"]=data.USERNAME.encode('utf-8')
                user["CONTACT"]=data.CONTACT.encode('utf-8')
                user["USEREMAIL"]=data.USEREMAIL.encode('utf-8')
                user["DATE"]=data.DATE.encode('utf-8')
            return render(request, 'cuNeedBlood.html', {"data":user})
    elif request.method == 'POST':
        LOOKUP_KEY = login_info[0].encode("utf-8")
        ZIP = request.POST['pin']
        ADDRESS = request.POST['street']
        CITY = request.POST['city']
        STATE = request.POST['state']
        COUNTRY = request.POST['country']
        BLOOD_GP = request.POST['bloodgroup']
        USERNAME = request.POST['usercontact']
        CONTACT = request.POST['contactno']       
        USEREMAIL = request.POST['emailid']
        DATE = request.POST['date']       
        LATITUDE, LONGITUDE = getLatitudeLongitude.getLatitudeLongitude(ADDRESS.strip() + ", " + CITY.strip() + ", " + STATE.strip() + ", " + COUNTRY.strip())      
        if(BLOOD_GP[-1] == '+'):
            BLOOD_GP = BLOOD_GP[0:-1]+ 'Positive'
        else:
            BLOOD_GP = BLOOD_GP[0:-1]+ 'Negative'
        enterUserNeedBloodDetails(LOOKUP_KEY, ZIP,ADDRESS,CITY,STATE,COUNTRY,BLOOD_GP,USERNAME,CONTACT,USEREMAIL,DATE,LONGITUDE,LATITUDE)
        rows = fetchHospitalsWithSameBG(BLOOD_GP)
        output = {}
        i=0
        for value in rows:
            distance = getDistanceBetweenTwoPoints.distance(float(LATITUDE), float(LONGITUDE), float(value.LATITUDE), float(value.LONGITUDE))
            if (distance <=40):
                output[i]= {'HOSPITAL_NAME':value.HOSPITAL_NAME, 'ADDRESS':value.ADDRESS, 'CITY':value.CITY, 'STATE':value.STATE,'COUNTRY':value.COUNTRY, 'CONTACT_NO':value.CONTACT_NO, 'EMAIL':value.EMAIL, 'DISTANCE':distance}
                i+=1
        sorted_output = {}
        i = 0
        for s in sorted(output.iteritems(), key=lambda (x, y): y['DISTANCE']):
            sorted_output[i] = s[1]
            i+=1
        if(output):
            return HttpResponse(str(json.dumps({'message':'success', 'data':sorted_output})))
        else:
            return HttpResponse(str(json.dumps({'message':'No hospital have this blood group available!'})))
       
def reset_password(request, id, otp):
    user = {}
    if request.method == 'GET':
        rows, time_model = get_valid_otp_object(id, otp)
        if(rows):
            timeZoneDiff = timezone.now() - rows.created_on
            if(timeZoneDiff.total_seconds() > 1800):
                user["message"] = "Your link has expired"
                return render(request, 'errorPage.html', {"data":user})
            else:
                return render(request, 'resetPassword.html', {})
        else:
            user["message"] = "You entered an Invalid Link"
            return render(request, 'errorPage.html', {"data":user})
    elif request.method == 'POST':
        rows, time_model = get_valid_otp_object(id, otp)
        if(rows):
            resetPassword = request.POST['resetPassword']
            encrypted_password = sha256_crypt.encrypt(resetPassword)
            if(sha256_crypt.verify(resetPassword, time_model.PASSWORD)):
                return HttpResponse(str(json.dumps({'message':'Old Password and New Password are same. Try another password'})))
            else:
                set_password_otp(time_model, encrypted_password)
                return HttpResponse(str(json.dumps({'message':'Password reset successfully! Please Login!'})))
        else:
            user["message"] = "You entered an Invalid Link"
            return render(request, 'errorPage.html', {"data":user})
            
def resetUser(request):
    if request.method == 'GET':
        return render(request, 'resetUser.html', {})
    elif request.method == 'POST':
        userEmail = request.POST['userEmailConfirm']
        rows = checkUser(userEmail)
        if(rows):
            id, otp, userName = create_otp(user = userEmail, purpose = 'FP')
            HOST_METHOD = getattr(settings, "HOST_METHOD", None)
            HOST_ADDRESS = getattr(settings, "HOST_ADDRESS", None)
            HOST_PORT = getattr(settings, "HOST_PORT", None)
            link = HOST_METHOD + '://' + HOST_ADDRESS + ':' + HOST_PORT + '/accounts/reset/%s/%s/' % (id,otp)
            msg_html = render_to_string('passwordRestMailTemplate.html', { 'username': userName, 'link':link})
            send_mail('Password Reset Request',"Hi",None,[userEmail],html_message=msg_html)
            return HttpResponse(str(json.dumps({'message':'Password reset Email has been sent to your link. Please reset and login!'})))
        else:
            return HttpResponse(str(json.dumps({'message':'Entered username is not registered! Please Signup!'})))
        

def cuDashboard(request):
    login_info = request.session.get('username', 'guest')
    
    if request.method == 'GET': 
        if(login_info[0].encode("utf-8")==""):
            return render(request, 'login.hmtl', {})
        else:
            user = OrderedDict() 
            user["USERNAME"]=login_info[1].encode("utf-8")
            user["USEREMAIL"]=login_info[0].encode("utf-8")
            user["CONTACT"]="".encode("utf-8")
            user["BLOOD_GP"]="".encode("utf-8")
            user["GENDER"]="".encode("utf-8")
            user["AGE"]="".encode("utf-8")
            user["ZIP"] = "".encode("utf-8")
            user["ADDRESS"]="".encode("utf-8")
            user["CITY"]="".encode("utf-8")
            user["STATE"]="".encode("utf-8")
            user["COUNTRY"]="".encode("utf-8")
            user["DONATE_Bf"]="".encode("utf-8")
            rows = GetUserDetails(login_info[0])
            if(rows):
                user["USERNAME"]=rows.USERNAME.encode("utf-8")
                user["USEREMAIL"]=rows.USEREMAIL.encode("utf-8")
                user["CONTACT"]=str(rows.CONTACT).encode("utf-8")
                user["BLOOD_GP"]=rows.BLOOD_GP.encode("utf-8")
                user["GENDER"]=rows.GENDER.encode("utf-8")
                user["AGE"]=str(rows.AGE).encode("utf-8")
                user["ZIP"]=rows.ZIP.encode("utf-8")
                user["ADDRESS"]=rows.ADDRESS.encode("utf-8")
                user["CITY"]=rows.CITY.encode("utf-8")
                user["STATE"]=rows.STATE.encode("utf-8")
                user["COUNTRY"]=rows.COUNTRY.encode("utf-8")
                user["DONATE_Bf"]=rows.DONATE_Bf.encode("utf-8")
            return render(request, 'cuDashboard.html', {"data":user})
    elif request.method == 'POST':
        rows = GetUserDetails(login_info[0])
        USERNAME = login_info[1].encode("utf-8")
        USEREMAIL = login_info[0].encode("utf-8")
        CONTACT = request.POST['contact-no']
        BLOOD_GP = request.POST['blood-group']
        GENDER = request.POST.get('gender')
        AGE = request.POST['age']
        ZIP = request.POST['zip']
        ADDRESS = request.POST['address']
        CITY = request.POST['city']
        STATE = request.POST['state']
        COUNTRY = request.POST['country']
        DONATE_Bf = request.POST.get('dbf')
        
        if (request.POST['btntype'] == 'submit'):
            if(rows):
                return HttpResponse(str(json.dumps({'message':'Details Exist! Try Reset Option'})))
            else:
                LONGITUDE, LATITUDE = getLatitudeLongitude.getLatitudeLongitude(ADDRESS.strip() + ", " + CITY.strip() + ", " + STATE.strip() + ", " + COUNTRY.strip())
                enterUserDetails(USEREMAIL, USERNAME, CONTACT,BLOOD_GP,GENDER,AGE,ZIP,ADDRESS,CITY,STATE,COUNTRY,DONATE_Bf,LONGITUDE, LATITUDE)
                return HttpResponse(str(json.dumps({'message':'success'})))
        else:
            if(rows):
                LONGITUDE, LATITUDE = getLatitudeLongitude.getLatitudeLongitude(ADDRESS.strip() + ", " + CITY.strip() + ", " + STATE.strip() + ", " + COUNTRY.strip())
                updateUserDetails(USEREMAIL, USERNAME, CONTACT,BLOOD_GP,GENDER,AGE,ZIP,ADDRESS,CITY,STATE,COUNTRY,DONATE_Bf,LONGITUDE, LATITUDE)
                return HttpResponse(str(json.dumps({'message':'success'})))
            else:
                return HttpResponse(str(json.dumps({'message':'Details dont exist! Try Submit First'})))

def login(request):
    if request.method == 'GET':
        return render(request, "login.html", {})
    elif request.method == 'POST':
        userEmail = request.POST['userEmail']
        userPassword = request.POST['userPassword']
        rows = verifyLogin(userEmail)
        if(rows):
            if(sha256_crypt.verify(userPassword, rows.PASSWORD)):
                request.session['username'] = [rows.USERNAME,rows.NAME]
                return  HttpResponse(str(json.dumps({'message':'success'}) ))
            else:
                return HttpResponse(str(json.dumps({'message':'Enter correct password'})))
        else:
            return HttpResponse(str(json.dumps({'message':'Entered username is not registered'})))
   
   
def signup(request):
    if request.method == 'GET':
        return render(request, "signup.html", {})
    elif request.method == 'POST':
        userName = request.POST['nameUser']
        userEmail = request.POST['emailUser']
        userPassword = request.POST['passwordUser']
        dept = "Volunteer"
        row = checkUser(userEmail)
        if(row):
            return HttpResponse(str(json.dumps({'message':'User Already Exists. Please login'})))
        else:
            encrypted_password = sha256_crypt.encrypt(userPassword)
            signUpUser(userEmail, userName, encrypted_password, dept)
            return HttpResponse(str(json.dumps({'message':'success'})))
    
