# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.core.serializers import serialize
from django.shortcuts import render
from django.http import HttpResponse
from django.core.mail import send_mail
from django.template.loader import render_to_string
import json
from collections import OrderedDict
from models import *
from django.http import JsonResponse
import json
import datetime
from django.utils import timezone
from login.distanceLongitudeLatitude import getLatitudeLongitude, getDistanceBetweenTwoPoints
from operator import itemgetter
from django.conf import settings
from datetime import date
# Create your views here.

path = getattr(settings, "CSV_FOLDER", None) +'CountryToCodeMapping.csv'
CountryToCodeMappingFile = open(path, "r")
CountryToCodeMapping = {}
for rows in CountryToCodeMappingFile:
    rows = rows[0:-1].decode('UTF-8')
    fullForm, ShortForm = rows.split("|")
    CountryToCodeMapping[fullForm] = ShortForm

def network(request):
    return render(request, 'homePage.html', {})

    
def hpbloodMonitor(request):    
    dummy = "mercy_71"
    hosp_id = int(dummy.split("_")[-1])
    rows_hosp = GetHospitalDetails(hosp_id)
    rows2 = GetBloodDonorDataforHospId(hosp_id)
    row_data = list(rows2)
    rows_hosp_list = [rows_hosp]
    json_data = serialize('json', row_data)
    json2 = serialize('json', rows_hosp_list) 
    
    return render(request, 'hpBloodMonitor.html', {"data_hosp":json2,"data_comb":json_data})    
    

def hpDashboard(request):
    dummy = "mercy_71"
    hosp_id = int(dummy.split("_")[-1])
    rows_hosp = GetHospitalDetails(hosp_id)
    rows2 = GetBloodDonorDataforHospId(hosp_id)
    row_data = list(rows2)
    rows_hosp_list = [rows_hosp]
    json_data = serialize('json', row_data)
    json2 = serialize('json', rows_hosp_list)  
    donor_list = []
    if(rows_hosp):
        country_lookup = rows_hosp.COUNTRY
        if (rows_hosp.COUNTRY in CountryToCodeMapping.keys()):
                country_lookup = CountryToCodeMapping[rows_hosp.COUNTRY].strip()
                today_date = str(date.today())
                print(today_date)
                #Removing status param
                #status = 0
                data_row = getRightDonors(country_lookup)
                print type(data_row)
                
                if(data_row):
                        for value in data_row:
                            distance = getDistanceBetweenTwoPoints.distance(float(rows_hosp.LATITUDE), float(rows_hosp.LONGITUDE), float(value.LATITUDE), float(value.LONGITUDE))
                            if (distance <=100):
                                distance = round(distance, 2)
                                donor_list.append(value)
  
        
    return render(request, 'hpDashboard.html', {"data_hosp":json2,"data_comb":json_data,"pred_don":serialize('json', donor_list)})    
    
    

def topDonors(request):
    
    if request.method == 'GET':
        dummy = "mercy_71"
        hosp_id = int(dummy.split("_")[-1])
        rows_hosp = GetHospitalDetails(hosp_id)
        donor_list = []
        if(rows_hosp):
            country_lookup = rows_hosp.COUNTRY
            if (rows_hosp.COUNTRY in CountryToCodeMapping.keys()):
                    country_lookup = CountryToCodeMapping[rows_hosp.COUNTRY].strip()
                    today_date = str(date.today())
                    print(today_date)
                    #Removing status param
                    #status = 0
                    rows = getRightDonors(country_lookup)

                    if(rows):
                            for value in rows:
                                distance = getDistanceBetweenTwoPoints.distance(float(rows_hosp.LATITUDE), float(rows_hosp.LONGITUDE), float(value.LATITUDE), float(value.LONGITUDE))
                                if (distance <=100):
                                    distance = round(distance, 2)
                                    donor_list.append(value)
        json_object = serialize('json', donor_list)
        print json_object
        return render(request, 'hpDonorList.html', {"data":rows,"data_json":json_object})

def sendemail(request):        
    if request.method == 'GET':
        msg_html = render_to_string('DonorReachOut.html', { 'email': request.GET['email'], 'bloodgroup':request.GET['bloodgroup']})
        send_mail('Blood Required Urgently',"Hi",None,[request.GET['email']],html_message=msg_html)
        return HttpResponse(str(json.dumps({'message':'Donor Reachout Email has been sent!'})))    
        
def sendRewards(request):        
    if request.method == 'GET':
        msg_html = render_to_string('sendVouchers.html', { 'email': request.GET['email']})
        send_mail('Reward',"Hi",None,[request.GET['email']],html_message=msg_html)
        return HttpResponse(str(json.dumps({'message':'Reward mail has been sent!'})))   

def reward(request):        
    if request.method == 'GET':
        dummy = "mercy_71"
        hosp_id = int(dummy.split("_")[-1])
        rows = GetBloodDonorDataforReward(hosp_id)
        json_object = serialize('json', rows)
        print json_object
        return render(request, 'hpRewardList.html', {"data":rows,"data_json":json_object})        