from django.core.management.base import BaseCommand, CommandError
from entries.models import Entry
import os
class Command(BaseCommand):
    help = 'Loads data from an mbox file and generates a json file for the chart.'

    def add_arguments(self, parser):
        parser.add_argument('from_email_address',  type=str)
        parser.add_argument('data_file',  type=str)

    def handle(self, *args, **options):
      Entry.build_all_from_mbox_file(
          options['data_file'],
          options['from_email_address'],
      )


      file_path = os.path.join(os.getcwd(), 'entries', 'static', 'moods.json')
      Entry.write_series_to_file(file_path)
