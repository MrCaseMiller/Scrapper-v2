/**
 * Next.js API Route: Get Fills
 * This is a mock implementation for demo purposes
 */

import type { NextApiRequest, NextApiResponse } from 'next';

// Mock fills data (empty for new user)
const mockFills: any[] = [];

export default function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { limit = 10 } = req.query;

    // Return empty fills for demo
    res.status(200).json(mockFills);
  } catch (error) {
    console.error('Error getting fills:', error);
    res.status(500).json({ error: 'Failed to get fills' });
  }
}
