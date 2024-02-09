import subprocess
import time

def toggle_packet_loss(interface, loss_percentage, duration, repeat=True):
    def apply_packet_loss():
        subprocess.run(["tc", "qdisc", "add", "dev", interface, "root", "netem", "loss", f"{loss_percentage}%"], stdout=subprocess.PIPE)
        print("Packet loss configuration applied.")

    def remove_packet_loss():
        subprocess.run(["tc", "qdisc", "del", "dev", interface, "root"], stdout=subprocess.PIPE)
        print("Packet loss configuration removed.")

    try:
        while True:
            # Apply packet loss
            apply_packet_loss()
            time.sleep(duration)

            # Remove packet loss
            remove_packet_loss()

            # If not repeating, break the loop
            if not repeat:
                break

            # Wait for the same duration before reapplying
            time.sleep(duration)

    except KeyboardInterrupt:
        # Ensure packet loss is removed if the process is interrupted
        remove_packet_loss()
        print("Packet loss configuration removed. Exiting.")

if __name__ == "__main__":
    toggle_packet_loss("eth0", 1, 60)
