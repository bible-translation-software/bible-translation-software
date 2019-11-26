from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.shortcuts import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from urllib.parse import urlencode
from .shared import auto_paragraphs
import copy
import datetime
import hashlib
import re


STEP_TRANSLATION = 'translation'
STEP_VERIFICATION = 'verification'
STEP_CHAPTER_VERIFICATION = 'chapter_verification'
STEP_ORAL_VERIFICATION = 'oral_verification'
STEP_CHOICES = [
    (STEP_TRANSLATION, _("Translation")),
    (STEP_VERIFICATION, _("Verification")),
    (STEP_CHAPTER_VERIFICATION, _("Chapter verification")),
    (STEP_ORAL_VERIFICATION, _("Oral verification")),
]
REVIEW_CATEGORIES = {
    "typo"        : { "fa": "fas fa-print"        , "name": _("Typo")},
    "clarity"     : { "fa": "fas fa-surprise"     , "name": _("Unclear")},
    "phrasing"    : { "fa": "fas fa-arrows-alt-h" , "name": _("Phrasing")},
    "theology"    : { "fa": "fas fa-cross"        , "name": _("Theology")},
    "meaning"     : { "fa": "fas fa-lightbulb"    , "name": _("Wrong meaning")},
    "terms"       : { "fa": "fas fa-book"         , "name": _("Incorrect key term")},
    "diacritics"  : { "fa": ""                    , "name": _("Incorrect diacritics")},
    "punctuation" : { "fa": ""                    , "name": _("Punctuation")},
    "region"      : { "fa": "fas fa-globe-africa" , "name": _("Wrong regional accent")},
}
TRANSLATIONS = {
    "KJV": {"lang": "en", "youversion_number": 1},
}

def validate_uppercase(value):
    if value.upper() != value:
        raise ValidationError(_('%(value)s is not uppercase'), params={'value': value})


class BookManager(models.Manager):
    def get_by_natural_key(self, book_code):
        return self.get(book_code=book_code)

class Book(models.Model):
    book_code = models.CharField(max_length=3, unique=True, validators=[validate_uppercase])
    book_name = models.CharField(max_length=1024, unique=True)
    book_number = models.IntegerField(unique=True)
    chapters = models.IntegerField()

    objects = BookManager()

    def __str__(self):
        return self.book_name

    class Meta:
        ordering = ['book_number']


class Verse(models.Model):
    translation_code = models.CharField(max_length=3, validators=[validate_uppercase])
    book = models.ForeignKey('Book', on_delete=models.PROTECT)
    chapter_number = models.IntegerField()
    verse_number = models.IntegerField()
    text = models.TextField()
    published = models.BooleanField(default=False)
    date_created = models.DateTimeField(default=timezone.now)
    approvers = models.ManyToManyField(settings.AUTH_USER_MODEL, through='Approval')
    comments = GenericRelation('Comment')

    def __str__(self):
        return "%s %d:%d (%s)" % (self.book.book_code, self.chapter_number, self.verse_number, self.translation_code)

    def get_absolute_url(self):
        return reverse('scripturet:verse', kwargs={
            'book_code': self.book.book_code,
            'chapter_number': self.chapter_number,
            'verse_number': self.verse_number
        })

    def pretty_reference_string(self):
        return "%s %d : %d" % (self.book.book_name, self.chapter_number, self.verse_number)

    def approver_profiles(self):
        return [user.userprofile for user in self.approvers.all()]

    def category_reviews(self):
        all_reviews = CategoryReview.objects.filter(verse=self)
        reviews = copy.deepcopy(REVIEW_CATEGORIES)
        for category, data in reviews.items():
            data["reviews"] = []
            data["approvers"] = set()
        for review in all_reviews:
            reviews[review.category]["reviews"].append(review)
            reviews[review.category]["approvers"].add(review.author)
        return reviews

    def next_verse(self):
        verse = (Verse.objects
            .filter(translation_code=self.translation_code)
            .filter(published=self.published)
            .filter(
                (Q(book=self.book) & Q(chapter_number=self.chapter_number) & Q(verse_number__gt=self.verse_number))
                | (Q(book=self.book) & Q(chapter_number__gt=self.chapter_number))
                | Q(book__gt=self.book)
            )
            .order_by('book', 'chapter_number', 'verse_number')
            .first())
        return verse

    def previous_verse(self):
        verse = (Verse.objects
            .filter(translation_code=self.translation_code)
            .filter(published=self.published)
            .filter(
                (Q(book=self.book) & Q(chapter_number=self.chapter_number) & Q(verse_number__lt=self.verse_number))
                | (Q(book=self.book) & Q(chapter_number__lt=self.chapter_number))
                | Q(book__lt=self.book)
            )
            .order_by('-book', '-chapter_number', '-verse_number')
            .first())
        return verse

    def same_reference_as(self, other_verse):
        return (self.book == other_verse.book and self.chapter_number == other_verse.chapter_number
            and self.verse_number == other_verse.verse_number)

    def youversion_link(self, for_chapter=False):
        if for_chapter:
            return "https://www.bible.com/%s/bible/%d/%s.%d" % (
                self.lang(), TRANSLATIONS[self.translation_code]["youversion_number"], self.book.book_code,
                self.chapter_number,
            )
        else:
            return "https://www.bible.com/%s/bible/%d/%s.%d.%d" % (
                self.lang(), TRANSLATIONS[self.translation_code]["youversion_number"], self.book.book_code,
                self.chapter_number, self.verse_number
            )

    def lang(self):
        return TRANSLATIONS[self.translation_code]["lang"]

    def dir(self):
        if self.lang() == "ar":
            return "rtl"
        return "ltr"


    def get_equivalent_published_verse(self):
        equivalent_verse = Verse.objects.get(
            book=self.book,
            chapter_number=self.chapter_number,
            verse_number=self.verse_number,
            translation_code=self.translation_code,
            published=True,
        )
        return equivalent_verse

    def get_most_approved_equivalent_verse(self):
        equivalent_verses = list(Verse.objects.filter(
            book=self.book,
            chapter_number=self.chapter_number,
            verse_number=self.verse_number,
            translation_code=self.translation_code,
        ))
        if not equivalent_verses:
            return
        equivalent_verses.sort(key=lambda x: (
            x.approval_set.filter(step=STEP_TRANSLATION, approved=True).count(),
            not x.published,
            x.date_created,
        ))
        return equivalent_verses[-1]

    def get_progress_avatars(self, steps=None):
        """If steps is None, then return all steps"""
        # TODO: this needs to be modified to handle new users
        if steps is None:
            steps = [STEP_TRANSLATION, STEP_VERIFICATION, STEP_CHAPTER_VERIFICATION, STEP_ORAL_VERIFICATION]
        rv = []
        most_approved_verse = self.get_most_approved_equivalent_verse()
        for step in steps:
            if step == STEP_TRANSLATION:
                count = 2
            else:
                count = 1
            added = []
            approvers = most_approved_verse.approvers.filter(approval__step=step).order_by('approval__date_created')[:count]
            for approver in approvers:
                added.append({
                    'checked': True,
                    'claimed': False,
                    'user': approver,
                })
            # Currently, we're disabling the claim functionality altogether

            # claims = list(Claim.objects.filter(
            #     book=self.book,
            #     chapter_number=self.chapter_number,
            #     verse_number=self.verse_number,
            #     step=step,
            #     finished=False,
            # ).order_by('date_created')[:count-len(added)])
            # for claim in claims:
            #     if claim.claimer not in set(x["user"] for x in added):
            #         added.append({
            #             'checked': False,
            #             'claimed': True,
            #             'user': claim.claimer,
            #         })
            rv.extend(added)
            rv.extend([None] * (count - len(added)))
        return rv

    @classmethod
    def filter_by_string(klass, string):
        match = re.search(r'^([a-zA-Z]{3})\s*(\d+)\s*:\s*(\d+)\s([a-zA-Z]+)$', string)
        if match:
            return klass.objects.filter(
                book__book_code=match.group(1).upper(),
                chapter_number=int(match.group(2)),
                verse_number=int(match.group(3)),
                translation_code=match.group(4).upper(),
            )
        else:
            raise Exception("could not parse string, expect something like 'MAT 1:1 KJV'")

    class Meta:
        ordering = ['book', 'chapter_number', 'verse_number', 'translation_code']
        indexes = [
            models.Index(fields=["book", "chapter_number", "verse_number"]),
        ]
        permissions = [
            ("propose_verse", _("Can propose a translation revision to a verse")),
        ]

class Approval(models.Model):
    approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    verse = models.ForeignKey('Verse', on_delete=models.PROTECT)
    step = models.CharField(max_length=32, choices=STEP_CHOICES)
    approved = models.BooleanField(default=True) # TODO: do we need this at all?
    date_created = models.DateTimeField(default=timezone.now)

    def recent_enough_to_delete(self):
        if self.date_created > (timezone.now() - datetime.timedelta(minutes=60)):
            return True
        return False

    class Meta:
        ordering = ['date_created']
        unique_together = [['approver', 'verse', 'step']]
        permissions = [
            ("handle_own_approval", _("Can approve and disapprove in user's own name")),
        ]

    def __str__(self):
        return 'Approval by %r for %r' % (self.approver, self.verse)



class Claim(models.Model):
    claimer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    book = models.ForeignKey('Book', on_delete=models.PROTECT)
    chapter_number = models.IntegerField()
    verse_number = models.IntegerField()
    step = models.CharField(max_length=32, choices=STEP_CHOICES)
    date_created = models.DateTimeField(default=timezone.now)
    finished = models.BooleanField(default=False) # TODO: delete claim instead of marking it as finished

    class Meta:
        ordering = ['book', 'chapter_number', 'verse_number', 'date_created', 'claimer']
        indexes = [
            models.Index(fields=["book", "chapter_number", "verse_number"]),
        ]
        permissions = [
            ("handle_own_claim", _("Can claim and remove claim in user's own name")),
        ]


class CategoryReview(models.Model):
    verse = models.ForeignKey('Verse', on_delete=models.PROTECT)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    category = models.CharField(max_length=32)
    date_created = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [['verse', 'author', 'category']]
        permissions = [
            ("handle_own_categoryreview", _("Can add and remove category reviews in user's own name")),
        ]

    def name(self):
        return REVIEW_CATEGORIES[self.category]["name"]

    def fa(self):
        return REVIEW_CATEGORIES[self.category]["fa"]

    def __str__(self):
        return "Author %s reviewed %s with category %s" % (self.author, self.verse, self.category)

class Comment(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    comment_text = models.TextField()
    resolved = models.BooleanField(default=False)
    hidden = models.BooleanField(default=False)
    parent = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='comment_children',
    )
    date_created = models.DateTimeField(default=timezone.now)

    def get_comment_html(self):
        return auto_paragraphs(self.comment_text)

    def recent_enough_to_delete(self):
        if self.date_created > (timezone.now() - datetime.timedelta(minutes=60)):
            return True
        return False

    class Meta:
        ordering = ['date_created']
        permissions = [
            ("handle_own_comment", ("Can make, modify and delete comments in user's own name")),
        ]

class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        unique=True,
    )
    profile_pic_url = models.URLField(max_length=200, blank=True)

    def get_profile_pic_url(self):
        if not self.profile_pic_url:
            avatar_url = self.social_account_avatar_url()
            if avatar_url:
                return avatar_url
            else:
                return self.gravatar_url()
        else:
            return str(self.profile_pic_url)

    def social_account_avatar_url(self):
        for socialaccount in self.user.socialaccount_set.all().order_by('id'):
            avatar_url = socialaccount.get_avatar_url()
            if avatar_url:
                return avatar_url
        return None

    def gravatar_url(self):
        default = "robohash"
        size = 150
        gravatar_url = "https://www.gravatar.com/avatar/" + hashlib.md5(self.user.email.lower().encode("UTF-8")).hexdigest() + "?"
        gravatar_url += urlencode({'d':default, 's':str(size)})
        return gravatar_url

    def admin_image_tag(self):
        return format_html('<img src="{}" width=30 height=30 crossorigin="anonymous" alt="">', self.get_profile_pic_url())
    admin_image_tag.short_description = _('Image')

    def get_absolute_url(self):
        return reverse('scripturet:team_member', kwargs={'user_pk': self.pk})

    def __str__(self):
        return "UserProfile of %s" % self.user.username

# TODO: notifications
