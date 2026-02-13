/**
 * Next.js API Route: Stop Trading Bot
 * This is a mock implementation for demo purposes
 */

import type { NextApiRequest, NextApiResponse } from 'next';

// In-memory bot state (shared with start.ts in production this would be in a database)
const botStates = new Map<string, any>();

export default function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const userId = 'demo-user'; // In production, get from auth token

    // Remove bot state
    botStates.delete(userId);

    res.status(200).json({
      user_id: userId,
      running: false,
      message: 'Bot stopped successfully'
    });
  } catch (error) {
    console.error('Error stopping bot:', error);
    res.status(500).json({ error: 'Failed to stop bot' });
  }
}
