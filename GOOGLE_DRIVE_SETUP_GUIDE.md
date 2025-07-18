# Google Drive Integration Setup Guide

## 🎯 **Overview**
This guide walks you through setting up Google Drive integration for the DNC Automator. The system will automatically download DNC files from a shared Google Drive folder and process them.

---

## 📋 **Prerequisites**
- Google account with access to Google Drive
- Admin access to create service accounts (or personal account for OAuth)
- Google Drive folder containing DNC files

---

## 🔧 **Option 1: Service Account Setup (Recommended for Production)**

### **Step 1: Create Google Cloud Project**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Create Project" or select existing project
3. Note your **Project ID** (you'll need this)

### **Step 2: Enable Google Drive API**
1. In Google Cloud Console, go to **APIs & Services** > **Library**
2. Search for "Google Drive API"
3. Click on "Google Drive API" and click **Enable**

### **Step 3: Create Service Account**
1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **Service Account**
3. Fill in details:
   - **Service account name**: `dnc-automator-service`
   - **Service account ID**: `dnc-automator-service`
   - **Description**: `Service account for DNC Automator Google Drive access`
4. Click **Create and Continue**
5. Skip granting access to project (click **Continue**)
6. Skip granting users access (click **Done**)

### **Step 4: Create Service Account Key**
1. In **Credentials** page, click on your service account
2. Go to **Keys** tab
3. Click **Add Key** > **Create New Key**
4. Select **JSON** format
5. Click **Create**
6. **IMPORTANT**: Save the downloaded JSON file as `config/google_credentials.json` in your project

### **Step 5: Share Google Drive Folder**
1. Create a folder in Google Drive for DNC files
2. Right-click the folder > **Share**
3. Add the service account email (found in the JSON file, looks like `dnc-automator-service@your-project.iam.gserviceaccount.com`)
4. Give it **Editor** permissions
5. **Copy the folder ID** from the URL (e.g., `https://drive.google.com/drive/folders/1ABC123DEF456` → ID is `1ABC123DEF456`)

---

## 🔧 **Option 2: OAuth Setup (Recommended for Development)**

### **Step 1: Create OAuth Credentials**
1. In Google Cloud Console, go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth client ID**
3. If prompted, configure OAuth consent screen:
   - **Application type**: Desktop application
   - **Name**: `DNC Automator`
   - **Authorized redirect URIs**: `http://localhost:8080/callback`
4. Select **Application type**: **Desktop application**
5. **Name**: `DNC Automator Desktop`
6. Click **Create**
7. Download the JSON file and save as `config/google_credentials.json`

### **Step 2: Get Drive Folder ID**
1. Create a folder in Google Drive for DNC files
2. Open the folder in Google Drive
3. Copy the folder ID from the URL (e.g., `https://drive.google.com/drive/folders/1ABC123DEF456` → ID is `1ABC123DEF456`)

---

## 📁 **File Structure Setup**

### **Create Required Directories**
```bash
mkdir -p config
mkdir -p data/downloads
mkdir -p data/processed
mkdir -p data/archived
```

### **Environment Variables**
Add these to your `.env` file:
```bash
# Google Drive Configuration
GOOGLE_DRIVE_FOLDER_ID=1ABC123DEF456  # Replace with your folder ID
GOOGLE_DRIVE_CREDENTIALS_PATH=config/google_credentials.json
GOOGLE_DRIVE_TOKEN_PATH=config/google_token.json
```

---

## 📊 **Test DNC Files Setup**

### **Create Test Files in Google Drive**
Upload these test files to your Google Drive folder:

**File 1: `client_a_16-07-25.csv`**
```csv
company_name,domain
Microsoft Corporation,microsoft.com
Apple Inc,apple.com
Google LLC,google.com
Amazon.com Inc,amazon.com
Tesla Inc,tesla.com
```

**File 2: `client_b_16-07-25.csv`**
```csv
company_name,domain
Salesforce.com Inc,salesforce.com
Netflix Inc,netflix.com
Uber Technologies Inc,uber.com
Airbnb Inc,airbnb.com
Spotify Technology SA,spotify.com
```

**File 3: `acme_corp_16-07-25.csv`**
```csv
company_name,domain
Meta Platforms Inc,meta.com
Twitter Inc,twitter.com
LinkedIn Corporation,linkedin.com
Adobe Inc,adobe.com
Oracle Corporation,oracle.com
```

---

## 🔐 **Security Best Practices**

### **Service Account Security**
1. **Never commit** `google_credentials.json` to version control
2. Add `config/google_credentials.json` to `.gitignore`
3. Add `config/google_token.json` to `.gitignore`
4. Store credentials as GitHub secrets for production:
   - `GOOGLE_CREDENTIALS_JSON`: Content of the JSON file
   - `GOOGLE_DRIVE_FOLDER_ID`: Your folder ID

### **Folder Permissions**
1. Only share with necessary service accounts
2. Use **Editor** permissions (not **Owner**)
3. Regularly review folder access permissions
4. Consider using organization-managed shared drives

---

## 🧪 **Testing the Setup**

### **Test 1: Authentication**
```bash
# Test authentication
uv run python -c "
from src.utils.google_drive_client import GoogleDriveClient
import os

try:
    client = GoogleDriveClient(
        credentials_path='config/google_credentials.json',
        token_path='config/google_token.json'
    )
    print('✅ Google Drive authentication successful')
except Exception as e:
    print(f'❌ Authentication failed: {e}')
"
```

### **Test 2: Folder Access**
```bash
# Test folder access
uv run python -c "
from src.utils.google_drive_client import GoogleDriveClient
import os

client = GoogleDriveClient(
    credentials_path='config/google_credentials.json',
    token_path='config/google_token.json'
)

folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
if folder_id:
    files = client.list_files_in_folder(folder_id)
    print(f'✅ Found {len(files)} files in folder:')
    for file in files:
        print(f'  - {file[\"name\"]} ({file[\"id\"]})')
else:
    print('❌ GOOGLE_DRIVE_FOLDER_ID not set')
"
```

### **Test 3: File Download**
```bash
# Test file download
uv run python -c "
from src.utils.google_drive_client import GoogleDriveClient
import os

client = GoogleDriveClient(
    credentials_path='config/google_credentials.json',
    token_path='config/google_token.json'
)

folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
if folder_id:
    downloaded = client.download_dnc_files(folder_id, 'data/downloads/')
    print(f'✅ Downloaded {len(downloaded)} files:')
    for file_path in downloaded:
        print(f'  - {file_path}')
else:
    print('❌ GOOGLE_DRIVE_FOLDER_ID not set')
"
```

---

## 🔍 **Troubleshooting**

### **Common Issues**

#### **1. Authentication Errors**
```
Error: google.auth.exceptions.DefaultCredentialsError
```
**Solution**: 
- Verify `google_credentials.json` is in the correct location
- Check file permissions (should be readable by your user)
- Ensure the service account has been created correctly

#### **2. Folder Access Denied**
```
Error: The user does not have sufficient permissions for folder
```
**Solution**:
- Verify the service account email is shared with the folder
- Check that permissions are set to **Editor** or higher
- Ensure the folder ID is correct

#### **3. API Not Enabled**
```
Error: Google Drive API has not been used in project
```
**Solution**:
- Go to Google Cloud Console > APIs & Services > Library
- Search for "Google Drive API" and enable it
- Wait 5-10 minutes for changes to propagate

#### **4. File Not Found**
```
Error: File not found or naming pattern incorrect
```
**Solution**:
- Verify files follow the pattern: `client_name_16-07-25.csv`
- Check that files are in the correct folder
- Ensure files are not in subfolders

### **Debug Mode**
Add this to your environment for detailed logging:
```bash
export GOOGLE_DRIVE_DEBUG=true
```

---

## 📋 **GitHub Actions Setup**

### **Add GitHub Secrets**
1. Go to your GitHub repository
2. Navigate to **Settings** > **Secrets and variables** > **Actions**
3. Add these secrets:
   - `GOOGLE_CREDENTIALS_JSON`: Content of your `google_credentials.json` file
   - `GOOGLE_DRIVE_FOLDER_ID`: Your Google Drive folder ID

### **Update GitHub Actions Workflow**
The workflow will automatically:
1. Download DNC files from Google Drive
2. Extract client names from filenames
3. Process each client's DNC list
4. Update HubSpot with dynamic property names
5. Archive processed files

---

## 🎯 **Next Steps**

Once Google Drive integration is working:

1. **Test with Multiple Clients**: Upload files for different clients
2. **Verify Dynamic Properties**: Ensure HubSpot properties are generated correctly
3. **Test Automation**: Run the complete workflow end-to-end
4. **Monitor Performance**: Check download speeds and processing times

---

## 📞 **Support**

If you encounter issues:
1. Check the troubleshooting section above
2. Review Google Cloud Console logs
3. Verify all environment variables are set
4. Test with a simple file first

**Important**: Keep your `google_credentials.json` file secure and never commit it to version control!