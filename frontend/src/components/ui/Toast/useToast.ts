import { useState, useCallback, useEffect } from 'react'
import { ToastItem } from './ToastContainer'

interface ToastOptions {
  duration?: number
}

class ToastManager {
  private static instance: ToastManager
  private listeners: ((toasts: ToastItem[]) => void)[] = []
  private toasts: ToastItem[] = []

  static getInstance(): ToastManager {
    if (!ToastManager.instance) {
      ToastManager.instance = new ToastManager()
    }
    return ToastManager.instance
  }

  subscribe(listener: (toasts: ToastItem[]) => void) {
    this.listeners.push(listener)
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener)
    }
  }

  private notify() {
    this.listeners.forEach(listener => listener([...this.toasts]))
  }

  show(message: string, type: ToastItem['type'] = 'info', options: ToastOptions = {}) {
    const id = Date.now().toString() + Math.random().toString(36).substr(2, 9)
    const toast: ToastItem = {
      id,
      message,
      type,
      duration: options.duration
    }

    this.toasts.push(toast)
    this.notify()

    // 自动移除
    if (options.duration !== 0) {
      const duration = options.duration || 3000
      setTimeout(() => {
        this.remove(id)
      }, duration)
    }

    return id
  }

  remove(id: string) {
    this.toasts = this.toasts.filter(toast => toast.id !== id)
    this.notify()
  }

  clear() {
    this.toasts = []
    this.notify()
  }
}

export const toastManager = ToastManager.getInstance()

export const useToast = () => {
  const [toasts, setToasts] = useState<ToastItem[]>([])

  useEffect(() => {
    return toastManager.subscribe(setToasts)
  }, [])

  const show = useCallback((message: string, type: ToastItem['type'] = 'info', options: ToastOptions = {}) => {
    return toastManager.show(message, type, options)
  }, [])

  const success = useCallback((message: string, options: ToastOptions = {}) => {
    return show(message, 'success', options)
  }, [show])

  const error = useCallback((message: string, options: ToastOptions = {}) => {
    return show(message, 'error', options)
  }, [show])

  const info = useCallback((message: string, options: ToastOptions = {}) => {
    return show(message, 'info', options)
  }, [show])

  const warning = useCallback((message: string, options: ToastOptions = {}) => {
    return show(message, 'warning', options)
  }, [show])

  const remove = useCallback((id: string) => {
    toastManager.remove(id)
  }, [])

  const clear = useCallback(() => {
    toastManager.clear()
  }, [])

  return {
    toasts,
    show,
    success,
    error,
    info,
    warning,
    remove,
    clear
  }
}