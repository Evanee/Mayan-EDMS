from __future__ import absolute_import

from django.db import models
from django.utils.translation import ugettext_lazy as _

from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

from documents.models import Document, DocumentType

from .managers import IndexManager
from .settings import AVAILABLE_INDEXING_FUNCTIONS

available_indexing_functions_string = (_(u'Available functions: %s') % u','.join([u'%s()' % name for name, function in AVAILABLE_INDEXING_FUNCTIONS.items()])) if AVAILABLE_INDEXING_FUNCTIONS else u''


class Index(models.Model):
    name = models.CharField(unique=True, max_length=64, verbose_name=_(u'Name'), help_text=_(u'Internal name used to reference this index.'))
    title = models.CharField(unique=True, max_length=128, verbose_name=_(u'Title'), help_text=_(u'The name that will be visible to users.'))
    enabled = models.BooleanField(default=True, verbose_name=_(u'Enabled'), help_text=_(u'Causes this index to be visible and updated when document data changes.'))
    document_types = models.ManyToManyField(DocumentType, verbose_name=_(u'Document types'))

    objects = IndexManager()

    @property
    def template_root(self):
        return self.indextemplatenode_set.get(parent=None)

    @property
    def instance_root(self):
        return self.template_root.node_instance

    def __unicode__(self):
        return self.title

    @models.permalink
    def get_absolute_url(self):
        return ('index_instance_node_view', [self.instance_root.pk])

    def get_index_document_types(self):
        return self.document_types.all()

    def get_document_types_not_in_index(self):
        return DocumentType.objects.exclude(pk__in=self.get_index_document_types())

    def save(self, *args, **kwargs):
        super(Index, self).save(*args, **kwargs)
        index_template_node_root, created = IndexTemplateNode.objects.get_or_create(parent=None, index=self)

    def get_document_types_names(self):
        return u', '.join([unicode(document_type) for document_type in self.document_types.all()] or [u'All'])

    def natural_key(self):
        return (self.name,)

    def get_instance_node_count(self):
        try:
            return self.instance_root.get_descendant_count()
        except IndexInstanceNode.DoesNotExist:
            return 0

    class Meta:
        verbose_name = _(u'Index')
        verbose_name_plural = _(u'Indexes')


class IndexTemplateNode(MPTTModel):
    parent = TreeForeignKey('self', null=True, blank=True, related_name='index_template_node')
    index = models.ForeignKey(Index, verbose_name=_(u'Index'))
    expression = models.CharField(max_length=128, verbose_name=_(u'Indexing expression'), help_text=_(u'Enter a python string expression to be evaluated.'))
    # % available_indexing_functions_string)
    enabled = models.BooleanField(default=True, verbose_name=_(u'Enabled'), help_text=_(u'Causes this node to be visible and updated when document data changes.'))
    link_documents = models.BooleanField(default=False, verbose_name=_(u'Link documents'), help_text=_(u'Check this option to have this node act as a container for documents and not as a parent for further nodes.'))

    def __unicode__(self):
        return self.expression

    @property
    def node_instance(self):
        return self.indexinstancenode_set.get()

    class Meta:
        verbose_name = _(u'Index template node')
        verbose_name_plural = _(u'Indexes template nodes')


class IndexInstanceNode(MPTTModel):
    parent = TreeForeignKey('self', null=True, blank=True, related_name='index_instance_node')
    index_template_node = models.ForeignKey(IndexTemplateNode, verbose_name=_(u'Index template node'))
    value = models.CharField(max_length=128, blank=True, verbose_name=_(u'Value'))
    documents = models.ManyToManyField(Document, verbose_name=_(u'Documents'))

    def __unicode__(self):
        return self.value

    @models.permalink
    def get_absolute_url(self):
        return ('index_instance_node_view', [self.pk])

    class Meta:
        verbose_name = _(u'Index instance node')
        verbose_name_plural = _(u'Indexes instance nodes')


class DocumentRenameCount(models.Model):
    index_instance_node = models.ForeignKey(IndexInstanceNode, verbose_name=_(u'Index instance'))
    document = models.ForeignKey(Document, verbose_name=_(u'Document'))
    suffix = models.PositiveIntegerField(blank=True, verbose_name=(u'Suffix'))

    def __unicode__(self):
        return u'%s - %s - %s' % (self.index_instance_node, self.document, self.suffix or u'0')

    class Meta:
        verbose_name = _(u'Document rename count')
        verbose_name_plural = _(u'Documents rename count')
