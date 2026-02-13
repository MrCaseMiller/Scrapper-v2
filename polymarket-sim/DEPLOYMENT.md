# Deployment Guide - Railway + Supabase

This guide covers deploying the Polymarket Simulation Trader to Railway with Supabase as the database backend.

## Prerequisites

1. **Supabase Account** - [https://supabase.com](https://supabase.com)
2. **Railway Account** - [https://railway.app](https://railway.app)
3. **Git Repository** - Code pushed to GitHub

## Step 1: Set Up Supabase

### 1.1 Create Supabase Project

1. Go to [Supabase](https://supabase.com) and create a new project
2. Choose a project name and database password
3. Select a region closest to your users
4. Wait for the project to be provisioned

### 1.2 Configure Authentication

1. In Supabase dashboard, go to **Authentication** → **Settings**
2. Enable **Email** provider
3. Configure **Site URL** (will be your Railway frontend URL)
4. Configure **Redirect URLs** (add your Railway frontend URL)
5. Customize email templates if desired

### 1.3 Get Database Credentials

1. Go to **Settings** → **Database**
2. Copy the **Connection string** (Postgres URL)
3. Go to **Settings** → **API**
4. Copy:
   - **Project URL**
   - **anon/public** key
   - **service_role** key (keep this secret!)

## Step 2: Deploy Backend to Railway

### 2.1 Create New Project

1. Go to [Railway](https://railway.app)
2. Click **New Project**
3. Select **Deploy from GitHub repo**
4. Connect your GitHub account and select the repository

### 2.2 Configure Backend Service

1. Railway will auto-detect the Python app
2. Go to **Settings** → **Environment Variables**
3. Add the following environment variables:

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
DATABASE_URL=postgresql://...  (from Supabase)
JWT_SECRET_KEY=your-secret-key  (generate with: openssl rand -hex 32)
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENVIRONMENT=production
FRONTEND_URL=https://your-frontend.railway.app  (will set after frontend deploy)
DEFAULT_STARTING_BALANCE=1000.0
```

4. Go to **Settings** → **Networking**
5. Click **Generate Domain** to get a public URL
6. Copy the backend URL (e.g., `https://your-backend.railway.app`)

### 2.3 Configure Build

1. Go to **Settings** → **Build**
2. Set **Build Command**: `cd web && pip install -r requirements.txt`
3. Set **Start Command**: `cd web/backend && uvicorn main:app --host 0.0.0.0 --port $PORT`

## Step 3: Deploy Frontend to Railway

### 3.1 Create Frontend Service

1. In the same Railway project, click **New Service**
2. Select **Deploy from GitHub repo** (same repository)
3. Choose a different name (e.g., "frontend")

### 3.2 Configure Frontend Service

1. Go to **Settings** → **Environment Variables**
2. Add:

```
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

3. Go to **Settings** → **Networking**
4. Click **Generate Domain** to get a public URL
5. Copy the frontend URL

### 3.3 Configure Build

1. Go to **Settings** → **Build**
2. Set **Build Command**: `cd web/frontend && npm install && npm run build`
3. Set **Start Command**: `cd web/frontend && npm start`

## Step 4: Update Environment Variables

### 4.1 Update Backend

Go back to the backend service and update `FRONTEND_URL` to your frontend Railway URL.

### 4.2 Update Supabase

1. In Supabase, go to **Authentication** → **Settings**
2. Update **Site URL** to your frontend URL
3. Add frontend URL to **Redirect URLs**

## Step 5: Initialize Database

### 5.1 Run Database Migrations

The database tables will be created automatically on first startup. To verify:

1. Visit your backend URL: `https://your-backend.railway.app/health`
2. You should see: `{"status": "healthy"}`

### 5.2 Verify Tables

In Supabase:
1. Go to **Table Editor**
2. You should see tables: `users`, `portfolios`, `markets`, `orders`, `fills`, `positions`, etc.

## Step 6: Test the Application

1. Visit your frontend URL: `https://your-frontend.railway.app`
2. Click **Sign Up**
3. Enter email and password
4. Check your email for confirmation link
5. Click the confirmation link
6. Log in with your credentials
7. You should see the dashboard!

## Step 7: Configure Email (Optional)

### 7.1 Custom SMTP

For production, configure custom SMTP in Supabase:

1. Go to **Settings** → **Auth** → **SMTP Settings**
2. Enable **Custom SMTP**
3. Enter your SMTP credentials (SendGrid, Mailgun, etc.)

### 7.2 Email Templates

Customize email templates in **Authentication** → **Email Templates**

## Environment Variables Reference

### Backend (.env)

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key

# Database
DATABASE_URL=postgresql://user:pass@host:port/db

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
ENVIRONMENT=production
FRONTEND_URL=https://your-frontend.railway.app
DEFAULT_STARTING_BALANCE=1000.0
```

### Frontend (.env.local)

```bash
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

## Troubleshooting

### Backend Not Starting

- Check Railway logs: **Deployments** → **View Logs**
- Verify all environment variables are set
- Ensure DATABASE_URL is correct

### Frontend Not Loading

- Check Railway logs
- Verify API_URL points to backend
- Check browser console for errors

### Authentication Not Working

- Verify Supabase Site URL and Redirect URLs
- Check JWT_SECRET_KEY is set
- Ensure email confirmation is working

### Database Connection Failed

- Verify DATABASE_URL format: `postgresql+asyncpg://...`
- Check Supabase database is active
- Verify network connectivity from Railway to Supabase

## Monitoring

### Railway

- View logs in **Deployments** → **View Logs**
- Monitor metrics in **Metrics** tab
- Set up alerts in **Settings** → **Alerts**

### Supabase

- Monitor auth events in **Authentication** → **Logs**
- View database performance in **Database** → **Performance**
- Check API usage in **Settings** → **API**

## Scaling

### Railway

- Upgrade plan for more resources
- Enable horizontal scaling in **Settings**
- Configure auto-scaling rules

### Supabase

- Upgrade to paid plan for more connections
- Enable connection pooling
- Optimize database queries

## Security Checklist

- [ ] All environment variables are set and secure
- [ ] JWT_SECRET_KEY is random and strong (32+ characters)
- [ ] SUPABASE_SERVICE_KEY is kept secret (not exposed to frontend)
- [ ] CORS is configured correctly (only allow your frontend URL)
- [ ] HTTPS is enabled (Railway provides this by default)
- [ ] Email confirmation is required for signup
- [ ] Database credentials are not exposed
- [ ] API endpoints require authentication

## Next Steps

1. **Add Trading Logic**: Integrate the simulation engine
2. **Set Up Monitoring**: Add error tracking (Sentry, etc.)
3. **Configure Backups**: Enable database backups in Supabase
4. **Custom Domain**: Add custom domain in Railway
5. **Analytics**: Add analytics tracking
6. **Rate Limiting**: Implement rate limiting on API

## Support

- Railway: [https://railway.app/help](https://railway.app/help)
- Supabase: [https://supabase.com/docs](https://supabase.com/docs)
- Issues: Open an issue on GitHub
