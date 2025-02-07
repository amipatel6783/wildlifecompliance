from __future__ import unicode_literals
import logging
from django.db import models
from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.postgres.fields.jsonb import JSONField
from django.db.models import Max
from django.contrib.auth.models import Permission, ContentType
from multiselectfield import MultiSelectField
from django.utils.encoding import python_2_unicode_compatible
from rest_framework import serializers
from ledger.accounts.models import EmailUser, RevisionedMixin
from ledger.licence.models import LicenceType
from wildlifecompliance.components.main.models import (
        CommunicationsLogEntry,
        UserAction, 
        Document,
        #CallEmailTriageGroup, OfficerGroup, ManagerGroup,
        ComplianceManagementSystemGroup,
        )
from wildlifecompliance.components.main.related_item import can_close_record
#from wildlifecompliance.components.users.models import CompliancePermissionGroup
from wildlifecompliance.components.main.models import Region, District

logger = logging.getLogger(__name__)

def update_compliance_doc_filename(instance, filename):
    #return 'wildlifecompliance/compliance/{}/documents/{}'.format(
        #instance.call_email.id, filename)
    pass

def update_call_email_doc_filename(instance, filename):
    # return 'wildlifecompliance/compliance/{}/documents/{}'.format(
      #  instance.call_email.id, filename)
    pass

def update_compliance_comms_log_filename(instance, filename):
    #return 'wildlifecompliance/compliance/{}/communications/{}/{}'.format(
        #instance.log_entry.call_email.id, instance.id, filename)
    pass

def update_call_email_comms_log_filename(instance, filename):
    #return 'wildlifecompliance/compliance/{}/communications/{}/{}'.format(
     #   instance.log_entry.call_email.id, instance.id, filename)
    pass

def update_compliance_workflow_log_filename(instance, filename):
    #return 'wildlifecompliance/compliance/{}/workflow/{}/{}'.format(
        #instance.workflow.call_email.id, instance.id, filename)
    pass


class Classification(models.Model):
    CLASSIFICATION_COMPLAINT = 'complaint'
    CLASSIFICATION_ENQUIRY = 'enquiry'
    CLASSIFICATION_INCIDENT = 'incident'

    NAME_CHOICES = (
        (CLASSIFICATION_COMPLAINT, 'Complaint'),
        (CLASSIFICATION_ENQUIRY, 'Enquiry'),
        (CLASSIFICATION_INCIDENT, 'Incident'),
    )

    name = models.CharField(
        max_length=30,
        choices=NAME_CHOICES,
        default=CLASSIFICATION_COMPLAINT,
        unique=True
    )

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_Classification'
        verbose_name_plural = 'CM_Classifications'

    def __str__(self):
        return self.get_name_display()

class CallType(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True,
    )
    all_wildcare_species = models.BooleanField(default=False)
    call_type_index = models.SmallIntegerField(default=0,blank=True, null=True)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_CallType'
        verbose_name_plural = 'CM_CallTypes'

    def __str__(self):
        return self.name
        
class WildcareSpeciesType(models.Model):
    call_type=models.ForeignKey(CallType, on_delete=models.CASCADE , related_name='wildcare_species_types', blank=True, null=True)
    species_name = models.CharField(
        max_length=100,
        unique=True,
    )
    check_pinky_joey = models.BooleanField(default=False)
    show_species_name_textbox = models.BooleanField(default=False)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_WildcareSpeciesType'
        verbose_name_plural = 'CM_WildcareSpeciesTypes'
        ordering = ['species_name']
        #unique_together = ['species_name','call_type']

    def __str__(self):
        return self.species_name
        
class WildcareSpeciesSubType(models.Model):
    wildcare_species_type=models.ForeignKey(WildcareSpeciesType, on_delete=models.CASCADE , related_name='wildcare_species_sub_types', limit_choices_to={'show_species_name_textbox':False},)
    species_sub_name = models.CharField(
        max_length=100,
        #choices=WILDCARE_SPECIES_SUB_TYPE_CHOICES,
        unique=True,
    )

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_WildcareSpeciesSubType'
        verbose_name_plural = 'CM_WildcareSpeciesSubTypes'
        ordering = ['species_sub_name']
        #unique_together = ['species_sub_name','wildcare_species_type']

    def __str__(self):
        return self.species_sub_name


class Referrer(models.Model):
    name = models.CharField(max_length=50, blank=True)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_Referrer'
        verbose_name_plural = 'CM_Referrers'

    def __str__(self):
        return self.name


class ReportType(models.Model):

    report_type = models.CharField(max_length=50)
    schema = JSONField(null=True)
    version = models.SmallIntegerField(default=1, blank=False, null=False)
    description = models.CharField(max_length=255, blank=True, null=True)
    replaced_by = models.ForeignKey(
        'self', on_delete=models.PROTECT, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    #advice_url = models.CharField(max_length=255, blank=True, null=True, help_text="Should start with http://")
    advice_url = models.URLField(max_length=255, blank=True, null=True)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_CallEmailReportType'
        verbose_name_plural = 'CM_CallEmailReportTypes'
        unique_together = ('report_type', 'version')

    def __str__(self):
        return '{0}, v.{1}'.format(self.report_type, self.version)

    def referred_to(self):
        if self.referrer:
            return self.referrer.name


class Location(models.Model):

    STATE_CHOICES = (
        ('WA', 'Western Australia'),
        ('VIC', 'Victoria'),
        ('QLD', 'Queensland'),
        ('NSW', 'New South Wales'),
        ('TAS', 'Tasmania'),
        ('NT', 'Northern Territory'),
        ('ACT', 'Australian Capital Territory')
    )

    wkb_geometry = models.PointField(srid=4326, blank=True, null=True)
    street = models.CharField(max_length=100, blank=True, null=True)
    town_suburb = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(
        max_length=50, choices=STATE_CHOICES, blank=True, null=True, default='WA')
    postcode = models.CharField(max_length=10, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True, default='Australia')
    objects = models.GeoManager()
    details = models.TextField(blank=True)
    ben_number = models.CharField(max_length=100, blank=True, null=True)

    @property
    def call_email_id(self):
        if self.call_location.count() > 0:
            return self.call_location.first().id;

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_Location'
        verbose_name_plural = 'CM_Locations'

    def __str__(self):
        if self.country or self.state or self.town_suburb:
            return '{}, {}, {}, {}'.format(self.street, self.town_suburb, self.state, self.country)
        else:
            return self.details


class MapLayer(models.Model):
    display_name = models.CharField(max_length=100, blank=True, null=True)
    layer_name = models.CharField(max_length=200, blank=True, null=True)  # layer name defined in geoserver (kmi.dpaw.wa.gov.au)
    availability = models.BooleanField(default=True)  # False to hide from the frontend options

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_MapLayer'
        verbose_name_plural = 'CM_MapLayers'

    def __str__(self):
        return '{0}, {1}'.format(self.display_name, self.layer_name)


class CallEmail(RevisionedMixin):
    STATUS_DRAFT = 'draft'
    STATUS_OPEN = 'open'
    STATUS_OPEN_FOLLOWUP = 'open_followup'
    STATUS_OPEN_INSPECTION = 'open_inspection'
    STATUS_OPEN_CASE = 'open_case'
    STATUS_CLOSED = 'closed'
    STATUS_PENDING_CLOSURE = 'pending_closure'
    STATUS_CHOICES = (
        (STATUS_DRAFT, 'Draft'),
        (STATUS_OPEN, 'Open'),
        (STATUS_OPEN_FOLLOWUP, 'Open (follow-up)'),
        (STATUS_OPEN_INSPECTION, 'Open (Inspection)'),
        (STATUS_OPEN_CASE, 'Open (Case)'),
        (STATUS_CLOSED, 'Closed'),
        (STATUS_PENDING_CLOSURE, 'Pending Closure'),
    )

    ENTANGLED_NO = 'no'
    ENTANGLED_FISHING_LINE = 'fishing_line'
    ENTANGLED_ROPE = 'rope'
    ENTANGLED_STRING = 'string'
    ENTANGLED_WIRE = 'wire'
    ENTANGLED_OTHER = 'other'
    ENTANGLED_CHOICES = (
        (ENTANGLED_NO, 'No'),
        (ENTANGLED_FISHING_LINE, 'Fishing Line'),
        (ENTANGLED_ROPE, 'Rope'),
        (ENTANGLED_STRING, 'String'),
        (ENTANGLED_WIRE, 'Wire'),
        (ENTANGLED_OTHER, 'Other'),
    )

    GENDER_FEMALE = 'female'
    GENDER_MALE = 'male'
    GENDER_UNKNOWN = 'unknown'
    GENDER_CHOICES = (
        (GENDER_FEMALE, 'Female'),
        (GENDER_MALE, 'Male'),
        (GENDER_UNKNOWN, 'Unknown'),
    )

    AGE_BABY = 'baby'
    AGE_JUVENILE = 'juvenile'
    AGE_ADULT = 'adult'
    AGE_CHOICES = (
        (AGE_BABY, 'Baby'),
        (AGE_JUVENILE, 'Juvenile'),
        (AGE_ADULT, 'Adult'),
    )

    BABY_KANGAROO_PINKY = 'pinky'
    BABY_KANGAROO_JOEY = 'joey'
    BABY_KANGAROO_CHOICES = (
        (BABY_KANGAROO_PINKY, 'Pinky'),
        (BABY_KANGAROO_JOEY, 'Joey'),
    )

    status = models.CharField(
        max_length=40,
        choices=STATUS_CHOICES,
        default='draft')
    location = models.ForeignKey(
        Location,
        null=True,
        related_name="call_location"
    )
    classification = models.ForeignKey(
        Classification,
        null=True,
        related_name="call_classification"
    )
    call_type = models.ForeignKey(
        CallType,
        null=True,
        blank=True,
        related_name="call_type"
    )
    wildcare_species_type = models.ForeignKey(
        WildcareSpeciesType,
        null=True,
        blank=True,
        related_name="wildcare_species_type"
    )
    wildcare_species_sub_type = models.ForeignKey(
        WildcareSpeciesSubType,
        null=True,
        blank=True,
        related_name="wildcare_species_sub_type"
    )
    species_name = models.CharField(max_length=50, blank=True, null=True)
    dead = models.NullBooleanField()
    euthanise = models.NullBooleanField()
    number_of_animals = models.CharField(max_length=100, blank=True, null=True)
    brief_nature_of_call = models.TextField(blank=True)
    entangled = MultiSelectField(max_length=40, choices=ENTANGLED_CHOICES, blank=True, null=True)
    entangled_other = models.CharField(max_length=100, blank=True, null=True)
    gender = MultiSelectField(max_length=30, choices=GENDER_CHOICES, blank=True, null=True)
    baby_kangaroo = MultiSelectField(max_length=30, choices=BABY_KANGAROO_CHOICES, blank=True, null=True)
    age = MultiSelectField(max_length=30, choices=AGE_CHOICES, blank=True, null=True)
    lodged_on = models.DateField(auto_now_add=True)
    number = models.CharField(max_length=50, blank=True, null=True)
    caller = models.CharField(max_length=100, blank=True, null=True)
    caller_phone_number = models.CharField(max_length=50, blank=True, null=True)
    assigned_to = models.ForeignKey(
        EmailUser, 
        related_name='callemail_assigned_to',
        null=True
    )
    volunteer = models.ForeignKey(
        EmailUser, 
        related_name='callemail_volunteer',
        null=True
    )
    anonymous_call = models.BooleanField(default=False)
    caller_wishes_to_remain_anonymous = models.BooleanField(default=False)
    occurrence_from_to = models.BooleanField(default=False)
    occurrence_date_from = models.DateField(null=True)
    occurrence_time_from = models.CharField(max_length=20, blank=True, null=True)
    occurrence_time_start = models.TimeField(blank=True, null=True)
    occurrence_date_to = models.DateField(null=True)
    occurrence_time_to = models.CharField(max_length=20, blank=True, null=True)
    occurrence_time_end = models.TimeField(blank=True, null=True)
    date_of_call = models.DateField(null=True)
    time_of_call = models.TimeField(blank=True, null=True)
    report_type = models.ForeignKey(
        ReportType,
        null=True,
        related_name='call_schema',
    )
    referrer = models.ManyToManyField(
        Referrer,
        blank=True,
        # related_name="report_referrer"
    )
    email_user = models.ForeignKey(
        EmailUser,
        null=True,
    )
    advice_given = models.BooleanField(default=False)
    advice_details = models.TextField(blank=True, null=True)
    #region = models.ForeignKey(
    #    Region, 
    #    related_name='callemail_region', 
    #    null=True
    #)
    #district = models.ForeignKey(
    #    District, 
    #    related_name='callemail_district', 
    #    null=True
    #)
    allocated_group = models.ForeignKey(
        ComplianceManagementSystemGroup,
        null=True
    )

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_Call/Email'
        verbose_name_plural = 'CM_Calls/Emails'

    def __str__(self):
        return 'ID: {0}, Status: {1}, Number: {2}, Caller: {3}, Assigned To: {4}' \
            .format(self.id, self.status, self.number, self.caller, self.assigned_to)
    
    # Prefix "C" char to CallEmail number.
    def save(self, *args, **kwargs):
        
        super(CallEmail, self).save(*args,**kwargs)
        if self.number is None:
            new_number_id = 'C{0:06d}'.format(self.pk)
            self.number = new_number_id
            self.save()
        
    @property
    def data(self):
        """ returns a queryset of form data records attached to CallEmail (shortcut to ComplianceFormDataRecord related_name). """
        return self.form_data_records.all()

    @property
    def schema(self):
        
        if self.report_type:
            return self.report_type.schema
    
    #def log_user_action(self, action, request):
     #   return CallEmailUserAction.log_action(self, action, request.user)
    def log_user_action(self, action, request=None):
        if request:
            return CallEmailUserAction.log_action(self, action, request.user)
        else:
            return CallEmailUserAction.log_action(self, action)

    @property
    def get_related_items_identifier(self):
        return self.number

    @property
    def get_related_items_descriptor(self):
        #return '{0}, {1}'.format(self.status, self.caller)
        return self.caller
    # @property
    # def related_items(self):
    #     return get_related_items(self)

    #def set_allocated_group(self, permission_codename, region_id=None, district_id=None):
    #    #import ipdb; ipdb.set_trace()
    #    if district_id:
    #        region_id = None
    #    compliance_content_type = ContentType.objects.get(model="compliancepermissiongroup")
    #    permission = Permission.objects.filter(codename=permission_codename).filter(content_type_id=compliance_content_type.id).first()
    #    self.allocated_group = CompliancePermissionGroup.objects.get(permissions=permission, region_id=region_id, district_id=district_id)
    #    #request_data.update({'allocated_group_id': group.id})
    #    self.save()

    def forward_to_regions(self, request):
        if not self.location:
            raise serializers.ValidationError({"Location": "must be recorded"})
        region_id = None if not request.data.get('region_id') else request.data.get('region_id')
        district_id = None if not request.data.get('district_id') else request.data.get('district_id')
        #self.allocated_group =  CallEmailTriageGroup.objects.get(region_id=region_id, district_id=district_id)
        self.allocated_group =  ComplianceManagementSystemGroup.objects.get(name=settings.GROUP_CALL_EMAIL_TRIAGE, region_id=region_id, district_id=district_id)
        self.status = self.STATUS_OPEN
        self.log_user_action(
            CallEmailUserAction.ACTION_FORWARD_TO_REGIONS.format(self.number),
            request)
        self.save()

    def forward_to_wildlife_protection_branch(self, request):
        if not self.location:
            raise serializers.ValidationError({"Location": "must be recorded"})
        self.allocated_group =  ComplianceManagementSystemGroup.objects.get(name=settings.GROUP_CALL_EMAIL_TRIAGE, region=Region.objects.get(head_office=True))
        #self.allocated_group = CallEmailTriageGroup.objects.get(region=Region.objects.get(head_office=True))
        self.status = self.STATUS_OPEN
        self.log_user_action(
            CallEmailUserAction.ACTION_FORWARD_TO_WILDLIFE_PROTECTION_BRANCH.format(self.number),
            request)
        self.save()

    def allocate_for_follow_up(self, request):
        region_id = None if not request.data.get('region_id') else request.data.get('region_id')
        district_id = None if not request.data.get('district_id') else request.data.get('district_id')
        if district_id:
            region_id = None
        self.allocated_group = OfficerGroup.objects.get(region_id=region_id, district_id=district_id)
        self.status = self.STATUS_OPEN_FOLLOWUP
        self.log_user_action(
                CallEmailUserAction.ACTION_ALLOCATE_FOR_FOLLOWUP.format(self.number),
                request)
        self.save()

    def allocate_for_inspection(self, request):
        region_id = None if not request.data.get('region_id') else request.data.get('region_id')
        district_id = None if not request.data.get('district_id') else request.data.get('district_id')
        if district_id:
            region_id = None
        self.allocated_group = OfficerGroup.objects.get(region_id=region_id, district_id=district_id)
        self.status = self.STATUS_OPEN_INSPECTION
        self.log_user_action(
                CallEmailUserAction.ACTION_ALLOCATE_FOR_INSPECTION.format(self.number),
                request)
        self.save()

    def allocate_for_case(self, request):
        region_id = None if not request.data.get('region_id') else request.data.get('region_id')
        district_id = None if not request.data.get('district_id') else request.data.get('district_id')
        if district_id:
            region_id = None
        self.allocated_group = OfficerGroup.objects.get(region_id=region_id, district_id=district_id)
        self.status = self.STATUS_OPEN_CASE
        self.log_user_action(
                CallEmailUserAction.ACTION_ALLOCATE_FOR_CASE.format(self.number),
                request)
        self.save()

    def close(self, request=None):
        close_record, parents = can_close_record(self, request)
        if close_record:
            self.status = self.STATUS_CLOSED
            self.log_user_action(
                    CallEmailUserAction.ACTION_CLOSE.format(self.number), 
                    request)
        else:
            self.status = self.STATUS_PENDING_CLOSURE
            self.log_user_action(
                    CallEmailUserAction.ACTION_PENDING_CLOSURE.format(self.number), 
                    request)
        self.save()
        # Call Email has no parents in pending_closure status

    def add_offence(self, request):
        self.log_user_action(
                CallEmailUserAction.ACTION_OFFENCE.format(self.number), 
                request)
        self.save()

    def add_sanction_outcome(self, request):
        self.log_user_action(
                CallEmailUserAction.ACTION_SANCTION_OUTCOME.format(self.number), 
                request)
        self.save()

    def add_referrers(self, request):
        referrers_selected = request.data.get('referrers_selected').split(",")
        for selection in referrers_selected:
            print(selection)
            try:
                selection_int = int(selection)
            except Exception as e:
                raise e
            referrer = Referrer.objects.get(id=selection_int)
            if referrer:
                self.referrer.add(referrer)
        self.save()

@python_2_unicode_compatible
class ComplianceFormDataRecord(models.Model):

    INSTANCE_ID_SEPARATOR = "__instance-"

    ACTION_TYPE_ASSIGN_VALUE = 'value'
    ACTION_TYPE_ASSIGN_COMMENT = 'comment'

    COMPONENT_TYPE_TEXT = 'text'
    COMPONENT_TYPE_TAB = 'tab'
    COMPONENT_TYPE_SECTION = 'section'
    COMPONENT_TYPE_GROUP = 'group'
    COMPONENT_TYPE_NUMBER = 'number'
    COMPONENT_TYPE_EMAIL = 'email'
    COMPONENT_TYPE_SELECT = 'select'
    COMPONENT_TYPE_MULTI_SELECT = 'multi-select'
    COMPONENT_TYPE_TEXT_AREA = 'text_area'
    COMPONENT_TYPE_TABLE = 'table'
    COMPONENT_TYPE_EXPANDER_TABLE = 'expander_table'
    COMPONENT_TYPE_LABEL = 'label'
    COMPONENT_TYPE_RADIO = 'radiobuttons'
    COMPONENT_TYPE_CHECKBOX = 'checkbox'
    COMPONENT_TYPE_DECLARATION = 'declaration'
    COMPONENT_TYPE_FILE = 'file'
    COMPONENT_TYPE_DATE = 'date'
    COMPONENT_TYPE_CHOICES = (
        (COMPONENT_TYPE_TEXT, 'Text'),
        (COMPONENT_TYPE_TAB, 'Tab'),
        (COMPONENT_TYPE_SECTION, 'Section'),
        (COMPONENT_TYPE_GROUP, 'Group'),
        (COMPONENT_TYPE_NUMBER, 'Number'),
        (COMPONENT_TYPE_EMAIL, 'Email'),
        (COMPONENT_TYPE_SELECT, 'Select'),
        (COMPONENT_TYPE_MULTI_SELECT, 'Multi-Select'),
        (COMPONENT_TYPE_TEXT_AREA, 'Text Area'),
        (COMPONENT_TYPE_TABLE, 'Table'),
        (COMPONENT_TYPE_EXPANDER_TABLE, 'Expander Table'),
        (COMPONENT_TYPE_LABEL, 'Label'),
        (COMPONENT_TYPE_RADIO, 'Radio'),
        (COMPONENT_TYPE_CHECKBOX, 'Checkbox'),
        (COMPONENT_TYPE_DECLARATION, 'Declaration'),
        (COMPONENT_TYPE_FILE, 'File'),
        (COMPONENT_TYPE_DATE, 'Date'),
    )

    call_email = models.ForeignKey(CallEmail, related_name='form_data_records')
    field_name = models.CharField(max_length=512, blank=True, null=True)
    schema_name = models.CharField(max_length=256, blank=True, null=True)
    instance_name = models.CharField(max_length=256, blank=True, null=True)
    component_type = models.CharField(
        max_length=64,
        choices=COMPONENT_TYPE_CHOICES,
        default=COMPONENT_TYPE_TEXT)
    value = JSONField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    deficiency = models.TextField(blank=True, null=True)

    def __str__(self):
        return "CallEmail {id} record {field}: {value}".format(
            id=self.call_email_id,
            field=self.field_name,
            value=self.value[:8]
        )

    class Meta:
        app_label = 'wildlifecompliance'
        unique_together = ('call_email', 'field_name',)

    @staticmethod
    def process_form(request, CallEmail, form_data, action=ACTION_TYPE_ASSIGN_VALUE):
        can_edit_comments = request.user.has_perm(
            'wildlifecompliance.licensing_officer'
        ) or request.user.has_perm(
            'wildlifecompliance.assessor'
        )
        can_edit_deficiencies = request.user.has_perm(
            'wildlifecompliance.licensing_officer'
        )

        if action == ComplianceFormDataRecord.ACTION_TYPE_ASSIGN_COMMENT and\
                not can_edit_comments and not can_edit_deficiencies:
            raise Exception(
                'You are not authorised to perform this action!')
        
        for field_name, field_data in form_data.items():
            schema_name = field_data.get('schema_name', '')
            component_type = field_data.get('component_type', '')
            value = field_data.get('value', '')
            comment = field_data.get('comment_value', '')
            deficiency = field_data.get('deficiency_value', '')
            instance_name = ''

            if ComplianceFormDataRecord.INSTANCE_ID_SEPARATOR in field_name:
                [parsed_schema_name, instance_name] = field_name.split(
                    ComplianceFormDataRecord.INSTANCE_ID_SEPARATOR
                )
                schema_name = schema_name if schema_name else parsed_schema_name

            form_data_record, created = ComplianceFormDataRecord.objects.get_or_create(
                call_email_id=CallEmail.id,
                field_name=field_name
            )
            if created:
                form_data_record.schema_name = schema_name
                form_data_record.instance_name = instance_name
                form_data_record.component_type = component_type
            if action == ComplianceFormDataRecord.ACTION_TYPE_ASSIGN_VALUE:
                form_data_record.value = value
            elif action == ComplianceFormDataRecord.ACTION_TYPE_ASSIGN_COMMENT:
                if can_edit_comments:
                    form_data_record.comment = comment
                if can_edit_deficiencies:
                    form_data_record.deficiency = deficiency
            form_data_record.save()


class CallEmailDocument(Document):
    call_email = models.ForeignKey('CallEmail', related_name='documents')
    #_file = models.FileField(max_length=255, upload_to=update_call_email_doc_filename)
    _file = models.FileField(max_length=255)
    input_name = models.CharField(max_length=255, blank=True, null=True)
    # after initial submit prevent document from being deleted
    can_delete = models.BooleanField(default=True)
    version_comment = models.CharField(max_length=255, blank=True, null=True)

    def delete(self):
        if self.can_delete:
            return super(CallEmailDocument, self).delete()
        logger.info(
            'Cannot delete existing document object after application has been submitted (including document submitted before\
            application pushback to status Draft): {}'.format(
                self.name)
        )

    class Meta:
        app_label = 'wildlifecompliance'


class CallEmailLogDocument(Document):
    #name = models.CharField(max_length=100, blank=True,
     #       verbose_name='name', help_text='')
    log_entry = models.ForeignKey(
        'CallEmailLogEntry',
        related_name='documents')
    #input_name = models.CharField(max_length=255, blank=True, null=True)
    #version_comment = models.CharField(max_length=255, blank=True, null=True)
    #_file = models.FileField(max_length=255, upload_to=update_call_email_comms_log_filename)
    _file = models.FileField(max_length=255)

    class Meta:
        app_label = 'wildlifecompliance'


class CallEmailLogEntry(CommunicationsLogEntry):
    call_email = models.ForeignKey(CallEmail, related_name='comms_logs')

    class Meta:
        app_label = 'wildlifecompliance'


class CallEmailUserAction(models.Model):
    ACTION_CREATE_CALL_EMAIL = "Create Call/Email {}"
    ACTION_SAVE_CALL_EMAIL_ = "Save Call/Email {}"
    ACTION_FORWARD_TO_REGIONS = "Forward Call/Email {} to regions"
    ACTION_FORWARD_TO_WILDLIFE_PROTECTION_BRANCH = "Forward Call/Email {} to Wildlife Protection Branch"
    ACTION_ALLOCATE_FOR_FOLLOWUP = "Allocate Call/Email {} for follow up"
    ACTION_ALLOCATE_FOR_INSPECTION = "Allocate Call/Email {} for inspection"
    ACTION_ALLOCATE_FOR_LEGAL_CASE = "Allocate Call/Email {} for case"
    ACTION_CLOSE = "Close Call/Email {}"
    ACTION_PENDING_CLOSURE = "Mark Call/Email {} as pending closure"
    ACTION_OFFENCE = "Create linked offence for Call/Email {}"
    ACTION_SANCTION_OUTCOME = "Create Sanction Outcome for Call/Email {}"
    ACTION_PERSON_SEARCH = "Linked person to Call/Email {}"
    # ACTION_ADD_WEAK_LINK = "Create manual link between Call/Email: {} and {}: {}"
    # ACTION_REMOVE_WEAK_LINK = "Remove manual link between Call/Email: {} and {}: {}"
    ACTION_ADD_WEAK_LINK = "Create manual link between {}: {} and {}: {}"
    ACTION_REMOVE_WEAK_LINK = "Remove manual link between {}: {} and {}: {}"

    who = models.ForeignKey(EmailUser, null=True, blank=True)
    when = models.DateTimeField(null=False, blank=False, auto_now_add=True)
    what = models.TextField(blank=False)

    class Meta:
        app_label = 'wildlifecompliance'
        ordering = ('-when',)

    @classmethod
    def log_action(cls, call_email, action, user=None):
        return cls.objects.create(
            call_email=call_email,
            who=user,
            what=str(action)
        )

    call_email = models.ForeignKey(CallEmail, related_name='action_logs')


import reversion
reversion.register(Classification, follow=['call_classification'])
reversion.register(CallType, follow=['wildcare_species_types', 'call_type'])
reversion.register(WildcareSpeciesType, follow=['wildcare_species_sub_types', 'wildcare_species_type'])
reversion.register(WildcareSpeciesSubType, follow=['wildcare_species_sub_type'])
reversion.register(Referrer, follow=['callemail_set'])
reversion.register(ReportType, follow=['reporttype_set', 'call_schema'])
reversion.register(Location, follow=['inspection_location', 'offence_location'])
reversion.register(MapLayer, follow=[])
#reversion.register(CallEmail_referrer, follow=[])
reversion.register(CallEmail, follow=['location', 'form_data_records', 'documents', 'comms_logs', 'action_logs', 'legal_case_call_email', 'inspection_call_email', 'offence_call_eamil'])
reversion.register(ComplianceFormDataRecord, follow=[])
reversion.register(CallEmailDocument, follow=[])
reversion.register(CallEmailLogDocument, follow=[])
reversion.register(CallEmailLogEntry, follow=['documents'])
reversion.register(CallEmailUserAction, follow=[])

