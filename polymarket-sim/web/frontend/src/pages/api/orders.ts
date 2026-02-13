/**
 * Next.js API Route: Get Orders
 * This is a mock implementation for demo purposes
 */

import type { NextApiRequest, NextApiResponse } from 'next';

// Mock orders data (empty for new user)
const mockOrders: any[] = [];

export default function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    // Return empty orders for demo
    res.status(200).json(mockOrders);
  } catch (error) {
    console.error('Error getting orders:', error);
    res.status(500).json({ error: 'Failed to get orders' });
  }
}
