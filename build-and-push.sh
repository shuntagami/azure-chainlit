#!/bin/bash
# ACRへのビルドとプッシュを行うスクリプト

# 変数設定
ACR_NAME="acrchainlitapp"
IMAGE_NAME="chainlit-app"
DOCKERFILE_PATH="./Dockerfile"  # Dockerfileのパス
BUILD_CONTEXT="."  # ビルドコンテキスト（通常はDockerfileがあるディレクトリ）

# 1. Azure CLIでログインする
echo "Azureにログインします..."
az login

# 2. ACRにログインする
echo "ACR ($ACR_NAME) にログインします..."
az acr login --name $ACR_NAME

# 3. Dockerイメージをビルドする
echo "Dockerイメージをビルドしています..."
# docker build --platform linux/amd64 -t ${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${TAG} -f $DOCKERFILE_PATH $BUILD_CONTEXT
docker build --platform linux/amd64 . -t chainlit-app:main
docker tag chainlit-app:main ${ACR_NAME}.azurecr.io/chainlit-app:main

# 4. イメージをACRにプッシュする
echo "イメージをACRにプッシュしています..."
docker push ${ACR_NAME}.azurecr.io/${IMAGE_NAME}:main

echo "完了しました！イメージが正常にACRにプッシュされました。"
echo "イメージURL: ${ACR_NAME}.azurecr.io/${IMAGE_NAME}:main"
