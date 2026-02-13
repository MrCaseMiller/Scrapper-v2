# Railway Deployment Guide - Real Polymarket Integration

**Complete step-by-step guide to deploy with REAL Polymarket data on the first try**

---

## 🎯 **Prerequisites**

Before starting, ensure you have:
- [ ] Railway account (https://railway.app)
- [ ] Supabase account (https://supabase.com)
- [ ] GitHub repository connected to Railway
- [ ] OpenSSL installed (for generating secrets)

---

## 📋 **Step 1: Set Up Supabase Database**

### 1.1 Create Supabase Project

1. Go to https://supabase.com/dashboard
2. Click "New project"
3. Choose organization and fill in:
   - **Project name**: `polymarket-sim` (or your choice)
   - **Database password**: Generate a strong password (save it!)
   - **Region**: Choose closest to your users
4. Click "Create new project" (takes ~2 minutes)

### 1.2 Gather Supabase Credentials

Once project is created, go to **Settings** → **API**:

```bash
# Copy these values (you'll need them later):
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # anon/public key
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # service_role key
```

Go to **Settings** → **Database** → **Connection string** → **URI**:

```bash
DATABASE_URL=postgresql+asyncpg://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres
```

**Important**: Replace `[YOUR-PASSWORD]` with your actual database password!

### 1.3 Configure Supabase Auth

Go to **Authentication** → **Providers**:
- [ ] Enable "Email" provider
- [ ] Confirm user email: **Enabled** (or disabled for testing)
- [ ] Save changes

Go to **Authentication** → **URL Configuration**:
- **Site URL**: `https://your-app.up.railway.app` (update after deployment)
- **Redirect URLs**: Add `https://your-app.up.railway.app/**`

---

## 🔐 **Step 2: Generate JWT Secret**

On your local machine, generate a secure JWT secret:

```bash
openssl rand -hex 32
```

**Save this output** - you'll use it as `JWT_SECRET_KEY`

Example output:
```
a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6
```

---

## 🚂 **Step 3: Deploy Backend to Railway**

### 3.1 Create Railway Project

1. Go to https://railway.app/dashboard
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your `Scrapper-v2` repository
5. Railway will detect the Dockerfile automatically

### 3.2 Configure Backend Service

#### Set Root Directory

1. Click on the service (should be named after your repo)
2. Go to **Settings** tab
3. Under "Build", set:
   - **Root Directory**: `polymarket-sim`
   - **Dockerfile Path**: `Dockerfile`

#### Configure Environment Variables

Go to **Variables** tab and add these variables:

**Required Variables:**
```bash
# Supabase (from Step 1.2)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Database (from Step 1.2)
DATABASE_URL=postgresql+asyncpg://postgres:YOUR-PASSWORD@db.xxxxx.supabase.co:5432/postgres

# JWT (from Step 2)
JWT_SECRET_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
ENVIRONMENT=production
DEFAULT_STARTING_BALANCE=1000.0
FRONTEND_URL=https://awake-mindfulness-staging.up.railway.app  # Update after frontend deploy
```

**Optional Variables (for LLM strategy):**
```bash
# Only if using LLM Directional strategy
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

#### Generate Public Domain

1. Go to **Settings** tab
2. Under "Networking" → **Public Networking**
3. Click "Generate Domain"
4. Copy the domain (e.g., `scrapper-v2-production.up.railway.app`)
5. **Save this URL** - you'll need it for frontend config

### 3.3 Deploy Backend

1. Click "Deploy" or wait for auto-deploy
2. Monitor **Deployments** tab for build progress
3. Wait for "Success" status (~3-5 minutes)

### 3.4 Verify Backend Health

Once deployed, test the backend:

```bash
# Replace with your actual backend URL
curl https://scrapper-v2-production.up.railway.app/health
```

**Expected response:**
```json
{"status":"healthy"}
```

If you get this, backend is working! ✅

---

## 🎨 **Step 4: Deploy Frontend to Railway**

### 4.1 Create Frontend Service

1. In same Railway project, click "+ New"
2. Select "GitHub Repo" again
3. Choose same `Scrapper-v2` repository
4. Railway creates a second service

### 4.2 Configure Frontend Service

#### Set Root Directory

1. Click on the new service
2. Rename it to "frontend" (Settings → General → Service Name)
3. Go to **Settings** tab
4. Under "Build", set:
   - **Root Directory**: `polymarket-sim/web/frontend`
   - **Build Command**: `npm install && npm run build`
   - **Start Command**: `npm start`

#### Configure Environment Variables

Go to **Variables** tab and add:

```bash
# Backend API URL (from Step 3.2 - your backend domain)
NEXT_PUBLIC_API_URL=https://scrapper-v2-production.up.railway.app

# Supabase (same as backend)
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Generate Public Domain

1. Go to **Settings** tab
2. Under "Networking" → **Public Networking**
3. Click "Generate Domain"
4. Copy the domain (e.g., `awake-mindfulness-staging.up.railway.app`)

### 4.3 Update Backend FRONTEND_URL

**Important:** Go back to backend service and update the FRONTEND_URL variable:

1. Click on backend service
2. Go to **Variables** tab
3. Update `FRONTEND_URL` with your frontend domain:
   ```bash
   FRONTEND_URL=https://awake-mindfulness-staging.up.railway.app
   ```
4. Backend will auto-redeploy

### 4.4 Deploy Frontend

1. Click "Deploy" or wait for auto-deploy
2. Monitor **Deployments** tab
3. Wait for "Success" status (~2-3 minutes)

---

## 🔄 **Step 5: Update Supabase URLs**

Go back to Supabase dashboard:

1. **Authentication** → **URL Configuration**
2. Update **Site URL**: `https://awake-mindfulness-staging.up.railway.app`
3. Update **Redirect URLs**: Add `https://awake-mindfulness-staging.up.railway.app/**`
4. Save changes

---

## ✅ **Step 6: Verify Deployment**

### 6.1 Test Frontend

Visit your frontend URL: `https://awake-mindfulness-staging.up.railway.app`

**Expected:**
- Page loads without errors
- Login/Signup buttons visible
- No console errors

### 6.2 Test Sign Up

1. Click "Sign Up"
2. Enter email and password
3. Check for confirmation email (if enabled)
4. Confirm account
5. Login should work

### 6.3 Test Real Polymarket Data

1. Login to dashboard
2. Look at "Markets" section
3. **You should see REAL Polymarket markets!**
   - Example: "Will Bitcoin hit $100k by 2026?"
   - Example: "Will Trump win 2024 election?"
4. Markets should have real questions, not fake mock data

### 6.4 Test Bot Functionality

1. Go to "Bot Controls" section
2. Select "Sum-to-One Arb" strategy
3. Click "Start Bot"
4. **Bot should start with REAL market discovery!**
5. Check logs in Railway backend for:
   ```
   INFO: Fetching markets from Polymarket Gamma API
   INFO: Found 20 active markets
   INFO: Bot started for user_xxx
   ```

---

## 🐛 **Troubleshooting**

### Backend Won't Start

**Error**: `ModuleNotFoundError: No module named 'src'`
- **Fix**: Ensure Dockerfile includes `COPY src ./src`
- **Fix**: Ensure Root Directory is `polymarket-sim` (not `polymarket-sim/web`)

**Error**: `FATAL: database does not exist`
- **Fix**: Check DATABASE_URL format (must be `postgresql+asyncpg://...`)
- **Fix**: Verify Supabase password is correct

**Error**: `401 Unauthorized` on `/api/auth/signup`
- **Fix**: Check SUPABASE_KEY and SUPABASE_SERVICE_KEY are correct
- **Fix**: Verify Supabase email provider is enabled

### Frontend Won't Load

**Error**: `Failed to fetch`
- **Fix**: Check NEXT_PUBLIC_API_URL points to backend Railway domain
- **Fix**: Verify backend is running (check `/health` endpoint)

**Error**: CORS errors in console
- **Fix**: Backend CORS should allow all origins (already configured)
- **Fix**: Verify FRONTEND_URL is set in backend env vars

### Bot Won't Start

**Error**: `404 Not Found` on `/api/bot/start`
- **Fix**: Verify backend has bot endpoints uncommented
- **Fix**: Check backend logs for import errors

**Error**: `No markets found`
- **Fix**: Polymarket API might be down (check https://polymarket.com)
- **Fix**: Check backend logs for Gamma API errors

---

## 📊 **Monitoring & Logs**

### Backend Logs

Railway Dashboard → Backend Service → **Logs** tab

**Look for:**
```
INFO: Application startup complete
INFO: Uvicorn running on http://0.0.0.0:8000
INFO: Fetching markets from Polymarket Gamma API
INFO: Found 20 markets
```

### Frontend Logs

Railway Dashboard → Frontend Service → **Logs** tab

**Look for:**
```
Compiled successfully
Ready on http://0.0.0.0:3000
```

### Database Logs

Supabase Dashboard → **Database** → **Logs**

**Look for:**
- Connection attempts
- Query execution
- Table creation

---

## 🎯 **Success Criteria**

You've successfully deployed when:

- ✅ Backend `/health` returns `{"status":"healthy"}`
- ✅ Frontend loads without errors
- ✅ Sign up flow creates user in Supabase
- ✅ Login redirects to dashboard
- ✅ Dashboard shows portfolio ($1000 balance)
- ✅ Markets section shows **REAL Polymarket markets**
- ✅ Bot can be started with any strategy
- ✅ Bot status updates in real-time

---

## 🚀 **Next Steps After Deployment**

### Enable Additional Features

1. **LLM Directional Strategy**:
   - Add `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` to backend env vars
   - Redeploy backend
   - Strategy will use real LLM predictions

2. **WebSocket Real-Time Updates**:
   - Already enabled in backend (`/ws/{user_id}`)
   - Connect from frontend for live portfolio updates

3. **Advanced Monitoring**:
   - Add Sentry for error tracking
   - Add LogDNA/DataDog for log aggregation
   - Add Uptime monitoring (UptimeRobot, etc.)

---

## 📚 **Additional Resources**

- **Railway Docs**: https://docs.railway.app
- **Supabase Docs**: https://supabase.com/docs
- **Polymarket API**: https://docs.polymarket.com (unofficial)
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Next.js Docs**: https://nextjs.org/docs

---

## 💡 **Tips for Production**

1. **Use Custom Domain**: Railway allows custom domains (Settings → Networking)
2. **Enable HTTPS**: Automatic with Railway
3. **Database Backups**: Supabase auto-backups daily (free tier)
4. **Monitor Costs**: Railway has usage-based pricing
5. **Environment Separation**: Create separate projects for dev/staging/prod
6. **Secret Rotation**: Rotate JWT_SECRET_KEY periodically
7. **Rate Limiting**: Consider adding rate limits to API endpoints

---

**You're now running a production Polymarket simulation trader with REAL market data!** 🎉

Questions? Check the troubleshooting section or Railway/Supabase docs.
