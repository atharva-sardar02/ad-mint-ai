/**
 * Reusable Select component.
 */
import React, { useId } from "react";

export interface SelectProps
  extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  options: Array<{ value: string; label: string }>;
}

/**
 * Select component with label and options.
 */
export const Select: React.FC<SelectProps> = ({
  label,
  options,
  className = "",
  id,
  ...props
}) => {
  const generatedId = useId();
  const selectId = id ?? generatedId;

  return (
    <div className="w-full">
      {label && (
        <label
          htmlFor={selectId}
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          {label}
        </label>
      )}
      <select
        id={selectId}
        className={`
          block w-full px-3 py-2 border border-gray-300 rounded-md
          shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500
          bg-white text-gray-900
          ${className}
        `}
        {...props}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
};

