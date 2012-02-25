#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       views.py
#       
#       Copyright 2011 dominique hunziker <dominique.hunziker@gmail.com>
#       
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.
#       
#   	

from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import auth
from django.core.context_processors import csrf
from django.shortcuts import render_to_response

DOMAIN = "http://localhost/"

########################################################################

FOOTER = """The RoboEarth web interface is licensed under
      the <a href="http://www.apache.org/licenses/LICENSE-2.0">Apache
      License</a> Version 2.0. &#151; <a href="http://roboearth.informatik.uni-stuttgart.de/releases">Get</a> the source code!"""

def webpage_values(request, values={}):
    values['MainMenu'] = MainMenu(request)
    values['Footer'] = FOOTER
    values['Domain'] = DOMAIN
    values.update(csrf(request))
    return values

def MainMenu(request):
    """ This is the main menu, shown at every webpage """
    documentation = '<li class="topmenu"><a href="/documentation">Documentation</a></li><!--<li class="topmenu"><a href="/about">About</a></li>-->'
    generic_profil = """
    <ul>
    <li class="submenu"><a href="/profile">My Profile</a></li>
    <li class="submenu"><a href="/subscriptions">My Subscriptions</a></li>
    <li class="submenu"><a href="/myrobots">My Robots</a></li>
    <li class="submenu"><a href="/newsfeed">Newsfeed</a></li>
    """
    super_user = '<li class="submenu"><a href="/accounts/manage">User Management</a></li>'
    logout = '<li class="submenu"><a href="/logout">Logout</a></li>'


    if request.user.is_authenticated():
        user = '<li class="topmenu"><a href="">'+request.user.username+'</a>'+generic_profil
        if request.user.is_superuser:
            user = user + super_user
        user = user + logout + '</ul></li>'
    else:
        user = """
        <li class="topmenu"><a href="/register">Register</a></li>
        <li class="topmenu"><a href="/login">Login</a></li>
        """

    public = """
        <li class="topmenu"><a href="">Search</a>
        <ul>
          <li class="submenu"><a href="/recipes/request">Action Recipes</a></li>
          <li class="submenu"><a href="/objects/request">Objects</a></li>
          <li class="submenu"><a href="/environments/request">Environments</a></li>        
          <li class="submenu"><a href="/robots/request">Robots</a></li>
          <li class="submenu"><a href="/serql">SeRQL Console</a></li>
            <!--<li><a href="/locations/objects/request">Objects</a></li>-->
        </ul></li>
      """
    private = """
        <li class="topmenu"><a href="">Submit</a>
        <ul>
          <li class="submenu"><a href="/recipes">Action Recipe</a></li>
          <li class="submenu"><a href="/objects">Object</a></li>
          <li class="submenu"><a href="/environments">Environments</a></li>
          <li class="submenu"><a href="/robots">Robots</a></li>
            <!--<li><a href="/locations/objects">Objects</a></li>-->
        </ul></li>
     """

    
    if request.user.is_authenticated():
        return '<ul>'+public + private + documentation + user+'</ul>'
    else:
        return '<ul>'+public + documentation + user+'</ul>'

########################################################################

def webpage_values_(request, values={}):
    values['MainMenu'] = '' #MainMenu(request)
    values['Footer'] = '' #FOOTER
    values['Domain'] = DOMAIN
    values.update(csrf(request))
    return values

def loginForm(request, error=False):
    """ show login form """
    if request.user.is_authenticated():
        return HttpResponseRedirect("/")
    
    values = {'error' : error}
    
    return render_to_response('login.html', webpage_values(request,values))

def login(request):
    """ authenticate a user. The user has to provide his user name and password """
    username = request.POST['username']
    password = request.POST['password']
    user = auth.authenticate(username=username, password=password)
    if user is not None and user.is_active:
        # Correct password, and the user is marked "active"
        auth.login(request, user)
        # Redirect to a success page.
        return HttpResponseRedirect("/")
    else:
        # Show an error page
        return HttpResponse(loginForm(request, error=True))

def startPage(request):
    """ show start page """
    template = loader.get_template('index.html')
    webpage_values = Context(roboearth.webpage_values(request))
    
    return template.render(webpage_values)

def index(request):
    return render_to_response('index.html', webpage_values(request,{}))