import os
import csv
from flask import Flask, jsonify

# Path to the CSV file inside the container
TARGETS_CSV_PATH = '/data/targets.csv'

# The broadcast IP for your 172.16.0.1/21 network
BROADCAST_IP = "172.16.7.255"

app = Flask(__name__)

def send_wol_packet(mac):
    """
    A helper function to send a single WoL packet.
    This version explicitly sets the broadcast IP and port to avoid script errors.
    """
    # Use the -i flag for the broadcast IP and -p for the port
    command = f"wakeonlan -i {BROADCAST_IP} -p 9 {mac}"
    result = os.system(command)
    return result == 0

# --- Keep the rest of your app.py file the same ---

@app.route('/wakeup/<mac_address>', methods=['GET'])
def wakeup_single(mac_address):
    """Wakes up a single machine by its MAC address."""
    if not (12 <= len(mac_address) <= 17) and len(mac_address.replace(":", "").replace("-", "")) != 12:
        return jsonify({"status": "error", "message": "Invalid MAC address format."}), 400
    
    if send_wol_packet(mac_address):
        print(f"Successfully sent WoL packet to {mac_address}")
        return jsonify({"status": "success", "message": f"WoL packet sent to {mac_address}"})
    else:
        print(f"Failed to send WoL packet to {mac_address}")
        return jsonify({"status": "error", "message": "Failed to execute wakeonlan command."}), 500

@app.route('/wakeup/batch', methods=['GET'])
def wakeup_batch():
    """
    Reads all MAC addresses from the CSV file and sends WoL packets to each.
    """
    successes = []
    failures = []

    try:
        with open(TARGETS_CSV_PATH, mode='r', newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.reader(csvfile)
            next(reader) # Skip header

            for i, row in enumerate(reader):
                if len(row) >= 3:
                    mac = row[2].strip()
                    if mac:
                        if send_wol_packet(mac):
                            successes.append(mac)
                        else:
                            failures.append(mac)
                    else:
                        failures.append(f"Empty MAC in row {i+2}")
                else:
                    failures.append(f"Malformed row {i+2}")

    except FileNotFoundError:
        return jsonify({"status": "error", "message": "targets.csv not found."}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
    return jsonify({
        "status": "complete",
        "sent_packets": len(successes),
        "failed_packets": len(failures),
        "successes": successes,
        "failures": failures
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
