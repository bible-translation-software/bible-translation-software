from .models import (Book, Verse, CategoryReview, Claim, Approval, Comment, UserProfile,
    TRANSLATIONS, REVIEW_CATEGORIES, STEP_TRANSLATION, STEP_VERIFICATION,
    STEP_CHAPTER_VERIFICATION, STEP_ORAL_VERIFICATION)
from .forms import ChangeNameForm
from annoying.decorators import ajax_request
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Permission
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.forms.models import model_to_dict
from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.utils.cache import patch_cache_control
from django.utils.timezone import now
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST
from robohash import Robohash
import datetime
import json
import random
import string

NEW_USER_ACCESS = {
    'MRK': { 2: list(range(1, 17)), },
    'ROM': { 1: list(range(16, 23)), },
}

@login_required
def all_chapters(request):
    books = [model_to_dict(book) for book in Book.objects.all().order_by('book_number')]
    if not request.user.has_perm('scripturet.view_book'):
        books = [b for b in books if b["book_code"] in NEW_USER_ACCESS.keys()]

    for book in books:
        if request.user.has_perm('scripturet.view_book'):
            book["chapters_range"] = range(1, book["chapters"] + 1)
        else:
            book["chapters_range"] = sorted(NEW_USER_ACCESS[book["book_code"]].keys())

    # Simple fix just in case
    for user in get_user_model().objects.filter(userprofile=None):
        UserProfile.objects.create(user=user)

    return render(request, 'scripturet/all_chapters.html', {'books': books, 'new_user_access': NEW_USER_ACCESS})

@login_required
def chapter(request, book_code, chapter_number):
    new_user_allowed = bool(NEW_USER_ACCESS.get(book_code, {}).get(chapter_number)) and not request.user.has_perm('scripturet.view_verse')
    if not request.user.has_perms(['scripturet.view_book', 'scripturet.view_verse']):
        if not new_user_allowed:
            raise Http404()
    book = get_object_or_404(Book, book_code=book_code)
    published_verses = Verse.objects.filter(
        book=book,
        chapter_number=chapter_number,
        translation_code=settings.SCRIPTURE_DEFAULT_TRANSLATION_CODE,
        published=True,
    )

    if not request.user.has_perm('scripturet.view_verse'):
        published_verses = published_verses.filter(verse_number__in=NEW_USER_ACCESS[book_code][chapter_number])

    published_verses = list(published_verses.order_by('verse_number', 'date_created'))

    if not published_verses:
        raise Http404()

    if request.user.has_perms(['scripturet.view_book', 'scripturet.view_verse']):
        previous_verse = published_verses[0].previous_verse()
        next_verse = published_verses[-1].next_verse()
    else:
        # For easier coding:
        previous_verse = None
        next_verse = None

    rows = [{'published_verse': v} for v in published_verses]

    for row in rows:
        possible_latest_verses = Verse.objects.filter(
            book=book,
            chapter_number=chapter_number,
            verse_number=row['published_verse'].verse_number,
            translation_code=settings.SCRIPTURE_DEFAULT_TRANSLATION_CODE,
            published=False,
        )
        if not request.user.has_perm('scripturet.view_verse'):
            possible_latest_verses = possible_latest_verses.filter(approvers=request.user)
        row['verse'] = possible_latest_verses.order_by('date_created').last()
        row['verse'] = row['verse'] or row['published_verse']
        row['in_test'] = row['verse'].verse_number in NEW_USER_ACCESS.get(book_code, {}).get(chapter_number, [])

    other_versions = list(Verse.objects.filter(
        book=book,
        chapter_number=chapter_number,
        verse_number=1,
        published=True,
    ))
    other_versions.sort(key=lambda x: (list(TRANSLATIONS.keys()).index(x.translation_code), x.translation_code))

    context = {
        'book': book,
        'chapter_number': chapter_number,
        'rows': rows,
        'previous_link': reverse('scripturet:chapter', kwargs={'book_code': previous_verse.book.book_code, 'chapter_number': previous_verse.chapter_number}) if previous_verse else None,
        'next_link': reverse('scripturet:chapter', kwargs={'book_code': next_verse.book.book_code, 'chapter_number': next_verse.chapter_number}) if next_verse else None,
        'other_version_links': [{'name': ov.translation_code, 'link': ov.youversion_link(True)} for ov in other_versions],
        'new_user_allowed': new_user_allowed,
        'test_for_new_user': bool(NEW_USER_ACCESS.get(book_code, {}).get(chapter_number)),
    }
    return render(request, 'scripturet/chapter.html', context)


@login_required
def verse(request, book_code, chapter_number, verse_number):
    new_user_allowed = (verse_number in NEW_USER_ACCESS.get(book_code, {}).get(chapter_number, [])) and not request.user.has_perm('scripturet.view_verse')
    if not request.user.has_perms(['scripturet.view_book', 'scripturet.view_verse']):
        if not new_user_allowed:
            raise Http404()
    book = get_object_or_404(Book, book_code=book_code)
    youversion_verse = get_object_or_404(Verse, book=book, chapter_number=chapter_number, verse_number=verse_number, translation_code=settings.SCRIPTURE_DEFAULT_TRANSLATION_CODE, published=True)
    if request.method == "POST":
        if not request.user.has_perm('scripturet.propose_verse') and not verse_number in NEW_USER_ACCESS[book_code][chapter_number]:
            raise PermissionDenied()
        correction = Verse(
            book=book,
            chapter_number=chapter_number,
            verse_number=verse_number,
            text=request.POST["correction"],
            translation_code=settings.SCRIPTURE_DEFAULT_TRANSLATION_CODE,
            published=False,
        )
        correction.full_clean()
        correction.save()
        Approval.objects.create(
            approver=request.user,
            verse=correction,
            step=STEP_TRANSLATION,
            approved=True,
        ).full_clean()
        _check_claims_finished(book, chapter_number, verse_number)
        return redirect(
            reverse("scripturet:verse", kwargs={'book_code': book.book_code, 'chapter_number': chapter_number, 'verse_number': verse_number})
            + "#step-translation")
    other_versions = list(Verse.objects.filter(
        book=book,
        chapter_number=chapter_number,
        verse_number=verse_number,
        published=True,
    ).exclude(translation_code=settings.SCRIPTURE_DEFAULT_TRANSLATION_CODE))
    other_versions.sort(key=lambda x: (list(TRANSLATIONS.keys()).index(x.translation_code), x.translation_code))
    corrections = Verse.objects.filter(
        book=book,
        chapter_number=chapter_number,
        verse_number=verse_number,
        published=False,
        translation_code=settings.SCRIPTURE_DEFAULT_TRANSLATION_CODE,
    ).order_by('date_created')
    if not request.user.has_perm('scripturet.view_verse'):
        corrections = corrections.filter(approvers=request.user)


    claimers = {}
    if request.user.has_perm('scripturet.view_claim'):
        all_claims = Claim.objects.filter(book=book,chapter_number=chapter_number,verse_number=verse_number)
    else:
        all_claims = []
    for claim in all_claims:
        claimers.setdefault(claim.step, []).append(claim.claimer.userprofile)
    for i in range(2):
        if len(claimers.setdefault(STEP_TRANSLATION, [])) < 2:
            claimers[STEP_TRANSLATION].append(None)
    for step in [STEP_VERIFICATION, STEP_CHAPTER_VERIFICATION, STEP_ORAL_VERIFICATION]:
        if len(claimers.setdefault(step, [])) < 1:
            claimers[step] = [None]
    claimed = {}
    able_to_claim = {}
    for step in claimers.keys():
        claimer_users = [claimer.user for claimer in claimers[step] if claimer]
        claimed[step] = request.user in claimer_users
        if step == STEP_TRANSLATION:
            able_to_claim[step] = len(claimer_users) < 2
        else:
            able_to_claim[step] = len(claimer_users) < 1

    steps = [STEP_TRANSLATION, STEP_VERIFICATION, STEP_CHAPTER_VERIFICATION, STEP_ORAL_VERIFICATION]

    return render(request, 'scripturet/verse.html', {
        'youversion_verse': youversion_verse,
        'other_versions': other_versions,
        'review_categories': REVIEW_CATEGORIES,
        'original_and_corrections': [youversion_verse] + list(corrections),
        'show_diff_button': len(corrections) > 0,
        'progress_avatars': {step: youversion_verse.get_progress_avatars(steps=[step]) for step in steps},
        'claimers': claimers,
        'claimed': claimed,
        'able_to_claim': able_to_claim,
        'comments': youversion_verse.comments.all().order_by('date_created'),
        'new_user_allowed': new_user_allowed,
        'test_for_new_user': verse_number in NEW_USER_ACCESS.get(book_code, {}).get(chapter_number, []),
        'script_data': {
            'urlCategory': reverse('scripturet:ajax_submit_category'),
            'urlClaim': reverse('scripturet:ajax_claim'),
            'bookCode': youversion_verse.book.book_code,
            'chapterNumber': youversion_verse.chapter_number,
            'verseNumber': youversion_verse.verse_number,
        },
    })

@login_required
@permission_required('scripturet.propose_verse')
def team(request):
    User = get_user_model()
    perm = Permission.objects.get(codename='propose_verse')
    team_members = User.objects.filter(
        (Q(groups__permissions=perm) | Q(user_permissions=perm)) & Q(is_active=True)
    ).distinct().order_by('first_name', 'last_name', 'username')
    waiting_for_approval = User.objects.filter(is_active=True).exclude(
        Q(groups__permissions=perm) | Q(user_permissions=perm) | Q(is_superuser=True)
    ).distinct().order_by('first_name', 'last_name', 'username')
    # Note that we're deliberately ignoring superusers here among waiting_for_approval

    four_weeks_ago = now() - datetime.timedelta(weeks=4)
    approvals = Approval.objects.filter(date_created__gt=four_weeks_ago).order_by('-date_created')
    comments = Comment.objects.filter(hidden=False, date_created__gt=four_weeks_ago).order_by('-date_created')

    return render(request, 'scripturet/team.html', {
        'team_members': team_members,
        'waiting_for_approval': waiting_for_approval,
        'activity': _activity_stream(list(approvals) + list(comments)),
    })

@login_required
def team_member(request, user_pk):
    User = get_user_model()
    if not request.user.has_perm('scripturet.propose_verse') and not request.user.pk == user_pk:
        # TODO: hide inactive users too?
        raise PermissionDenied()
    team_member = User.objects.get(pk=user_pk)
    approvals = Approval.objects.filter(approver=team_member).order_by('-date_created')
    comments = Comment.objects.filter(author=team_member, hidden=False).order_by('-date_created')
    return render(request, 'scripturet/team_member.html', {
        'team_member': team_member,
        'activity': _activity_stream(list(approvals) + list(comments)),
    })

def _activity_stream(objects):
    activity = []
    for obj in objects:
        if isinstance(obj, Approval):
            activity.append({
                'user': obj.approver,
                'date_created': obj.date_created,
                'link_text': obj.verse.pretty_reference_string(),
                'link_href': obj.verse.get_absolute_url(),
            })
        elif isinstance(obj, Comment):
            if obj.content_object:
                activity.append({
                    'user': obj.author,
                    'date_created': obj.date_created,
                    'link_text': _("Comment on %s") % obj.content_object.pretty_reference_string(),
                    'link_href': obj.content_object.get_absolute_url(),
                })
            else:
                activity.append({
                    'user': obj.author,
                    'date_created': obj.date_created,
                    'link_text': _("Subcomment on %s") % obj.parent.content_object.pretty_reference_string(),
                    'link_href': obj.parent.content_object.get_absolute_url(),
                })
        else:
            raise Exception("Don't know how to deal with this type")
    activity.sort(key=lambda x: x["date_created"], reverse=True)
    return activity

@login_required
def user_profile(request):
    suggested_pics = []
    # Note: not using set5 because it is too slow
    for s in [4, 3, 2, 1]:
        for i in range(30):
            suggested_pics.append(reverse('scripturet:robohash', kwargs={
                'hash_string':  ''.join(random.choice(string.ascii_lowercase) for i in range(10)),
                'set_number': s,
            }))

    return render(request, 'scripturet/user_profile.html', {'suggested_pics': suggested_pics})

@login_required
def change_name(request):
    if request.method == "POST":
        form = ChangeNameForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _("Your name was saved succesfully. Hello %s!") % (request.user.get_full_name(),))
            return redirect(reverse('scripturet:all_chapters'))
    else:
        form = ChangeNameForm(instance=request.user)
    return render(request, 'scripturet/change_name.html', {'form': form})

@login_required
def change_profile_pic(request):
    profile = request.user.userprofile
    if request.method == "POST":
        new_url = request.POST["profile-pic-url"]
        if not new_url:
            profile.profile_pic_url = ""
        elif new_url.startswith("https://robohash.org/") or new_url.startswith("/") or new_url.startswith("https://www.gravatar.com/"):
            profile.profile_pic_url = request.build_absolute_uri(new_url)
        else:
            raise(Exception("Invalid new URL"))
        profile.full_clean()
        profile.save()
        return redirect(reverse('scripturet:thank_you_profile_pic'))
    return render(request, 'scripturet/thank_you_profile_pic.html')

@require_POST
@login_required
def release_claim(request, book_code, chapter_number, verse_number):
    if not request.user.has_perm('scripturet.handle_own_claim'):
        raise PermissionDenied()
    step = request.POST['step']
    book = Book.objects.get(book_code=book_code)
    Claim.objects.filter(
        book=book,
        chapter_number=chapter_number,
        verse_number=verse_number,
        step=step,
        claimer=request.user,
    ).delete()
    return redirect(reverse('scripturet:verse', kwargs={'book_code': book_code, 'chapter_number': chapter_number, 'verse_number': verse_number}))

@ajax_request
@login_required
def ajax_submit_category(request):
    if not request.user.has_perm('scripturet.handle_own_categoryreview'):
        raise PermissionDenied()
    inp = json.loads(request.body)
    verse = Verse.objects.get(id=inp["verseId"])
    if inp["register"]:
        (new_review, created) = CategoryReview.objects.update_or_create(
            verse=verse,
            author=request.user,
            category=inp["category"],
        )
        new_review.full_clean()
    else:
        CategoryReview.objects.filter(
            verse=verse,
            author=request.user,
            category=inp["category"],
        ).delete()
    reviews = verse.category_reviews()
    current_user_voted = False
    for review in reviews[inp["category"]]["reviews"]:
        if review.author == request.user:
            current_user_voted = True
            break
    return {
        'newCount': len(reviews[inp["category"]]["reviews"]),
        'currentUserVoted': current_user_voted,
    }

@ajax_request
@login_required
def ajax_claim(request):
    if not request.user.has_perm('scripturet.handle_own_categoryreview'):
        raise PermissionDenied()
    inp = json.loads(request.body)
    book = Book.objects.get(book_code=inp["bookCode"])
    chapter_number = inp["chapterNumber"] + 0
    verse_number = inp["verseNumber"] + 0
    step = inp["step"]
    if step == "translation":
        other_claims = Claim.objects.filter(
            book=book,
            chapter_number=chapter_number,
            verse_number=verse_number,
            step=step,
        ).exclude(claimer=request.user)
        if len(other_claims) >= 2:
            return JsonResponse({
                'error': 'max_claimers',
                'error_message': 'Maximum number of claims reached',
            }, status=400)
        (claim, _) = Claim.objects.update_or_create(
            book=book,
            chapter_number=chapter_number,
            verse_number=verse_number,
            claimer=request.user,
            step=step,
        )
        claim.full_clean()
    current_claims = Claim.objects.filter(
        book=book,
        chapter_number=chapter_number,
        verse_number=verse_number,
    )
    return {
        'current_claimers': [
            {'pic': claim.claimer.userprofile.get_profile_pic_url(), 'full_name': claim.claimer.get_full_name()}
            for claim
            in current_claims
        ],
    }

@require_POST
@login_required
def submit_correct_verse(request, verse_id):
    verse = Verse.objects.get(pk=verse_id)
    if not request.user.has_perm('scripturet.propose_verse') and \
            not verse.verse_number in NEW_USER_ACCESS.get(verse.book.book_code, {}).get(verse.chapter_number, []):
        raise PermissionDenied()
    (approval, _) = Approval.objects.update_or_create(
        approver=request.user,
        verse=verse,
        step=STEP_TRANSLATION,
        approved=True,
    )
    approval.full_clean()
    _check_claims_finished(verse.book, verse.chapter_number, verse.verse_number)
    return redirect(verse.get_absolute_url() + '#step-translation')


def _check_claims_finished(book, chapter_number, verse_number):
    # first step
    translations = Verse.objects.filter(
        book=book,
        chapter_number=chapter_number,
        verse_number=verse_number,
    ).filter(Q(published=False) | (Q(published=True) & Q(translation_code=settings.SCRIPTURE_DEFAULT_TRANSLATION_CODE)))
    step_1_finished = False
    for translation in translations:
        if translation.approvers.filter(approval__approved=True).count() >= 2:
            step_1_finished = True
            break
    if step_1_finished:
        Claim.objects.filter(
            book=book,
            chapter_number=chapter_number,
            verse_number=verse_number,
            step=STEP_TRANSLATION,
        ).update(finished=True)
    # TODO: the other steps


@login_required
@require_POST
def submit_comment_on_verse(request):
    if not request.user.has_perm('scripturet.handle_own_comment'):
        raise PermissionDenied()
    verse = Verse.objects.get(id=int(request.POST['verse']))
    comment = Comment(
        content_object=verse,
        author=request.user,
        comment_text=request.POST['comment'],
        resolved=False,
        parent=None,
    )
    comment.full_clean()
    comment.save()
    return redirect(verse.get_absolute_url() + "#comment-" + str(comment.id))

@login_required
@require_POST
def delete_comment(request):
    if not request.user.has_perm('scripturet.handle_own_comment'):
        raise PermissionDenied()
    comment = Comment.objects.get(
        id=int(request.POST['comment']),
    )
    if not request.user.has_perm('scripturet.delete_comment'):
        if comment.author != request.user:
            raise PermissionDenied()
        if not comment.recent_enough_to_delete():
            raise PermissionDenied()
    verse = comment.content_object or comment.parent.content_object
    comment.delete()
    return redirect(verse.get_absolute_url())


@login_required
@require_POST
def delete_approval(request):
    if not request.user.has_perm('scripturet.handle_own_approval'):
        raise PermissionDenied()
    approval = Approval.objects.get(id=int(request.POST['approval']))
    if not request.user.has_perm('scripturet.delete_approval'):
        if approval.approver != request.user:
            raise PermissionDenied()
        if not approval.recent_enough_to_delete():
            raise PermissionDenied()
    verse = approval.verse
    approval.delete()
    return redirect(verse.get_absolute_url())

@login_required
@require_POST
def submit_subcomment(request):
    if not request.user.has_perm('scripturet.handle_own_comment'):
        raise PermissionDenied()
    parent = Comment.objects.get(id=int(request.POST['parent']))
    comment = Comment(
        author=request.user,
        comment_text=request.POST['comment'],
        resolved=False,
        parent=parent
    )
    comment.full_clean()
    comment.save()
    return redirect(parent.content_object.get_absolute_url() + '#comment-' + str(comment.id))


def robohash(request, hash_string, set_number):
    robohash = Robohash(hash_string)
    robohash.assemble(roboset='set%d' % (set_number, ))
    response = HttpResponse(content_type='image/png')
    robohash.img.save(response, format='PNG')
    patch_cache_control(response, public=True, max_age=365 * 24 * 60 * 60, immutable=True)
    return response
