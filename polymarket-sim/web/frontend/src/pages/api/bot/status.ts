/**
 * Next.js API Route: Get Bot Status
 * This is a mock implementation for demo purposes
 */

import type { NextApiRequest, NextApiResponse } from 'next';

// In-memory bot state (shared with start.ts in production this would be in a database)
const botStates = new Map<string, any>();

export default function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const userId = 'demo-user'; // In production, get from auth token

    const status = botStates.get(userId);

    // Return null if bot not running
    if (!status) {
      return res.status(200).json(null);
    }

    // Simulate signal count incrementing
    if (status.running) {
      status.signal_count += Math.floor(Math.random() * 3);
      status.last_update = new Date().toISOString();
    }

    res.status(200).json(status);
  } catch (error) {
    console.error('Error getting bot status:', error);
    res.status(500).json({ error: 'Failed to get bot status' });
  }
}
