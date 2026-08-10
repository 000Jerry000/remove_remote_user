import subprocess
import time
import logging
import ctypes
from datetime import datetime

from winotify import Notification, audio


# ============================================================
# CONFIGURATION
# ============================================================

CHECK_INTERVAL = 1 * 60  # 1 minutes

# Users that are allowed to remain in Remote Desktop Users.
ALLOWED_USERS = {
    "Administrator",
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
# ADMINISTRATOR CHECK
# ============================================================

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


# ============================================================
# DESKTOP SECURITY NOTIFICATION
# ============================================================

def security_alert(username):

    title = "🚨 SECURITY ALERT"

    message = (
        "Possible malware activity detected.\n\n"
        f"Unauthorized RDP account:\n{username}\n\n"
        "The account is being removed."
    )

    print()
    print("=" * 70)
    print("🚨🚨🚨 SECURITY ALERT 🚨🚨🚨")
    print("=" * 70)
    print(f"Unauthorized RDP account: {username}")
    print("Possible malware activity detected.")
    print("The account is being removed.")
    print("=" * 70)
    print()

    try:
        toast = Notification(
            app_id="RDP Security Guard",
            title=title,
            msg=message
        )

        toast.set_audio(
            audio.LoopingAlarm,
            loop=False
        )

        toast.show()

    except Exception as e:

        logging.error(
            "Failed to display desktop notification: %s",
            e
        )


# ============================================================
# GET REMOTE DESKTOP USERS
# ============================================================

def get_rdp_users():

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
            errors="ignore",
            timeout=30
        )

        if result.returncode != 0:
            logging.error(
                "Failed to query Remote Desktop Users: %s",
                result.stdout.strip()
            )

            print(
                "[ERROR] Failed to query Remote Desktop Users."
            )

            return None

        users = []

        for line in result.stdout.splitlines():

            line = line.strip()

            if not line:
                continue

            # Skip headers/separators
            if line.startswith("Alias name"):
                continue

            if line.startswith("Comment"):
                continue

            if line.startswith("Members"):
                continue

            if line.startswith("---"):
                continue

            if line.lower().startswith(
                "the command completed successfully"
            ):
                continue

            users.append(line)

        return users

    except subprocess.TimeoutExpired:

        logging.error(
            "Timeout while checking Remote Desktop Users."
        )

        print(
            "[ERROR] Windows command timed out."
        )

        return None

    except Exception as e:

        logging.exception(
            "Unexpected error: %s",
            e
        )

        print(
            f"[ERROR] {e}"
        )

        return None


# ============================================================
# REMOVE USER
# ============================================================

def remove_rdp_user(username):

    print(
        f"[SECURITY] Unauthorized user detected: {username}"
    )

    logging.warning(
        "Unauthorized Remote Desktop user detected: %s",
        username
    )

    # Show notification BEFORE removing account
    security_alert(username)

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
            errors="ignore",
            timeout=30
        )

        if result.returncode == 0:

            print(
                f"[SECURITY] Removed user: {username}"
            )

            logging.warning(
                "Removed unauthorized RDP user: %s",
                username
            )

            return True

        else:

            print(
                f"[ERROR] Could not remove: {username}"
            )

            logging.error(
                "Failed to remove %s: %s",
                username,
                result.stdout.strip()
            )

            return False

    except subprocess.TimeoutExpired:

        print(
            f"[ERROR] Timeout removing: {username}"
        )

        logging.error(
            "Timeout removing user: %s",
            username
        )

        return False

    except Exception as e:

        print(
            f"[ERROR] {e}"
        )

        logging.exception(
            "Exception removing user %s",
            username
        )

        return False


# ============================================================
# CHECK USERS
# ============================================================

def check_rdp_users():

    print()
    print(
        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
        "Checking Remote Desktop Users..."
    )

    logging.info(
        "Starting Remote Desktop Users check."
    )

    users = get_rdp_users()

    if users is None:
        print(
            "[WARNING] Could not complete this check."
        )
        return

    if not users:

        print(
            "[OK] No Remote Desktop Users found."
        )

        logging.info(
            "No Remote Desktop Users found."
        )

        return

    print(
        f"[INFO] Found {len(users)} RDP user(s):"
    )

    for username in users:

        print(
            f"       - {username}"
        )

    logging.info(
        "Current Remote Desktop Users: %s",
        users
    )

    for username in users:

        # Convert DOMAIN\User to User
        clean_username = username.split("\\")[-1]

        if clean_username in ALLOWED_USERS:

            print(
                f"[OK] Allowed user: {username}"
            )

            logging.info(
                "Allowed RDP user: %s",
                username
            )

        else:

            remove_rdp_user(username)


# ============================================================
# COUNTDOWN
# ============================================================

def countdown(seconds):

    remaining = seconds

    while remaining > 0:

        minutes = remaining // 60
        secs = remaining % 60

        print(
            f"\r[WAITING] Next check in "
            f"{minutes:02d}:{secs:02d}",
            end="",
            flush=True
        )

        # Sleep for one second
        time.sleep(1)

        remaining -= 1

    print()


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 65)
    print("        RDP USER SECURITY WATCHDOG")
    print("=" * 65)
    print()

    if not is_admin():

        print(
            "[ERROR] Administrator privileges are required."
        )

        print()
        print(
            "Please run Command Prompt as Administrator."
        )

        logging.error(
            "Program started without Administrator privileges."
        )

        input(
            "\nPress Enter to exit..."
        )

        return

    print(
        "[OK] Administrator privileges confirmed."
    )

    print(
        f"[OK] Check interval: {CHECK_INTERVAL // 60} minutes"
    )

    if ALLOWED_USERS:

        print(
            "[OK] Allowed users:"
        )

        for user in ALLOWED_USERS:
            print(
                f"     - {user}"
            )

    else:

        print(
            "[WARNING] No users are allowed."
        )

    print()
    print(
        "Watchdog started."
    )

    print(
        "Press Ctrl+C to stop."
    )

    logging.info(
        "RDP Guard started."
    )

    # ========================================================
    # MAIN LOOP
    # ========================================================

    cycle = 1

    while True:

        print()
        print(
            "=" * 65
        )

        print(
            f"CHECK CYCLE #{cycle}"
        )

        print(
            "=" * 65
        )

        logging.info(
            "Starting check cycle #%d",
            cycle
        )

        try:

            check_rdp_users()

        except Exception as e:

            print(
                f"[ERROR] Check failed: {e}"
            )

            logging.exception(
                "Check cycle failed."
            )

        print()
        print(
            "[OK] Check completed."
        )

        logging.info(
            "Check cycle #%d completed.",
            cycle
        )

        cycle += 1

        print()
        print(
            "Waiting 1 minutes before the next check..."
        )

        countdown(CHECK_INTERVAL)

# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        print()
        print()
        print(
            "[INFO] RDP Security Watchdog stopped."
        )

        logging.info(
            "RDP Guard stopped by user."
        )