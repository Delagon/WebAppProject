from django.shortcuts import render
from django.http import HttpResponse
from Tetris.models import *
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required
from Tetris.forms import *
from django.contrib.sites.shortcuts import get_current_site
import time

def pieceGen(seed):
    context_dict={}
    # IMPORTANT #
    # NUMBER BELLOW HOW DEEP TO GO #
    # EDIT FOR BALANCING #
    nopiecestotake = 100
    #-----------------#
    f = file("piecelist.txt")
    line = f.readline()
    f.close()
    pieces = ""
    frontno = 1
    #-----------------#
	#Reading the randomised pieces list from the file.
    f = file("piecelist.txt")
    line = f.readline()
    f.close()
    # Make it MUCH easier to compute, might change later if we come up with a more effecit calc
    if seed.lower() == "dailychallenge":
        day = time.strftime("%c").split()
        s = day[0] + day[1] + day[-1]
        a = int(day[2])
        for i in s:
            frontno *= (ord(i) + a)
            if frontno > 1000007:
                frontno %= 1000007
    else:
        if len(seed) > 30:
            seed = seed[:30]
        for i in seed:
            frontno *= ord(i)
            while frontno >= 1000007:
                frontno -= 1000007
    pointer = frontno
    while len(pieces) < nopiecestotake:
        if pointer >= 1000007:
            pointer %= 1000007
        pieces += line[pointer]
        pointer += frontno
    returnPieces = ""
    for p in pieces:
        returnPieces+=str(p)+","
    context_dict = {'seed':seed, 'pieces':returnPieces[:-1]}
    return context_dict

def index(request):
    score_list = Score.objects.order_by('-score')[:5]
    context_dict = {'scores':score_list}
    latest_leaderboard = Leaderboard.objects.order_by('-creation_date')[:5]
    context_dict['latest'] = latest_leaderboard
    return render(request, 'Tetris/index.html', context_dict)

def play(request):
    #TODO RETURN PAGE
    seed = str(int(time.time()*1000000)) * 2
    current_site=get_current_site(request)
    context_dict = pieceGen(seed)
    context_dict['site']=current_site
    return render(request, 'Tetris/play.html', context_dict)


def game(request, seed):
    current_site=get_current_site(request)
    context_dict = pieceGen(seed)
    context_dict['site']=current_site
    return render(request, 'Tetris/play.html', context_dict)

def about(request):
    return render(request, 'rango/about.html')

def register(request):

    # A boolean value for telling the template whether the registration was successful.
    # Set to False initially. Code changes value to True when registration succeeds.
    registered = False

    # If it's a HTTP POST, we're interested in processing form data.
    if request.method == 'POST':
        # Attempt to grab information from the raw form information.
        # Note that we make use of both UserForm and UserProfileForm.
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        # If the two forms are valid...
        if user_form.is_valid() and profile_form.is_valid():
            # Save the user's form data to the database.
            user = user_form.save()

            # Now we hash the password with the set_password method.
            # Once hashed, we can update the user object.
            user.set_password(user.password)
            user.save()

            # Now sort out the UserProfile instance.
            # Since we need to set the user attribute ourselves, we set commit=False.
            # This delays saving the model until we're ready to avoid integrity problems.
            profile = profile_form.save(commit=False)
            profile.user = user

            # Did the user provide a profile picture?
            # If so, we need to get it from the input form and put it in the UserProfile model.
            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            # Now we save the UserProfile model instance.
            profile.save()

            # Update our variable to tell the template registration was successful.
            registered = True

        # Invalid form or forms - mistakes or something else?
        # Print problems to the terminal.
        # They'll also be shown to the user.
        else:
            print user_form.errors, profile_form.errors

    # Not a HTTP POST, so we render our form using two ModelForm instances.
    # These forms will be blank, ready for user input.
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()

@login_required
def user_logout(request):
    # Since we know the user is logged in, we can now just log them out.
    logout(request)

    # Take the user back to the homepage.
    return HttpResponseRedirect('/')

def user_login(request):
        # If the request is a HTTP POST, try to pull out the relevant information.
    if request.method == 'POST':
        # Gather the username and password provided by the user.
        # This information is obtained from the login form.
        username = request.POST['username']
        password = request.POST['password']

        # Use Django's machinery to attempt to see if the username/password
        # combination is valid - a User object is returned if it is.
        user = authenticate(username=username, password=password)

        # If we have a User object, the details are correct.
        # If None (Python's way of representing the absence of a value), no user
        # with matching credentials was found.
        if user:
            # Is the account active? It could have been disabled.
            if user.is_active:
                # If the account is valid and active, we can log the user in.
                # We'll send the user back to the homepage.
                login(request, user)
                return HttpResponseRedirect('/Tetris/')
            else:
                # An inactive account was used - no logging in!
                return HttpResponse("Your Tetris account is disabled.")
        else:
            # Bad login details were provided. So we can't log the user in.
            print "Invalid login details: {0}, {1}".format(username, password)
            return render(request, "Tetris/login.html", {"message":"Your username or Password was incorrect."})

    # The request is not a HTTP POST, so display the login form.
    # This scenario would most likely be a HTTP GET.
    else:
        # No context variables to pass to the template system, hence the
        # blank dictionary object...
        return render(request, 'Tetris/login.html', {})

@login_required
def userpage(request):
    user = User.objects.get(username=request.user.username)
    context_dict = {}
    try:
        userprofile = UserProfile.objects.get(user=user)
    except:
        userprofile = None

    context_dict['user'] = user
    context_dict['userprofile'] = userprofile
    context_dict['scores'] =  Score.objects.filter(user= user).order_by('-score')[:5]
    context_dict['edit'] = True
    return render(request, 'Tetris/userpage.html', context_dict)

def otherpage(request, uname):
    context_dict = {}
    try:
        u = User.objects.get(username=uname)
        topScores = Score.objects.filter(user = u).order_by('-score')
        if len(topScores) > 5:
            topScores = topScores[:5]
        up = UserProfile.objects.get(user = u)
    except:
        u = None
        topScores = None
        up = None
    context_dict['user'] = u
    context_dict['userprofile'] = up
    context_dict['scores'] = topScores
    context_dict['edit'] = False
    return render(request, 'Tetris/userpage.html', context_dict)

@login_required
def edit_profile(request):
    try:
           profile = request.user.userprofile
    except UserProfile.DoesNotExist:
           profile = UserProfile(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES or None, instance=profile)
        if form.is_valid():
            form.save()
            return index(request)
    else:
           form = UserProfileForm(instance=profile)
    return render(request, 'Tetris/edit_profile.html', {'form': form})


def challenge(request, seed, u):
    #Gets best score from user
    leaderboard = Leaderboard.objects.get(seed=seed)
    user = User.objects.get(username=u)
    bestScore = Score.objects.filter(leaderboard=leaderboard).filter(user=user).order_by('-score')[0]
    context_dict = pieceGen(seed)
    context_dict['score'] = bestScore.score
    leaderboard.addChallenge()
    leaderboard.save()
    context_dict['challenger']=user.username
    current_site=get_current_site(request)
    context_dict['site']=current_site

    return render(request,'Tetris/play.html',context_dict)


@login_required
def score(request, seed, score):
    l = Leaderboard.objects.get_or_create(seed=seed)[0]
    l.addPlay()
    l.save()
    u =  User.objects.get(username=request.user.username)
    s = Score.objects.get_or_create(leaderboard=l,user = u, score = int(score))[0]
    bestScore = Score.objects.filter(leaderboard=l).filter(user=u).order_by('-score')[0]
    context_dict={'score':s.score,'seed':seed,'bestScore':bestScore.score,'user':u.username}
    current_site=get_current_site(request)
    context_dict['site']=current_site
    return render(request,'Tetris/score.html',context_dict)


def seedleaderboard(request, seed):
    l = Leaderboard.objects.get_or_create(seed = seed)[0]
    scores = Score.objects.filter(leaderboard = l).order_by('-score')
    try:
        u = User.objects.get(username = request.user.username)
        bestScore = Score.objects.filter(leaderboard=l).filter(user=u).order_by('-score')[0]
    except:
        u = None
        bestScore = None
    context_dict = {'scores':scores,'best':bestScore,'seed':seed}
    return render(request,'Tetris/seedLeaderboard.html',context_dict)

def leaderboard(request):
   score_list = Score.objects.order_by('-score')[:10]
   context_dict = {'scores':score_list}
   top_leaderboard = Leaderboard.objects.order_by('-plays')[:15]
   context_dict['top'] = top_leaderboard
   return render(request,'Tetris/leaderboard.html',context_dict)

#By far the best part of the project 
#If the user mistypes the url, this will attemept to redirect them to the page they were looking for
#Very simple algorithm, just checks how closes to any given word it is, then, if it is at least 50%, renders the appriorate view
#If none, checks again, this time taking into accont missing letters etc.
def error404(request):
    s = request.path.split('/')[-1]
    pages = {'index':0,'play':0,'game':0,'about':0,'userpage':0,'daily':0,'challenge':0,'leaderboard':0,'login':0,'register':0,'logout':0}
    k = pages.keys()
    for i in s:
        for u in k:
            if pages[u] < len(u):
                if i == u[pages[u]]:
                    pages[u] += 1
    for u in k:
        pages[u] = (1.0*pages[u])/len(u)
    pages['404'] = 0.5
    m = '404'
    for u in k:
        if pages[u] > pages[m]:
            m = u
    if m == '404':
        for u in k:
            pages[u] = [0]*len(u) + [0]
        for i in s:
            for u in k:
                if pages[u][-1] < len(u):
                    for t in range(pages[u][-1],len(u)):
                        if u[t] == i and pages[u][t] != 1:
                            pages[u][-1] = t
                            pages[u][t] = 1
                            break
        for u in k:
            n = 0.0
            for i in pages[u][:-1]:
                n += i
            pages[u] = 1.0*n/len(s)
            pages[m] = 0.5
        for u in k:
            if pages[u] > pages[m]:
                m = u
    if m == 'leaderboard':
        return leaderboard(request)
    elif m == 'challenge' or m == 'daily':
        return game(request,'dailychallenge')
    elif m == 'game' or m == 'play':
        return play(request)
    elif m == 'about' or m == 'index':
        return index(request)
    elif m == 'userpage':
        return userpage(request)
    elif m == 'login':
        return user_login(request)
    elif m == 'logout':
        return user_logout(request)
    elif m == 'register':
        return register(request)
    else:
        return render(request,'Tetris/error404.html')
