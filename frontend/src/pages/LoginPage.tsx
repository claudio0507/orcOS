import { LoginForm } from '../components/auth/LoginForm';
import { MFAForm } from '../components/auth/MFAForm';

export function LoginPage() {
  return (
    <div>
      <h1>orcOS — Login</h1>
      <LoginForm />
      {/* MFA aparece condicionalmente depois */}
      <MFAForm onVerify={(code) => console.log('MFA:', code)} />
    </div>
  );
}
