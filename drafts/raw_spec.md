# Feature Request: Google OAuth Integration

We need to add Google OAuth login to our internal Flask web application. Currently, users have to log in using legacy passwords, which are hard to manage and pose security risks.

## High-Level Requirements:
1. Replace password fields with a "Sign in with Google" button.
2. Store logged-in user profile data (email, name, profile picture URL) in our Spanner database.
3. Keep user sessions active for 7 days unless the user explicitly logs out.
4. Make sure there is a redirect fallback if the user is not found in our Spanner users table.
