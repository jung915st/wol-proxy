# WoL Proxy API Documentation

## Overview

The WoL Proxy provides a REST API for sending Wake-on-LAN (WoL) magic packets to network devices. This allows remote power-on functionality over HTTP.

**Base URL**: `http://localhost:5000`

## Endpoints

### 1. Wake Single Device

Wake up a single network device by its MAC address.

**Endpoint**: `GET /wakeup/<mac_address>`

**Parameters**:
- `mac_address` (path parameter, required): MAC address of the target device

**Supported MAC Address Formats**:
- Colon-separated: `D8:43:AE:6F:42:63`
- Dash-separated: `D8-43-AE-6F-42-63`
- Plain hexadecimal: `D843AE6F4263`

**Request Example**:
```bash
curl http://localhost:5000/wakeup/D8:43:AE:6F:42:63
```

**Success Response** (200 OK):
```json
{
  "status": "success",
  "message": "WoL packet sent to D8:43:AE:6F:42:63"
}
```

**Error Responses**:

*Invalid MAC Address Format (400 Bad Request)*:
```json
{
  "status": "error",
  "message": "Invalid MAC address format."
}
```

*Command Execution Failure (500 Internal Server Error)*:
```json
{
  "status": "error",
  "message": "Failed to execute wakeonlan command."
}
```

**cURL Examples**:
```bash
# Wake with colon-separated MAC
curl http://localhost:5000/wakeup/D8:43:AE:6F:42:63

# Wake with dash-separated MAC
curl http://localhost:5000/wakeup/D8-43-AE-6F-42-63

# Wake with plain MAC
curl http://localhost:5000/wakeup/D843AE6F4263
```

---

### 2. Wake Multiple Devices (Batch)

Wake up all devices listed in the configured CSV file.

**Endpoint**: `GET /wakeup/batch`

**Parameters**: None

**CSV File Format**:
The CSV file must be located at `/data/targets.csv` (inside the container) and should have the following format:

```csv
location,ip_address,mac_address
一年二班,172.16.7.149,D8:43:AE:6F:42:63
一年三班,172.16.7.131,D8:43:AE:6F:42:65
```

- **Column 1** (`location`): Human-readable location or device name
- **Column 2** (`ip_address`): IP address of the device (informational only)
- **Column 3** (`mac_address`): MAC address (required for WoL)

**Request Example**:
```bash
curl http://localhost:5000/wakeup/batch
```

**Success Response** (200 OK):
```json
{
  "status": "complete",
  "sent_packets": 3,
  "failed_packets": 1,
  "successes": [
    "D8:43:AE:6F:42:63",
    "D8:43:AE:6F:42:65",
    "D843AE746D49"
  ],
  "failures": [
    "Empty MAC in row 5"
  ]
}
```

**Response Fields**:
- `status`: Always "complete" for successful execution
- `sent_packets`: Number of successfully sent WoL packets
- `failed_packets`: Number of failed attempts
- `successes`: Array of MAC addresses that received packets successfully
- `failures`: Array of MAC addresses or error descriptions for failures

**Error Responses**:

*CSV File Not Found (500 Internal Server Error)*:
```json
{
  "status": "error",
  "message": "targets.csv not found."
}
```

*Other Errors (500 Internal Server Error)*:
```json
{
  "status": "error",
  "message": "<error description>"
}
```

**cURL Example**:
```bash
curl http://localhost:5000/wakeup/batch
```

---

## Error Handling

The API uses standard HTTP status codes:

- **200 OK**: Request successful
- **400 Bad Request**: Invalid input (e.g., malformed MAC address)
- **500 Internal Server Error**: Server-side error (e.g., file not found, command failure)

All error responses include:
```json
{
  "status": "error",
  "message": "<error description>"
}
```

---

## Network Requirements

For WoL packets to successfully wake devices:

1. **Same Network Segment**: The service must run on the same network as target devices
2. **Broadcast Address**: Configured for `172.16.0.255` (172.16.0.1/21 network)
3. **UDP Port**: Uses port 9 (standard WoL port)
4. **Device Support**: Target devices must have Wake-on-LAN enabled in BIOS/firmware
5. **Network Configuration**: Switches and routers must allow broadcast packets

---

## Troubleshooting

### WoL Packets Not Working

**Problem**: API returns success but devices don't wake up

**Solutions**:
1. Verify WoL is enabled in device BIOS/firmware
2. Check that the broadcast address matches your network configuration
3. Ensure network switches/routers allow broadcast packets
4. Verify devices are connected via Ethernet (not Wi-Fi)
5. Check firewall rules allow UDP port 9

### CSV File Not Found

**Problem**: `/wakeup/batch` returns "targets.csv not found"

**Solutions**:
1. Verify the CSV file is mounted correctly in docker-compose.yml
2. Check file path in the container: `docker exec wol-proxy ls -la /data/`
3. Ensure the source file exists: `./target.csv`

### Invalid MAC Address Format

**Problem**: API returns "Invalid MAC address format"

**Solutions**:
1. Ensure MAC address is 12 hexadecimal characters
2. Use supported separators (`:` or `-`) or no separator at all
3. Example valid formats:
   - `D8:43:AE:6F:42:63`
   - `D8-43-AE-6F-42-63`
   - `D843AE6F4263`

---

## Security Considerations

⚠️ **Important Security Notes**:

1. **No Authentication**: This API has no built-in authentication
   - Deploy only on trusted networks
   - Consider adding authentication for production use
   - Use firewall rules to restrict access

2. **Input Validation**: Limited to MAC address format checking
   - Does not validate if MAC address exists
   - No rate limiting implemented

3. **Recommended Production Setup**:
   - Add authentication middleware (e.g., API keys, OAuth)
   - Implement rate limiting
   - Use HTTPS/TLS
   - Deploy behind a reverse proxy (nginx, Apache)
   - Monitor and log all API access

---

## Testing the API

### Using cURL

```bash
# Test single device wake
curl -v http://localhost:5000/wakeup/D8:43:AE:6F:42:63

# Test batch wake
curl -v http://localhost:5000/wakeup/batch
```

### Using Python

```python
import requests

# Wake single device
response = requests.get('http://localhost:5000/wakeup/D8:43:AE:6F:42:63')
print(response.json())

# Wake all devices
response = requests.get('http://localhost:5000/wakeup/batch')
result = response.json()
print(f"Sent: {result['sent_packets']}, Failed: {result['failed_packets']}")
```

### Using JavaScript/Fetch

```javascript
// Wake single device
fetch('http://localhost:5000/wakeup/D8:43:AE:6F:42:63')
  .then(response => response.json())
  .then(data => console.log(data));

// Wake all devices
fetch('http://localhost:5000/wakeup/batch')
  .then(response => response.json())
  .then(data => {
    console.log(`Sent: ${data.sent_packets}, Failed: ${data.failed_packets}`);
    console.log('Successes:', data.successes);
    console.log('Failures:', data.failures);
  });
```

---

## Rate Limiting

⚠️ **Note**: This API does not implement rate limiting. Consider adding it for production use to prevent abuse.

---

## Integration Examples

### Scheduled Wake-up (Cron)

Wake all devices at 8:00 AM every weekday:

```bash
# Add to crontab
0 8 * * 1-5 curl http://localhost:5000/wakeup/batch
```

### Home Automation Integration

Example for Home Assistant:

```yaml
rest_command:
  wake_computer:
    url: http://wol-proxy:5000/wakeup/D8:43:AE:6F:42:63
    method: GET
```

### Script for Selective Wake-up

```bash
#!/bin/bash
# Wake specific classrooms

CLASSROOMS=("D8:43:AE:6F:42:63" "D8:43:AE:6F:42:65" "D843AE746D49")

for mac in "${CLASSROOMS[@]}"; do
  echo "Waking $mac..."
  curl -s "http://localhost:5000/wakeup/$mac"
done
```

---

## Version Information

- API Version: 1.0
- Python: 3.x
- Flask: Latest
- wakeonlan: System package

---

## Support

For issues and questions:
- Check the main README.md for troubleshooting
- Review Docker logs: `docker logs wol-proxy`
- Verify network configuration
