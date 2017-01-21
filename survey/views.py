from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse
from django.views.generic import TemplateView

from survey.models import Answer
from survey.forms import StartForm


@login_required
def definition_view(request):
    if request.COOKIES.get(InstructionsView.cookie_name):
        return render(request, 'survey/definition.html')
    else:
        return HttpResponseRedirect(reverse('survey:instructions'))


class InstructionsView(LoginRequiredMixin, TemplateView):
    template_name = 'survey/instructions.html'
    cookie_name = 'instructions_was_viewed2'


    def get(self, request, *args, **kwargs):
        response = super(self.__class__, self).get(self, request, *args, **kwargs)
        response.set_cookie(self.cookie_name, True, 365*24*60*60)
        return response


@login_required
def start_view(request):
    if request.user.country is None:
        raise ValueError('User country is not set')

    regions = request.user.country.region_set.all()
    if len(regions):
        region_choices = [(region.pk, region.name) for region in regions]
    else:
        region_choices = []

    form = StartForm(request.POST or None, region_choices=region_choices)

    if request.method == 'POST':
        if form.is_valid():
            response = Answer(
                user=request.user,
                country=request.user.country,
                organization_id=form.cleaned_data['organization'],
                survey_id=form.cleaned_data['survey']
            )
            if form.cleaned_data['region']:
                response.region_id = form.cleaned_data['region']
            response.save()
            return HttpResponseRedirect(reverse('survey:pass', kwargs={'id': response.pk}))


    return render(request, 'survey/start.html', {'form': form})


@login_required
def pass_view(request, id):
    answer = Answer.objects.select_related('survey').get(pk=id)
    if answer.body:
        return HttpResponseRedirect(reverse('survey:start'))

    if answer.user_id != request.user.pk:
        return HttpResponseRedirect(reverse('survey:start'))

    if request.method == 'POST':
        answer.body = request.POST.urlencode()
        answer.save()
        return HttpResponseRedirect(reverse('survey:thanks'))

    items = answer.survey.survey_items.all().prefetch_related('question__option_set')
    return render(request, 'survey/pass.html', {'items': items})
