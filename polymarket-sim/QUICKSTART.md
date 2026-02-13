# Quick Start Guide - Railway + Supabase Deployment

This guide will get you from zero to deployed in under 15 minutes.

## Prerequisites

- GitHub account
- Railway account (free tier works)
- Supabase account (free tier works)

## Step 1: Set Up Supabase (5 minutes)

1. Go to [supabase.com](https://supabase.com)
2. Click **New Project**
3. Name it `polymarket-sim`
4. Choose a database password (save it!)
5. Select closest region
6. Click **Create new project**

While it's provisioning:
7. Go to **Settings** → **API**
8. Copy these 3 values:
   - Project URL
   - `anon` `public` key
   - `service_role` key

9. Go to **Settings** → **Database**
10. Scroll to **Connection string** → **URI**
11. Copy the connection string (it starts with `postgresql://`)

## Step 2: Deploy Backend to Railway (5 minutes)

1. Go to [railway.app](https://railway.app)
2. Click **New Project**
3. Select **Deploy from GitHub repo**
4. Connect GitHub and select this repository
5. Railway will detect the project

Configure environment variables:
6. Click on the service → **Variables**
7. Click **+ New Variable** and add each:

```
SUPABASE_URL=<your-project-url>
SUPABASE_KEY=<your-anon-key>
SUPABASE_SERVICE_KEY=<your-service-role-key>
DATABASE_URL=<your-connection-string>
JWT_SECRET_KEY=<run: openssl rand -hex 32>
JWT_ALGORITHM=HS256
ENVIRONMENT=production
DEFAULT_STARTING_BALANCE=1000.0
```

8. Click **Settings** → **Networking** → **Generate Domain**
9. Copy the backend URL (e.g., `https://xxx.railway.app`)

## Step 3: Deploy Frontend to Railway (3 minutes)

1. In same Railway project, click **+ New** → **GitHub Repo**
2. Select same repository
3. Railway will create a new service

Configure environment variables:
4. Click on the new service → **Variables**
5. Add these variables:

```
NEXT_PUBLIC_API_URL=<your-backend-url>
NEXT_PUBLIC_SUPABASE_URL=<your-supabase-project-url>
NEXT_PUBLIC_SUPABASE_ANON_KEY=<your-supabase-anon-key>
```

6. Click **Settings** → **Networking** → **Generate Domain**
7. Copy the frontend URL

## Step 4: Update Configuration (2 minutes)

### Update Backend
1. Go to backend service → **Variables**
2. Add/update:
```
FRONTEND_URL=<your-frontend-url>
```

### Update Supabase
1. Go to Supabase → **Authentication** → **URL Configuration**
2. Set **Site URL**: `<your-frontend-url>`
3. Add **Redirect URLs**: `<your-frontend-url>/*`
4. Click **Save**

### Update Frontend Service
1. In Railway, click frontend service → **Settings**
2. Under **Build**, verify:
   - **Root Directory**: (leave empty)
   - **Build Command**: `cd web/frontend && npm install && npm run build`
   - **Start Command**: `cd web/frontend && npm start`

### Update Backend Service
1. Click backend service → **Settings**
2. Under **Build**, verify:
   - **Root Directory**: (leave empty)
   - **Build Command**: `cd web && pip install -r requirements.txt`
   - **Start Command**: `cd web/backend && uvicorn main:app --host 0.0.0.0 --port $PORT`

## Step 5: Test It! (1 minute)

1. Visit your frontend URL
2. Click **Sign Up**
3. Enter email and password
4. Check your email for confirmation
5. Click the confirmation link
6. Go back and **Login**
7. See your dashboard!

## Troubleshooting

### "Connection refused" error
- Wait 2-3 minutes for services to deploy
- Check Railway logs: Service → **Deployments** → **View Logs**

### Email not arriving
- Check spam folder
- In Supabase, go to **Authentication** → **Email Templates**
- Verify SMTP is configured (default uses Supabase's SMTP)

### Backend health check fails
- Visit `<backend-url>/health`
- Should return `{"status":"healthy"}`
- If not, check Railway logs

### Database not connecting
- Verify `DATABASE_URL` format: `postgresql://...`
- Make sure it starts with `postgresql://` not `postgres://`
- If using Supabase pooler, replace with direct connection string

## Generate JWT Secret

On Mac/Linux:
```bash
openssl rand -hex 32
```

On Windows (PowerShell):
```powershell
[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Maximum 256 }))
```

Or use an online generator: [randomkeygen.com](https://randomkeygen.com/)

## Quick Commands

### View Backend Logs
Railway → Backend Service → Deployments → View Logs

### View Frontend Logs
Railway → Frontend Service → Deployments → View Logs

### Restart Services
Railway → Service → Settings → Restart

### Check Database
Supabase → Table Editor (should see tables after first deployment)

## What's Next?

- ✅ Users can sign up and log in
- ✅ Dashboard shows portfolio
- ⏳ Add trading simulation engine integration
- ⏳ Connect to Polymarket APIs
- ⏳ Add strategy selection UI
- ⏳ Enable real-time updates via WebSocket

## Cost Estimate

**Supabase Free Tier:**
- 500 MB database
- 2 GB bandwidth
- 50,000 monthly active users
- **Cost: $0/month**

**Railway Free Tier:**
- $5 of usage per month
- 500 GB of outbound bandwidth
- **Cost: $0/month** (with free credits)

**Total: $0/month** to get started!

## Support

- **Railway Issues**: Check logs in Railway dashboard
- **Supabase Issues**: Check Supabase logs and docs
- **App Issues**: Open GitHub issue

## Security Checklist

- [ ] JWT_SECRET_KEY is random and 32+ characters
- [ ] SUPABASE_SERVICE_KEY is secret (not in frontend)
- [ ] Email confirmation is enabled
- [ ] CORS allows only your frontend URL
- [ ] Database password is strong

## Done!

Your Polymarket Simulation Trader web app is now live! 🎉

Visit your frontend URL and start paper trading!
