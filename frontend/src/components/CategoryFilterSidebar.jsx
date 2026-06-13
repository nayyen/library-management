import { useState, useEffect } from 'react';
import api from '../lib/api';

/**
 * CategoryFilterSidebar — multi-select category filter.
 *
 * Props:
 *   selected   : string[] — currently selected categories
 *   onChange   : (selected: string[]) => void
 */
export default function CategoryFilterSidebar({ selected = [], onChange }) {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    api
      .get('/buku/kategori')
      .then((res) => {
        if (!cancelled) setCategories(res.data);
      })
      .catch(() => {
        if (!cancelled) setCategories([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  function toggle(kat) {
    const next = selected.includes(kat)
      ? selected.filter((k) => k !== kat)
      : [...selected, kat];
    onChange(next);
  }

  return (
    <aside className="w-full lg:w-56 shrink-0">
      <h3 className="text-label-md font-label-md text-primary mb-4 flex items-center gap-2">
        <span className="material-symbols-outlined text-[18px] text-outline">filter_list</span>
        Kategori
      </h3>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-5 bg-surface-container rounded animate-pulse" />
          ))}
        </div>
      ) : categories.length === 0 ? (
        <p className="text-body-sm font-body-sm text-outline-variant">
          Tidak ada kategori
        </p>
      ) : (
        <ul className="space-y-3">
          {categories.map((kat) => {
            const checked = selected.includes(kat);
            return (
              <li key={kat}>
                <label className="flex items-center gap-3 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => toggle(kat)}
                    className="w-4 h-4 rounded border-outline-variant text-antique-gold focus:ring-antique-gold/30 accent-antique-gold"
                  />
                  <span
                    className={`text-body-md font-body-md transition-colors ${
                      checked
                        ? 'text-primary font-label-md'
                        : 'text-outline group-hover:text-primary'
                    }`}
                  >
                    {kat}
                  </span>
                </label>
              </li>
            );
          })}
        </ul>
      )}

      {selected.length > 0 && (
        <button
          type="button"
          onClick={() => onChange([])}
          className="mt-5 text-body-sm font-body-sm text-antique-gold hover:underline flex items-center gap-1"
        >
          <span className="material-symbols-outlined text-[16px]">close</span>
          Hapus filter
        </button>
      )}
    </aside>
  );
}
