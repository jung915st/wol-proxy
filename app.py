"""
WoL Proxy - Wake-on-LAN REST API Service

This Flask application provides HTTP endpoints to send Wake-on-LAN (WoL) magic packets
to network devices, enabling remote power-on functionality.

The service supports:
- Single device wake-up via MAC address
- Batch wake-up of all devices listed in a CSV file
"""

import os
import csv
from flask import Flask, jsonify

# Path to the CSV file inside the container
# This file contains the list of target devices with their MAC addresses
TARGETS_CSV_PATH = '/data/targets.csv'

# The broadcast IP for the 172.16.0.1/21 network
# WoL packets are sent to this broadcast address to reach all devices on the subnet
BROADCAST_IP = "172.16.0.255"

app = Flask(__name__)

def send_wol_packet(mac):
    """
    Send a Wake-on-LAN magic packet to a specific MAC address.
    
    This function uses the 'wakeonlan' command-line utility to send a magic packet
    that can wake up a sleeping or powered-off network device.
    
    Args:
        mac (str): MAC address of the target device. Can be in various formats:
                   - Colon-separated: "D8:43:AE:6F:42:63"
                   - Dash-separated: "D8-43-AE-6F-42-63"
                   - Plain: "D843AE6F4263"
    
    Returns:
        bool: True if the wakeonlan command executed successfully (exit code 0),
              False otherwise.
    
    Note:
        - Uses broadcast IP to ensure the packet reaches the target subnet
        - Sends to UDP port 9 (standard WoL port)
        - The device must have Wake-on-LAN enabled in BIOS/firmware
    """
    # Use the -i flag for the broadcast IP and -p for the port
    command = f"wakeonlan -i {BROADCAST_IP} -p 9 {mac}"
    result = os.system(command)
    return result == 0

@app.route('/wakeup/<mac_address>', methods=['GET'])
def wakeup_single(mac_address):
    """
    Wake up a single network device by its MAC address.
    
    This endpoint validates the MAC address format and sends a WoL magic packet
    to wake the specified device.
    
    Args:
        mac_address (str): MAC address from the URL path. Supports multiple formats:
                          - With colons: D8:43:AE:6F:42:63
                          - With dashes: D8-43-AE-6F-42-63
                          - Plain hex: D843AE6F4263
    
    Returns:
        JSON response with status and message:
        - 200: Success - {"status": "success", "message": "WoL packet sent to <mac>"}
        - 400: Invalid MAC address format
        - 500: Failed to execute wakeonlan command
    
    Example:
        GET http://localhost:5000/wakeup/D8:43:AE:6F:42:63
    """
    # Validate MAC address format
    # Length check: 12 chars (plain) to 17 chars (with separators)
    # Also verify that without separators it's exactly 12 hex chars
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
    Wake up all devices listed in the CSV file.
    
    This endpoint reads the CSV file containing target device information and sends
    WoL packets to each device. It tracks both successful and failed operations.
    
    CSV Format:
        location,ip_address,mac_address
        一年二班,172.16.7.149,D8:43:AE:6F:42:63
        ...
    
    Returns:
        JSON response with batch operation results:
        {
            "status": "complete",
            "sent_packets": <count>,
            "failed_packets": <count>,
            "successes": [<list of successful MAC addresses>],
            "failures": [<list of failed MAC addresses or error descriptions>]
        }
        
        Error responses (500):
        - File not found
        - Other exceptions with error message
    
    Processing:
        1. Opens CSV file with UTF-8-BOM encoding support
        2. Skips header row
        3. Extracts MAC address from column 3 (index 2)
        4. Sends WoL packet to each valid MAC
        5. Records successes and failures
    
    Example:
        GET http://localhost:5000/wakeup/batch
    """
    successes = []
    failures = []

    try:
        # Open CSV with UTF-8-BOM encoding to handle files with byte order marks
        with open(TARGETS_CSV_PATH, mode='r', newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Skip header row

            # Process each row in the CSV
            for i, row in enumerate(reader):
                # Check if row has all required columns (location, ip, mac)
                if len(row) >= 3:
                    mac = row[2].strip()  # MAC address is in the third column
                    if mac:
                        # Attempt to send WoL packet
                        if send_wol_packet(mac):
                            successes.append(mac)
                        else:
                            failures.append(mac)
                    else:
                        # Empty MAC address in this row
                        failures.append(f"Empty MAC in row {i+2}")
                else:
                    # Row doesn't have enough columns
                    failures.append(f"Malformed row {i+2}")

    except FileNotFoundError:
        return jsonify({"status": "error", "message": "targets.csv not found."}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
    # Return summary of batch operation
    return jsonify({
        "status": "complete",
        "sent_packets": len(successes),
        "failed_packets": len(failures),
        "successes": successes,
        "failures": failures
    })


if __name__ == '__main__':
    """
    Application entry point.
    
    Starts the Flask development server on all network interfaces (0.0.0.0)
    on port 5000, making it accessible from outside the container.
    
    Note: This is suitable for development and containerized deployments.
          For production, consider using a WSGI server like gunicorn or uWSGI.
    """
    app.run(host='0.0.0.0', port=5000)
