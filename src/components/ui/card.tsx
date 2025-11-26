import * as React from 'react';

const combineClasses = (...classes: Array<string | undefined>) =>
  classes.filter(Boolean).join(' ');

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {}

const Card = React.forwardRef<HTMLDivElement, CardProps>(({ className, ...props }, ref) => (
  <div ref={ref} className={combineClasses('rounded-xl bg-white shadow', className)} {...props} />
));
Card.displayName = 'Card';

export interface CardContentProps extends React.HTMLAttributes<HTMLDivElement> {}

const CardContent = React.forwardRef<HTMLDivElement, CardContentProps>(({ className, ...props }, ref) => (
  <div ref={ref} className={combineClasses('p-6', className)} {...props} />
));
CardContent.displayName = 'CardContent';

export { Card, CardContent };
