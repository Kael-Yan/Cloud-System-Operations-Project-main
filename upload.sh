#!/bin/bash

# 設置錯誤時退出
set -e

# 更新系統
sudo yum update -y || { echo "系統更新失敗"; exit 1; }

# 啟動 Docker 服務
sudo systemctl enable docker || { echo "Docker 服務啟用失敗"; exit 1; }
sudo systemctl start docker || { echo "Docker 服務啟動失敗"; exit 1; }

# 等待 Docker 服務完全啟動
for i in {1..10}; do
    if systemctl is-active --quiet docker; then
        break
    fi
    sleep 1
    if [ $i -eq 10 ]; then
        echo "Docker 服務啟動超時"
        exit 1
    fi
done

# 創建上傳目錄並設置權限
sudo mkdir -p /var/www/hkgolden/uploads
sudo chown -R ec2-user:ec2-user /var/www/hkgolden
sudo chmod -R 777 /var/www/hkgolden

# 創建環境變量文件
cat << EOF > /home/ec2-user/.env
FLASK_APP=app/__init__.py
FLASK_ENV=production
FLASK_DEBUG=0
ADMINS=tszchen8@gmail.com
SECRET_KEY=e304d75e32b3900541368dd13fdd1029d72d7a12c280d3477c072ea7e75a5ca1
DATABASE_URL=postgresql://postgres:a00NY4B2ZCOt1X|eZYhkZ:M5C<QT@database-project-instance-1.cgungkabvm7q.us-east-1.rds.amazonaws.com:5432/postgres
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=tszchen8@gmail.com
MAIL_PASSWORD=hdjzrqmyvmnmtrok
UPLOAD_FOLDER=/workspace/app/static/uploads
EOF

# 設置環境變量文件權限
sudo chmod 600 /home/ec2-user/.env || { echo "設置文件權限失敗"; exit 1; }

# 創建 Docker 網絡
sudo docker network create hkgolden-network || true

# 如果容器已存在，先停止並刪除
sudo docker stop hkgolden-app || true
sudo docker rm hkgolden-app || true

# 創建並啟動容器
sudo docker run -d \
  --name hkgolden-app \
  --restart unless-stopped \
  -p 5000:5000 \
  --env-file /home/ec2-user/.env \
  --network hkgolden-network \
  -v /var/www/hkgolden/uploads:/workspace/app/static/uploads \
  hkgolden:latest 

# 檢查容器狀態
sleep 5
if ! sudo docker ps | grep -q hkgolden-app; then
    echo "容器未運行"
    sudo docker logs hkgolden-app
    exit 1
fi

echo "部署完成"

##############################
# 更新系統
sudo yum update -y

# 安裝 Docker
sudo yum install docker -y
sudo service docker start
sudo systemctl enable docker

# 將當前用戶添加到 docker 組
sudo usermod -a -G docker ec2-user
docker save -o hkgolden.tar hkgolden:latest
scp -i "labsuser (5).pem" hkgolden.tar ec2-user@3.87.87.151:/home/ec2-user/
sudo docker load -i hkgolden-app.tar

docker log hkgolden_app
postgresql://postgres:a00NY4B2ZCOt1X|eZYhkZ:M5C<QT@database-project.cluster-cgungkabvm7q.us-east-1.rds.amazonaws.com:5432/database-project
postgresql://postgres:a00NY4B2ZCOt1X|eZYhkZ:M5C<QT@database-project-instance-1.cgungkabvm7q.us-east-1.rds.amazonaws.com:5432/postgres
