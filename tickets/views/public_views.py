# encoding: utf-8

from collections import defaultdict
import datetime
from time import mktime

from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponseNotAllowed, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template import RequestContext
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.messages import add_message, INFO, WARNING, ERROR
from django.views.decorators.http import require_POST, require_GET, require_http_methods
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.db.models import Sum

try:
    from reportlab.pdfgen import canvas
except ImportError:
    from warnings import warn
    warn('Failed to import ReportLab. Generating receipts will fail.')

from core.utils import multiform_validate, multiform_save, initialize_form, url

# XXX * imports
from ..models import *
from ..forms import *
from ..helpers import *
from ..utils import *


__all__ = [
    "ALL_PHASES",
    "tickets_address_view",
    "tickets_closed_view",
    "tickets_confirm_view",
    "tickets_thanks_view",
    "tickets_tickets_view",
    "tickets_welcome_view",
]


FIRST_PHASE = "tickets_welcome_view"
LAST_PHASE = "tickets_address_view"


def decorate(view_obj):
    """
    Applying decorators to our makeshift class based views seems a bit tricky.
    Let's do the decorator dance in this helper instead.

    NB. can't use functools.wraps due to Phase not having a __name__.

    Usage:
    realized_phase = ClassBasedView()
    realized_view = decorate(realized_phase)
    """
    @tickets_event_required
    def wrapper(request, event, *args, **kwargs):
        return view_obj(request, event, *args, **kwargs)
    return wrapper


class Phase(object):
    name = "XXX_fill_me_in"
    friendly_name = "XXX Fill Me In"
    methods = ["GET", "POST"]
    template = "tickets_dummy_phase.html"
    prev_phase = None
    next_phase = None
    payment_phase = None
    next_text = "Seuraava &raquo;"
    can_cancel = True
    index = None

    def __call__(self, request, event):
        if request.method not in self.methods:
            return HttpResponseNotAllowed(self.methods)

        order = get_order(request, event)

        if not self.available(request, event):
            if order.is_confirmed:
                return redirect(LAST_PHASE)
            else:
                return redirect(FIRST_PHASE)

        form = self.make_form(request, event)

        if request.method == "POST":
            # Which button was clicked?
            action = request.POST.get("action", "cancel")

            # On "Cancel" there's no need to do form validation, just bail out
            # right away.
            if action == "cancel":
                return self.cancel(request, event)

            if action not in ("next", "prev"):
                # TODO the user is manipulating the POST data
                raise NotImplementedError("evil user")

            # Data validity is checked before even attempting save.
            errors = self.validate(request, event, form)

            if not errors:
                self.save(request, event, form)

                # The "Next" button should only proceed with valid data.
                if action == "next":
                    complete_phase(request, event, self.name)
                    return self.next(request, event)

            # The "Previous" button should work regardless of form validity.
            if action == "prev":
                return self.prev(request, event)

            # "Next" with invalid data falls through.
        elif request.method == "GET":
            if request.session.get('payment_status') == 2:
                del request.session['payment_status']
                if not order.is_confirmed:
                    order.confirm_order()
                    complete_phase(request, event, self.name)
                    return self.next(request, event)
                else:
                    return redirect("tickets_confirm_view")
            else:
                errors = []
        else:
            errors = []

        # POST with invalid data and GET are handled the same.
        return self.get(request, event, form, errors)

    def available(self, request, event):
        order = get_order(request, event)
        return is_phase_completed(request, event, self.prev_phase) and not order.is_confirmed

    def validate(self, request, event, form):
        if not form.is_valid():
            add_message(request, ERROR, 'Tarkista lomakkeen sisältö.')
            return ["syntax"]
        else:
            return []

    def get(self, request, event, form, errors):
        order = get_order(request, event)

        phases = []

        for phase in ALL_PHASES:
            phases.append(dict(
                url=url(phase.name, event.slug),
                friendly_name=phase.friendly_name,
                available=phase.index < self.index and not order.is_confirmed,
                current=phase is self
            ))

        phase = dict(
            url=url(self.name, event.slug),
            next_phase=bool(self.next_phase),
            prev_phase=bool(self.prev_phase),
            can_cancel=self.can_cancel,
            next_text=self.next_text,
            payment_phase=self.payment_phase,
            name=self.name
        )

        vars = dict(self.vars(request, event, form),
            event=event,
            form=form,
            errors=errors,
            order=order,
            phase=phase,
            phases=phases
        )

        return render(request, self.template, vars)

    def make_form(self, request, event):
        return initialize_form(NullForm, request)

    def save(self, request, event, form):
        form.save()

    def next(self, request, event):
        return redirect(self.next_phase, event.slug)

    def prev(self, request, event):
        return redirect(self.prev_phase, event.slug)

    def cancel(self, request, event):
        destroy_order(request, event)
        return HttpResponseRedirect(event.homepage_url)

    def vars(self, request, event, form):
        return {}


class WelcomePhase(Phase):
    name = "tickets_welcome_view"
    friendly_name = "Tervetuloa"
    template = "tickets_welcome_phase.jade"
    prev_phase = None
    next_phase = "tickets_tickets_view"
    permit_new = True

    def save(self, request, event, form):
        order = get_order(request, event)
        order.save()
        set_order(request, event, order)

    def available(self, request, event):
        order = get_order(request, event)
        return not order.is_confirmed


tickets_welcome_phase = WelcomePhase()
tickets_welcome_view = decorate(tickets_welcome_phase)


class TicketsPhase(Phase):
    name = "tickets_tickets_view"
    friendly_name = "Liput"
    template = "tickets_tickets_phase.jade"
    prev_phase = "tickets_welcome_view"
    next_phase = "tickets_address_view"

    def make_form(self, request, event):
        order = get_order(request, event)
        forms = []

        # XXX When the admin changes the available property of products, existing sessions in the Tickets phase will break.
        for product in Product.objects.filter(available=True):
            order_product, created = OrderProduct.objects.get_or_create(order=order, product=product)
            form = initialize_form(OrderProductForm, request, instance=order_product, prefix="o%d" % order_product.pk)
            forms.append(form)

        return forms

    def validate(self, request, event, form):
        errors = multiform_validate(form)

        # If the above step failed, not all forms have cleaned_data.
        if errors:
            return errors

        if sum(i.cleaned_data["count"] for i in form) <= 0:
            add_message(request, INFO, 'Valitse vähintään yksi tuote.')
            errors.append("zero")
            return errors

        if (is_soldout(dict((i.instance.product, i.cleaned_data["count"]) for i in form))):
            add_message(request, ERROR, 'Valitsemasi tuote on valitettavasti juuri myyty loppuun.')
            errors.append("soldout")
            return errors

        return []

    def save(self, request, event, form):
        multiform_save(form)


tickets_tickets_phase = TicketsPhase()
tickets_tickets_view = decorate(tickets_tickets_phase)


class AddressPhase(Phase):
    name = "tickets_address_view"
    friendly_name = "Toimitusosoite"
    template = "tickets_address_phase.jade"
    prev_phase = "tickets_tickets_view"
    next_phase = "tickets_confirm_view"

    def make_form(self, request, event):
        order = get_order(request, event)

        return initialize_form(CustomerForm, request, instance=order.customer)

    def save(self, request, event, form):
        order = get_order(request, event)
        cust = form.save()

        order.customer = cust
        order.save()


tickets_address_phase = AddressPhase()
tickets_address_view = decorate(tickets_address_phase)


class ConfirmPhase(Phase):
    name = "tickets_confirm_view"
    friendly_name = "Vahvistaminen"
    template = "tickets_confirm_phase.jade"
    prev_phase = "tickets_address_view"
    next_phase = "tickets_address_view"
    payment_phase = True
    next_text ="Siirry maksamaan &#10003;"

    def validate(self, request, event, form):
        errors = multiform_validate(form)
        order = get_order(request, event)
        products = OrderProduct.objects.filter(order=order, count__gt=0)
        if (is_soldout(dict((i.product, i.count) for i in products))):
            errors.append("soldout_confirm")
            return errors
        return []

    def vars(self, request, event, form):
        order = get_order(request, event)
        products = OrderProduct.objects.filter(order=order, count__gt=0)

        return dict(products=products)

    def save(self, request, event, form):
        pass

    def next(self, request, event):
        order = get_order(request, event)
        # .confirm_* call .save
        if not order.is_confirmed:
            return HttpResponseRedirect("http://localhost:8000/process/?test=1")
        else:
            payment_phase = None # XXX WTF
            return super(ConfirmPhase, self).next(request)


tickets_confirm_phase = ConfirmPhase()
tickets_confirm_view = decorate(tickets_confirm_phase)


class ThanksPhase(Phase):
    name = "tickets_thanks_view"
    friendly_name = "Kiitos!"
    template = "tickets_thanks_phase.jade"
    prev_phase = None
    next_phase = "tickets_welcome_view"
    next_text = "Uusi tilaus"
    can_cancel = False

    def available(self, request, event):
        order = get_order(request, event)
        return order.is_confirmed

    def vars(self, request, event, form):
        order = get_order(request, event)
        products = OrderProduct.objects.filter(order=order)

        return dict(products=products)

    def save(self, request, event, form):
        pass

    def next(self, request, event):
        # Start a new order
        clear_order(request, event)

        return redirect(self.next_phase)


class ClosedPhase(Phase):
    name = "tickets_welcome_view"
    friendly_name = "Tervetuloa!"
    template = "tickets_closed_phase.html"
    prev_phase = None
    next_phase = None
    can_cancel = True
    index = 0

    def available(self, request, event):
        return True

    def save(self, request, event, form):
        pass

    def next(self, request, event):
        return HttpResponseRedirect(event.homepage_url)


tickets_thanks_phase = ThanksPhase()
tickets_thanks_view = decorate(tickets_thanks_phase)
tickets_closed_phase = ClosedPhase()
tickets_closed_view = decorate(tickets_closed_phase)


ALL_PHASES = [
    tickets_welcome_phase,
    tickets_tickets_phase,
    tickets_address_phase,
    tickets_confirm_phase,
    tickets_thanks_phase,
]

for num, phase in enumerate(ALL_PHASES):
    phase.index = num