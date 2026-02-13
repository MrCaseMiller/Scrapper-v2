/**
 * Login page
 */

import AuthForm from '../../components/AuthForm';

export default function LoginPage() {
  return (
    <div className="min-h-screen bg-bg-primary flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-text-high mb-2">
            Polymarket Sim
          </h1>
          <p className="text-text-medium">
            Paper trading for prediction markets
          </p>
        </div>
        <AuthForm mode="login" />
      </div>
    </div>
  );
}
