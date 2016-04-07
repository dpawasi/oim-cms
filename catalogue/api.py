from rest_framework import serializers, viewsets, status, generics
from models import Record, Style
from rest_framework.response import Response
import base64
from django.core.files.base import ContentFile
import md5
import base64
from django.views.decorators.csrf import csrf_exempt
import os
from django.conf import settings

#Ows Resource Serializer
class OwsResourceSerializer(serializers.Serializer):
    wfs = serializers.BooleanField(write_only=True, default=False)
    wfs_endpoint = serializers.CharField(write_only=True,allow_null=True)
    wfs_version = serializers.CharField(write_only=True,allow_null=True)
    wms = serializers.BooleanField(write_only=True,default=False)
    wms_endpoint = serializers.CharField(write_only=True,allow_null=True)
    wms_version = serializers.CharField(write_only=True,allow_null=True)
    gwc = serializers.BooleanField(write_only=True,default=False)
    gwc_endpoint = serializers.CharField(write_only=True,allow_null=True)

    def validate(self,data):
        if data['wfs_endpoint'] or data['wms_endpoint'] or data['gwc_endpoint']:
            return data
        else:
            raise serializers.ValidationError("An endpoint must be provided for one of the services.")

    def save(self,record=None):
        if record:
            links = ''
            if self.validated_data['wfs'] and self.validated_data['wfs_endpoint']:
                links += Record.generate_ows_link('WFS',self.validated_data['wfs_version'],record)
                record.service_type = 'WFS'
                record.service_type_version = self.validated_data['wfs_version']
            if self.validated_data['gwc'] and self.validated_data['gwc_endpoint']:
                links +=  Record.generate_ows_link('WMS','',record)
                record.service_type = 'WMS'
            if self.validated_data['wms'] and self.validated_data['wms_endpoint']:
                links +=  Record.generate_ows_link('WMS',self.validated_data['wms_version'],record)
                record.service_type = 'WMS'
                record.service_type_version = self.validated_data['wms_version']
            record.links = links
            record.save()

# Style Serializer
class StyleSerializer(serializers.ModelSerializer):
    content = serializers.CharField(write_only=True,allow_null=True)
    name = serializers.CharField(default=Style.BUILTIN)
    
    def get_raw_content(self, obj):
        if obj.content:
            return obj.content.read().encode('base64')
        else:
            return None
    
    def __init__(self, *args, **kwargs):
        super(StyleSerializer, self).__init__(*args, **kwargs)
        if kwargs.get('context'):
            request = kwargs['context']['request']
            borg = request.GET.get('borg',False)
            if borg:
                self.fields['raw_content'] = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Style
        fields = (
            'name',
            'format',
            'default',
            'content',
        )

# Record Serializer
class RecordSerializer(serializers.ModelSerializer):
    ows_resource = OwsResourceSerializer(write_only=True, required=False)
    workspace =  serializers.CharField(max_length=255, write_only=True)
    name = serializers.CharField(max_length=255, write_only=True)
    identifier = serializers.CharField(max_length=255, read_only=True)
    url = serializers.SerializerMethodField(read_only=True)
    
    def __init__(self, *args, **kwargs):
        super(RecordSerializer, self).__init__(*args, **kwargs)
        if kwargs.get('context'):
            request = kwargs['context']['request']
            format_date = request.GET.get('format_date',False)
            self.fields['styles'] = StyleSerializer(many=True,required=False, context={'request':request})
            if format_date:
                self.fields['publication_date'] = serializers.DateTimeField(format='%A, %d %B %Y %H:%M %p')
                self.fields['modified'] = serializers.DateTimeField(format='%A, %d %B %Y %H:%M %p')
        else:
            self.fields['styles'] = StyleSerializer(many=True,required=False)

    def get_url(self,obj):
        return '{0}/catalogue/api/records/{1}.json'.format(settings.BASE_URL,obj.identifier)

    class Meta:
        model = Record
        fields = (
            'ows_resource',
            'url',
            'identifier',
            'title',
            'insert_date',
            'any_text',
            'modified',
            'abstract',
            'keywords',
            'bounding_box',
            'crs',
            'publication_date',
            'service_type',
            'service_type_version',
            'links',
            'styles',
            'workspace',
            'name',
            'auto_update',
        )

class RecordViewSet(viewsets.ModelViewSet):
    queryset = Record.objects.all()
    serializer_class = RecordSerializer
    authentication_classes =[]
    lookup_field = "identifier"
    
    def createStyle(self,content):
        uploaded_style = ContentFile(content)
        return uploaded_style
    
    def calculate_checksum(self, content):
        checksum = md5.new()
        checksum.update(content)
        return base64.b64encode(checksum.digest())
        
    def perform_destroy(self, instance):
        instance.active = False
        instance.save()

    def create(self,request):
        styles_data = None
        ows_data = None
        auto_update = True
        http_status = status.HTTP_200_OK
        if "styles" in request.data:
            styles_data = request.data.pop("styles")
        if "ows_resource" in request.data:
            ows_data = request.data.pop("ows_resource")
        #parse and valid record data
        serializer = RecordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        #parse and valid styles data
        style_serializers = [StyleSerializer(data=style) for style in styles_data] if styles_data else []
        if style_serializers:
            for style_serializer in style_serializers:
                style_serializer.is_valid(raise_exception=True)
        #parse and vlaidate ows data
        ows_serializer = OwsResourceSerializer(data=ows_data)
        ows_serializer.is_valid(raise_exception=True)
        #save record data.
        identifier = "{}:{}".format(serializer.validated_data['workspace'],serializer.validated_data['name'])
        try:
            serializer.instance = Record.objects.get(identifier=identifier)
            serializer.instance.active = True
            auto_update = serializer.instance.auto_update
            if not serializer.instance.auto_update:
                #auto update disabled
                for key in ["title","abstract","auto_update","modified","insert_date"]:
                    if key in serializer.validated_data: serializer.validated_data.pop(key)

        except Record.DoesNotExist:
            serializer.validated_data['identifier']=identifier
            http_status = status.HTTP_201_CREATED

        #remove fake fields
        workspace = serializer.validated_data.pop("workspace")
        name = serializer.validated_data.pop("name")
        record = serializer.save()
        #
        #ows_serializer.save(record)

        if auto_update:
            #auto update is enabled update styles
            #set the missing data and transform the content
            for style_serializer in style_serializers:
                uploaded_style = style_serializer.validated_data
                uploaded_style["record"] = record
                uploaded_style["content"] = self.createStyle(uploaded_style["content"].decode("base64"))

            #set default style
            origin_default_style = {"sld":record.sld.name if record.sld else None,"qml":record.qml.name if record.qml else None, "lyr":record.lyr.name if record.lyr else None }
            default_style = { }
            for style_serializer in style_serializers:
                uploaded_style = style_serializer.validated_data
                if uploaded_style.get("default",False):
                    #user set this style as default style, use the user's setting
                    default_style[uploaded_style["format"]] = uploaded_style
                elif origin_default_style.get(uploaded_style["format"].lower(),None) == uploaded_style["name"]:
                    #the current style is configured default style.
                    default_style[uploaded_style["format"]] = uploaded_style
                elif not origin_default_style.get(uploaded_style["format"].lower(),None) and  uploaded_style["format"] not in default_style:
                    #no default style has been set, set the current style as the default style
                    default_style[uploaded_style["format"]] = uploaded_style
                #clear the default flag
                uploaded_style["default"] = False

            #set the default style
            for uploaded_style in default_style.itervalues():
                uploaded_style["default"] = True

            #save  style
            for style_serializer in style_serializers:
                if http_status != status.HTTP_201_CREATED:
                    #record is already exist,should check whether style exist or not.
                    try:
                        style_serializer.instance = Style.objects.get(record=record,name=style_serializer.validated_data["name"],format=style_serializer.validated_data["format"])
                        setattr(style_serializer.instance,"access_channel","restapi")
                    except Style.DoesNotExist:
                        pass
                style_serializer.save()

        record.styles = list(Style.objects.filter(record=record))
        serializer = RecordSerializer(record)
        return Response(serializer.data,status=http_status)
