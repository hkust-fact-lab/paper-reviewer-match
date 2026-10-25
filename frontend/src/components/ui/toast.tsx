/**
 * 极简 toast，不依赖第三方库。
 * 用法：toast.success('已添加') / toast.error('失败')
 */
import { useEffect, useState } from 'react'

type ToastItem = { id: number; message: string; type: 'success' | 'error' | 'info' }

let _items: ToastItem[] = []
let _listeners = new Set<() => void>()
let _nextId = 1

function notify() { _listeners.forEach(f => f()) }

export const toast = {
  success: (msg: string) => add(msg, 'success'),
  error:   (msg: string) => add(msg, 'error'),
  info:    (msg: string) => add(msg, 'info'),
}

function add(message: string, type: ToastItem['type']) {
  const id = _nextId++
  _items = [..._items, { id, message, type }]
  notify()
  setTimeout(() => {
    _items = _items.filter(i => i.id !== id)
    notify()
  }, 3000)
}

export function Toaster() {
  const [items, setItems] = useState<ToastItem[]>(_items)
  useEffect(() => {
    const handler = () => setItems([..._items])
    _listeners.add(handler)
    return () => { _listeners.delete(handler) }
  }, [])

  if (!items.length) return null

  return (
    <div className="fixed bottom-4 right-4 z-[var(--z-toast)] flex flex-col gap-2 pointer-events-none">
      {items.map(item => (
        <div
          key={item.id}
          className={`anim-spring-in px-4 py-2.5 rounded-[var(--radius)] shadow-lg text-sm font-medium pointer-events-auto
            ${item.type === 'success' ? 'bg-success text-white' : item.type === 'error' ? 'bg-danger text-white' : 'bg-surface border border-[var(--border)] text-foreground'}`}
        >
          {item.message}
        </div>
      ))}
    </div>
  )
}
