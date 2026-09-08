import React from 'react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'solid' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  children?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'solid',
  size = 'md',
  className = '',
  disabled,
  children,
  ...props
}) => {
  const baseStyles =
    'inline-flex items-center justify-center font-medium transition-all duration-150 ease-in-out select-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-interactive focus-visible:ring-offset-2 focus-visible:ring-offset-app disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none active:scale-[0.98]';

  const sizeStyles = {
    sm: 'h-8 px-3 text-xs rounded-sm gap-1.5',
    md: 'h-10 px-4 text-sm rounded-md gap-2',
    lg: 'h-12 px-6 text-base rounded-md gap-2.5',
  };

  const variantStyles = {
    solid:
      'bg-primary-interactive hover:bg-primary-hover text-text-primary shadow-neumorphic-card border border-white/[0.08]',
    outline:
      'bg-transparent hover:bg-surface border border-border-hairline hover:border-border-subtle text-text-primary shadow-sm',
    ghost:
      'bg-transparent hover:bg-surface/60 text-text-secondary hover:text-text-primary',
  };

  return (
    <button
      className={`${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${className}`.trim()}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
};

export default Button;
