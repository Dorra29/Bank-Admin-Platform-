import logging

from ldap3 import Server, Connection, ALL
from django.conf import settings
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


class ActiveDirectoryBackend(BaseBackend):

    def authenticate(self, request, username=None, password=None):

        if not username or not password:
            return None

        try:
            # Connect to AD using service account
            server = Server(
                settings.LDAP_SERVER,
                port=settings.LDAP_PORT,
                get_info=ALL
            )

            admin_conn = Connection(
                server,
                user=settings.LDAP_BIND_DN,
                password=settings.LDAP_BIND_PASSWORD,
                auto_bind=True
            )

            # Search the user in AD
            admin_conn.search(
                search_base=settings.LDAP_USER_SEARCH_BASE,
                search_filter=f"(sAMAccountName={username})",
                attributes=[
                    "distinguishedName",
                    "sAMAccountName",
                    "givenName",
                    "sn",
                    "mail",
                    "memberOf"
                ]
            )

            logger.debug("LDAP search returned %d entries", len(admin_conn.entries))

            if len(admin_conn.entries) == 0:
                logger.info("LDAP authentication failed: user '%s' not found", username)
                return None

            entry = admin_conn.entries[0]
            user_dn = entry.entry_dn
            logger.debug("Resolved user DN for '%s': %s", username, user_dn)

            # Extract AD groups
            groups = []
            if hasattr(entry, "memberOf"):
                for group in entry.memberOf:
                    groups.append(str(group))

            logger.debug("AD groups for '%s': %s", username, groups)

            # Verify user password
            user_conn = Connection(
                server,
                user=user_dn,
                password=password,
                auto_bind=True
            )

            if not user_conn.bound:
                logger.info("LDAP authentication failed: invalid password for '%s'", username)
                return None

            # Create or update Django user
            django_user, created = User.objects.get_or_create(username=username)

            django_user.first_name = str(entry.givenName.value) if entry.givenName else ""
            django_user.last_name = str(entry.sn.value) if entry.sn else ""
            django_user.email = str(entry.mail.value) if entry.mail else ""

            # Reset permissions first
            django_user.is_staff = False
            django_user.is_superuser = False

            # Map AD groups to Django roles
            for group in groups:
                if "GG_Admins" in group:
                    django_user.is_staff = True
                    django_user.is_superuser = True
                elif "GG_SupportAdmins" in group:
                    django_user.is_staff = True
                elif "GG_Managers" in group:
                    django_user.is_staff = True
                elif "GG_Employees" in group:
                    django_user.is_staff = False
                    django_user.is_superuser = False

            # Save AD groups on the user object
            django_user.ad_groups = groups
            django_user.save()

            logger.info("LDAP authentication succeeded for '%s' (created=%s)", username, created)
            return django_user

        except Exception:
            logger.exception("LDAP authentication error for user '%s'", username)
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
