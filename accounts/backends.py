from ldap3 import Server, Connection, ALL
from django.conf import settings
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User


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

            print("RESULT COUNT:", len(admin_conn.entries))

            for user in admin_conn.entries:
                print(user)


            if len(admin_conn.entries) == 0:
                print("USER NOT FOUND")
                return None


            entry = admin_conn.entries[0]


            user_dn = entry.entry_dn


            print("USER FOUND:")
            print(user_dn)



            # Extract AD groups

            groups = []


            if hasattr(entry, "memberOf"):

                for group in entry.memberOf:
                    groups.append(str(group))


            print("AD GROUPS:")

            for g in groups:
                print(g)



            # Verify user password

            user_conn = Connection(
                server,
                user=user_dn,
                password=password,
                auto_bind=True
            )


            if not user_conn.bound:
                print("PASSWORD INVALID")
                return None



            # Create or update Django user

            django_user, created = User.objects.get_or_create(
                username=username
            )


            django_user.first_name = (
                str(entry.givenName.value)
                if entry.givenName
                else ""
            )


            django_user.last_name = (
                str(entry.sn.value)
                if entry.sn
                else ""
            )


            django_user.email = (
                str(entry.mail.value)
                if entry.mail
                else ""
            )



            # Reset permissions first

            django_user.is_staff = False
            django_user.is_superuser = False



            # Map AD groups to Django roles

            for group in groups:


                if "GG_Admins" in group:
                    django_user.is_staff = True
                    django_user.is_superuser = True


                elif "GG_Managers" in group:
                    django_user.is_staff = True


                elif "GG_Employees" in group:
                    django_user.is_staff = False
                    django_user.is_superuser = False
            
            # Save AD groups on the user object
            django_user.ad_groups = groups

            django_user.save()


            return django_user
        



        except Exception as e:

            print("LDAP ERROR:", e)
            return None



    def get_user(self, user_id):

        try:

            return User.objects.get(pk=user_id)

        except User.DoesNotExist:

            return None
        
   