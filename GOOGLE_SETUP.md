# Google OAuth Setup Guide

To enable Google Sign-In for students, you need to set up Google OAuth credentials.

## Steps:

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/

2. **Create or Select a Project**
   - Create a new project or select an existing one

3. **Enable Google Identity Services**
   - Go to "APIs & Services" > "Library"
   - Search for "Google Identity" and enable it

4. **Create OAuth 2.0 Credentials**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client ID"
   - Choose "Web application"
   - Add your authorized origins:
     - `http://localhost:3000` (for development)
     - Your production domain (e.g., `https://yourdomain.com`)

5. **Set Environment Variable**
   - Create a `.env` file in the `socratic-frontend` directory
   - Add: `REACT_APP_GOOGLE_CLIENT_ID=your_client_id_here.apps.googleusercontent.com`

6. **Update the Client ID**
   - Replace `YOUR_GOOGLE_CLIENT_ID` in `StudentAuthPage.jsx` with your actual client ID
   - Or better yet, use the environment variable: `process.env.REACT_APP_GOOGLE_CLIENT_ID`

## Example .env file:
```
REACT_APP_GOOGLE_CLIENT_ID=123456789-abcdefghijklmnop.apps.googleusercontent.com
```

## Security Notes:
- Never commit your actual client ID to version control
- Use environment variables for different environments (dev, staging, prod)
- The client ID is safe to expose in frontend code (it's designed to be public) 