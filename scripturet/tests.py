from django.test import TestCase
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import Book, Verse, Approval, STEP_TRANSLATION


class MyTests(TestCase):
    @classmethod
    def setUpTestData(klass):
        # Note that changes to these instances will persist between tests
        matthew = Book(book_code='MAT', book_name='Matthew', book_number=40, chapters=28)
        matthew.full_clean()
        matthew.save()
        for i in range(20):
            Verse.objects.create(
                translation_code=settings.SCRIPTURE_DEFAULT_TRANSLATION_CODE,
                book=matthew, chapter_number=1, verse_number=i,
                text="This is the test content of Matthew 1:%d" % (i,),
                published=True,
            ).full_clean()
        klass.matthew11 = Verse.objects.get(book=matthew, chapter_number=1, verse_number=1)
        User = get_user_model()
        klass.user1 = User.objects.create_user(username='test1')
        klass.user2 = User.objects.create_user(username='test2')
        klass.user3 = User.objects.create_user(username='test3')

    def test_progress_avatars(self):
        self.assertEquals(
            self.matthew11.get_progress_avatars(),
            [None, None, None, None, None]
        )
        Approval.objects.create(
            approver=self.user1,
            verse=self.matthew11,
            step=STEP_TRANSLATION,
            approved=True,
        ).full_clean()
        self.assertEquals(
            self.matthew11.get_progress_avatars(),
            [
                { 'checked': True, 'claimed': False, 'user': self.user1, },
                None, None, None, None
            ],
        )
        Approval.objects.create(
            approver=self.user2,
            verse=self.matthew11,
            step=STEP_TRANSLATION,
            approved=True,
        ).full_clean()
        self.assertEquals(
            self.matthew11.get_progress_avatars(),
            [
                { 'checked': True, 'claimed': False, 'user': self.user1, },
                { 'checked': True, 'claimed': False, 'user': self.user2, },
                None, None, None
            ]
        )
        revision = Verse.objects.create(
            book=self.matthew11.book,
            chapter_number=self.matthew11.chapter_number,
            verse_number=self.matthew11.verse_number,
            translation_code=settings.SCRIPTURE_DEFAULT_TRANSLATION_CODE,
            text='A revision of Matthew 1:1',
            published=False,
        )
        revision.full_clean()
        self.assertEquals(
            self.matthew11.get_progress_avatars(),
            [
                { 'checked': True, 'claimed': False, 'user': self.user1, },
                { 'checked': True, 'claimed': False, 'user': self.user2, },
                None, None, None
            ]
        )
        Approval.objects.create(
            approver=self.user3,
            verse=revision,
            step=STEP_TRANSLATION,
            approved=True,
        ).full_clean()
        self.assertEquals(
            self.matthew11.get_progress_avatars(),
            [
                { 'checked': True, 'claimed': False, 'user': self.user1, },
                { 'checked': True, 'claimed': False, 'user': self.user2, },
                None, None, None
            ]
        )
        Approval.objects.create(
            approver=self.user1,
            verse=revision,
            step=STEP_TRANSLATION,
            approved=True,
        ).full_clean()
        self.assertEquals(
            self.matthew11.get_progress_avatars(),
            [
                { 'checked': True, 'claimed': False, 'user': self.user3, },
                { 'checked': True, 'claimed': False, 'user': self.user1, },
                None, None, None
            ]
        )
