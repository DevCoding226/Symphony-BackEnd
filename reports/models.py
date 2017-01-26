import jsonfield

from django.db import models


from survey.models import Country, Survey, Organization, Answer, Question, Option


class Stat(models.Model):
    country = models.ForeignKey(Country, blank=True, null=True)
    survey = models.ForeignKey(Survey, null=True)
    total = models.PositiveIntegerField(default=0)

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.total)


class SurveyStat(Stat):
    last = models.DateTimeField(blank=True, null=True)


class OrganizationStat(Stat):
    organization = models.ForeignKey(Organization, null=True)
    ordering = models.PositiveIntegerField('Ordering in reports', default=1, blank=True, db_index=True)

    class Meta:
        ordering = ['ordering', 'id']


class RepresentationTypeMixin(models.Model):
    TYPE_AVERAGE_PERCENT = 'type_average_percent'
    TYPE_YES_NO = 'type_yes_no'
    TYPE_MULTISELECT_TOP = 'type_multiselect_top'

    TYPE_CHOICES = (
        (TYPE_AVERAGE_PERCENT, 'Average percent representation'),
        (TYPE_YES_NO, 'Representation for "yes" or "no" answers'),
        (TYPE_MULTISELECT_TOP, 'Top 1 and top 3 representation for ordered multiselect'),

    )
    type = models.CharField('Representation Type', choices=TYPE_CHOICES, max_length=50, null=True)

    class Meta:
        abstract = True


class Representation(RepresentationTypeMixin, models.Model):
    survey = models.ForeignKey(Survey)
    question = models.ManyToManyField(Question)
    active = models.BooleanField(blank=True, default=True, db_index=True)
    ordering = models.PositiveIntegerField('Ordering in reports', default=1, blank=True, db_index=True)
    label1 = models.CharField('Label 1', max_length=400, default='', blank=True)
    label2 = models.CharField('Label 2', max_length=400, default='', blank=True)
    label3 = models.CharField('Label 3', max_length=400, default='', blank=True)

    def __str__(self):
        return "%s, %s %s %s" % (self.id, self.label1, self.label2, self.label3)

    class Meta:
        ordering = ['ordering', 'id']


class QuestionStat(RepresentationTypeMixin, models.Model):
    survey = models.ForeignKey(Survey, null=True)
    country = models.ForeignKey(Country, blank=True, null=True)
    representation = models.ForeignKey(Representation)
    data = jsonfield.JSONField()
    vars = jsonfield.JSONField()
    ordering = models.PositiveIntegerField('Ordering in reports', default=1, blank=True, db_index=True)

    class Meta:
        ordering = ['ordering', 'id']

    def update_type_average_percent(self):
        pass

    def update_type_yes_no(self):
        pass

    def update_type_multiselect_top(self):
        pass

    def update_vars(self):
        if not self.type:
            raise KeyError('Empty type')

        getattr(self, 'update_%s' % self.type)()

    @classmethod
    def clear(cls):
        pass



class OptionDict(models.Model):
    lower = models.CharField(max_length=200, unique=True)
    original = models.CharField(max_length=200)

    data = {}
    is_loaded = False

    @classmethod
    def clear(cls):
        cls.data = {}
        cls.is_loaded = False

    @classmethod
    def _load(cls):
        for od in cls.objects.all():
            cls.data[od.lower] = od
        cls.is_loaded = True

        for opt in Option.objects.all():
            lower = opt.value.lower()
            if lower not in cls.data:
                new_dict = cls(lower=lower, original=opt.value)
                new_dict.save()
                cls.data[lower] = new_dict
            elif opt.value != cls.data[lower].original:
                cls.data[lower].original = opt.value
                cls.data[lower].save()


    @classmethod
    def get(cls, name):
        if not cls.is_loaded:
            cls._load()
        if name in cls.data:
            return cls.data[name].original
        else:
            return name

    @classmethod
    def register(cls, lower, original):
        if not cls.is_loaded:
            cls._load()

        if lower not in cls.data:
            new_dict = cls(lower=lower, original=original)
            new_dict.save()
            cls.data[lower] = new_dict
