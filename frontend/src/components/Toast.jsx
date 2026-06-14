import { useState, useEffect, useCallback } from 'react';

/**
 * Toast — lightweight notification.
 *
 * Props:
 *   message : string   — toast text
 *   type    : 'success' | 'error' | 'info'
 *   onClose : () => void
 *   duration: number   — auto-dismiss ms (default 3000)
 */

const typeStyles = {
  success: 'bg-sage-green text-white',
  error: 'bg-alert-crimson text-white',
  info: 'bg-ink-blue text-white',
};

export default function Toast({ message, type = 'info', onClose, duration = 3000 }) {
  const [visible, setVisible] = useState(true);

  const dismiss = useCallback(() => {
    setVisible(false);
    setTimeout(() => onClose?.(), 300);
  }, [onClose]);

  useEffect(() => {
    const timer = setTimeout(dismiss, duration);
    return () => clearTimeout(timer);
  }, [duration, dismiss]);

  return (
    <div
      className={`fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-3 px-5 py-3 rounded-full shadow-lg transition-all duration-300 ${
        typeStyles[type] ?? typeStyles.info
      } ${visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}
    >
      <span className="material-symbols-outlined text-[18px]">
        {type === 'success' ? 'check_circle' : type === 'error' ? 'error' : 'info'}
      </span>
      <span className="text-body-sm font-body-sm">{message}</span>
      <button
        type="button"
        onClick={dismiss}
        className="ml-2 opacity-70 hover:opacity-100 transition-opacity"
        aria-label="Tutup"
      >
        <span className="material-symbols-outlined text-[18px]">close</span>
      </button>
    </div>
  );
}
