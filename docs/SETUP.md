# Detailed Setup Guide

## 1. Switch Instagram to Creator Account

1. Open Instagram app on your phone
2. Go to Profile > Menu (three lines) > Settings and privacy
3. Scroll to "Account type and tools"
4. Tap "Switch to professional account"
5. Select **Creator**
6. Choose a category (e.g., "Digital Creator")
7. Done! Your account is now API-ready.

## 2. Create Meta Developer App

1. Go to https://developers.facebook.com
2. Click "My Apps" > "Create App"
3. Select "Business" type
4. Enter app name (e.g., "Srija Social Assistant")
5. In your app dashboard, click "Add Product"
6. Find "Instagram" and click "Set Up"
7. Go to Instagram > Basic Display (or API Setup)
8. Add OAuth Redirect URI: `http://localhost:8600/api/auth/instagram/callback`
9. Note your **Instagram App ID** and **Instagram App Secret**

## 3. Set Up Google Drive for Image Hosting

Instagram API requires publicly accessible URLs for images. We use Google Drive as a temporary host.

### Create Google Cloud Service Account:
1. Go to https://console.cloud.google.com
2. Create a new project (or use existing)
3. Enable "Google Drive API" in APIs & Services
4. Go to IAM & Admin > Service Accounts > Create
5. Download the JSON key file
6. Save it somewhere safe (e.g., alongside the project)

### Create a Drive Folder:
1. Go to Google Drive
2. Create a new folder (e.g., "srija-temp-images")
3. Share the folder with the service account email (found in the JSON file, looks like `xxx@xxx.iam.gserviceaccount.com`)
4. Copy the folder ID from the URL: `drive.google.com/drive/folders/{THIS_IS_THE_ID}`

### Configure in App:
Enter the JSON file path and folder ID in Settings > Google Drive.

## 4. Get Anthropic API Key

1. Go to https://console.anthropic.com
2. Create an API key
3. Enter it in Settings > Anthropic API Key

## 5. First Run

1. Copy `.env.example` to `.env`
2. Run `python run.py` (or double-click `launch.bat`)
3. Go to Settings page:
   - Generate encryption key
   - Enter Anthropic API key
   - Enter Instagram App ID & Secret
   - Enter Google Drive credentials
   - Click "Connect Instagram" and authorize
4. Create your first post!

## Android App

### Build APK:
1. Install Android Studio
2. Open the `android/` folder as a project
3. Build > Build Bundle(s) / APK(s) > Build APK(s)
4. Find APK in `android/app/build/outputs/apk/debug/`

### Usage:
1. Run the Python backend on your PC
2. Find your PC's local IP: `ipconfig` (Windows) or `ifconfig` (Mac/Linux)
3. In the Android app, go to Menu > Server Settings
4. Enter: `http://YOUR_PC_IP:8600`
5. Make sure your phone is on the same WiFi network

### To make backend accessible from phone:
Change `HOST=127.0.0.1` to `HOST=0.0.0.0` in `.env` to allow external connections.
