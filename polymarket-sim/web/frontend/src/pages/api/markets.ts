/**
 * Next.js API Route: Get Markets
 * This is a mock implementation for demo purposes
 * In production, this would fetch real markets from Polymarket API
 */

import type { NextApiRequest, NextApiResponse } from 'next';

// Mock market data
const mockMarkets = [
  {
    market_id: '0x1234567890abcdef',
    question: 'Will Bitcoin reach $100k by end of 2026?',
    end_date: new Date('2026-12-31').toISOString(),
    yes_token_id: 'btc-100k-yes',
    no_token_id: 'btc-100k-no',
    active: true,
    category: 'Crypto'
  },
  {
    market_id: '0xabcdef1234567890',
    question: 'Will Ethereum merge complete successfully?',
    end_date: new Date('2026-06-30').toISOString(),
    yes_token_id: 'eth-merge-yes',
    no_token_id: 'eth-merge-no',
    active: true,
    category: 'Crypto'
  },
  {
    market_id: '0x9876543210fedcba',
    question: 'Will S&P 500 reach 6000 by Q2 2026?',
    end_date: new Date('2026-06-30').toISOString(),
    yes_token_id: 'sp500-yes',
    no_token_id: 'sp500-no',
    active: true,
    category: 'Finance'
  },
  {
    market_id: '0xfedcba0987654321',
    question: 'Will AI achieve AGI in 2026?',
    end_date: new Date('2026-12-31').toISOString(),
    yes_token_id: 'agi-yes',
    no_token_id: 'agi-no',
    active: true,
    category: 'Technology'
  },
  {
    market_id: '0x1111222233334444',
    question: 'Will Tesla stock hit $500 by end of Q1 2026?',
    end_date: new Date('2026-03-31').toISOString(),
    yes_token_id: 'tsla-500-yes',
    no_token_id: 'tsla-500-no',
    active: true,
    category: 'Stocks'
  }
];

export default function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { limit = 20 } = req.query;
    const maxLimit = parseInt(limit as string);

    // Return mock markets
    const markets = mockMarkets.slice(0, maxLimit);

    res.status(200).json(markets);
  } catch (error) {
    console.error('Error fetching markets:', error);
    res.status(500).json({ error: 'Failed to fetch markets' });
  }
}
