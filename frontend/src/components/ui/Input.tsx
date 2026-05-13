import { InputHTMLAttributes, forwardRef } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className = '', ...props }, ref) => {
    return (
      <div className="space-y-1 w-full">
        {label && (
          <label className="block text-sm font-medium text-gray-700">
            {label}
          </label>
        )}
        <input
          ref={ref}
          className={`
            border border-gray-300 p-2 rounded w-full 
            focus:ring-2 focus:ring-blue-500 focus:border-transparent 
            outline-none transition-all
            ${error ? 'border-red-500' : ''}
            ${className}
          `}
          {...props}
        />
        {error && <p className="text-red-500 text-xs">{error}</p>}
      </div>
    );
  }
);

Input.displayName = 'Input';
