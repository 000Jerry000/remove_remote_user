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

# Add ONLY legitimate accounts that are allowed
# to be members of "Remote Desktop Users".
ALLOWED_USERS = {
    "Administrator",
    # "AKIRA",
}

LOG_FILE = r"D:\git\remove_remote_user\rdp_guard.log"


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

            if line.startswith("---"):
                started = True
                continue

            if not started:
                continue

            if line.lower().startswith(
                "the command completed successfully"
            ):
                break

            users.append(line)

        return users

    except Exception as e:

        logging.exception(
            "Error reading RDP users: %s",
            e
        )

        return []


# ============================================================
# REMOVE UNAUTHORIZED RDP USER
# ============================================================

def remove_rdp_user(username):

    logging.warning(
        "UNAUTHORIZED RDP USER DETECTED: %s",
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
            errors="ignore"
        )

        if result.returncode == 0:

            logging.warning(
                "Successfully removed unauthorized RDP user: %s",
                username
            )

            print(
                f"[{datetime.now()}] Removed: {username}"
            )

            return True

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
# CHECK RDP USERS
# ============================================================

def check_rdp_users():
    print(
        f"[{datetime.now()}] Checking Remote Desktop Users..."
    )

    users = get_rdp_users()

    if not users:
        logging.info(
            "No Remote Desktop Users found."
        )
        print("No RDP users found.")
        return

    logging.info(
        "Current RDP users: %s",
        users
    )

    for username in users:

        clean_username = username.split("\\")[-1]

        if clean_username not in ALLOWED_USERS:
            remove_rdp_user(username)

        else:
            logging.info(
                "Allowed RDP user: %s",
                username
            )

            print(
                f"Allowed RDP user: {username}"
            )


# ============================================================
# MAIN
# ============================================================

def main():

    if not is_admin():

        print()
        print("=" * 70)
        print("ERROR: Administrator privileges are required.")
        print("=" * 70)
        print()
        print("Please open Command Prompt with:")
        print("Run as administrator")
        print()

        return

    print("=" * 70)
    print("🛡️  RDP SECURITY GUARD")
    print("=" * 70)
    print(
        f"Check interval: {CHECK_INTERVAL // 60} minutes"
    )
    print(
        "Allowed users:",
        ", ".join(ALLOWED_USERS) if ALLOWED_USERS else "NONE"
    )
    print("=" * 70)

    logging.info(
        "RDP Security Guard started."
    )

    # Check immediately
    check_rdp_users()

    while True:

        time.sleep(CHECK_INTERVAL)

        check_rdp_users()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()