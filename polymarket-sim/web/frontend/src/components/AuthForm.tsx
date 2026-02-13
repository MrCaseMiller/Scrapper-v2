/**
 * Authentication form component
 */

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { authAPI } from '../utils/api';

interface AuthFormProps {
  mode: 'login' | 'signup';
}

export default function AuthForm({ mode }: AuthFormProps) {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (mode === 'signup') {
        await authAPI.signup(email, password);
        setShowConfirmation(true);
      } else {
        const data = await authAPI.login(email, password);
        localStorage.setItem('access_token', data.access_token);
        router.push('/dashboard');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  if (showConfirmation) {
    return (
      <div className="w-full max-w-md p-8 bg-bg-secondary rounded-8 border border-text-low">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-text-high mb-4">
            Check Your Email
          </h2>
          <p className="text-text-medium mb-8">
            We've sent a confirmation email to <strong>{email}</strong>.
            Please click the link in the email to verify your account.
          </p>
          <button
            onClick={() => router.push('/login')}
            className="w-full py-3 px-4 bg-accent hover:bg-accent/90 text-white rounded-8 transition-colors duration-200"
          >
            Go to Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-md p-8 bg-bg-secondary rounded-8 border border-text-low">
      <h2 className="text-2xl font-bold text-text-high mb-8 text-center">
        {mode === 'login' ? 'Login' : 'Sign Up'}
      </h2>

      <form onSubmit={handleSubmit} className="space-y-6">
        {error && (
          <div className="p-4 bg-error/10 border border-error rounded-8 text-error text-sm">
            {error}
          </div>
        )}

        <div>
          <label htmlFor="email" className="block text-sm text-text-medium mb-2">
            Email
          </label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full px-4 py-3 bg-bg-primary border border-text-low rounded-8 text-text-high focus:outline-none focus:border-accent transition-colors"
            required
            disabled={loading}
          />
        </div>

        <div>
          <label htmlFor="password" className="block text-sm text-text-medium mb-2">
            Password
          </label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-4 py-3 bg-bg-primary border border-text-low rounded-8 text-text-high focus:outline-none focus:border-accent transition-colors"
            required
            minLength={6}
            disabled={loading}
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 px-4 bg-accent hover:bg-accent/90 text-white rounded-8 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Loading...' : mode === 'login' ? 'Login' : 'Sign Up'}
        </button>

        <p className="text-center text-sm text-text-medium">
          {mode === 'login' ? (
            <>
              Don't have an account?{' '}
              <a href="/signup" className="text-accent hover:underline">
                Sign up
              </a>
            </>
          ) : (
            <>
              Already have an account?{' '}
              <a href="/login" className="text-accent hover:underline">
                Login
              </a>
            </>
          )}
        </p>
      </form>
    </div>
  );
}
