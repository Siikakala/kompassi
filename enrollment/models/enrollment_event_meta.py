# encoding: utf-8



from django.db import models
from django.utils.translation import ugettext_lazy as _

from core.models import EventMetaBase
from core.utils import alias_property, is_within_period


class EnrollmentEventMeta(EventMetaBase):
    """
    An event has an instance of this class to indicate use of the enrollment module.
    """
    form_class_path = models.CharField(
        max_length=63,
        help_text=_("Reference to form class. Example: events.yukicon2016.forms:EnrollmentForm"),
    );

    enrollment_opens = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Enrollment opens"),
    )
    public_from = alias_property('enrollment_opens')

    enrollment_closes = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Enrollment closes"),
    )
    public_until = alias_property('enrollment_closes')

    override_enrollment_form_message = models.TextField(
        blank=True,
        default='',
        verbose_name=_('Enrollment form message'),
        help_text=_(
            'Use this field to override the message that is shown in top of the enrollment form. '
            'If this field is not filled in, a default message is shown.'
        )
    )

    @property
    def form_class(self):
        if not getattr(self, '_form_class', None):
            from core.utils import get_code
            self._form_class = get_code(self.form_class_path)

        return self._form_class

    @property
    def is_enrollment_open(self):
        return is_within_period(self.enrollment_opens, self.enrollment_closes)

    @property
    def enrollment_form_message(self):
        if self.override_enrollment_form_message:
            return self.override_enrollment_form_message
        else:
            return _(
                'Using this form you can enroll in the event. Please note that filling in the form '
                'does not guarantee automatic admittance into the event. You will be contacted by '
                'the event organizer and notified of the decision whether to accept your enrollment '
                'or not.'
            )
