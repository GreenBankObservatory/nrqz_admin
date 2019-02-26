from django.apps import AppConfig

from watson import search as watson


class CasesConfig(AppConfig):
    name = "cases"

    def ready(self):
        watson.register(self.get_model("Case"), exclude="data_type")
        watson.register(self.get_model("Facility"), exclude="data_type")
        watson.register(self.get_model("Person"), exclude="data_type")
