# -*- coding: utf-8 -*-
from django.test import TestCase
from django.contrib.auth.models import User
from django.db import models
from tastypie.models import ApiKey
from elections.models import Election, Candidate, Category, PersonalData, \
                             BackgroundCategory, Background, PersonalDataCandidate, \
                             Question, Answer
from tastypie.test import ResourceTestCase, TestApiClient
from django.core import serializers
from django.core.urlresolvers import reverse
from django.utils.unittest import skip

class ApiTestCase(ResourceTestCase):
    
    def setUp(self):
        super(ApiTestCase, self).setUp()
        self.user = User.objects.create_user(username='the_user',
                                                password='joe',
                                                email='doe@joe.cl')
        Election.objects.filter(owner=self.user).delete()
        self.not_user = User.objects.create_user(username='joe',
                                                password='joe',
                                                email='doe@joe.cl')
        self.election, created = Election.objects.get_or_create(name='BarBaz',
                                                            owner=self.user,
                                                            slug='barbaz',
                                                            published=True)
        self.election.category_set.all().delete()
        self.election.personaldata_set.all().delete()
        self.personal_data1 = PersonalData.objects.create(label=u"Age", election=self.election)
        self.personal_data2 = PersonalData.objects.create(label=u"Profession", election=self.election)

        self.category1 = Category.objects.create(name=u"Pets and phisicians", election=self.election, slug="pets")
        self.category2 = Category.objects.create(name=u"language problemas ", election=self.election, slug="language")
        self.question1 = Question.objects.create(category=self.category1, question=u"¿Cuál es el nombre de la ferocidad?")
        self.answer1 = Answer.objects.create(caption=u"Fiera", question=self.question1)
        self.answer2 = Answer.objects.create(caption=u"Ratón inteligente pero barza", question=self.question1)
        self.question2 = Question.objects.create(category=self.category1, question=u"¿Which one is your favourite colour?")
        self.answer3 = Answer.objects.create(caption=u"apple", question=self.question2)
        self.answer4 = Answer.objects.create(caption=u"orange", question=self.question2)
        self.question3 = Question.objects.create(category=self.category2, question=u"¿!¿Why don't you speak proper english?!?")
        self.answer5 = Answer.objects.create(caption=u"Hablo inglés perfectamente", question=self.question3)
        self.answer6 = Answer.objects.create(caption=u"I don't speak any english", question=self.question3)

        self.election2, created = Election.objects.get_or_create(name='BarBaz2',
                                                            owner=self.not_user,
                                                            slug='barbaz2',
                                                            published=True)
        self.candidate = Candidate.objects.create(
                                                            name='Bar Baz',
                                                            election=self.election)

        self.age1 = PersonalDataCandidate.objects.create(personal_data=self.personal_data1, candidate=self.candidate, value=u"2")
        self.profession1 = PersonalDataCandidate.objects.create(personal_data=self.personal_data2, candidate=self.candidate, value=u"Perro")
        self.candidate2 = Candidate.objects.create(
                                                            name='Fieri',
                                                            election=self.election)
        self.candidate3  = Candidate.objects.create(
                                                            name='Ratón 1',
                                                            election=self.election2)
        self.candidate3.personal_data.all().delete()
        self.election3, created = Election.objects.get_or_create(name='BarBaz3',
                                                            owner=self.user,
                                                            slug='barbaz3',
                                                            published=True)
        self.api_client = TestApiClient()
        self.data = {'format': 'json', 'username': self.user.username, 'api_key':self.user.api_key.key}


    def test_get_all_my_elections(self):
        url = '/api/v1/election/'
        resp = self.api_client.get(url,data = self.data)
        self.assertValidJSONResponse(resp)
        elections = self.deserialize(resp)['objects']
        self.assertEqual(len(elections), 2) #Only my elections
        self.assertTrue(elections[0].has_key("name"))
        self.assertEqual(elections[0]["id"], self.election.id) #I make sure this is the election
        self.assertTrue(elections[0].has_key("id"))
        self.assertTrue(elections[0].has_key("slug"))
        self.assertTrue(elections[0].has_key("description"))
        self.assertTrue(elections[0].has_key("information_source"))
        self.assertTrue(elections[0].has_key("logo"))
        self.assertTrue(elections[0].has_key("published"))
        self.assertFalse(elections[0].has_key("custom_style"))
        self.assertTrue(elections[0].has_key("candidates"))

    def test_get_filter_elections(self):
        url = '/api/v1/election/'
        filter_key = 'slug'
        filter_value = 'barbaz'
        self.data[filter_key] = filter_value
        resp = self.api_client.get(url,data = self.data)
        self.assertValidJSONResponse(resp)
        elections = self.deserialize(resp)['objects']
        self.assertEqual(len(elections), 1)

    def test_get_elections_including_candidate_basic_data(self):
        url = '/api/v1/election/'
        filter_key = 'slug'
        filter_value = 'barbaz'
        self.data[filter_key] = filter_value
        resp = self.api_client.get(url, data=self.data)

        self.assertValidJSONResponse(resp)
        elections = self.deserialize(resp)['objects']
        self.assertEqual(type(elections[0]['candidates'][0]), dict)
        self.assertTrue(elections[0]['candidates'][0].has_key('name'))

    def test_get_including_unpublished_elections(self):
        self.election.published = False
        self.election.save()
        url = '/api/v1/election/'
        resp = self.api_client.get(url,data = self.data)
        self.assertValidJSONResponse(resp)
        elections = self.deserialize(resp)['objects']
        self.assertEqual(len(elections), 2) #Only my elections
        self.assertFalse(elections[0]['published'])

    def test_get_candidates_from_elections_owned_by_user(self):
        url = '/api/v1/candidate/'
        resp = self.api_client.get(url,data = self.data)
        self.assertValidJSONResponse(resp)
        candidates = self.deserialize(resp)['objects']
        self.assertEqual(len(candidates), 2)

    def test_get_candidates_per_election(self):
        url = '/api/v1/election/{0}/'.format(self.election.id)
        resp = self.api_client.get(url, data=self.data)

        self.assertValidJSONResponse(resp)
        election = self.deserialize(resp)
        candidates = election['candidates']
        self.assertEqual(len(candidates), 2)

        self.assertEqual(candidates[0]['name'], self.candidate.name)
        self.assertEqual(candidates[0]['resource_uri'], "/api/v1/candidate/{0}/".format(self.candidate.id))
        self.assertEqual(candidates[1]['name'], self.candidate2.name)
        self.assertEqual(candidates[1]['resource_uri'], "/api/v1/candidate/{0}/".format(self.candidate2.id))

    def test_an_election_shows_questions(self):
        url = '/api/v1/election/{0}/'.format(self.election.id)
        resp = self.api_client.get(url, data=self.data)
        election = self.deserialize(resp)

        self.assertTrue(election.has_key("categories"))
        self.assertEquals(len(election["categories"]), 2)

        category = election["categories"][0]

        self.assertEquals(category['name'], u"Pets and phisicians")
        self.assertTrue(category.has_key('questions'))

        self.assertEquals(len(category["questions"]), 2)
        self.assertEquals(category["questions"][0]["question"], u"¿Cuál es el nombre de la ferocidad?")
        self.assertEquals(category["questions"][1]["question"], u"¿Which one is your favourite colour?")

    def test_a_question_has_possible_answers(self):
        url = '/api/v1/election/{0}/'.format(self.election.id)
        resp = self.api_client.get(url, data=self.data)
        election = self.deserialize(resp)

        question = election["categories"][0]["questions"][0]
        self.assertTrue(question.has_key("possible_answers"))
        self.assertEquals(len(question["possible_answers"]), 2)
        self.assertEquals(question["possible_answers"][0]["caption"],u"Fiera")
        self.assertEquals(question["possible_answers"][1]["caption"],u"Ratón inteligente pero barza")

    def test_candidate_detail_shows_personal_data(self):
        url = '/api/v1/candidate/{0}/'.format(self.candidate.id)
        resp = self.api_client.get(url, data=self.data)
        candidate = self.deserialize(resp)

        self.assertTrue("personal_data" in candidate)
        self.assertFalse("resource_uri" in candidate["personal_data"][0])
        self.assertEqual(candidate["personal_data"][0]["label"], "Age")
        self.assertEqual(candidate["personal_data"][1]["label"], "Profession")
        self.assertEqual(candidate["personal_data"][0]["value"], "2")
        self.assertEqual(candidate["personal_data"][1]["value"], "Perro")
