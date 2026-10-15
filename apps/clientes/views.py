from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from .models import Cliente


class ClienteListView(LoginRequiredMixin, ListView):
    model = Cliente
    template_name = "clientes/cliente_list.html"
    context_object_name = "clientes"


class ClienteCreateView(LoginRequiredMixin, CreateView):
    model = Cliente
    pass


class ClienteDetailView(LoginRequiredMixin, DetailView):
    model = Cliente
    pass


class ClienteUpdateView(LoginRequiredMixin, UpdateView):
    model = Cliente
    pass
