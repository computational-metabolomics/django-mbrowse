# -*- coding: utf-8 -*-
from __future__ import unicode_literals


def add_middleware_to_request(request, middleware_class):
    middleware = middleware_class()
    middleware.process_request(request)
    return request

def add_middleware_to_response(request, middleware_class):
    middleware = middleware_class()
    middleware.process_response(request)
    return request

# class MFileCreateView(TestCase):
#     def setUp(self):
#         self.factory = RequestFactory()
#         self.user = User.objects.create_user(
#             username='jacob', email='jacob@…', password='top_secret')
#
#     def test_login_redirect(self):
#         """
#         Test to check if a guest user is redirect to the login page
#         """
#         request = self.factory.get('/misa/upload_mfile')
#
#         request.user = AnonymousUser()
#         request = add_middleware_to_request(request, SessionMiddleware)
#
#         response = MFileCreateView.as_view()(request)
#
#         # client acts as a fake website for the request
#         response.client = Client()
#
#         print 'LOGIN REDIRECT', response
#         self.assertRedirects(response, '/misa/login/?next=/misa/upload_mfile')
#
#     def test_get(self):
#         """
#         Test to check get
#         """
#         request = self.factory.get(reverse('upload_mfile'))
#
#         request.user = self.user
#         # request = add_middleware_to_request(request, SessionMiddleware)
#
#         response =  MFileCreateView.as_view()(request)
#         self.assertEqual(response.status_code, 200)

#
# class Init2ViewTestCase(TestCase):
#     def setUp(self):
#         self.factory = RequestFactory()
#         self.user = User.objects.create_user(
#             username='jacob', email='jacob@…', password='top_secret')
#         self.org = Organism.objects.create(name='Daphnia magna')
#         self.org.save()
#         # make extractions
#         extraction_input = ['AP', 'P']
#         self.extractions = [ExtractionType.objects.create(type=e) for e in extraction_input]
#
#         spe_input = ['WAX', 'WCX', 'C18']
#         self.spes = [SpeType.objects.create(type=e) for e in spe_input]
#
#         chrom_input = ['C30', 'C18']
#         self.chrom = [ChromatographyType.objects.create(type=e) for e in chrom_input]
#
#         save_model_list(self.extractions)
#         save_model_list(self.spes)
#         save_model_list(self.chrom)
#         self.dma = Dma.objects.create(name='Daphnia magna', organism=self.org)
#         self.dma.save()
#
#
#         self.etl = [ExtractionLink(dma=self.dma, extractiontype=et) for et in self.extractions]
#         save_model_list(self.etl)
#
#
#
#     def test_login_redirect(self):
#         """
#         Test to check if a guest user is redirect to the login page
#         """
#         request = self.factory.get('/dma/init2/{}'.format(self.dma.id))
#
#         request.user = AnonymousUser()
#         request = add_middleware_to_request(request, SessionMiddleware)
#
#         response = Init2View.as_view()(request)
#
#         # client acts as a fake website for the request
#         response.client = Client()
#
#         print 'LOGIN REDIRECT', response
#         self.assertRedirects(response, '/dma/login/?next=/dma/init2/{}'.format(self.dma.id))
#
#     def test_get(self):
#         """
#         Test to check init1 get
#         """
#         request = self.factory.get(reverse('init2', kwargs={'dmaid': self.dma.id}))
#
#         request.user = self.user
#         request = add_middleware_to_request(request, SessionMiddleware)
#
#         # have to pass the kwargs 'dmaid' again for some reason
#         response = Init2View.as_view()(request, dmaid=self.dma.id)
#         self.assertEqual(response.status_code, 200)
#
#
#     # def test_post(self):
#     #     """
#     #     Test to check init2 post (not sure how to get the post test working yet)
#     #     """
#     #     request = self.factory.post(reverse('init2', kwargs={'dmaid': self.dma.id}), {'name': 'daphnia'})
#     #
#     #     request.user = self.user
#     #     print 'REQUEST', request
#     #
#     #     response = Init2View.as_view()(request, dmaid=self.dma.id)
#     #
#     #
#     #     self.assertEqual(response.status_code, 200)
#     #
#     # get an error due to the formset validation, Only a problem when unit testing but not live
#     # not sure how to fix. Due to the managementForm params used for the formset. for See error:
#     # ValidationError: [u'ManagementForm data is missing or has been tampered with']
#
#
#
# class Init3ViewTestCase(TestCase):
#     def setUp(self):
#         self.factory = RequestFactory()
#         self.user = User.objects.create_user(
#             username='jacob', email='jacob@…', password='top_secret')
#         self.org = Organism.objects.create(name='Daphnia magna')
#         self.org.save()
#         # make extractions
#         extraction_input = ['AP', 'P']
#         self.extractions = [ExtractionType.objects.create(type=e) for e in extraction_input]
#
#         spe_input = ['WAX', 'WCX', 'C18']
#         self.spes = [SpeType.objects.create(type=e) for e in spe_input]
#
#         chrom_input = ['C30', 'C18']
#         self.chrom = [ChromatographyType.objects.create(type=e) for e in chrom_input]
#
#         save_model_list(self.extractions)
#         save_model_list(self.spes)
#         save_model_list(self.chrom)
#         self.dma = Dma.objects.create(name='Daphnia magna', organism=self.org)
#         self.dma.save()
#
#         self.etl = [ExtractionLink(dma=self.dma, extractiontype=et) for et in self.extractions]
#         save_model_list(self.etl)
#
#         for spe in self.spes:
#             for e in self.etl:
#                 spelink = SpeLink(extractionlink=e, spetype=spe)
#                 spelink.save()
#
#
#     def test_login_redirect(self):
#         """
#         Test to check if a guest user is redirect to the login page
#         """
#         request = self.factory.get('/dma/init3/{}'.format(self.dma.id))
#
#         request.user = AnonymousUser()
#         request = add_middleware_to_request(request, SessionMiddleware)
#
#         response = Init3View.as_view()(request)
#
#         # client acts as a fake website for the request
#         response.client = Client()
#
#         print 'LOGIN REDIRECT', response
#         self.assertRedirects(response, '/dma/login/?next=/dma/init3/{}'.format(self.dma.id))
#
#
#
#
#
#
#
#
