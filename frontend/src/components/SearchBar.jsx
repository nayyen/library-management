import { useState, useEffect, useRef } from 'react';

/**
 * SearchBar — debounced search input.
 *
 * Props:
 *   value      : string   — controlled value from parent
 *   onChange   : (val: string) => void
 *   placeholder: string
 */
export default function SearchBar({ value, onChange, placeholder = 'Cari judul, penulis, atau ISBN…' }) {
  const [local, setLocal] = useState(value ?? '');
  const debounceRef = useRef(null);

  // Sync external value changes
  useEffect(() => {
    setLocal(value ?? '');
  }, [value]);

  function handleChange(e) {
    const v = e.target.value;
    setLocal(v);
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      onChange(v);
    }, 300);
  }

  function handleClear() {
    setLocal('');
    clearTimeout(debounceRef.current);
    onChange('');
  }

  // Cleanup on unmount
  useEffect(() => {
    return () => clearTimeout(debounceRef.current);
  }, []);

  return (
    <div className="relative w-full">
      <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-outline text-[20px] pointer-events-none">
        search
      </span>
      <input
        type="text"
        value={local}
        onChange={handleChange}
        placeholder={placeholder}
        className="w-full bg-surface-container-low border border-outline-variant rounded-full py-3 pl-12 pr-12 text-body-md font-body-md text-primary placeholder:text-outline-variant focus:outline-none focus:border-antique-gold focus:ring-1 focus:ring-antique-gold/30 transition-all"
      />
      {local && (
        <button
          type="button"
          onClick={handleClear}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-outline hover:text-primary transition-colors"
          aria-label="Hapus pencarian"
        >
          <span className="material-symbols-outlined text-[20px]">close</span>
        </button>
      )}
    </div>
  );
}
