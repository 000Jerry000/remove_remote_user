import subprocess
import time
import logging
from datetime import datetime
import os

# Setup logging
log_file = os.path.expanduser("~/rdp_cleanup.log")
logging.basicConfig(
  level=logging.INFO,
  format='%(asctime)s - %(levelname)s - %(message)s',
  handlers=[
      logging.FileHandler(log_file),
      logging.StreamHandler()
  ]
)
logger = logging.getLogger(__name__)

# Protected system accounts - DO NOT DELETE
PROTECTED_USERS = {
    'Administrator',
    'Guest',
    'DefaultAccount',
    'WDAGUtilityAccount'
}

# Known legitimate RDP users (add your own accounts here)
LEGITIMATE_USERS = {
    # 'your_username',  # Uncomment and add your own usernames
    
}

def get_local_users():
    """Get list of all local users on the system"""
    try:
        result = subprocess.run(
            ['net', 'user'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            users = []
            for line in lines:
                line = line.strip()
                # Skip headers and empty lines
                if line and not line.startswith('---') and line != 'User accounts for' and '\\\\' not in line:
                    # Users are listed, filter out the command output headers
                    if line and not any(x in line for x in ['User accounts for', 'The command completed']):
                        users.extend(line.split())
            return [u for u in users if u]
        else:
            logger.error(f"Failed to get user list: {result.stderr}")
            return []
    except Exception as e:
        logger.error(f"Error getting local users: {e}")
        return []

def get_rdp_users():
    """Get list of users in Remote Desktop Users group"""
    try:
        result = subprocess.run(
            ['net', 'localgroup', 'Remote Desktop Users'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            rdp_users = []
            capture = False
            
            for line in lines:
                line = line.strip()
                # Start capturing after the header
                if '---' in line:
                    capture = True
                    continue
                # Stop at command completion line
                if 'The command completed' in line:
                    break
                # Capture user entries
                if capture and line and not line.startswith('---'):
                    rdp_users.append(line)
            
            return rdp_users
        else:
            logger.error(f"Failed to get RDP users: {result.stderr}")
            return []
    except Exception as e:
        logger.error(f"Error getting RDP users: {e}")
        return []

def remove_user_from_rdp_group(username):
    """Remove a user from Remote Desktop Users group"""
    try:
        result = subprocess.run(
            ['net', 'localgroup', 'Remote Desktop Users', username, '/delete'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            logger.warning(f"REMOVED from RDP group: {username}")
            return True
        else:
            logger.error(f"Failed to remove {username} from RDP group: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Error removing {username} from RDP: {e}")
        return False

def delete_user_account(username):
    """Delete a local user account"""
    try:
        result = subprocess.run(
            ['net', 'user', username, '/delete'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            logger.warning(f"DELETED user account: {username}")
            return True
        else:
            logger.error(f"Failed to delete {username}: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Error deleting {username}: {e}")
        return False

def cleanup_cycle():
    """Main cleanup cycle"""
    logger.info("=" * 60)
    logger.info("Starting RDP user cleanup cycle")
    logger.info("=" * 60)
    
    rdp_users = get_rdp_users()
    logger.info(f"Found {len(rdp_users)} RDP users: {rdp_users}")
    
    removed_count = 0
    
    for user in rdp_users:
        # Skip protected and legitimate users
        if user in PROTECTED_USERS or user in LEGITIMATE_USERS:
            logger.info(f"SKIPPED (protected/legitimate): {user}")
            continue
        
        # Remove from RDP group first
        if remove_user_from_rdp_group(user):
            removed_count += 1
            
            # Optionally delete the account entirely
            # Uncomment the line below if you want to delete the entire account
            # delete_user_account(user)
    
    logger.info(f"Cleanup cycle complete. Removed {removed_count} unauthorized users.")
    logger.info("=" * 60)
    logger.info("")

def main():
    """Main loop - runs cleanup every 15 minutes"""
    logger.info("RDP User Cleanup Bot started")
    logger.info("Cycle interval: 1 minutes")
    logger.info("Log file: " + log_file)
    logger.info("")
    
    cycle_interval = 1 * 60  # 15 minutes in seconds
    
    try:
        while True:
            cleanup_cycle()
            logger.info(f"Next cleanup in 1 minutes ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
            time.sleep(cycle_interval)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {e}")

if __name__ == "__main__":
    main()