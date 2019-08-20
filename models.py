"""Logsforhumans pretends logs all models changes to human beings."""
# coding: utf-8
import threading

from django.utils.six import python_2_unicode_compatible
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.fields.related import ManyToManyField
from django.db.models.signals import post_delete, m2m_changed
from django.dispatch import receiver
from django.db.models.fields.related_descriptors import ManyToManyDescriptor
from six import text_type as unicode

DEFAULT_DELETE_MESSAGE = u'The {model_name} "{instance_str}" (id={instance_id}) was deleted'
DEFAULT_CREATION_MESSAGE = u'The {model_name} "{instance_str}" was created'
DEFAULT_FIELD_CHANGE_MESSAGE = u'The field {field_verbose_name} was changed from "{old_value}" to "{new_value}"'
DEFAULT_M2M_FIELDS_MESSAGE = u'The {item_model_name} "{item}" was {action} in the field {m2m_table}'
DEFAULT_GENERIC_CHANGE = u'The field {field_verbose_name} was changed'


def get_delete_format_message():
    return getattr(
        settings,
        'LOGSFORHUMANS_DELETE_MESSAGE',
        DEFAULT_DELETE_MESSAGE)


def get_creation_format_message():
    return getattr(
        settings,
        'LOGSFORHUMANS_CREATION_MESSAGE',
        DEFAULT_CREATION_MESSAGE)


def get_field_change_format_message():
    return getattr(
        settings,
        'LOGSFORHUMANS_FIELD_CHANGE_MESSAGE',
        DEFAULT_FIELD_CHANGE_MESSAGE)


def get_m2m_fields_change_format_message():
    return getattr(
        settings,
        'LOGSFORHUMANS_M2M_FIELDS_CHANGE_MESSAGE',
        DEFAULT_M2M_FIELDS_MESSAGE)


def get_generic_change_format_message():
    return getattr(
        settings,
        'LOGSFORHUMANS_GENERIC_CHANGE_MESSAGE',
        DEFAULT_GENERIC_CHANGE)


@python_2_unicode_compatible
class HumanLog(models.Model):
    description = models.TextField(blank=False)

    app_label = models.CharField(max_length=255)
    model_name = models.CharField(max_length=255)
    object_id = models.CharField(max_length=512)

    creation_date = models.DateTimeField(
        auto_now_add=True, verbose_name=u'Created in')
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        editable=False,
        verbose_name=u'Updated by',
        on_delete=models.CASCADE)

    class Meta:
        ordering = ('-creation_date', )

    def __str__(self):
        return self.description


LOGSFORHUMAN_THREAD = threading.local()


def get_models_changelogs(self):
    to_ignore = getattr(self, 'LOGSFORHUMANS_IGNORE_DETAILS', [])
    ignore_changes = getattr(self, 'LOGSFORHUMANS_IGNORE_CHANGES', [])
    model_name = self._meta.verbose_name
    instance_str = unicode(self)
    instance_id = self.pk

    tem_pk = bool(instance_id)
    if not tem_pk:
        return get_creation_format_message().format(**locals())

    old_instance = self.__class__.objects.filter(pk=self.pk).first()
    if not old_instance:
        return u''

    description = u''
    for field in self._meta.get_fields():
        field_name = field.name
        if field_name in ignore_changes:
            continue

        if not isinstance(field, ManyToManyField):
            if not hasattr(self, field_name):
                continue

            new_value = getattr(self, field_name)
            if hasattr(self, 'get_{}_display'.format(field_name)):
                new_value = getattr(
                    self, 'get_{}_display'.format(field_name))()

            old_value = getattr(old_instance, field_name)
            if hasattr(old_instance, 'get_{}_display'.format(field_name)):
                old_value = getattr(
                    old_instance, 'get_{}_display'.format(field_name))()

            if new_value != old_value:
                field_verbose_name = field.verbose_name
                if field_name in to_ignore:
                    description += get_generic_change_format_message().format(
                        **locals()) + '\n'
                else:
                    description += get_field_change_format_message().format(
                        **locals()) + '\n'
    return description


def can_have_changelog(self):
    if not hasattr(self, 'skip_changelog') or not self.skip_changelog:
        return True
    return False


def get_logs(self):
    return HumanLog.objects.filter(
        model_name=self._meta.model_name,
        app_label=self._meta.app_label,
        object_id=self.pk)


def add_log(self, log):
    user = self.get_current_user()
    if isinstance(user, get_user_model()):
        human_log = HumanLog.objects.create(
            description=log,
            app_label=self._meta.app_label,
            model_name=self._meta.model_name,
            object_id=self.pk,
            updated_by=user
        )
    else:
        human_log = HumanLog.objects.create(
            description=log,
            app_label=self._meta.app_label,
            model_name=self._meta.model_name,
            object_id=self.pk)
    if hasattr(self, 'logsforhumans_onchange'):
        self.logsforhumans_onchange(human_log)


def add_delete_log(self, kwargs):
    if not self.can_have_changelog():
        return

    model_name = self._meta.verbose_name
    instance_str = unicode(self)
    instance_id = self.pk

    message = get_delete_format_message().format(**locals())
    self.add_log(message)


def get_save_method(original_save):
    def save(self, *args, **kwargs):
        description = None
        if self.can_have_changelog():
            description = self.get_models_changelogs()
        original_save(self, *args, **kwargs)
        if description:
            self.add_log(description)

    return save


@classmethod
def get_current_user(cls):
    """Return the current user configured in middleware."""
    if hasattr(LOGSFORHUMAN_THREAD, 'request'):
        return getattr(LOGSFORHUMAN_THREAD.request, 'user', None)


@staticmethod
def generate_m2m_change_logs(**kwargs):
    if not hasattr(kwargs['instance'], 'add_log'):
        return

    create_logs = False
    action = u''
    if kwargs.get('action') == 'post_remove':
        create_logs = True
        # fixme: create a variable for that
        action = 'removido'
    elif kwargs.get('action') == 'post_add':
        create_logs = True
        # fixme: create a variable for that
        action = 'adicionado'
    if not create_logs:
        return
    log = u''
    for pk in kwargs.get('pk_set', list()):
        item = kwargs.get('model').objects.filter(pk=pk).first()
        item_model_name = kwargs.get('model')._meta.verbose_name
        m2m_table = kwargs.get('sender')._meta.db_table

        log += get_m2m_fields_change_format_message().format(**locals())
        log += '\n'
    if log:
        kwargs['instance'].add_log(log)


def generate_humanlogs(class_obj):
    class_obj.can_have_changelog = can_have_changelog
    class_obj.get_logs = get_logs
    class_obj.get_models_changelogs = get_models_changelogs
    class_obj.add_log = add_log
    class_obj.add_delete_log = add_delete_log
    class_obj.save = get_save_method(class_obj.save)
    class_obj.get_current_user = get_current_user
    class_obj.generate_m2m_change_logs = generate_m2m_change_logs

    @receiver(post_delete, sender=class_obj, weak=False)
    def class_instance_post_delete(**kwargs):
        instance = kwargs['instance']
        instance.add_delete_log(kwargs)
    class_obj.class_instance_post_delete = class_instance_post_delete

    for field in dir(class_obj):
        if isinstance(getattr(class_obj, field), ManyToManyDescriptor):
            through = getattr(class_obj, field).through

            @receiver(m2m_changed, sender=through, weak=False)
            def class_instance_m2m_changed(**kwargs):
                class_obj.generate_m2m_change_logs(**kwargs)

    return class_obj
