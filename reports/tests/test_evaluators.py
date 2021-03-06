from datetime import datetime
from mixer.backend.django import mixer
import pytest
from querystring_parser.parser import MalformedQueryStringError
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.utils import timezone

from survey.models import Answer, Survey, Organization, Question, Region, Option
from insights.users.models import User, Country

from ..models import SurveyStat, OrganizationStat, QuestionStat, Representation, OptionDict
from ..evaluators import TotalEvaluator, LastEvaluator

pytestmark = pytest.mark.django_db


class TestTotalEvaluator(TestCase):
    evaluator_cls = TotalEvaluator
    # fixtures = ['survey.json']

    def setUp(self):
        self.survey = mixer.blend(Survey)
        self.evaluator = self.evaluator_cls(self.survey)

    def test_get_answers(self):
        (o1, o2) = mixer.cycle(2).blend(Organization, name=mixer.sequence("org_{0}"))
        mixer.blend(Answer, survey=self.survey, organization=o1, is_updated=True)
        mixer.blend(Answer, survey=self.survey, organization=o2, is_updated=False)
        answers = self.evaluator.get_answers()
        assert len(answers) == 2, 'Should return all records'

    def test_clear(self):
        assert SurveyStat.objects.all().count() == 0, 'Cleared'
        assert OrganizationStat.objects.all().count() == 0, 'Cleared'
        assert QuestionStat.objects.all().count() == 0, 'Cleared'

    def test_load_stat(self):
        c1 = mixer.blend(Country, use_in_reports=True)
        c2 = mixer.blend(Country, use_in_reports=True)
        (o1, o2) = mixer.cycle(2).blend(Organization, name=mixer.sequence("org_{0}"))
        s1 = mixer.blend(Survey, countries=[c1, c2], organizations=[o1, o2])
        s2 = mixer.blend(Survey, countries=[c1, c2], organizations=[o1, o2])

        evaluator = self.evaluator_cls(s1)

        mixer.blend(SurveyStat, survey=s1, country=None)
        mixer.blend(SurveyStat, survey=s1, country=c1)
        mixer.blend(SurveyStat, survey=s2, country=c1)
        mixer.blend(OrganizationStat, survey=s1, country_id=None, organization=o1)
        mixer.blend(OrganizationStat, survey=s1, country=c1, organization=o1)
        mixer.blend(OrganizationStat, survey=s2, country=c1, organization=o1)
        mixer.blend(OrganizationStat, survey=s2, country=c1, organization=o2)

        r1 = mixer.blend(Representation, active=True)
        r2 = mixer.blend(Representation, active=True)

        mixer.blend(QuestionStat, survey=s1, country=None, representation=r1)
        mixer.blend(QuestionStat, survey=s1, country=c1, representation=r1)
        mixer.blend(QuestionStat, survey=s1, country=c1, representation=r2)

        evaluator.load_stat()
        assert len(evaluator.survey_stat) == 3
        assert len(evaluator.organization_stat) == 4
        assert len(evaluator.question_stat) == 3

    def test_fill_out(self):
        c1 = mixer.blend(Country, use_in_reports=True)
        c2 = mixer.blend(Country, use_in_reports=True)
        (o1, o2) = mixer.cycle(2).blend(Organization, name=mixer.sequence("org_{0}"))
        s1 = mixer.blend(Survey, countries=[c1, c2], organizations=[o1, o2], active=True)
        q1 = mixer.blend(Question, survey=s1)
        q2 = mixer.blend(Question, survey=s1)
        mixer.blend(Question, survey=s1)
        r1 = mixer.blend(Representation, active=True, question=q1, ordering=1)
        r2 = mixer.blend(Representation, active=True, question=q2, ordering=2)

        evaluator = self.evaluator_cls(s1)

        mixer.blend(SurveyStat, survey=s1, country=None)
        mixer.blend(SurveyStat, survey=s1, country=c1)
        mixer.blend(OrganizationStat, survey=s1, country_id=None, organization=o1)
        mixer.blend(OrganizationStat, survey=s1, country=c1, organization=o1)
        mixer.blend(QuestionStat, survey=s1, country=None, representation=r1, type=r1.type)
        mixer.blend(QuestionStat, survey=s1, country=c1, representation=r1, type=r1.type)
        evaluator.load_stat()

        assert len(evaluator.survey_stat) == 2
        assert len(evaluator.organization_stat) == 2
        assert len(evaluator.question_stat) == 2

        evaluator.fill_out()
        assert len(evaluator.survey_stat) == 3
        assert len(evaluator.organization_stat) == 6
        assert len(evaluator.question_stat) == 6
        assert evaluator.question_stat[(s1.pk, None, r2.pk)].ordering == 2
        assert evaluator.question_representation_link == {
            q1.pk: r1,
            q2.pk: r2
        }
        assert evaluator.question_dict == {
            q1.pk: q1,
            q2.pk: q2
        }

        for qs in evaluator.question_stat.values():
            assert qs.type == qs.representation.type

    @patch('reports.evaluators.AbstractEvaluator.process_answer')
    @patch('reports.evaluators.AbstractEvaluator.load_stat')
    @patch('reports.evaluators.AbstractEvaluator.fill_out')
    @patch('reports.evaluators.AbstractEvaluator.save')
    def test_process_answers(self, save, fill_out, load_stat, process_answer):
        s1 = mixer.blend(Survey)
        s2 = mixer.blend(Survey)
        c1 = mixer.blend(Country, use_in_reports=True)
        c2 = mixer.blend(Country, use_in_reports=True)
        (o1, o2) = mixer.cycle(2).blend(Organization, name=mixer.sequence("org_{0}"))
        mixer.blend(SurveyStat, survey=s1, country=None)
        mixer.blend(SurveyStat, survey=s1, country=c1)
        mixer.blend(SurveyStat, survey=s2, country=c1)
        mixer.blend(OrganizationStat, survey=s1, country=None, organization=o1)
        mixer.blend(OrganizationStat, survey=s1, country=c1, organization=o1)
        mixer.blend(OrganizationStat, survey=s2, country=c1, organization=o1)
        mixer.blend(OrganizationStat, survey=s2, country=c1, organization=o2)
        mixer.blend(Answer, survey=s1, organization=o1, is_updated=False)
        mixer.blend(Answer, survey=s2, organization=o2, is_updated=False)
        self.evaluator_cls.process_answers(s1)
        self.evaluator_cls.process_answers(s2)
        assert process_answer.call_count == 2
        assert fill_out.call_count == 2
        assert load_stat.call_count == 2
        assert save.call_count == 2

    @patch('reports.evaluators.AbstractEvaluator.update_survey_stat')
    @patch('reports.evaluators.AbstractEvaluator.update_organization_stat')
    def test_process_answer_with_empty_data(self, organization_stat, survey_stat):

        (o1, o2) = mixer.cycle(2).blend(Organization, name=mixer.sequence("org_{0}"))
        country = mixer.blend(Country, id=1)
        answer = mixer.blend(Answer, body='', survey=self.survey, organization=o1)
        self.evaluator.process_answer(answer)
        assert organization_stat.call_count == 0
        assert survey_stat.call_count == 0

        answer = mixer.blend(Answer, body='111', survey=self.survey, organization=o2)
        self.assertRaises(MalformedQueryStringError, self.evaluator.process_answer, answer)
        assert organization_stat.call_count == 0
        assert survey_stat.call_count == 0

        answer = mixer.blend(Answer, body='a=1', survey=self.survey, organization=o1)
        self.assertRaises(KeyError, self.evaluator.process_answer, answer)

        answer = mixer.blend(Answer, body='data=1', survey=self.survey, organization=o2)
        self.assertRaises(KeyError, self.evaluator.process_answer, answer)

        answer = mixer.blend(Answer, country=country, body='data[111]=Yes', survey=self.survey,
                             organization=o1)
        self.evaluator.process_answer(answer)

        survey_stat.assert_called_once_with((answer.survey_id, country.pk), answer)
        organization_stat.assert_called_once_with((answer.survey_id, country.pk, answer.organization_id))

    def test_process_answer(self):
        d1 = timezone.make_aware(datetime(2017, 1, 1))
        d2 = timezone.make_aware(datetime(2017, 1, 2))
        mixer.blend(SurveyStat, survey_id=1, country_id=None, total=2, last=d1)
        mixer.blend(SurveyStat, survey_id=1, country_id=1, total=2, last=d1)
        (o1, o2) = mixer.cycle(2).blend(Organization, name=mixer.sequence("org_{0}"))
        mixer.blend(OrganizationStat, survey_id=1, country_id=None, organization=o1, total=2)
        mixer.blend(OrganizationStat, survey_id=1, country_id=1, organization=o1, total=2)

        self.evaluator.load_stat()

    def test_process_dependencies(self):
        self.evaluator.dependencies = [
            {
                'source': 3,
                'target': 5,
                'type': 'set_radio',
                'additional': {
                    'options': ['Aripiprazole-oral', 'Aripiprazole-LAI'],
                    'anwser': 'Yes'
                }
            },
            {
                'source': 11,
                'target': 13,
                'type': 'set_radio',
                'additional': {
                    'options': ['Aripiprazole-oral', 'Aripiprazole-LAI'],
                    'anwser': 'Yes'
                }
            }
        ]

        d1 = {
            1: {'main': '10', 'additional': ''},
            2: 'Yes',
            3: {'': ['Ari-oral', 'Resperidol-oral', 'Ari-LAI', ''], 'other': ''},
            4: {'': ['Age', 'Preference of the patients', 'Efficacy profile', ''], 'other': ''},
            6: {'': ['Age', 'Mechanism of Action', 'Preference of the patients', ''], 'other': ''},
            7: 'No',
            9: {'main': '', 'additional': ''},
            11: {'': '', 'other': ''},
            12: {'': '', 'other': ''},
            14: {'': '', 'other': ''},
            16: 'xxx'
        }
        self.evaluator.process_dependencies(d1)
        assert 5 not in d1

        d2 = {
            1: {'main': '10', 'additional': ''},
            2: 'Yes',
            3: {'': ['Aripiprazole-oral', 'Resperidol-oral', 'Ari-LAI', ''], 'other': ''},
            4: {'': ['Age', 'Preference of the patients', 'Efficacy profile', ''], 'other': ''},
            6: {'': ['Age', 'Mechanism of Action', 'Preference of the patients', ''], 'other': ''},
            7: 'No',
            9: {'main': '', 'additional': ''},
            11: {'': '', 'other': ''},
            12: {'': '', 'other': ''},
            14: {'': '', 'other': ''},
            16: 'xxx'
        }
        self.evaluator.process_dependencies(d2)
        assert d2[5] == 'Yes'

    def test_update_survey_stat(self):
        d1 = timezone.make_aware(datetime(2017, 1, 1))
        d2 = timezone.make_aware(datetime(2017, 1, 2))
        (o1, o2) = mixer.cycle(2).blend(Organization, name=mixer.sequence("org_{0}"))
        a1 = mixer.blend(Answer, organization=o1)
        a1.created_at = d1
        a2 = mixer.blend(Answer, organization=o2)
        a2.created_at = d2
        self.evaluator.update_survey_stat((1, 2), a1)
        self.evaluator.update_survey_stat((1, 2), a2)
        assert self.evaluator.survey_stat[(1, 2)].total == 2
        assert self.evaluator.survey_stat[(1, 2)].last == d2
        assert self.evaluator.survey_stat[(1, None)].total == 2
        assert self.evaluator.survey_stat[(1, None)].last == d2

    def test_update_organization_stat(self):
        self.evaluator.update_organization_stat((1, 2, 3))
        self.evaluator.update_organization_stat((1, 2, 3))
        self.evaluator.update_organization_stat((1, 2, 4))
        self.evaluator.update_organization_stat((1, 2, 4))
        assert self.evaluator.organization_stat[(1, 2, 3)].total == 2

    def test_save(self):
        ss1 = MagicMock()
        ss2 = MagicMock()
        self.evaluator.survey_stat = {
            (1, 1): ss1,
            (1, 2): ss2,
        }

        os1 = MagicMock()
        os2 = MagicMock()
        self.evaluator.organization_stat = {
            (1, 2, 3): os1,
            (1, 3, 3): os2,
        }

        qs1 = MagicMock()
        qs2 = MagicMock()
        self.evaluator.question_stat = {
            (1, 2, 3): qs1,
            (1, 3, 3): qs2,
        }

        self.evaluator.save()

        os1.save.assert_called_once_with()
        ss1.save.assert_called_once_with()
        qs1.save.assert_called_once_with()
        os2.save.assert_called_once_with()
        ss2.save.assert_called_once_with()
        qs2.save.assert_called_once_with()

    def test_parse_query_string(self):
        results = self.evaluator.parse_query_string('data%5B12%5D%5B%5D=&data%5B4%5D%5B%5D=Age&data%5B4%5D%5B%5D=Preference+of+the+patients&data%5B4%5D%5B%5D=Efficacy+profile&data%5B4%5D%5B%5D=&csrfmiddlewaretoken=C7UlUxD6GI60dwB3PnGtA9en518LhHhRfqQwzXRb6pMVAs9jgaMIgWK0mq2AH8a6&data%5B14%5D%5B%5D=&data%5B3%5D%5Bother%5D=&data%5B7%5D=No&data%5B9%5D%5Badditional%5D=&data%5B2%5D=Yes&data%5B3%5D%5B%5D=Ari-oral&data%5B3%5D%5B%5D=Resperidol-oral&data%5B3%5D%5B%5D=Ari-LAI&data%5B3%5D%5B%5D=&data%5B11%5D%5Bother%5D=&data%5B9%5D%5Bmain%5D=&data%5B6%5D%5B%5D=Age&data%5B6%5D%5B%5D=Mechanism+of+Action&data%5B6%5D%5B%5D=Preference+of+the+patients&data%5B6%5D%5B%5D=&data%5B16%5D=xxx&data%5B11%5D%5B%5D=&data%5B14%5D%5Bother%5D=&data%5B1%5D%5Bmain%5D=10&data%5B4%5D%5Bother%5D=&data%5B12%5D%5Bother%5D=&data%5B6%5D%5Bother%5D=&data%5B1%5D%5Badditional%5D=')  # noqa
        assert results['data'] == {

            1: {'main': '10', 'additional': ''},
            2: 'Yes',
            3: {'': ['Ari-oral', 'Resperidol-oral', 'Ari-LAI', ''], 'other': ''},
            4: {'': ['Age', 'Preference of the patients', 'Efficacy profile', ''], 'other': ''},
            6: {'': ['Age', 'Mechanism of Action', 'Preference of the patients', ''], 'other': ''},
            7: 'No',
            9: {'main': '', 'additional': ''},
            11: {'': '', 'other': ''},
            12: {'': '', 'other': ''},
            14: {'': '', 'other': ''},
            16: 'xxx'
        }


class TestLastEvaluator(object):
    evaluator_cls = LastEvaluator

    def test_get_answers(self):
        s = mixer.blend(Survey)
        (o1, o2) = mixer.cycle(2).blend(Organization, name=mixer.sequence("org_{0}"))
        mixer.blend(Answer, survey=s, organization=o1, is_updated=True)
        mixer.blend(Answer, survey=s, organization=o2, is_updated=False)

        evaluator = self.evaluator_cls(s)
        answers = evaluator.get_answers()
        assert len(answers) == 1, 'Should return just one last record'


class TestTypeProcessor(TestCase):

    def setUp(self):
        OptionDict.clear()

    def test_types(self):
        s1 = mixer.blend(Survey, active=True)
        c1 = mixer.blend(Country, use_in_reports=True)

        q1 = mixer.blend(Question, survey=s1, type=Question.TYPE_TWO_DEPENDEND_FIELDS)
        q2 = mixer.blend(Question, survey=s1, type=Question.TYPE_YES_NO)
        q3 = mixer.blend(Question, survey=s1, type=Question.TYPE_YES_NO_JUMPING)
        q4 = mixer.blend(Question, survey=s1, type=Question.TYPE_MULTISELECT_ORDERED)
        q5 = mixer.blend(Question, survey=s1, type=Question.TYPE_MULTISELECT_WITH_OTHER)
        q6 = mixer.blend(Question, survey=s1, type=Question.TYPE_DEPENDEND_QUESTION)
        q7 = mixer.blend(Question, survey=s1, type=Question.TYPE_CHOICES)

        r1 = mixer.blend(Representation, active=True, question=q1)
        r2 = mixer.blend(Representation, active=True, question=q2)
        r3 = mixer.blend(Representation, active=True, question=q3)
        r4 = mixer.blend(Representation, active=True, question=q4)
        r5 = mixer.blend(Representation, active=True, question=q5)
        r6 = mixer.blend(Representation, active=True, question=q6)
        r7 = mixer.blend(Representation, active=True, question=q7)

        a = mixer.blend(Answer, survey=s1)

        qs = mixer.blend(QuestionStat)

        evaluator = TotalEvaluator(s1)

        for name, dsc in Representation.TYPE_CHOICES:
            assert callable(getattr(evaluator, "%s_processor" % name))

        evaluator.fill_out()

        self.assertRaises(ValueError, evaluator.type_average_percent_processor, q2.pk, {}, a)
        self.assertRaises(ValueError, evaluator.type_average_percent_processor, q3.pk, {}, a)
        self.assertRaises(ValueError, evaluator.type_average_percent_processor, q4.pk, {}, a)
        self.assertRaises(ValueError, evaluator.type_average_percent_processor, q5.pk, {}, a)
        self.assertRaises(ValueError, evaluator.type_average_percent_processor, q6.pk, {}, a)
        self.assertRaises(ValueError, evaluator.type_average_percent_processor, q7.pk, {}, a)

        self.assertRaises(ValueError, evaluator.type_multiselect_top_processor, q1.pk, {}, a)
        self.assertRaises(ValueError, evaluator.type_multiselect_top_processor, q2.pk, {}, a)
        self.assertRaises(ValueError, evaluator.type_multiselect_top_processor, q3.pk, {}, a)
        self.assertRaises(ValueError, evaluator.type_multiselect_top_processor, q5.pk, {}, a)
        self.assertRaises(ValueError, evaluator.type_multiselect_top_processor, q6.pk, {}, a)
        self.assertRaises(ValueError, evaluator.type_multiselect_top_processor, q7.pk, {}, a)

        self.assertRaises(ValueError, evaluator.type_yes_no_processor, q1.pk, {}, a)
        self.assertRaises(ValueError, evaluator.type_yes_no_processor, q4.pk, {}, a)
        self.assertRaises(ValueError, evaluator.type_yes_no_processor, q5.pk, {}, a)
        self.assertRaises(ValueError, evaluator.type_yes_no_processor, q6.pk, {}, a)
        self.assertRaises(ValueError, evaluator.type_yes_no_processor, q7.pk, {}, a)

    def init_models(self, question_type, representation_type):
        self.c1 = mixer.blend(Country, use_in_reports=True)
        self.c2 = mixer.blend(Country, use_in_reports=True)
        self.c3 = mixer.blend(Country, use_in_reports=True)
        self.u1 = mixer.blend(User, country=self.c1)
        self.u11 = mixer.blend(User, country=self.c1)
        self.u2 = mixer.blend(User, country=self.c2)
        self.u3 = mixer.blend(User, country=self.c3)
        self.reg11 = mixer.blend(Region, country=self.c1)
        self.reg12 = mixer.blend(Region, country=self.c1)
        self.reg13 = mixer.blend(Region, country=self.c1)
        self.reg21 = mixer.blend(Region, country=self.c2)
        self.reg31 = mixer.blend(Region, country=self.c3)
        self.org = mixer.blend(Organization)
        self.surv = mixer.blend(Survey, countries=[self.c1, self.c2, self.c3],
                                organizations=[self.org], active=True)
        self.q = mixer.blend(Question, survey=self.surv, type=question_type)
        self.r = mixer.blend(Representation, question=self.q, type=representation_type)

        self.evaluator = TotalEvaluator(self.surv)
        self.evaluator.load_stat()
        self.evaluator.fill_out()

    def create_answer(self, **kwargs):
        if 'survey' not in kwargs:
            kwargs['survey'] = self.surv
        if 'region' not in kwargs:
            kwargs['region'] = self.reg11
        if 'user' not in kwargs:
            kwargs['user'] = self.u2
        if 'country' not in kwargs:
            kwargs['country'] = self.c1
        if 'org' not in kwargs:
            kwargs['organization'] = self.org
        if 'is_updated' not in kwargs:
            kwargs['is_update'] = False
        return mixer.blend(Answer, **kwargs)

    def test_type_average_percent_processor(self):

        self.init_models(Question.TYPE_TWO_DEPENDEND_FIELDS, Representation.TYPE_AVERAGE_PERCENT)
        qid = self.q.pk
        a1 = self.create_answer(body='data[%s][main]=40' % qid, country=self.c1, region=self.reg11)
        a2 = self.create_answer(body='data[%s][main]=20' % qid, country=self.c1, region=self.reg12)
        a3 = self.create_answer(body='data[%s][main]=30' % qid, country=self.c2, region=self.reg21)

        self.evaluator.type_average_percent_processor(qid, {'main': '40', 'additional': ''}, a1)
        self.evaluator.type_average_percent_processor(qid, {'additional': '2'}, a2)
        self.evaluator.type_average_percent_processor(qid, {'main': '30', 'additional': ''}, a3)

        k0 = (self.surv.pk, None, self.r.pk)
        k1 = (self.surv.pk, self.c1.pk, self.r.pk)

        data = self.evaluator.question_stat[k0].data
        assert data['main_cnt'] == 3
        self.assertAlmostEqual(data['main_sum'],  90.0)
        assert data['dist'] == {
            '20': 1,
            '30': 1,
            '40': 1
        }

        reg_key = str(self.c1.pk)
        assert data['reg_cnt'][reg_key] == 2
        self.assertAlmostEqual(data['reg_sum'][reg_key],  60.0)

        reg_key = str(self.c2.pk)
        assert data['reg_cnt'][reg_key] == 1
        self.assertAlmostEqual(data['reg_sum'][reg_key],  30.0)

        assert data['org_cnt'][str(self.org.pk)] == 3
        self.assertAlmostEqual(data['org_sum'][str(self.org.pk)],  90.0)

        data = self.evaluator.question_stat[k1].data
        assert data['main_cnt'] == 2
        self.assertAlmostEqual(data['main_sum'],  60.0)
        assert data['dist'] == {
            '20': 1,
            '40': 1
        }

        assert data['reg_cnt'][str(self.reg11.pk)] == 1
        self.assertAlmostEqual(data['reg_sum'][str(self.reg11.pk)],  40.0)

        assert data['reg_cnt'][str(self.reg12.pk)] == 1
        self.assertAlmostEqual(data['reg_sum'][str(self.reg12.pk)],  20.0)

        assert data['org_cnt'][str(self.org.pk)] == 2
        self.assertAlmostEqual(data['org_sum'][str(self.org.pk)],  60.0)

    def test_type_yes_no_processor(self):
        self.init_models(Question.TYPE_YES_NO, Representation.TYPE_YES_NO)
        qid = self.q.pk
        a1 = self.create_answer(body='data[%s]=Yes' % qid, region=self.reg11)
        a2 = self.create_answer(body='data[%s]=No' % qid, region=self.reg12)
        a3 = self.create_answer(body='data[%s]=Yes' % qid, country=self.c2, region=self.reg21)

        self.evaluator.type_yes_no_processor(qid, 'Yes', a1)
        self.evaluator.type_yes_no_processor(qid, 'No', a2)
        self.evaluator.type_yes_no_processor(qid, 'Yes', a3)

        k0 = (self.surv.pk, None, self.r.pk)
        k1 = (self.surv.pk, self.c1.pk, self.r.pk)

        data = self.evaluator.question_stat[k0].data
        assert data['main_cnt'] == 3
        assert data['main_yes'] == 2

        assert data['reg_cnt'][str(self.c1.pk)] == 2
        assert data['reg_yes'][str(self.c1.pk)] == 1

        assert data['reg_cnt'][str(self.c2.pk)] == 1
        assert data['reg_yes'][str(self.c2.pk)] == 1

        assert data['org_cnt'][str(self.org.pk)] == 3
        assert data['org_yes'][str(self.org.pk)] == 2

        data = self.evaluator.question_stat[k1].data
        assert data['main_cnt'] == 2
        assert data['main_yes'] == 1

        assert data['reg_cnt'][str(self.reg11.pk)] == 1
        assert data['reg_yes'][str(self.reg11.pk)] == 1

        assert data['reg_cnt'][str(self.reg12.pk)] == 1
        assert data['reg_yes'][str(self.reg12.pk)] == 0

        assert data['org_cnt'][str(self.org.pk)] == 2
        assert data['org_yes'][str(self.org.pk)] == 1

    def test_type_multiselect_top_processor(self):
        self.init_models(Question.TYPE_MULTISELECT_ORDERED, Representation.TYPE_MULTISELECT_TOP)
        qid = self.q.pk
        a1 = self.create_answer(body='data[{0}][]=x1&data[{0}][]=x2&data[{0}][]=x3&data[{0}][]=x4'.format(qid),
                                country=self.c1, region=self.reg11)
        a2 = self.create_answer(body='data[{0}][]=x1&data[{0}][]=x2'.format(qid), region=self.reg12)
        a3 = self.create_answer(body='data[{0}][]=x2&data[{0}][]=x3'.format(qid), country=self.c2, region=self.reg21)
        a4 = self.create_answer(body='data[{0}][]=x3'.format(qid), country=self.c2, region=self.reg21)

        self.evaluator.type_multiselect_top_processor(qid, {'': ['x1', 'x2', 'x3', 'x4', ''], 'other': ''}, a1)
        self.evaluator.type_multiselect_top_processor(qid, {'': ['X1', 'x2', ''], 'other': ''}, a2)
        self.evaluator.type_multiselect_top_processor(qid, {'': ['x2', 'X3', 'x3', ''], 'other': ''}, a3)
        self.evaluator.type_multiselect_top_processor(qid, {'': 'x3', 'other': ''}, a4)

        k0 = (self.surv.pk, None, self.r.pk)
        k1 = (self.surv.pk, self.c1.pk, self.r.pk)
        data = self.evaluator.question_stat[k0].data
        assert data['cnt'] == 4
        assert data['top1'] == {
            'x1': 2,
            'x2': 1,
            'x3': 1,
        }
        assert data['top3'] == {
            'x1': 2,
            'x2': 3,
            'x3': 3
        }
        assert data['org'] == {
            str(self.org.pk): {
                'cnt': 4,
                'top1': {
                    'x1': 2,
                    'x2': 1,
                    'x3': 1,
                },
                'top3': {
                    'x1': 2,
                    'x2': 3,
                    'x3': 3
                }
            }
        }

        data = self.evaluator.question_stat[k1].data
        assert data['cnt'] == 2
        assert data['top1'] == {
            'x1': 2,
        }
        assert data['top3'] == {
            'x1': 2,
            'x2': 2,
            'x3': 1,
        }
        assert data['org'] == {
            str(self.org.pk): {
                'cnt': 2,
                'top1': {
                    'x1': 2,
                },
                'top3': {
                    'x1': 2,
                    'x2': 2,
                    'x3': 1,
                }
            }
        }

    def test_type_multiselect_top_processor_top1(self):
        self.init_models(Question.TYPE_MULTISELECT_ORDERED, Representation.TYPE_MULTISELECT_TOP)
        qid = self.q.pk
        a1 = self.create_answer(body='data[{0}][]=x1&data[{0}][]=x2&data[{0}][]=x3&data[{0}][]=x4'.format(qid),
                                country=self.c1, region=self.reg11)
        a2 = self.create_answer(body='data[{0}][]=x1&data[{0}][]=x2'.format(qid), region=self.reg12)
        a3 = self.create_answer(body='data[{0}][]=x2&data[{0}][]=x3'.format(qid), country=self.c2, region=self.reg21)
        a4 = self.create_answer(body='data[{0}][]=x3'.format(qid), country=self.c2, region=self.reg21)
        a5 = self.create_answer(body='data[{0}][]=x4'.format(qid), country=self.c2, region=self.reg21)

        # self.evaluator.type_multiselect_top_processor(qid, {'': ['x1', 'x2', 'x3', 'x4', ''], 'other': ''}, a1)
        # self.evaluator.type_multiselect_top_processor(qid, {'': ['X1', 'x2', ''], 'other': ''}, a2)
        # self.evaluator.type_multiselect_top_processor(qid, {'': ['x2', 'X3', 'x3', ''], 'other': ''}, a3)
        # self.evaluator.type_multiselect_top_processor(qid, {'': 'x3', 'other': ''}, a4)
        # self.evaluator.type_multiselect_top_processor(qid, {'': 'x4', 'other': ''}, a5)
        self.evaluator.process_answer(a1)
        self.evaluator.process_answer(a2)
        self.evaluator.process_answer(a3)
        self.evaluator.process_answer(a4)
        self.evaluator.process_answer(a5)
        self.evaluator.save()

        k0 = (self.surv.pk, None, self.r.pk)
        k1 = (self.surv.pk, self.c1.pk, self.r.pk)
        data = self.evaluator.question_stat[k0].data
        assert data['cnt'] == 5
        assert data['top1'] == {
            'x1': 2,
            'x2': 1,
            'x3': 1,
            'x4': 1,
        }
        assert data['top3'] == {
            'x1': 2,
            'x2': 3,
            'x3': 3,
            'x4': 1,
        }
        assert data['org'] == {
            str(self.org.pk): {
                'cnt': 5,
                'top1': {
                    'x1': 2,
                    'x2': 1,
                    'x3': 1,
                    'x4': 1,
                },
                'top3': {
                    'x1': 2,
                    'x2': 3,
                    'x3': 3,
                    'x4': 1,
                }
            }
        }

        data = self.evaluator.question_stat[k1].data
        assert data['cnt'] == 2
        assert data['top1'] == {
            'x1': 2,
        }
        assert data['top3'] == {
            'x1': 2,
            'x2': 2,
            'x3': 1,
        }
        assert data['org'] == {
            str(self.org.pk): {
                'cnt': 2,
                'top1': {
                    'x1': 2,
                },
                'top3': {
                    'x1': 2,
                    'x2': 2,
                    'x3': 1,
                }
            }
        }
        vars_ = self.evaluator.question_stat[k0].vars
        assert vars_['top1']['pie'] == {
            'labels': ('x1', 'x2', 'x3', 'Other'),
            'data': (2, 1, 1, 1),
            'hide_last_legend_item': 'true',
        }
