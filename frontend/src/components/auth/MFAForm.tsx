import { useState } from 'react';

export function MFAForm({ onVerify }: { onVerify: (code: string) => void }) {
  const [code, setCode] = useState('');

  return (
    <form onSubmit={(e) => { e.preventDefault(); onVerify(code); }}>
      <input
        value={code}
        onChange={(e) => setCode(e.target.value)}
        placeholder="Código TOTP (6 dígitos)"
        maxLength={6}
      />
      <button type="submit">Verificar</button>
    </form>
  );
}
