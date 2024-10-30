from django.test import TestCase
from django.urls import reverse




class URLTestsNotLoggedIn(TestCase):
    def test_homapage_url(self):
        response = self.client.get('')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')

    def test_loginpage(self):
        response = self.client.get(reverse('home:login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')

    def test_contactpage(self):
        response = self.client.get(reverse('home:contact'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'contact.html')

    def test_membership(self):
        response = self.client.get(reverse('home:membership'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'membership.html')

class TestHomepageHTML(TestCase):


    def test_for_some_html_elements(self):
        response = self.client.get(reverse('home:home'))
        self.assertInHTML("""<div>About Cl&ograve</div>""",
                          response.content.decode())

