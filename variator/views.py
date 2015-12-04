#-*- coding=utf-8 -*-

from django.shortcuts import HttpResponse

def index(request):
  return HttpResponse("Halla gangster går det bra på Stiklestad. RE RE RE RE RE")
