import React, { createContext, useContext } from 'react';
import Input from '../Input/Input';
import Textarea from '../Textarea/Textarea';
import styles from './Form.module.css';

interface FormProps {
  children: React.ReactNode;
  layout?: 'vertical' | 'horizontal';
  onSubmit?: (e: React.FormEvent) => void;
  className?: string;
}

interface FormItemProps {
  label?: string;
  name?: string;
  required?: boolean;
  help?: string;
  error?: string;
  children: React.ReactNode;
  className?: string;
}

interface FormContextValue {
  layout: 'vertical' | 'horizontal';
}

const FormContext = createContext<FormContextValue>({ layout: 'vertical' });

const Form: React.FC<FormProps> = ({
  children,
  layout = 'vertical',
  onSubmit,
  className = '',
}) => {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (onSubmit) {
      onSubmit(e);
    }
  };

  return (
    <FormContext.Provider value={{ layout }}>
      <form
        className={`${styles.form} ${className}`}
        onSubmit={handleSubmit}
      >
        {children}
      </form>
    </FormContext.Provider>
  );
};

const FormItem: React.FC<FormItemProps> = ({
  label,
  name,
  required = false,
  help,
  error,
  children,
  className = '',
}) => {
  const { layout } = useContext(FormContext);

  return (
    <div
      className={`${styles.formItem} ${styles[layout]} ${
        error ? styles.hasError : ''
      } ${className}`}
    >
      {label && (
        <label className={styles.label} htmlFor={name}>
          {label}
          {required && <span className={styles.required}>*</span>}
        </label>
      )}
      <div className={styles.control}>
        {children}
        {help && !error && <div className={styles.help}>{help}</div>}
        {error && <div className={styles.error}>{error}</div>}
      </div>
    </div>
  );
};

export { Form, FormItem };
export type { FormProps, FormItemProps };