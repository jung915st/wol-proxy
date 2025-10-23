# WoL Proxy - Wake-on-LAN Proxy Service

## Project Overview

This is a Flask-based REST API service that provides Wake-on-LAN (WoL) functionality over HTTP. The application allows you to wake up network devices remotely by sending magic packets to their MAC addresses, either individually or in batch mode.

## Architecture

The project uses:
- **Flask**: Lightweight Python web framework for the REST API
- **Docker**: Containerization for easy deployment
- **wakeonlan**: Linux utility for sending WoL magic packets
- **CSV**: Storage format for target device configurations

## Code Analysis

### Main Application (`app.py`)

The application consists of several key components:

#### 1. Configuration Constants

```python
TARGETS_CSV_PATH = '/data/targets.csv'  # Path to CSV containing target devices
BROADCAST_IP = "172.16.0.255"          # Network broadcast address for WoL packets
```

- `TARGETS_CSV_PATH`: Mounted volume path where the CSV file with target devices is stored
- `BROADCAST_IP`: Configured for a 172.16.0.1/21 network (subnet mask 255.255.248.0)

#### 2. Core Functions

##### `send_wol_packet(mac)`

**Purpose**: Sends a Wake-on-LAN magic packet to a specific MAC address.

**Parameters**:
- `mac` (string): MAC address of the target device

**Returns**: 
- `True` if the packet was sent successfully
- `False` if the command failed

**Implementation Details**:
- Uses the `wakeonlan` system command
- Explicitly sets broadcast IP with `-i` flag
- Sets UDP port to 9 with `-p` flag
- Executes command using `os.system()`
- Return code of 0 indicates success

**Example**:
```python
send_wol_packet("D8:43:AE:6F:42:63")  # Returns True/False
```

#### 3. API Endpoints

##### `GET /wakeup/<mac_address>`

**Purpose**: Wake up a single device by its MAC address.

**Parameters**:
- `mac_address` (URL parameter): MAC address in various formats (with colons, dashes, or plain)

**Validation**:
- Checks MAC address length (12-17 characters)
- Validates that cleaned MAC address (without separators) is exactly 12 characters

**Response**:
- Success (200): `{"status": "success", "message": "WoL packet sent to <mac>"}`
- Invalid MAC (400): `{"status": "error", "message": "Invalid MAC address format."}`
- Command failure (500): `{"status": "error", "message": "Failed to execute wakeonlan command."}`

**Console Output**:
- Logs success/failure to stdout for debugging

**Example Usage**:
```bash
curl http://localhost:5000/wakeup/D8:43:AE:6F:42:63
curl http://localhost:5000/wakeup/D8-43-AE-6F-42-63
curl http://localhost:5000/wakeup/D843AE6F4263
```

##### `GET /wakeup/batch`

**Purpose**: Wake up all devices listed in the CSV file.

**CSV Format**:
```csv
location,ip_address,mac_address
一年二班,172.16.7.149,D8-43-AE-6F-42-63
```

**Processing Logic**:
1. Opens the CSV file with UTF-8-BOM encoding support (`utf-8-sig`)
2. Skips the header row
3. Iterates through each row
4. Extracts MAC address from the third column (index 2)
5. Sends WoL packet to each valid MAC address
6. Tracks successes and failures

**Error Handling**:
- Empty MAC addresses: Recorded as failures with row number
- Malformed rows (< 3 columns): Recorded as failures with row number
- File not found: Returns 500 error
- General exceptions: Returns 500 with error message

**Response**:
```json
{
  "status": "complete",
  "sent_packets": 10,
  "failed_packets": 2,
  "successes": ["MAC1", "MAC2", ...],
  "failures": ["MAC3", "Empty MAC in row 5"]
}
```

**Example Usage**:
```bash
curl http://localhost:5000/wakeup/batch
```

#### 4. Application Entry Point

```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

- Binds to all network interfaces (`0.0.0.0`)
- Listens on port 5000
- Allows access from outside the container

### Docker Configuration

#### `Dockerfile`

**Base Image**: `debian:bookworm-slim`
- Minimal Debian installation for smaller container size

**Installed Packages**:
- `python3`: Python runtime
- `python3-pip`: Python package installer
- `wakeonlan`: WoL utility for sending magic packets
- `python3-flask`: Flask web framework
- `netbase`: Provides `/etc/protocols` file required by networking tools

**Container Setup**:
- Working directory: `/app`
- Exposes port 5000
- Runs `python3 app.py` on startup
- Cleans up apt cache to reduce image size

#### `docker-compose.yml`

**Service Configuration**:
- Service name: `wol-proxy`
- Container name: `wol-proxy`
- Restart policy: `unless-stopped`

**Volume Mounting**:
- Mounts `./target.csv` to `/data/targets.csv` (read-only)
- Uses explicit bind mount syntax for clarity
- Allows updating the CSV without rebuilding the container

**Network Configuration**:
- Maps host port 5000 to container port 5000
- Commented out `network_mode: "host"` (could be used for direct network access)

## Data Format

### `target.csv`

The CSV file contains target device information with three columns:

| Column        | Description                          | Example           |
|---------------|--------------------------------------|-------------------|
| location      | Human-readable location/device name  | 一年二班          |
| ip_address    | IP address of the device             | 172.16.7.149      |
| mac_address   | MAC address (various formats)        | D8:43:AE:6F:42:63 |

**Supported MAC Formats**:
- Colon-separated: `D8:43:AE:6F:42:63`
- Dash-separated: `D8-43-AE-6F-42-63`
- Plain: `D843AE6F4263`

## Deployment

### Building the Container

```bash
docker-compose build
```

### Running the Service

```bash
docker-compose up -d
```

### Updating Target Devices

1. Edit `target.csv` with new device information
2. Restart the container (volume is read-only, so restart picks up changes):
   ```bash
   docker-compose restart
   ```

## Network Requirements

- The service must run on the same network segment as the target devices
- WoL magic packets are sent to broadcast address `172.16.0.255`
- UDP port 9 is used for WoL packets
- Devices must support Wake-on-LAN in their BIOS/firmware

## Security Considerations

1. **No Authentication**: The API has no authentication mechanism
   - Should be deployed on a trusted network
   - Consider adding authentication for production use

2. **CSV File Permissions**: Mounted as read-only to prevent modification

3. **Input Validation**: MAC addresses are validated for length, but not for exact format

## Use Cases

This service appears to be designed for a school or educational institution (based on classroom names in Chinese):
- Wake up classroom computers remotely
- Batch wake-up for all devices at once
- Automated power management

## API Examples

### Wake Single Device

```bash
# Wake up a specific classroom computer
curl http://localhost:5000/wakeup/D8:43:AE:6F:42:63
```

### Wake All Devices

```bash
# Wake up all devices in the CSV
curl http://localhost:5000/wakeup/batch
```

## Troubleshooting

### Common Issues

1. **WoL packets not working**:
   - Verify devices have WoL enabled in BIOS
   - Check network firewall rules
   - Ensure broadcast address is correct for your network

2. **CSV file not found**:
   - Verify volume mount path in docker-compose.yml
   - Ensure target.csv exists in the same directory

3. **Permission denied errors**:
   - Check file permissions on target.csv
   - Verify container has read access to the mounted file

## Function Summary

| Function/Endpoint      | Purpose                              | Input                | Output              |
|------------------------|--------------------------------------|----------------------|---------------------|
| `send_wol_packet()`    | Send WoL magic packet                | MAC address (string) | Boolean (success)   |
| `GET /wakeup/<mac>`    | Wake single device                   | MAC address (URL)    | JSON response       |
| `GET /wakeup/batch`    | Wake all devices from CSV            | None                 | JSON with results   |

## Code Quality Observations

### Strengths:
- Clear separation of concerns (helper function vs. endpoints)
- Good error handling with specific error messages
- Console logging for debugging
- Flexible MAC address format support
- UTF-8-BOM support for international characters

### Potential Improvements:
- Add authentication/authorization
- Add rate limiting to prevent abuse
- Use subprocess.run() instead of os.system() for better security
- Add more robust MAC address validation
- Consider async processing for batch operations
- Add health check endpoint
- Environment variables for configuration (broadcast IP, CSV path)
- Add unit tests
- Add API documentation (OpenAPI/Swagger)
