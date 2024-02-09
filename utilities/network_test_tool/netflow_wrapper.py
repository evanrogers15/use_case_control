import subprocess
import time
import os
import signal

# Path to the script you want to run
script_path = '/home/netflow.py'

def run_script():
    # Start the script
    process = subprocess.Popen(['python3', script_path])

    try:
        # Let the script run for 3 hours
        time.sleep(3 * 3600)

        # Stop the script
        process.send_signal(signal.SIGTERM)

        # Wait for the process to terminate
        process.wait()

    except Exception as e:
        print(f"Error occurred: {e}")

    # Restart the script after 5 seconds
    time.sleep(5)
    run_script()

# Run the script
run_script()
