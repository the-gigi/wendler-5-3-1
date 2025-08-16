#!/bin/bash

# Database backup script for Wendler 5-3-1
# Daily backups to GCS, keeping 3 most recent

set -e

DB_PATH="~/data/wendler.db"
BUCKET_NAME="wendler-5-3-1-backups"  # Change this to your preferred bucket name
PROJECT_ID="playground-161404"

echo "$(date): Starting database backup..."

# Check if database exists and is not empty
if [ ! -f ~/data/wendler.db ]; then
    echo "$(date): Database file not found at ~/data/wendler.db - skipping backup"
    exit 0
fi

if [ ! -s ~/data/wendler.db ]; then
    echo "$(date): Database file is empty - skipping backup"
    exit 0
fi

# Create timestamped backup filename
TIMESTAMP=$(date +%Y%m%d)
BACKUP_FILE="wendler_backup_$TIMESTAMP.db"

# Create GCS bucket if it doesn't exist (idempotent)
if ! gsutil ls gs://$BUCKET_NAME >/dev/null 2>&1; then
    echo "$(date): Creating new bucket: $BUCKET_NAME"
    gsutil mb -p $PROJECT_ID -c STANDARD -l us-west1 gs://$BUCKET_NAME
    
    # Set lifecycle rule to delete backups older than 3 days
    cat > /tmp/lifecycle.json << EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 3}
      }
    ]
  }
}
EOF
    gsutil lifecycle set /tmp/lifecycle.json gs://$BUCKET_NAME
    rm /tmp/lifecycle.json
    echo "$(date): Bucket created with 3-day lifecycle rule"
fi

# Upload backup to GCS (overwrites if same day)
echo "$(date): Uploading backup to Cloud Storage..."
gsutil cp ~/data/wendler.db gs://$BUCKET_NAME/$BACKUP_FILE

echo "$(date): Backup completed successfully!"
echo "$(date): Cloud backup: gs://$BUCKET_NAME/$BACKUP_FILE"