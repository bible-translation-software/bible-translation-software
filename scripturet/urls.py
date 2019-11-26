from django.urls import path
from . import views

app_name = 'scripturet'

urlpatterns = [
    path('', views.all_chapters, name='all_chapters'),
    path('profile/', views.user_profile, name='user_profile'),
    path('profile/pic_set/', views.change_profile_pic, name='thank_you_profile_pic'),
    path('profile/change_name/', views.change_name, name='change_name'),
    path('team/', views.team, name='team'),
    path('team/<int:user_pk>', views.team_member, name='team_member'),
    path('submit_correct/<int:verse_id>/', views.submit_correct_verse, name='submit_correct_verse'),
    path('submit_comment_on_verse/', views.submit_comment_on_verse, name='submit_comment_on_verse'),
    path('submit_subcomment/', views.submit_subcomment, name='submit_subcomment'),
    path('delete_comment/', views.delete_comment, name='delete_comment'),
    path('delete_approval/', views.delete_approval, name='delete_approval'),
    path('robohash/<hash_string>/<int:set_number>/', views.robohash, name='robohash'),

    path('b/<book_code>/<int:chapter_number>/', views.chapter, name='chapter'),
    path('b/<book_code>/<int:chapter_number>/<int:verse_number>/', views.verse, name='verse'),
    path('b/<book_code>/<int:chapter_number>/<int:verse_number>/release_claim', views.release_claim, name='release_claim'),

    path('!category/', views.ajax_submit_category, name='ajax_submit_category'),
    path('!claim/', views.ajax_claim, name='ajax_claim'),
]
