export default function InputField({
  label,
  type = 'text',
  value,
  onChange,
  error,
  placeholder,
  icon,
  ...props
}) {
  return (
    <div className="space-y-1">
      <label className="block text-label-md font-label-md text-primary">
        {label}
      </label>
      <div className="relative">
        {icon && (
          <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline text-[20px]">
            {icon}
          </span>
        )}
        <input
          type={type}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          className={`w-full bg-transparent border-b-2 py-3 text-body-md font-body-md text-primary placeholder:text-outline-variant focus:outline-none transition-colors ${
            icon ? 'pl-10' : 'pl-0'
          } ${
            error
              ? 'border-error focus:border-error'
              : 'border-outline-variant focus:border-antique-gold'
          }`}
          {...props}
        />
      </div>
      {error && (
        <p className="text-body-sm font-body-sm text-error mt-1">{error}</p>
      )}
    </div>
  );
}
