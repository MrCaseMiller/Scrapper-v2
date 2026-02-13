/**
 * Next.js API Route: Get Portfolio
 * This is a mock implementation for demo purposes
 */

import type { NextApiRequest, NextApiResponse } from 'next';

// Mock portfolio data
const mockPortfolio = {
  balance: 10000.00,
  total_deposited: 10000.00,
  realized_pnl: 0.00,
  total_fees_paid: 0.00,
  positions_value: 0.00,
  total_value: 10000.00,
  unrealized_pnl: 0.00,
  total_pnl: 0.00,
  total_return_pct: 0.00,
  num_positions: 0
};

export default function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    // Return mock portfolio data
    res.status(200).json(mockPortfolio);
  } catch (error) {
    console.error('Error getting portfolio:', error);
    res.status(500).json({ error: 'Failed to get portfolio' });
  }
}
