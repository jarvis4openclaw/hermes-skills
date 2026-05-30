---
name: maintain-personal-web-app
description: Maintain personal web applications with reliable timestamp updates
category: productivity
---

# Maintain Personal Web Application with Timestamp Updates

## When to Use This Skill
When you have a simple personal web application that:
- Displays data that updates periodically (e.g., social media feeds, logs, metrics)
- Shows a "last updated" timestamp that should reflect when data was last refreshed
- Uses scripts to fetch data and generate HTML
- Needs reliable timestamp updates to show current status

## Problem
The "last updated" timestamp on a web page doesn't reflect when data was actually last refreshed, causing confusion about content freshness.

## Solution
Ensure timestamp files are updated *before* HTML generation in your update workflow.

## Steps
1. **Identify the workflow**: Locate your data fetch/update script and HTML generation script
2. **Find the timestamp file**: Look for a file that stores the last update time (often .last_updated, timestamp, etc.)
3. **Modify update script**: Add a step to write current timestamp to the timestamp file *before* calling HTML generation
4. **Verify HTML generation**: Ensure your HTML generation script reads from the timestamp file
5. **Test the fix**: Run the update script and verify the timestamp appears correctly on the webpage
6. **Document the process**: Create/maintain documentation explaining the update workflow
7. **Clean up**: Remove or archive unused files to reduce clutter
8. **Version control**: Set up Git repository with appropriate .gitignore rules

## Example Fix (Bash)
```bash
# In your update script (e.g., update.sh):
#!/bin/bash
# Fetch new data
fetch_data_command
# UPDATE TIMESTAMP BEFORE HTML GENERATION
date +"%Y-%m-%d %H:%M:%S %Z" > /path/to/your/site/.last_updated
# Generate HTML with new data and timestamp
generate_html_script
# Optional: restart web server if needed
restart_web_server_command
```

## Verification
- Check that timestamp file updates after each run
- Verify webpage shows updated timestamp
- Confirm data freshness matches timestamp
- Test multiple update cycles

## Maintenance
- Schedule regular updates via cron or similar
- Monitor for failures in timestamp updates
- Keep documentation current with any workflow changes
- Periodically clean up unused files

## Troubleshooting
- If timestamp doesn't update: check script execution order and file permissions
- If webpage shows old timestamp: verify HTML generation reads correct file
- If data doesn't match timestamp: check that data fetch and timestamp update are in same script execution