#!/bin/bash
# Open Edit — Deploy to Aliyun Server
set -e

KEY="/Users/lisun/Desktop/Agent/_config/阿里云轻量服务器密钥.pem"
HOST="root@47.79.229.47"
REMOTE_DIR="/opt/open-edit"

echo "📦 Building deployment package..."

# Create deploy dir locally
DEPLOY_DIR="/tmp/open-edit-deploy"
rm -rf "$DEPLOY_DIR"
mkdir -p "$DEPLOY_DIR"

# Copy web app to root of deploy dir
cp -r /Users/lisun/Desktop/Agent/projects/视频制作/open-edit/web/* "$DEPLOY_DIR/"
cp -r /Users/lisun/Desktop/Agent/projects/视频制作/open-edit/taxonomy "$DEPLOY_DIR/"

# Create Dockerfile
cat > "$DEPLOY_DIR/Dockerfile" << 'DOCKERFILE'
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5555

CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5555", "--timeout", "120", "app:app"]
DOCKERFILE

# Clean up unnecessary files from deploy
rm -rf "$DEPLOY_DIR/__pycache__" 2>/dev/null || true
rm -rf "$DEPLOY_DIR/pipeline/__pycache__" 2>/dev/null || true
rm -rf "$DEPLOY_DIR/uploads" 2>/dev/null || true
mkdir -p "$DEPLOY_DIR/uploads"
touch "$DEPLOY_DIR/uploads/.gitkeep"

echo "🚀 Uploading to server..."
scp -i "$KEY" -r "$DEPLOY_DIR" "$HOST:/tmp/open-edit-pkg"

# Deploy on server
ssh -i "$KEY" "$HOST" << 'SSH_CMDS'
    set -e
    cd /tmp/open-edit-pkg

    # Check if ARK_API_KEY is set
    if [ -z "$ARK_API_KEY" ]; then
        echo "⚠️  ARK_API_KEY is not set! Vision analysis will not work."
        echo "   Set it with: export ARK_API_KEY=a67d5de9-aa45-423c-a326-c011d5692a4c"
    fi

    # Stop existing container
    docker stop open-edit 2>/dev/null || true
    docker rm open-edit 2>/dev/null || true

    # Build and run
    docker build -t open-edit:latest .
    docker run -d \
        --name open-edit \
        --restart unless-stopped \
        -p 5555:5555 \
        -e ARK_API_KEY="a67d5de9-aa45-423c-a326-c011d5692a4c" \
        -e PYTHONUNBUFFERED=1 \
        open-edit:latest

    echo "✅ Open Edit deployed!"
    echo "   http://47.79.229.47:5555"

    # Cleanup
    rm -rf /tmp/open-edit-pkg

    # Check logs
    sleep 2
    docker logs open-edit --tail 10
SSH_CMDS

echo "✅ Deployment complete!"
