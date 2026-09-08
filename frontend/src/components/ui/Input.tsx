import React from 'react';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: string;
  label?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className = '', error, label, id, disabled, ...props }, ref) => {
    return (
      <div className="w-full space-y-1.5">
        {label && (
          <label
            htmlFor={id}
            className="block text-xs font-medium text-text-secondary select-none tracking-wide"
          >
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={id}
          disabled={disabled}
          className={`w-full h-10 px-3.5 text-sm rounded-md bg-app/80 text-text-primary placeholder:text-text-muted border border-border-hairline shadow-neumorphic-inset transition-all duration-150 ease-in-out focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary-interactive focus-visible:border-primary-interactive disabled:opacity-50 disabled:cursor-not-allowed ${
            error ? 'border-red-400/60 focus-visible:ring-red-400/80' : ''
          } ${className}`.trim()}
          {...props}
        />
        {error && <p className="text-xs text-red-400/90 font-medium tracking-wide">{error}</p>}
      </div>
    );
  }
);

Input.displayName = 'Input';

export default Input;
