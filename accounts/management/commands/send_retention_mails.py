# from django.core.management.base import BaseCommand
# from accounts.ml_utils import check_and_send_retention_emails

# class Command(BaseCommand):
#     help = '7 days inactive users sending retention emails'

#     def handle(self, *args, **kwargs):
#         self.stdout.write("Checking for inactive users...")
#         check_and_send_retention_emails() # तपाईँले ml_utils.py मा बनाएको फङ्सन
#         self.stdout.write(self.style.SUCCESS("Retention emails sent successfully!"))