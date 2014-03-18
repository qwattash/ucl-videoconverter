#!/usr/bin/python

from django import forms

class UploadFileForm(forms.Form):
    target = forms.FileField()
