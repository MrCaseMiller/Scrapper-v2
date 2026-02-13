/**
 * Next.js API Route: Start Trading Bot
 * This is a mock implementation for demo purposes
 */

import type { NextApiRequest, NextApiResponse } from 'next';

// In-memory bot state (would be in database in production)
const botStates = new Map<string, any>();

export default function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const config = req.body;
    const userId = 'demo-user'; // In production, get from auth token

    // Simulate bot starting
    const botStatus = {
      user_id: userId,
      running: true,
      strategy: config.strategy,
      active_markets: Math.floor(Math.random() * 5) + 3, // 3-7 markets
      signal_count: 0,
      error_count: 0,
      last_update: new Date().toISOString(),
      config: config
    };

    botStates.set(userId, botStatus);

    // Simulate signal updates
    setTimeout(() => {
      const state = botStates.get(userId);
      if (state) {
        state.signal_count = Math.floor(Math.random() * 10) + 1;
        state.last_update = new Date().toISOString();
      }
    }, 2000);

    res.status(200).json(botStatus);
  } catch (error) {
    console.error('Error starting bot:', error);
    res.status(500).json({ error: 'Failed to start bot' });
  }
}
