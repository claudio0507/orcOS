import { useState } from 'react';

interface MFAFormProps {
  onVerify: (code: string) => void;
}

export function MFAForm({ onVerify }: MFAFormProps) {
  const [code, setCode] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (code.length === 6) {
      onVerify(code);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <p className="text-sm text-gray-600">Insira o código de 6 dígitos do seu app de autenticação.</p>
      <input
        type="text"
        value={code}
        onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
        placeholder="Código TOTP (6 dígitos)"
        maxLength={6}
        className="border p-2 w-full text-center tracking-widest text-lg"
      />
      <button 
        type="submit" 
        className="bg-green-600 text-white p-2 rounded w-full hover:bg-green-700"
      >
        Verificar
      </button>
    </form>
  );
}
