import React from 'react';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'elevated' | 'inset';
  children?: React.ReactNode;
}

export const Card: React.FC<CardProps> = ({
  variant = 'default',
  className = '',
  children,
  ...props
}) => {
  const variantStyles = {
    default:
      'bg-surface border border-border-hairline shadow-neumorphic-card',
    elevated:
      'bg-surface border border-border-hairline shadow-neumorphic-elevated',
    inset:
      'bg-app/70 border border-border-hairline shadow-neumorphic-inset',
  };

  return (
    <div
      className={`rounded-lg p-5 text-text-primary transition-all duration-150 ease-in-out ${variantStyles[variant]} ${className}`.trim()}
      {...props}
    >
      {children}
    </div>
  );
};

export default Card;
