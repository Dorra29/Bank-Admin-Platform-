"""
Reusable Active Directory service layer.

Every view (admin_panel, manager_panel, employee_panel) that needs to talk
to AD should go through LDAPService instead of calling ldap3 directly.
That keeps connection handling, error messages, and AD-specific quirks
(password rules, userAccountControl flags, OU placement) in one place
instead of duplicated across views.
"""
import ssl
from contextlib import contextmanager

from django.conf import settings
from ldap3 import (
    Server, Connection, Tls, ALL, SUBTREE,
    MODIFY_REPLACE, MODIFY_ADD, MODIFY_DELETE,
)
from ldap3.core.exceptions import LDAPException

UAC_ACCOUNTDISABLE = 2
UAC_NORMAL_ACCOUNT = 512
UAC_DONT_EXPIRE_PASSWORD = 65536


class LDAPServiceError(Exception):
    """Raised for any AD/LDAP failure. Message is safe to show in the UI."""
    pass


class LDAPService:
    def __init__(self):
        self.base_dn = settings.LDAP_BASE_DN

    @contextmanager
    def _connection(self):
        try:
            tls = Tls(validate=ssl.CERT_REQUIRED if settings.LDAP_TLS_VALIDATE else ssl.CERT_NONE)
            server = Server(
                settings.LDAP_SERVER_HOST,
                port=settings.LDAP_SERVER_PORT,
                use_ssl=settings.LDAP_USE_SSL,
                tls=tls,
                get_info=ALL,
            )
            conn = Connection(
                server,
                user=settings.LDAP_BIND_DN,
                password=settings.LDAP_BIND_PASSWORD,
                auto_bind=True,
            )
            if settings.LDAP_USE_START_TLS and not settings.LDAP_USE_SSL:
                conn.start_tls()
        except LDAPException as exc:
            raise LDAPServiceError(f"Could not connect to the domain controller: {exc}")

        try:
            yield conn
        finally:
            conn.unbind()

    # ── Create ────────────────────────────────────────────────────────
    def create_user(self, *, first_name, last_name, username, password, role):
        if role not in settings.LDAP_ROLE_OU_MAP:
            raise LDAPServiceError(f"Unknown role '{role}'.")

        ou_dn = settings.LDAP_ROLE_OU_MAP[role]
        group_dn = settings.LDAP_ROLE_GROUP_MAP[role]
        full_name = f"{first_name} {last_name}"
        user_dn = f"CN={full_name},{ou_dn}"

        with self._connection() as conn:
            # 1. Create the object, disabled, no password yet.
            if not conn.add(user_dn, attributes={
                'objectClass': ['top', 'person', 'organizationalPerson', 'user'],
                'cn': full_name,
                'givenName': first_name,
                'sn': last_name,
                'displayName': full_name,
                'sAMAccountName': username,
                'userPrincipalName': f"{username}@{settings.LDAP_DOMAIN}",
                'userAccountControl': UAC_NORMAL_ACCOUNT | UAC_ACCOUNTDISABLE,  # 514
            }):
                raise LDAPServiceError(self._describe(conn, "create the AD object"))

            # 2. Set the password. Requires the encrypted connection.
            if not conn.extend.microsoft.modify_password(user_dn, password):
                conn.delete(user_dn)  # don't leave a broken half-created account behind
                raise LDAPServiceError(self._describe(conn, "set the password"))

            # 3. Enable the account, stop AD forcing a password change at
            #    first logon, and add to the role's security group.
            if not conn.modify(user_dn, {
                'userAccountControl': [(MODIFY_REPLACE, [UAC_NORMAL_ACCOUNT | UAC_DONT_EXPIRE_PASSWORD])],
                'pwdLastSet': [(MODIFY_REPLACE, [-1])],
            }):
                raise LDAPServiceError(self._describe(conn, "enable the account"))

            if not conn.modify(group_dn, {'member': [(MODIFY_ADD, [user_dn])]}):
                raise LDAPServiceError(self._describe(conn, "add the user to their group"))

        return user_dn

    # ── Enable / disable / unlock ───────────────────────────────────────
    def _get_uac(self, conn, user_dn):
        conn.search(user_dn, '(objectClass=user)', attributes=['userAccountControl'])
        if not conn.entries:
            raise LDAPServiceError("User not found.")
        return int(conn.entries[0].userAccountControl.value)

    def disable_user(self, user_dn):
        with self._connection() as conn:
            uac = self._get_uac(conn, user_dn)
            if not conn.modify(user_dn, {'userAccountControl': [(MODIFY_REPLACE, [uac | UAC_ACCOUNTDISABLE])]}):
                raise LDAPServiceError(self._describe(conn, "disable the account"))

    def enable_user(self, user_dn):
        with self._connection() as conn:
            uac = self._get_uac(conn, user_dn)
            if not conn.modify(user_dn, {'userAccountControl': [(MODIFY_REPLACE, [uac & ~UAC_ACCOUNTDISABLE])]}):
                raise LDAPServiceError(self._describe(conn, "enable the account"))

    def unlock_user(self, user_dn):
        with self._connection() as conn:
            if not conn.modify(user_dn, {'lockoutTime': [(MODIFY_REPLACE, [0])]}):
                raise LDAPServiceError(self._describe(conn, "unlock the account"))

    # ── Password / delete / move / groups ───────────────────────────────
    def reset_password(self, user_dn, new_password, force_change_at_logon=False):
        with self._connection() as conn:
            if not conn.extend.microsoft.modify_password(user_dn, new_password):
                raise LDAPServiceError(self._describe(conn, "reset the password"))
            conn.modify(user_dn, {'pwdLastSet': [(MODIFY_REPLACE, [0 if force_change_at_logon else -1])]})

    def delete_user(self, user_dn):
        with self._connection() as conn:
            if not conn.delete(user_dn):
                raise LDAPServiceError(self._describe(conn, "delete the account"))

    def move_user(self, user_dn, new_role):
        if new_role not in settings.LDAP_ROLE_OU_MAP:
            raise LDAPServiceError(f"Unknown role '{new_role}'.")
        rdn = user_dn.split(',', 1)[0]
        new_ou = settings.LDAP_ROLE_OU_MAP[new_role]
        with self._connection() as conn:
            if not conn.modify_dn(user_dn, rdn, new_superior=new_ou):
                raise LDAPServiceError(self._describe(conn, "move the account"))
        return f"{rdn},{new_ou}"

    def add_to_group(self, user_dn, group_dn):
        with self._connection() as conn:
            if not conn.modify(group_dn, {'member': [(MODIFY_ADD, [user_dn])]}):
                raise LDAPServiceError(self._describe(conn, "add the user to the group"))

    def remove_from_group(self, user_dn, group_dn):
        with self._connection() as conn:
            if not conn.modify(group_dn, {'member': [(MODIFY_DELETE, [user_dn])]}):
                raise LDAPServiceError(self._describe(conn, "remove the user from the group"))

    # ── Read ──────────────────────────────────────────────────────────
    def search_users(self, query=''):
        base_filter = '(&(objectClass=user)(objectCategory=person))'
        if query:
            base_filter = (
                f'(&(objectClass=user)(objectCategory=person)'
                f'(|(cn=*{query}*)(sAMAccountName=*{query}*)(mail=*{query}*)))'
            )

        with self._connection() as conn:
            conn.search(
                self.base_dn, base_filter, search_scope=SUBTREE,
                attributes=['cn', 'sAMAccountName', 'mail', 'userAccountControl',
                            'memberOf', 'distinguishedName', 'lockoutTime'],
            )
            results = []
            for e in conn.entries:
                uac = int(e.userAccountControl.value)
                results.append({
                    'dn': str(e.distinguishedName),
                    'name': str(e.cn),
                    'username': str(e.sAMAccountName),
                    'email': str(e.mail) if e.mail else '',
                    'enabled': not (uac & UAC_ACCOUNTDISABLE),
                    'locked': bool(e.lockoutTime and int(e.lockoutTime.value or 0) != 0),
                    'groups': [g.split(',')[0].replace('CN=', '') for g in e.memberOf] if e.memberOf else [],
                })
            return results

    def dashboard_stats(self):
        users = self.search_users()
        return {
            'total': len(users),
            'enabled': sum(1 for u in users if u['enabled']),
            'disabled': sum(1 for u in users if not u['enabled']),
            'locked': sum(1 for u in users if u['locked']),
            'admins': sum(1 for u in users if 'GG_Admins' in u['groups']),
            'managers': sum(1 for u in users if 'GG_Managers' in u['groups']),
            'employees': sum(1 for u in users if 'GG_Employees' in u['groups']),
        }

    @staticmethod
    def _describe(conn, action):
        return f"AD refused to {action}: {conn.result.get('description')} — {conn.result.get('message')}"
