from rest_framework import serializers

from dictionary import models


class TermContentSerializer(serializers.ModelSerializer):

    description = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    author = serializers.SerializerMethodField()
    similar = serializers.SerializerMethodField()
    version = serializers.IntegerField(source='version.number')

    class Meta:
        model = models.TermContent
        fields = [
            'id',
            'code',
            'title',
            'language',
            'description',
            'extended_description',
            'author',
            'url',
            'similar',
            'acronym',
            'version',
            'permalink',
        ]

    def get_url(self, obj):
        return obj.get_absolute_url()

    def get_description(self, obj):
        return obj.rendered_description

    def get_author(self, obj):
        if obj.author and (obj.author.first_name or obj.author.last_name):
            return '{} {}'.format(
                obj.author.first_name, obj.author.last_name).strip()

    def get_similar(self, obj):
        return obj.similar.values_list('title', flat=True)


class ConceptSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Concept
        fields = ['id', 'title']


class TermSerializer(serializers.ModelSerializer):

    content = TermContentSerializer(source='latest_content', many=True)
    country = serializers.CharField()
    current_version = serializers.IntegerField(
        source='current_version.number')
    concepts = serializers.SerializerMethodField()

    class Meta:
        model = models.Term
        fields = [
            'id',
            'title',
            'slug',
            'country',
            'current_version',
            'content',
            'concepts',
        ]

    def get_concepts(self, obj):
        return obj.concepts.values_list('title', flat=-True)


class SimpleTermContentSerializer(serializers.ModelSerializer):

    description = serializers.CharField(source='rendered_description')
    version = serializers.IntegerField(source='version.number')
    concepts = serializers.SerializerMethodField()

    class Meta:
        model = models.TermContent
        fields = [
            'id',
            'title',
            'description',
            'extended_description',
            'version',
            'concepts',
        ]

    def get_concepts(self, obj):
        return obj.version.term.concepts.values_list('title', flat=True)


class TermVersionSerializer(serializers.ModelSerializer):

    title = serializers.CharField(source='term.title')
    slug = serializers.CharField(source='term.slug')
    content = TermContentSerializer(many=True)
    version = serializers.IntegerField(source='number')
    country = serializers.CharField(source='term.country')
    concepts = serializers.SerializerMethodField()
    similar = serializers.SerializerMethodField()

    class Meta:
        model = models.TermVersion
        fields = [
            'id',
            'title',
            'slug',
            'version',
            'country',
            'content',
            'concepts',
            'similar',
        ]

    def get_concepts(self, obj):
        return obj.term.concepts.values_list('title', flat=True)

    def get_similar(self, obj):
        return obj.term.similar.values_list('title', flat=True)

