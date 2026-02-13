# Polymarket Simulation Trader - Web Application

A production-ready web application for paper trading Polymarket prediction markets with Supabase authentication and PostgreSQL backend.

## Features

### Authentication
- Email/password signup with confirmation
- Secure JWT-based authentication
- Protected routes and API endpoints
- Supabase integration for user management

### Web Dashboard
- Real-time portfolio tracking
- Position management with P&L
- Recent fills history
- Resting orders display
- Mobile-responsive design
- Dark mode (Special Projects design system)

### Backend API
- FastAPI with async/await
- PostgreSQL database (Supabase)
- RESTful API endpoints
- WebSocket support for real-time updates
- Secure authentication middleware

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Relational database via Supabase
- **SQLAlchemy** - ORM with async support
- **Supabase** - Authentication and database hosting
- **JWT** - Secure token-based auth

### Frontend
- **Next.js 14** - React framework with SSR
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS
- **Axios** - HTTP client

### Deployment
- **Railway** - Backend and frontend hosting
- **Supabase** - Database and auth infrastructure

## Project Structure

```
polymarket-sim/
├── web/
│   ├── backend/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI application
│   │   ├── config.py        # Configuration management
│   │   ├── database.py      # PostgreSQL models and operations
│   │   └── auth.py          # Authentication logic
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── app/         # Next.js app directory
│   │   │   │   ├── login/   # Login page
│   │   │   │   ├── signup/  # Signup page
│   │   │   │   └── dashboard/ # Main dashboard
│   │   │   ├── components/  # React components
│   │   │   └── utils/       # API client and utilities
│   │   ├── package.json
│   │   └── tailwind.config.js
│   └── requirements.txt     # Python dependencies
├── railway.json             # Railway backend config
├── railway-frontend.json    # Railway frontend config
├── Procfile                 # Railway process file
├── .env.example            # Environment variables template
└── DEPLOYMENT.md           # Deployment guide
```

## Local Development

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL (or Supabase account)
- Supabase account

### Setup Backend

1. Install dependencies:
```bash
cd web
pip install -r requirements.txt
```

2. Create `.env` file:
```bash
cp ../.env.example .env
# Edit .env with your Supabase credentials
```

3. Run backend:
```bash
cd backend
uvicorn main:app --reload --port 8000
```

Backend will be available at `http://localhost:8000`

### Setup Frontend

1. Install dependencies:
```bash
cd web/frontend
npm install
```

2. Create `.env.local` file:
```bash
cp .env.local.example .env.local
# Edit .env.local with your API and Supabase URLs
```

3. Run frontend:
```bash
npm run dev
```

Frontend will be available at `http://localhost:3000`

## API Endpoints

### Authentication
- `POST /api/auth/signup` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user

### Portfolio
- `GET /api/portfolio` - Get user portfolio
- `GET /api/positions` - Get user positions
- `GET /api/fills` - Get recent fills
- `GET /api/orders` - Get resting orders

### WebSocket
- `WS /ws/{user_id}` - Real-time updates

## Database Schema

### Users
- `id` - Supabase user ID (primary key)
- `email` - User email
- `created_at` - Account creation timestamp
- `updated_at` - Last update timestamp

### Portfolios
- `user_id` - Foreign key to users
- `balance` - Available USDC
- `total_deposited` - Total deposited amount
- `realized_pnl` - Realized profit/loss
- `total_fees_paid` - Total fees paid

### Positions
- `user_id` - Foreign key to users
- `token_id` - Token identifier
- `market_id` - Market identifier
- `market_side` - YES or NO
- `shares` - Number of shares
- `avg_entry_price` - Average entry price
- `current_price` - Current market price

### Orders
- `order_id` - Unique order ID
- `user_id` - Foreign key to users
- `market_id` - Foreign key to markets
- `side` - BUY or SELL
- `status` - PENDING, FILLED, RESTING, REJECTED

### Fills
- `fill_id` - Unique fill ID
- `order_id` - Foreign key to orders
- `user_id` - Foreign key to users
- `shares` - Shares filled
- `price` - Fill price
- `fee` - Trading fee

## Design System

Following Special Projects design principles:

### Colors
- **Background Primary**: #09090B
- **Background Secondary**: #18181B
- **Text High**: #E4E4E7
- **Text Medium**: #71717A
- **Text Low**: #3F3F46
- **Accent**: #3B82F6
- **Success**: #10B981
- **Error**: #EF4444

### Spacing
- 0, 8px, 16px, 40px only

### Typography
- **Sans**: System sans-serif for labels
- **Mono**: Monospace for all data (prices, numbers, etc.)

### Radius
- 8px only

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

### Quick Deploy to Railway

1. **Backend**:
   - Create new Railway project from GitHub
   - Add environment variables
   - Deploy with `railway.json` config

2. **Frontend**:
   - Add new service to same project
   - Add frontend environment variables
   - Deploy with `railway-frontend.json` config

3. **Database**:
   - Use Supabase (automatically handled)
   - Tables created on first startup

## Environment Variables

### Backend (.env)
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
DATABASE_URL=postgresql://...
JWT_SECRET_KEY=your-secret-key
FRONTEND_URL=https://your-frontend.railway.app
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

## Security

- JWT authentication on all protected endpoints
- Supabase handles email verification
- Password hashing via Supabase
- HTTPS enforced in production
- CORS configured for frontend domain only
- Service role key kept server-side only

## Testing

### Backend Tests
```bash
cd web
pytest
```

### Frontend Tests
```bash
cd web/frontend
npm test
```

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test locally
5. Submit pull request

## License

© Special Projects Studio

## Support

- Issues: [GitHub Issues](https://github.com/your-repo/issues)
- Railway: [Railway Docs](https://docs.railway.app)
- Supabase: [Supabase Docs](https://supabase.com/docs)
