import { useState } from 'react';
import { LoginForm } from '../components/auth/LoginForm';
import { MFAForm } from '../components/auth/MFAForm';

export function LoginPage() {
  const [isMfaRequired, setIsMfaRequired] = useState(false);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
      <div className="max-w-md w-full bg-white p-8 rounded-lg shadow-md border border-gray-200">
        <h1 className="text-2xl font-bold text-center mb-6 text-gray-800">orcOS — Login</h1>
        
        {!isMfaRequired ? (
          <LoginForm />
        ) : (
          <MFAForm onVerify={(code) => console.log('Verificando MFA:', code)} />
        )}

        <div className="mt-4 text-center">
          <button 
            onClick={() => setIsMfaRequired(!isMfaRequired)}
            className="text-sm text-blue-500 hover:underline"
          >
            {isMfaRequired ? "Voltar para senha" : "Simular MFA (Teste)"}
          </button>
        </div>
      </div>
    </div>
  );
}
