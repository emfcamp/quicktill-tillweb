from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# XXX be careful to refer to this explicitly, otherwise you might get
# the quicktill.models.Session object instead!
class Session(models.Model):
    """When we're open
    """
    opening_time = models.DateTimeField(help_text="Time we open")
    closing_time = models.DateTimeField(help_text="Time we close")
    weight = models.FloatField(help_text="Expected busyness of session")
    comment = models.CharField(
        max_length=100, blank=True,
        help_text="Displayed on web interface; not private!")

    class Meta:
        ordering = ('opening_time',)
        constraints = (
            models.CheckConstraint(
                check=models.Q(closing_time__gt=models.F('opening_time')),
                name="ends_after_start"),
        )

    def __str__(self):
        return f"{self.opening_time:} – {self.closing_time}"

    @property
    def length(self):
        return self.closing_time - self.opening_time

    def clean(self):
        if self.opening_time >= self.closing_time:
            raise ValidationError(_("Session must end after it starts."))
