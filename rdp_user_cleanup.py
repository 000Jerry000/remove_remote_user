import subprocess
import time
import logging
import ctypes
from datetime import datetime

# ============================================================
# CONFIGURATION
# ============================================================

CHECK_INTERVAL = 1 * 60  # 1 minutes

# Accounts that are ALLOWED to remain in Remote Desktop Users.
# Add your legitimate Windows username(s) here.
ALLOWED_USERS = {
    "Administrator",
    "AKIRA",
    # "YourWindowsUsername",
}

LOG_FILE = "rdp_guard.log"

# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


# ============================================================
# ADMIN CHECK
# ============================================================

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


# ============================================================
# GET REMOTE DESKTOP USERS
# ============================================================

def get_rdp_users():
    """
    Get members of the local 'Remote Desktop Users' group.
    """

    try:
        result = subprocess.run(
            [
                "net",
                "localgroup",
                "Remote Desktop Users"
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )

        if result.returncode != 0:
            logging.error(
                "Failed to query Remote Desktop Users: %s",
                result.stderr.strip()
            )
            return []

        users = []

        started = False

        for line in result.stdout.splitlines():

            line = line.strip()

            if not line:
                continue

            # Start reading after this separator
            if line.startswith("---"):
                started = True
                continue

            if not started:
                continue

            # End of users
            if line.lower().startswith(
                "the command completed successfully"
            ):
                break

            users.append(line)

        return users

    except Exception as e:
        logging.exception("Error reading RDP users: %s", e)
        return []


# ============================================================
# REMOVE UNAUTHORIZED USER
# ============================================================

def remove_rdp_user(username):

    logging.warning(
        "Unauthorized Remote Desktop user detected: %s",
        username
    )

    try:

        result = subprocess.run(
            [
                "net",
                "localgroup",
                "Remote Desktop Users",
                username,
                "/delete"
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )

        if result.returncode == 0:

            logging.warning(
                "Removed unauthorized RDP user: %s",
                username
            )

            print(
                f"[{datetime.now()}] Removed: {username}"
            )

            return True

        else:

            logging.error(
                "Failed to remove %s: %s",
                username,
                result.stdout.strip()
            )

            return False

    except Exception as e:

        logging.exception(
            "Exception removing user %s: %s",
            username,
            e
        )

        return False


# ============================================================
# SECURITY CHECK
# ============================================================

def check_rdp_users():

    users = get_rdp_users()

    if not users:
        logging.info(
            "No Remote Desktop Users found."
        )
        return

    logging.info(
        "Current Remote Desktop Users: %s",
        users
    )

    for username in users:

        # Remove domain prefix if present:
        # DOMAIN\username -> username
        clean_username = username.split("\\")[-1]

        if clean_username not in ALLOWED_USERS:
            remove_rdp_user(username)

        else:
            logging.info(
                "Allowed RDP user: %s",
                username
            )


# ============================================================
# MAIN WATCHDOG
# ============================================================

def main():

    if not is_admin():

        print(
            "ERROR: This program must be run as Administrator."
        )

        logging.error(
            "Program was not started with administrator privileges."
        )

        return

    print("=" * 60)
    print("RDP USER SECURITY WATCHDOG")
    print("=" * 60)

    print(
        f"Checking every {CHECK_INTERVAL // 60} minutes."
    )

    print(
        f"Allowed users: {', '.join(ALLOWED_USERS)}"
    )

    logging.info(
        "RDP Guard started."
    )

    # First check immediately
    check_rdp_users()

    while True:

        time.sleep(CHECK_INTERVAL)

        logging.info(
            "Running scheduled RDP user check."
        )

        check_rdp_users()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()