import React from 'react'
import ToastContainer from './ToastContainer'
import { useToast } from './useToast'

interface ToastProviderProps {
  children: React.ReactNode
}

export const ToastProvider: React.FC<ToastProviderProps> = ({ children }) => {
  const { toasts, remove } = useToast()

  return (
    <>
      {children}
      <ToastContainer toasts={toasts} onClose={remove} />
    </>
  )
}