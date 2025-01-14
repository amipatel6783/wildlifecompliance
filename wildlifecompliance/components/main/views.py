import traceback
import logging
from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework import serializers, views, status
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from wildlifecompliance.components.main.utils import (
    search_keywords,
    search_reference,
    #retrieve_department_users,
)
from wildlifecompliance.components.main.serializers import (
    SearchKeywordSerializer,
    SearchReferenceSerializer,
)
from wildlifecompliance.components.main.related_item import (
        RelatedItemsSerializer,
        WeakLinks,
        get_related_items, 
        format_model_name,
        search_weak_links
       )
from django.contrib.auth.models import ContentType
from django.conf import settings
from wildlifecompliance.components.users.models import (
        #CompliancePermissionGroup, 
        ComplianceManagementUserPreferences,
        )
from wildlifecompliance.helpers import (
        is_compliance_management_readonly_user, 
        is_compliance_management_callemail_readonly_user,
        prefer_compliance_management,
        )

logger = logging.getLogger(__name__)

class GeocodingAddressSearchTokenView(views.APIView):
    def get(self, request, format=None):
        return Response({"access_token": settings.GEOCODING_ADDRESS_SEARCH_TOKEN})


class SystemPreferenceView(views.APIView):
    def get(self, request, format=None):
        #import ipdb; ipdb.set_trace()
        res = { "system": "wildlife_licensing" }
        if prefer_compliance_management(request):
            res = { "system": "compliance_management" }
        return Response(res)


#class DepartmentUserView(views.APIView):
#    renderer_classes = [JSONRenderer]
#
#    def get(self, request, format=None):
#        qs = []
#        #if request.data.get('searchText'): # modify as appropriate
#         #   qs = search_weak_links(request.data)
#        qs = retrieve_department_users()
#        #return_qs = qs[:10]
#        #return Response(return_qs)
#        return Response(qs)


class SearchKeywordsView(views.APIView):
    renderer_classes = [JSONRenderer]

    def post(self, request, format=None):
        qs = []
        search_words = request.data.get('searchKeywords')
        search_application = request.data.get('searchApplication')
        search_licence = request.data.get('searchLicence')
        search_returns = request.data.get('searchReturn')
        is_internal = request.data.get('is_internal')
        if search_words:
            qs = search_keywords(search_words, search_application, search_licence, search_returns, is_internal)
        serializer = SearchKeywordSerializer(qs, many=True)
        return Response(serializer.data)


class SearchWeakLinksView(views.APIView):
    renderer_classes = [JSONRenderer]

    def post(self, request, format=None):
        qs = []
        if request.data.get('searchText'): # modify as appropriate
            qs = search_weak_links(request.data)
        return_qs = qs[:10]
        return Response(return_qs)


class CreateWeakLinkView(views.APIView):
    renderer_classes = [JSONRenderer]

    def post(self, request, format=None):
        try:
            with transaction.atomic():
                first_content_type_str = request.data.get('first_content_type')
                first_object_id = request.data.get('first_object_id')
                second_content_type_str = request.data.get('second_content_type')
                second_object_id = request.data.get('second_object_id')
                can_user_action = request.data.get('can_user_action')
                comment = request.data.get('comment')
                
                if can_user_action:
                    # transform request data to create new Weak Links obj
                    second_object_id_int = int(second_object_id)
                    first_content_type = ContentType.objects.get(
                            app_label='wildlifecompliance', 
                            model=first_content_type_str)
                    second_content_type = ContentType.objects.get(
                            app_label='wildlifecompliance', 
                            model=second_content_type_str)
                    
                    weak_link_instance, created = WeakLinks.objects.get_or_create(
                            first_content_type_id = first_content_type.id,
                            first_object_id = first_object_id,
                            second_content_type_id = second_content_type.id,
                            second_object_id = second_object_id_int,
                            comment = comment
                            )
                    # derive parent (calling) object instance from weak_link_instance
                    calling_instance = weak_link_instance.first_content_type.model_class().objects.get(id=first_object_id)
                    secondary_instance = weak_link_instance.second_content_type.model_class().objects.get(id=second_object_id_int)

                    # log user action for both calling and secondary instances
                    calling_instance.log_user_action(
                        calling_instance.action_logs.model.ACTION_ADD_WEAK_LINK.format(
                        format_model_name(first_content_type.model),
                        calling_instance.get_related_items_identifier,
                        format_model_name(second_content_type.model),
                        secondary_instance.get_related_items_identifier
                        ), 
                        request)
                    secondary_instance.log_user_action(
                        secondary_instance.action_logs.model.ACTION_ADD_WEAK_LINK.format(
                        format_model_name(first_content_type.model),
                        calling_instance.get_related_items_identifier,
                        format_model_name(second_content_type.model),
                        secondary_instance.get_related_items_identifier
                        ), 
                        request)

                    # get related items of calling_instance
                    related_items = get_related_items(calling_instance)
                    return Response(
                            related_items,
                            status=status.HTTP_200_OK,
                            )
                else:
                    content = {'message': 'User does not have permission to perform this action'}
                    return Response(content, status=status.HTTP_403_FORBIDDEN)

        except Exception as e:
            print(traceback.print_exc())
            raise e


class RemoveWeakLinkView(views.APIView):
    renderer_classes = [JSONRenderer]

    def post(self, request, format=None):
        try:
            with transaction.atomic():
                # These are the presumptive first_content and second_content values, but may be reversed
                first_content_type_str = request.data.get('first_content_type')
                first_object_id = request.data.get('first_object_id')
                second_content_type_str = request.data.get('second_content_type')
                second_object_id = request.data.get('second_object_id')
                can_user_action = request.data.get('can_user_action')
                calling_instance = None
                paired_instance = None

                if can_user_action:
                    # transform request data to search for Weak Link obj to delete
                    second_object_id_int = int(second_object_id)
                    first_content_type = ContentType.objects.get(
                            app_label='wildlifecompliance', 
                            model=first_content_type_str)
                    second_content_type = ContentType.objects.get(
                            app_label='wildlifecompliance', 
                            model=second_content_type_str)

                    weak_link_qs = WeakLinks.objects.filter(
                            first_content_type_id = first_content_type.id,
                            first_object_id = first_object_id,
                            second_content_type_id = second_content_type.id,
                            second_object_id = second_object_id_int
                            )
                    if weak_link_qs:
                        weak_link_instance = weak_link_qs[0]
                        calling_instance = first_content_type.model_class().objects.get(id=first_object_id)
                        paired_instance = weak_link_instance.second_content_type.model_class().objects.get(id=second_object_id_int)

                        # calling instance will be Weak Link originator
                        calling_instance.log_user_action(
                            calling_instance.action_logs.model.ACTION_REMOVE_WEAK_LINK.format(
                            format_model_name(first_content_type.model),
                            calling_instance.get_related_items_identifier,
                            format_model_name(second_content_type.model),
                            paired_instance.get_related_items_identifier
                            ),
                            request)
                        paired_instance.log_user_action(
                            paired_instance.action_logs.model.ACTION_REMOVE_WEAK_LINK.format(
                            format_model_name(first_content_type.model),
                            calling_instance.get_related_items_identifier,
                            format_model_name(second_content_type.model),
                            paired_instance.get_related_items_identifier
                            ), 
                            request)
                        # delete from db
                        weak_link_instance.delete()
                    else:
                    # If weak link obj not found, test for object with first and second fields reversed and delete that instead.
                        weak_link_qs = WeakLinks.objects.filter(
                                first_content_type_id = second_content_type.id,
                                first_object_id = second_object_id_int,
                                second_content_type_id = first_content_type.id,
                                second_object_id = first_object_id
                                )
                        if weak_link_qs:
                            weak_link_instance = weak_link_qs[0]
                            # primary object
                            paired_instance = second_content_type.model_class().objects.get(id=second_object_id_int)
                            # secondary object
                            calling_instance = weak_link_instance.second_content_type.model_class().objects.get(id=first_object_id)

                            # must reverse first_content and second_content positions
                            paired_instance.log_user_action(
                                paired_instance.action_logs.model.ACTION_REMOVE_WEAK_LINK.format(
                                format_model_name(second_content_type.model),
                                paired_instance.get_related_items_identifier,
                                format_model_name(first_content_type.model),
                                calling_instance.get_related_items_identifier
                                ), 
                                request)
                            calling_instance.log_user_action(
                                calling_instance.action_logs.model.ACTION_REMOVE_WEAK_LINK.format(
                                format_model_name(second_content_type.model),
                                paired_instance.get_related_items_identifier,
                                format_model_name(first_content_type.model),
                                calling_instance.get_related_items_identifier
                                ), 
                                request)
                            # delete from db
                            weak_link_instance.delete()
                    # get related items of calling_instance
                    related_items = get_related_items(calling_instance)
                    return Response(related_items)
                else:
                    content = {'message': 'User does not have permission to perform this action'}
                    return Response(content, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            print(traceback.print_exc())
            raise e


class SearchReferenceView(views.APIView):
    renderer_classes = [JSONRenderer]

    def post(self, request, format=None):
        try:
            #qs = []
            reference_number = request.data.get('reference_number')
            if reference_number:
                result = search_reference(reference_number)
            #serializer = SearchReferenceSerializer(qs)
            #return Response(serializer.data)
            return Response(result)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                logger.error('SearchReferenceView(): {0}'.format(e))
                # raise serializers.ValidationError(repr(e[0].encode('utf-8')))
                raise serializers.ValidationError(repr(e[0]))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

