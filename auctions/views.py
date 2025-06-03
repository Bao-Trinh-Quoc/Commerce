from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from .models import User
from .models import Listing
from .models import Bid
from .models import Comment
from .forms import ListingForm

def index(request):
    listings = Listing.objects.filter(active=True)
    for listing in listings:
        highest_bid = listing.bids.order_by('-amount').first()
        listing.current_price = highest_bid.amount if highest_bid else listing.starting_bid
    return render(request, "auctions/index.html", {
        "listings": listings
    })

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")

def listing_detail(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    highest_bid = listing.bids.order_by('-amount').first()
    listing.current_price = highest_bid.amount if highest_bid else listing.starting_bid
    
    winner = None
    if not listing.active and highest_bid:
        winner = highest_bid.bidder

    # Handle comment
    comment_error = None
    if request.method == "POST" and "comment" in request.POST:
        if request.user.is_authenticated:
            content = request.POST.get("comment", "").strip()
            if content:
                Comment.objects.create(
                    listing=listing,
                    commentor=request.user,
                    content=content
                )
                return redirect('listing_detail', listing_id=listing_id)
            else:
                comment_error = "Comment cannot be empty"
        else:
            comment_error = "You must be logged in to comment"

    comments = listing.comments.order_by('-timestamp')
    return render(request, "auctions/listing_detail.html", {
        "listing": listing,
        "winner": winner,
        "comments": comments,
        "comment_error": comment_error
    })

def categories(request):
    categories = Listing.objects.values_list('category', flat=True).distinct()
    return render(request, "auctions/categories.html", {
        "categories": categories
    })

def category_listings(request, category):
    listings = Listing.objects.filter(category=category, active=True)
    for listing in listings:
        highest_bid = listing.bids.order_by('-amount').first()
        listing.current_price = highest_bid.amount if highest_bid else listing.starting_bid
    return render(request, "auctions/category_listings.html", {
        "category": category,
        "listings": listings
    })

@login_required
def create_listing(request):
    if request.method == "POST":
        form = ListingForm(request.POST)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.owner = request.user
            listing.save()
            return HttpResponseRedirect(reverse("index"))
    else:
        form = ListingForm()
    return render(request, "auctions/create_listing.html", {"form": form})

@login_required
def toggle_watchlist(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    if listing in request.user.watchlist.all():
        request.user.watchlist.remove(listing)
    else:
        request.user.watchlist.add(listing)

    return redirect('listing_detail', listing_id=listing_id)

@login_required
def bid_item(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    highest_bid = listing.bids.order_by('-amount').first()
    listing.current_price = highest_bid.amount if highest_bid else listing.starting_bid

    if request.method == "POST":
        # Check if user is the owner of the listing
        if request.user == listing.owner:
            error = "You cannot bid on your own listing."
            return render(request, "auctions/listing_detail.html", {
                "listing": listing,
                "bid_error": error
            })
        # get bid amount from post
        try:
            bid_amount = float(request.POST["bid"])
        except (KeyError, ValueError):
            bid_amount = None
    
        # Validation
        if bid_amount is None:
            error = "Invalid bid amount"
        elif bid_amount < listing.starting_bid:
            error = "Bid must be at least the starting bid"
        elif highest_bid and bid_amount <= highest_bid.amount:
            error = "Bid must be greater than the current highest bid"
        else:
            # Save the new bid
            Bid.objects.create(
                listing = listing,
                bidder = request.user,
                amount = bid_amount
            )
            return redirect('listing_detail', listing_id=listing_id)

        # If error
        return render(request, "auctions/listing_detail.html", {
            "listing": listing,
            "bid_error": error
        })

    return redirect('listing_detail', listing_id=listing_id)        

@login_required
def close_listing(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    # Backend check
    if request.user != listing.owner or not listing.active:
        return redirect('listing_detail', listing_id=listing_id)
    if request.method == "POST":
        listing.active = False
        listing.save()
    
    return redirect('listing_detail', listing_id=listing_id)

@login_required
def watchlist(request):
    listings = request.user.watchlist.all()
    for listing in listings:
        highest_bid = listing.bids.order_by('-amount').first()
        listing.current_price = highest_bid.amount if highest_bid else listing.starting_bid

    return render(request, "auctions/watchlist.html", {
        "listings": listings
    })