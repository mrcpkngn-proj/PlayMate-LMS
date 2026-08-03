from django.apps import AppConfig


class ClassroomConfig(AppConfig):
    name = 'apps.classroom'

    def ready(self):

        import apps.classroom.signals
