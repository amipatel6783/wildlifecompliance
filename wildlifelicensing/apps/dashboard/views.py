from __future__ import unicode_literals
import json
import urllib
import logging
import datetime

from django.core.urlresolvers import reverse_lazy, reverse
from django.shortcuts import redirect
from django.views.generic import TemplateView
from django_datatables_view.base_datatable_view import BaseDatatableView
from django.db.models import Q
from django.contrib.staticfiles.templatetags.staticfiles import static

from django.contrib.auth.mixins import LoginRequiredMixin

from ledger.licence.models import LicenceType
from wildlifelicensing.apps.main.models import WildlifeLicence
from wildlifelicensing.apps.applications.models import Application, Assessment
from wildlifelicensing.apps.main.mixins import OfficerRequiredMixin, OfficerOrAssessorRequiredMixin, \
    AssessorRequiredMixin
from wildlifelicensing.apps.main.helpers import is_officer, is_assessor, get_all_officers, render_user_name
from wildlifelicensing.apps.dashboard.forms import LoginForm

logger = logging.getLogger(__name__)


def _build_url(base, query):
    return base + '?' + urllib.urlencode(query)


def _get_user_applications(user):
    return Application.objects.filter(applicant_profile__user=user).exclude(customer_status='approved')


def _get_user_licences(user):
    return WildlifeLicence.objects.filter(user=user)


def _get_processing_statuses_but_draft():
    return [s for s in Application.PROCESSING_STATUS_CHOICES if s[0] != 'draft']


# render date in dd/mm/yyyy format
def _render_date(date):
    if isinstance(date, datetime.datetime) or isinstance(date, datetime.date):
        return date.strftime("%d/%m/%Y")
    if not date:
        return ''
    return 'not a valid date object'


def _render_licence_document(licence):
    if licence is not None and licence.document is not None:
        return '<a href="{0}" target="_blank">View PDF</a><img height="20" src="{1}"></img>'.format(
            licence.document.file.url,
            static('wl/img/pdf.png')
        )
    else:
        return ''


class DashBoardRoutingView(TemplateView):
    template_name = 'wl/index.html'

    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated():
            if is_officer(self.request.user):
                return redirect('dashboard:tree_officer')
            elif is_assessor(self.request.user):
                return redirect('dashboard:tables_assessor')

            return redirect('dashboard:tables_customer')
        else:
            kwargs['form'] = LoginForm
            return super(DashBoardRoutingView, self).get(*args, **kwargs)


class DashboardTreeViewBase(TemplateView):
    template_name = 'wl/dash_tree.html'
    url = reverse_lazy('dashboard:tables_applications_officer')

    @staticmethod
    def _create_node(title, href=None, count=None):
        node_template = {
            'text': 'Title',
            'href': '#',
            'tags': [],
            'nodes': None,
            'state': {
                'expanded': True
            }
        }
        result = {}
        result.update(node_template)
        result['text'] = str(title)
        if href is not None:
            result['href'] = str(href)
        if count is not None:
            result['tags'].append(str(count))

        return result

    @staticmethod
    def _add_node(parent, child):
        if 'nodes' not in parent or type(parent['nodes']) != list:
            parent['nodes'] = [child]
        else:
            parent['nodes'].append(child)
        return parent

    def _build_tree_nodes(self):
        """
        Subclass should implement the nodes with the help of _create_node and _build_node
        """
        parent_node = self._create_node('Parent node', href='#', count=2)
        child1 = self._create_node('Child#1', href='#', count=1)
        self._add_node(parent_node, child1)
        child2 = self._create_node('Child#2', href='#', count=1)
        self._add_node(parent_node, child2)
        return [parent_node]

    def get_context_data(self, **kwargs):
        if 'dataJSON' not in kwargs:
            kwargs['dataJSON'] = json.dumps(self._build_tree_nodes())
        if 'title' not in kwargs and hasattr(self, 'title'):
            kwargs['title'] = self.title
        return super(DashboardTreeViewBase, self).get_context_data(**kwargs)


class DashboardOfficerTreeView(OfficerRequiredMixin, DashboardTreeViewBase):
    template_name = 'wl/dash_tree.html'
    title = 'Officer Dashboard'
    url = reverse_lazy('dashboard:tables_applications_officer')

    def _build_tree_nodes(self):
        """
            +Applications assigned to me
              - status
            +All applications
              - status
        """
        # The draft status is excluded from the officer status list
        statuses = _get_processing_statuses_but_draft()
        all_applications = Application.objects.filter(processing_status__in=[s[0] for s in statuses])
        all_applications_node = self._create_node('All applications', href=self.url,
                                                  count=all_applications.count())
        all_applications_node['state']['expanded'] = False
        for s_value, s_title in statuses:
            applications = all_applications.filter(processing_status=s_value)
            if applications.count() > 0:
                query = {
                    'application_status': s_value,
                }
                href = _build_url(self.url, query)
                node = self._create_node(s_title, href=href, count=applications.count())
                self._add_node(all_applications_node, node)

        user_applications = all_applications.filter(assigned_officer=self.request.user)
        query = {
            'application_assignee': self.request.user.pk
        }
        user_applications_node = self._create_node('My assigned applications', href=_build_url(self.url, query),
                                                   count=user_applications.count())
        user_applications_node['state']['expanded'] = True
        for s_value, s_title in statuses:
            applications = user_applications.filter(processing_status=s_value)
            if applications.count() > 0:
                query.update({
                    'application_status': s_value
                })
                href = _build_url(self.url, query)
                node = self._create_node(s_title, href=href, count=applications.count())
                self._add_node(user_applications_node, node)

        # Licences
        url = reverse_lazy('dashboard:tables_licences_officer')
        all_licences_node = self._create_node('All licences', href=url, count=WildlifeLicence.objects.count())

        return [user_applications_node, all_applications_node, all_licences_node]


class DashboardCustomerTreeView(LoginRequiredMixin, DashboardTreeViewBase):
    template_name = 'wl/dash_tree.html'
    title = 'My Dashboard'
    url = reverse_lazy('dashboard:tables_customer')

    def _build_tree_nodes(self):
        """
            +My applications
              - status
        :return:
        """
        my_applications = _get_user_applications(self.request.user)
        my_applications_node = self._create_node('My applications', href=self.url, count=my_applications.count())
        # one children node per status
        for status_value, status_title in Application.CUSTOMER_STATUS_CHOICES:
            applications = my_applications.filter(customer_status=status_value)
            if applications.count() > 0:
                query = {
                    'application_status': status_value,
                }
                href = _build_url(self.url, query)
                node = self._create_node(status_title, href=href, count=applications.count())
                self._add_node(my_applications_node, node)
        return [my_applications_node]


class TableBaseView(TemplateView):
    template_name = 'wl/dash_tables.html'

    def _build_data(self):
        licence_types = [('all', 'All')] + [(lt.pk, lt.code) for lt in LicenceType.objects.all()]
        data = {
            'applications': {
                'columnDefinitions': [],
                'filters': {
                    'licenceType': {
                        'values': licence_types,
                    },
                    'status': {
                        'values': [],
                    }
                },
                'ajax': {
                    'url': ''
                }
            },
            'licences': {
                'columnDefinitions': [],
                'filters': {
                    'licenceType': {
                        'values': licence_types,
                    },
                },
                'ajax': {
                    'url': ''
                }
            }
        }
        return data

    def get_context_data(self, **kwargs):
        if 'dataJSON' not in kwargs:
            data = self._build_data()
            # add the request query to the data
            data['query'] = self.request.GET.dict()
            kwargs['dataJSON'] = json.dumps(data)
        return super(TableBaseView, self).get_context_data(**kwargs)


def _build_field_query(fields_to_search, search):
    """
    Build a OR __icontains query
    :param fields_to_search:
    :param search:
    :return:
    """
    query = Q()
    for field in fields_to_search:
        query |= Q(**{"{0}__icontains".format(field): search})
    return query


class DataTableBaseView(LoginRequiredMixin, BaseDatatableView):
    """
    View to handle datatable server-side processing
    It is extension of the BaseDatatableView at
     https://bitbucket.org/pigletto/django-datatables-view
    It just provides a configurable way to define render and search functions for each defined columns through the
    column_helpers = {
       'column': {
            'search': callable(search_term)
            'render': callable(model_instance)
       }
    }

    """
    columns_helpers = {
    }

    def _build_global_search_query(self, search):
        query = Q()
        col_data = super(DataTableBaseView, self).extract_datatables_column_data()
        for col_no, col in enumerate(col_data):
            if col['searchable']:
                col_name = self.columns[col_no]
                # special cases
                if col_name in self.columns_helpers and 'search' in self.columns_helpers[col_name]:
                    func = self.columns_helpers[col_name]['search']
                    if callable(func):
                        q = func(self, search)
                        query |= q
                else:
                    query |= Q(**{'{0}__icontains'.format(self.columns[col_no].replace('.', '__')): search})
        return query

    def _parse_filters(self):
        """
        The additional filters are sent in the query param with the following form (example):
        'filters[0][name]': '['licence_type']'
        'filters[0][value]: ['all']'
        'filters[1][name]': '['status']'
        'filters[1][value]: ['draft']'
        .....
        :return: a dict {
            'licence_type': 'all',
            'status': 'draft',
            ....
        }
        """
        result = {}
        querydict = self._querydict
        counter = 0
        filter_key = 'filters[{0}][name]'.format(counter)
        while filter_key in querydict:
            result[querydict.get(filter_key)] = querydict.get('filters[{0}][value]'.format(counter))
            counter += 1
            filter_key = 'filters[{0}][name]'.format(counter)
        return result

    def filter_queryset(self, qs):
        """
        Two level of filtering:
        1- The filters included in the query (see _parse_filter)
        2- The data table search filter
        :param qs:
        :return:
        """
        query = Q()
        # part 1: filter from top level filters
        filters = self._parse_filters()
        for filter_name, filter_value in filters.items():
            # look for a filter_<filter_name> method and call it with the filter value
            # the method must return a Q instance, if it returns None or anything else it will be ignored
            filter_method = getattr(self, 'filter_' + filter_name.lower(), None)
            if callable(filter_method):
                q_filter = filter_method(filter_value)
                if isinstance(q_filter, Q):
                    query &= q_filter

        search = self.request.GET.get('search[value]', None)
        if search:
            query &= self._build_global_search_query(search)
        return qs.filter(query)

    def render_column(self, instance, column):
        if column in self.columns_helpers and 'render' in self.columns_helpers[column]:
            func = self.columns_helpers[column]['render']
            if callable(func):
                return func(self, instance)
            else:
                return 'render is not a function'
        else:
            result = super(DataTableBaseView, self).render_column(instance, column)
        return result


class DataTableApplicationBaseView(LoginRequiredMixin, BaseDatatableView):
    model = Application
    columns = ['licence_type.code', 'applicant_profile.user', 'applicant_profile', 'processing_status']
    order_columns = ['licence_type.code', 'applicant_profile.user', 'applicant_profile', 'processing_status']

    def _build_search_query(self, fields_to_search, search):
        query = Q()
        for field in fields_to_search:
            query |= Q(**{"{0}__icontains".format(field): search})
        return query

    def _build_user_search_query(self, search):
        fields_to_search = ['applicant_profile__user__last_name', 'applicant_profile__user__first_name']
        return self._build_search_query(fields_to_search, search)

    def _build_profile_search_query(self, search):
        fields_to_search = ['applicant_profile__email', 'applicant_profile__name']
        return self._build_search_query(fields_to_search, search)

    def _render_user_column(self, obj):
        return render_user_name(obj.applicant_profile.user, first_name_first=False)

    def _render_profile_column(self, obj):
        profile = obj.applicant_profile
        if profile is None:
            return 'unknown'
        else:
            # return the string rep
            return '{}'.format(profile)

    columns_helpers = {
        'applicant_profile.user': {
            'render': _render_user_column,
            'search': _build_user_search_query
        },
        'applicant_profile': {
            'render': _render_profile_column,
            'search': _build_profile_search_query
        }
    }

    def _parse_filters(self):
        """
        The additional filters are sent in the query param with the following form (example):
        'filters[0][name]': '['licence_type']'
        'filters[0][value]: ['all']'
        'filters[1][name]': '['status']'
        'filters[1][value]: ['draft']'
        .....
        :return: a dict {
            'licence_type': 'all',
            'status': 'draft',
            ....
        }
        """
        result = {}
        querydict = self._querydict
        counter = 0
        filter_key = 'filters[{0}][name]'.format(counter)
        while filter_key in querydict:
            result[querydict.get(filter_key)] = querydict.get('filters[{0}][value]'.format(counter))
            counter += 1
            filter_key = 'filters[{0}][name]'.format(counter)
        return result

    def get_initial_queryset(self):
        return self.model.objects.all()

    def _build_status_filter(self, status_value):
        return Q(processing_status=status_value) if status_value != 'all' else Q()

    def filter_queryset(self, qs):
        query = Q()
        # part 1: filter from top level filters
        filters = self._parse_filters()
        for filter_name, filter_value in filters.items():
            # if the value is 'all' no filter to apply.
            # There is a special case for the status. There are two kinds of status depending on the user
            # (customer or officer) also if the application is a draft it should not be seen by the officers.
            # That is why the status filter is left to be implemented by subclasses.
            if filter_name == 'status':
                query &= self._build_status_filter(filter_value)
            if filter_value != 'all':
                if filter_name == 'assignee':
                    query &= Q(assigned_officer__pk=filter_value)
        # part 2: filter from the global search
        search = self.request.GET.get('search[value]', None)
        if search:
            query &= self._build_global_search_query(search)
        return qs.filter(query)

    def render_column(self, application, column):
        if column in self.columns_helpers and 'render' in self.columns_helpers[column]:
            func = self.columns_helpers[column]['render']
            if callable(func):
                return func(self, application)
            else:
                return 'render is not a function'
        else:
            result = super(DataTableApplicationBaseView, self).render_column(application, column)
        return result

    def _build_global_search_query(self, search):
        query = Q()
        col_data = super(DataTableApplicationBaseView, self).extract_datatables_column_data()
        for col_no, col in enumerate(col_data):
            if col['searchable']:
                col_name = self.columns[col_no]
                # special cases
                if col_name in self.columns_helpers and 'search' in self.columns_helpers[col_name]:
                    func = self.columns_helpers[col_name]['search']
                    if callable(func):
                        q = func(self, search)
                        query |= q
                else:
                    query |= Q(**{'{0}__icontains'.format(self.columns[col_no].replace('.', '__')): search})
        return query


########################
#    Officers
########################

class TableApplicationsOfficerView(OfficerRequiredMixin, TableBaseView):
    template_name = 'wl/dash_tables_applications_officer.html'

    def _build_data(self):
        data = super(TableApplicationsOfficerView, self)._build_data()
        data['applications']['columnDefinitions'] = [
            {
                'title': 'Lodge No.'
            },
            {
                'title': 'Licence Type'
            },
            {
                'title': 'User'
            },
            {
                'title': 'Status',
            },
            {
                'title': 'Lodged on'
            },
            {
                'title': 'Assignee'
            },
            {
                'title': 'Proxy'
            },
            {
                'title': 'Action',
                'searchable': False,
                'orderable': False
            }
        ]
        data['applications']['filters']['status']['values'] = \
            [('all', 'All')] + _get_processing_statuses_but_draft()
        data['applications']['filters']['assignee'] = {
            'values': [('all', 'All')] + [(user.pk, render_user_name(user),) for user in get_all_officers()]
        }
        data['applications']['ajax']['url'] = reverse('dashboard:data_application_officer')
        # global table options
        data['applications']['tableOptions'] = {
            'pageLength': 25
        }
        return data


class DataTableApplicationsOfficerView(OfficerRequiredMixin, DataTableApplicationBaseView):
    columns = ['lodgement_number', 'licence_type.code', 'applicant_profile.user', 'processing_status', 'lodgement_date',
               'assigned_officer', 'proxy_applicant', 'action']
    order_columns = ['lodgement_number', 'licence_type.code',
                     ['applicant_profile.user.last_name', 'applicant_profile.user.first_name',
                      'applicant_profile.user.email'],
                     'processing_status', 'lodgement_date',
                     ['assigned_officer.first_name', 'assigned_officer.last_name', 'assigned_officer.email'],
                     ['proxy_applicant.first_name', 'proxy_applicant.last_name', 'proxy_applicant.email'],
                     '']

    def _build_status_filter(self, status_value):
        # officers should not see applications in draft mode.
        return Q(processing_status=status_value) if status_value != 'all' else ~Q(customer_status='draft')

    def _render_action_column(self, obj):
        if obj.processing_status == 'ready_for_conditions':
            return '<a href="{0}">Enter Conditions</a>'.format(
                reverse('applications:enter_conditions', args=[obj.pk]),
            )
        if obj.processing_status == 'ready_to_issue':
            return '<a href="{0}">Issue Licence</a>'.format(
                reverse('applications:issue_licence', args=[obj.pk]),
            )
        elif obj.processing_status == 'issued' and obj.licence is not None and obj.licence.document is not None:
            return '<a href="{0}" target="_blank">View licence</a>'.format(
                obj.licence.document.file.url
            )
        else:
            return '<a href="{0}">Process</a>'.format(
                reverse('applications:process', args=[obj.pk]),
            )

    def _build_assignee_search_query(self, search):
        fields_to_search = ['assigned_officer__last_name', 'assigned_officer__first_name']
        return self._build_search_query(fields_to_search, search)

    def _build_proxy_search_query(self, search):
        fields_to_search = ['assigned_officer__last_name', 'assigned_officer__first_name']
        return self._build_search_query(fields_to_search, search)

    def _render_assignee_column(self, obj):
        return render_user_name(obj.assigned_officer)

    def _render_lodgement_date(self, obj):
        return _render_date(obj.lodgement_date)

    columns_helpers = dict(DataTableApplicationBaseView.columns_helpers.items(), **{
        'assigned_officer': {
            'search': _build_assignee_search_query,
            'render': _render_assignee_column
        },
        'proxy_applicant': {
            'search': lambda self, search: _build_field_query([
                'proxy_applicant__last_name', 'proxy_applicant__first_name'],
                search),
            'render': lambda self, obj: render_user_name(obj.proxy_applicant)
        },
        'action': {
            'render': _render_action_column,
        },
        'lodgement_date': {
            'render': _render_lodgement_date
        },
    })

    def get_initial_queryset(self):
        return self.model.objects.all()


class TableLicencesOfficerView(OfficerRequiredMixin, TableBaseView):
    template_name = 'wl/dash_tables_licences_officer.html'

    DATE_FILTER_ACTIVE = 'active'
    DATE_FILTER_EXPIRING = 'expiring'
    DATE_FILTER_EXPIRED = 'expired'
    DATE_FILTER_ALL = 'all'

    def _build_data(self):
        data = super(TableLicencesOfficerView, self)._build_data()
        del data['applications']
        data['licences']['columnDefinitions'] = [
            {
                'title': 'Licence No.'
            },
            {
                'title': 'Licence Type'
            },
            {
                'title': 'User'
            },
            {
                'title': 'Start Date'
            },
            {
                'title': 'Expiry Date'
            },
            {
                'title': 'Licence',
                'searchable': False,
                'orderable': False
            },
            {
                'title': 'Action',
                'searchable': False,
                'orderable': False
            }
        ]
        data['licences']['ajax']['url'] = reverse('dashboard:data_licences_officer')
        # filters (note: there is already the licenceType from the super class)
        filters = {
            'date': {
                'values': [
                    (self.DATE_FILTER_ACTIVE, self.DATE_FILTER_ACTIVE.capitalize()),
                    (self.DATE_FILTER_EXPIRING, self.DATE_FILTER_EXPIRING.capitalize()),
                    (self.DATE_FILTER_EXPIRED, self.DATE_FILTER_EXPIRED.capitalize()),
                    (self.DATE_FILTER_ALL, self.DATE_FILTER_ALL.capitalize()),
                ]
            }
        }
        data['licences']['filters'].update(filters)
        # global table options
        data['licences']['tableOptions'] = {
            'pageLength': 25
        }
        return data


class DataTableLicencesOfficerView(DataTableBaseView):
    model = WildlifeLicence
    columns = ['licence_no', 'licence_type.code', 'profile.user', 'start_date', 'end_date', 'licence', 'action']
    order_columns = ['licence_no', 'licence_type.code', 'issue_date', 'start_date', 'end_date', '', '']

    columns_helpers = {
        'profile.user': {
            'render': lambda self, instance: render_user_name(instance.profile.user, first_name_first=False),
            'search': lambda self, search: _build_field_query([
                'profile__user__last_name', 'profile__user__first_name'],
                search),
        },
        'issue_date': {
            'render': lambda self, instance: _render_date(instance.issue_date)
        },
        'start_date': {
            'render': lambda self, instance: _render_date(instance.start_date)
        },
        'end_date': {
            'render': lambda self, instance: _render_date(instance.end_date)
        },
        'licence': {
            'render': lambda self, instance: _render_licence_document(instance)
        },
        'action': {
            'render': lambda self, instance: self._render_action(instance)
        }
    }

    @staticmethod
    def filter_date(value):
        today = datetime.date.today()
        if value == TableLicencesOfficerView.DATE_FILTER_ACTIVE:
            return Q(start_date__lte=today) & Q(end_date__gte=today)
        elif value == TableLicencesOfficerView.DATE_FILTER_EXPIRING:
            return Q(end_date__gte=today) & Q(end_date__lte=today + datetime.timedelta(days=30))
        elif value == TableLicencesOfficerView.DATE_FILTER_EXPIRED:
            return Q(end_date__lt=today)
        else:
            return None

    def filter_licence_type(self, value):
        if value.lower() != 'all':
            return Q(licence_type__pk=value)
        else:
            return None

    @staticmethod
    def _render_action(instance):
        url = reverse('applications:reissue_licence', args=(instance.pk,))
        return '<a href="{0}">Reissue</a>'.format(url)

    def get_initial_queryset(self):
        return WildlifeLicence.objects.all()


########################
#    Assessors
########################

class TableAssessorView(AssessorRequiredMixin, TableApplicationsOfficerView):
    """
    Same table as officer with limited filters
    """
    template_name = 'wl/dash_tables_assessor.html'

    def _build_data(self):
        data = super(TableApplicationsOfficerView, self)._build_data()
        data['applications']['columnDefinitions'] = [
            {
                'title': 'Lodge No.'
            },
            {
                'title': 'Licence Type'
            },
            {
                'title': 'User'
            },
            {
                'title': 'Lodged on'
            },
            {
                'title': 'Assigned Officer'
            },
            {
                'title': 'Action',
                'searchable': False,
                'orderable': False
            }
        ]
        data['applications']['ajax']['url'] = reverse('dashboard:data_application_assessor')
        return data


class DataTableApplicationAssessorView(OfficerOrAssessorRequiredMixin, DataTableApplicationBaseView):
    """
    Model of this table is not Application but Assessment
     see: get_initial_queryset method
    """
    columns = [
        'application.lodgement_number',
        'application.licence_type.code',
        'application.applicant_profile.user',
        'application.lodgement_date',
        'application.assigned_officer',
        'action'
    ]
    order_columns = [
        'application.lodgement_number',
        'application.licence_type.code',
        ['application.applicant_profile.user.last_name', 'application.applicant_profile.user.first_name',
         'application.applicant_profile.user.email'],
        'application.lodgement_date',
        ['application.assigned_officer.first_name', 'application.assigned_officer.last_name',
         'application.assigned_officer.email'], ''
    ]

    def _render_action_column(self, obj):
        return '<a href="{0}">Review</a>'.format(
            reverse('applications:enter_conditions_assessor', args=[obj.application.pk, obj.pk])
        )

    def _search_assignee_query(self, search):
        fields_to_search = ['application__assigned_officer__last_name',
                            'application__assigned_officer__first_name',
                            'application__assigned_officer__email']
        return self._build_search_query(fields_to_search, search)

    def _render_assignee_column(self, obj):
        return render_user_name(obj.application.assigned_officer)

    def _render_lodgement_date(self, obj):
        return _render_date(obj.application.lodgement_date)

    def _render_applicant(self, obj):
        return super(DataTableApplicationAssessorView, self)._render_user_column(obj.application),

    def _search_user_query(self, search):
        fields_to_search = ['application__applicant_profile__user__last_name',
                            'application__applicant_profile__user__first_name']
        return self._build_search_query(fields_to_search, search)

    columns_helpers = dict(**{
        'application.applicant_profile.user': {
            'render': _render_applicant,
            'search': _search_user_query
        },
        'application.assigned_officer': {
            'search': _search_assignee_query,
            'render': _render_assignee_column,
        },
        'action': {
            'render': _render_action_column,
        },
        'application.lodgement_date': {
            'render': _render_lodgement_date,
        },
    })

    def get_initial_queryset(self):
        groups = self.request.user.assessorgroup_set.all()
        assessments = Assessment.objects.filter(assessor_group__in=groups).filter(
            status='awaiting_assessment')
        return assessments


########################
#    Customers
########################


class TableCustomerView(LoginRequiredMixin, TableBaseView):
    template_name = 'wl/dash_tables_customer.html'

    def _build_data(self):
        data = super(TableCustomerView, self)._build_data()
        data['applications']['columnDefinitions'] = [
            {
                'title': 'Lodge No.'
            },
            {
                'title': 'Licence Type'
            },
            {
                'title': 'Profile'
            },
            {
                'title': 'Status'
            },
            {
                'title': 'Lodged on'
            },
            {
                'title': 'Action',
                'searchable': False,
                'orderable': False
            }
        ]
        data['applications']['filters']['status']['values'] = \
            [('all', 'All')] + list(Application.CUSTOMER_STATUS_CHOICES)
        data['applications']['ajax']['url'] = reverse('dashboard:data_application_customer')

        data['licences']['columnDefinitions'] = [
            {
                'title': 'Licence No.'
            },
            {
                'title': 'Licence Type'
            },
            {
                'title': 'Issue Date'
            },
            {
                'title': 'Start Date'
            },
            {
                'title': 'Expiry Date'
            },
            {
                'title': 'Licence',
                'searchable': False,
                'orderable': False
            },
            {
                'title': 'Action',
                'searchable': False,
                'orderable': False
            }
        ]
        data['licences']['ajax']['url'] = reverse('dashboard:data_licences_customer')
        return data


class DataTableApplicationCustomerView(DataTableApplicationBaseView):
    columns = ['lodgement_number', 'licence_type.code', 'applicant_profile', 'customer_status', 'lodgement_date',
               'action']
    order_columns = ['lodgement_number', 'licence_type.code', 'applicant_profile', 'customer_status', 'lodgement_date',
                     '']

    def get_initial_queryset(self):
        return _get_user_applications(self.request.user)

    def _build_status_filter(self, status_value):
        return Q(customer_status=status_value) if status_value != 'all' else Q()

    def _render_action_column(self, obj):
        status = obj.customer_status
        if status == 'draft':
            return '<a href="{0}">{1}</a>'.format(
                reverse('applications:edit_application', args=[obj.licence_type.code, obj.pk]),
                'Continue application'
            )
        elif status == 'amendment_required' or status == 'id_and_amendment_required':
            return '<a href="{0}">{1}</a>'.format(
                reverse('applications:edit_application', args=[obj.licence_type.code, obj.pk]),
                'Amend application'
            )
        elif status == 'id_required' and obj.id_check_status == 'awaiting_update':
            return '<a href="{0}">{1}</a>'.format(
                reverse('main:identification'),
                'Update ID')
        elif obj.processing_status == 'issued' and obj.licence is not None and obj.licence.document is not None:
            return '<a href="{0}" target="_blank">View licence</a>'.format(
                obj.licence.document.file.url
            )
        else:
            return 'Locked'

    def _render_lodgement_date(self, obj):
        return _render_date(obj.lodgement_date)

    columns_helpers = dict(DataTableApplicationBaseView.columns_helpers.items(), **{
        'action': {
            'render': _render_action_column,
        },
        'lodgement_date': {
            'render': _render_lodgement_date
        },
    })


class DataTableLicencesCustomerView(DataTableBaseView):
    model = WildlifeLicence
    columns = ['licence_no', 'licence_type.code', 'issue_date', 'start_date', 'end_date', 'licence', 'action']
    order_columns = ['licence_no', 'licence_type.code', 'issue_date', 'start_date', 'end_date', '', '']

    columns_helpers = {
        'issue_date': {
            'render': lambda self, instance: _render_date(instance.issue_date)
        },
        'start_date': {
            'render': lambda self, instance: _render_date(instance.start_date)
        },
        'end_date': {
            'render': lambda self, instance: _render_date(instance.end_date)
        },
        'licence': {
            'render': lambda self, instance: _render_licence_document(instance)
        },
        'action': {
            'render': lambda self, instance: self._render_action(instance)
        }
    }

    @staticmethod
    def _can_user_renew_licence(license):
        return license.licence_type.is_renewable \
               and license.end_date <= datetime.date.today() + datetime.timedelta(days=30)

    @staticmethod
    def _render_action(instance):
        if not DataTableLicencesCustomerView._can_user_renew_licence(instance):
            return 'Not renewable'

        try:
            application = Application.objects.get(licence=instance)
            if Application.objects.filter(previous_application=application).exists():
                return 'Renewed'
        except Application.DoesNotExist:
            pass

        url = reverse('applications:renew_licence', args=(instance.pk,))
        return '<a href="{0}">Renew</a>'.format(url)

    def get_initial_queryset(self):
        return _get_user_licences(self.request.user)