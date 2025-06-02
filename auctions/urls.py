from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create_listing", views.create_listing, name="create_listing"),
    path("listing/<int:listing_id>/", views.listing_detail, name="listing_detail"),
    path("listing/<int:listing_id>/watchlist/", views.toggle_watchlist, name="toggle_watchlist"),
    path("listing/<int:listing_id>/bid/", views.bid_item, name="bid_item"),
    path("listing/<int:listing_id>/close/", views.close_listing, name="close_listing"),
    path("watchlist/", views.watchlist, name="watchlist"),
    path("categories", views.categories, name="categories"),
    path("categories/<str:category>/", views.category_listings, name="category_listings"),
]
