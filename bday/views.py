from django.shortcuts import render, redirect
import datetime
from django.http import HttpResponse
import json
import secrets
import requests
from django.utils import timezone
from models import Doctor

#fuction to refresh tokens once they have expired
def refresh_tokens(doctor):
    response = requests.post("https://drchrono.com/o/token/", data={
                             "grant_type":    "refresh_token",
                             "client_id":     secrets.client_id,
                             "client_secret": secrets.client_secret,
                             "refresh_token": doctor.refresh_token,
                             "redirect_uri":  "http://127.0.0.1:8000/auth",
                             }).json()
    return response

#function to get a list of patients
def get_patients(doctor):
    if doctor.expires < timezone.now():                     #checks if the tokens have expired
        tokens = refresh_tokens(doctor)                     #refresh expired tokens
        doctor.access_token = tokens["access_token"]
        doctor.refresh_token = tokens["refresh_token"]
        doctor.expires = datetime.datetime.now() + datetime.timedelta(seconds=new_tokens["expires_in"])
        doctor.save()
    
    patients = []
    response = requests.get("https://drchrono.com/api/patients", headers={
                            "Authorization": "Bearer " + doctor.access_token
                            }).json()
    while True:                                             #iterate through responses to get the patients in a list
        patients.extend(response["results"])
        if response["next"] is None:
            break
        response = requests.get(patients["next"],headers={
                        "Authorization": "Bearer " + doctor.access_token
                        }).json()
    return patients

#checks if the patient has a birthday today or not
def is_birthday(patient):
    if patient["date_of_birth"] is None:                    #if daate of birth not provided
        return False
    date = patient["date_of_birth"].split("-")
    return int(date[1]) == datetime.datetime.now().month and int(date[2]) == datetime.datetime.now().day


#primary view function
def index(request):
    if 'user' in request.session:
        doctor = Doctor.objects.get(pk = request.session['user'])
        patients = filter(is_birthday, get_patients(doctor))  #filters patients who have birthday today
        context = {
                "patients": patients
        }
        return render(request, "bday/patients.html", context) # renders patients page for patients with birthdays

    context = {
        "client_id": secrets.client_id,
    }
    return render(request, "bday/index.html", context)        #renders login page with client-id

#authorisation function, the API redirects to this function
def auth(request):
    code =request.GET.get("code", "")
    tokens = requests.post("https://drchrono.com/o/token/", data= {    #get tokens
                           "grant_type":"authorization_code",
                           "client_id":     secrets.client_id,
                           "client_secret": secrets.client_secret,
                           "code":          code,
                           "redirect_uri":  "http://localhost:8000/auth",
                           }).json()
    expires = datetime.datetime.now() + datetime.timedelta(seconds=tokens["expires_in"])
    doctor = Doctor.objects.create(                            #store doctor in database
            access_token  = tokens["access_token"],
            refresh_token = tokens["refresh_token"],
            expires       = expires,
    )
    doctor.save()
    request.session['user'] = doctor.pk
    return redirect("/")