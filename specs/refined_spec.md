# Compiled Product Specification & Execution Plan
*Generated automatically by Spec Deliberator Agent*

---

## Part 1: User Story & Acceptance Criteria
# Google OAuth Integration for Internal Flask Application

**Issue Type:** User Story
**Status:** Ready for Development
**Priority:** High

## 1. Description
**As an** internal user,
**I want to** log in to the Flask web application using my Google account,
**So that** I can securely access the application without managing legacy passwords, and benefit from a streamlined login experience.

## 2. Business Context & Background
This feature is crucial for enhancing the security posture and improving the usability of our internal Flask web application. By replacing traditional password-based authentication with Google OAuth, we eliminate the need for users to manage yet another set of credentials, thereby reducing security risks associated with weak or reused passwords. It also streamlines the login process, aligning with modern enterprise security practices and improving overall user experience.

## 3. Acceptance Criteria

*   **AC1: Successful Google Login for Authenticated Users**
    *   **Given** an internal user navigates to the Flask application's login page
    *   **When** the user clicks "Sign in with Google" and successfully authenticates with their corporate Google account
    *   **Then** the user is successfully logged in to the Flask application, and their session remains active for 7 days.
*   **AC2: New User Profile Data Storage on First Login**
    *   **Given** a user successfully authenticates with Google OAuth for the first time
    *   **When** the system receives their profile data (email, full name, profile picture URL) from Google
    *   **Then** the user's email, full name, and profile picture URL are securely stored in the Spanner database, and the user is logged in.
*   **AC3: Redirect Fallback for Unauthorized Users**
    *   **Given** a user attempts to log in via Google OAuth
    *   **When** the user's Google account is authenticated, but their email is not found in the Spanner users table or is not authorized to access the application
    *   **Then** the system redirects the user to a predefined "Access Denied" page or a page prompting them to contact an administrator.
*   **AC4: User Initiated Logout**
    *   **Given** a user is actively logged into the Flask application via Google OAuth
    *   **When** the user explicitly clicks the "Logout" button/link
    *   **Then** the user's session in the Flask application is immediately terminated, and they are redirected to the login page.

## 4. Technical Constraints & Out of Scope
*   **Constraints:**
    *   Must utilize Google OAuth 2.0 for authentication.
    *   Session management must securely maintain user sessions for 7 days or until explicit logout.
    *   User profile data (email, name, profile picture URL) must be stored exclusively in the existing Spanner database schema.
    *   The implementation must comply with our internal security policies and data privacy regulations.
    *   Supported browsers: Latest stable versions of Chrome, Firefox, Safari, and Edge.
*   **Out of Scope:**
    *   Integration with any other identity providers (e.g., GitHub, Azure AD).
    *   Complex role-based access control (RBAC) or authorization features beyond basic user authentication.
    *   Self-service user provisioning or account linking functionality.
    *   User administration features (e.g., blocking users, changing roles) are outside the scope of this story.

## 5. Design & UI/UX (If applicable)
*   The login page will feature a prominent "Sign in with Google" button, replacing the existing username/password fields.
*   Consideration for a loading state or spinner during the OAuth redirect process.

## 6. Definition of Done (DoD)
*   [x] Code is peer-reviewed and approved.
*   [x] Unit and integration tests are written and passing for all authentication flows.
*   [x] All Acceptance Criteria are successfully verified through testing.
*   [x] Relevant documentation (e.g., README for setup, developer notes) is updated.
*   [x] Feature is deployable without breaking existing functionality and passes security audits.

---

## Part 2: RFC Technical Design
# RFC: Google OAuth Integration for Internal Flask Application

## 1. Context and Scope
*   **Background:** Internal Flask application currently uses password-based authentication. This project aims to replace it with Google OAuth 2.0 for enhanced security, improved user experience, and alignment with modern enterprise security practices.
*   **Goals:**
    *   Enable users to log in using their corporate Google accounts.
    *   Securely store new user profile data (email, full name, profile picture URL) in Spanner upon first successful Google authentication.
    *   Maintain active user sessions for 7 days or until explicit logout.
    *   Redirect unauthorized users to an "Access Denied" page.
    *   Implement a "Sign in with Google" button on the login page and a "Logout" functionality.
*   **Non-Goals:**
    *   Integration with other identity providers.
    *   Complex role-based access control beyond basic authentication.
    *   Self-service user provisioning or account linking.
    *   User administration features.

## 2. Proposed Architecture
*   **High-Level Design:** The Flask application will integrate directly with Google's OAuth 2.0 endpoint for authentication. User profile information will be retrieved from Google and stored in an existing Spanner database. Session management will be handled by the Flask application, maintaining secure sessions for 7 days.
*   **Architecture Diagram:**
```mermaid
---
title: Google OAuth Integration Flow
---
graph LR
    User[Internal User] -- 1. Access Flask App Login --> FlaskApp[Flask Application]
    FlaskApp -- 2. "Sign in with Google" Click --> Browser[User's Browser]
    Browser -- 3. Redirect to Google Auth --> GoogleAuth[Google OAuth 2.0]
    GoogleAuth -- 4. User Authenticates with Corporate Google Account --> GoogleAuth
    GoogleAuth -- 5. Redirect with Authorization Code --> Browser
    Browser -- 6. Send Authorization Code --> FlaskApp
    FlaskApp -- 7. Exchange Code for Tokens --> GoogleAuth
    GoogleAuth -- 8. Return Access Token & User Info --> FlaskApp
    FlaskApp -- 9. Check User in Spanner DB, Create if New --> SpannerDB[Spanner Database]
    SpannerDB -- 10. Store/Retrieve User Profile --> FlaskApp
    FlaskApp -- 11. Create Session & Redirect to Dashboard --> Browser
    Browser -- 12. Logged In Session (7 days) --> FlaskApp
    FlaskApp -- 13. "Logout" Click --> Browser
    Browser -- 14. Terminate Session --> FlaskApp
    FlaskApp -- 15. Redirect to Login Page --> Browser

    subgraph Authentication
        GoogleAuth
    end

    subgraph Application
        FlaskApp
        SpannerDB
    end

    style User fill:#f9f,stroke:#333,stroke-width:2px
    style Browser fill:#ADD8E6,stroke:#333,stroke-width:2px
    style FlaskApp fill:#DAF7A6,stroke:#333,stroke-width:2px
    style GoogleAuth fill:#FFFACD,stroke:#333,stroke-width:2px
    style SpannerDB fill:#D8BFD8,stroke:#333,stroke-width:2px
```

## 3. Detailed Implementation Strategy

*   **Data Layer / Persistence:**
    *   **Schema Modification (Spanner):**
        *   Modify the `users` table in Spanner to include `google_profile_picture_url` (VARCHAR(MAX) or appropriate length).
        *   Ensure `email` and `full_name` fields exist and are of appropriate types (e.g., `email` as VARCHAR(255), `full_name` as VARCHAR(255)).
        *   Consider adding a `last_login_at` (TIMESTAMP) field for auditing and session management purposes.
        *   **File:** `db/spanner_schema.sql` (or similar schema definition file)
    *   **ORM/Data Access Layer:**
        *   Update existing user model/ORM to handle new `google_profile_picture_url` field.
        *   Implement methods to:
            *   `find_user_by_email(email)`: Check if a user exists.
            *   `create_user(email, full_name, google_profile_picture_url)`: Create a new user entry.
            *   `update_user_last_login(email)`: Update last login timestamp.
        *   **Files:** `app/models/user.py`, `app/database/spanner_connector.py` (or similar data access modules)

*   **Core Logic / Services:**
    *   **OAuth Configuration:**
        *   Store Google OAuth client ID and client secret securely (e.g., environment variables, Key Management Service).
        *   Configure authorized redirect URIs in the Google API Console.
    *   **Flask Application Initialization:**
        *   Integrate a Flask-compatible OAuth client library (e.g., `Authlib` which supports Flask). This will simplify OAuth 2.0 flow management.
        *   Initialize the OAuth client with Google credentials.
        *   **File:** `app/__init__.py` or `config.py`
    *   **Authentication Flow (Login):**
        *   **`/login` route:**
            *   Modify this route to present the "Sign in with Google" button.
            *   On button click, initiate the Google OAuth flow, redirecting the user to Google's authorization endpoint with necessary scopes (e.g., `profile`, `email`) and a `state` parameter for CSRF protection.
        *   **`/oauth/callback` route:**
            *   This route will handle the redirect from Google.
            *   Verify the `state` parameter to prevent CSRF.
            *   Exchange the authorization code for an access token from Google.
            *   Use the access token to fetch user profile information (email, full name, profile picture URL) from Google's UserInfo endpoint.
            *   **User Authorization:**
                *   Check if the fetched email exists in the Spanner `users` table using `find_user_by_email`.
                *   If the user does not exist:
                    *   Create a new user entry in Spanner using `create_user`. (AC2)
                *   If the user exists but is not authorized (e.g., an internal check, though the story implies simply checking if they exist in Spanner), or if the email domain is not allowed:
                    *   Redirect to `/access-denied`. (AC3)
                *   If the user is successfully authenticated and authorized:
                    *   Update `last_login_at` using `update_user_last_login`.
                    *   Create a secure Flask session for the user, storing necessary user ID/email. (AC1)
                    *   Set session expiry for 7 days.
                    *   Redirect to the application dashboard/home page.
        *   **`@login_required` decorator/middleware:** Update or create a decorator to protect application routes, checking for an active session.
        *   **File:** `app/routes/auth.py`, `app/services/user_service.py`
    *   **Logout Functionality:**
        *   **`/logout` route:**
            *   Clear the user's Flask session. (AC4)
            *   Redirect the user to the `/login` page.
        *   **File:** `app/routes/auth.py`
    *   **Error Handling:** Implement robust error handling for OAuth failures, network issues, and unauthorized access.
    *   **File:** `app/errors.py` (or similar)
*   **API / Interfaces:**
    *   **Frontend Changes:**
        *   Update `login.html` template to display a "Sign in with Google" button and remove legacy username/password fields.
        *   Implement client-side redirect logic for the Google OAuth flow if needed, or rely on server-side redirects.
        *   Add a "Logout" link/button in the UI for logged-in users.
        *   **File:** `app/templates/login.html`, `app/templates/base.html` (for logout button)
    *   **New Endpoints:**
        *   `GET /login`: Displays the login page with Google button.
        *   `GET /oauth/callback`: Handles the OAuth redirect from Google.
        *   `GET /logout`: Terminates the user session.
        *   `GET /access-denied`: Page for unauthorized users.

## 4. Cross-Cutting Concerns

*   **Security & Auth:**
    *   **Client Secret Management:** Google OAuth client secret must be stored securely (e.g., environment variables, secret manager) and never hardcoded or committed to source control.
    *   **CSRF Protection:** Utilize the `state` parameter during the OAuth flow to prevent Cross-Site Request Forgery attacks.
    *   **Session Security:** Implement secure session management (e.g., using Flask's built-in session management with a strong secret key, secure cookies, HTTPOnly flag).
    *   **Token Validation:** Ensure proper validation of ID tokens (if used) and access tokens received from Google, checking issuer, audience, and expiration.
    *   **Access Control:** The initial check will be if the user exists in Spanner. Further authorization beyond basic authentication is out of scope.
    *   **Data Privacy:** Ensure only necessary user profile data is requested (scopes) and stored in Spanner, adhering to internal policies.
*   **Performance & Scalability:**
    *   The OAuth flow involves redirects to Google, which are outside the direct control of the application. The Flask application's direct involvement is minimal per request (handshakes, DB lookups).
    *   Spanner is highly scalable, so storing user profiles will not be a bottleneck.
    *   Session management should use an efficient backend (e.g., signed cookies, or a fast key-value store if sessions grow complex, though for this scope, Flask's default should suffice).
*   **Observability:**
    *   **Logging:** Implement comprehensive logging for key authentication events:
        *   OAuth flow initiation and callbacks.
        *   Successful user login and logout.
        *   New user creation in Spanner.
        *   Unauthorized access attempts or redirects to `/access-denied`.
        *   Errors during token exchange or profile fetching.
    *   **Metrics:** Consider basic metrics for successful logins, failed logins, and new user registrations per day.
    *   **Tracing:** Implement basic tracing if a distributed tracing system is already in place to track the OAuth request flow through the application.

## 5. Dependency Analysis & Ripple Effects

*   **Upstream/Downstream Impacts:**
    *   **Existing Login Page:** The current username/password login page (`/login`) will be replaced or heavily modified.
    *   **User Model:** The existing `User` model (if any) will need to be updated to accommodate `google_profile_picture_url`.
    *   **Authentication Middleware/Decorators:** Any existing `@login_required` or similar authentication checks will need to be adapted to rely on the new session management.
*   **Backward Compatibility:**
    *   The user story implies a complete replacement of the login mechanism. Therefore, backward compatibility with the old password-based login is *not* a goal and the old system will be deprecated/removed. During a transition phase, both could coexist, but this is outside the current scope.
    *   Existing user data (if any, besides email/name) not related to Google OAuth will remain unaffected in Spanner.

## 6. Architecture Decision Records (ADRs)

*   **ADR 1: Choice of Flask OAuth Client Library**
    *   **Context:** To simplify the implementation of Google OAuth 2.0 flow within the Flask application, a reliable and well-maintained OAuth client library is needed.
    *   **Decision:** Utilize `Authlib` (specifically `flask-oauthlib` or the Flask integration within `Authlib`) as the OAuth client library. It supports Flask, follows OAuth 2.0 specifications, and handles many complexities like token refreshing and state parameter generation.
    *   **Consequence:** Reduces development time and potential for errors compared to implementing the OAuth flow from scratch. Introduces a new external dependency.
*   **ADR 2: User Authorization Strategy**
    *   **Context:** The application needs to determine if a user who successfully authenticates with Google is authorized to access the Flask application.
    *   **Decision:** Authorization will be determined by the presence of the user's email in the existing Spanner `users` table. If the email is not found, the user is considered unauthorized and redirected to an access denied page. New users found via Google OAuth will be provisioned into the `users` table on first login.
    *   **Consequence:** This approach leverages the existing user data store for authorization. It aligns with the user story's focus on basic authentication and avoids implementing complex RBAC at this stage. It ensures only pre-approved (or newly provisioned) internal users can access the application.
*   **ADR 3: Session Management for 7-Day Duration**
    *   **Context:** The application requires user sessions to remain active for 7 days or until explicit logout.
    *   **Decision:** Flask's built-in session management will be used, configured with a `permanent_session_lifetime` of 7 days and secured using a strong `SECRET_KEY`. Session data will be encrypted and stored in secure, HTTPOnly cookies.
    *   **Consequence:** Simplifies session management without introducing additional external services. Relies on the security of Flask's session implementation and proper secret key management.

## 7. Testing Plan

*   **Unit Tests:**
    *   Tests for the Spanner data access layer (e.g., `find_user_by_email`, `create_user`, `update_user_last_login`).
    *   Tests for Flask routes: `/oauth/callback` (for code exchange, token validation, user creation/lookup, session creation, redirects), `/logout` (for session termination).
    *   Tests for the `login_required` decorator.
    *   Tests for session management logic (setting expiry, clearing).
*   **Integration Tests:**
    *   End-to-end flow: Simulate a user clicking "Sign in with Google," mocking Google's OAuth responses for authorization code, access token, and user info. Verify successful login, session creation, and redirection.
    *   First-time user login: Verify user creation in Spanner.
    *   Existing user login: Verify session renewal without creating a new user.
    *   Unauthorized user: Verify redirection to `/access-denied` for users not in Spanner.
    *   Logout flow: Verify session termination and redirection to `/login`.
    *   UI interaction tests (e.g., using Selenium/Playwright) for button clicks and redirects.

---

## Part 3: Task Breakdown & Execution Plan
No execution plan table was generated.
