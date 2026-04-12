# OAuth Provider Setup — Google & Microsoft

This is a **one-time setup** to enable "Sign in with Google" and "Sign in with Microsoft" on ClaudERP at `https://erp.tellefsen.org`. It must be done before JR's deployment of OAuth will work, because the providers will not redirect to URIs they have not been told about.

Both providers take about 10 minutes each. You need:

- A Google account (for Google Cloud Console)
- A Microsoft account (for Azure Portal)
- The ability to receive the generated client secrets and paste them into `/etc/claud-erp/.env` on the droplet

When you're done, you'll have four values to hand to JR:

```
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
MICROSOFT_CLIENT_ID=...
MICROSOFT_CLIENT_SECRET=...
```

---

## 1 — Google OAuth (10 minutes)

### 1.1 Create or select a project

1. Go to https://console.cloud.google.com/
2. In the top bar, click the project dropdown → **New project**
3. Name: `ClaudERP` → **Create**
4. Wait for the project to provision, then make sure it's selected in the top bar

### 1.2 Configure the OAuth consent screen

This is the "Sign in with Google — ClaudERP wants to access your email" screen users see the first time.

1. Left sidebar → **APIs & Services** → **OAuth consent screen**
2. User type: **External** → **Create**
3. Fill in the required fields:
   - **App name:** `ClaudERP`
   - **User support email:** your email
   - **App logo:** optional, skip for MVP
   - **App domain → Application home page:** `https://erp.tellefsen.org`
   - **Authorized domains:** add `tellefsen.org` (Google validates your redirect URIs against this)
   - **Developer contact information:** your email
4. **Save and Continue**
5. **Scopes** step: click **Add or remove scopes**, tick:
   - `.../auth/userinfo.email`
   - `.../auth/userinfo.profile`
   - `openid`
   Click **Update**, then **Save and Continue**.
6. **Test users** step: add yourself (and anyone else who will test before the app is published). Click **Save and Continue**.
7. **Summary** step: **Back to dashboard**.

**Publishing status:** the app will start in "Testing" mode, meaning only the test users listed in step 6 can sign in. For a real launch, click **Publish app** in the consent screen page (Google will require a privacy policy URL and may go through a verification review that can take days to weeks — not needed for your own testing).

### 1.3 Create OAuth credentials

1. Left sidebar → **APIs & Services** → **Credentials**
2. **+ Create Credentials** → **OAuth client ID**
3. **Application type:** `Web application`
4. **Name:** `ClaudERP Web`
5. **Authorized JavaScript origins:** add:
   ```
   https://erp.tellefsen.org
   ```
6. **Authorized redirect URIs:** add:
   ```
   https://erp.tellefsen.org/api/v1/auth/google/callback
   ```
7. **Create**
8. A modal pops up with your **Client ID** and **Client secret**. Copy them somewhere safe (you can also download a JSON file).
   - Format: `Client ID` ends in `.apps.googleusercontent.com`
   - Format: `Client secret` starts with `GOCSPX-`

These are the two values you need for `/etc/claud-erp/.env`:

```
GOOGLE_CLIENT_ID=xxxxxxxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxxxxxxx
```

---

## 2 — Microsoft OAuth (10 minutes)

### 2.1 Register an application

1. Go to https://portal.azure.com/
2. Top search bar → **Microsoft Entra ID** (formerly "Azure Active Directory") → click it
3. Left sidebar → **App registrations** → **+ New registration**
4. Fill in:
   - **Name:** `ClaudERP`
   - **Supported account types:** choose one of:
     - **Accounts in any organizational directory and personal Microsoft accounts** ← use this for public sign-up. Matches `MICROSOFT_TENANT=common` in the env file.
     - **Accounts in this organizational directory only** ← use this if ClaudERP is only for your own company's employees. In this case, set `MICROSOFT_TENANT` to your tenant GUID (findable on the Entra ID overview page).
   - **Redirect URI:** `Web` → `https://erp.tellefsen.org/api/v1/auth/microsoft/callback`
5. **Register**

You're now on the **Overview** page of your new app. Copy the **Application (client) ID** from the top — that's your `MICROSOFT_CLIENT_ID`.

### 2.2 Create a client secret

1. Left sidebar (within your app) → **Certificates & secrets**
2. **Client secrets** tab → **+ New client secret**
3. **Description:** `ClaudERP prod`
4. **Expires:** choose `24 months` (you'll need to rotate it before this date)
5. **Add**
6. A new row appears. Immediately copy the **Value** column (NOT the "Secret ID" column — the Value is what you need, and it's only shown once).

That's your `MICROSOFT_CLIENT_SECRET`.

### 2.3 Configure API permissions

This is what tells Microsoft what data ClaudERP is allowed to read from the signed-in user's profile.

1. Left sidebar → **API permissions**
2. You should see `User.Read` already listed under Microsoft Graph. If not: **+ Add a permission** → **Microsoft Graph** → **Delegated permissions** → tick `User.Read`, `email`, `openid`, `profile` → **Add permissions**
3. Click **Grant admin consent for \<your directory\>** (blue button at the top of the permissions table). Confirm.

If you skip the admin consent step, users will be prompted to consent on their first sign-in, which works but looks less polished.

### 2.4 (Optional) Enable public client flows

Not needed for this app — we use the standard Web app flow. Skip this page.

### 2.5 The values you need

From the Overview page:
- **Application (client) ID** → `MICROSOFT_CLIENT_ID`

From the Certificates & secrets page:
- **Client secret Value** (copied at creation time) → `MICROSOFT_CLIENT_SECRET`

Tenant setting:
- If you chose "any organizational directory and personal Microsoft accounts" in step 2.1 → `MICROSOFT_TENANT=common`
- If you chose "this organizational directory only" → `MICROSOFT_TENANT=<your-tenant-GUID>`

---

## 3 — Add to the droplet and restart the API

SSH into the droplet and add the four values to `/etc/claud-erp/.env`. These are the only env vars you need to add — the OAuth code path is already deployed, it just needs credentials to activate.

```bash
ssh root@<droplet> "cat >> /etc/claud-erp/.env <<'EOF'

# OAuth providers (added <date>)
GOOGLE_CLIENT_ID=xxxxxxxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxxxxxxx
MICROSOFT_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
MICROSOFT_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
MICROSOFT_TENANT=common
OAUTH_REDIRECT_BASE_URL=https://erp.tellefsen.org
FRONTEND_URL=https://erp.tellefsen.org
OAUTH_STATE_SECRET=$(openssl rand -hex 32)
EOF"
```

Then restart just the API container so it re-reads the env file. You do NOT need to rebuild any images:

```bash
ssh root@<droplet> "cd /opt/claud-erp && \
  docker compose -f docker-compose.prod.yml restart api"
```

## 4 — Verify

```bash
curl -fsS https://erp.tellefsen.org/api/v1/auth/providers | jq .
# Expected: {"google": true, "microsoft": true}
```

Then open `https://erp.tellefsen.org/login` in a private browser window. You should see the two social buttons appear above the email/password form. Click **Continue with Google** — you should be redirected to `accounts.google.com`, then back to ClaudERP, and finally land on `/dashboard` logged in as a new user with a personal "Workspace" agency auto-created for you.

## 5 — Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Buttons don't appear on the login page | `GOOGLE_CLIENT_ID` or `MICROSOFT_CLIENT_ID` is empty, OR the API container wasn't restarted | Check `/etc/claud-erp/.env`, then `docker compose restart api` |
| "Error 400: redirect_uri_mismatch" from Google | The redirect URI registered in Google Cloud Console doesn't exactly match | Go to Credentials → edit your OAuth client → confirm it's exactly `https://erp.tellefsen.org/api/v1/auth/google/callback` (no trailing slash, no `http://`) |
| "AADSTS50011: The reply URL specified in the request does not match" from Microsoft | Same issue for Azure | Go to your app registration → Authentication → confirm the Web redirect URI is exact |
| "AADSTS700054: response_type 'id_token' is not enabled for the application" | You ticked the wrong flow when registering | Go to Authentication → under "Implicit grant and hybrid flows", leave both checkboxes unticked (we use the standard authorization code flow) |
| "Error 403: access_denied" from Google | Your Google Workspace admin has restricted third-party apps, OR the app is in Testing mode and you're not a listed test user | Add yourself as a test user in the OAuth consent screen, OR ask the admin to allow the app |
| Login succeeds but `/dashboard` shows 0 clients | The OAuth user got auto-assigned a new empty agency — they're not in the seeded ClaudERP demo agency | Either seed more data for the new user's agency, or share the `demo@claud-erp.com` / `demo1234` credentials for testing |
| `"provider google is not configured on this server"` error on button click | The API startup didn't pick up the new env vars | `docker compose restart api` — env vars are loaded once at container start |

## 6 — Secret rotation

Both client secrets expire. Calendar reminders:

- **Google:** secrets don't expire, but rotate annually as good practice
- **Microsoft:** expires at the date you chose in step 2.2 (24 months by default). You'll get an email from Microsoft a few weeks before expiry. Generate a new secret, update `/etc/claud-erp/.env`, restart the API.

If a secret leaks, revoke it immediately in the respective console and generate a new one — the old one is burned.
