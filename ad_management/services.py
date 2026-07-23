from ldap3 import Server, Connection, ALL
from django.conf import settings


def create_ad_user(
    first_name,
    last_name,
    username,
    password,
    ou
):
    try:

        server = Server(
            settings.LDAP_SERVER,
            port=settings.LDAP_PORT,
            get_info=ALL
        )

        conn = Connection(
            server,
            user=settings.LDAP_BIND_DN,
            password=settings.LDAP_BIND_PASSWORD,
            auto_bind=True
        )

        user_dn = (
            f"CN={first_name} {last_name},"
            f"OU={ou},"
            "DC=bank,DC=local"
        )

        attributes = {
            "givenName": first_name,
            "sn": last_name,
            "displayName": f"{first_name} {last_name}",
            "sAMAccountName": username,
            "userPrincipalName": f"{username}",
            "objectClass": [
                "top",
                "person",
                "organizationalPerson",
                "user"
            ],
        }

        print("ATTRIBUTES BEING SENT:")
        print(attributes)

        success = conn.add(
        dn=user_dn,
        attributes=attributes
        )

        print("==============================")
        print("LDAP ADD RESULT:")
        print(conn.result)
        print("==============================")

        if not success:
            print("USER CREATION FAILED")
            print(conn.result)

        return {
            "success": False,
            "message": conn.result
        }


        print("USER CREATED:")
        print(user_dn)
        # Enable account
        conn.extend.microsoft.modify_password(
            user_dn,
            password
        )

        conn.modify(
            user_dn,
            {
                "userAccountControl": [("MODIFY_REPLACE", [512])]
            }
        )

        return {
            "success": True,
            "message": "User created successfully."
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }