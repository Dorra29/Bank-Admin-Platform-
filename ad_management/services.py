import ssl
from ldap3 import Server, Connection, ALL, Tls, MODIFY_REPLACE
from django.conf import settings


def get_connection():
    """Single LDAPS connection used for every write operation.
    Plain LDAP:389 is fine for reads, but AD refuses unicodePwd changes
    over an unencrypted channel — so we standardize on SSL here."""
    tls_config = Tls(validate=ssl.CERT_NONE)  # lab self-signed cert
    server = Server(
        settings.LDAP_SERVER,
        port=settings.LDAP_SSL_PORT,
        use_ssl=True,
        tls=tls_config,
        get_info=ALL,
    )
    return Connection(
        server,
        user=settings.LDAP_BIND_DN,
        password=settings.LDAP_BIND_PASSWORD,
        auto_bind=True,
    )


def find_user_dn(conn, username):
    conn.search(
        search_base=settings.LDAP_USER_SEARCH_BASE,
        search_filter=f"(sAMAccountName={username})",
        attributes=["distinguishedName"],
    )
    if not conn.entries:
        return None
    return conn.entries[0].entry_dn


def _is_account_disabled(entry):
    if "userAccountControl" not in entry or not entry.userAccountControl.raw_values:
        return False
    try:
        return int(entry.userAccountControl.raw_values[0]) & 2 == 2
    except (ValueError, TypeError):
        return False


def _is_account_locked(entry):
    if "lockoutTime" not in entry or not entry.lockoutTime.raw_values:
        return False
    try:
        return int(entry.lockoutTime.raw_values[0]) != 0
    except (ValueError, TypeError):
        return False


def create_ad_user(first_name, last_name, username, password, ou):
    try:
        conn = get_connection()

        user_dn = f"CN={first_name} {last_name},OU={ou},{settings.LDAP_BASE_DN}"

        attributes = {
            "givenName": first_name,
            "sn": last_name,
            "displayName": f"{first_name} {last_name}",
            "sAMAccountName": username,
            "userPrincipalName": f"{username}@bank.local",
            "objectClass": ["top", "person", "organizationalPerson", "user"],
        }

        if not conn.add(dn=user_dn, attributes=attributes):
            return {"success": False, "message": conn.result}

        if not conn.extend.microsoft.modify_password(user_dn, password):
            if conn.result.get("description") == "unwillingToPerform":
                return {
                    "success": False,
                    "message": "Password rejected by AD — it likely doesn't meet the domain's "
                                "complexity policy (min 7 chars, 3 of: upper/lower/digit/symbol).",
                }
            return {"success": False, "message": conn.result}

        # 512 = NORMAL_ACCOUNT, enabled
        if not conn.modify(user_dn, {"userAccountControl": [(MODIFY_REPLACE, [512])]}):
            return {"success": False, "message": conn.result}

        return {"success": True, "message": "User created and enabled successfully."}

    except Exception as e:
        return {"success": False, "message": str(e)}


def enable_ad_user(username):
    try:
        conn = get_connection()
        user_dn = find_user_dn(conn, username)
        if not user_dn:
            return {"success": False, "message": "User not found."}

        if not conn.modify(user_dn, {"userAccountControl": [(MODIFY_REPLACE, [512])]}):
            return {"success": False, "message": conn.result}
        return {"success": True, "message": f"{username} enabled."}
    except Exception as e:
        return {"success": False, "message": str(e)}


def disable_ad_user(username):
    try:
        conn = get_connection()
        user_dn = find_user_dn(conn, username)
        if not user_dn:
            return {"success": False, "message": "User not found."}

        # 514 = NORMAL_ACCOUNT + ACCOUNTDISABLE
        if not conn.modify(user_dn, {"userAccountControl": [(MODIFY_REPLACE, [514])]}):
            return {"success": False, "message": conn.result}
        return {"success": True, "message": f"{username} disabled."}
    except Exception as e:
        return {"success": False, "message": str(e)}


def reset_ad_password(username, new_password):
    try:
        conn = get_connection()
        user_dn = find_user_dn(conn, username)
        if not user_dn:
            return {"success": False, "message": "User not found."}

        # No old_password → administrative reset (requires the bind
        # account to have Reset Password permission, which Administrator has).
        if not conn.extend.microsoft.modify_password(user_dn, new_password):
            if conn.result.get("description") == "unwillingToPerform":
                return {
                    "success": False,
                    "message": "Password rejected by AD — it likely doesn't meet the domain's "
                                "complexity policy (min 7 chars, 3 of: upper/lower/digit/symbol).",
                }
            return {"success": False, "message": conn.result}
        return {"success": True, "message": f"Password reset for {username}."}
    except Exception as e:
        return {"success": False, "message": str(e)}


def unlock_ad_user(username):
    try:
        conn = get_connection()
        user_dn = find_user_dn(conn, username)
        if not user_dn:
            return {"success": False, "message": "User not found."}

        # lockoutTime = 0 clears the lockout
        if not conn.modify(user_dn, {"lockoutTime": [(MODIFY_REPLACE, [0])]}):
            return {"success": False, "message": conn.result}
        return {"success": True, "message": f"{username} unlocked."}
    except Exception as e:
        return {"success": False, "message": str(e)}


def get_admin_dashboard_stats():
    try:
        conn = get_connection()

        stats = {
            "admins": {"total": 0, "enabled": 0, "disabled": 0, "locked": 0},
            "managers": {"total": 0, "enabled": 0, "disabled": 0, "locked": 0},
            "employees": {"total": 0, "enabled": 0, "disabled": 0, "locked": 0},
        }

        # OU=Admins — every account here is an admin
        conn.search(
            search_base=f"OU=Admins,{settings.LDAP_BASE_DN}",
            search_filter="(&(objectClass=user)(objectCategory=person))",
            attributes=["userAccountControl", "lockoutTime"],
        )
        for entry in conn.entries:
            stats["admins"]["total"] += 1
            stats["admins"]["disabled" if _is_account_disabled(entry) else "enabled"] += 1
            if _is_account_locked(entry):
                stats["admins"]["locked"] += 1

        # OU=Employees — holds both GG_Employees and GG_Managers members
        conn.search(
            search_base=f"OU=Employees,{settings.LDAP_BASE_DN}",
            search_filter="(&(objectClass=user)(objectCategory=person))",
            attributes=["userAccountControl", "lockoutTime", "memberOf"],
        )
        for entry in conn.entries:
            member_of = entry.memberOf.values if "memberOf" in entry else []
            bucket = "managers" if any("GG_Managers" in g for g in member_of) else "employees"

            stats[bucket]["total"] += 1
            stats[bucket]["disabled" if _is_account_disabled(entry) else "enabled"] += 1
            if _is_account_locked(entry):
                stats[bucket]["locked"] += 1

        stats["total_users"] = sum(s["total"] for s in [stats["admins"], stats["managers"], stats["employees"]])
        stats["total_disabled"] = sum(s["disabled"] for s in [stats["admins"], stats["managers"], stats["employees"]])
        stats["total_locked"] = sum(s["locked"] for s in [stats["admins"], stats["managers"], stats["employees"]])

        return stats
    except Exception as e:
        return {"error": str(e)}


def get_employee_list():
    """Read-only list of AD accounts under OU=Employees (both managers and employees)."""
    try:
        conn = get_connection()
        conn.search(
            search_base=f"OU=Employees,{settings.LDAP_BASE_DN}",
            search_filter="(&(objectClass=user)(objectCategory=person))",
            attributes=["sAMAccountName", "givenName", "sn", "mail",
                        "userAccountControl", "lockoutTime", "memberOf"],
        )

        results = []
        for entry in conn.entries:
            member_of = entry.memberOf.values if "memberOf" in entry else []
            role = "Manager" if any("GG_Managers" in g for g in member_of) else "Employee"

            results.append({
                "username": str(entry.sAMAccountName) if "sAMAccountName" in entry else "",
                "first_name": str(entry.givenName) if "givenName" in entry else "",
                "last_name": str(entry.sn) if "sn" in entry else "",
                "email": str(entry.mail) if "mail" in entry else "",
                "role": role,
                "enabled": not _is_account_disabled(entry),
                "locked": _is_account_locked(entry),
            })

        results.sort(key=lambda r: (r["role"], r["username"]))
        return results

    except Exception:
        return []


def get_ad_user_profile(username):
    """Read-only profile lookup used by the employee's own dashboard."""
    try:
        conn = get_connection()
        conn.search(
            search_base=settings.LDAP_BASE_DN,
            search_filter=f"(sAMAccountName={username})",
            attributes=["sAMAccountName", "givenName", "sn", "mail", "memberOf",
                        "userAccountControl", "lockoutTime"],
        )
        if not conn.entries:
            return None

        entry = conn.entries[0]
        groups = entry.memberOf.values if "memberOf" in entry else []

        return {
            "username": str(entry.sAMAccountName) if "sAMAccountName" in entry else username,
            "first_name": str(entry.givenName) if "givenName" in entry else "",
            "last_name": str(entry.sn) if "sn" in entry else "",
            "email": str(entry.mail) if "mail" in entry else "",
            "groups": [g.split(",")[0].replace("CN=", "") for g in groups],
            "enabled": not _is_account_disabled(entry),
            "locked": _is_account_locked(entry),
        }
    except Exception as e:
        return {"error": str(e)}
